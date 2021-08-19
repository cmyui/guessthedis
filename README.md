# A little minigame I created for learning about python's opcodes & disassembly

Basically you can write your own function, decorate it with @test_func, then it will ask you to write the disassembly 1 opcode at a time.

At the moment it picks a random function from the list of functions decorated with @test_func, but ideally I'd like to make this more interesting and have it actually teach you the common opcodes one at a time, challenging you in a more school-like fashion. It currently expects you to just google your way around things which is debatably a better way to learn to prepare for the real world, but I'm sure theres a better middleground.
