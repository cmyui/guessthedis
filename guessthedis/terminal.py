"""Terminal I/O utilities: raw input, ANSI colors, and interactive widgets."""

import contextlib
import os
import signal
import sys
import termios
import tty
from enum import IntEnum
from typing import Any
from typing import Callable
from typing import Iterator

from .state import format_time as _format_time
from .test_functions import Difficulty


class Ansi(IntEnum):
    # Default colours
    BLACK = 30
    RED = 31
    GREEN = 32
    YELLOW = 33
    BLUE = 34
    MAGENTA = 35
    CYAN = 36
    WHITE = 37

    # Light colours
    GRAY = 90
    LRED = 91
    LGREEN = 92
    LYELLOW = 93
    LBLUE = 94
    LMAGENTA = 95
    LCYAN = 96
    LWHITE = 97

    RESET = 0

    def __repr__(self) -> str:
        return f"\x1b[{self.value}m"


@contextlib.contextmanager
def ignore_sigint() -> Iterator[None]:
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    try:
        yield None
    finally:
        signal.signal(signal.SIGINT, signal.default_int_handler)


def printc(string: str, col: Ansi, end: str = "\n") -> None:
    """Print out a given string, with a colour."""
    print(f"{col!r}{string}\x1b[m", end=end)


class NavigationRequested(Exception):
    """Raised when the user presses ^G to open the challenge picker."""


_input_history: list[str] = []


def read_line(prompt: str) -> str:
    """Read a line of input with support for ^G (navigation), ^D (EOF), ^C (interrupt).

    Handles character-by-character reading in raw terminal mode to intercept
    hotkeys while supporting basic line editing (backspace, enter) and
    up/down arrow history navigation.
    """
    sys.stdout.write(prompt)
    sys.stdout.flush()

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        buf: list[str] = []
        history_index = len(_input_history)
        saved_line = ""

        def _replace_buf(new_content: str) -> None:
            # erase current display, replace buffer contents
            if buf:
                sys.stdout.write(f"\x1b[{len(buf)}D\x1b[0K")
            buf.clear()
            buf.extend(new_content)
            sys.stdout.write(new_content)
            sys.stdout.flush()

        while True:
            ch = sys.stdin.read(1)
            if ch == "\x07":  # ^G
                sys.stdout.write("\x1b[2K\r")
                sys.stdout.flush()
                raise NavigationRequested
            elif ch == "\x04":  # ^D
                sys.stdout.write("\x1b[2K\r")
                sys.stdout.flush()
                raise EOFError
            elif ch == "\x03":  # ^C
                sys.stdout.write("\x1b[2K\r")
                sys.stdout.flush()
                raise KeyboardInterrupt
            elif ch == "\x1b":  # escape sequence
                seq = sys.stdin.read(1)
                if seq == "[":
                    arrow = sys.stdin.read(1)
                    if arrow == "A":  # up
                        if history_index > 0:
                            if history_index == len(_input_history):
                                saved_line = "".join(buf)
                            history_index -= 1
                            _replace_buf(_input_history[history_index])
                    elif arrow == "B":  # down
                        if history_index < len(_input_history):
                            history_index += 1
                            if history_index == len(_input_history):
                                _replace_buf(saved_line)
                            else:
                                _replace_buf(_input_history[history_index])
            elif ch in ("\r", "\n"):  # Enter
                sys.stdout.write("\r\n")
                sys.stdout.flush()
                line = "".join(buf)
                if line:
                    _input_history.append(line)
                return line
            elif ch in ("\x7f", "\x08"):  # Backspace
                if buf:
                    buf.pop()
                    sys.stdout.write("\b \b")
                    sys.stdout.flush()
            elif ch >= " ":  # printable characters
                buf.append(ch)
                sys.stdout.write(ch)
                sys.stdout.flush()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def pick_challenge(
    challenges: list[tuple[Difficulty, Callable[..., Any]]],
    results: list[str],
    current_index: int,
    *,
    game_state: dict[str, Any] | None = None,
) -> int | None:
    """Interactive challenge picker using arrow keys.

    Returns the selected index, or None if the user cancels.
    """
    cursor = current_index
    term_height = os.get_terminal_size().lines
    # reserve lines for header (2) + footer (1) + padding (1)
    viewport_size = max(term_height - 4, 5)

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)

        # hide cursor
        sys.stdout.write("\x1b[?25l")

        while True:
            total = len(challenges)
            # compute viewport scroll offset
            if total <= viewport_size:
                scroll_offset = 0
                visible_count = total
            else:
                half = viewport_size // 2
                if cursor < half:
                    scroll_offset = 0
                elif cursor >= total - (viewport_size - half):
                    scroll_offset = total - viewport_size
                else:
                    scroll_offset = cursor - half
                visible_count = viewport_size

            lines: list[str] = []
            lines.append("Challenge Navigation (^G)")
            lines.append("\u2500" * 40)

            for i in range(scroll_offset, scroll_offset + visible_count):
                difficulty, func = challenges[i]
                name = func.__name__
                diff_label = difficulty.name.lower()

                if results[i] == "correct":
                    status = f"\x1b[{Ansi.LGREEN.value}m\u2713\x1b[m"
                else:
                    status = " "

                best_suffix = ""
                if game_state is not None:
                    best = game_state["challenge_bests"].get(name)
                    if best is not None:
                        best_suffix = f"  {_format_time(best)}"

                row = f"  {status} {name:<28s} ({diff_label}){best_suffix}"
                if i == cursor:
                    row = f"\x1b[38;2;180;160;255m{row}\x1b[m"
                elif i == current_index:
                    row = f"\x1b[38;2;227;160;75m{row}\x1b[m"
                lines.append(row)

            lines.append("")
            lines.append("\u2191\u2193 navigate | Enter select | q/^C cancel")

            output = "\x1b[2J\x1b[H" + "\r\n".join(lines)
            sys.stdout.write(output)
            sys.stdout.flush()

            # read input
            ch = sys.stdin.read(1)
            if ch == "\x1b":  # escape sequence or bare Escape
                seq = sys.stdin.read(1)
                if seq == "[":
                    arrow = sys.stdin.read(1)
                    if arrow == "A":  # up
                        cursor = max(0, cursor - 1)
                    elif arrow == "B":  # down
                        cursor = min(total - 1, cursor + 1)
                elif seq == "\x1b":
                    # double-Escape — cancel
                    return None
                # otherwise ignore unknown escape sequences
            elif ch in ("\x03", "q"):  # ^C or q
                return None
            elif ch in ("\r", "\n"):  # Enter
                return cursor
    finally:
        # show cursor, clear screen, restore terminal
        sys.stdout.write("\x1b[?25h\x1b[2J\x1b[H")
        sys.stdout.flush()
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
