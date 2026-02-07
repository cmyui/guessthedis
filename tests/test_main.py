import dis

from guessthedis import test_functions
from guessthedis.__main__ import OPCODES_WITH_UNPARSEABLE_ARGUMENT
from guessthedis.__main__ import _parse_user_arg
from guessthedis.__main__ import get_source_code_lines

# -- _parse_user_arg --


class TestParseUserArgBareIdentifiers:
    def test_simple_name(self) -> None:
        ok, val = _parse_user_arg("x", "x")
        assert ok is True
        assert val == "x"

    def test_dotted_name(self) -> None:
        ok, val = _parse_user_arg("os.path", "os.path")
        assert ok is True

    def test_wrong_name(self) -> None:
        ok, _ = _parse_user_arg("y", "x")
        assert ok is False


class TestParseUserArgQuotedStrings:
    def test_simple_string(self) -> None:
        ok, val = _parse_user_arg("'hello'", "hello")
        assert ok is True
        assert val == "hello"

    def test_string_with_spaces(self) -> None:
        ok, val = _parse_user_arg("' is '", " is ")
        assert ok is True
        assert val == " is "

    def test_string_with_leading_space(self) -> None:
        ok, val = _parse_user_arg("' years old'", " years old")
        assert ok is True

    def test_double_quoted(self) -> None:
        ok, val = _parse_user_arg('"hello"', "hello")
        assert ok is True

    def test_wrong_string(self) -> None:
        ok, _ = _parse_user_arg("'wrong'", "right")
        assert ok is False


class TestParseUserArgLiterals:
    def test_integer(self) -> None:
        ok, val = _parse_user_arg("42", 42)
        assert ok is True
        assert val == 42

    def test_negative_integer(self) -> None:
        ok, val = _parse_user_arg("-1", -1)
        assert ok is True

    def test_float(self) -> None:
        ok, val = _parse_user_arg("3.14", 3.14)
        assert ok is True

    def test_none(self) -> None:
        ok, val = _parse_user_arg("None", None)
        assert ok is True
        assert val is None

    def test_true(self) -> None:
        ok, val = _parse_user_arg("True", True)
        assert ok is True

    def test_false(self) -> None:
        ok, val = _parse_user_arg("False", False)
        assert ok is True

    def test_tuple(self) -> None:
        ok, val = _parse_user_arg("(1, 2)", (1, 2))
        assert ok is True

    def test_wrong_integer(self) -> None:
        ok, _ = _parse_user_arg("99", 42)
        assert ok is False


class TestParseUserArgTypeMismatches:
    def test_string_vs_int(self) -> None:
        ok, _ = _parse_user_arg("'42'", 42)
        assert ok is False

    def test_int_vs_string(self) -> None:
        ok, _ = _parse_user_arg("42", "42")
        assert ok is False

    def test_int_vs_float(self) -> None:
        # int and float are not interchangeable in bytecode args
        ok, _ = _parse_user_arg("3", 3.0)
        assert ok is False


class TestParseUserArgFrozenset:
    def test_from_set_literal(self) -> None:
        ok, val = _parse_user_arg("{1, 2, 3}", frozenset({1, 2, 3}))
        assert ok is True
        assert val == frozenset({1, 2, 3})

    def test_wrong_elements(self) -> None:
        ok, _ = _parse_user_arg("{4, 5, 6}", frozenset({1, 2, 3}))
        assert ok is False


# -- get_source_code_lines --


class TestGetSourceCodeLines:
    def test_strips_single_decorator(self) -> None:
        lines = get_source_code_lines(test_functions.no_op_pass)
        assert lines[0].startswith("def no_op_pass")

    def test_preserves_body(self) -> None:
        lines = get_source_code_lines(test_functions.unary_op)
        source = "\n".join(lines)
        assert "x = 5" in source
        assert "return -x" in source

    def test_no_decorator_in_output(self) -> None:
        lines = get_source_code_lines(test_functions.for_loop)
        assert not any(line.strip().startswith("@") for line in lines)

    def test_multiline_body_dedented(self) -> None:
        lines = get_source_code_lines(test_functions.store_collection_types_fast)
        # the body lines should not have excessive indentation
        body_lines = [l for l in lines[1:] if l.strip()]
        for line in body_lines:
            assert line.startswith("    "), f"Expected 4-space indent: {line!r}"


# -- OPCODES_WITH_UNPARSEABLE_ARGUMENT --


class TestUnparseableOpcodes:
    def test_covers_all_jump_opcodes(self) -> None:
        all_jumps = frozenset(dis.hasjrel) | frozenset(dis.hasjabs)
        missing = all_jumps - OPCODES_WITH_UNPARSEABLE_ARGUMENT
        assert missing == set(), (
            f"Jump opcodes missing from skip set: "
            f"{sorted(dis.opname[op] for op in missing)}"
        )

    def test_format_value_included_if_present(self) -> None:
        if "FORMAT_VALUE" in dis.opmap:
            assert dis.opmap["FORMAT_VALUE"] in OPCODES_WITH_UNPARSEABLE_ARGUMENT

    def test_convert_value_included_if_present(self) -> None:
        if "CONVERT_VALUE" in dis.opmap:
            assert dis.opmap["CONVERT_VALUE"] in OPCODES_WITH_UNPARSEABLE_ARGUMENT


# -- test_functions registry --


class TestFunctionRegistry:
    def test_all_functions_disassemble(self) -> None:
        for _difficulty, func in test_functions.functions:
            # should not raise
            instructions = list(dis.get_instructions(func))
            assert len(instructions) > 0, f"{func.__name__} has no instructions"

    def test_functions_are_registered(self) -> None:
        assert len(test_functions.functions) > 0

    def test_no_duplicate_names(self) -> None:
        names = [f.__name__ for _d, f in test_functions.functions]
        assert len(names) == len(set(names))
