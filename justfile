set shell := ["bash", "-uc"]

default:
    @just --list

# Installation
install:
    uv sync

install-dev:
    uv sync --all-extras

# Run commands
run *ARGS:
    uv run python shmupfetch.py {{ARGS}}

# Fetch ROMs for a specific developer
fetch DEV *ARGS:
    uv run python shmupfetch.py "{{DEV}}" {{ARGS}}

# List available developers
list-devs:
    uv run python shmupfetch.py --list-developers

# Scan existing ROMs
scan:
    uv run python shmupfetch.py --scan

# Generate shmuparch.py entries
generate *ARGS:
    uv run python shmupfetch.py --generate {{ARGS}}

# Download all missing ROMs (non-interactive)
download-all *ARGS:
    uv run python shmupfetch.py --all -y {{ARGS}}

# Code quality
fmt:
    uv run ruff format .
    uv run ruff check . --fix

lint:
    uv run ruff check .

fmt-check:
    uv run ruff format . --check
    uv run ruff check .

test:
    uv run pytest -v

# Cleanup
clean:
    rm -rf __pycache__ src/__pycache__ .pytest_cache .ruff_cache
    rm -rf dist build *.egg-info
    rm -rf ~/.cache/shmupfetch

# Check ROM directory
check-roms:
    @echo "=== ROM Directory Status ==="
    @ls -la /mnt/z/roms/arcade/*.zip 2>/dev/null | wc -l | xargs echo "ZIP files:"
    @du -sh /mnt/z/roms/arcade 2>/dev/null || echo "ROM directory not found"
