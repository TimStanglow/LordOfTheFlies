import random


def make_turn(world, memory):
    movement = [random.randrange(3) - 1, random.randrange(3) - 1]
    do_split = False
    split_memory = None
    chase_target = None
    return movement, do_split, split_memory, chase_target, memory
