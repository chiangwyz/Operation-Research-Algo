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




# Customized Benders callback
class BendersCallback(cp.CallbackBase):
    def __init__(self, nsuppliers, ndemanders, supply, demand, fixcost, m_var_q, m_var_y, subprob, bigM, s_var_x, s_constr_demand, s_constr_supply, s_constr_link):
        super().__init__()


        # Initialize data
        self._iter = 0
        self._nsuppliers = nsuppliers
        self._ndemanders = ndemanders
        self._supply = supply
        self._demand = demand
        self._fixcost = fixcost

        self._m_var_q = m_var_q
        self._m_var_y = m_var_y

        # Initialize subproblem, variables and constraints
        self._subprob = subprob
        self._bigM = bigM
        self._s_var_x = s_var_x
        self._s_constr_demand = s_constr_demand
        self._s_constr_supply = s_constr_supply
        self._s_constr_link = s_constr_link

    def callback(self):
        if self.where() == COPT.CBCONTEXT_MIPSOL:
            print("Iteration: {0} (best objective: {1})".format(self._iter, self.getInfo(COPT.CBInfo.BestObj)))

            if self._iter >= 1:
                tmp_y_value = []
                for i in range(self._nsuppliers):
                    for j in range(self._ndemanders):
                        print("y_{}_{} = {}".format(i, j, self.getSolution(self._m_var_y[i][j])))
                        self._s_constr_link[i][j].lb = - self._bigM[i][j] * self.getSolution(self._m_var_y[i][j])

            print("Solving subproblem...")
            self._subprob.solve()

            print("sub problem status: {}".format(self._subprob.status))

            if self._subprob.status == COPT.INFEASIBLE or self._subprob.status == COPT.UNBOUNDED:
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

                lazyconstr = sum(-self._s_constr_supply[i].dualfarkas * self._supply[i] for i in range(self._nsuppliers)) + \
                             sum(self._s_constr_demand[i].dualfarkas * self._demand[i] for i in range(self._ndemanders)) + \
                             cp.quicksum(-self._s_constr_link[i][j].dualfarkas * self._bigM[i][j] * self._m_var_y[i][j] for i in range(self._nsuppliers) \
                                         for j in range(self._ndemanders))
                self.addLazyConstr(lazyconstr <= 0)
                print("feasibility cut = {}".format(lazyconstr))

                self._iter += 1
            elif self._subprob.status == COPT.OPTIMAL:
                tmp_sum_y = sum(self._fixcost[i][j] * self.getSolution(self._m_var_y[i][j]) for i in range(self._nsuppliers) for j in range(self._ndemanders))
                print("subprob.objval =: {}".format(self._subprob.objval))
                print("tmp_sum_y =: {}".format(tmp_sum_y))
                print("var q =: {}".format(self.getSolution(self._m_var_q)))
                if self._subprob.objval > self.getSolution(self._m_var_q) + 1e-6:
                    print("Adding optimality cut...")
                    lazyconstr = sum(-self._s_constr_supply[i].pi * self._supply[i] for i in range(self._nsuppliers)) + \
                                 sum(self._s_constr_demand[i].pi * self._demand[i] for i in range(self._ndemanders)) + \
                                 cp.quicksum( -self._s_constr_link[i][j].pi * self._bigM[i][j] * self._m_var_y[i][j] for i in
                                     range(self._nsuppliers) \
                                     for j in range(self._ndemanders))
                    self.addLazyConstr(self._m_var_q >= lazyconstr)
                    print("optimality cut = {}".format(lazyconstr))

                self._iter += 1
            else:
                self.interrupt()
        else:
            print("Unregistered callback context\n")
            sys.exit()

        print("")


class FCTP:
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

    def build(self):
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

    def solve(self):
        # Build the master problem and subproblem
        self.build()

        # Create Benders callback object
        bdcallback = BendersCallback(self.nsuppliers, self.ndemanders, self.supply, self.demand, self.fixcost, \
                                     self.m_var_q, self.m_var_y, self.subprob, self.bigM, \
                                     self.s_var_x, self.s_constr_demand, \
                                     self.s_constr_supply, self.s_constr_link)

        # Solve the master problem
        print("               *** Benders Decomposition Loop ***               ")
        self.masterprob.setCallback(bdcallback, COPT.CBCONTEXT_MIPSOL)
        self.masterprob.solve()
        print("                        *** End Loop ***                        \n")

        # Solve the subproblem
        self.subprob.solve()

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


if __name__ == "__main__":
    fctp = FCTP()
    fctp.initial_date()
    fctp.solve()
    fctp.report()