# -*- coding: utf-8 -*-
"""
Benders for Pre-positioning: master problem and subproblem

@author: shaol

"""
from __future__ import division, print_function
from plugins import append_df_to_excel
import gurobipy as GRBPY
import pandas as pd
import numpy as np
import time

tic = time.perf_counter()
# awkward restriction for 'callback'
def cbprepositioning(model, where):
    if where == GRBPY.GRB.Callback.MIPSOL:
        if model._iter >= 1:
            for a in model._AS:
                for i in model._IS:
                    for s in model._NS:
                        model._alpha[a,i,s].obj = model.cbGetSolution(model._y[a,i])
                        for j in model._IS:
                            model._beta[a,j,s].obj = model._D[a,j,s]

        model._sub.optimize()

        if model._sub.status == GRBPY.GRB.INFEASIBLE:
            print("Iteration: ", model._iter)
            print("Adding feasibility cut...\n")

            lazycut = GRBPY.quicksum(model._alpha[a,i,s].unbdray * model._y[a,i] for a in model._AS for i in model._IS for s in model._NS) +\
                      GRBPY.quicksum(model._beta[a,j,s].unbdray * model._D[a,j,s] for a in model._AS for j in model._IS for s in model._NS)
            #使用gurobi通过farkasdual抓约束的极射线时数值方向是相反的，所以要改成>=
            #使用gurobi通过unbdray抓变量的极射线时数值方向可能也是相反的，可能也要改成>=？
            model.cbLazy(lazycut <= 0)

            model._iter += 1
        elif model._sub.status == GRBPY.GRB.OPTIMAL:
            print("obj of sub problem: ", model._sub.objval)
            #print("expected cost: ", model.cbGetSolution(model._maxexpectedcost))
            #print("gap: ", ((model._sub.objval-model.cbGetSolution(model._maxexpectedcost) + 1e-6)/(model._sub.objval + 1e-6)))
            if ((model._sub.objval-model.cbGetSolution(model._maxexpectedcost) + 1e-6)/(model._sub.objval + 1e-6)) > 0.001:
                print("Iteration: ", model._iter)
                print("Adding optimality cut...\n")

                lazycut = GRBPY.quicksum(model._alpha[a,i,s].x * model._y[a,i] for a in model._AS for i in model._IS for s in model._NS) +\
                          GRBPY.quicksum(model._beta[a,j,s].x * model._D[a,j,s] for a in model._AS for j in model._IS for s in model._NS)
                model.cbLazy(lazycut <= model._maxexpectedcost)

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
        self.IS = 10 #Set of locations
        #self.IS = 20 #Set of locations
        self.AS = 3 #Set of item types
        self.LS = 3 #Set of size categories
        self.NS = 100 #scenario

        print('define parameters ...\n')
        self.scenario_data = pd.read_excel(filename,'scenario_20')
        self.main_data = pd.read_excel(filename, 'main_data_20', header=None)
        # probability
        self.pr = self.scenario_data['w1'].to_numpy()
    
        # demand: 此系数的设置是根据物资单位来定的
        self.D = np.empty((self.AS,self.IS,self.NS))
        self.D[0,:,:] = np.rint(self.scenario_data.iloc[:self.NS,1:self.IS+1].to_numpy().T* 0.03)
        self.D[1,:,:] = np.rint((self.D[0,:,:] / 4))
        self.D[2,:,:] = np.rint((self.D[0,:,:] / 8))
    
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
            self.master.setParam("OutputFlag", 1)
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

            self.maxexpectedcost = self.master.addVar(vtype=GRBPY.GRB.CONTINUOUS,name='f')
            
            self.master.addConstrs((GRBPY.quicksum(self.y[a,i] * self.V[a] for a in self.AS) <= GRBPY.quicksum(self.x[i,l] * self.U[l] for l in self.LS) for i in self.IS), 
                         "Constraint (2)")
            
            self.master.addConstrs((GRBPY.quicksum(self.x[i,l] for l in self.LS) <= 1 for i in self.IS), 
                         "Constraint (3)")
            
            self.master.setObjective(GRBPY.quicksum(self.CF[l] * self.x[i,l] for i in self.IS for l in self.LS) +
                                     GRBPY.quicksum(self.CP[a] * self.y[a,i] for a in self.AS for i in self.IS) +
                                                    self.maxexpectedcost, GRBPY.GRB.MINIMIZE)

            # construct subproblem  
            self.alpha = self.sub.addVars(self.AS,self.IS,self.NS,lb=-GRBPY.GRB.INFINITY, ub=GRBPY.GRB.INFINITY, vtype=GRBPY.GRB.CONTINUOUS, name="alpha")
            self.beta = self.sub.addVars(self.AS,self.IS,self.NS,lb=-GRBPY.GRB.INFINITY, ub=GRBPY.GRB.INFINITY,vtype=GRBPY.GRB.CONTINUOUS, name="beta")
            self.f = self.sub.addVars(self.AS,self.NS,vtype=GRBPY.GRB.CONTINUOUS, name="f")

            self.sub.addConstrs((self.alpha[a,i,s] <= self.pr[s] * self.CH[a]
                                     for a in self.AS for i in self.IS for s in self.NS),"Constraint (13)")

            self.sub.addConstrs((self.beta[a,j,s] <= self.pr[s] * self.G[a]
                                     for a in self.AS for j in self.IS for s in self.NS),"Constraint (14)")
            
            self.sub.addConstrs((self.alpha[a,i,s] + self.beta[a,j,s] <= self.pr[s] * self.CT[a] * self.H[i,j]
                                     for a in self.AS for i in self.IS for j in self.IS for s in self.NS),"Constraint (15)")
            
            self.sub.addConstrs((self.f[a,s] == GRBPY.quicksum(self.D[a,i,s] * self.alpha[a,i,s] for i in self.IS) + 
                                                GRBPY.quicksum(self.D[a,j,s] * self.beta[a,j,s] for j in self.IS)
                                                                         for a in self.AS for s in self.NS), "objective function")
            
            #sub objective functions             
            self.sub.setObjective(GRBPY.quicksum(self.f[a,s] for a in self.AS for s in self.NS), GRBPY.GRB.MAXIMIZE)
            self.sub.write("sub problem.lp")
            
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

        self.master._alpha = self.alpha
        self.master._beta = self.beta
        self.master._x = self.x
        self.master._y = self.y
        self.master._maxexpectedcost = self.maxexpectedcost

        self.master._sub = self.sub

        # optimize master problem
        print("               *** Benders Decomposition Loop ***               ")
        self.master.optimize(cbprepositioning)
        print("                        *** End Loop ***                        ")
        
        # it seems that 64-bit needs this extra work        
        for a in self.AS:
            for i in self.IS:
                for s in self.NS:
                    self.alpha[a,i,s].obj = self.y[a,i].x
                    
        self.sub.optimize()
        
    def report(self):
        #solve the prepositioning model by gurobi with the given x and y 
        print("         *** Obtaining x and y value ***         ")
        #print("Objective: %.6f" % self.master.objval)
        #print("Objective: %.6f" % self.sub.objval)
        Vx = np.zeros((self.IS[-1]+1,self.LS[-1]+1))
        Vy = np.zeros((self.AS[-1]+1,self.IS[-1]+1))
        for i in self.IS:
            for l in self.LS:
                if abs(self.x[i,l].x) > 1e-6:
                    Vx[i,l] = self.x[i,l].x

        for a in self.AS:
            for i in self.IS:
                if abs(self.y[a,i].x) > 1e-6:
                    Vy[a,i] = self.y[a,i].x
                    
        m = GRBPY.Model("two-stage_SP")

        # create variables
        print('define variables ...\n')
        q = m.addVars(self.AS,self.IS,self.IS,self.NS,vtype=GRBPY.GRB.INTEGER, name="q")   
        z = m.addVars(self.AS,self.IS,self.NS,vtype=GRBPY.GRB.INTEGER, name="z")
        w = m.addVars(self.AS,self.IS,self.NS,vtype=GRBPY.GRB.INTEGER, name="w")
        hc = m.addVars(self.NS,vtype=GRBPY.GRB.CONTINUOUS, name="hc")
        tc = m.addVars(self.NS,vtype=GRBPY.GRB.CONTINUOUS, name="tc")
        wc = m.addVars(self.NS,vtype=GRBPY.GRB.CONTINUOUS, name="wc")

        f = m.addVar(vtype=GRBPY.GRB.CONTINUOUS,name='f')
        fc = m.addVar(vtype=GRBPY.GRB.CONTINUOUS,name='fc')
        pc = m.addVar(vtype=GRBPY.GRB.CONTINUOUS,name='pc')

        print('define Constraint (3) ...\n')
        m.addConstrs((z[a,i,s] == Vy[a,i] - sum(q[a,i,j,s] for j in self.IS) for a in self.AS for i in self.IS for s in self.NS), 
                    "Constraint (3)")

        print('define Constraint (4) ...\n')
        # C03
        m.addConstrs((w[a,j,s] == self.D[a,j,s] - sum(q[a,i,j,s] for i in self.IS) for a in self.AS for j in self.IS for s in self.NS), 
                    "Constraint (4)")

        print('objective functions')
        # C05
        m.addConstrs((wc[s] == sum(self.G[a] * w[a,j,s] 
                                for a in self.AS for j in self.IS) for s in self.NS), "Shortage Costs")
            
        m.addConstrs((hc[s] == sum(self.CH[a] * z[a,i,s] 
                                for a in self.AS for i in self.IS) for s in self.NS), "Surplus Costs")

        m.addConstrs((tc[s] == sum(self.CT[a] * self.H[i,j] * q[a,i,j,s] 
                                for a in self.AS for i in self.IS for j in self.IS) for s in self.NS), "Transportation Costs")

        print('define objective ...\n')

        # Objective
        m.addConstr((fc == sum(self.CF[l] * Vx[i,l] for i in self.IS for l in self.LS)), "Fixed Facility Costs")

        m.addConstr((pc == sum(self.CP[a] * Vy[a,i] for a in self.AS for i in self.IS)), "Procurement Costs")

        m.addConstr((f == fc + pc + sum(self.pr[s] * (tc[s] + hc[s] + wc[s]) for s in self.NS)), "Objective Function")

        m.setObjective((f), GRBPY.GRB.MINIMIZE)

        print('solving ...\n')

        m.optimize()

        # Work in progress
        if m.status == GRBPY.GRB.OPTIMAL:

            
            Vq = np.zeros((self.AS[-1]+1,self.IS[-1]+1,self.IS[-1]+1,self.NS[-1]+1))
            Vz = np.zeros((self.AS[-1]+1,self.IS[-1]+1,self.NS[-1]+1))
            Vw = np.zeros((self.AS[-1]+1,self.IS[-1]+1,self.NS[-1]+1))
            for i in self.IS:
                for a in self.AS:
                    for s in self.NS:
                        Vz[a,i,s] = z[a,i,s].x
                        Vw[a,i,s] = w[a,i,s].x
                        for j in self.IS:
                            Vq[a,i,j,s] = q[a,i,j,s].x
                            

            Vfc = fc.x
            Vpc = pc.x
            Vtc = sum(self.pr[s] * tc[s].x for s in self.NS)
            Vhc = sum(self.pr[s] * hc[s].x for s in self.NS)
            Vwc = sum(self.pr[s] * wc[s].x for s in self.NS)        
            Vf = m.getObjective().getValue()
            
            costs = pd.DataFrame([Vf,Vfc,Vpc,Vtc,Vhc,Vwc]).T
            location = pd.DataFrame(Vx)
            inventory = pd.DataFrame(Vy).T
            #nextrow = create_template('output.xlsx')
            append_df_to_excel('output.xlsx', costs, sheet_name='result', index = False,header = False,startrow = 2)
            append_df_to_excel('output.xlsx', location, sheet_name='result', index = False,header = False,startrow = 2,startcol = 8)
            append_df_to_excel('output.xlsx', inventory, sheet_name='result', index = False,header = False,startrow = 2,startcol = 13)


        else:
            print('Hmm, something went wrong! Status code:', m.status)
            
        toc = time.perf_counter()
        print("Elapsed time is " + str(toc - tic) + " seconds.")

if __name__ == "__main__":
    prepositioning = Prepositioning()
    prepositioning.read("data.xlsx")
    prepositioning.solve()
    prepositioning.report()