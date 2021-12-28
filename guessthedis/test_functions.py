""" Define functions to be used when testing.

Create, and mark a function with `@test` to enable it for selection.

There are some pre-added examples you can try out as well.
"""
from typing import TypeVar

T = TypeVar("T")


def test(f: T) -> T:
    functions.append(f)
    return f


functions = []


### TEST FUNCTIONS ###

# TODO: a function factory which just randomizes use
#       of some basic operators to create a test?


@test
def f(x: float) -> float:
    return x * x


# @test
# def f(x: str) -> str:
#     return x.upper()

# @test
# def f(x: int, y: int) -> str:
#     x *= 2
#     z = 'abc'
#     return z * x ** y

# @test
# def f(x: int) -> str:
#     y = 3 ^ x
#     z = 4 * ~y
#     s = 'miniature' * y ** len('lamp')
#     return s[:z] * 5

# @test
# def f() -> list[int]:
#     l = []
#     for i in range(16):
#         l.append(~i & 4)
#     return l

# @test
# def f() -> list[int]:
#     return [x ** 2 for x in range(16)]

# @test
# def f(x: int, y: str) -> tuple[int]:
#     l = [*map(ord,y)]
#     for i in range(max(len(y), abs(x ** ~len(y)))):
#         l[i] ^= ord(l[i]) * 2

#     del i
#     return tuple(l)
