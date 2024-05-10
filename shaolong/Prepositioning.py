# -*- coding: utf-8 -*-
"""
Benders for Pre-positioning: master problem and subproblem

@author: shaol

"""
from __future__ import division, print_function

import gurobipy as GRBPY
import pandas as pd
import numpy as np


# awkward restriction for 'callback'
def cbprepositioning(model, where):
    if where == GRBPY.GRB.Callback.MIPSOL:
        if model._iter >= 1:
            for s in model._NS:
                for a in model._AS:
                    for i in model._IS:
                        model._csupply[s,a,i].rhs = model.cbGetSolution(model._y[a,i])

        model._sub.optimize()

        if model._sub.status == GRBPY.GRB.INFEASIBLE:
            print("Iteration: ", model._iter)
            print("Adding feasibility cut...\n")

            lazycut = GRBPY.quicksum(model._csupply[s,a,i].farkasdual * model._y[a,i] for s in model._NS for a in model._AS for i in model._IS) +\
                      GRBPY.quicksum(model._cdemand[s,a,i].farkasdual * model._D[s,a,i] for s in model._NS for a in model._AS for i in model._IS)

            model.cbLazy(lazycut <= 0)

            model._iter += 1
        elif model._sub.status == GRBPY.GRB.OPTIMAL:
            if model._sub.objval > model.cbGetSolution(model._maxshipcost) + 1e-6:
                print("Iteration: ", model._iter)
                print("Adding optimality cut...\n")

                lazycut = GRBPY.quicksum(model._csupply[i].pi * model._supply[i] * model._vmbuild[i] \
                                         for i in range(model._nwarehouse)) + \
                          sum(model._cdemand[i].pi * model._demand[i] for i in range(model._nstore))
                lazycut = GRBPY.quicksum(model._csupply[s,a,i].pi * model._y[a,i] for s in model._NS for a in model._AS for i in model._IS) +\
                      GRBPY.quicksum(model._cdemand[s,a,i].pi * model._D[s,a,i] for s in model._NS for a in model._AS for i in model._IS)

                model.cbLazy(model._maxexpectedcost >= lazycut)

                model._iter += 1
        else:
            model.terminate()

class Prepositioning:
    '''
    def __init__(self):

        # initialize variables and constraints
        self.x = []
        self.y = []
        self.q = []
        self.z = []
        self.w = []
        
        self.csupply = []
        self.cdemand = []
    '''
    def read(self, filename):
        # input data
        print('define set ...\n')
        self.IS = 20 #Set of locations
        self.AS = 3 #Set of item types
        self.LS = 3 #Set of size categories
        self.NS = 100 #scenario

        print('define parameters ...\n')
        self.scenario_data = pd.read_excel(filename,'scenario_20')
        self.main_data = pd.read_excel(filename, 'main_data_20', header=None)
        # probability
        self.pr = self.scenario_data['w1'].to_numpy()
    
        # demand
        self.Dr = np.empty((self.NS,self.IS,self.AS))
        self.Dr[:,:,0] = self.scenario_data.iloc[:self.NS,1:self.IS+1].to_numpy()
        self.Dr[:,:,1] = np.rint((self.Dr[:,:,0] / 4))
        self.Dr[:,:,2] = np.rint((self.Dr[:,:,0] / 8))
    
        # Fixed cost, Storage capacity, volume of items
        self.CF = self.main_data.loc[1,1:3].to_numpy()
        self.U = self.main_data.loc[2,1:3].to_numpy()
    
        # Distance
        self.H = self.main_data.loc[8:27,1:].to_numpy()
    
        #volume of items
        self.V = self.main_data.loc[1,6:8].to_numpy()
        # Unit procurement price
        self.CP = self.main_data.loc[2,6:8].to_numpy()
        # Unit transportation cost
        self.CT = self.main_data.loc[3,6:8].to_numpy()
        # Unit holding cost
        self.CH = self.main_data.loc[4,6:8].to_numpy()
        # Unit penalty cost
        self.G = self.main_data.loc[5,6:8].to_numpy()
        
        #此系数的设置是根据物资单位来定的
        self.D = np.zeros((self.NS,self.AS,self.IS))
        for j in range(self.IS):
            for a in range(self.AS):
                for s in range(self.NS):
                     self.D[s,a,j] = np.rint(self.Dr[s,j,a] * 0.03)
        
        # create sets
        self.IS = range(self.IS)
        self.AS = range(self.AS)
        self.LS = range(self.LS)
        self.NS = range(self.NS)

    def build(self):
        try:
            # define models for 'master' and 'sub'
            self.master = GRBPY.Model("master")
            self.sub = GRBPY.Model("sub")

            # disable log information
            self.master.setParam("OutputFlag", 0)
            self.sub.setParam("OutputFlag", 0)

            # use lazy constraints
            self.master.setParam("LazyConstraints", 1)

            # disable presolving in subproblem
            self.sub.setParam("Presolve", 0)

            # required to obtain farkas dual
            self.sub.setParam("InfUnbdInfo", 1)

            # use dual simplex
            self.sub.setParam("Method", 1)

            # construct master problem           
            self.x = self.master.addVars(self.IS,self.LS,vtype=GRBPY.GRB.BINARY, name="x")
            self.y = self.master.addVars(self.AS,self.IS,vtype=GRBPY.GRB.INTEGER, name="y")

            self.maxexpectedcost = self.master.addVar(0.0, GRBPY.GRB.INFINITY, 0.0, GRBPY.GRB.CONTINUOUS)
            
            self.master.addConstrs((GRBPY.quicksum(self.y[a,i] * self.V[a] for a in self.AS) <= GRBPY.quicksum(self.x[i,l] * self.U[l] for l in self.LS) for i in self.IS), 
                         "Constraint (2)")

            self.master.setObjective(GRBPY.quicksum(self.CF[i] * self.x[i,l] for i in self.IS for l in self.LS) +
                                     GRBPY.quicksum(self.CP[a] * self.y[a,i] for a in self.AS for i in self.IS) +
                                                    self.maxexpectedcost, GRBPY.GRB.MINIMIZE)

            # construct subproblem
            self.q = self.sub.addVars(self.NS,self.AS,self.IS,self.IS,vtype=GRBPY.GRB.INTEGER, name="q")   
            self.z = self.sub.addVars(self.NS,self.AS,self.IS,vtype=GRBPY.GRB.INTEGER, name="z")
            self.w = self.sub.addVars(self.NS,self.AS,self.IS,vtype=GRBPY.GRB.INTEGER, name="w")
            self.hc = self.sub.addVars(self.NS,vtype=GRBPY.GRB.CONTINUOUS, name="hc")
            self.tc = self.sub.addVars(self.NS,vtype=GRBPY.GRB.CONTINUOUS, name="tc")
            self.wc = self.sub.addVars(self.NS,vtype=GRBPY.GRB.CONTINUOUS, name="wc")

            self.csupply = self.sub.addConstrs((self.z[s,a,i] + GRBPY.quicksum(self.q[s,a,i,j] for j in self.IS) == self.D[s,a,i]
                                                for a in self.AS for i in self.IS for s in self.NS),"Constraint (3)")

            self.cdemand = self.sub.addConstrs((self.w[s,a,j] + GRBPY.quicksum(self.q[s,a,i,j] for i in self.IS) == self.D[s,a,j]
                                                for a in self.AS for j in self.IS for s in self.NS),"Constraint (4)")
            
            #sub objective functions
            # C05
            self.sub.addConstrs((self.wc[s] == GRBPY.quicksum(self.G[a] * self.w[s,a,j] 
                                       for a in self.AS for j in self.IS) for s in self.NS), "Shortage Costs")
                
            self.sub.addConstrs((self.hc[s] == GRBPY.quicksum(self.CH[a] * self.z[s,a,i] 
                                       for a in self.AS for i in self.IS) for s in self.NS), "Surplus Costs")
            
            self.sub.addConstrs((self.tc[s] == GRBPY.quicksum(self.CT[a] * self.H[i,j] * self.q[s,a,i,j] 
                                       for a in self.AS for i in self.IS for j in self.IS) for s in self.NS), "Transportation Costs")

            self.sub.setObjective(GRBPY.quicksum(self.pr[s] * (self.tc[s] + self.hc[s] + self.wc[s]) for s in self.NS), GRBPY.GRB.MINIMIZE)
            
        except GRBPY.GurobiError as e:
            print('Error code' + str(e.errno) + ': ' + str(e))
        except AttributeError as e:
            print('Encountered an attribute error: ' + str(e))

    def solve(self):
        # build 'master' and 'sub'
        self.build()

        # register callback
        self.master._iter = 0
        self.master._IS = self.IS
        self.master._LS = self.LS
        self.master._AS = self.AS
        self.master._NS = self.NS
        
        self.master._pr = self.pr
        self.master._CF = self.CF
        self.master._U = self.U
        self.master._H = self.H
        self.master._V = self.V
        self.master._CP = self.CP
        self.master._CT = self.CT
        self.master._CH = self.CH
        self.master._G = self.G
        self.master._D = self.D

        self.master._csupply = self.csupply
        self.master._cdemand = self.cdemand
        self.master._x = self.x
        self.master._y = self.y
        self.master._maxexpectedcost = self.maxexpectedcost

        self.master._sub = self.sub

        # optimize master problem
        print("               *** Benders Decomposition Loop ***               ")
        self.master.optimize(cbprepositioning)
        print("                        *** End Loop ***                        ")

        # it seems that 64-bit needs this extra work
        for s in self.NS:
            for a in self.AS:
                for i in self.IS:
                    self.csupply[s,a,i].rhs = self.y[a,i].x

        self.sub.optimize()

    def report(self):
        print("               *** Summary Report ***               ")
        print("Objective: %.6f" % self.master.objval)
        '''
        print("Variables:")
        for i in range(self.nwarehouse):
            if abs(self.vmbuild[i].x) > 1e-6:
                print("  Build[%d] = %.0f" % (i, self.vmbuild[i].x))

        for i in range(self.nwarehouse):
            for j in range(self.nstore):
                if abs(self.vship[i][j].x) > 1e-6:
                    print("  Ship[%d][%d] = %.6f" % (i, j, self.vship[i][j].x))
        '''
if __name__ == "__main__":
    prepositioning = Prepositioning()
    prepositioning.read("data.xlsx")
    prepositioning.solve()
    prepositioning.report()