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

# These opcodes require a line number argument, which is not realistically
# possible to input by the user, so we'll allow some grace for these.
OPCODES_WITH_LINE_NUMBER_ARGUMENT = frozenset(
    dis.opmap[name]
    for name in (
        "FOR_ITER",
        "JUMP_ABSOLUTE",
        "JUMP_FORWARD",
        "JUMP_BACKWARD",
        "JUMP_IF_FALSE_OR_POP",
        "JUMP_IF_TRUE_OR_POP",
        "JUMP_IF_NOT_EXC_MATCH",
        "JUMP_IF_NOT_NONE",
        "JUMP_IF_NONE",
        "POP_JUMP_IF_FALSE",
        "POP_JUMP_IF_TRUE",
        "POP_JUMP_IF_NONE",
        "POP_JUMP_IF_NOT_NONE",
    )
    if name in dis.opmap
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


# TODO: more generic type for disassembly_target?
def test_user(disassembly_target: Callable[..., Any]) -> bool:
    """Test the user on a single function.
    Returns 1 for correct, -1 for incorrect."""
    ## print the source code of the function for the user
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

    ## prompt the user to disassemble the function
    print("Write the disassembly below (line by line):")

    # TODO: make a higher level version of this where i can disassemble
    # the constants within the function i am disassembling, so that we
    # can define things like functions and classes within them
    instruction_iterator = dis.get_instructions(disassembly_target)

    # quiz them on each operation
    for instruction in instruction_iterator:
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
            user_input_opcode, *user_input_args = user_input_raw.split()
            user_input_opcode = user_input_opcode.lower()

            # validate operation code name
            if user_input_opcode != instruction.opname.lower():
                printc(f"Incorrect opcode value: {user_input_opcode}", Ansi.LRED)
                continue

            # if this opcode expects arguments,
            # parse them from user input & validate
            if (
                instruction.arg is not None
                # for this, the argument is the offset for
                # the end of the loop, this is pretty hard
                # to figure out, so i'll allow mistakes for now.
                and instruction.opcode not in OPCODES_WITH_LINE_NUMBER_ARGUMENT
            ):
                if not user_input_args:
                    printc("Missing argument(s), please try again", Ansi.LRED)
                    continue

                # NOTE: no python instruction uses more than a single argument,
                # so in reality we're only parsing a single argument here.
                user_input_args_str = " ".join(user_input_args)
                if isinstance(instruction.argval, str):
                    # strings are easy - just forward it through
                    user_input_arg = user_input_args_str
                else:
                    # argument type is something different - attempt a literal eval
                    try:
                        user_input_arg = ast.literal_eval(user_input_args_str)

                        # NOTE: ast.literal_eval only supports strings, bytes,
                        # numbers, tuples, lists, dicts, sets, booleans, and None
                        if isinstance(instruction.argval, frozenset):
                            user_input_arg = frozenset(user_input_arg)

                        assert isinstance(user_input_arg, type(instruction.argval))
                    except (
                        AssertionError,
                        # from ast.eval_literal
                        ValueError,
                        TypeError,
                        SyntaxError,
                        MemoryError,
                        RecursionError,
                    ):
                        printc(
                            f"Incorrect argument value: {user_input_args_str}",
                            Ansi.LRED,
                        )
                        continue

                if instruction.argval != user_input_arg:
                    printc(
                        f"Incorrect argument value: {user_input_args_str}",
                        Ansi.LRED,
                    )
                    continue
            else:
                if user_input_args:
                    printc(
                        "Provided argument(s) in invalid context, please try again",
                        Ansi.LRED,
                    )
                    continue

            # user input is all correct
            break

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
