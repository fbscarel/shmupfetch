"""Database management for ROM caching and local scanning."""

import re
import sqlite3
from pathlib import Path

from .config import DB_PATH, ROM_DIR, SHMUPARCH_PATH


class GameDatabase:
    """SQLite database for caching game data and tracking local ROMs."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        """Initialize database schema."""
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS games (
                rom_name TEXT PRIMARY KEY,
                display_name TEXT,
                developer TEXT,
                manufacturer TEXT,
                orientation INTEGER DEFAULT 1,
                has_chd INTEGER DEFAULT 0,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS local_roms (
                rom_name TEXT PRIMARY KEY,
                file_path TEXT,
                file_size INTEGER,
                mtime REAL,
                last_scanned TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_games_developer ON games(developer);
            CREATE INDEX IF NOT EXISTS idx_local_roms_name ON local_roms(rom_name);
        """)
        self.conn.commit()

    def close(self):
        """Close database connection."""
        self.conn.close()

    def upsert_game(self, game: dict):
        """Insert or update a game record."""
        self.conn.execute(
            """
            INSERT INTO games (rom_name, display_name, developer, manufacturer, orientation, has_chd)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(rom_name) DO UPDATE SET
                display_name = excluded.display_name,
                developer = excluded.developer,
                manufacturer = excluded.manufacturer,
                orientation = excluded.orientation,
                has_chd = excluded.has_chd,
                last_seen = CURRENT_TIMESTAMP
        """,
            (
                game["rom_name"],
                game.get("display_name", game["rom_name"]),
                game.get("developer", "Unknown"),
                game.get("manufacturer", "Unknown"),
                game.get("orientation", 1),
                1 if game.get("has_chd") else 0,
            ),
        )

    def upsert_games(self, games: list[dict]):
        """Bulk insert or update games."""
        for game in games:
            self.upsert_game(game)
        self.conn.commit()

    def get_games_by_developer(self, developer: str) -> list[dict]:
        """Get all cached games for a developer."""
        cursor = self.conn.execute(
            """
            SELECT * FROM games WHERE developer = ? ORDER BY display_name
        """,
            (developer,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_all_games(self) -> list[dict]:
        """Get all cached games."""
        cursor = self.conn.execute("""
            SELECT * FROM games ORDER BY developer, display_name
        """)
        return [dict(row) for row in cursor.fetchall()]

    def get_game(self, rom_name: str) -> dict | None:
        """Get a single game by ROM name."""
        cursor = self.conn.execute(
            """
            SELECT * FROM games WHERE rom_name = ?
        """,
            (rom_name,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def upsert_local_rom(self, rom_name: str, file_path: Path, file_size: int, mtime: float):
        """Record a local ROM file."""
        self.conn.execute(
            """
            INSERT INTO local_roms (rom_name, file_path, file_size, mtime)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(rom_name) DO UPDATE SET
                file_path = excluded.file_path,
                file_size = excluded.file_size,
                mtime = excluded.mtime,
                last_scanned = CURRENT_TIMESTAMP
        """,
            (rom_name, str(file_path), file_size, mtime),
        )

    def get_local_roms(self) -> set[str]:
        """Get set of all local ROM names."""
        cursor = self.conn.execute("SELECT rom_name FROM local_roms")
        return {row["rom_name"] for row in cursor.fetchall()}

    def has_local_rom(self, rom_name: str) -> bool:
        """Check if a ROM exists locally."""
        cursor = self.conn.execute(
            "SELECT 1 FROM local_roms WHERE rom_name = ?",
            (rom_name,),
        )
        return cursor.fetchone() is not None

    def clear_local_roms(self):
        """Clear all local ROM records (for rescanning)."""
        self.conn.execute("DELETE FROM local_roms")
        self.conn.commit()

    def get_stats(self) -> dict:
        """Get database statistics."""
        games_count = self.conn.execute("SELECT COUNT(*) FROM games").fetchone()[0]
        local_count = self.conn.execute("SELECT COUNT(*) FROM local_roms").fetchone()[0]
        developers = self.conn.execute(
            "SELECT DISTINCT developer FROM games ORDER BY developer"
        ).fetchall()

        return {
            "total_games": games_count,
            "local_roms": local_count,
            "developers": [row["developer"] for row in developers],
        }


def scan_rom_directory(db: GameDatabase, rom_dir: Path = ROM_DIR, force: bool = False) -> int:
    """Scan ROM directory and update database.

    Args:
        db: GameDatabase instance
        rom_dir: Directory to scan
        force: If True, rescan all files

    Returns:
        Number of ROMs found
    """
    if not rom_dir.exists():
        print(f"ROM directory not found: {rom_dir}")
        return 0

    if force:
        db.clear_local_roms()

    count = 0
    existing_roms = db.get_local_roms() if not force else set()

    for rom_file in rom_dir.glob("*.zip"):
        rom_name = rom_file.stem

        # Skip if already scanned and file unchanged
        if rom_name in existing_roms:
            continue

        stat = rom_file.stat()
        db.upsert_local_rom(rom_name, rom_file, stat.st_size, stat.st_mtime)
        count += 1

    db.conn.commit()
    return count


def get_missing_games(db: GameDatabase, games: list[dict]) -> list[dict]:
    """Filter games to only those not in local ROM directory.

    Args:
        db: GameDatabase instance
        games: List of game dicts

    Returns:
        List of games not found locally
    """
    local_roms = db.get_local_roms()
    return [g for g in games if g["rom_name"] not in local_roms]


def get_existing_games(db: GameDatabase, games: list[dict]) -> list[dict]:
    """Filter games to only those in local ROM directory.

    Args:
        db: GameDatabase instance
        games: List of game dicts

    Returns:
        List of games found locally
    """
    local_roms = db.get_local_roms()
    return [g for g in games if g["rom_name"] in local_roms]


def generate_shmuparch_entries(games: list[dict]) -> str:
    """Generate Python dict entries for shmuparch.py GAMES dict.

    Args:
        games: List of game dicts with rom_name, display_name, developer, orientation

    Returns:
        Python code string for GAMES dict entries
    """
    lines = []
    current_developer = None

    # Sort by developer, then by display name
    sorted_games = sorted(games, key=lambda g: (g.get("developer", ""), g.get("display_name", "")))

    for game in sorted_games:
        developer = game.get("developer", "Unknown")

        # Add developer comment header
        if developer != current_developer:
            if current_developer is not None:
                lines.append("")
            lines.append(f"    # === {developer} ===")
            current_developer = developer

        rom_name = game["rom_name"]
        display_name = game.get("display_name", rom_name)
        orientation = game.get("orientation", 1)

        # Escape quotes in display name
        display_name = display_name.replace('"', '\\"')

        lines.append(f'    "{rom_name}": ("{display_name}", "{developer}", {orientation}),')

    return "\n".join(lines)


def update_shmuparch_file(games: list[dict], shmuparch_path: Path = SHMUPARCH_PATH) -> bool:
    """Update shmuparch.py GAMES dict with new entries.

    Args:
        games: List of game dicts to add
        shmuparch_path: Path to shmuparch.py

    Returns:
        True if successful, False otherwise
    """
    if not shmuparch_path.exists():
        print(f"shmuparch.py not found at {shmuparch_path}")
        return False

    content = shmuparch_path.read_text()

    # Find existing GAMES dict
    games_match = re.search(r"^GAMES\s*=\s*\{", content, re.MULTILINE)
    if not games_match:
        print("Could not find GAMES dict in shmuparch.py")
        return False

    # Get existing ROM names to avoid duplicates
    existing_roms = set(re.findall(r'"([a-z0-9_]+)":\s*\(', content))

    # Filter to only new games
    new_games = [g for g in games if g["rom_name"] not in existing_roms]

    if not new_games:
        print("All games already in shmuparch.py")
        return True

    # Generate entries for new games
    entries = generate_shmuparch_entries(new_games)

    # Find the closing brace of GAMES dict
    # Look for the pattern: last entry followed by }
    # We'll insert before the closing }
    games_end = re.search(r"\n(\s*)\}\s*\n", content[games_match.start() :])
    if not games_end:
        print("Could not find end of GAMES dict")
        return False

    insert_pos = games_match.start() + games_end.start()

    # Insert new entries before closing brace
    new_content = content[:insert_pos] + "\n" + entries + "\n" + content[insert_pos:]

    # Write back
    shmuparch_path.write_text(new_content)
    print(f"Added {len(new_games)} games to {shmuparch_path}")

    return True


def get_shmuparch_games(shmuparch_path: Path = SHMUPARCH_PATH) -> set[str]:
    """Get set of ROM names already in shmuparch.py.

    Args:
        shmuparch_path: Path to shmuparch.py

    Returns:
        Set of ROM names
    """
    if not shmuparch_path.exists():
        return set()

    content = shmuparch_path.read_text()
    return set(re.findall(r'"([a-z0-9_]+)":\s*\(', content))
