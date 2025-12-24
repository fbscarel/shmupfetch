"""Curses-based TUI for game and developer selection."""

import curses


def select_developer(developers: list[str]) -> str | None:
    """Interactive single-select menu for developer selection.

    Args:
        developers: List of developer names

    Returns:
        Selected developer name, or None if cancelled
    """
    if not developers:
        return None

    def run_curses(stdscr) -> int | None:
        curses.curs_set(0)
        curses.use_default_colors()

        curses.init_pair(1, curses.COLOR_GREEN, -1)
        curses.init_pair(2, curses.COLOR_CYAN, -1)

        cursor = 0
        scroll_offset = 0

        while True:
            stdscr.clear()
            height, width = stdscr.getmaxyx()

            # Header
            header = "Select a developer"
            controls = "↑↓:move  ENTER:select  a:all developers  q:quit"
            stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
            stdscr.addstr(0, 0, header[: width - 1])
            stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)
            stdscr.addstr(1, 0, controls[: width - 1])
            stdscr.addstr(2, 0, "─" * min(width - 1, 50))

            # List
            list_start = 3
            list_height = height - list_start - 1
            visible_count = min(list_height, len(developers))

            if cursor < scroll_offset:
                scroll_offset = cursor
            elif cursor >= scroll_offset + visible_count:
                scroll_offset = cursor - visible_count + 1

            for i in range(visible_count):
                dev_idx = scroll_offset + i
                if dev_idx >= len(developers):
                    break

                dev = developers[dev_idx]
                is_cursor = dev_idx == cursor
                y = list_start + i

                if is_cursor:
                    stdscr.attron(curses.A_REVERSE)
                    stdscr.attron(curses.color_pair(1))

                line = f"  {dev}"
                try:
                    stdscr.addstr(y, 0, line[: width - 1])
                except curses.error:
                    pass

                if is_cursor:
                    stdscr.attroff(curses.A_REVERSE)
                    stdscr.attroff(curses.color_pair(1))

            # Status bar
            status = f" Developer {cursor + 1}/{len(developers)}"
            try:
                stdscr.addstr(height - 1, 0, status[: width - 1], curses.A_REVERSE)
            except curses.error:
                pass

            stdscr.refresh()
            key = stdscr.getch()

            if key == ord("q") or key == 27:
                return None
            elif key == curses.KEY_UP or key == ord("k"):
                cursor = max(0, cursor - 1)
            elif key == curses.KEY_DOWN or key == ord("j"):
                cursor = min(len(developers) - 1, cursor + 1)
            elif key == curses.KEY_PPAGE:
                cursor = max(0, cursor - visible_count)
            elif key == curses.KEY_NPAGE:
                cursor = min(len(developers) - 1, cursor + visible_count)
            elif key == ord("a"):
                return -1  # Signal for "all developers"
            elif key == ord("\n") or key == curses.KEY_ENTER:
                return cursor

        return None

    try:
        result = curses.wrapper(run_curses)
        if result == -1:
            return "__ALL__"
        elif result is not None:
            return developers[result]
        return None
    except KeyboardInterrupt:
        return None


def select_games(games: list[dict], local_roms: set[str] | None = None) -> list[dict]:
    """Interactive multi-select menu for game selection.

    Args:
        games: List of game dicts with rom_name, display_name, developer
        local_roms: Optional set of ROM names that exist locally

    Returns:
        List of selected game dicts
    """
    if not games:
        return []

    local_roms = local_roms or set()
    has_local = [g["rom_name"] in local_roms for g in games]

    # Pre-select non-local games
    selected = set(i for i, is_local in enumerate(has_local) if not is_local)

    def run_curses(stdscr) -> list[int]:
        nonlocal selected

        curses.curs_set(0)
        curses.use_default_colors()

        curses.init_pair(1, curses.COLOR_GREEN, -1)  # Selected
        curses.init_pair(2, curses.COLOR_YELLOW, -1)  # Local
        curses.init_pair(3, curses.COLOR_CYAN, -1)  # Header
        curses.init_pair(4, curses.COLOR_MAGENTA, -1)  # Developer

        cursor = 0
        scroll_offset = 0

        while True:
            stdscr.clear()
            height, width = stdscr.getmaxyx()

            # Header
            header = "Select games to download"
            controls = "↑↓:move  SPACE:toggle  a:all  n:none  m:missing only  ENTER:confirm  q:quit"
            stdscr.attron(curses.color_pair(3) | curses.A_BOLD)
            stdscr.addstr(0, 0, header[: width - 1])
            stdscr.attroff(curses.color_pair(3) | curses.A_BOLD)
            stdscr.addstr(1, 0, controls[: width - 1])
            stdscr.addstr(2, 0, "─" * min(width - 1, 80))

            # List
            list_start = 3
            list_height = height - list_start - 1
            visible_count = min(list_height, len(games))

            if cursor < scroll_offset:
                scroll_offset = cursor
            elif cursor >= scroll_offset + visible_count:
                scroll_offset = cursor - visible_count + 1

            for i in range(visible_count):
                game_idx = scroll_offset + i
                if game_idx >= len(games):
                    break

                game = games[game_idx]
                is_selected = game_idx in selected
                is_local = has_local[game_idx]
                is_cursor = game_idx == cursor

                marker = "[*]" if is_selected else "[ ]"
                name = game.get("display_name", game["rom_name"])[:40]
                rom = game["rom_name"][:15]
                dev = game.get("developer", "")[:12]
                orient = "TATE" if game.get("orientation", 1) == 1 else "YOKO"

                if is_local:
                    line = f"{marker} {name:<41} {rom:<16} {dev:<13} {orient} [LOCAL]"
                else:
                    line = f"{marker} {name:<41} {rom:<16} {dev:<13} {orient}"

                line = line[: width - 1]
                y = list_start + i

                if is_cursor:
                    stdscr.attron(curses.A_REVERSE)

                if is_local:
                    stdscr.attron(curses.A_DIM)

                if is_selected and not is_local:
                    stdscr.attron(curses.color_pair(1))

                try:
                    stdscr.addstr(y, 0, line)
                except curses.error:
                    pass

                stdscr.attroff(curses.A_REVERSE | curses.A_DIM)
                stdscr.attroff(curses.color_pair(1))

            # Status bar
            local_count = sum(has_local)
            status = (
                f" {len(selected)} selected, {local_count} local | Game {cursor + 1}/{len(games)}"
            )
            try:
                stdscr.addstr(height - 1, 0, status[: width - 1], curses.A_REVERSE)
            except curses.error:
                pass

            stdscr.refresh()
            key = stdscr.getch()

            if key == ord("q") or key == 27:
                return []
            elif key == curses.KEY_UP or key == ord("k"):
                cursor = max(0, cursor - 1)
            elif key == curses.KEY_DOWN or key == ord("j"):
                cursor = min(len(games) - 1, cursor + 1)
            elif key == curses.KEY_PPAGE:
                cursor = max(0, cursor - visible_count)
            elif key == curses.KEY_NPAGE:
                cursor = min(len(games) - 1, cursor + visible_count)
            elif key == curses.KEY_HOME:
                cursor = 0
            elif key == curses.KEY_END:
                cursor = len(games) - 1
            elif key == ord(" "):
                if cursor in selected:
                    selected.discard(cursor)
                else:
                    selected.add(cursor)
                cursor = min(len(games) - 1, cursor + 1)
            elif key == ord("a"):
                selected = set(range(len(games)))
            elif key == ord("n"):
                selected = set()
            elif key == ord("m"):
                # Select only missing (non-local) games
                selected = set(i for i, is_local in enumerate(has_local) if not is_local)
            elif key == ord("\n") or key == curses.KEY_ENTER:
                return list(sorted(selected))

        return []

    try:
        result = curses.wrapper(run_curses)
        return [games[i] for i in result]
    except KeyboardInterrupt:
        return []


def confirm_action(message: str, default: bool = True) -> bool:
    """Simple yes/no confirmation in curses.

    Args:
        message: Message to display
        default: Default choice if Enter is pressed

    Returns:
        True for yes, False for no
    """

    def run_curses(stdscr) -> bool:
        curses.curs_set(0)
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_CYAN, -1)

        stdscr.clear()
        height, width = stdscr.getmaxyx()

        stdscr.attron(curses.color_pair(1) | curses.A_BOLD)
        stdscr.addstr(1, 2, message[: width - 4])
        stdscr.attroff(curses.color_pair(1) | curses.A_BOLD)

        if default:
            prompt = "[Y/n]: "
        else:
            prompt = "[y/N]: "

        stdscr.addstr(3, 2, prompt)
        stdscr.refresh()

        while True:
            key = stdscr.getch()

            if key == ord("y") or key == ord("Y"):
                return True
            elif key == ord("n") or key == ord("N"):
                return False
            elif key == ord("\n") or key == curses.KEY_ENTER:
                return default
            elif key == ord("q") or key == 27:
                return False

    try:
        return curses.wrapper(run_curses)
    except KeyboardInterrupt:
        return False
