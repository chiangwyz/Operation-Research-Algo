"""
An example of Benders Decomposition on fixed charge transportation
problem bk4x3.
Optimal objective in reference : 350.
Erwin Kalvelagen, December 2002
See:
http://www.in.tu-clausthal.de/~gottlieb/benchmarks/fctp/

use COPT to calculate it 
author: JIANG DAPEI
"""

import sys
import coptpy as cp
from coptpy import COPT

class FCTP:
    def __init__(self):
        # Initialize data
        self.nsuppliers = 0
        self.ndemanders = 0
        self.supply = []
        self.demand = []
        self.fixcost = []
        self.transportcost = []

        # Initialize variables and constraints
        self.var_x = []
        self.var_y = []
        self.constr_demand = []
        self.constr_supply = []
        self.constr_link = []

        # Initialize COPT environment
        self.coptenv = cp.Envr()

    def input_date(self):
        # Input data
        self.nsuppliers = 4
        self.ndemanders = 3

        self.supply = [10, 30, 40, 20]
        self.demand = [20, 50, 30]
        fix_cost = [10, 30, 20]
        self.fixcost = [fix_cost[:] for _ in range(self.nsuppliers)]
        self.transportcost = [[2.0, 3.0, 4.0], [3.0, 2.0, 1.0], [1.0, 4.0, 3.0], [4.0, 5.0, 2.0]]
        # 使用最大的供应量作为bigM
        self.bigM = max(self.demand)

    def build(self):
        try:
            # Define the master problem
            self.masterprob = self.coptenv.createModel("FCTP problem")

            # display log information
            self.masterprob.setParam(COPT.Param.Logging, 1)

            # Construct master problem
            # add variables
            for i in range(self.nsuppliers):
                var_list = []
                for j in range(self.ndemanders):
                    var_list.append(self.masterprob.addVar(lb=0.0, ub=COPT.INFINITY, vtype=COPT.CONTINUOUS, name="x_"+str(i+1)+"_"+str(j+1)))
                self.var_x.append(var_list)
            for i in range(self.nsuppliers):
                var_list = []
                for j in range(self.ndemanders):
                    var_list.append(self.masterprob.addVar(lb=0, ub=1, vtype=COPT.BINARY, name="y_"+str(i+1)+"_"+str(j+1)))
                self.var_y.append(var_list)

            # add constraints
            for j in range(self.ndemanders):
                self.constr_demand.append(self.masterprob.addConstr(cp.quicksum(self.var_x[i][j] for i in range(self.nsuppliers))
                                                                    >= self.demand[j]))
            for i in range(self.nsuppliers):
                self.constr_supply.append(self.masterprob.addConstr(
                    cp.quicksum(self.var_x[i][j] for j in range(self.ndemanders)) <= self.supply[i]))
            for i in range(self.nsuppliers):
                expr_list = []
                for j in range(self.ndemanders):
                    expr = cp.LinExpr([(self.var_x[i][j], 1), (self.var_y[i][j], - self.bigM)])
                    self.constr_link.append(self.masterprob.addConstr(expr, COPT.LESS_EQUAL, 0, name="link_"+str(i+1) + "_" + str(j+1)))


            # add objective
            self.masterprob.setObjective(cp.quicksum(self.transportcost[i][j] * self.var_x[i][j] + self.fixcost[i][j] * self.var_y[i][j] \
                                                  for i in range(self.nsuppliers) for j in range(self.ndemanders))
                                         , COPT.MINIMIZE)


        except cp.CoptError as e:
            print('Return code' + str(e.retcode) + ': ' + e.message)

    def solve(self):
        # Build the master problem
        self.build()

        # Solve the master problem
        print("               *** Start solve ***               ")
        self.masterprob.solve()
        print("               *** End solve ***               \n")

    def report(self):
        print("               *** Summary Report ***               ")
        print("Best objective: {0}".format(self.masterprob.objval))

        print("Variables solution:")
        for var in self.masterprob.getVars():
            if var.name.startswith("x") and var.x > 1e-3:
                print("{} = {}".format(var.name, var.x))

        for var in self.masterprob.getVars():
            if var.name.startswith("y") and 1 - var.x < 1e-3:
                print("{} = {}".format(var.name, 1))

if __name__ == "__main__":
    fctp = FCTP()
    fctp.input_date()
    fctp.build()
    fctp.solve()
    fctp.report()

