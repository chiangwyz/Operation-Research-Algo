# -*- coding: utf-8 -*-
"""
benders decomposition with dual sub-problem in facility location problem
"""
import gurobipy as grbpy
from gurobipy import GRB
from logger_config import logger


def cbwarehouse(model, where):
    if where == GRB.Callback.MIPSOL:
        logger.info("starting callback MIPSOL")
        var_y_value = model.cbGetSolution(model._var_y_master)
        logger.info("var_y_value =\n%s", var_y_value)
        if model._iter >= 1:
            for i in range(len(var_y_value)):
                model._dual_sub.setAttr(GRB.Attr.Obj, model._var_alpha_sub[i], var_y_value[i] * model._supply[i])

        model._dual_sub.optimize()
        model._dual_sub.write(f"dual sub {model._iter}.lp")

        if model._dual_sub.status == GRB.INFEASIBLE or model._dual_sub.status == GRB.UNBOUNDED:
            print("Iteration: ", model._iter)
            print("Adding feasibility cut...\n")

            lazycut = grbpy.quicksum(model._var_alpha_sub[i].unbdray * model._supply[i] * model._var_y_master[i] \
                                     for i in range(model._nwarehouse)) + \
                      sum(model._var_beta_sub[i].unbdray * model._demand[i] for i in range(model._nstore))

            for i in range(model._nwarehouse):
                print("{} unbdray {}".format(i, model._var_alpha_sub[i].unbdray))
            for i in range(model._nstore):
                print("{} unbdray {}".format(i, model._var_beta_sub[i].unbdray))

            logger.info("feasibility cut: %s <=0", lazycut)

            model.cbLazy(lazycut <= 0)

            model._iter += 1
        elif model._dual_sub.status == GRB.OPTIMAL:
            if model._dual_sub.objval > model.cbGetSolution(model._var_maxshipcost_master) + 1e-6:
                print("Iteration: ", model._iter)
                print("Adding optimality cut...\n")

                lazycut = grbpy.quicksum(model._var_alpha_sub[i].x * model._supply[i] * model._var_y_master[i] \
                                         for i in range(model._nwarehouse)) + \
                          sum(model._var_beta_sub[i].x * model._demand[i] for i in range(model._nstore))

                model.cbLazy(model._var_maxshipcost_master >= lazycut)

                logger.info("optimality cut: %s <= %s", lazycut, model._var_maxshipcost_master)

                model._iter += 1
        else:
            model.terminate()


class WareHouse:
    def __init__(self):
        # initialize data
        self.nwarehouse = 0
        self.nstore = 0
        self.supply = []
        self.demand = []
        self.fixcost = []
        self.varcost = []

        # initialize variables and constraints
        self.var_y_master = []
        self.var_alpha_sub = []
        self.var_beta_sub = []
        self.constr_capacity_sub = []

    def read(self, filename):
        # input data
        with open(filename, "r") as data:
            self.nwarehouse = int(data.readline())
            self.nstore = int(data.readline())

            column = data.readline().split()
            for i in range(self.nwarehouse):
                self.supply.append(float(column[i]))

            column = data.readline().split()
            for i in range(self.nstore):
                self.demand.append(float(column[i]))

            column = data.readline().split()
            for i in range(self.nwarehouse):
                self.fixcost.append(float(column[i]))

            for i in range(self.nwarehouse):
                column = data.readline().split()
                lvarcost = []
                for j in range(self.nstore):
                    lvarcost.append(float(column[j]))
                self.varcost.append(lvarcost)

    def build(self):
        try:
            # define models for 'master' and 'dual_sub'
            self.master = grbpy.Model("master")
            self.dual_sub = grbpy.Model("dual_sub")

            # disable log information
            self.master.setParam(GRB.Param.OutputFlag, 1)
            self.dual_sub.setParam(GRB.Param.OutputFlag, 1)

            # use lazy constraints
            self.master.setParam(GRB.Param.LazyConstraints, 1)

            # disable presolving in subproblem
            self.dual_sub.setParam(GRB.Param.Presolve, 0)

            # required to obtain farkas dual
            self.dual_sub.setParam(GRB.Param.InfUnbdInfo, 1)

            # use dual simplex
            self.dual_sub.setParam(GRB.Param.Method, 1)

            # construct master problem
            for i in range(self.nwarehouse):
                self.var_y_master.append(self.master.addVar(0.0, 1.0, 0.0, GRB.BINARY, name="y_"+str(i)))

            self.maxshipcost = self.master.addVar(0.0, GRB.INFINITY, 0.0, GRB.CONTINUOUS)

            self.master.setObjective(grbpy.quicksum(self.fixcost[i] * self.var_y_master[i] \
                                                    for i in range(self.nwarehouse)) + \
                                     self.maxshipcost, GRB.MINIMIZE)

            self.master.write("master problem 2.lp")

            # construct dual sub problem
            for i in range(self.nwarehouse):
                self.var_alpha_sub.append(self.dual_sub.addVar(-GRB.INFINITY, 0.0, 0.0, GRB.CONTINUOUS))
            for i in range(self.nstore):
                self.var_beta_sub.append(self.dual_sub.addVar(-GRB.INFINITY, GRB.INFINITY, 0.0, GRB.CONTINUOUS))

            for i in range(self.nwarehouse):
                for j in range(self.nstore):
                    self.constr_capacity_sub.append(self.dual_sub.addConstr(self.var_alpha_sub[i] + self.var_beta_sub[j] <= self.varcost[i][j]))

            self.dual_sub.setObjective(grbpy.quicksum(1.0 * self.supply[i] * self.var_alpha_sub[i] for i in range(self.nwarehouse)) + \
                                       grbpy.quicksum(self.demand[j] * self.var_beta_sub[j] for j in range(self.nstore)), GRB.MAXIMIZE)

            self.dual_sub.write("dual subproblem.lp")

        except grbpy.GurobiError as e:
            print('Error code' + str(e.errno) + ': ' + str(e))
        except AttributeError as e:
            print('Encountered an attribute error: ' + str(e))

    def solve(self):
        # build 'master' and 'dual_sub'
        self.build()

        # register callback
        self.master._iter = 0
        self.master._nwarehouse = self.nwarehouse
        self.master._nstore = self.nstore
        self.master._supply = self.supply
        self.master._demand = self.demand

        self.master._var_y_master = self.var_y_master
        self.master._var_alpha_sub = self.var_alpha_sub
        self.master._var_beta_sub = self.var_beta_sub
        self.master._maxshipcost = self.maxshipcost

        self.master._dual_sub = self.dual_sub

        # optimize master problem
        print("               *** Benders Decomposition Loop ***               ")
        self.master.optimize(cbwarehouse)
        print("                        *** End Loop ***                        ")

        self.dual_sub.optimize()

    def report(self):
        print("               *** Summary Report ***               ")
        print("Objective: %.6f" % self.master.objval)
        print("Variables:")
        for i in range(self.nwarehouse):
            if abs(self.var_y_master[i].x) > 1e-6:
                print("  Build[%d] = %.0f" % (i, self.var_y_master[i].x))

if __name__ == "__main__":
    warehouse = WareHouse()
    warehouse.read("warehouse.dat")
    warehouse.solve()
    warehouse.report()
