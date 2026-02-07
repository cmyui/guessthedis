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


def _is_word_char(ch: str) -> bool:
    return ch.isalnum() or ch == "_"


def _word_boundary_back(buf: list[str], pos: int) -> int:
    """Find the start of the previous word (non-alnum/underscore boundary)."""
    while pos > 0 and not _is_word_char(buf[pos - 1]):
        pos -= 1
    while pos > 0 and _is_word_char(buf[pos - 1]):
        pos -= 1
    return pos


def _word_boundary_fwd(buf: list[str], pos: int) -> int:
    """Find the end of the next word (non-alnum/underscore boundary)."""
    while pos < len(buf) and _is_word_char(buf[pos]):
        pos += 1
    while pos < len(buf) and not _is_word_char(buf[pos]):
        pos += 1
    return pos


def _whitespace_boundary_back(buf: list[str], pos: int) -> int:
    """Find start of previous whitespace-delimited word (for Ctrl+W)."""
    while pos > 0 and buf[pos - 1] == " ":
        pos -= 1
    while pos > 0 and buf[pos - 1] != " ":
        pos -= 1
    return pos


def _read_csi_sequence(fd: int) -> str:
    """Read a CSI escape sequence after ESC [ has been consumed.

    CSI sequences end with a byte in the range 0x40-0x7E.
    Returns the parameter + final bytes (e.g. "A", "3~", "1;5D").
    """
    parts: list[str] = []
    while True:
        c = sys.stdin.read(1)
        parts.append(c)
        if 0x40 <= ord(c) <= 0x7E:
            break
        if len(parts) > 8:
            break
    return "".join(parts)


def read_line(prompt: str) -> str:
    """Read a line of input with readline-style editing.

    Supports cursor movement, word operations, history navigation,
    reverse incremental search (^R), and game-specific hotkeys
    (^G = navigation, ^D = cheatsheet, ^C = exit).
    """
    sys.stdout.write(prompt)
    sys.stdout.flush()

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        buf: list[str] = []
        cursor = 0
        history_index = len(_input_history)
        saved_line = ""

        def _redraw() -> None:
            sys.stdout.write(f"\r{prompt}{''.join(buf)}\x1b[0K")
            if cursor < len(buf):
                sys.stdout.write(f"\x1b[{len(buf) - cursor}D")
            sys.stdout.flush()

        def _set_line(content: str) -> None:
            nonlocal cursor
            buf.clear()
            buf.extend(content)
            cursor = len(buf)
            _redraw()

        def _clear_and_raise(exc: BaseException) -> None:
            sys.stdout.write("\x1b[2K\r")
            sys.stdout.flush()
            raise exc

        def _delete_back_to(new_pos: int) -> None:
            nonlocal cursor
            del buf[new_pos:cursor]
            cursor = new_pos
            _redraw()

        def _reverse_search() -> None:
            """Reverse incremental history search (Ctrl+R)."""
            nonlocal cursor
            query: list[str] = []
            match_index = len(_input_history)
            match_text = ""

            def _draw_search() -> None:
                query_str = "".join(query)
                display = f"(reverse-i-search)'{query_str}': {match_text}"
                sys.stdout.write(f"\x1b[2K\r{display}")
                sys.stdout.flush()

            def _find_backward() -> bool:
                nonlocal match_index, match_text
                query_str = "".join(query)
                if not query_str:
                    match_text = ""
                    return False
                for i in range(match_index - 1, -1, -1):
                    if query_str in _input_history[i]:
                        match_index = i
                        match_text = _input_history[i]
                        return True
                return False

            _draw_search()

            while True:
                sch = sys.stdin.read(1)
                if sch == "\x12":  # ^R again — next earlier match
                    _find_backward()
                    _draw_search()
                elif sch == "\x07":  # ^G — cancel search, restore original
                    _redraw()
                    return
                elif sch == "\x03":  # ^C
                    _clear_and_raise(KeyboardInterrupt())
                elif sch in ("\r", "\n"):  # Enter — accept and submit
                    if match_text:
                        _set_line(match_text)
                    else:
                        _redraw()
                    return
                elif sch == "\x1b":  # Escape — accept match, continue editing
                    if match_text:
                        _set_line(match_text)
                    else:
                        _redraw()
                    return
                elif sch == "\x7f":  # Backspace — remove from query
                    if query:
                        query.pop()
                        match_index = len(_input_history)
                        match_text = ""
                        _find_backward()
                    _draw_search()
                elif sch >= " ":  # printable — add to query
                    query.append(sch)
                    _find_backward()
                    _draw_search()

        while True:
            ch = sys.stdin.read(1)

            # game-specific hotkeys
            if ch == "\x07":  # ^G — navigation picker
                _clear_and_raise(NavigationRequested())
            elif ch == "\x04":  # ^D — cheatsheet
                _clear_and_raise(EOFError())
            elif ch == "\x03":  # ^C — exit
                _clear_and_raise(KeyboardInterrupt())

            # cursor movement
            elif ch == "\x01":  # ^A — beginning of line
                cursor = 0
                _redraw()
            elif ch == "\x02":  # ^B — back one char
                if cursor > 0:
                    cursor -= 1
                    sys.stdout.write("\x1b[D")
                    sys.stdout.flush()
            elif ch == "\x05":  # ^E — end of line
                cursor = len(buf)
                _redraw()
            elif ch == "\x06":  # ^F — forward one char
                if cursor < len(buf):
                    cursor += 1
                    sys.stdout.write("\x1b[C")
                    sys.stdout.flush()

            # deletion
            elif ch == "\x0b":  # ^K — kill to end of line
                del buf[cursor:]
                _redraw()
            elif ch == "\x15":  # ^U — kill to beginning of line
                _delete_back_to(0)
            elif ch == "\x17":  # ^W — delete word backward (whitespace boundary)
                if cursor > 0:
                    _delete_back_to(_whitespace_boundary_back(buf, cursor))
            elif ch == "\x08":  # Ctrl+Backspace — delete word backward
                if cursor > 0:
                    _delete_back_to(_whitespace_boundary_back(buf, cursor))

            # search
            elif ch == "\x12":  # ^R — reverse incremental search
                _reverse_search()

            # escape sequences
            elif ch == "\x1b":
                seq = sys.stdin.read(1)
                if seq == "[":
                    csi = _read_csi_sequence(fd)
                    if csi == "A":  # Up — history backward
                        if history_index > 0:
                            if history_index == len(_input_history):
                                saved_line = "".join(buf)
                            history_index -= 1
                            _set_line(_input_history[history_index])
                    elif csi == "B":  # Down — history forward
                        if history_index < len(_input_history):
                            history_index += 1
                            if history_index == len(_input_history):
                                _set_line(saved_line)
                            else:
                                _set_line(_input_history[history_index])
                    elif csi == "C":  # Right
                        if cursor < len(buf):
                            cursor += 1
                            sys.stdout.write("\x1b[C")
                            sys.stdout.flush()
                    elif csi == "D":  # Left
                        if cursor > 0:
                            cursor -= 1
                            sys.stdout.write("\x1b[D")
                            sys.stdout.flush()
                    elif csi == "H" or csi == "1~":  # Home
                        cursor = 0
                        _redraw()
                    elif csi == "F" or csi == "4~":  # End
                        cursor = len(buf)
                        _redraw()
                    elif csi == "3~":  # Delete
                        if cursor < len(buf):
                            del buf[cursor]
                            _redraw()
                    elif csi in ("1;5D", "1;3D"):  # Ctrl+Left / Alt+Left
                        cursor = _word_boundary_back(buf, cursor)
                        _redraw()
                    elif csi in ("1;5C", "1;3C"):  # Ctrl+Right / Alt+Right
                        cursor = _word_boundary_fwd(buf, cursor)
                        _redraw()
                elif seq == "b":  # Alt+B — back one word
                    cursor = _word_boundary_back(buf, cursor)
                    _redraw()
                elif seq == "f":  # Alt+F — forward one word
                    cursor = _word_boundary_fwd(buf, cursor)
                    _redraw()
                elif seq == "\x7f":  # Alt+Backspace — delete word backward
                    if cursor > 0:
                        _delete_back_to(_word_boundary_back(buf, cursor))
                elif seq == "d":  # Alt+D — delete word forward
                    if cursor < len(buf):
                        new_pos = _word_boundary_fwd(buf, cursor)
                        del buf[cursor:new_pos]
                        _redraw()

            # enter
            elif ch in ("\r", "\n"):
                sys.stdout.write("\r\n")
                sys.stdout.flush()
                line = "".join(buf)
                if line:
                    _input_history.append(line)
                return line

            # backspace
            elif ch == "\x7f":
                if cursor > 0:
                    cursor -= 1
                    del buf[cursor]
                    _redraw()

            # printable characters
            elif ch >= " ":
                buf.insert(cursor, ch)
                cursor += 1
                _redraw()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def pick_challenge(
    challenges: list[tuple[Difficulty, Callable[..., Any]]],
    results: list[str],
    current_index: int,
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

                row = f"  {status} {name:<28s} ({diff_label})"
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
