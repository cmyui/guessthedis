""" guessthedis - gameify learning python disassembly

For an in-detail explanation, please visit
the repo @ https://github.com/cmyui/guessthedis
"""
from __future__ import annotations

import dis
import inspect
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


def printc(string: str, col: Ansi) -> None:
    """Print out a given string, with a colour."""
    print(f"{col!r}{string}\x1b[m")


def test_user(f: Callable[..., object]) -> bool:
    """Test the user on a single function.
    Returns 1 for correct, -1 for incorrect."""
    ## print the source code of the function for the user
    source_lines, _ = inspect.getsourcelines(f)

    # (remove decorators from output)
    start_line = 0
    while source_lines[start_line].lstrip().startswith("@"):
        start_line += 1

    source_code = "".join(source_lines[start_line:])
    printc(textwrap.dedent(source_code), Ansi.LBLUE)

    ## prompt the user to disassemble the function
    print("Write the disassembly below (line by line).")

    # quiz them on each operation
    for idx, inst in enumerate(dis.get_instructions(f)):
        uinput = input(f"{idx * 2}: ").lower().split(" ")
        if uinput[0] != inst.opname.lower():
            printc(f"Incorrect opname - {inst.opname}\n", Ansi.LRED)
            return False

        # if opcode takes args, check them
        if inst.opcode >= dis.HAVE_ARGUMENT:
            if inst.opcode == dis.opmap["FOR_ITER"]:
                # for this, the argument is the offset for
                # the end of the loop, this is pretty hard
                # to figure out, so i'll allow mistakes for now.
                continue

            if len(uinput) != 2:
                printc("Must provide argval!\n", Ansi.LRED)
                return False

            if str(inst.argval).lower() != uinput[1]:
                printc(f"Incorrect argval - {inst.argval}\n", Ansi.LRED)
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
            # NOTE: ^C can be used to quit out of the game
            print("\x1b[2K", end="\r")  # clear current line
            break
        except EOFError:
            # NOTE: ^D can be used to show the correct disassembly
            print("\x1b[2K", end="\r")  # clear current line
            print()  # \n
            printc("Correct disassembly", Ansi.LMAGENTA)
            dis.dis(function)
            print()  # \n

            try:
                input("Press enter to continue...")
            except (KeyboardInterrupt, EOFError):
                # treat ^C and ^D the same as enter
                pass

            print()  # \n
            continue  # don't count towards score

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
