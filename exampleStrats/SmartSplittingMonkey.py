import random

# SmartSplittingMonkeys are SplittingMonkeys, that are more likely to split the more energy they have
def make_turn(world, self, memory):
    movement = [random.randrange(3) - 1, random.randrange(3) - 1]
    do_split = random.randrange(100) < self.energy / 100
    split_memory = None
    chase_target = None
    return movement, do_split, split_memory, chase_target, memory
