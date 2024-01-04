"""
2023年11月26日16:55:19
DAPEI Jiang
Lagrangian relaxation on LTP
Referencing on https://github.com/wujianjack/optimizationmodels/tree/master/gurobi/locationtransport, with modifications.
"""

import coptpy as cp
from coptpy import COPT
import copy
import pandas as pd
import re

class LagrangianRelaxation:
    def __init__(self):
        # Initial data
        self.warehouseNumLimit = 0  # warehouses limit
        self.customerNum = 0        # customers limit
        self.supply = []            # supply
        self.demand = []            # demands
        self.travelCost = []        # travel cost

        # Initialize COPT environment and model
        self.coptenv = cp.Envr()
        self.var_x = []
        self.var_y = []
        self.cons_supply = []
        self.cons_facilityNum = []
        self.relax_cons_demand = []

        # Initialize parameters
        self.LTP_model = None
        self.iterLimit = 100
        self.noChangeLimit = 3
        self.stepSizeLog = []
        self.thetaLog = []
        self.xLBlog = []
        self.xUBlog = []

        # debug flag
        self.print_flag = False

    def read_data(self, filename: str):
        with open(filename, "r") as f:
            lines = f.readlines()

        # Read the facility number limit
        self.warehouseNumLimit = int(lines[0].strip())
        # Read the number of customers
        self.customerNum = int(lines[1].strip())

        # Process supply and demand using list comprehension to create lists of floats
        self.supply = [float(num) for num in re.split(r" +", lines[2].strip())]
        self.demand = [float(num) for num in re.split(r" +", lines[3].strip())]

        # Start reading travel costs from the fifth line and construct a cost matrix
        for line in lines[4:4 + self.customerNum]:
            # Split each line of costs and convert to a list of floats, then add to the cost matrix
            costs = [float(num) for num in re.split(r" +", line.strip())]
            self.travelCost.append(costs)

        # Print the data for verification
        if self.print_flag:
            print("Facility Number Limit:", self.warehouseNumLimit)
            print("Customer Number:", self.customerNum)
            print("Supply:", self.supply)
            print("Demand:", self.demand)
            print("Travel Cost Matrix:")
            for row in self.travelCost:
                print(row)

    def buildModel(self):
        try:
            self.LTP_model = self.coptenv.createModel("LR with LTP")

            # open console output
            self.LTP_model.setParam(COPT.Param.Logging, 0)

            # create LTP model x variable
            for i in range(self.customerNum):
                tmp_var_x = []
                for j in range(self.customerNum):
                    tmp_var_x.append(self.LTP_model.addVar(lb=0, ub=self.demand[j], vtype=COPT.INTEGER,
                                                           name="x_" + str(i + 1) + "_" + str(j + 1)))
                self.var_x.append(tmp_var_x)

            # create LTP model y variables
            for i in range(self.customerNum):
                self.var_y.append(self.LTP_model.addVar(lb=0, ub=1, vtype=COPT.BINARY,
                                                        name="y_" + str(i + 1)))

            # add constraint
            """
            supply constraint
            sum_{j \in C} x_ij <= s_i * y_i, \forall i \in D
            """
            for i in range(self.customerNum):
                self.cons_supply.append(self.LTP_model.addConstr(cp.quicksum(self.var_x[i][j] for j in range(self.customerNum)) \
                                                                 - self.supply[i] * self.var_y[i] <= 0, name="supply_"+str(i+1)))

            """
            facility count constraint
            sum_{i \in D} y_i <= P
            """
            self.cons_facilityNum.append(self.LTP_model.addConstr(cp.quicksum(self.var_y[i] for i in range(self.customerNum)) <= self.warehouseNumLimit, name="cons"))

            """
            relax demand constraint
            sum_{i \in D} x_ij >= d_j, \forall j \in C
            """
            for j in range(self.customerNum):
                self.relax_cons_demand.append(self.LTP_model.addConstr(cp.quicksum(self.var_x[i][j] for i in range(self.customerNum)) >= self.demand[j], name="demand_" + str(j + 1)))

            """
            set objective
            // sum_{i \in D, j \in c} c_{ij} * x_{ij} + sum_{j \in C} u_j * d_j - sum_{i \in D, j \in c} u_j * x_{ij}
            sum_{i \in D, j \in c} c_{ij} * x_{ij}
            """
            self.LTP_model.setObjective(cp.quicksum(self.var_x[i][j] * self.travelCost[i][j] \
                                        for i in range(self.customerNum) \
                                        for j in range(self.customerNum)), COPT.MINIMIZE)

            self.LTP_model.write("LTP problem.lp")

        except cp.CoptError as e:
            print('Return code' + str(e.retcode) + ': ' + e.message)
        except AttributeError as e:
            print('Encountered an attribute error: ' + str(e))

    def LRsubGradientSolve(self):
        # 'Lagrangian Relaxation' parameters
        same = 0
        norm = 0.0
        step = 0.0
        theta = 1.0     # theta = 2.0，
        xLB = 0.0
        xUB = 0.0
        lagrangian_multiplier = [0.0] * self.customerNum
        slack = [0.0] * self.customerNum

        # build model
        self.buildModel()

        # initial lower bound lb through LP relaxation
        xLB = self.getRelaxUB(self.LTP_model)
        print("LB = ", xLB)

        # initial UB through sum all max travelcost
        for i in range(self.customerNum):
            xUB += max(self.travelCost[i])
        print("UB = ", xUB)

        # temporary linear expression
        obj_total_travel_cost_linear_expression = cp.quicksum(self.var_x[i][j] * self.travelCost[i][j] for i in range(self.customerNum) for j in range(self.customerNum))

        # flag that indicate whether the current model is lagrangian relaxation
        isModelLagrangianRelaxed = False

        # main 'Lagrangian Relaxation' loop
        for iter in range(self.iterLimit):
            print("iter = ", iter)

            # solve lower bound
            if not isModelLagrangianRelaxed:
                isModelLagrangianRelaxed = True
                
                # get relax constraints
                relaxConsNum = len(self.relax_cons_demand)
                for i in range(relaxConsNum):
                    self.LTP_model.remove(self.relax_cons_demand[i])
                self.relax_cons_demand = []

            # lagrangian relaxation term : sum_{j \in C} u_j * (d_j - sum_{i \in D} x_{ij})
            obj_lagrangian_relaxed_term = cp.quicksum(lagrangian_multiplier[j] * (self.demand[j] - cp.quicksum(self.var_x[i][j] for i in range(self.customerNum))) for j in range(self.customerNum))

            # lagrangian relaxation objective: sum_{i \in D, j \in c} c_{ij} * x_{ij} + sum_{j \in C} u_j * d_j - sum_{i \in D, j \in c} u_j * x_{ij}
            self.LTP_model.setObjective(obj_total_travel_cost_linear_expression + obj_lagrangian_relaxed_term, COPT.MINIMIZE)

            # solve relaxed(LP) model  and obtain lower bound
            self.LTP_model.solve()
            print("LTP model objval: ", self.LTP_model.ObjVal)

            # calculate slacks for each relaxed constraints by the solution x
            for j in range(self.customerNum):
                # slacks for each relaxed constraints: sum_{i \in D} x_{ij} - d_j
                slack[j] = sum(self.var_x[i][j].x for i in range(self.customerNum)) - self.demand[j]
                print("slack_{}: {}".format(j, slack[j]))

            # update lower bound if there has any improvement, or keep the no change count
            if self.LTP_model.objval > xLB + 1e-6:
                xLB = self.LTP_model.objval
                same = 0
            else:
                same += 1

            # if within k steps no improvement, update
            if same == self.noChangeLimit:
                theta /= 2.0
                same = 0

            # calculate ''2-norm
            squareSum = sum(slack[i]**2 for i in range(self.customerNum))

            # update step size
            step = theta * (xUB - self.LTP_model.objval) / squareSum

            # update lagrangian multipliers with update equations
            for i in range(self.customerNum):
                if lagrangian_multiplier[i] > step * slack[i]:
                    lagrangian_multiplier[i] = lagrangian_multiplier[i] - step * slack[i]
                else:
                    lagrangian_multiplier[i] = 0.0

            # get an upper bound of original model
            """
            we relax the demand constraints, thus the relaxed model may select more facility so that the supply will exceed the demand
            """
            selected_facility_supply = sum(self.supply[j] * self.var_y[j].x for j in range(self.customerNum))
            sum_all_demand = sum(self.demand)

            temp_y_value = []
            for i in range(self.customerNum):
                # print("var_y {} {}".format(i, self.var_y[i].x))
                temp_y_value.append(self.var_y[i].x)

            print("selected facility supply =", selected_facility_supply)
            print("sum all demand =", sum_all_demand)
            if selected_facility_supply - sum_all_demand >= 1e-6:
                isModelLagrangianRelaxed = False

                """
                add relaxed constraints into LTP model and fix y, so that the model is easy to solve, this LTP model is same as the original model, but with fixed y in lagrangian relaxation version, we relax these constraints in this version, we add them back, aiming to obtain an UB
                """
                for j in range(self.customerNum):
                    self.relax_cons_demand.append(self.LTP_model.addConstr(cp.quicksum(self.var_x[i][j] for i in range(self.customerNum)) >= self.demand[j]))

                # retrieve solution from LB model and fix it
                """
                fix facility location variable and get an upper bound of original model fix the value of y
                """
                for i in range(self.customerNum):
                    self.var_y[i].setInfo(COPT.Info.LB, temp_y_value[i])
                    self.var_y[i].setInfo(COPT.Info.UB, temp_y_value[i])

                    # self.LTP_model.setInfo(COPT.Info.LB, self.var_y[i], temp_y_value[i])
                    # self.LTP_model.setInfo(COPT.Info.UB, self.var_y[i], temp_y_value[i])

                self.LTP_model.setObjective(obj_total_travel_cost_linear_expression, COPT.MINIMIZE)

                # solve the revised model with fixed y and get an upper bound
                self.LTP_model.solve()
                xUB = min(xUB, self.LTP_model.objval)

                # reset the facility location variable y's bound to 0-1
                for i in range(self.customerNum):
                    self.var_y[i].setInfo(COPT.Info.LB, 0.0)
                    self.var_y[i].setInfo(COPT.Info.UB, 1.0)

            # update LB, UB, step size, theta
            self.xLBlog.append(xLB)
            self.xUBlog.append(xUB)
            self.stepSizeLog.append(step)
            self.thetaLog.append(theta)

    def getRelaxUB(self, locationTransModel):
        # solve model linear programming
        locationTransModel.solveLP()

        relax_UB = locationTransModel.objval

        return relax_UB

    def reportInformation(self):
        print("\n               *** Summary Report ***               \n")
        print("  Iter        LB               UB          theta        step")

        for i in range(len(self.xLBlog)):
            print("  %3d    %12.6f    %12.6f    %8.6f    %8.6f" \
                  % (i, self.xLBlog[i], self.xUBlog[i], self.thetaLog[i], self.stepSizeLog[i]))



if __name__ == "__main__":
    lagrangian_relaxation = LagrangianRelaxation()

    # read the data file
    file_path = "locationTransportProblem.dat"
    lagrangian_relaxation.read_data(file_path)

    lagrangian_relaxation.LRsubGradientSolve()

    lagrangian_relaxation.reportInformation()












