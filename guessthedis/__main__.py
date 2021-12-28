""" guessthedis - gameify learning python disassembly

For an in-detail explanation, please visit
the repo @ https://github.com/cmyui/guessthedis
"""

__author__ = "Joshua Smith (cmyui)"
__email__ = "cmyuiosu@gmail.com"

import dis
import inspect
import random
from typing import Callable

from cmyui.logging import Ansi
from cmyui.logging import printc

from . import test_functions


def test_user(f: Callable[..., object]) -> bool:
    """Test the user on a single function.
       Returns 1 for correct, -1 for incorrect."""
    # get instructions, and print source
    instructions = [*dis.get_instructions(f)]

    # ignore first line (it's the @test_func decorator)
    lines, _ = inspect.getsourcelines(f)
    printc(''.join(lines[1:]), Ansi.LBLUE)

    print('Write the disassembly below (line by line).')

    for idx, inst in enumerate(instructions):
        uinput = input(f'{idx * 2}: ').lower().split(' ')
        if uinput[0] != inst.opname.lower():
            printc(f'Incorrect opname - {inst.opname}\n', Ansi.LRED)
            return False

        # if opcode takes args, check them
        if inst.opcode >= dis.HAVE_ARGUMENT:
            if inst.opcode == dis.opmap['FOR_ITER']:
                # for this, the argument is the offset for
                # the end of the loop, this is pretty hard
                # to figure out, so i'll allow mistakes for now.
                continue

            if len(uinput) != 2:
                printc('Must provide argval!\n', Ansi.LRED)
                return False
            if str(inst.argval).lower() != uinput[1]:
                printc(f'Incorrect argval - {inst.argval}\n', Ansi.LRED)
                return False

    printc('Correct!\n', Ansi.LGREEN)
    return True

def main() -> int:
    if not test_functions.functions:
        printc("No functions marked with @test_func", Ansi.LRED)
        return 1

    correct = incorrect = 0

    while True:
        # test the user on a random function from the list
        # TODO: teach the player & increase difficulty over time
        function = random.choice(test_functions.functions)

        try:
            disassembled_correctly = test_user(function)
        except (KeyboardInterrupt, EOFError) as exc:
            if isinstance(exc, EOFError):
                # TODO: use ^D to show correct disassembly
                pass
            else:
                # TODO: perhaps remove the ^C from terminal?
                pass
            break
        except:
            raise

        if disassembled_correctly:
            correct += 1
        else:
            incorrect += 1

    print('\n\nThanks for playing! :)\n\nResults\n-------')
    printc(f'Correct: {correct}', Ansi.LGREEN)
    printc(f'Incorrect: {incorrect}', Ansi.LRED)


    return 0


if __name__ == '__main__':
    raise SystemExit(main())
