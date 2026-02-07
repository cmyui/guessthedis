"""Define functions to be used when testing.

Create, and mark a function with `@register(Difficulty.LEVEL)` to enable it
for selection.

There are some pre-added examples you can try out as well.
"""

from enum import IntEnum
from typing import Any
from typing import Callable
from typing import TypeVar

T = TypeVar("T", bound=Callable[..., Any])


class Difficulty(IntEnum):
    BEGINNER = 1
    INTERMEDIATE = 2
    ADVANCED = 3


functions: list[tuple[Difficulty, Callable[..., Any]]] = []


def register(difficulty: Difficulty) -> Callable[[T], T]:
    def decorator(f: T) -> T:
        functions.append((difficulty, f))
        return f

    return decorator


@register(Difficulty.BEGINNER)
def no_op_pass() -> None:
    pass


@register(Difficulty.BEGINNER)
def no_op_ellipsis() -> None: ...


@register(Difficulty.BEGINNER)
def unary_op() -> int:
    x = 5
    return -x


@register(Difficulty.BEGINNER)
def binary_op() -> int:
    return 5 * 5


@register(Difficulty.BEGINNER)
def store_primitive_types_fast() -> None:
    i = 5
    f = 3.14
    b = True


@register(Difficulty.BEGINNER)
def del_variable() -> None:
    x = 42
    del x


@register(Difficulty.BEGINNER)
def function_call() -> list[str]:
    return dir()


@register(Difficulty.BEGINNER)
def method_call() -> str:
    return "abc".upper()


@register(Difficulty.BEGINNER)
def binary_subscr(l: list[int]) -> int:
    return l[0]


@register(Difficulty.BEGINNER)
def multiple_assignment() -> tuple[int, int, int]:
    a, b, c = 1, 2, 3
    return (a, b, c)


@register(Difficulty.INTERMEDIATE)
def if_else() -> int:
    x = True
    if x:
        return 1
    else:
        return 0


@register(Difficulty.INTERMEDIATE)
def ternary_expression(x: int) -> str:
    return "positive" if x > 0 else "non-positive"


@register(Difficulty.INTERMEDIATE)
def boolean_short_circuit(a: int, b: int) -> int:
    return a and b or 0


@register(Difficulty.INTERMEDIATE)
def string_formatting(name: str, age: int) -> str:
    return f"{name} is {age} years old"


@register(Difficulty.INTERMEDIATE)
def store_collection_types_fast() -> None:
    l = [1, 2, 3]
    t = (1, 2, 3)
    s = {1, 2, 3}
    d = {"a": 1, "b": 2, "c": 3}
    r = range(10)


@register(Difficulty.INTERMEDIATE)
def for_loop() -> int:
    total = 0
    for i in range(10):
        total += i
    return total


@register(Difficulty.INTERMEDIATE)
def while_loop() -> int:
    total = 0
    while total < 10:
        total += total
    return total


@register(Difficulty.INTERMEDIATE)
def list_comprehension() -> list[int]:
    r = range(5)
    l = [i * 2 for i in r]
    return l


@register(Difficulty.INTERMEDIATE)
def dict_comprehension() -> dict[int, int]:
    r = range(5)
    l = {i: i * 2 for i in r}
    return l


@register(Difficulty.INTERMEDIATE)
def chained_comparison(x: int) -> bool:
    return 0 < x < 10


@register(Difficulty.INTERMEDIATE)
def star_unpacking() -> list[int]:
    a, *b, c = [1, 2, 3, 4, 5]
    return b


@register(Difficulty.INTERMEDIATE)
def raise_exception() -> None:
    raise Exception("This is an exception")


@register(Difficulty.ADVANCED)
def try_except() -> int:
    try:
        return int("abc")
    except ValueError:
        return -1


@register(Difficulty.ADVANCED)
def with_statement() -> str:
    with open("/dev/null") as f:
        return f.read()


@register(Difficulty.ADVANCED)
def walrus_operator(data: list[int]) -> int | None:
    if (n := len(data)) > 3:
        return n
    return None


@register(Difficulty.ADVANCED)
def generator_function() -> int:
    def gen():
        yield 1
        yield 2
        yield 3

    return sum(gen())


@register(Difficulty.ADVANCED)
def nested_closure() -> int:
    x = 10

    def inner() -> int:
        return x + 1

    return inner()


@register(Difficulty.ADVANCED)
def match_statement(command: str) -> str:
    match command:
        case "quit":
            return "goodbye"
        case "hello":
            return "hi there"
        case _:
            return "unknown"


@register(Difficulty.ADVANCED)
def create_function() -> None:
    def f(x: int, y: int) -> int:
        return x + y


@register(Difficulty.ADVANCED)
def create_class() -> None:
    class Player:
        def __init__(self, name: str) -> None:
            self.name = name
