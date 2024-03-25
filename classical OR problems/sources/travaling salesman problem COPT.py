"""
2024-1-10 16:11:12
author: Dapei JIANG

Using COPT to solve a traveling salesman problem with c101.txt, refer COPT provided example.
There are two ways to solve this problem, one with MTZ constraints, another with lazy constraints.
We use VRP case c101 to generate the problem.
"""

import re
import math
import matplotlib.pyplot as plt

import coptpy as cp
from coptpy import COPT


def find_subtour(solution: cp.tupledict) -> list[int]:
    """
    Given an integer-feasible solution, which is tupledict,
    find the shortest sub-tour. Result is returned as 'tour' list
    """

    # edges (i, j) is tuplelist type
    edges = cp.tuplelist((i, j) for i, j in solution.keys() if solution[i, j] > 0.5)
    unvisited = list(range(data.nodeNum))

    # Initialize sub-tour with one more city
    bestTour = range(data.nodeNum + 1)
    # bestTour = range(1)
    while unvisited:  # When still having unvisited cities
        tour = []
        # Initialize neighbors with first unvisited city
        neighbors = [unvisited[0]]
        while neighbors:
            curr = neighbors[0]
            tour.append(curr)
            unvisited.remove(curr)
            # Enumerate all unvisited neighbors of current city
            neighbors = [j for i, j in edges.select(curr, '*') if j in unvisited]
        # Save the current tour if it is better
        if len(tour) < len(bestTour):
            bestTour = tour
    return bestTour

def draw_tours(nodeCoordinate, edges, vars):
    """
    Draw tours
    """
    tour = []
    for var in vars.select():
        if var.x > 0.5:
            tour.append(edges[var.index])

    nCities = len(nodeCoordinate)
    plt.figure(figsize=(5, 5))
    for i in range(nCities):
        plt.scatter(nodeCoordinate[i][0], nodeCoordinate[i][1], color='blue', marker='o')

    for i in range(nCities):
        plt.text(nodeCoordinate[i][0], nodeCoordinate[i][1], i)

    for i, j in tour:
        plt.arrow(nodeCoordinate[i][0], nodeCoordinate[i][1],
                  nodeCoordinate[j][0]-nodeCoordinate[i][0], nodeCoordinate[j][1]-nodeCoordinate[i][1],
                  color='red', head_width=0.02, length_includes_head=True)
    plt.show()


class TSPCallback(cp.CallbackBase):
    def __init__(self, vars: cp.tupledict, nodeNum) -> None:
        super().__init__()
        self._vars = vars
        self._nodeNum = nodeNum

    def callback(self) -> None:
        if self.where() == COPT.CBCONTEXT_MIPSOL:
            # print("invoke callback")

            # solution is a tupledict
            solution = self.getSolution(self._vars)
            # for sol_key, sol_value in solution.items():
            #     print("{} = {}".format(sol_key, sol_value))
            tour = find_subtour(solution)
            sz = len(tour)
            if sz < self._nodeNum:
                self.addLazyConstr(
                    cp.quicksum(vars[tour[i], tour[i+1]] for i in range(sz - 1))
                    + vars[tour[-1], tour[0]] <= sz - 1)


class Data:
    def __init__(self):
        # basic data
        self.nodeNum = 0
        self.vehicleNum = 0
        self.capacity = 0
        self.cor_X = []
        self.cor_Y = []
        self.nodeCoordinate = []
        self.demand = []
        self.serviceTime = []
        self.readyTime = []
        self.dueTime = []
        self.disMatrix = [[]]
        self.edges = []

    def readData(self, file_path: str):
        with open(file_path, 'r') as f:
            lines = f.readlines()

        # Extract vehicle number and capacity from the file
        vehicle_info = lines[4].strip()
        self.vehicleNum, self.capacity = map(int, re.split(r" +", vehicle_info)[:2])

        # Process customer data, ignore the depot, we only consider 100 nodes with TSP
        for line in lines[10:]:
            line = line.strip()
            if line:  # check if line is not empty
                string = re.split(r" +", line)
                x, y, demand_val, ready, due, service = map(int, string[1:7])
                self.cor_X.append(x)
                self.cor_Y.append(y)
                self.demand.append(demand_val)
                self.readyTime.append(ready)
                self.dueTime.append(due)
                self.serviceTime.append(service)
                self.nodeNum += 1
            else:
                break  # stop reading if an empty line is encountered

        # for test
        self.nodeNum = 20

        self.nodeCoordinate = [[self.cor_X[i], self.cor_Y[i]] for i in range(self.nodeNum)]

        # Compute distance matrix
        self.disMatrix = [
            [round(math.sqrt((self.cor_X[i] - self.cor_X[j]) ** 2 + (self.cor_Y[i] - self.cor_Y[j]) ** 2), 2)
             for j in range(self.nodeNum)] for i in range(self.nodeNum)]


    def printData(self):
        print(" 打印数据以供校验\n")
        print("node number = {}".format(self.nodeNum))
        print("vehicle number = {}".format(self.vehicleNum))
        print("vehicle capacity = {}".format(self.capacity))

        print("DEMAND\tXCOORD.\tYCOORD.\tREADY TIME\tDUE DATE\tSERVICE TIME")
        for i in range(self.nodeNum):
            print("{}\t{}\t{}\t{}\t{}\t{}".format(self.demand[i], self.cor_X[i], self.cor_Y[i], self.readyTime[i], self.dueTime[i], self.serviceTime[i]))

        print("\n--------距离矩阵--------")
        # for i in range(self.nodeNum):
        #     for j in range(self.nodeNum):
        #         print("\t{}".format(self.disMatrix[i][j]), end=" ")
        #     print()


if __name__ == "__main__":
    # Initial data class and read it
    data = Data()
    data.readData("c101.txt")

    # verify data
    data.printData()

    # Create COPT environment and model
    env = cp.Envr()
    TSP_model = env.createModel("TSP Callback Example")

    # Create variable tupledict
    vars = cp.tupledict()

    # x_ij, decision variable
    for i in range(data.nodeNum):
        for j in range(data.nodeNum):
            if i != j:
                vars[i, j] = TSP_model.addVar(vtype=COPT.BINARY, name="x_" + str(i) + "_" + str(j))

    # add constraint 1
    for j in range(data.nodeNum):
        lhs = cp.LinExpr(0)
        for i in range(data.nodeNum):
            if i != j:
                lhs.addTerm(vars[i, j], 1)
                data.edges.append((i, j))
        TSP_model.addConstr(lhs == 1, name="in_" + str(j))

    # add constraint 2
    for i in range(data.nodeNum):
        lhs = cp.LinExpr(0)
        for j in range(data.nodeNum):
            if i != j:
                lhs.addTerm(vars[i, j], 1)
        TSP_model.addConstr(lhs == 1, name="out_" + str(i))

    # create objective
    obj = cp.LinExpr(0)
    for i in range(data.nodeNum):
        for j in range(data.nodeNum):
            if i != j:
                obj.addTerms(vars[i, j], data.disMatrix[i][j])

    TSP_model.setObjective(obj, sense=COPT.MINIMIZE)
    TSP_model.write("tsp_callback.lp")

    # callback
    tsp_cb = TSPCallback(vars, data.nodeNum)
    # CBCONTEXT_MIPSOL, Invokes the callback when a new MIP candidate solution is found.
    TSP_model.setCallback(tsp_cb, COPT.CBCONTEXT_MIPSOL)

    # Solve the TSP problem
    TSP_model.solve()

    # Output the result
    if TSP_model.hasmipsol:
        solution = TSP_model.getInfo(COPT.Info.Value, vars)
        tour = find_subtour(solution)
        assert len(tour) == data.nodeNum

        print("")
        print("Optimal tour:{}".format(str(tour)))
        print("Optimal cost:{}".format(TSP_model.ObjVal))
    else:
        print("Fail to get best TSP tour")

    print("\n***** TSP Callback Example Finished *****")

    # draw the route
    draw_tours(data.nodeCoordinate, data.edges, vars)
