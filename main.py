import dis
import random
import inspect
from typing import Callable
from cmyui import printc, Ansi

functions = []

def test_func(f):
    functions.append(f)
    return f

#@test_func
#def f(x: float) -> float:
#    return x * x
#
#@test_func
#def f(x: float, y: float) -> float:
#    return x / y
#
#@test_func
#def f(x: str) -> str:
#    return x.upper()
#
#@test_func
#def f(x: int, y: int) -> str:
#    x *= 2
#    z = 'abc'
#    return z * x ** y

#@test_func
#def f():
#    return [x ** 2 for x in range(16)]

#@test_func
#def f():
#    l = []
#    for i in range(16):
#        l.append(~i & 4)
#    return l

@test_func
def f(x: int, y: str):
    l = [*map(ord,y)]
    for i in range(max(len(y), abs(x ** ~len(y)))):
        l[i] ^= ord(l[i]) * 2

    del i
    return tuple(l)

#@test_func
#def f(x: int):
#    y = 3 ^ x
#    z = 4 * ~y
#    s = 'miniature' * y ** len('lamp')
#    return s[:z] * 5
#
#class A:
#    def __init__(self, x: int, y: str) -> None:
#        self.x = x
#        self.y = y
#    def __repr__(self) -> str:
#        return '{x}: {y}'.format(**self.__dict__)
#
#@test_func
#def f():
#    return A(1, 'dn').__repr__()

#@test_func
#def f():
#  class dn:
#    def __init__(self):
#      return 'b'
#
#    def print(self):
#      return __import__('os').system('echo dn')
#  return dn

right = wrong = 0

def test(f: Callable):
    """Test the user on a single function.
       Returns 1 for correct, -1 for incorrect."""
    # get instructions, and print source
    instructions = [*dis.get_instructions(f)]

    # ignore first line cuz it's the @test_func decorator
    lines, _ = inspect.getsourcelines(f)
    printc(''.join(lines[1:]), Ansi.LBLUE)

    print('Write the disassembly below (line by line).')

    for idx, inst in enumerate(instructions):
        uinput = input(f'{idx * 2}: ').lower().split(' ')
        if uinput[0] != inst.opname.lower():
            printc(f'Incorrect opname - {inst.opname}\n', Ansi.LRED)
            return -1

        # if opcode takes args, check them
        if inst.opcode >= dis.HAVE_ARGUMENT:
            if inst.opcode == dis.opmap['FOR_ITER']:
                # for this, the argument is the offset for
                # the end of the loop, this is pretty hard
                # to figure out, so i'll allow mistakes for now.
                continue

            if len(uinput) != 2:
                printc('Must provide argval!\n', Ansi.LRED)
                return -1
            if str(inst.argval).lower() != uinput[1]:
                printc(f'Incorrect argval - {inst.argval}\n', Ansi.LRED)
                return -1

    printc('Correct!\n', Ansi.LGREEN)
    return 1

while True:
    # test the user on a random function from the list
    result = test(random.choice(functions))

    if result == 1:
        right += 1
    else:
        wrong += 1
