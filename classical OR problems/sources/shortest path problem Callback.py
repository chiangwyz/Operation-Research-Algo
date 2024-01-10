#
#  This file is part of the Cardinal Optimizer, all rights reserved.
#
#
#
# In the MIP formulation of asymmetric TSP problem, binary variables e[i,j] indicate whether
#  there is a directed edge between city[i] and city[j]. The weight of edge is distance
#  from city[i] to city[j]. The constraints are as follows:
#    1. Each city[i] must have exactly outdegree 1
#    2. Each city[i] must have exactly indegree 1
#
#    minimize    sum_ij {dist[i, j] * e[i, j]}
#    subject to  sum_j e[i,j] = 1 for each i
#                sum_i e[i,j] = 1 for each j
#
# Note that solutions to this model may contain subtours, which don't visit all cities.
# The lazy constraint callback adds new constraints to cut them off.
#
"""
Using COPT callback to solve a traveling salesman problem on randomly generated cities.

"""

import sys
import math
import random
import matplotlib.pyplot as plt

import coptpy as cp
from coptpy import COPT


def get_distance(pi, pj):
    """
    Calculate euclidean distance between i-th and j-th points.
    """
    return math.sqrt((pi[0] - pj[0]) ** 2 + (pi[1] - pj[1]) ** 2)


def find_subtour(solution):
    """
    Given an integer-feasible solution, which is tupledict,
    find the shortest sub-tour. Result is returned as 'tour' list
    """

    # Build a list of edges (i, j) selected from the solution
    edges = cp.tuplelist((i, j)
                      for i, j in solution.keys() if solution[i, j] > 0.5)
    unvisited = list(range(nCities))

    # Initialize sub-tour with one more city
    bestTour = range(nCities + 1)
    while unvisited:  # When still having unvisited cities
        tour = []
        # Initialize neighbors with first unvisited city
        neighbors = [unvisited[0]]
        while neighbors:
            curr = neighbors[0]
            tour.append(curr)
            unvisited.remove(curr)
            # Enumerate all unvisited neighbors of current city
            neighbors = [j for i, j in edges.select(
                curr, '*') if j in unvisited]
        # Save the current tour if it is better
        if len(bestTour) > len(tour):
            bestTour = tour
    return bestTour


def draw_tours(cities, edges, vars):
    """
    Draw tours with current solution
    """

    tour = []
    for var in vars.select():
        if var.x > 0.5:
            tour.append(edges[var.index])

    nCities = len(cities)
    plt.figure(figsize=(5, 5))
    for i in range(nCities):
        plt.scatter(cities[i][0], cities[i][1], color='blue', marker='o')

    for i in range(nCities):
        plt.text(cities[i][0], cities[i][1], i)

    for i, j in tour:
        plt.arrow(cities[i][0], cities[i][1],
                  cities[j][0]-cities[i][0], cities[j][1]-cities[i][1],
                  color='red', head_width=0.02, length_includes_head=True)
    plt.show()


class TspCallback(cp.CallbackBase):
    """
    Customize callback class. User must implement callback().
    For more information of callback methods, refer to CallbackBase.
    """

    def __init__(self, vars, nCities) -> None:
        super().__init__()
        self._vars = vars
        self._nCities = nCities

    def callback(self) -> None:
        if self.where() == COPT.CBCONTEXT_MIPSOL:
            solution = self.getSolution(self._vars)
            tour = find_subtour(solution)
            sz = len(tour)
            if sz < self._nCities:
                self.addLazyConstr(
                    cp.quicksum(vars[tour[i], tour[i+1]] for i in range(sz - 1))
                    + vars[tour[-1], tour[0]] <= sz - 1)


if __name__ == "__main__":
    # Parse argument
    nCities = 10
    if len(sys.argv) > 1:
        nCities = int(sys.argv[1])

    # Create random points
    random.seed(1)
    cities = [[random.random(), random.random()] for i in range(nCities)]

    distances = dict()
    for i in range(nCities):
        for j in range(i + 1, nCities):
            distances[(j, i)] = distances[(i, j)] = get_distance(
                cities[i], cities[j])
    edges = list(distances.keys())

    # Create COPT environment and model
    env = cp.Envr()
    model = env.createModel("TSP Callback Example")

    # Add 0-1 variables, one for every pair of cities
    vars = model.addVars(edges, vtype=COPT.BINARY, nameprefix='e')

    # Add outdegree-1 constraint for TSP loop
    model.addConstrs(vars.sum(i, '*') == 1 for i in range(nCities))
    # Add indegree-1 constraint for TSP loop
    model.addConstrs(vars.sum('*', j) == 1 for j in range(nCities))

    # Set objective function
    model.setObjective(vars.prod(distances), sense=COPT.MINIMIZE)

    # Set TSP callback instance
    tcb = TspCallback(vars, nCities)
    model.setCallback(tcb, COPT.CBCONTEXT_MIPSOL)

    # Solve the TSP problem
    model.solve()

    # Output the result
    if model.hasmipsol:
        solution = model.getInfo(COPT.Info.Value, vars)
        tour = find_subtour(solution)
        assert len(tour) == nCities

        print("")
        print("Optimal tour:{}".format(str(tour)))
        print("Optimal cost:{}".format(model.ObjVal))
    else:
        print("Fail to get best TSP tour")

    draw_tours(cities, edges, vars)
    print("\n***** TSP Callback Example Finished *****")
