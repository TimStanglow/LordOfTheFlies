import random
import os
import itertools
import importlib
import numpy as np

# PARAMETERS

# World Parameter
world_height = 10
world_width = 20
# If True agents can walk around the world, if False they are boxed in
# For Now Only True is implemented
world_wraparound = True

# Tournament Paramenter
STRATEGY_FOLDER = "exampleStrats"
RESULTS_FILE = "results.txt"
numberOfRounds = 3


class Player:
    def __init__(self, x, y, strategy, id):
        self.x = x
        self.y = y
        self.strategy = strategy
        self.id = id
        self.movement = None
        self.do_split = None
        self.split_memory = None
        self.chase_target = None


class World:

    def __init__(self, sizeX, sizeY, WorldGenTypeID, strategies):
        # Values correspond to ID from Concept
        self.terrain = np.zeros((sizeX, sizeY), np.int32)
        # For Now 0 = No Vegetation, All else are one higher than the ID from concept
        self.vegetation = np.zeros((sizeX, sizeY), np.int32)
        self.playerMap = np.zeros((sizeX, sizeY), bool)

        self.strategies = strategies
        self.players = list()

        self.tileNorth = np.zeros(self.terrain.shape, object)
        self.tileSouth = np.zeros(self.terrain.shape, object)
        self.tileEast = np.zeros(self.terrain.shape, object)
        self.tileWest = np.zeros(self.terrain.shape, object)
        self.pregenerateDirections()

        # Prior to the event different world generators can be implemented and Tested.
        if WorldGenTypeID == 0:
            self.WorldGen0()

        if WorldGenTypeID == 1:
            self.WorldGen1()

        for strategy in strategies:
            self.players.append(Player(random.randrange(sizeX), random.randrange(sizeY), strategy, 0))

    # Moves to be made next Turn
    def addMove(self, strategy, id, movement, do_split, split_memory, chase_target):
        # TODO Change how correct player is found, this will be slow with more players
        # TODO Implement id's correctly
        for player in self.players:
            if player.strategy == strategy and id == player.id:
                player.movement = movement
                player.do_split = do_split
                player.split_memory = split_memory
                player.chase_target = chase_target

    def WorldSimulation(self):
        self.playerSimulation()
        self.vegetationSimulation()

    def playerSimulation(self):
        for player in self.players:
            player.x += player.movement[0]
            player.x %= world_width
            player.y += player.movement[1]
            player.y %= world_height
        # TODO implement the results of walking
        # TODO implement other actions than walking

    def vegetationSimulation(self):
        for idx, x in np.ndenumerate(self.terrain):
            localTerrain = self.terrain[idx]
            localVegatation = self.vegetation[idx]
            if localVegatation == 1:
                randomNumber = random.randrange(100)
                if randomNumber < 3:
                    if self.vegetation[self.tileNorth[idx]] == 0:
                        self.vegetation[self.tileNorth[idx]] = 3
                elif randomNumber < 6:
                    if self.vegetation[self.tileEast[idx]] == 0:
                        self.vegetation[self.tileEast[idx]] = 3
                elif randomNumber < 9:
                    if self.vegetation[self.tileSouth[idx]] == 0:
                        self.vegetation[self.tileSouth[idx]] = 3
                elif randomNumber < 12:
                    if self.vegetation[self.tileWest[idx]] == 0:
                        self.vegetation[self.tileWest[idx]] = 3
            elif localVegatation == 2:
                randomNumber = random.randrange(100)
                if randomNumber < 5:
                    if self.vegetation[self.tileNorth[idx]] == 0:
                        self.vegetation[self.tileNorth[idx]] = 3
                elif randomNumber < 10:
                    if self.vegetation[self.tileEast[idx]] == 0:
                        self.vegetation[self.tileEast[idx]] = 3
                elif randomNumber < 15:
                    if self.vegetation[self.tileSouth[idx]] == 0:
                        self.vegetation[self.tileSouth[idx]] = 3
                elif randomNumber < 20:
                    if self.vegetation[self.tileWest[idx]] == 0:
                        self.vegetation[self.tileWest[idx]] = 3
            elif localVegatation == 0:
                if localTerrain == 0:  # Grass
                    randomNumber = random.randrange(100)
                    if randomNumber < 5:
                        self.vegetation[idx] = 4
                elif localTerrain == 1:  # Jungle
                    randomNumber = random.randrange(100)
                    if randomNumber < 5:
                        self.vegetation[idx] = 4
                    elif randomNumber < 15:
                        self.vegetation[idx] = 5
                elif localTerrain == 2:  # Mountain
                    randomNumber = random.randrange(100)
                    if randomNumber < 3:
                        self.vegetation[idx] = 4
                elif localTerrain == 3:  # Desert
                    randomNumber = random.randrange(100)
                    if randomNumber < 2:
                        self.vegetation[idx] = 4
                    elif randomNumber < 10:
                        self.vegetation[idx] = 6

    # Each Tile Random and independent of surrounding
    # This method should not be used for the competition,
    # and is only here, as it's the simplest possible so other parts can be worked on.
    def WorldGen0(self):
        # Generate the terrain, and the none respawning vegetation (Trees) first.
        for idx, x in np.ndenumerate(self.terrain):
            self.terrain[idx] = random.randrange(4)
            # Grass
            if self.terrain[idx] == 0:
                randomNumber = random.randrange(100)
                if randomNumber < 5:
                    self.vegetation[idx] = 1
            # Jungle
            if self.terrain[idx] == 1:
                randomNumber = random.randrange(100)
                if randomNumber < 10:
                    self.vegetation[idx] = 1
                elif randomNumber < 20:
                    self.vegetation[idx] = 2
            # Mountain
            if self.terrain[idx] == 2:
                randomNumber = random.randrange(100)
                if randomNumber < 2:
                    self.vegetation[idx] = 1
            # Desert: Do nothing

        #  Generate the respawning vegetation by simulating n=4 Steps
        for i in range(4):
            self.vegetationSimulation()
        return

    # TODO other methods for generating the world
    def WorldGen1(self):
        raise NotImplementedError("WorldGen1 not yet Implemented")

    # Vegetation Simulation requires the tiles north/south/east/west of other Tiles
    # To Deal with the edgeCases would take a lot of computation power each step
    # So the adjacent Tiles are precalculated, and placed in a Lookup Table here
    def pregenerateDirections(self):
        sizeX = self.terrain.shape[0]
        sizeY = self.terrain.shape[1]
        for idx, x in np.ndenumerate(self.terrain):
            x = idx[0]
            y = idx[1]
            self.tileNorth[idx] = (x, (y + 1) % sizeY)
            self.tileSouth[idx] = (x, (y - 1) % sizeY)
            self.tileWest[idx] = ((x - 1) % sizeX, y)
            self.tileEast[idx] = ((x + 1) % sizeX, y)


def main():
    runFullTournament(STRATEGY_FOLDER, RESULTS_FILE)


def runFullTournament(inFolder, outFile):
    print("Starting tournament, reading files from " + inFolder)
    scoreKeeper = {}
    STRATEGY_LIST = []
    for file in os.listdir(inFolder):
        if file.endswith(".py"):
            STRATEGY_LIST.append(file[:-3])

    for strategy in STRATEGY_LIST:
        scoreKeeper[strategy] = 0

    f = open(outFile, "w+")
    for roundN in range(numberOfRounds):
        runRound(STRATEGY_LIST)

    f.write("Not Implemented")
    f.flush()
    f.close()
    print("Done with everything! Results file written to " + RESULTS_FILE)


def runRound(STRATEGY_LIST):
    modules = dict()
    memories = dict()
    for strategy in STRATEGY_LIST:
        modules[strategy] = importlib.import_module(STRATEGY_FOLDER + "." + strategy)
        memories[strategy] = list()
        memories[strategy].append(None)

    LENGTH_OF_GAME = 25000
    world = World(world_width, world_height, 0, STRATEGY_LIST)
    for turn in range(LENGTH_OF_GAME):
        for strategy in STRATEGY_LIST:
            for id, memory in enumerate(memories[strategy]):
                # TODO specify a format in which the world be given to Players
                movement, do_split, split_memory, chase_target, memory = modules[strategy].make_turn(None, memory)
                world.addMove(strategy, id, movement, do_split, split_memory, chase_target)
        world.WorldSimulation()

    history = None
    return history


if __name__ == '__main__':
    main()