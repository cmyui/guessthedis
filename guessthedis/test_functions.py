"""Define functions to be used when testing.

Create, and mark a function with `@register(Difficulty.LEVEL)` to enable it
for selection.

There are some pre-added examples you can try out as well.
"""

import sys
import textwrap
from enum import IntEnum
from typing import Any
from typing import Callable
from typing import TypeVar

T = TypeVar("T", bound=Callable[..., Any])


class Difficulty(IntEnum):
    BEGINNER = 1
    INTERMEDIATE = 2
    ADVANCED = 3
    RIDICULOUS = 4


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


@register(Difficulty.BEGINNER)
def membership_test(x: int, items: list[int]) -> bool:
    return x in items


@register(Difficulty.BEGINNER)
def identity_test(x: object) -> bool:
    return x is None


@register(Difficulty.BEGINNER)
def assert_statement(x: int) -> None:
    assert x > 0, "must be positive"


@register(Difficulty.BEGINNER)
def bitwise_invert(x: int) -> int:
    return ~x


@register(Difficulty.BEGINNER)
def import_statement() -> str:
    from os.path import join

    return join("a", "b")


@register(Difficulty.BEGINNER)
def lambda_expression() -> int:
    f = lambda x, y: x + y
    return f(1, 2)


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


@register(Difficulty.INTERMEDIATE)
def set_comprehension() -> set[int]:
    r = range(5)
    s = {i * 2 for i in r}
    return s


@register(Difficulty.INTERMEDIATE)
def generator_expression() -> int:
    return sum(x * 2 for x in range(5))


@register(Difficulty.INTERMEDIATE)
def for_else() -> int:
    for i in range(10):
        if i == 5:
            break
    else:
        return -1
    return i


@register(Difficulty.INTERMEDIATE)
def subscript_store_delete() -> None:
    d: dict[str, str] = {}
    d["key"] = "value"
    del d["key"]


@register(Difficulty.INTERMEDIATE)
def raise_from() -> None:
    try:
        pass
    except Exception as e:
        raise RuntimeError("wrapped") from e


@register(Difficulty.INTERMEDIATE)
def try_finally() -> int:
    try:
        x = 1
    finally:
        x = 0
    return x


@register(Difficulty.INTERMEDIATE)
def global_statement() -> None:
    global _global_var
    _global_var = 42


@register(Difficulty.INTERMEDIATE)
def nonlocal_statement() -> int:
    x = 10

    def inner() -> int:
        nonlocal x
        x += 1
        return x

    return inner()


@register(Difficulty.INTERMEDIATE)
def star_call() -> None:
    args = (1, 2, 3)
    kwargs = {"sep": "-"}
    print(*args, **kwargs)


@register(Difficulty.INTERMEDIATE)
def fstring_format_spec(value: float, width: int, precision: int) -> str:
    return f"{value:{width}.{precision}f}"


@register(Difficulty.ADVANCED)
def try_except() -> int:
    try:
        return int("abc")
    except ValueError:
        return -1


@register(Difficulty.ADVANCED)
def try_except_multiple() -> int:
    try:
        return int("abc")
    except ValueError:
        return -1
    except TypeError:
        return -2


@register(Difficulty.ADVANCED)
def try_except_tuple() -> int:
    try:
        return int("abc")
    except (ValueError, TypeError):
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


@register(Difficulty.ADVANCED)
async def async_await() -> None:
    import asyncio

    await asyncio.sleep(0)


@register(Difficulty.ADVANCED)
async def async_for(aiter: Any) -> None:
    async for item in aiter:
        pass


@register(Difficulty.ADVANCED)
async def async_with(ctx: Any) -> None:
    async with ctx as c:
        pass


@register(Difficulty.ADVANCED)
def yield_from_delegation() -> list[int]:
    def inner():
        yield from range(5)

    return list(inner())


@register(Difficulty.ADVANCED)
def match_sequence(data: list[int]) -> int:
    match data:
        case [x, y, *rest]:
            return x + y
        case _:
            return -1


@register(Difficulty.ADVANCED)
def match_mapping(data: dict[str, Any]) -> str:
    match data:
        case {"name": name, "age": age}:
            return f"{name}: {age}"
        case _:
            return "unknown"


@register(Difficulty.ADVANCED)
def match_class(data: object) -> int:
    match data:
        case int(x):
            return x
        case _:
            return -1


@register(Difficulty.ADVANCED)
def nested_comprehension() -> dict[str, list[int]]:
    return {k: [x * 2 for x in v] for k, v in {"a": [1, 2], "b": [3, 4]}.items()}


@register(Difficulty.ADVANCED)
async def async_generator():
    for i in range(5):
        yield i * 2


@register(Difficulty.ADVANCED)
def multiple_with() -> str:
    with open("/dev/null") as a, open("/dev/null") as b:
        return a.read() + b.read()


@register(Difficulty.ADVANCED)
def match_or_guard(data: int) -> str:
    match data:
        case 1 | 2 | 3:
            return "small"
        case x if x > 100:
            return "big"
        case _:
            return "other"


if sys.version_info >= (3, 11):
    # NOTE: except* syntax requires Python 3.11+ and cannot be parsed by
    # older interpreters, so we use exec() to conditionally define it.
    exec(  # noqa: S102
        textwrap.dedent("""\
        @register(Difficulty.RIDICULOUS)
        def except_star() -> None:
            try:
                raise ExceptionGroup("eg", [ValueError("a"), TypeError("b")])
            except* ValueError:
                pass
            except* TypeError:
                pass
        """),
        globals(),
    )


@register(Difficulty.RIDICULOUS)
def metaclass_with_kwargs() -> None:
    class Meta(type):
        def __new__(mcs, name, bases, namespace, **kwargs):
            return super().__new__(mcs, name, bases, namespace)

    class Foo(metaclass=Meta, flag=True):
        pass


@register(Difficulty.RIDICULOUS)
def stacked_decorators() -> None:
    def repeat(n):
        def decorator(f):
            def wrapper(*args):
                return [f(*args) for _ in range(n)]

            return wrapper

        return decorator

    def add_tag(tag):
        def decorator(f):
            def wrapper(*args):
                return f"{tag}: {f(*args)}"

            return wrapper

        return decorator

    @repeat(3)
    @add_tag("result")
    def greet(name):
        return f"hi {name}"
