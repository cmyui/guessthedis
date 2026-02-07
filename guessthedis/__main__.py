"""guessthedis - gameify learning python disassembly

For an in-detail explanation, please visit
the repo @ https://github.com/cmyui/guessthedis
"""

from __future__ import annotations

import ast
import contextlib
import dis
import inspect
import signal
import subprocess
import tempfile
import types
import textwrap
from enum import IntEnum
from typing import Any
from typing import Callable
from typing import Iterator

from rich.console import Console
from rich.syntax import Syntax

from . import test_functions

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
                user_input_raw = input(f"{instruction.offset}: ").strip()
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


def test_user(disassembly_target: Callable[..., Any]) -> bool:
    """Test the user on a single function."""
    source_code_lines = get_source_code_lines(disassembly_target)
    max_len_line = max(len(line) for line in source_code_lines)

    print("Given the following function:")
    syntax = Syntax(
        code="\n".join(source_code_lines),
        lexer="python",
        theme="monokai",  # TODO: customization?
        line_numbers=True,
        code_width=max_len_line + 1,
    )
    Console().print(syntax)  # TODO: can i create this once and reuse?

    print("Write the disassembly below (line by line):")
    _quiz_instructions(disassembly_target)

    printc("Correct!\n", Ansi.LGREEN)
    return True


def main() -> int:
    if not test_functions.functions:
        printc("No functions marked with @test", Ansi.LRED)
        return 1

    # use gnu readline interface
    # https://docs.python.org/3/library/readline.html
    import readline

    correct = incorrect = 0

    for function in test_functions.functions:
        try:
            disassembled_correctly = test_user(function)
        except KeyboardInterrupt:
            # NOTE: ^C can be used to exit the game early
            print("\x1b[2K", end="\r")  # clear current line
            break

        if disassembled_correctly:
            correct += 1
        else:
            incorrect += 1

    print()  # \n
    print("Thanks for playing! :)\n\nResults\n-------")
    printc(f"Correct: {correct}", Ansi.LGREEN)
    printc(f"Incorrect: {incorrect}", Ansi.LRED)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
