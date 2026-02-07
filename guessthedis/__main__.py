"""guessthedis - gameify learning python disassembly

For an in-detail explanation, please visit
the repo @ https://github.com/cmyui/guessthedis
"""

import argparse
import ast
import contextlib
import dis
import inspect
import os
import signal
import subprocess
import sys
import tempfile
import termios
import textwrap
import tty
import types
from enum import IntEnum
from typing import Any
from typing import Callable
from typing import Iterator

from rich.console import Console
from rich.syntax import Syntax

from . import test_functions
from .test_functions import Difficulty

__author__ = "Joshua Smith (cmyui)"
__email__ = "cmyuiosu@gmail.com"

# Opcodes whose arguments are not viable for user input.
#
# Jump opcodes (dis.hasjrel, dis.hasjabs) have byte-offset targets
# that change with any code modification. These are covered
# automatically across all Python versions via the dis module.
#
# Additionally, some opcodes have non-literal argvals:
# - FORMAT_VALUE (3.10-3.12): argval is a (conversion, has_format_spec) tuple
# - CONVERT_VALUE (3.13-3.14): argval is a builtin function object (e.g. repr)
OPCODES_WITH_UNPARSEABLE_ARGUMENT = (
    frozenset(dis.hasjrel)
    | frozenset(dis.hasjabs)
    | frozenset(
        dis.opmap[name]
        for name in (
            "CONVERT_VALUE",  # 3.13+
            "FORMAT_VALUE",  # 3.10-3.12
        )
        if name in dis.opmap
    )
)


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


def printc(string: str, col: Ansi, end="\n") -> None:
    """Print out a given string, with a colour."""
    print(f"{col!r}{string}\x1b[m", end=end)


class NavigationRequested(Exception):
    """Raised when the user presses ^G to open the challenge picker."""


_input_history: list[str] = []


def _read_line(prompt: str) -> str:
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


def get_source_code_lines(disassembly_target: Callable[..., Any]) -> list[str]:
    """Get the source code of a function."""
    source_lines, _ = inspect.getsourcelines(disassembly_target)

    # (remove decorators from output)
    start_line = 0
    while source_lines[start_line].lstrip().startswith("@"):
        start_line += 1

    return textwrap.dedent("".join(source_lines[start_line:])).split("\n")


def _parse_user_arg(
    raw: str,
    expected_argval: object,
) -> tuple[bool, object]:
    """Parse a user-provided argument string and compare to the expected value.

    Returns (success, parsed_value).
    """
    # try ast.literal_eval first (handles quoted strings, numbers, collections)
    try:
        parsed = ast.literal_eval(raw)

        if isinstance(expected_argval, frozenset):
            parsed = frozenset(parsed)

        if not isinstance(parsed, type(expected_argval)):
            return False, None

        return parsed == expected_argval, parsed
    except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
        pass

    # fall back to bare identifier (e.g. variable names in LOAD_FAST)
    if isinstance(expected_argval, str) and raw == expected_argval:
        return True, raw

    return False, None


def _quiz_instructions(
    disassembly_target: Callable[..., Any] | types.CodeType,
) -> None:
    """Quiz the user on each instruction in the disassembly target.

    Recurses into nested code objects (inner functions, classes, etc.)
    after the outer disassembly is complete.
    """
    instruction_iterator = dis.get_instructions(disassembly_target)
    nested_code_objects: list[types.CodeType] = []

    for instruction in instruction_iterator:
        # collect nested code objects for recursive quizzing
        if isinstance(instruction.argval, types.CodeType):
            nested_code_objects.append(instruction.argval)

        # loop indefinitely to get valid user input
        while True:
            try:
                user_input_raw = _read_line(f"{instruction.offset}: ").strip()
            except EOFError:
                # NOTE: ^D can be used to show the correct disassembly "cheatsheet"
                print("\x1b[2K", end="\r")  # clear current line

                # we'll show the disassembly "cheatsheet" in gnu's less interface
                # to do this, we'll need to write the contents to a temporary file
                # TODO: how common is the less command? should i have a fallback?
                with tempfile.NamedTemporaryFile("w") as f:
                    # always write opcode reference documentation at the top of output
                    f.write(
                        "python3 opcode reference\n"
                        "------------------------\n"
                        "- https://docs.python.org/3/library/dis.html#python-bytecode-instructions"
                        "\n\n",
                    )

                    # write the disassembly contents to the file
                    dis.dis(disassembly_target, file=f)

                    # make sure all contents have been flushed to disk
                    f.flush()

                    # open the file in the less interface
                    with ignore_sigint():
                        subprocess.run(["less", f.name])

                continue

            if not user_input_raw:
                printc("Invalid input, please try again", Ansi.LRED)
                continue

            # user has provided some input - check if it's correct
            # split only on the first space to preserve whitespace in arguments
            parts = user_input_raw.split(maxsplit=1)
            user_input_opcode = parts[0].lower()
            user_input_arg_raw = parts[1] if len(parts) > 1 else None

            # validate operation code name
            if user_input_opcode != instruction.opname.lower():
                printc(f"Incorrect opcode value: {user_input_opcode}", Ansi.LRED)
                continue

            # if this opcode expects arguments,
            # parse them from user input & validate
            expects_user_arg = (
                instruction.arg is not None
                and instruction.opcode not in OPCODES_WITH_UNPARSEABLE_ARGUMENT
                and not isinstance(instruction.argval, types.CodeType)
            )
            if expects_user_arg:
                if user_input_arg_raw is None:
                    printc("Missing argument(s), please try again", Ansi.LRED)
                    continue

                correct, _ = _parse_user_arg(
                    user_input_arg_raw,
                    instruction.argval,
                )
                if not correct:
                    printc(
                        f"Incorrect argument value: {user_input_arg_raw}",
                        Ansi.LRED,
                    )
                    continue
            else:
                if user_input_arg_raw is not None:
                    printc(
                        "Provided argument(s) in invalid context, please try again",
                        Ansi.LRED,
                    )
                    continue

            # user input is all correct
            break

    # recurse into nested code objects (inner functions, classes, etc.)
    for code_obj in nested_code_objects:
        code_name = getattr(code_obj, "co_qualname", code_obj.co_name)
        print(f"\nDisassembly of {code_name}:")
        _quiz_instructions(code_obj)


def _pick_challenge(
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


def test_user(
    disassembly_target: Callable[..., Any],
    *,
    console: Console,
) -> bool:
    """Test the user on a single function."""
    source_code_lines = get_source_code_lines(disassembly_target)
    max_len_line = max(len(line) for line in source_code_lines)

    print("Given the following function:")
    syntax = Syntax(
        code="\n".join(source_code_lines),
        lexer="python",
        theme="monokai",
        line_numbers=True,
        code_width=max_len_line + 1,
    )
    console.print(syntax)

    print("Write the disassembly below (line by line):")
    _quiz_instructions(disassembly_target)

    printc("Correct!\n", Ansi.LGREEN)
    return True


DIFFICULTY_CHOICES = [
    "beginner",
    "intermediate",
    "advanced",
    "ridiculous",
    "beginner+",
    "intermediate+",
    "advanced+",
    "ridiculous+",
]


def _parse_difficulty_filter(raw: str) -> tuple[Difficulty, bool]:
    """Parse a difficulty flag value into (level, and_above)."""
    and_above = raw.endswith("+")
    name = raw.removesuffix("+").upper()
    return Difficulty[name], and_above


def main() -> int:
    parser = argparse.ArgumentParser(description="guessthedis")
    parser.add_argument(
        "-d",
        "--difficulty",
        choices=DIFFICULTY_CHOICES,
        default=None,
        help="filter functions by difficulty level (append '+' for that level and above)",
    )
    args = parser.parse_args()

    if args.difficulty is not None:
        min_difficulty, and_above = _parse_difficulty_filter(args.difficulty)
        filtered = [
            (d, f)
            for d, f in test_functions.functions
            if (d >= min_difficulty if and_above else d == min_difficulty)
        ]
    else:
        filtered = test_functions.functions

    if not filtered:
        printc("No functions matched the given difficulty", Ansi.LRED)
        return 1

    console = Console()
    results: list[str] = ["pending"] * len(filtered)
    current_index = 0

    while current_index < len(filtered):
        printc("(^D = cheatsheet, ^G = navigate, ^C = exit)", Ansi.GRAY)
        print()
        _difficulty, function = filtered[current_index]
        try:
            test_user(function, console=console)
            results[current_index] = "correct"
            current_index += 1
        except KeyboardInterrupt:
            print("\x1b[2K", end="\r")
            break
        except NavigationRequested:
            picked = _pick_challenge(filtered, results, current_index)
            if picked is not None:
                current_index = picked

    correct = results.count("correct")
    remaining = len(filtered) - correct

    print()
    print("Thanks for playing! :)\n\nResults\n-------")
    printc(f"Correct: {correct}", Ansi.LGREEN)
    printc(f"Remaining: {remaining}", Ansi.GRAY)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
