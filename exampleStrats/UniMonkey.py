import random

# Monkeys just walk randomly
# Splitting Monkeys sometimes split (with a 1% chance)
# UniMonkeys walk randomly, but only south, east, or southeast
def make_turn(world, memory):
    movement = [random.randrange(2) - 1, random.randrange(2) - 1]
    do_split = False
    split_memory = None
    chase_target = None
    return movement, do_split, split_memory, chase_target, memory
