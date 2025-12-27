# shmupfetch

A companion tool for [ShmupArch Linux](https://github.com/fbscarel/shmuparch-linux) that fetches arcade shmup ROMs from [mdk.cab](https://mdk.cab).

## Features

- **Developer-based browsing** - Browse games by developer (Cave, Raizing, Toaplan, etc.)
- **Smart filtering** - Automatically filters non-shmup games (puzzle, sports, fighting)
- **ROM downloading** - Downloads split ROM sets from mdk.cab
- **Database integration** - Generates entries for `games_db.py` in shmuparch
- **Local ROM scanning** - Tracks which ROMs you already have
- **TUI selection** - Interactive game selection with checkboxes

## Installation

Requires Python 3.12+ and uv:

```bash
# Clone the repository
git clone https://github.com/fbscarel/shmupfetch
cd shmupfetch

# Run with uv (auto-installs dependencies)
uv run shmupfetch.py --help
```

Or install dependencies manually:

```bash
pip install requests beautifulsoup4
python shmupfetch.py --help
```

## Usage

```bash
# Interactive: select developer, then games
./shmupfetch.py

# Fetch games from specific developer
./shmupfetch.py "Cave"
./shmupfetch.py "Raizing"

# Fetch from all developers
./shmupfetch.py --all

# List available developers
./shmupfetch.py --list-developers

# Scan local ROMs and show stats
./shmupfetch.py --scan

# Generate games_db.py entries for local ROMs
./shmupfetch.py --generate

# Show games without downloading (dry run)
./shmupfetch.py "Cave" --dry-run

# Auto-download all missing games (no prompts)
./shmupfetch.py "Cave" -y

# Only show/download missing games
./shmupfetch.py "Cave" --missing-only
```

## Supported Developers

| Developer | Notes |
|-----------|-------|
| Cave | All shmup releases |
| Raizing | Battle Garegga, Batrider, Bakraid, Mahou Daisakusen series |
| Toaplan | Truxton, Batsugun, Fire Shark, Zero Wing, etc. |
| Psikyo | Gunbird, Strikers 1945, Tengai, Dragon Blaze |
| Capcom | 194X series, Giga Wing, Progear, Mars Matrix |
| Irem | R-Type series, Image Fight, X-Multiply |
| Taito | Darius, Rayforce, Metal Black, G-Darius |
| Seibu Kaihatsu | Raiden series, Raiden Fighters series |
| Konami | Gradius, Salamander, Parodius, Thunder Cross |
| SNK | Metal Slug, Blazing Star, Pulstar |
| NMK | Hacha Mecha Fighter, Black Heart, Vandyke |
| Treasure | Radiant Silvergun, Ikaruga (via MAME) |
| Technosoft | Thunder Force AC |
| And more... | ADK, Aicom, Allumer, Athena, Face, Gazelle, etc. |

## Configuration

Edit `src/config.py` to customize:

```python
# ROM download directory
ROM_DIR = Path("/mnt/z/roms/arcade")

# Path to shmuparch's games_db.py
GAMES_DB_PATH = Path.home() / "src" / "shmuparch" / "games_db.py"
```

## How It Works

1. **Scrapes mdk.cab** - Fetches game lists from manufacturer pages
2. **Filters non-shmups** - Skips puzzle, sports, fighting games by keyword
3. **Caches metadata** - Stores game info in local SQLite database
4. **Downloads ROMs** - Fetches split ROM sets (parent + clone deltas)
5. **Updates games_db.py** - Generates `_add(Game(...))` entries

## File Structure

```
shmupfetch/
├── shmupfetch.py       # Entry point
├── src/
│   ├── cli.py          # Command-line interface
│   ├── config.py       # Configuration constants
│   ├── db.py           # SQLite database and games_db.py integration
│   ├── mdk.py          # mdk.cab scraping and downloads
│   └── tui.py          # Terminal UI (selection, confirmation)
├── pyproject.toml      # Project dependencies
└── justfile            # Development commands
```

## Integration with ShmupArch

shmupfetch is designed to work with shmuparch's `games_db.py`:

1. Download ROMs with shmupfetch
2. shmupfetch generates `_add(Game(...))` entries
3. Add entries to `games_db.py` (or let shmupfetch append them)
4. shmuparch automatically picks up new games

## License

MIT License
