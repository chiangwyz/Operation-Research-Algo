# -*- coding: utf-8 -*-
"""
"""
import gurobipy as grbpy
from gurobipy import GRB
from logger_config import logger

lazyconstraint = []


def cbwarehouse(model, where):
    if where == GRB.Callback.MIPSOL:
        logger.info(f"{model._iter} callback was invoke!")
        if model._iter >= 1:
            tmp_info = []
            for i in range(model._nwarehouse):
                model._constr_supply_sub[i].rhs = model.cbGetSolution(model._var_build_master[i]) * model._supply[i]
                tmp_info.append(("{}: {}".format(i, model.cbGetSolution(model._var_build_master[i]))))

            # logger.info(f"{model._iter} : %s", tmp_info)

        model._sub.write(f"sub problem {model._iter}.lp")
        model._sub.optimize()

        if model._sub.status == GRB.INFEASIBLE:
            logger.info("Iteration: %s", model._iter)
            logger.info("Adding feasibility cut...")

            lazycut = grbpy.quicksum(
                model._constr_supply_sub[i].FarkasDual * model._supply[i] * model._var_build_master[i] \
                for i in range(model._nwarehouse)) + \
                      sum(model._constr_demand_sub[i].FarkasDual * model._demand[i] for i in range(model._nstore))

            for i in range(model._nwarehouse):
                logger.info("%s farkasdual %s", i, model._constr_supply_sub[i].FarkasDual)

            model.cbLazy(lazycut >= 0)
            lazyconstraint.append((lazycut, GRB.GREATER_EQUAL, 0))

            logger.info("%s >=0", lazycut)

            model._iter += 1
        elif model._sub.status == GRB.OPTIMAL:
            if model._sub.objval > model.cbGetSolution(model._var_maxshipcost_master) + 1e-6:
                logger.info("Iteration: %s", model._iter)
                logger.info("Adding optimality cut...")
                logger.info("sub problem objval: %s", model._sub.objval)
                logger.info("var maxshipcost master: %s", model.cbGetSolution(model._var_maxshipcost_master))

                lazycut = grbpy.quicksum(model._constr_supply_sub[i].Pi * model._supply[i] * model._var_build_master[i] \
                                         for i in range(model._nwarehouse)) + \
                          sum(model._constr_demand_sub[i].Pi * model._demand[i] for i in range(model._nstore))

                for i in range(model._nwarehouse):
                    logger.info("%s pi %s", i, model._constr_supply_sub[i].Pi)

                model.cbLazy(model._var_maxshipcost_master >= lazycut)

                logger.info("%s >= %s", model._var_maxshipcost_master.VarName, lazycut)

                lazyconstraint.append((lazycut, GRB.GREATER_EQUAL, model._var_maxshipcost_master))

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
        self.var_maxshipcost_master = None
        self.var_build_master = []
        self.var_ship_sub = []
        self.constr_supply_sub = []
        self.constr_demand_sub = []

    def read(self, filename):
        logger.info("starting read data file!")
        # input data
        with open(filename, "r") as data:
            self.nwarehouse = int(data.readline().strip())
            self.nstore = int(data.readline().strip())

            # Read supply
            self.supply = list(map(float, data.readline().strip().split()))

            # Read demand
            self.demand = list(map(float, data.readline().strip().split()))

            # Read fixed costs
            self.fixcost = list(map(float, data.readline().strip().split()))

            # Read variable costs
            self.varcost = []
            for _ in range(self.nwarehouse):
                row = list(map(float, data.readline().strip().split()))
                self.varcost.append(row)

        logger.info("successfully read data!")

    def print_data(self):
        # print the read data
        print(f"Number of Warehouses: {self.nwarehouse}")
        print(f"Number of Stores: {self.nstore}")
        print(f"Supply: {self.supply}")
        print(f"Demand: {self.demand}")
        print(f"Fixed Costs: {self.fixcost}")
        print("Variable Costs:")
        for row in self.varcost:
            print(row)

    def build(self):
        try:
            logger.info("start building model!")

            # define models for 'master' and 'sub'
            self.master = grbpy.Model("master problem")
            self.sub = grbpy.Model("sub problem")

            # disable log information
            self.master.setParam(GRB.Param.OutputFlag, 1)
            self.sub.setParam(GRB.Param.OutputFlag, 1)

            # use lazy constraints
            self.master.setParam(GRB.Param.LazyConstraints, 1)

            # disable presolving in subproblem
            self.sub.setParam(GRB.Param.Presolve, 0)

            # required to obtain farkas dual
            self.sub.setParam(GRB.Param.InfUnbdInfo, 1)

            # use dual simplex
            self.sub.setParam(GRB.Param.Method, 1)

            # construct master problem
            for i in range(self.nwarehouse):
                self.var_build_master.append(self.master.addVar(0.0, 1.0, 0.0, GRB.BINARY, name="y_" + str(i)))

            self.var_maxshipcost_master = self.master.addVar(0.0, GRB.INFINITY, 0.0, GRB.CONTINUOUS,
                                                             name="q_maxshipcost")

            self.master.setObjective(grbpy.quicksum(self.fixcost[i] * self.var_build_master[i] \
                                                    for i in range(self.nwarehouse)) + \
                                     self.var_maxshipcost_master, GRB.MINIMIZE)

            self.master.write("master problem.lp")

            # construct subproblem
            for i in range(self.nwarehouse):
                lvship = []
                for j in range(self.nstore):
                    lvship.append(self.sub.addVar(0.0, GRB.INFINITY, 0.0, GRB.CONTINUOUS))
                self.var_ship_sub.append(lvship)

            for i in range(self.nwarehouse):
                self.constr_supply_sub.append(self.sub.addConstr(grbpy.quicksum(self.var_ship_sub[i][j] \
                                                                                for j in range(self.nstore)) \
                                                                 <= self.supply[i] * 1.0))

            for j in range(self.nstore):
                self.constr_demand_sub.append(self.sub.addConstr(grbpy.quicksum(self.var_ship_sub[i][j] \
                                                                                for i in range(self.nwarehouse)) \
                                                                 == self.demand[j]))

            self.sub.setObjective(grbpy.quicksum(self.varcost[i][j] * self.var_ship_sub[i][j] \
                                                 for i in range(self.nwarehouse) \
                                                 for j in range(self.nstore)), GRB.MINIMIZE)

            self.sub.write("sub problem.lp")

            logger.info("building model successfully!")

        except grbpy.GurobiError as e:
            print('Error code' + str(e.errno) + ': ' + str(e))
        except AttributeError as e:
            print('Encountered an attribute error: ' + str(e))

    def solve(self):
        # build 'master' and 'sub'
        self.build()

        # register callback
        self.master._iter = 0
        self.master._nwarehouse = self.nwarehouse
        self.master._nstore = self.nstore
        self.master._supply = self.supply
        self.master._demand = self.demand

        self.master._constr_supply_sub = self.constr_supply_sub
        self.master._constr_demand_sub = self.constr_demand_sub
        self.master._var_build_master = self.var_build_master
        self.master._var_maxshipcost_master = self.var_maxshipcost_master

        self.master._sub = self.sub

        # optimize master problem
        print("               *** Benders Decomposition Loop ***               ")
        logger.info("               *** Benders Decomposition Loop ***               ")
        self.master.optimize(cbwarehouse)
        print("                        *** End Loop ***                        ")
        logger.info("               *** End Loop ***               ")

        # # it seems that 64-bit needs this extra work
        # for i in range(self.nwarehouse):
        #     self.constr_supply_sub[i].rhs = self.var_build_master[i].x * self.supply[i]
        #
        # self.sub.optimize()

        # for i in range(len(lazyconstraint)):
        #     self.master.addConstr(lazyconstraint[i][0] >= lazyconstraint[i][2])

        # self.master.write("master problem add lazy constraints.lp")
        #
        # self.master.optimize()

    def report(self):
        print("               *** Summary Report ***               ")
        print("Objective: %.6f" % self.master.objval)
        print("Variables:")
        for i in range(self.nwarehouse):
            if abs(self.var_build_master[i].x) > 1e-6:
                print("  Build[%d] = %.0f" % (i, self.var_build_master[i].x))

        for i in range(self.nwarehouse):
            for j in range(self.nstore):
                if abs(self.var_ship_sub[i][j].x) > 1e-6:
                    print("  Ship[%d][%d] = %.6f" % (i, j, self.var_ship_sub[i][j].x))


if __name__ == "__main__":
    warehouse = WareHouse()
    warehouse.read("warehouse.dat")
    # warehouse.print_data()
    warehouse.solve()
    warehouse.report()
