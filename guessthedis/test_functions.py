"""Define functions to be used when testing.

Create, and mark a function with `@test` to enable it for selection.

There are some pre-added examples you can try out as well.
"""

from __future__ import annotations

from typing import Any, Callable, TypeVar

T = TypeVar("T", bound=Callable[..., Any])

functions: list[Callable[[], Any]] = []


def register(f: T) -> T:
    functions.append(f)
    return f


# -- Beginner --


@register
def no_op_pass() -> None:
    pass


@register
def no_op_ellipsis() -> None: ...


@register
def unary_op() -> int:
    x = 5
    return -x


@register
def binary_op() -> int:
    return 5 * 5


@register
def store_primitive_types_fast() -> None:
    i = 5
    f = 3.14
    b = True


@register
def del_variable() -> None:
    x = 42
    del x


@register
def function_call() -> list[str]:
    return dir()


@register
def method_call() -> str:
    return "abc".upper()


@register
def binary_subscr(l: list[int]) -> int:
    return l[0]


@register
def multiple_assignment() -> tuple[int, int, int]:
    a, b, c = 1, 2, 3
    return (a, b, c)


# -- Intermediate --


@register
def if_else() -> int:
    x = True
    if x:
        return 1
    else:
        return 0


@register
def ternary_expression(x: int) -> str:
    return "positive" if x > 0 else "non-positive"


@register
def boolean_short_circuit(a: int, b: int) -> int:
    return a and b or 0


@register
def string_formatting(name: str, age: int) -> str:
    return f"{name} is {age} years old"


@register
def store_collection_types_fast() -> None:
    l = [1, 2, 3]
    t = (1, 2, 3)
    s = {1, 2, 3}
    d = {"a": 1, "b": 2, "c": 3}
    r = range(10)


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
def chained_comparison(x: int) -> bool:
    return 0 < x < 10


@register
def star_unpacking() -> list[int]:
    a, *b, c = [1, 2, 3, 4, 5]
    return b


@register
def raise_exception() -> None:
    raise Exception("This is an exception")


# -- Advanced --


@register
def try_except() -> int:
    try:
        return int("abc")
    except ValueError:
        return -1


@register
def with_statement() -> str:
    with open("/dev/null") as f:
        return f.read()


@register
def walrus_operator(data: list[int]) -> int | None:
    if (n := len(data)) > 3:
        return n
    return None


@register
def generator_function() -> int:
    def gen():
        yield 1
        yield 2
        yield 3

    return sum(gen())


@register
def nested_closure() -> int:
    x = 10

    def inner() -> int:
        return x + 1

    return inner()


@register
def match_statement(command: str) -> str:
    match command:
        case "quit":
            return "goodbye"
        case "hello":
            return "hi there"
        case _:
            return "unknown"


@register
def create_function() -> None:
    def f(x: int, y: int) -> int:
        return x + y


@register
def create_class() -> None:
    class Player:
        def __init__(self, name: str) -> None:
            self.name = name
