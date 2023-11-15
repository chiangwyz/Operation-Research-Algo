"""
FCTP, benders decomposition,
MIP solver, COPT
author: Jiang DAPEI
2023-11-15
"""

import numpy as np
import coptpy as cp
from coptpy import COPT
import random


class FCTP_Benders_Decomposition:
    def __init__(self):
        # Initialize data
        self.nsuppliers = 0
        self.ndemanders = 0
        self.supply = []
        self.demand = []
        self.fixcost = []
        self.transportcost = []
        self.bigM = []

        # Initialize master and subproblem variables and constraints
        self.m_var_q = None
        self.m_var_y = []

        self.s_var_x = []
        self.s_var_y_bar = []
        self.s_constr_demand = []
        self.s_constr_supply = []
        self.s_constr_link = []

        # Initialize UB and LB
        self.global_UB_change = []
        self.global_LB_change = []
        self.iter = 0

        # Initialize COPT environment
        self.coptenv = cp.Envr()

    def initial_date(self):
        # Input data
        self.nsuppliers = 4
        self.ndemanders = 3

        self.supply = [10, 30, 40, 20]
        self.demand = [20, 50, 30]
        fix_cost = [10, 30, 20]
        self.fixcost = [fix_cost[:] for _ in range(self.nsuppliers)]
        self.transportcost = [[2.0, 3.0, 4.0], [3.0, 2.0, 1.0], [1.0, 4.0, 3.0], [4.0, 5.0, 2.0]]
        # 使用最大的供应量作为bigM
        for i in range(self.nsuppliers):
            row = []
            for j in range(self.ndemanders):
                row.append(min(self.supply[i], self.demand[j]))
            self.bigM.append(row)

        # model related
        self.s_var_y_bar = [[0 for j in range(self.ndemanders)] for i in range(self.nsuppliers)]

    def build_master_and_sub_problem(self):
        try:
            # Define the master and sub problem
            self.masterprob = self.coptenv.createModel("FCTP master problem")
            self.subprob = self.coptenv.createModel("FCTP sub problem")

            # non display log information
            self.masterprob.setParam(COPT.Param.Logging, 0)
            self.subprob.setParam(COPT.Param.Logging, 0)

            # Required to obtain farkas dual
            self.subprob.setParam(COPT.Param.ReqFarkasRay, 1)

            """
            Construct master problem
            """
            # add variables y_ij
            for i in range(self.nsuppliers):
                var_list = []
                for j in range(self.ndemanders):
                    var_list.append(self.masterprob.addVar(lb=0, ub=1, vtype=COPT.BINARY,
                                                           name="y_" + str(i + 1) + "_" + str(j + 1)))
                self.m_var_y.append(var_list)
            # add variables q
            self.m_var_q = self.masterprob.addVar(lb=0, ub=COPT.INFINITY, vtype=COPT.CONTINUOUS,
                                                           name="q")
            # add objective
            self.masterprob.setObjective(cp.quicksum(self.fixcost[i][j] * self.m_var_y[i][j] for i in
                                     range(self.nsuppliers) for j in range(self.ndemanders) ) + self.m_var_q, COPT.MINIMIZE)
            self.masterprob.write("FCTP master problem.lp")

            """
            Construct sub problem(not dual sub problem)
            """
            # add variables x_ij
            for i in range(self.nsuppliers):
                var_list = []
                for j in range(self.ndemanders):
                    var_list.append(self.subprob.addVar(lb=0.0, ub=COPT.INFINITY, vtype=COPT.CONTINUOUS,
                                                           name="x_" + str(i + 1) + "_" + str(j + 1)))
                self.s_var_x.append(var_list)

            # add constraints
            for i in range(self.nsuppliers):
                self.s_constr_supply.append(self.subprob.addConstr(
                    cp.quicksum( - self.s_var_x[i][j] for j in range(self.ndemanders)) >= - self.supply[i], name="supply_"+str(i + 1)))

            for j in range(self.ndemanders):
                self.s_constr_demand.append(
                    self.subprob.addConstr(cp.quicksum(self.s_var_x[i][j] for i in range(self.nsuppliers))
                                              >= self.demand[j], name="demand_"+str(j + 1)))

            for i in range(self.nsuppliers):
                constr = []
                for j in range(self.ndemanders):
                    constr.append(self.subprob.addConstr( - self.s_var_x[i][j], COPT.GREATER_EQUAL, - self.s_var_y_bar[i][j] * self.bigM[i][j],
                                                                      name="link_" + str(i + 1) + "_" + str(j + 1)))
                self.s_constr_link.append(constr)
            # add objective
            self.subprob.setObjective(
                cp.quicksum(self.transportcost[i][j] * self.s_var_x[i][j] \
                            for i in range(self.nsuppliers) for j in range(self.ndemanders))
                , COPT.MINIMIZE)

            self.subprob.write("FCTP sub problem.lp")

        except cp.CoptError as e:
            print('Return code' + str(e.retcode) + ': ' + e.message)

    def solve_master_problem(self):
        self.masterprob.solve()

        if self.masterprob.status == COPT.OPTIMAL:
            print("Objective: {}".format(self.masterprob.objval))

            print("Variables solution:")
            for var in self.masterprob.getVars():
                if var.name.startswith("x") and var.x > 1e-3:
                    print("{} = {}".format(var.name, round(var.x)))

            for var in self.masterprob.getVars():
                if var.name.startswith("y") and var.x > 1e-3:
                    print("{} = {}".format(var.name, round(var.x)))

    def solve_sub_problem(self):
        self.subprob.solve()

        if self.subprob.status == COPT.OPTIMAL:
            pass

        else:
            pass

    def update_sub_problem(self):
        if self.iter >= 1:
            print("Iteration: {}".format(self.iter))
            for i in range(self.nsuppliers):
                for j in range(self.ndemanders):
                    print("y_{}_{} = {}".format(i + 1, j + 1, self.m_var_y[i][j].x))
                    self.s_constr_link[i][j].lb = - self.bigM[i][j] * self.m_var_y[i][j].x

    def generate_benders_cut_and_add_to_master_problem(self):

        if self.subprob.status == COPT.OPTIMAL:
            print("Adding optimality cut...")

            optimality_cut = str()
            coeff = sum(-self.s_constr_supply[i].pi * self.supply[i] for i in range(self.nsuppliers)) + \
                    sum(self.s_constr_demand[i].pi * self.demand[i] for i in range(self.ndemanders))

            print("coeff = ", coeff)
            optimality_cut += str(coeff)
            for i in range(self.nsuppliers):
                for j in range(self.ndemanders):
                    if self.s_constr_link[i][j].pi != 0:
                        term = - self.s_constr_link[i][j].pi * self.bigM[i][j]
                        if term > 0:
                            # Append the term to the feasibility cut string
                            optimality_cut += " +" + str(term) + "*y_" + str(i + 1) + "_" + str(j + 1)
                        else:
                            optimality_cut += " " + str(term) + "*y_" + str(i + 1) + "_" + str(j + 1)
            optimality_cut += str(" <= q")
            print("optimality cut: {}".format(optimality_cut))

            optimality_cut_constr = sum(-self.s_constr_supply[i].pi * self.supply[i] for i in range(self.nsuppliers)) + \
                         sum(self.s_constr_demand[i].pi * self.demand[i] for i in range(self.ndemanders)) + \
                         cp.quicksum(-self.s_constr_link[i][j].pi * self.bigM[i][j] * self.m_var_y[i][j] for i in \
                                     range(self.nsuppliers) for j in range(self.ndemanders))
            self.masterprob.addConstr(self.m_var_q >= optimality_cut_constr)

            self.iter += 1
        else:
            print("Adding feasibility cut...")
            # print("len _s_constr_link = ", len(self._s_constr_link))
            # for i in range(self._nsuppliers):
            #     print("dualfarkas = {}, supply = {}".format(self._s_constr_supply[i].dualfarkas, self._supply[i]))
            # for i in range(self._ndemanders):
            #     print("dualfarkas = {}, demand = {}".format(self._s_constr_demand[i].dualfarkas, self._demand[i]))
            # print("_s_constr_link[0][0] =", self._s_constr_link[0][0].dualfarkas)
            # for i in range(self._nsuppliers):
            #     for j in range(self._ndemanders):
            #         print("dualfarkas = {}, bigM = {}".format(self._s_constr_link[i][j].dualfarkas, self._bigM[i][j]))

            feasibility_cut = str()
            coeff = sum(-self.s_constr_supply[i].dualfarkas * self.supply[i] for i in range(self.nsuppliers)) + \
                    sum(self.s_constr_demand[i].dualfarkas * self.demand[i] for i in range(self.ndemanders))

            print("coeff =", coeff)
            feasibility_cut += str(coeff)
            for i in range(self.nsuppliers):
                for j in range(self.ndemanders):
                    if self.s_constr_link[i][j].dualfarkas != 0:
                        term = - self.s_constr_link[i][j].dualfarkas * self.bigM[i][j]
                        if term > 0:
                            # Append the term to the feasibility cut string
                            feasibility_cut += " +" + str(term) + "*y_" + str(i + 1) + "_" + str(j + 1)
                        else:
                            feasibility_cut += " " + str(term) + "*y_" + str(i + 1) + "_" + str(j + 1)
            feasibility_cut += str(" <= 0")
            print("feasibility cut = {}".format(feasibility_cut))

            feasibility_cut_constr = sum(
                -self.s_constr_supply[i].dualfarkas * self.supply[i] for i in range(self.nsuppliers)) + \
                         sum(self.s_constr_demand[i].dualfarkas * self.demand[i] for i in
                             range(self.ndemanders)) + \
                         cp.quicksum(
                             -self.s_constr_link[i][j].dualfarkas * self.bigM[i][j] * self.m_var_y[i][j] for i in
                             range(self.nsuppliers) \
                             for j in range(self.ndemanders))
            self.masterprob.addConstr(feasibility_cut_constr <= 0)

            self.iter += 1

    def report(self):
        print("               *** Summary Report ***               ")
        print("Best objective: {}".format(self.masterprob.objval))

        print("Variables solution:")
        for var in self.masterprob.getVars():
            if var.name.startswith("x") and var.x > 1e-3:
                print("{} = {}".format(var.name, round(var.x)))

        for var in self.masterprob.getVars():
            if var.name.startswith("y") and var.x > 1e-3:
                print("{} = {}".format(var.name, round(var.x)))

    def main_solve_function(self):
        """
        Initialize
        """
        self.UB = 9999
        self.LB = 1
        self.Gap = np.inf
        self.eps = 0.001
        self.benders_iter = 0
        max_no_change = 2
        no_change_cnt = 0
        y_bar_change = []

        self.initial_date()

        """ build the initial MP and SP"""
        self.build_master_and_sub_problem()
        self.masterprob.setParam(COPT.Param.Logging, 0)
        # self.masterprob.solve()

        """ get an initial y_var """
        y_var = 1000
        y_bar_change.append(y_var)

        """ solve """
        self.subprob.setParam(COPT.Param.Logging, 0)

        """ Main loop of Benders Decomposition """
        print('\n\n ============================================')
        print(' Benders Decomposition Starts ')

        print('============================================')
        while self.UB - self.LB > self.eps:
            self.benders_iter += 1

            """ solve Dual SP """
            self.subprob.solve()

            """ update global UB """
            if self.subprob.status == COPT.OPTIMAL:
                self.UB = min(self.UB, self.subprob.ObjVal)

            """ generate Cuts """
            self.generate_benders_cut_and_add_to_master_problem()

            """ solve updated MP """
            self.masterprob.solve()
            print("self.MP.status = ", self.masterprob.status)
            for var in self.masterprob.getVars():
                if var.name.startswith("q"):
                    print("y_sol = ", var.x)
                    self.LB = max(self.LB, var.x)




            """ update optimality Gap """
            self.Gap = round(100 * (self.UB - self.LB) / self.LB, 4)

            """ update y_bar"""
            # if self.benders_iter > 1:
            #     y_var = self.MP_var_y.x
            # y_bar_change.append(y_var)

            """ update SP by y_bar """
            self.update_sub_problem()

            """ if y_bar do not change, then give an different value """

            print(' %7.2f ' % self.UB, end='')
            print(' %7.2f ' % self.LB, end='')
            print(' %8.4f ' % self.Gap, end='%')

            print()
            print('\n\n ====== Optimal Solution Found ! ====== ')
            self.report()





if __name__ == "__main__":
    FCPT_benders_decomposition = FCTP_Benders_Decomposition()
    FCPT_benders_decomposition.main_solve_function()

