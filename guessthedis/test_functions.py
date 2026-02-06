""" Define functions to be used when testing.

Create, and mark a function with `@test` to enable it for selection.

There are some pre-added examples you can try out as well.
"""
from __future__ import annotations

from typing import Any, Callable, TypeVar

T = TypeVar("T", bound=Callable[..., Any])

functions: list[Callable[..., Any]] = []

def register(f: T) -> T:
    functions.append(f)
    return f


def no_op_pass() -> None:
    pass


def no_op_ellipsis() -> None: ...


@register
def unary_op() -> int:
    x = 5
    return -x


@register
def binary_op() -> int:
    return 5 * 5


@register
def function_call() -> list[str]:
    return dir()


@register
def method_call() -> str:
    return "abc".upper()


@register
def if_else() -> int:
    x = True
    if x:
        return 1
    else:
        return 0


@register
def store_primitive_types_fast() -> None:
    i = 5
    f = 3.14
    b = True


@register
def store_collection_types_fast() -> None:
    l = [1, 2, 3]
    t = (1, 2, 3)
    s = {1, 2, 3}
    d = {"a": 1, "b": 2, "c": 3}
    r = range(10)


@register
def binary_subscr(l: list[int]) -> int:
    return l[0]


@register
def for_loop() -> int:
    total = 0
    for i in range(10):
        total += i
    return total


@register
def while_loop() -> int:
    total = 0
    while total < 10:
        total += total
    return total


@register
def list_comprehension() -> list[int]:
    r = range(5)
    l = [i * 2 for i in r]
    return l


@register
def dict_comprehension() -> dict[int, int]:
    r = range(5)
    l = {i: i * 2 for i in r}
    return l


@register
def raise_exception() -> None:
    raise Exception("This is an exception")


# TODO: add support for multiple disassembly definitions
#       so we can do cool stuff like functions and classes

# @register
# def create_function() -> None:
#     def f(x: int, y: int) -> int:
#         return x + y


# @register
# def create_class() -> None:
#     class Player:
#         def __init__(self, name: str) -> None:
#             self.name = name
