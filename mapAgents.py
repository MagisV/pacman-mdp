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

from pacman import Directions
from game import Agent
import api
import random
import game
import util
import sys

FOOD_VALUE = 10
EMTPY_VALUE = -1

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
#
# An agent that creates a map.
#
# As currently implemented, the map places a % for each section of
# wall, a * where there is food, and a space character otherwise. That
# makes the display look nice. Other values will probably work better
# for decision making.
#
class MapAgent(Agent):

    # The constructor. We don't use this to create the map because it
    # doesn't have access to state information.
    def __init__(self):
        print "Running init!"

    # This function is run when the agent is created, and it has access
    # to state information, so we use it to build a map for the agent.
    def registerInitialState(self, state):
         print "Running registerInitialState!"
         # Make a map of the right size
         self.makeMap(state)
         self.addWallsToMap(state)
         self.updateFoodInMap(state)
        #  self.map.display()

    # This is what gets run when the game ends.
    def final(self, state):
        print "Looks like I just died!"

    # Make a map by creating a grid of the right size
    def makeMap(self,state):
        corners = api.corners(state)
        height = self.getLayoutHeight(corners)
        width  = self.getLayoutWidth(corners)
        self.map = Grid(width, height)
        
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
    def updateFoodInMap(self, state):
        # First, make all grid elements that aren't walls blank.
        for i in range(self.map.getWidth()):
            for j in range(self.map.getHeight()):
                if self.map.getValue(i, j) != None:
                    self.map.setValue(i, j, EMTPY_VALUE)
        food = api.food(state)
        for i in range(len(food)):
            self.map.setValue(food[i][0], food[i][1], FOOD_VALUE)
 
    # For now I just move randomly, but I display the map to show my progress
    def getAction(self, state):
        self.updateFoodInMap(state)        
        legal = api.legalActions(state)

        # removing stop for now, might be worth adding back later on.
        if Directions.STOP in legal:
            legal.remove(Directions.STOP)

        position = api.whereAmI(state)

        rewards = []
        for action in legal:
            currRewards = []
            for direction in movePossibleResults[action]:
                new_x, new_y = self.getCoordinateAfterMove(direction, position)
                rewardValue = self.map.getValue(new_x, new_y)
                currRewards.append(rewardValue)
            rewards.append((action, self.getExpectedValue(currRewards)))
        print(rewards)
        # max expected utility from legal actions
        maxRewardMove = max(rewards, key = lambda res: res[1])[0] # if the rewards are the same, this will always pick west > east -> can get stuck in corners. Will probably change with next implementation.
        return api.makeMove(maxRewardMove, legal)
    
    def getExpectedValue(self, rewards):

        # bumping into wall gives reward of 0. Check what happens when bumping into wall and possibly change accordingly.
        def valOrZero(val):
            return 0 if val == None else val
        
        expected = 0
        expected += 0.8 * valOrZero(rewards[0])
        expected += 0.1 * valOrZero(rewards[1])
        expected += 0.1 * valOrZero(rewards[2])

        
        
        return expected


    def getCoordinateAfterMove(self, direction, position):
        move = directionCoordinate[direction]
        x, y = move[0] + position[0], move[1] + position[1]
        return x, y

   
