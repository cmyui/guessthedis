"""guessthedis - gameify learning python disassembly

For an in-detail explanation, please visit
the repo @ https://github.com/cmyui/guessthedis
"""

import argparse
import ast
import dis
import inspect
import subprocess
import tempfile
import textwrap
import time
import types
from typing import Any
from typing import Callable

from rich.console import Console
from rich.syntax import Syntax

from . import state as state_mod
from . import test_functions
from .terminal import Ansi
from .terminal import NavigationRequested
from .terminal import ignore_sigint
from .terminal import pick_challenge
from .terminal import printc
from .terminal import read_line
from .test_functions import Difficulty

__author__ = "Joshua Smith (cmyui)"
__email__ = "cmyuiosu@gmail.com"

# Opcodes whose arguments are not viable for user input.
#
# Jump opcodes (dis.hasjrel, dis.hasjabs) have byte-offset targets
# that change with any code modification. These are covered
# automatically across all Python versions via the dis module.
#
# Additionally, some opcodes have non-literal argvals:
# - FORMAT_VALUE (3.10-3.12): argval is a (conversion, has_format_spec) tuple
# - CONVERT_VALUE (3.13-3.14): argval is a builtin function object (e.g. repr)
OPCODES_WITH_UNPARSEABLE_ARGUMENT = (
    frozenset(dis.hasjrel)
    | frozenset(dis.hasjabs)
    | frozenset(
        dis.opmap[name]
        for name in (
            "CONVERT_VALUE",  # 3.13+
            "FORMAT_VALUE",  # 3.10-3.12
        )
        if name in dis.opmap
    )
)


def get_source_code_lines(disassembly_target: Callable[..., Any]) -> list[str]:
    """Get the source code of a function."""
    source_lines, _ = inspect.getsourcelines(disassembly_target)

    # (remove decorators from output)
    start_line = 0
    while source_lines[start_line].lstrip().startswith("@"):
        start_line += 1

    return textwrap.dedent("".join(source_lines[start_line:])).split("\n")


def _parse_user_arg(
    raw: str,
    expected_argval: object,
) -> tuple[bool, object]:
    """Parse a user-provided argument string and compare to the expected value.

    Returns (success, parsed_value).
    """
    # try ast.literal_eval first (handles quoted strings, numbers, collections)
    try:
        parsed = ast.literal_eval(raw)

        if isinstance(expected_argval, frozenset):
            parsed = frozenset(parsed)

        if not isinstance(parsed, type(expected_argval)):
            return False, None

        return parsed == expected_argval, parsed
    except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
        pass

    # fall back to bare identifier (e.g. variable names in LOAD_FAST)
    if isinstance(expected_argval, str) and raw == expected_argval:
        return True, raw

    return False, None


def _quiz_instructions(
    disassembly_target: Callable[..., Any] | types.CodeType,
) -> None:
    """Quiz the user on each instruction in the disassembly target.

    Recurses into nested code objects (inner functions, classes, etc.)
    after the outer disassembly is complete.
    """
    instruction_iterator = dis.get_instructions(disassembly_target)
    nested_code_objects: list[types.CodeType] = []

    for instruction in instruction_iterator:
        # collect nested code objects for recursive quizzing
        if isinstance(instruction.argval, types.CodeType):
            nested_code_objects.append(instruction.argval)

        # loop indefinitely to get valid user input
        while True:
            try:
                user_input_raw = read_line(f"{instruction.offset}: ").strip()
            except EOFError:
                # NOTE: ^D can be used to show the correct disassembly "cheatsheet"
                print("\x1b[2K", end="\r")  # clear current line

                # we'll show the disassembly "cheatsheet" in gnu's less interface
                # to do this, we'll need to write the contents to a temporary file
                # TODO: how common is the less command? should i have a fallback?
                with tempfile.NamedTemporaryFile("w") as f:
                    # always write opcode reference documentation at the top of output
                    f.write(
                        "python3 opcode reference\n"
                        "------------------------\n"
                        "- https://docs.python.org/3/library/dis.html#python-bytecode-instructions"
                        "\n\n",
                    )

                    # write the disassembly contents to the file
                    dis.dis(disassembly_target, file=f)

                    # make sure all contents have been flushed to disk
                    f.flush()

                    # open the file in the less interface
                    with ignore_sigint():
                        subprocess.run(["less", f.name])

                continue

            if not user_input_raw:
                printc("Invalid input, please try again", Ansi.LRED)
                continue

            # user has provided some input - check if it's correct
            # split only on the first space to preserve whitespace in arguments
            parts = user_input_raw.split(maxsplit=1)
            user_input_opcode = parts[0].lower()
            user_input_arg_raw = parts[1] if len(parts) > 1 else None

            # validate operation code name
            if user_input_opcode != instruction.opname.lower():
                printc(f"Incorrect opcode value: {user_input_opcode}", Ansi.LRED)
                continue

            # if this opcode expects arguments,
            # parse them from user input & validate
            expects_user_arg = (
                instruction.arg is not None
                and instruction.opcode not in OPCODES_WITH_UNPARSEABLE_ARGUMENT
                and not isinstance(instruction.argval, types.CodeType)
            )
            if expects_user_arg:
                if user_input_arg_raw is None:
                    printc("Missing argument(s), please try again", Ansi.LRED)
                    continue

                correct, _ = _parse_user_arg(
                    user_input_arg_raw,
                    instruction.argval,
                )
                if not correct:
                    printc(
                        f"Incorrect argument value: {user_input_arg_raw}",
                        Ansi.LRED,
                    )
                    continue
            else:
                if user_input_arg_raw is not None:
                    printc(
                        "Provided argument(s) in invalid context, please try again",
                        Ansi.LRED,
                    )
                    continue

            # user input is all correct
            break

    # recurse into nested code objects (inner functions, classes, etc.)
    for code_obj in nested_code_objects:
        code_name = getattr(code_obj, "co_qualname", code_obj.co_name)
        print(f"\nDisassembly of {code_name}:")
        _quiz_instructions(code_obj)


def test_user(
    disassembly_target: Callable[..., Any],
    *,
    console: Console,
) -> float:
    """Test the user on a single function. Returns elapsed seconds."""
    source_code_lines = get_source_code_lines(disassembly_target)
    max_len_line = max(len(line) for line in source_code_lines)

    print("Given the following function:")
    syntax = Syntax(
        code="\n".join(source_code_lines),
        lexer="python",
        theme="monokai",
        line_numbers=True,
        code_width=max_len_line + 1,
    )
    console.print(syntax)

    print("Write the disassembly below (line by line):")
    start = time.monotonic()
    _quiz_instructions(disassembly_target)
    elapsed = time.monotonic() - start

    printc("Correct!", Ansi.LGREEN)
    return elapsed


DIFFICULTY_CHOICES = [
    "beginner",
    "intermediate",
    "advanced",
    "ridiculous",
    "beginner+",
    "intermediate+",
    "advanced+",
    "ridiculous+",
]


def _parse_difficulty_filter(raw: str) -> tuple[Difficulty, bool]:
    """Parse a difficulty flag value into (level, and_above)."""
    and_above = raw.endswith("+")
    name = raw.removesuffix("+").upper()
    return Difficulty[name], and_above


def main() -> int:
    parser = argparse.ArgumentParser(description="guessthedis")
    parser.add_argument(
        "-d",
        "--difficulty",
        choices=DIFFICULTY_CHOICES,
        default=None,
        help="filter functions by difficulty level (append '+' for that level and above)",
    )
    args = parser.parse_args()

    if args.difficulty is not None:
        min_difficulty, and_above = _parse_difficulty_filter(args.difficulty)
        filtered = [
            (d, f)
            for d, f in test_functions.functions
            if (d >= min_difficulty if and_above else d == min_difficulty)
        ]
    else:
        filtered = test_functions.functions

    if not filtered:
        printc("No functions matched the given difficulty", Ansi.LRED)
        return 1

    session_key = args.difficulty or "all"
    game_state = state_mod.load_state()

    console = Console()
    results: list[str] = ["pending"] * len(filtered)
    current_index = 0
    session_start = time.monotonic()

    while current_index < len(filtered):
        printc("(^D = cheatsheet, ^G = navigate, ^C = exit)", Ansi.GRAY)
        print()
        _difficulty, function = filtered[current_index]
        try:
            elapsed = test_user(function, console=console)

            func_name = function.__name__
            prev_best = state_mod.record_challenge_time(
                game_state,
                func_name,
                elapsed,
            )
            if prev_best is not None:
                printc(
                    f"Time: {state_mod.format_time(elapsed)} "
                    f"(new personal best! was {state_mod.format_time(prev_best)})",
                    Ansi.LYELLOW,
                )
            else:
                current_best = state_mod.get_challenge_best(game_state, func_name)
                if current_best is not None and current_best < elapsed:
                    printc(
                        f"Time: {state_mod.format_time(elapsed)} "
                        f"(best: {state_mod.format_time(current_best)})",
                        Ansi.GRAY,
                    )
                else:
                    printc(f"Time: {state_mod.format_time(elapsed)}", Ansi.GRAY)

            print()
            state_mod.save_state(game_state)

            results[current_index] = "correct"
            current_index += 1
        except KeyboardInterrupt:
            print("\x1b[2K", end="\r")
            break
        except NavigationRequested:
            picked = pick_challenge(
                filtered,
                results,
                current_index,
                game_state=game_state,
            )
            if picked is not None:
                current_index = picked

    correct = results.count("correct")
    remaining = len(filtered) - correct

    print()
    print("Thanks for playing! :)\n\nResults\n-------")
    printc(f"Correct: {correct}", Ansi.LGREEN)
    printc(f"Remaining: {remaining}", Ansi.GRAY)

    if remaining == 0:
        session_elapsed = time.monotonic() - session_start
        prev_session = state_mod.record_session_time(
            game_state,
            session_key,
            session_elapsed,
        )
        if prev_session is not None:
            printc(
                f"Session time: {state_mod.format_time(session_elapsed)} "
                f"(new personal best! was {state_mod.format_time(prev_session)})",
                Ansi.LYELLOW,
            )
        else:
            current_session = game_state["session_bests"].get(session_key)
            if current_session is not None and current_session < session_elapsed:
                printc(
                    f"Session time: {state_mod.format_time(session_elapsed)} "
                    f"(best: {state_mod.format_time(current_session)})",
                    Ansi.GRAY,
                )
            else:
                printc(
                    f"Session time: {state_mod.format_time(session_elapsed)}",
                    Ansi.GRAY,
                )
        state_mod.save_state(game_state)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
