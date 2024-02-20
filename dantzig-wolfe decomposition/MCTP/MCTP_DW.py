"""
2024-2-2, 17:55:31
"""

import math
import itertools
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

        # initialize COPT environment, variables and constraints
        self.coptenv = cp.Envr()

        self.master_model = None
        self.sub_model = None

        self.capacity_cons_master = []
        self.var_lambda_master = []
        self.convex_cons_master = None

        # it's a placeholder when build master model
        self.var_artificial_master = None

        # initialize variables in sub-problem
        self.var_x_sub = []

        # initialize parameters
        self.iter_cnt = 0

        # dual variables of convex constraints
        self.dual_convex_cons = 1.0

        # link constraint(capacity constraint) dual variable
        self.dual_capacity_cons_sub = []

        # sub problem total cost
        self.SP_total_cost = []

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
            tmp_supply = [float(column[k]) for k in range(self.number_products)]
            self.supply_orig.append(tmp_supply)
            current_line += 1

        for j in range(self.number_destinations):
            column = lines[current_line].split()
            tmp_demand = [float(column[k]) for k in range(self.number_products)]
            self.demand_dest.append(tmp_demand)
            current_line += 1

        for i in range(self.number_origins):
            column = lines[current_line].split()
            tmp_capacity = [float(column[j]) for j in range(self.number_destinations)]
            self.capacity_arc.append(tmp_capacity)
            current_line += 1

        for i in range(self.number_origins):
            tmp_cost = []
            for j in range(self.number_destinations):
                column = lines[current_line].split()
                ttmp_cost = [float(column[k]) for k in range(self.number_products)]
                tmp_cost.append(ttmp_cost)
            self.travel_cost.append(tmp_cost)
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

    def initialize_model(self):
        # initialize master problem and subproblem
        self.master_model = self.coptenv.createModel("DW master problem")
        self.sub_model = self.coptenv.createModel("DW sub problem")

        # open log information
        self.master_model.setParam(COPT.Param.Logging, 1)
        self.sub_model.setParam(COPT.Param.Logging, 1)

        # when build RMP, we need add initial artificial variable
        self.var_artificial_master = self.master_model.addVar(lb=0.0,
                                                              ub=COPT.INFINITY,
                                                              obj=0.0,
                                                              vtype=COPT.CONTINUOUS,
                                                              name="artificial_variable")

        # add temp capacity constraints in master model
        for i in range(self.number_origins):
            temp_capacity_cons = []
            for j in range(self.number_destinations):
                temp_capacity_cons.append(
                    self.master_model.addConstr(-self.var_artificial_master <= self.capacity_arc[i][j],
                                                name="capacity_cons_" + str(i) + "_" + str(j)))
                self.capacity_cons_master.append(temp_capacity_cons)

        # initilize the convex combination constraints
        self.convex_cons_master = self.master_model.addConstr(1 * self.var_artificial_master == 1, name="convex cons")

        """
        add sub-problem's variable and constraints
        """

        # add variables to sub-problem, x is flow on arcs
        for i in range(self.number_origins):
            var_x_array = []
            for j in range(self.number_destinations):
                var_x_temp = []
                for k in range(self.number_products):
                    var_x_temp.append(self.sub_model.addVar(lb=0.0,
                                                            ub=COPT.INFINITY,
                                                            obj=0.0,
                                                            vtype=COPT.CONTINUOUS,
                                                            name="x_" + str(i) + "_" + str(j) + "_" + str(k)))
                var_x_array.append(var_x_temp)
            self.var_x_sub.append(var_x_array)

        # add supply constraint to sub-problem
        for i in range(self.number_origins):
            for k in range(self.number_products):
                self.sub_model.addConstr(
                    cp.quicksum(self.var_x_sub[i][j][k] for j in range(self.number_destinations)) ==
                    self.supply_orig[i][k],
                    name="supply_con_" + str(i) + "_" + str(k))

        # add demand constraint to sub-problem
        for j in range(self.number_destinations):
            for k in range(self.number_products):
                self.sub_model.addConstr(
                    cp.quicksum(self.var_x_sub[i][j][k] for i in range(self.number_origins)) == self.demand_dest[j][k],
                    name="demand_con_" + str(j) + "_" + str(k))

        self.master_model.write("initial_RMP.lp")
        # self.master_model.solve()

    def optimize_phase_1(self):
        # initialize parameters
        for i in range(self.number_origins):
            dual_capacity_tmp = [0.0] * self.number_destinations
            self.dual_capacity_cons_sub.append(dual_capacity_tmp)

        obj_sub_phase_1 = - cp.quicksum(self.dual_capacity_cons_sub[i][j] * self.var_x_sub[i][j][k] \
                                        for i in range(self.number_origins) \
                                        for j in range(self.number_destinations) \
                                        for k in range(self.number_products)) \
                          - self.dual_convex_cons

        # set objective for rmp of phase1
        obj_master_phase_1 = self.var_artificial_master
        self.master_model.setObjective(obj_master_phase_1, COPT.MINIMIZE)

        # set objective for sub-problem of phase1
        self.sub_model.setObjective(obj_sub_phase_1, COPT.MINIMIZE)

        # 为了使得主问题在开始时能够可行，并获得可行解
        self.master_model.setCoeff(self.convex_cons_master, self.var_artificial_master, 0.0)

        while True:
            print("Iter: ", self.iter_cnt)

            self.master_model.write("master_problem_phase1.lp")

            self.sub_model.solve()

            if self.sub_model.objval >= - 1e-6:
                print("No new column will be generated, coz no negative reduced cost columns")
                break
            else:
                self.iter_cnt += 1

                # 计算子问题的总成本，该成本即为新列加入到RMP中的系数
                sub_problem_total_cost = sum(self.travel_cost[i][j][k] * self.var_x_sub[i][j][k].x \
                                             for i in range(self.number_origins) \
                                             for j in range(self.number_destinations) \
                                             for k in range(self.number_products))

                self.SP_total_cost.append(sub_problem_total_cost)

                # update constraints in RMP, add column
                col = cp.Column()
                for i in range(self.number_origins):
                    for j in range(self.number_destinations):
                        col.addTerms(self.capacity_cons_master[i][j],
                                     sum(self.var_x_sub[i][j][k].x for k in range(self.number_products)))

                col.addTerms(self.convex_cons_master, 1.0)

                # add decision variable lambda into RMP, i.e. extreme point obtained from sub-problem
                self.var_lambda_master.append(self.master_model.addVar(lb=0.0,
                                                                       ub=COPT.INFINITY,
                                                                       obj=0.0,
                                                                       vtype=COPT.CONTINUOUS,
                                                                       name="lam_phase1_" + str(self.iter_cnt),
                                                                       column=col))

                # solve RMP in phase 1
                self.master_model.solve()

                # update dual variables
                if self.master_model.objval <= 1e-6:
                    break
                else:
                    for i in range(self.number_origins):
                        for j in range(self.number_destinations):
                            self.dual_capacity_cons_sub[i][j] = self.capacity_cons_master[i][j].pi

                    self.dual_convex_cons = self.convex_cons_master.pi

                    # reset objective for sub-problem in phase 1
                    obj_sub_phase_1 = - cp.quicksum(self.dual_capacity_cons_sub[i][j] * self.var_x_sub[i][j][k] \
                                                    for i in range(self.number_origins) \
                                                    for j in range(self.number_destinations) \
                                                    for k in range(self.number_products)
                                                    ) - self.dual_convex_cons

                    self.sub_model.setObjective(obj_sub_phase_1, COPT.MAXIMIZE)

    def update_model_phase_2(self):
        # update model
        obj_master_phase_2 = cp.quicksum(
            self.SP_total_cost[i] * self.var_lambda_master[i] for i in range(len(self.SP_total_cost)))

        self.master_model.setObjective(obj_master_phase_2, COPT.MINIMIZE)

        self.master_model.setInfo(COPT.Info.LB, self.var_artificial_master, 0.0)
        self.master_model.setInfo(COPT.Info.UB, self.var_artificial_master, 0.0)

        # solve master problem in phase 2
        self.master_model.solve()

        # update dual variables
        for i in range(self.number_origins):
            for j in range(self.number_destinations):
                print("self.capacity_cons_master[i][j].pi = ", self.capacity_cons_master[i][j])
                self.dual_capacity_cons_sub[i][j] = self.capacity_cons_master[i][j].pi

        self.dual_convex_cons = self.convex_cons_master.pi

        # update objective of sub-problem by dual variables of RMP
        obj_sub_phase_2 = cp.quicksum(self.dual_capacity_cons_sub[i][j] * self.var_x_sub[i][j][k] \
                                      for i in range(self.number_origins) \
                                      for j in range(self.number_destinations) \
                                      for k in range(self.number_products)) \
                          - self.dual_convex_cons

    def optimize_phase_2(self):

        while True:
            print("----iter", self.iter_cnt)

            # solve subproblem in phase 2
            self.sub_model.solve()

            if self.sub_model.objval >= - 1e-6:
                pass
            else:
                self.iter_cnt += 1

                # 计算子问题的总成本，该成本即为新列加入到RMP中的系数
                sub_problem_total_cost = sum(self.travel_cost[i][j][k] * self.var_x_sub[i][j][k].x \
                                             for i in range(self.number_origins) \
                                             for j in range(self.number_destinations) \
                                             for k in range(self.number_products)
                                             )

                self.SP_total_cost.append(sub_problem_total_cost)

                # update constraints in RMP
                col = cp.Column()
                for i in range(self.number_origins):
                    for j in range(self.number_destinations):
                        col.addTerms(self.capacity_cons_master[i][j],
                                     sum(self.var_x_sub[i][j][k] for k in range(self.number_products)))

                col.addTerms(self.convex_cons_master, 1.0)

                # add decision variable lambda into RMP, i.e. extreme point obtained from sub-problem
                self.var_lambda_master.append(self.master_model.addVar(lb=0.0,
                                                                       ub=COPT.INFINITY,
                                                                       obj=0.0,
                                                                       vtype=COPT.CONTINUOUS,
                                                                       name="lam_phase1_" + str(self.iter_cnt),
                                                                       column=col))

                # solve RMP in phase 2
                self.master_model.solve()

                if self.sub_model.objval >= - 1e-6:
                    break
                else:
                    self.iter_cnt += 1

                    # 计算子问题的总成本，该成本即为新列加入到RMP中的系数
                    sub_problem_total_cost = sum(self.travel_cost[i][j][k] * self.var_x_sub[i][j][k].x \
                                                 for i in range(self.number_origins) \
                                                 for j in range(self.number_destinations) \
                                                 for k in range(self.number_products)
                                                 )

                    self.SP_total_cost.append(sub_problem_total_cost)

                    # update constraints in RMP
                    col = cp.Column()
                    for i in range(self.number_origins):
                        for j in range(self.number_destinations):
                            col.addTerms(self.capacity_cons_master[i][j],
                                         sum(self.var_x_sub[i][j][k] for k in range(self.number_products)))

                    col.addTerms(self.convex_cons_master, 1.0)

                    # add decision variable lambda into RMP, i.e. extreme point obtained from sub-problem
                    self.var_lambda_master.append(self.master_model.addVar(lb=0.0,
                                                                           ub=COPT.INFINITY,
                                                                           obj=sub_problem_total_cost,
                                                                           vtype=COPT.CONTINUOUS,
                                                                           name="lam_phase1_" + str(self.iter_cnt),
                                                                           column=col))

                    # solve RMP in phase 2
                    self.master_model.solve()

                    if self.master_model.objval <= 1e-6:
                        break
                    else:
                        for i in range(self.number_origins):
                            for j in range(self.number_destinations):
                                self.dual_capacity_cons_sub[i][j] = self.capacity_cons_master[i][j].pi

                        self.dual_capacity_cons_sub = self.convex_cons_master.pi

                        # reset objective for sub-problem in phase 1
                        obj_sub_phase_1 = -cp.quicksum(self.dual_capacity_cons_sub[i][j] * self.var_x_sub[i][j][k].x \
                                                       for i in range(self.number_origins) \
                                                       for j in range(self.number_destinations) \
                                                       for k in range(self.number_products)
                                                       ) - self.dual_convex_cons

                        self.sub_model.setObjective(obj_sub_phase_1, COPT.MAXIMIZE)

    def optimize_final_master_problem(self):
        # obtain the initial solution according the master solution
        opt_x = []
        for i in range(self.number_origins):
            opt_x_commodity = [0.0] * self.number_destinations
            opt_x.append(opt_x_commodity)

        for i in range(self.number_origins):
            for j in range(self.number_destinations):
                opt_x[i][j] = self.capacity_cons_master[i][j] + self.var_artificial_master.x - \
                              self.capacity_cons_master[i][j].slack

        obj_master_final = cp.quicksum(self.travel_cost[i][j][k] * self.var_x_sub[i][j][k] \
                                       for i in range(self.number_origins) \
                                       for j in range(self.number_destinations) \
                                       for k in range(self.number_products))

        self.sub_model.setObjective(obj_master_final, COPT.MINIMIZE)

        for i in range(self.number_origins):
            for j in range(self.number_destinations):
                self.sub_model.addConstr(
                    cp.quicksum(self.var_x_sub[i][j][k] for k in range(self.number_products)) == opt_x[i][j])

        self.sub_model.solve()

    def solve_mtcp(self):
        # 
        self.initialize_model()

        self.optimize_phase_1()

        self.update_model_phase_2()

        self.optimize_phase_2()

        self.optimize_final_master_problem()

    def report_solution(self):
        print("-------------------- solution info--------------------")

        print("Objective: ", self.sub_model.objval)

        print("Solution: ")

        for i in range(self.number_origins):
            for j in range(self.number_destinations):
                for k in range(self.number_products):
                    if math.fabs(self.var_x_sub[i][j][k].x > 0):
                        print("x[{},{},{}] = {}".format(i, j, k, self.var_x_sub[i][j][k].x))


if __name__ == "__main__":
    mctp_dw = MCTP_DW()
    mctp_dw.read_data("data.dat")
    mctp_dw.solve_mtcp()
    mctp_dw.report_solution()
