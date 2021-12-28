# guessthedis - gameify learning python disassembly

A simple command-line game to learn python's opcodes, and order of execution.

# How to play
Write a function in `guessthedis/test_functions.py`, and apply the `@test` decorator to it.\
(There are also some commented-out, sample functions you can try)
```py
@test
def f(x: int, y: int) -> str:
    x *= 2
    z = 'abc'
    return z * x ** y
```
Run the program.
It will pick a function marked with `@test`, and prompt you
to write the disassembly (instructions & data).
```py
$ ./main.py
def f(x: int, y: int) -> str:
    x *= 2
    z = 'abc'
    return z * x ** y

Write the disassembly below (line by line):
0: load_fast x
2: load_const 2
4: inplace_multiply
6: store_fast x
8: load_const abc
10: store_fast z
12: load_fast z
14: load_fast x
16: load_fast y
18: binary_power
20: binary_multiply
22: return_value
Correct!
```
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
2. You can use it to check the correct answers:
```py
$ python
Python 3.9.9+ (main, Nov 19 2021, 08:51:58)
[GCC 7.5.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> def f(x: int, y: int) -> str:
...     x *= 2
...     z = 'abc'
...     return z * x ** y
...
>>> import dis
>>> dis.dis(f)
  2           0 LOAD_FAST                0 (x)
              2 LOAD_CONST               1 (2)
              4 INPLACE_MULTIPLY
              6 STORE_FAST               0 (x)

  3           8 LOAD_CONST               2 ('abc')
             10 STORE_FAST               2 (z)

  4          12 LOAD_FAST                2 (z)
             14 LOAD_FAST                0 (x)
             16 LOAD_FAST                1 (y)
             18 BINARY_POWER
             20 BINARY_MULTIPLY
             22 RETURN_VALUE
>>>
```

# Help wanted!
This idea is currently simple, but I think it could certainly be built on.

I'm looking for project maintainers if anyone's interested in taking this on! :)
