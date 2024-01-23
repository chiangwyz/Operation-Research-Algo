"""
2024-1-18 17:44：36
MCTP solve by dantzig-wolfe decomposition with COPT, for more information, please visit the:https://www.shanshu.ai/copt
"""

from __future__ import division, print_function, annotations

import coptpy as cp
from coptpy import COPT

class MCTP_DW:
    def __init__(self):
        # initialize data
        self.number_origins = 0
        self.number_destinations = 0
        self.number_products = 0
        self.supply_orig = []
        self.demand_dest = []
        self.capacity_arc = []
        self.travel_cost = []

        # initialize variables and constraints
        self.coptenv = cp.Envr()
        self.cmulti = []
        self.vtrans = []
        self.vweight = []

        # initialize parameters
        self.iter = 0
        self.priceconvex = 1.0
        self.price = []
        self.propcost = []

        # tmp variable value
        self.tmp_value = 0

    def read_data(self, filename):
        # read all data from the file
        with open(filename, "r") as f:
            lines = f.readlines()

        self.number_origins = int(lines[0].strip())
        self.number_destinations = int(lines[1].strip())
        self.number_products = int(lines[2].strip())

        current_line = 3
        for i in range(self.number_origins):
            column = lines[current_line].split()
            lsupply = [float(column[k]) for k in range(self.number_products)]
            self.supply_orig.append(lsupply)
            current_line += 1

        for j in range(self.number_destinations):
            column = lines[current_line].split()
            ldemand = [float(column[k]) for k in range(self.number_products)]
            self.demand_dest.append(ldemand)
            current_line += 1

        for i in range(self.number_origins):
            column = lines[current_line].split()
            llcapacity = [float(column[j]) for j in range(self.number_destinations)]
            self.capacity_arc.append(llcapacity)
            current_line += 1

        for i in range(self.number_origins):
            lcost = []
            for j in range(self.number_destinations):
                column = lines[current_line].split()
                llcost = [float(column[k]) for k in range(self.number_products)]
                lcost.append(llcost)
            self.travel_cost.append(lcost)
            current_line += 1

    def print_data(self):
        # Print the loaded data for verification
        print("Number of Origins:", self.number_origins)
        print("Number of Destinations:", self.number_destinations)
        print("Number of Products:", self.number_products)
        print("\nSupply:")
        for i, supply in enumerate(self.supply_orig):
            print(f"Origin {i + 1}: {supply}")
        print("\nDemand:")
        for j, demand in enumerate(self.demand_dest):
            print(f"Destination {j + 1}: {demand}")
        print("\nLimits:")
        for i, limit in enumerate(self.capacity_arc):
            print(f"Origin {i + 1} to Destinations: {limit}")
        print("\nCosts:")
        for i, costs in enumerate(self.travel_cost):
            print(f"Origin {i + 1} to Destinations:")
            for j, cost in enumerate(costs):
                print(f"  To Destination {j + 1}: {cost}")

    def build_mode(self):
        try:
            self.master_model = self.coptenv.createModel("MCTP_DW_master")
            self.sub_model = self.coptenv.createModel("MCTP_DW_subr")

            # open console output
            self.master_model.setParam(COPT.Param.Logging, 0)
            self.sub_model.setParam(COPT.Param.Logging, 0)

            # add variable "excess" for master problem
            self.vexcess = self.master_model.addVar(lb=0.0, ub=COPT.INFINITY, obj=0.0, vtype=COPT.CONTINUOUS)

            for i in range(self.number_origins):
                tmp_con = []
                for j in range(self.number_destinations):
                    tmp_con.append(self.master_model.addConstr(-self.vexcess <= self.capacity_arc[i][j]))
                self.cmulti.append(tmp_con)

            # tricky approach to add temporary constraint 'convex' for master problem
            self.cconvex = self.master_model.addConstr(1e-6 * self.vexcess == 1.0)

            """
            construct subproblem
            """
            # add sub problem x_ij variable
            for i in range(self.number_origins):
                tmp_var = []
                for j in range(self.number_destinations):
                    ttmp_var = []
                    for k in range(self.number_products):
                        ttmp_var.append(self.sub_model.addVar(lb=0.0, ub=COPT.INFINITY, obj=0.0, vtype= COPT.CONTINUOUS))
                    tmp_var.append(ttmp_var)
                self.vtrans.append(tmp_var)

            # add supply constraint for subproblem
            for i in range(self.number_origins):
                for k in range(self.number_products):
                    self.sub_model.addConstr(cp.quicksum(self.vtrans[i][j][k] for j in range(self.number_destinations))
                                             == self.supply_orig[i][k])

            # add demand constraint for subproblem
            for j in range(self.number_destinations):
                for k in range(self.number_products):
                    self.sub_model.addConstr(cp.quicksum(self.vtrans[i][j][k] for i in range(self.number_origins))
                                             == self.demand_dest[j][k])

        except cp.CoptError as e:
            print('Return code' + str(e.retcode) + ': ' + e.message)
        except AttributeError as e:
            print('Encountered an attribute error: ' + str(e))

    def solvePhaseI(self):
        # initialize parameters
        for i in range(self.number_origins):
            lprice = [0.0] * self.number_destinations
            self.price.append(lprice)

        obj_masteri = self.vexcess
        obj_subi = -cp.quicksum(self.price[i][j] * self.vtrans[i][j][k] \
                                   for i in range(self.number_origins) \
                                   for j in range(self.number_destinations) \
                                   for k in range(self.number_products)) - self.priceconvex

        # set objective for master problem in 'Phase I'
        self.master_model.setObjective(obj_masteri, COPT.MINIMIZE)

        # set objective for subproblem in 'Phase I'
        self.sub_model.setObjective(obj_subi, COPT.MINIMIZE)

        # ok, forget this
        self.master_model.setCoeff(self.cconvex, self.vexcess, 0.0)

        # 'Phase I' of dantzig-wolfe decomposition
        print("Phase I: ")

        while True:
            print("Iteration: ", self.iter)

            # solve subproblem in 'Phase I'
            self.sub_model.solve()

            if self.sub_model.objval >= -1e-6:
                print("No feasible solution...")
                break
            else:
                self.iter += 1

                # calculate parameters for master problem
                sum_costxtrans = sum(self.travel_cost[i][j][k] * self.vtrans[i][j][k].x \
                                     for i in range(self.number_origins) \
                                     for j in range(self.number_destinations) \
                                     for k in range(self.number_products))

                self.propcost.append(sum_costxtrans)

                # update constraints in master problem
                col = cp.Column()
                for i in range(self.number_origins):
                    for j in range(self.number_destinations):
                        col.addTerms(self.cmulti[i][j], sum(self.vtrans[i][j][k].x for k in range(self.number_products)))

                col.addTerms(self.cconvex, 1.0)

                # add variable 'weight'
                self.vweight.append(self.master_model.addVar(0.0, COPT.INFINITY, 0.0, COPT.CONTINUOUS, "", col))

                # solve master problem in 'Phase I'
                self.master_model.solve()

                # get the vexcess value
                self.tmp_value = self.vexcess.x

                # update price
                if self.master_model.objval <= 1e-6:
                    break
                else:
                    for i in range(self.number_origins):
                        for j in range(self.number_destinations):
                            self.price[i][j] = self.cmulti[i][j].pi

                    self.priceconvex = self.cconvex.pi

                # reset objective for subproblem in 'Phase I'
                obj_subi = -cp.quicksum(self.price[i][j] * self.vtrans[i][j][k] \
                                           for i in range(self.number_origins) \
                                           for j in range(self.number_destinations) \
                                           for k in range(self.number_products)) - self.priceconvex

                self.sub_model.setObjective(obj_subi, COPT.MINIMIZE)


    def setupPhaseII(self):
        # setting up for 'Phase II'
        print("Setting up for Phase II...")

        # set objective for master problem in 'Phase II'
        obj_masterii = cp.quicksum(self.propcost[i] * self.vweight[i] for i in range(len(self.propcost)))

        self.master_model.setObjective(obj_masterii, COPT.MINIMIZE)

        # fix variable 'excess'
        self.vexcess.lb = self.tmp_value
        self.vexcess.ub = self.tmp_value

        # solve master problem in 'Phase II'
        self.master_model.solve()

        # update price
        for i in range(self.number_origins):
            for j in range(self.number_origins):
                self.price[i][j] = self.cmulti[i][j].pi

        self.priceconvex = self.cconvex.pi

        # set objective for subproblem in 'Phase II'
        obj_subii = cp.quicksum((self.travel_cost[i][j][k] - self.price[i][j]) * self.vtrans[i][j][k] \
                                   for i in range(self.number_origins) \
                                   for j in range(self.number_destinations) \
                                   for k in range(self.number_products)) - self.priceconvex

        self.sub_model.setObjective(obj_subii, COPT.MINIMIZE)

        # increase iteration count
        self.iter += 1

    def solvePhaseII(self):
        # 'Phase II' of dantzig-wolfe decomposition
        print("Phase II: ")

        while True:
            print("Iteration: ", self.iter)

            # solve subproblem in 'Phase II'
            self.sub_model.solve()

            if self.sub_model.objval >= -1e-6:
                print("Optimal solution...")
                break
            else:
                self.iter += 1

                # calculate parameters for master problem
                sum_costxtrans = sum(self.travel_cost[i][j][k] * self.vtrans[i][j][k].x \
                                     for i in range(self.number_origins) \
                                     for j in range(self.number_destinations) \
                                     for k in range(self.number_products))

                # update constraints in master problem
                col = cp.Column()
                for i in range(self.number_origins):
                    for j in range(self.number_destinations):
                        col.addTerms(sum(self.vtrans[i][j][k].x for k in range(self.number_products)), self.cmulti[i][j])

                col.addTerms(self.cconvex, 1.0)

                # add variable 'weight'
                self.vweight.append(
                    self.master_model.addVar(0.0, COPT.INFINITY, sum_costxtrans, COPT.CONTINUOUS, "", col))

                # solve master problem in 'Phase II'
                self.master_model.solve()

                # update price
                for i in range(self.number_origins):
                    for j in range(self.number_destinations):
                        self.price[i][j] = self.cmulti[i][j].pi

                self.priceconvex = self.cconvex.pi

                # reset objective for subproblem in 'Phase II'
                obj_subii = cp.quicksum((self.travel_cost[i][j][k] - self.price[i][j]) * self.vtrans[i][j][k] \
                                           for i in range(self.number_origins) \
                                           for j in range(self.number_destinations) \
                                           for k in range(self.number_products)) - self.priceconvex

                self.sub_model.setObjective(obj_subii, COPT.MINIMIZE)

    def solvePhaseIII(self):
        optship = []
        for i in range(self.number_origins):
            loptship = [0.0] * self.number_destinations
            optship.append(loptship)

        # 'Phase III' of dantzig-wolfe decomposition
        print("Phase III:")

        # set objective for master problem in 'Phase III'
        for i in range(self.number_origins):
            for j in range(self.number_destinations):
                optship[i][j] = self.capacity_arc[i][j] + self.vexcess.x - self.cmulti[i][j].slack

        obj_masteriii = cp.quicksum(self.travel_cost[i][j][k] * self.vtrans[i][j][k] \
                                       for i in range(self.number_origins) \
                                       for j in range(self.number_destinations) \
                                       for k in range(self.number_products))

        self.sub_model.setObjective(obj_masteriii, COPT.MINIMIZE)

        for i in range(self.number_origins):
            for j in range(self.number_destinations):
                self.sub_model.addConstr(cp.quicksum(self.vtrans[i][j][k] for k in range(self.number_products)) == optship[i][j])

        # solve master problem in 'Phase III'
        self.sub_model.solve()

    def solve(self):
        # build 'master' and 'sub'
        self.build_mode()

        # dantzig-wolfe decomposition
        print("               *** Dantzig-Wolfe Decomposition ***               ")
        self.solvePhaseI()

        self.setupPhaseII()

        self.solvePhaseII()

        self.solvePhaseIII()
        print("                        *** End Loop ***                        ")

    def report(self):
        # report solution
        print("               *** Summary Report ***                           ")
        print("Objective: ", self.sub_model.objval)
        print("Variables: ")
        for i in range(self.number_origins):
            for j in range(self.number_destinations):
                for k in range(self.number_products):
                    if abs(self.vtrans[i][j][k].x) >= 1e-6:
                        print("  trans[%d][%d][%d] = %12.6f" % (i, j, k, self.vtrans[i][j][k].x))


if __name__ == "__main__":
    mctp_dw = MCTP_DW()
    mctp_dw.read_data("data.dat")
    mctp_dw.print_data()
    mctp_dw.solve()
    # mctp_dw.report()

