# guessthedis - gameify learning python disassembly

A simple command-line game to learn python's opcodes, and order of execution.

# How to play
1. Write a function, and apply the `@test_func` decorator to it.\
![image](https://user-images.githubusercontent.com/17343631/147539227-c7ab10d9-bb32-4839-b76c-4bb15a1a76df.png)

2. Run the program, and write the disassembly, instruction by instructions; both opcode, and data.\
![image](https://user-images.githubusercontent.com/17343631/147539304-1ccbe624-de7d-4f6e-a4c3-233682a66c52.png)

3. When you exit the game (e.g. with `^C`), your total score will be shown.\
![image](https://user-images.githubusercontent.com/17343631/147539429-0fc01f61-e69e-4882-ba66-3ffb562becf6.png)

# Documentation & Debugging
You'll definitely want to be familiar with python's [dis module](https://docs.python.org/3/library/dis.html) for debugging.

1. It has a comprehensive [documentation of each of the various bytecode instructions](docs.python.org/3/library/dis.html#python-bytecode-instructions).
2. You can use it to check the correct answers:\
![image](https://user-images.githubusercontent.com/17343631/147539745-2fa4a088-1811-4e7e-a5a4-c6b1938ac95a.png)

# Help wanted!
This idea is currently simple, but I think it could certainly be built on.

I'm looking for project maintainers if anyone's interested in taking this on! :)
