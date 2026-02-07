# guessthedis - gameify learning python disassembly

A command-line game to test & grow your python bytecode disassembly knowledge.

Supports Python 3.10+. Note that bytecode instructions differ between Python
versions, so the expected answers depend on which version you're running.

# How to play
There are 30 built-in functions organized by difficulty (beginner, intermediate,
advanced) in `guessthedis/test_functions.py`. You can also write your own and
apply the `@register` decorator to include them.

```py
@register
def unary_op() -> int:
    x = 5
    return -x
```
Run the program with `python -m guessthedis`. It will show each function and
prompt you to write the disassembly (opcode name & arguments) line by line.

String arguments can be typed bare or quoted -- both `load_fast x` and
`load_fast 'x'` are accepted. String constants with whitespace must be
quoted (e.g. `load_const ' is '`).

```
$ python -m guessthedis
Given the following function:
  1 def unary_op() -> int:
  2     x = 5
  3     return -x

Write the disassembly below (line by line):
0: load_const 5
2: store_fast x
4: load_fast x
6: unary_negative
8: return_value
Correct!
```

Functions containing nested code objects (inner functions, classes) will also
quiz you on the inner disassembly after the outer function is complete.

When you exit the game (e.g. with `^C`), your total score will be shown.
```
Thanks for playing! :)

Results
-------
Correct: 6
Incorrect: 5
$
```

# Documentation & Debugging
You'll definitely want to be familiar with python's [dis module](https://docs.python.org/3/library/dis.html) for debugging.

1. It has a comprehensive [documentation of each bytecode instruction](https://docs.python.org/3/library/dis.html#python-bytecode-instructions).
2. You can press `^D` during the game to open a cheatsheet showing the correct
   disassembly for the current function in `less`.
3. You can use the `dis` module directly to check answers:
```pycon
>>> import dis
>>> def unary_op() -> int:
...     x = 5
...     return -x
...
>>> dis.dis(unary_op)
  2           0 LOAD_CONST               1 (5)
              2 STORE_FAST               0 (x)

  3           4 LOAD_FAST                0 (x)
              6 UNARY_NEGATIVE
              8 RETURN_VALUE
>>>
```
