# coding: utf-8
# mapAgents.py
# parsons/11-nov-2017
#
# Version 1.0
#
# A simple map-building to work with the PacMan AI projects from:
#
# http://ai.berkeley.edu/
#
# These use a simple API that allow us to control Pacman's interaction with
# the environment adding a layer on top of the AI Berkeley code.
#
# As required by the licensing agreement for the PacMan AI we have:
#
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).

# The agent here is an extension of the above code written by Simon
# Parsons, based on the code in pacmanAgents.py

# Todo: Make map update more efficient
# Todo: small map

# ideas:
# higher reward for food that is closer --> Aiming for higher score
# reduce reward for spots with less exits
# predict path of ghosts for n steps and give negative rewards to where they might go. Observation: usually go straight and then randomly select direction when at intersection.


from pacman import Directions
from game import Agent
import api
import random
import game
import util
import sys
from collections import deque

FOOD_REWARD = 20
EMTPY_REWARD = -0.03
GHOST_REWARD = -1250
GHOST_DANGER_ZONE = 3 # fields around ghost that are given a negative reward as well
GHOST_DANGER_ZONE_REWARD = GHOST_REWARD * 0.75 # fields around ghost that are given a negative reward as well
CAPSULE_REWARD = 100
GHOST_EDIBLE_REWARD = abs(GHOST_REWARD)
CAPSULE_TIME_RUNNING_OUT_THRESHOLD = 5
PREDICTION_THRESHOLD = 0.01
ISSMALL = False
ACTIONS = [Directions.NORTH, Directions.SOUTH, Directions.EAST, Directions.WEST]

# Value iteration:
ITERATIONS = 200
CONVERGENCE_THRESHOLD = 0.001

# Bellmann:
# How much the agent values future rewards over immediate rewards
GAMMA = 0.9

#
# A class that creates a grid that can be used as a map
#
# The map itself is implemented as a nested list, and the interface
# allows it to be accessed by specifying x, y locations.
#
class Grid:
         
    # Constructor
    #
    # Note that it creates variables:
    #
    # grid:   an array that has one position for each element in the grid.
    # width:  the width of the grid
    # height: the height of the grid
    #
    # Grid elements are not restricted, so you can place whatever you
    # like at each location. You just have to be careful how you
    # handle the elements when you use them.
    def __init__(self, width, height):
        self.width = width
        self.height = height
        subgrid = []
        for i in range(self.height):
            row=[]
            for j in range(self.width):
                row.append(0)
            subgrid.append(row)

        self.grid = subgrid

    
    # Print the grid out.
    def display(self):       
        for i in range(self.height):
            for j in range(self.width):
                # print grid elements with no newline
                print self.grid[i][j],
            # A new line after each line of the grid
            print 
        # A line after the grid
        print

    # The display function prints the grid out upside down. This
    # prints the grid out so that it matches the view we see when we
    # look at Pacman.
    def prettyDisplay(self):       
        for i in range(self.height):
            for j in range(self.width):
                # print grid elements with no newline
                print self.grid[self.height - (i + 1)][j],
            # A new line after each line of the grid
            print 
        # A line after the grid
        print
        
    # Set and get the values of specific elements in the grid.
    # Here x and y are indices.
    def setValue(self, x, y, value):
        self.grid[y][x] = value

    def getValue(self, x, y):
        return self.grid[y][x]

    # Return width and height to support functions that manipulate the
    # values stored in the grid.
    def getHeight(self):
        return self.height

    def getWidth(self):
        return self.width

# north is the direction of increasing y, or (0,1)
directionCoordinate = {Directions.NORTH: (0, 1), Directions.SOUTH: (0, -1), Directions.WEST: (-1, 0), Directions.EAST: (1, 0)}
movePossibleResults = {Directions.NORTH: [Directions.NORTH, Directions.WEST, Directions.EAST], 
                       Directions.SOUTH: [Directions.SOUTH, Directions.WEST, Directions.EAST], 
                       Directions.WEST: [Directions.WEST, Directions.NORTH, Directions.SOUTH], 
                       Directions.EAST: [Directions.EAST, Directions.NORTH, Directions.SOUTH]}


class OldGhostPredictionAgent(Agent):

    # The constructor. We don't use this to create the map because it
    # doesn't have access to state information.
    def __init__(self):
        print "Running init!"

    # This function is run when the agent is created, and it has access
    # to state information, so we use it to build a map for the agent.
    def registerInitialState(self, state):
        print "Running registerInitialState!"
        # Make a map of the right size
        self.makeMaps(state)
        self.addWallsToMap(state)
        self.initialiseRewardsInMap(state)
        self.initialiseLegalMovesMap()
        self.previousGhosts = []
        if self.map.getWidth() < 8:
            global FOOD_REWARD, EMTPY_REWARD, GHOST_REWARD, GHOST_DANGER_ZONE, GHOST_DANGER_ZONE_REWARD, GAMMA, ITERATIONS, ISSMALL
            FOOD_REWARD = 20
            EMTPY_REWARD = -0.01
            GHOST_REWARD = -100
            GHOST_DANGER_ZONE = 1 # fields around ghost that are given a negative reward as well
            GHOST_DANGER_ZONE_REWARD = GHOST_REWARD * 0.2 # fields around ghost that are given a negative reward as well
            GAMMA = 0.95
            ITERATIONS = 100
            ISSMALL = True

    # This is what gets run when the game ends.
    def final(self, state):
        # cleanup?
        print "Looks like I just died!"

    # Make a map by creating a grid of the right size
    def makeMaps(self,state):
        corners = api.corners(state)
        height = self.getLayoutHeight(corners)
        width  = self.getLayoutWidth(corners)
        self.map = Grid(width, height)
        self.legalMovesMap = Grid(width, height)
    # Functions to get the height and the width of the grid.
    #
    # We add one to the value returned by corners to switch from the
    # index (returned by corners) to the size of the grid (that damn
    # "start counting at zero" thing again).
    def getLayoutHeight(self, corners):
        height = -1
        for i in range(len(corners)):
            if corners[i][1] > height:
                height = corners[i][1]
        return height + 1

    def getLayoutWidth(self, corners):
        width = -1
        for i in range(len(corners)):
            if corners[i][0] > width:
                width = corners[i][0]
        return width + 1

    # Functions to manipulate the map.
    #
    # Put every element in the list of wall elements into the map
    def addWallsToMap(self, state):
        walls = api.walls(state)
        for i in range(len(walls)):
            self.map.setValue(walls[i][0], walls[i][1], None)

    # Create a map with a current picture of the food that exists.
    def initialiseRewardsInMap(self, state):

        # make all grid elements that aren't walls blank (= empty reward)
        for i in range(self.map.getWidth()):
            for j in range(self.map.getHeight()):
                if self.map.getValue(i, j) != None:
                    self.map.setValue(i, j, EMTPY_REWARD)

        # Food
        food = api.food(state)
        for x, y in food:
            self.map.setValue(x, y, FOOD_REWARD)
        
        # Capsules
        capsules = api.capsules(state)
        for x, y in capsules:
            self.map.setValue(x, y, CAPSULE_REWARD)

        # Ghosts
        ghosts = api.ghosts(state)
        for x, y in ghosts:
            self.map.setValue(x, y, GHOST_REWARD)

        self.previousGhosts = ghosts 

    def apiGetGhostsInt(self, state):
        return [(int(ghost[0]), int(ghost[1])) for ghost in api.ghosts(state)]

    def apiGetGhostsWithTimesInt(self, state):
        return [(int(ghost[0][0]), int(ghost[0][1]), ghost[1]) for ghost in api.ghostStatesWithTimes(state)]
    
    def initialiseLegalMovesMap(self):
        for x in range(self.legalMovesMap.getWidth()):
            for y in range(self.legalMovesMap.getHeight()):
                if self.map.getValue(x, y) != None:
                    self.legalMovesMap.setValue(x, y, self.getLegalMovesAt(x, y))
                else:
                    self.legalMovesMap.setValue(x, y, None) # walls are none
        print("legal moves map")
        self.legalMovesMap.prettyDisplay()

    def getLegalMovesAt(self, x, y):
        legal = []
        for action in ACTIONS:
            newX, newY = self.getCoordinateAfterMove(action, x, y)
            if self.map.getValue(newX, newY) != None:
                legal.append(action)
        return legal
    
    def updateMap(self, state, x, y):

        for i in range(self.map.getWidth()):
            for j in range(self.map.getHeight()):
                if self.map.getValue(i, j) != None:
                    self.map.setValue(i, j, EMTPY_REWARD)

        food = api.food(state)
        for x, y in food:
            self.map.setValue(x, y, FOOD_REWARD)
        # if ISSMALL and (3, 3) in food:
        #     self.map.setValue(3, 3, FOOD_REWARD * 0.5)

        # Capsules
        capsules = api.capsules(state)
        for x, y in capsules:
            self.map.setValue(x, y, CAPSULE_REWARD)


        # Ghosts
        ghosts = self.apiGetGhostsWithTimesInt(state)

        # predict where ghost is moving to. Give negative rewards to those fields.
        if len(self.previousGhosts) > 0: # no prediction can be made in first step of game since direction is unknown
            for (prevX, prevY, prevT), (currX, currY, currT) in zip(self.previousGhosts, ghosts):
                direction = self.getMovementDirection(prevX, prevY, currX, currY)
                print("Ghost from ", (prevX, prevY), "to", (currX, currY), "moving", direction)
                predictedGhostPath = self.predictGhostPath((currX, currY), direction)
                self.prettyPrintGhostPaths(predictedGhostPath)
                if currT > CAPSULE_TIME_RUNNING_OUT_THRESHOLD: # timer is bigger than threshold --> consider ghost as edible. chase after. otherwise run away
                    reward = GHOST_EDIBLE_REWARD # integrate time and distance of pacman to that spot into the reward (how likely is it that pacman will get there in time)
                    # negative rewards around spawn point, if a ghost is there
                    self.setNegativeRewardsAtRespawn(currX, currY)
                else:
                    reward = GHOST_REWARD
                
                self.map.setValue(prevX, prevY, reward) # try to prevent pacman from running into ghost

                for (xpG, ypG), (probability, distance) in predictedGhostPath.items():
                    discountedGhostReward = 1.0/(distance+1.0) * reward * probability
                    currentReward = self.map.getValue(xpG, ypG)
                    if currentReward == None:
                        print("current reward is none")
                        self.map.setValue(xpG, ypG, discountedGhostReward) # figure out how to fix this. Gets none when ghost respawns (but only sometimes)
                    else:
                        self.map.setValue(xpG, ypG, currentReward + discountedGhostReward)

        self.previousGhosts = ghosts
        # TODO: Make the map update more efficient.


    def setNegativeRewardsAtRespawn(self, x, y):
        respawn = [(8, 5), (9, 5), (10, 5), (11, 5)]
        if (x, y) in respawn:
            for xR, yR in respawn:
                self.map.setValue(xR, yR, GHOST_REWARD)


    def prettyPrintGhostPaths(self, probabilityMap):
        # Sort the paths by distance, which is the second item in the tuple
        sortedPaths = sorted(probabilityMap.items(), key=lambda item: item[1][1])
        
        # Pretty print the sorted paths
        for position, (probability, distance) in sortedPaths:
            print "Position: %s, Probability: %.2f, Distance: %s" % (position, probability, distance)


    def getMovementDirection(self, prevX, prevY, currX, currY):
            if currY > prevY:
                return Directions.NORTH
            elif currY < prevY:
                return Directions.SOUTH
            elif currX > prevX:
                return Directions.EAST
            else:
                return Directions.WEST


    def predictGhostPath(self, startPosition, startDirection):

        # Todo: Fix prediction when ghost is eaten
        # Todo: Fix pacman running into ghost if close to it because there is reward behind ghost.

        # This dictionary will hold the accumulated probabilities of the ghost being at each position
        probabilityMap = {}
        visited = set()
        # Initialize the queue with the starting position, direction, probability and distance
        queue = deque([(startPosition, startDirection, 1.0, 0)])
        
        while queue:
            currentPosition, currentDirection, currentProbability, currentDistance = queue.popleft()

            # Mark as visited by adding the position and the direction we came from
            visited.add((currentPosition, currentDirection))

            # If the probability is already below the threshold, don't continue this path
            if ISSMALL:
                if currentProbability < 0.25:
                    continue
            else:
                if currentProbability < PREDICTION_THRESHOLD:
                    continue

            if ISSMALL and currentDistance > 9: # only predict for 9 steps ahead in small map
                continue

            if currentPosition not in probabilityMap:
                probabilityMap[currentPosition] = (currentProbability, currentDistance)

            else:
                # If this position was reached by another path, combine the probabilities
                # and store the minimum distance.
                existingProbability, existingDistance = probabilityMap[currentPosition]
                combinedProbability = max(existingProbability, currentProbability)
                minimumDistance = min(existingDistance, currentDistance)
                probabilityMap[currentPosition] = (combinedProbability, minimumDistance)

            # Get the legal moves from the current position
            legalDirections = self.legalMovesMap.getValue(currentPosition[0], currentPosition[1])
            # print("legal directions", legalDirections) 
            if legalDirections != None: # I think gets None when ghost respawns
                if len(legalDirections) > 2:
                    # If at a junction, remove the opposite direction and split probability
                    legalDirections = self.filterOppositeDirection(legalDirections, currentDirection)
                    splitProbability = currentProbability / len(legalDirections)
                    for direction in legalDirections:
                        nextPosition = self.getCoordinateAfterMove(direction, currentPosition[0], currentPosition[1])
                        if (nextPosition, currentDirection) not in visited:
                            queue.append((nextPosition, direction, splitProbability, currentDistance + 1))
                else:
                    # If the ghost is at a dead end, it should turn around
                    if len(legalDirections) == 1: 
                        currentDirection = self.getOppositeDirection(currentDirection)  # Turn around

                    # go around corner
                    elif currentDirection not in legalDirections:
                        currentDirection = [d for d in legalDirections if d != self.getOppositeDirection(currentDirection)][0]

                    # Continue in the same direction / go around corner
                    nextPosition = self.getCoordinateAfterMove(currentDirection, currentPosition[0], currentPosition[1])

                    # check if the node was visited from the same direction. This might cause some problems but should solve the issue of a ghost going into a dead end.
                    if (nextPosition, currentDirection) not in visited:
                        queue.append((nextPosition, currentDirection, currentProbability, currentDistance + 1))

        return probabilityMap

    def getOppositeDirection(self, direction):
        opposite = {
            Directions.NORTH: Directions.SOUTH,
            Directions.SOUTH: Directions.NORTH,
            Directions.EAST: Directions.WEST,
            Directions.WEST: Directions.EAST
        }
        return opposite[direction]

    def filterOppositeDirection(self, directions, currentDirection):
        # Remove the opposite direction to the current direction
        opposite = self.getOppositeDirection(currentDirection)
        return [d for d in directions if d != opposite]

    def getNAdjacentPoints(self, n, startPoint):
        rowNum = [-1, 0, 0, 1]
        colNum = [0, -1, 1, 0]
        
        visited = set() # Keep track of visited points
        dangerPoints = set() # Keep track of points within the danger zone

        # Queue for BFS, initialized with the start point and the initial distance
        queue = deque([(startPoint, 0)])
        
        while queue:
            current, dist = queue.popleft()
            
            # If the current distance is within the danger zone, add the point to dangerPoints
            if dist <= n:
                dangerPoints.add(current)
                
                # Explore the neighbours
                for i in range(4):
                    adjX, adjY = current[0] + colNum[i], current[1] + rowNum[i]
                    adjPoint = (adjX, adjY)
                    
                    # Check if the neighbour is not a wall
                    if self.map.getValue(adjX, adjY) != None:
                        # If the neighbour hasn't been visited yet, add it to the queue
                        if adjPoint not in visited:
                            visited.add(adjPoint)
                            queue.append((adjPoint, dist + 1))
        
        return list(dangerPoints)

    # def updateRewardsCapsuleEaten(self, state, x, y, edibleTime):
    #     position = api.whereAmI(state)
    #     distance = len(self.distance(position, (x, y)))
    #     # maybe dont even need the distance. could just chase in general.
    #     if edibleTime > distance: # if time is more than distance, it is worth chasing after it. Otherwise it is quite unlikely to catch it. Can refine this condition.
    #         self.map.setValue(x, y, GHOST_EDIBLE_REWARD)
    #     else:
    #         self.map.setValue(x, y, GHOST_EDIBLE_REWARD) # could make this reward a function of time and distance

    #     # negative rewards around spawn point, if a ghost is there
    #     respawn = [(8, 5), (9, 5), (10, 5), (11, 5)]
    #     if (x, y) in respawn:
    #         for xR, yR in respawn:
    #             self.map.setValue(xR, yR, GHOST_DANGER_ZONE_REWARD)


    # use BFS to find distance to a point.
    def distance(self, start, end):

        queue = deque()

        queue.append((start, [start]))
        visited = set()

        while queue:
            current, path = queue.popleft()

            if current == end:
                return path
            
            # skip if already visited
            if current in visited:
                continue

            visited.add(current)

            # enqueue all valid neighbouring cells
            # These arrays are used to get row and column numbers of 4 neighbours of a given cell
            rowNum = [-1, 0, 0, 1]
            colNum = [0, -1, 1, 0]

            for i in range(4):
                adjX, adjY = current[0] + colNum[i], current[1] + rowNum[i]
                adjPoint = (adjX, adjY)

                if self.map.getValue(adjX, adjY) != None and adjPoint not in visited:
                    queue.append((adjPoint, path + [adjPoint]))

    def getAction(self, state):
        
        legal = api.legalActions(state)
        if Directions.STOP in legal:
            legal.remove(Directions.STOP)

        position = api.whereAmI(state)
        x,y = position[0], position[1]

        self.updateMap(state, x, y)
        utilityMap = self.valueIteration()  

        maxUtilityMove = self.getMaxUtilityMove(legal, utilityMap, x, y)
        print("Pacman at ", position)
        print("Best move ", maxUtilityMove)
        self.map.prettyDisplay()
        utilityMap.prettyDisplay()

        print("==========================")
        print()
        return api.makeMove(maxUtilityMove, legal)
    

    def getMaxUtilityMove(self, legal, utilityMap, x, y):
        allUtilities = []
         # find the best move to make from these utilities   
        for action in legal:
            possibleMoveOutcomes = movePossibleResults[action] # ordering important. Intended action first.
            newUtilities = []
            for movedTo in possibleMoveOutcomes:
                new_x, new_y = self.getCoordinateAfterMove(movedTo, x, y)
                if self.map.getValue(new_x, new_y) == None: # would end up in wall bump back
                    newUtility = utilityMap.getValue(x, y)  # Pacman stays in place
                else:
                    newUtility = utilityMap.getValue(new_x, new_y) # Utility of moving to the place action leads to
                newUtilities.append(newUtility)
            
            sumUtility = self.getExpectedUtility(newUtilities)

            allUtilities.append((action, sumUtility))

        # max expected utility from actions
        return max(allUtilities, key = lambda res: res[1])[0]

    def getCoordinateAfterMove(self, direction, x, y):
        move = directionCoordinate[direction]
        x, y = move[0] + x, move[1] + y
        return x, y
    

    def valueIteration(self):

        def copyMap(map, width, height):
            copy = Grid(map.getWidth(), map.getHeight())
            for i in range(width):
                for j in range(height):
                    copy.setValue(i, j, map.getValue(i, j))
            return copy
        
        # none of the values changed more than the threshold
        def converged(new, previous, width, height):
            for i in range(width):
                for j in range(height):
                    if new.getValue(i, j) != None:
                        if abs(new.getValue(i, j) - previous.getValue(i, j)) > CONVERGENCE_THRESHOLD:
                            return False
            return True
                        
        
        # initialise utility map
        width = self.map.getWidth()
        height = self.map.getHeight()
        utilityMap = Grid(width, height)
        # Utility of all spots set to 0, except for walls (None)
        for i in range(width):
            for j in range(height):
                initialValue = 0 if self.map.getValue(i, j) != None else None
                utilityMap.setValue(i, j, initialValue)
        
        for k in range (0, ITERATIONS):
            utilityMapCopy = copyMap(utilityMap, width, height) # use to keep track of new values
            for i in range(1, width - 1):
                for j in range(1, height - 1):
                    if self.map.getValue(i, j) != None: # only compute utility for non-wall spots
                        utility = self.bellmann(utilityMapCopy, i, j)
                        utilityMap.setValue(i, j, utility)
            if converged(utilityMap, utilityMapCopy, width, height): # the result is probably precise enough to stop iterating
                print("converged after ", k, "iterations")
                break
        return utilityMap
    

    def bellmann(self, utilityMap, x, y):

        def getLegalActionsForXY(x, y):
            possible = []
            actions = [Directions.NORTH, Directions.SOUTH, Directions.EAST, Directions.WEST]
            for action in actions:
                new_x, new_y = self.getCoordinateAfterMove(action, x, y)
                if self.map.getValue(new_x, new_y) != None:
                    possible.append(action)
            return possible

        maxUtility = float('-inf')

        for action in getLegalActionsForXY(x, y):
            possibleMoveOutcomes = movePossibleResults[action] # ordering important. Intended action first.
            newUtilities = []
            for movedTo in possibleMoveOutcomes:
                new_x, new_y = self.getCoordinateAfterMove(movedTo, x, y)
                if self.map.getValue(new_x, new_y) == None: # would end up in wall > bump back
                    newUtility = utilityMap.getValue(x, y)  # Pacman stays in place
                else:
                    newUtility = utilityMap.getValue(new_x, new_y) # Utility of moving to the place action leads to
                newUtilities.append(newUtility)

            # print("action ", action, "utilities", newUtilities)
            sumUtility = self.getExpectedUtility(newUtilities)
            # update the maximum utility
            if sumUtility > maxUtility:
                maxUtility = sumUtility

        reward = self.map.getValue(x, y)
        # utiliy = reward of being state s + discount * (utility of action with the max utility outcome) 
        utility = reward + GAMMA * maxUtility

        return utility

    # Hardcoded probabilities. Depends on the correct ordering of the rewards array. 
    def getExpectedUtility(self, rewards):
        expected = 0
        expected += 0.8 * rewards[0]
        expected += 0.1 * rewards[1]
        expected += 0.1 * rewards[2]
        
        return expected