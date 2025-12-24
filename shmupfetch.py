#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "requests>=2.31.0",
#     "beautifulsoup4>=4.12.0",
# ]
# ///
"""
shmupfetch - Fetch and organize shmup arcade ROMs

Usage:
    shmupfetch                     # Interactive: select developer, then games
    shmupfetch "Cave"              # Fetch games from specific developer
    shmupfetch --all               # Fetch from all developers
    shmupfetch --scan              # Scan existing ROMs
    shmupfetch --generate          # Generate shmuparch.py entries
    shmupfetch --list-developers   # List available developers
"""

from src.cli import main

if __name__ == "__main__":
    main()
