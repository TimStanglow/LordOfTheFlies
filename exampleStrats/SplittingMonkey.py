import random

# Monkeys just walk randomly
# Splitting Monkeys sometimes split (with a 1% chance)
# UniMonkeys walk randomly, but only south, east, or southeast
def make_turn(world, memory):
    movement = [random.randrange(3) - 1, random.randrange(3) - 1]
    do_split = random.randrange(100) < 1
    split_memory = None
    chase_target = None
    return movement, do_split, split_memory, chase_target, memory
