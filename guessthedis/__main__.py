""" guessthedis - gameify learning python disassembly

For an in-detail explanation, please visit
the repo @ https://github.com/cmyui/guessthedis
"""
from __future__ import annotations

import contextlib
import dis
import inspect
import signal
import subprocess
import tempfile
import textwrap
from enum import IntEnum
from typing import Callable

from . import test_functions

__author__ = "Joshua Smith (cmyui)"
__email__ = "cmyuiosu@gmail.com"


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
def ignore_sigint():
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    try:
        yield
    finally:
        signal.signal(signal.SIGINT, signal.default_int_handler)


def printc(string: str, col: Ansi) -> None:
    """Print out a given string, with a colour."""
    print(f"{col!r}{string}\x1b[m")


# TODO: more generic type for disassembly_target?
def test_user(disassembly_target: Callable[..., object]) -> bool:
    """Test the user on a single function.
    Returns 1 for correct, -1 for incorrect."""
    ## print the source code of the function for the user
    source_lines, _ = inspect.getsourcelines(disassembly_target)

    # (remove decorators from output)
    start_line = 0
    while source_lines[start_line].lstrip().startswith("@"):
        start_line += 1

    source_code = "".join(source_lines[start_line:])
    printc(textwrap.dedent(source_code), Ansi.LBLUE)

    ## prompt the user to disassemble the function
    print("Write the disassembly below (line by line).")

    # TODO: make a higher level version of this where i can disassemble
    # the constants within the function i am disassembling, so that we
    # can define things like functions and classes within them
    instruction_iterator = dis.get_instructions(disassembly_target)

    # quiz them on each operation
    for idx, instruction in enumerate(instruction_iterator):
        while True:
            try:
                user_input_raw = input(f"{idx * 2}: ").strip().lower()
            except EOFError:
                # NOTE: ^D can be used to show the correct disassembly
                print("\x1b[2K", end="\r")  # clear current line

                # we'll show the disassembly "cheatsheet" in gnu's less interface
                # to do this, we'll need to write the contents to a temporary file
                with tempfile.NamedTemporaryFile("w") as f:
                    # write the disassembly contents to the file
                    dis.dis(disassembly_target, file=f)
                    f.flush()

                    # open the file in the less interface
                    with ignore_sigint():
                        subprocess.run(["less", f.name])
            else:
                if user_input_raw:
                    user_input = user_input_raw.split()
                    break
                else:
                    print("Invalid input, please try again")

        if user_input[0] != instruction.opname.lower():
            printc(f"Incorrect opname - {instruction.opname}\n", Ansi.LRED)
            return False

        # if opcode takes args, check them
        if instruction.opcode >= dis.HAVE_ARGUMENT:
            if instruction.opcode == dis.opmap["FOR_ITER"]:
                # for this, the argument is the offset for
                # the end of the loop, this is pretty hard
                # to figure out, so i'll allow mistakes for now.
                continue

            if len(user_input) != 2:
                printc("Must provide argval!\n", Ansi.LRED)
                return False

            if str(instruction.argval).lower() != user_input[1]:
                printc(f"Incorrect argval - {instruction.argval}\n", Ansi.LRED)
                return False

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
