"""Configuration constants for shmupfetch."""

from pathlib import Path

# Paths
ROM_DIR = Path("/mnt/z/roms/arcade")
SHMUPARCH_PATH = Path.home() / "src" / "shmuparch" / "shmuparch.py"
DB_PATH = Path.home() / ".cache" / "shmupfetch" / "games.db"

# mdk.cab configuration
MDK_BASE_URL = "https://mdk.cab"
MDK_DOWNLOAD_URL = "https://mdk.cab/download/split"
MDK_CHD_URL = "https://mdk.cab/download/chd"

# Request settings
REQUEST_TIMEOUT = 30
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0"
}

# Developer configurations: name -> list of mdk.cab manufacturer paths
# Each developer can have multiple manufacturer entries (different licenses, etc.)
DEVELOPERS = {
    "Cave": [
        "Cave",
        "Cave+(AMI+license)",
        "Cave+(Atlus+license)",
        "Cave+(Capcom+license)",
        "Cave+(Nihon+System+license)",
        # Skip Jaleco license (puzzle games only)
    ],
    "Raizing": [
        "Raizing",
        "Raizing+%28Able+license%29",
        "Raizing+%28Unite+Trading+license%29",
        "Eighting+%252F+Raizing",
        "Eighting+%252F+Raizing+%28Capcom+license%29",
        "Raizing+%252F+Eighting",
        # Skip Eighting / Raizing / Namco (non-shmup games)
    ],
    "Toaplan": [
        "Toaplan",
    ],
    "Psikyo": [
        "Psikyo",
    ],
    "Irem": [
        "Irem",
        "Irem+(licensed+from+Broderbund)",
    ],
    "Seibu Kaihatsu": [
        "Seibu+Kaihatsu",
    ],
    "Konami": [
        "Konami",
        "Konami+(Centuri+license)",
    ],
    "Taito": [
        "Taito",
        "Taito+Corporation",
        "Taito+Corporation+Japan",
        "Taito+America+Corporation",
    ],
    "Capcom": [
        "Capcom",
    ],
    "SNK": [
        "SNK",
    ],
    "Treasure": [
        "Treasure",
    ],
    "Compile": [
        "Compile",
        "Compile+(Sega+license)",
        "Compile+%252F+Sega",
    ],
    "Technosoft": [
        "Technosoft",
    ],
    "NMK": [
        "NMK",
        "NMK+(UPL+license)",
    ],
    "Video System": [
        "Video+System+Co.",
    ],
    "Visco": [
        "Visco",
    ],
    "Atlus": [
        "Atlus",
    ],
    "Banpresto": [
        "Banpresto",
    ],
    "Jaleco": [
        "Jaleco",
    ],
    "Nichibutsu": [
        "Nihon+Bussan+Co.",
        "Nichibutsu",
    ],
}

# Known TATE (vertical) games - orientation = 1 in shmuparch.py
# Most shmups are TATE, so we'll default to TATE and have a YOKO list instead
YOKO_GAMES = {
    # Horizontal shooters
    "gradius",
    "gradius2",
    "gradius3",
    "gradius4",
    "salamand",
    "salamand2",
    "lifefrce",
    "darius",
    "darius2",
    "dariusg",
    "rtype",
    "rtype2",
    "rtypelo",
    "xmultipl",
    "thunderx",
    "thunderxa",
    "parodius",
    "parodiusj",
    "twinbee",
    "twinbeeb",
    "gaiapols",
    "silentd",
    "silentdj",
    "blazstar",
    "pulstar",
    # Run and guns (not shmups but in arcade collections)
    "contra",
    "contraj",
    "mslug",
    "mslug2",
    "mslug3",
    "mslug4",
    "mslug5",
    "mslugx",
}

# Keywords in game titles that indicate non-shmup games
# Used to filter out irrelevant games from mixed-genre publishers
SKIP_KEYWORDS = [
    # Photo booth / print club
    "print club", "pclub", "purikura",
    # Sports
    "bowling", "golf", "tennis", "soccer", "football", "baseball", "basketball",
    "hockey", "racing", "rally", "derby", "kart",
    # Fighting (standalone, not shooter hybrids)
    "street fighter", "fatal fury", "king of fighters", "tekken", "virtua fighter",
    "mortal kombat", "groove on fight", "power instinct", "gouketsuji",
    # Puzzle
    "puzzle", "tetris", "columns", "puyo", "match",
    # Mahjong
    "mahjong", "mahjon", "jan",
    # Quiz / Trivia
    "quiz", "trivia",
    # Gambling / Medal
    "pachinko", "pachislot", "slot", "casino", "medal", "poker", "roulette",
    # Licensed character games (usually not shmups)
    "pokemon", "winnie", "pooh", "disney", "sanrio", "hello kitty",
    "pepsiman", "felix the cat",
    # Misc non-shmup
    "dance", "karaoke", "music", "beatmania", "ddr",
    "princess", "love", "dating",
    "billiard", "pool",
]

# Games to skip (not shmups, puzzle games, etc.)
SKIP_GAMES = {
    # Puzzle games
    "uopoko",
    "uopokoj",
    "puzldama",
    "puzldamj",
    "hotgmck",
    "hotgmcki",
    "mjgtaste",
    "mushitam",
    "mushitama",
    # Festival/carnival games
    "fstgfish",
    "oygt",
    "oyks",
    # Fighting games
    "beastrzr",
    "beastrzra",
    "bldyroar",
    "bldyror2",
    "bldyror2a",
    "bldyror2j",
    "bldyror2u",
    "brvblade",
    "brvbladea",
    "brvbladej",
    "brvbladeu",
    # Sports/racing
    "btlkroad",
    "btlkroadk",
    # Non-shmup arcade
    "mmmbanc",
    # Medal/gambling
    "loderndfa",
    "loderndf",
    # Unsupported hardware (CAVE PC)
    "deathsm2",
    # BIOS files
    "coh1002e",
    # Light gun / non-shmup
    "ghunter",
    "golgo13",
    "g13knd",
    "g13jnr",
    "ghlpanic",
    "ohbakyuun",
}

# CHD games - ROM name -> CHD filename (for games that need CHD files)
CHD_GAMES = {
    # CV1000 games that might need CHDs
    # Most CV1000 games don't need CHDs, but some variants do
}

# Display name overrides (when mdk.cab name is ugly or abbreviated)
DISPLAY_NAMES = {
    "ddonpach": "DoDonPachi",
    "donpachi": "DonPachi",
    "dfeveron": "Dangun Feveron",
    "esprade": "ESP Ra.De.",
    "guwange": "Guwange",
    "progear": "Progear",
    "mushisam": "Mushihime-Sama",
    "futari15": "Mushihime-Sama Futari",
    "futaribl": "Mushihime-Sama Futari Black Label",
    "espgal": "Espgaluda",
    "espgal2": "Espgaluda II",
    "deathsml": "Deathsmiles",
    "dsmbl": "Deathsmiles MegaBlack Label",
    "ddpdoj": "DoDonPachi Dai-Ou-Jou",
    "ddpdojblk": "DoDonPachi Dai-Ou-Jou Black Label",
    "ddpdfk": "DoDonPachi Dai-Fukkatsu",
    "dfkbl": "DoDonPachi Dai-Fukkatsu Black Label",
    "ket": "Ketsui",
    "ibara": "Ibara",
    "ibarablk": "Ibara Kuro Black Label",
    "pinkswts": "Pink Sweets",
    "mmpork": "Muchi Muchi Pork!",
    "akatana": "Akai Katana",
    "bgaregga": "Battle Garegga",
    "batrider": "Armed Police Batrider",
    "bbakraid": "Battle Bakraid",
    "sstriker": "Sorcer Striker",
    "mahoudai": "Mahou Daisakusen",
    "shippumd": "Shippu Mahou Daisakusen",
    "kingdmgp": "Kingdom Grandprix",
    "sokyugrt": "Soukyugurentai",
    "dimahoo": "Dimahoo",
    "gmahou": "Great Mahou Daisakusen",
    "batsugun": "Batsugun",
    "batsugunsp": "Batsugun Special Version",
    "truxton": "Truxton",
    "truxton2": "Truxton II",
    "vimana": "Vimana",
    "fireshrk": "Fire Shark",
    "hellfire": "Hellfire",
    "zerowing": "Zero Wing",
    "outzone": "Out Zone",
    "tatsujin": "Tatsujin",
    "samesame": "Same! Same! Same!",
    "gunbird": "Gunbird",
    "gunbird2": "Gunbird 2",
    "s1945": "Strikers 1945",
    "s1945ii": "Strikers 1945 II",
    "s1945iii": "Strikers 1945 III",
    "tengai": "Tengai",
    "dragnblz": "Dragon Blaze",
    "soldivid": "Sol Divide",
    "raiden": "Raiden",
    "raiden2": "Raiden II",
    "raidendx": "Raiden DX",
    "raidenf": "Raiden Fighters",
    "raidenf2": "Raiden Fighters 2",
    "rdft": "Raiden Fighters Jet",
}
