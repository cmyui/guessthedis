""" Define functions to be used when testing.

Create, and mark a function with `@test_func` to enable it for selection.

There are some pre-added examples you can try out as well.
"""
from typing import Callable

functions = []

def test_func(f: Callable[..., object]) -> Callable[..., object]:
    functions.append(f)
    return f

### TEST FUNCTIONS ###

# TODO: a function factory which just randomizes use
#       of some basic operators to create a test?

@test_func
def f(x: float) -> float:
    return x * x

# @test_func
# def f(x: str) -> str:
#     return x.upper()

# @test_func
# def f(x: int, y: int) -> str:
#     x *= 2
#     z = 'abc'
#     return z * x ** y

# @test_func
# def f(x: int) -> str:
#     y = 3 ^ x
#     z = 4 * ~y
#     s = 'miniature' * y ** len('lamp')
#     return s[:z] * 5

# @test_func
# def f() -> list[int]:
#     l = []
#     for i in range(16):
#         l.append(~i & 4)
#     return l

# @test_func
# def f() -> list[int]:
#     return [x ** 2 for x in range(16)]

# @test_func
# def f(x: int, y: str) -> tuple[int]:
#     l = [*map(ord,y)]
#     for i in range(max(len(y), abs(x ** ~len(y)))):
#         l[i] ^= ord(l[i]) * 2

#     del i
#     return tuple(l)
