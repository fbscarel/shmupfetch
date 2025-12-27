"""Command-line interface and main orchestration."""

import argparse
import sys
from pathlib import Path

from .config import DEVELOPERS, ROM_DIR
from .db import (
    GameDatabase,
    generate_games_db_entries,
    get_existing_games,
    get_games_db_roms,
    get_missing_games,
    scan_rom_directory,
    update_games_db_file,
)
from .mdk import download_rom, fetch_developer_games, get_session
from .tui import confirm_action, select_developer, select_games


def main():
    parser = argparse.ArgumentParser(
        description="Fetch and organize shmup arcade ROMs from mdk.cab"
    )
    parser.add_argument(
        "developer",
        nargs="?",
        help="Developer name to fetch games from (e.g., 'Cave', 'Raizing')",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Fetch games from all developers",
    )
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip interactive selection, download all missing games",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show games but don't download",
    )
    parser.add_argument(
        "--list-developers",
        action="store_true",
        help="List available developers",
    )
    parser.add_argument(
        "--scan",
        action="store_true",
        help="Scan ROM directory and show statistics",
    )
    parser.add_argument(
        "--rescan",
        action="store_true",
        help="Force full rescan of ROM directory",
    )
    parser.add_argument(
        "--generate",
        action="store_true",
        help="Generate games_db.py entries for local ROMs",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help=f"Output directory for ROMs (default: {ROM_DIR})",
    )
    parser.add_argument(
        "--missing-only",
        action="store_true",
        help="Only show/download games not in local ROM directory",
    )

    args = parser.parse_args()

    # Handle --list-developers
    if args.list_developers:
        print("Available developers:")
        for dev in sorted(DEVELOPERS.keys()):
            mfr_count = len(DEVELOPERS[dev])
            print(f"  {dev} ({mfr_count} manufacturer path{'s' if mfr_count > 1 else ''})")
        return

    # Initialize database
    db = GameDatabase()

    # Handle --scan
    if args.scan or args.rescan:
        print(f"Scanning ROM directory: {ROM_DIR}")
        count = scan_rom_directory(db, ROM_DIR, force=args.rescan)
        print(f"  Found {count} new ROMs")

        stats = db.get_stats()
        print("\nDatabase statistics:")
        print(f"  Cached games: {stats['total_games']}")
        print(f"  Local ROMs: {stats['local_roms']}")
        if stats["developers"]:
            print(f"  Developers: {', '.join(stats['developers'])}")
        db.close()
        return

    # Handle --generate
    if args.generate:
        print("Scanning ROM directory...")
        scan_rom_directory(db, ROM_DIR, force=args.rescan)

        local_roms = db.get_local_roms()
        all_games = db.get_all_games()

        # Find games that are both in database and local
        local_games = get_existing_games(db, all_games)

        if not local_games:
            print("No games found in both database and local ROM directory.")
            print("Run 'shmupfetch <developer>' first to populate the database.")
            db.close()
            return

        print(f"\nGenerating entries for {len(local_games)} games...")
        entries = generate_games_db_entries(local_games)

        print("\n# Add these entries to games_db.py:")
        print(entries)

        db.close()
        return

    # Ensure ROM directory exists
    output_dir = args.output or ROM_DIR
    if not output_dir.exists():
        print(f"ROM directory not found: {output_dir}")
        if not confirm_action(f"Create {output_dir}?"):
            db.close()
            return
        output_dir.mkdir(parents=True, exist_ok=True)

    # Scan ROM directory
    print("Scanning local ROM directory...")
    scan_rom_directory(db, output_dir)
    local_roms = db.get_local_roms()
    print(f"  Found {len(local_roms)} local ROMs")

    # Determine which developer(s) to fetch
    if args.all:
        developers_to_fetch = list(DEVELOPERS.keys())
    elif args.developer:
        # Case-insensitive match
        dev_match = None
        for dev in DEVELOPERS:
            if dev.lower() == args.developer.lower():
                dev_match = dev
                break
        if not dev_match:
            print(f"Unknown developer: {args.developer}")
            print(f"Available: {', '.join(sorted(DEVELOPERS.keys()))}")
            db.close()
            sys.exit(1)
        developers_to_fetch = [dev_match]
    else:
        # Interactive developer selection
        selected = select_developer(sorted(DEVELOPERS.keys()))
        if selected is None:
            print("No developer selected.")
            db.close()
            return
        elif selected == "__ALL__":
            developers_to_fetch = list(DEVELOPERS.keys())
        else:
            developers_to_fetch = [selected]

    # Fetch games from mdk.cab
    session = get_session()
    all_games = []

    for developer in developers_to_fetch:
        print(f"\nFetching games for {developer}...")
        manufacturer_paths = DEVELOPERS[developer]
        games = fetch_developer_games(session, developer, manufacturer_paths)
        print(f"  Found {len(games)} games")

        # Cache in database
        db.upsert_games(games)
        all_games.extend(games)

    if not all_games:
        print("No games found.")
        db.close()
        return

    # Filter to missing games if requested
    if args.missing_only:
        all_games = get_missing_games(db, all_games)
        print(f"\n{len(all_games)} games missing locally")

    if args.dry_run:
        print(f"\n{len(all_games)} games available:")
        for g in all_games:
            local_marker = " [LOCAL]" if g["rom_name"] in local_roms else ""
            orient = "TATE" if g.get("orientation", 1) == 1 else "YOKO"
            print(
                f"  {g['rom_name']:20} {g.get('display_name', '')[:35]:36} {orient}{local_marker}"
            )
        db.close()
        return

    # Check what's already in games_db.py
    existing_db_roms = get_games_db_roms()

    # Find games that exist locally but aren't in games_db.py yet
    local_games = get_existing_games(db, all_games)
    games_to_add = [g for g in local_games if g["rom_name"] not in existing_db_roms]

    # Find games that need downloading
    missing_games = get_missing_games(db, all_games)

    print(f"\nSummary:")
    print(f"  {len(local_games)} games exist locally")
    print(f"  {len(games_to_add)} need to be added to games_db.py")
    print(f"  {len(missing_games)} missing from local ROM directory")

    # First, update games_db.py with existing local games
    if games_to_add:
        if args.yes:
            update_games_db_file(games_to_add)
        elif confirm_action(f"Add {len(games_to_add)} games to games_db.py?"):
            if update_games_db_file(games_to_add):
                print("games_db.py updated!")
            else:
                entries = generate_games_db_entries(games_to_add)
                print("\n# Add these entries manually:")
                print(entries)

    # Then handle downloads
    if not missing_games:
        print("\nNo games to download.")
        db.close()
        return

    # Select games to download
    if args.yes:
        to_download = missing_games
        print(f"\nAuto-selected {len(to_download)} games for download")
    else:
        if not confirm_action(f"Download {len(missing_games)} missing games?"):
            db.close()
            return
        to_download = select_games(missing_games, local_roms)

    if not to_download:
        print("No games selected for download.")
        db.close()
        return

    print(f"\nDownloading {len(to_download)} games to {output_dir}...")

    # Download
    success = 0
    failed = []

    for i, game in enumerate(to_download, 1):
        rom_name = game["rom_name"]
        display_name = game.get("display_name", rom_name)
        print(f"[{i}/{len(to_download)}] Downloading: {display_name} ({rom_name})")

        if download_rom(session, rom_name, output_dir):
            success += 1
            # Update local ROM database
            rom_path = output_dir / f"{rom_name}.zip"
            if rom_path.exists():
                stat = rom_path.stat()
                db.upsert_local_rom(rom_name, rom_path, stat.st_size, stat.st_mtime)
                db.conn.commit()
        else:
            failed.append(rom_name)

    print(f"\nDone! {success}/{len(to_download)} downloaded successfully.")
    if failed:
        print(f"Failed: {', '.join(failed)}")

    # Update games_db.py with newly downloaded games
    if success > 0:
        downloaded_games = [g for g in to_download if g["rom_name"] not in failed]
        if args.yes:
            update_games_db_file(downloaded_games)
        elif confirm_action("Add downloaded games to games_db.py?"):
            if update_games_db_file(downloaded_games):
                print("games_db.py updated!")
            else:
                entries = generate_games_db_entries(downloaded_games)
                print("\n# Add these entries manually:")
                print(entries)

    db.close()


if __name__ == "__main__":
    main()
