import random


def make_turn(world, memory):
    movement = [random.randrange(2) - 1, random.randrange(2) - 1]
    do_split = random.randrange(100) < 1
    split_memory = None
    chase_target = None
    return movement, do_split, split_memory, chase_target, memory
