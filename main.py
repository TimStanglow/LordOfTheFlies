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

playerStartingEnergy = 500
playerEnergyLossBase = 1
playerEnergyCostMultiplies = 0.001  # This Increases how much energy each player loses per energy they have

# Tournament Paramenter
STRATEGY_FOLDER = "exampleStrats"
RESULTS_FILE = "results.txt"
numberOfRounds = 1


def energyFromVegetation(id):
    if id == 3:
        return 20
    elif id == 4:
        return 30
    elif id == 5:
        return 15
    elif id == 6:
        return 10
    raise ValueError("energyFromVegetation: invalid Vegetation ID")


class Player:
    def __init__(self, x, y, strategy, id, modules):
        self.x = x
        self.y = y
        self.strategy = strategy
        self.id = id
        self.energy = playerStartingEnergy
        self.alive = True
        self.movement = [0, 0]
        self.do_split = False
        self.split_memory = None
        self.chase_target = None
        self.memory = None
        self.modules = modules

    def makeTurn(self):
        self.movement, self.do_split, self.split_memory, self.chase_target, self.memory = self.modules[
            self.strategy].make_turn(None, self.memory)


class World:

    def __init__(self, sizeX, sizeY, WorldGenTypeID, strategies, modules):
        # Values correspond to ID from Concept
        self.terrain = np.zeros((sizeX, sizeY), np.int32)
        # For Now 0 = No Vegetation, All else are one higher than the ID from concept
        self.vegetation = np.zeros((sizeX, sizeY), np.int32)
        self.playerMap = np.empty((sizeX, sizeY), object)

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

        self.nextPlayerID = 0
        for strategy in strategies:
            player = Player(random.randrange(sizeX), random.randrange(sizeY), strategy, self.nextPlayerID, modules)
            self.playerMap[player.x, player.y].append(self.nextPlayerID)
            self.players.append(player)
            self.nextPlayerID += 1

    def WorldSimulation(self):
        self.askPlayersForMove()
        self.playerMovementSimulation()
        self.vegetationSimulation()
        self.playerEatingSimulation()

    def askPlayersForMove(self):
        for player in self.players:
            if player.alive:
                player.makeTurn()

    def playerMovementSimulation(self):
        # Move Players
        for player in self.players:
            if player.alive:
                if player.do_split:
                    newPlayer = Player(player.x, player.y, player.strategy, self.nextPlayerID, player.modules)
                    player.energy = player.energy / 2
                    newPlayer.energy = player.energy
                    self.playerMap[player.x, player.y].append(self.nextPlayerID)
                    self.players.append(newPlayer)
                    self.nextPlayerID += 1

                if player.movement != [0, 0]:
                    self.playerMap[player.x, player.y].remove(player.id)
                    player.x += player.movement[0]
                    player.x %= world_width
                    player.y += player.movement[1]
                    player.y %= world_height
                    self.playerMap[player.x, player.y].append(player.id)
                    player.energy -= (playerEnergyLossBase + player.movement[0] * player.movement[0] + player.movement[
                        1] *
                                      player.movement[1]) * (1 + playerEnergyCostMultiplies * player.energy)
                else:
                    player.energy -= playerEnergyLossBase * (1 + playerEnergyCostMultiplies * player.energy)

                # Remove Dead Players
                if player.energy <= 0:
                    self.playerMap[player.x, player.y].remove(player.id)
                    player.alive = False

        # Resolve Conflicts (Players of the same team can share a spot)
        for idx, x in np.ndenumerate(self.playerMap):
            if len(x) >= 1:
                teams = set()
                for id in x:
                    teams.add(self.players[id].strategy)
                while len(teams) > 1:
                    # Select 2 Random players
                    p1 = random.randrange(len(x))
                    p2 = random.randrange(len(x))
                    if self.players[x[p1]].strategy != self.players[x[p2]].strategy:
                        # If the difference in Energy is less than 5, a random player survives with 5 energy left
                        if (self.players[x[p1]].energy - self.players[x[p2]].energy) ** 2 < 25:
                            self.players[x[p1]].energy = 5
                            self.players[x[p2]].alive = False
                            self.playerMap[self.players[x[p2]].x, self.players[x[p2]].y].remove(self.players[x[p2]].id)
                        # otherwise the one with more energy survives with the diffrence of energy
                        else:
                            if self.players[x[p1]].energy < self.players[x[p2]].energy:
                                self.players[x[p2]].energy = 5
                                self.players[x[p1]].alive = False
                                self.playerMap[self.players[x[p1]].x, self.players[x[p1]].y].remove(
                                    self.players[x[p1]].id)
                            else:
                                self.players[x[p1]].energy = 5
                                self.players[x[p2]].alive = False
                                self.playerMap[self.players[x[p2]].x, self.players[x[p2]].y].remove(
                                    self.players[x[p2]].id)
                        teams = set()
                        for id in x:
                            teams.add(self.players[id].strategy)

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

    def playerEatingSimulation(self):
        for player in self.players:
            if player.alive:
                if self.vegetation[player.x, player.y] > 2:
                    player.energy += energyFromVegetation(self.vegetation[player.x, player.y])
                    self.vegetation[player.x, player.y] = 0

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
            self.playerMap[idx] = list()


def main():
    runFullTournament(STRATEGY_FOLDER, RESULTS_FILE)


def runFullTournament(inFolder, outFile):
    # print("Starting tournament, reading files from " + inFolder)
    scoreKeeper = {}
    STRATEGY_LIST = []
    for file in os.listdir(inFolder):
        if file.endswith(".py"):
            STRATEGY_LIST.append(file[:-3])

    for strategy in STRATEGY_LIST:
        scoreKeeper[strategy] = 0

    f = open(outFile, "w+")
    for roundN in range(numberOfRounds):
        runRound(STRATEGY_LIST, f)

    f.flush()
    f.close()
    print("Done with everything! Results file written to " + RESULTS_FILE)


def runRound(STRATEGY_LIST, f):
    modules = dict()
    for strategy in STRATEGY_LIST:
        modules[strategy] = importlib.import_module(STRATEGY_FOLDER + "." + strategy)

    LENGTH_OF_GAME = 1000
    world = World(world_width, world_height, 0, STRATEGY_LIST, modules)

    f.write("Average Energy over Time:\n")

    for turn in range(LENGTH_OF_GAME):
        world.WorldSimulation()
        sum = 0
        c = 0
        for player in world.players:
            if player.alive:
                c += 1
                sum += player.energy
        f.write(f"{sum / max(c, 1):1f}, ")

    f.write("\n\n In the end, alive are:\n")
    count = dict()
    for strategy in STRATEGY_LIST:
        count[strategy] = 0
    for player in world.players:
        if player.alive:
            count[player.strategy] += 1
    for strategy in STRATEGY_LIST:
        f.write(f"Of the team {strategy} there are {count[strategy]} Players.\n")
    f.write("\n In detail, those alive are:\n")
    for player in world.players:
        if player.alive:
            f.write(f"Player {player.id} of the team {player.strategy} with {player.energy:1f} energy.\n")
    history = None
    return history


if __name__ == '__main__':
    main()
