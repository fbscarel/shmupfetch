"""mdk.cab scraping and ROM download functions."""

import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from .config import (
    CHD_GAMES,
    DISPLAY_NAMES,
    MDK_BASE_URL,
    MDK_CHD_URL,
    MDK_DOWNLOAD_URL,
    REQUEST_HEADERS,
    REQUEST_TIMEOUT,
    SKIP_GAMES,
    SKIP_KEYWORDS,
    YOKO_GAMES,
)


def get_session() -> requests.Session:
    """Create a configured requests session."""
    session = requests.Session()
    session.headers.update(REQUEST_HEADERS)
    return session


def is_likely_shmup(title: str, rom_name: str) -> bool:
    """Check if a game is likely a shmup based on title keywords.

    Returns False if the title contains keywords indicating non-shmup games.
    """
    title_lower = title.lower()
    rom_lower = rom_name.lower()

    for keyword in SKIP_KEYWORDS:
        if keyword in title_lower or keyword in rom_lower:
            return False

    return True


def fetch_games_by_manufacturer(session: requests.Session, manufacturer_path: str) -> list[dict]:
    """Fetch game list from a manufacturer page on mdk.cab.

    Args:
        session: Requests session
        manufacturer_path: URL-encoded manufacturer path (e.g., "Cave+(AMI+license)")

    Returns:
        List of game dicts with keys: rom_name, title, manufacturer
    """
    url = f"{MDK_BASE_URL}/manufacturer/{manufacturer_path}"

    try:
        response = session.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"  Error fetching {manufacturer_path}: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    games = []

    # Find all game links: <a href="/game/romname">
    for link in soup.find_all("a", href=re.compile(r"^/game/")):
        rom_name = link["href"].replace("/game/", "")

        # Skip explicitly blocked games
        if rom_name in SKIP_GAMES:
            continue

        # Find the parent details element to get the full title
        details = link.find_parent("details")
        if details:
            summary = details.find("summary")
            title = summary.get_text(strip=True) if summary else rom_name
        else:
            title = link.get_text(strip=True) or rom_name

        # Clean up title
        title = re.sub(r"\s*\([^)]*\)\s*$", "", title)  # Remove trailing (version info)
        title = re.sub(r"\s*\[[^\]]*\]\s*$", "", title)  # Remove trailing [info]

        # Skip games that don't look like shmups based on title keywords
        if not is_likely_shmup(title, rom_name):
            continue

        games.append(
            {
                "rom_name": rom_name,
                "title": title,
                "manufacturer": manufacturer_path,
            }
        )

    return games


def fetch_developer_games(
    session: requests.Session,
    developer: str,
    manufacturer_paths: list[str],
) -> list[dict]:
    """Fetch all games for a developer from all their manufacturer paths.

    Args:
        session: Requests session
        developer: Developer name (e.g., "Cave")
        manufacturer_paths: List of mdk.cab manufacturer paths

    Returns:
        List of unique game dicts, deduplicated by rom_name base
    """
    all_games = []
    seen_bases = set()

    for mfr_path in manufacturer_paths:
        print(f"  Fetching from {mfr_path}...")
        games = fetch_games_by_manufacturer(session, mfr_path)

        for game in games:
            # Deduplicate by base ROM name (remove region/version suffixes)
            base_name = get_base_rom_name(game["rom_name"])

            if base_name not in seen_bases:
                seen_bases.add(base_name)
                game["developer"] = developer
                game["display_name"] = get_display_name(game["rom_name"], game["title"])
                game["orientation"] = 0 if game["rom_name"] in YOKO_GAMES else 1
                game["has_chd"] = game["rom_name"] in CHD_GAMES
                all_games.append(game)

        # Rate limit
        time.sleep(0.3)

    return all_games


def get_base_rom_name(rom_name: str) -> str:
    """Get the base ROM name without region/version suffixes.

    Examples:
        gunbirdj -> gunbird
        bgaregganv -> bgaregga
        batriderja -> batrider
        s1945ii -> s1945ii (no suffix)
    """
    # Compound suffixes first (most specific), then single char
    # Order matters: check longer suffixes first
    suffixes = [
        # 3+ char compound suffixes
        "blk", "blka", "blkb",
        # 2-char compound suffixes (region + version)
        "ja", "jb", "jc", "ua", "ub", "ka", "kb", "ea", "eb",
        # 2-char region codes
        "hk", "tw", "kr", "nv", "bl", "sp", "cn",
        # Single char (region/version)
        "j", "u", "k", "a", "b", "c", "e", "t", "o",
    ]

    for suffix in suffixes:
        if rom_name.endswith(suffix) and len(rom_name) > len(suffix) + 3:
            base = rom_name[: -len(suffix)]
            # Only strip if remaining name looks valid (not too short)
            if len(base) >= 4:
                return base

    return rom_name


def get_display_name(rom_name: str, mdk_title: str) -> str:
    """Get a clean display name for a game.

    Uses override if available, otherwise cleans up mdk.cab title.
    """
    # Check for manual override
    base_name = get_base_rom_name(rom_name)
    if base_name in DISPLAY_NAMES:
        return DISPLAY_NAMES[base_name]
    if rom_name in DISPLAY_NAMES:
        return DISPLAY_NAMES[rom_name]

    # Clean up mdk.cab title
    title = mdk_title

    # Remove version info in parentheses at the end
    title = re.sub(r"\s*\([\d/\s.]+[^)]*\)\s*$", "", title)

    # Remove "MASTER VER" etc.
    title = re.sub(r"\s*MASTER\s*VER\.?.*$", "", title, flags=re.IGNORECASE)

    return title.strip()


def download_rom(
    session: requests.Session,
    rom_name: str,
    output_dir: Path,
    progress_callback=None,
) -> bool:
    """Download a ROM file from mdk.cab.

    Args:
        session: Requests session
        rom_name: ROM name (e.g., "ddonpach")
        output_dir: Directory to save the ROM
        progress_callback: Optional callback(bytes_downloaded, total_bytes)

    Returns:
        True if download succeeded, False otherwise
    """
    url = f"{MDK_DOWNLOAD_URL}/{rom_name}.zip"
    output_path = output_dir / f"{rom_name}.zip"

    # Skip if already exists
    if output_path.exists():
        print(f"  {rom_name}.zip already exists, skipping")
        return True

    try:
        response = session.get(url, timeout=REQUEST_TIMEOUT, stream=True)
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0))
        downloaded = 0

        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                if progress_callback:
                    progress_callback(downloaded, total_size)

        # Verify file size
        if output_path.stat().st_size == 0:
            output_path.unlink()
            print(f"  Error: Downloaded {rom_name}.zip is empty")
            return False

        return True

    except requests.RequestException as e:
        print(f"  Error downloading {rom_name}: {e}")
        if output_path.exists():
            output_path.unlink()
        return False


def download_chd(
    session: requests.Session,
    rom_name: str,
    chd_name: str,
    output_dir: Path,
    progress_callback=None,
) -> bool:
    """Download a CHD file from mdk.cab.

    Args:
        session: Requests session
        rom_name: ROM name (parent directory)
        chd_name: CHD filename
        output_dir: Base directory for ROMs
        progress_callback: Optional callback(bytes_downloaded, total_bytes)

    Returns:
        True if download succeeded, False otherwise
    """
    url = f"{MDK_CHD_URL}/{rom_name}/{chd_name}"
    chd_dir = output_dir / rom_name
    chd_dir.mkdir(exist_ok=True)
    output_path = chd_dir / chd_name

    # Skip if already exists
    if output_path.exists():
        print(f"  {chd_name} already exists, skipping")
        return True

    try:
        response = session.get(
            url, timeout=REQUEST_TIMEOUT * 10, stream=True
        )  # Longer timeout for CHDs
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0))
        downloaded = 0

        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=65536):  # Larger chunks for big files
                f.write(chunk)
                downloaded += len(chunk)
                if progress_callback:
                    progress_callback(downloaded, total_size)

        # Verify file size
        if output_path.stat().st_size == 0:
            output_path.unlink()
            print(f"  Error: Downloaded {chd_name} is empty")
            return False

        return True

    except requests.RequestException as e:
        print(f"  Error downloading {chd_name}: {e}")
        if output_path.exists():
            output_path.unlink()
        return False


def search_games(session: requests.Session, query: str) -> list[dict]:
    """Search for games on mdk.cab.

    Args:
        session: Requests session
        query: Search query

    Returns:
        List of game dicts with keys: rom_name, title
    """
    url = f"{MDK_BASE_URL}/search.php"

    try:
        response = session.post(url, data={"search": query}, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"  Error searching for '{query}': {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    games = []

    for link in soup.find_all("a", href=re.compile(r"^/game/")):
        rom_name = link["href"].replace("/game/", "")
        title = link.get_text(strip=True) or rom_name

        games.append(
            {
                "rom_name": rom_name,
                "title": title,
            }
        )

    return games
