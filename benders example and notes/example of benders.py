"""
reference: Taşkin, Zeki Caner. "Benders decomposition." Wiley Encyclopedia of Operations Research and Management Science (2010).
min 7 * y1 + 7 * y2 + 7 * y3 + 7 * y4 + 7 * y5 + x1 + x2 + x3 + x4 + x5
s.t. x1 + x4 + x5 = 8
    x2 + x5 = 3
    x3 + x4 = 5
    x1 <= 8y1
    x2 <= 3y2
    x3 <= 5y3
    x4 <= 5y4
    x5 <= 5y5
    x1,x2,x3,x4,x5>=0
    y1,y2,y3,y4,y5 are binary
"""

import sys
import coptpy as cp
from coptpy import COPT


# Customized Benders callback
class BendersCallback(cp.CallbackBase):
    def __init__(self, n_y_vars, n_x_vars, m_y_vars, x_demand_cons_rhs, x_link_y_cons_rhs, dualsubprob, y_vars, q_var, \
                 ds_alpha_vars, ds_beta_vars):
        super().__init__()

        # Initialize data
        self._iter = 0
        self._n_y_vars = n_y_vars
        self._n_x_vars = n_x_vars
        self._x_demand_cons_rhs = x_demand_cons_rhs
        self._x_link_y_cons_rhs = x_link_y_cons_rhs

        # Initialize subproblem, variables and constraints
        self._dualsubprob = dualsubprob
        self._m_y_vars = y_vars
        self._m_q_var = q_var
        self._ds_alpha_vars = ds_alpha_vars
        self._ds_beta_vars = ds_beta_vars

    def callback(self):
        if self.where() == COPT.CBCONTEXT_MIPSOL:
            print("Iteration: {0} (best objective: {1})".format(self._iter, self.getInfo(COPT.CBInfo.BestObj)))

            if self._iter >= 1:
                temp_y_values = self.getSolution(self._m_y_vars)
                print("temp_y_values = {}".format(temp_y_values))
                for i in range(len(self._ds_beta_vars)):
                    self._dualsubprob.setInfo(COPT.Info.Obj, self._ds_beta_vars[i],
                                              temp_y_values[i] * self._x_link_y_cons_rhs[i])

            print("Solving subproblem...")
            self._dualsubprob.solve()

            if self._dualsubprob.status == COPT.INFEASIBLE or self._dualsubprob.status == COPT.UNBOUNDED:
                print("Adding feasibility cut...")
                extreme_ray = []
                for i in range(len(self._x_demand_cons_rhs)):
                    extreme_ray.append(self._ds_alpha_vars[i].PrimalRay)
                for i in range(len(self._x_link_y_cons_rhs)):
                    extreme_ray.append(self._ds_beta_vars[i].PrimalRay)
                print("extreme ray = {}".format(extreme_ray))

                lazyconstr = cp.quicksum(self._x_demand_cons_rhs[i] * self._ds_alpha_vars[i].PrimalRay \
                                         for i in range(len(self._x_demand_cons_rhs))) + \
                             sum(self._x_link_y_cons_rhs[i] * self._m_y_vars[i] * self._ds_beta_vars[i].PrimalRay \
                                 for i in range(len(self._x_link_y_cons_rhs)))
                print("lazyconstr = {}".format(lazyconstr))
                self.addLazyConstr(lazyconstr <= 0)
                # print("feasibility cut = {}".format(lazyconstr))

                self._iter += 1
            elif self._dualsubprob.status == COPT.OPTIMAL:
                if self._dualsubprob.objval + 1e-6 < self.getSolution(self._m_q_var) :
                    print("Adding optimality cut...")
                    lazyconstr = cp.quicksum(self._x_demand_cons_rhs[i] * self._ds_alpha_vars[i].x \
                                         for i in range(len(self._x_demand_cons_rhs))) + \
                             sum(self._x_link_y_cons_rhs[i] * self._m_y_vars[i] * self._ds_beta_vars[i].x \
                                 for i in range(len(self._x_link_y_cons_rhs)))
                    self.addLazyConstr(self._m_q_var >= lazyconstr)

                self._iter += 1
            else:
                self.interrupt()
        else:
            print("Unregistered callback context\n")
            sys.exit()

        print("")


class Example:
    def __init__(self):
        # Initialize data
        self.n_y_vars = 0
        self.n_x_vars = 0
        self.x_demand_cons_rhs = []
        self.x_link_y_cons_rhs = []
        self.x_obj_coff = []
        self.y_obj_coff = []

        # Initialize dual problem variables and constraints
        self.m_y_vars = []
        self.m_q_var = None
        self.ds_alpha_vars = []
        self.ds_beta_vars = []
        self.ds_constraints = []

        # Initialize COPT environment
        self.coptenv = cp.Envr()

    def initial_date(self):
        # Input data
        self.n_y_vars = 5
        self.n_x_vars = 5

        self.x_demand_cons_rhs = [8, 3, 5]
        self.x_link_y_cons_rhs = [8, 3, 5, 5, 5]
        self.x_obj_coff = [1, 1, 1, 1, 1]
        self.y_obj_coff = [7, 7, 7, 7, 7]

        self.y_bar = [0, 0, 0, 0, 0]

    def build(self):
        try:
            # Define the master problem and subproblem
            self.masterprob = self.coptenv.createModel("masterprob")
            self.dualsubprob = self.coptenv.createModel("dualsubprob")

            # Disable log information
            self.masterprob.setParam(COPT.Param.Logging, 0)
            self.dualsubprob.setParam(COPT.Param.Logging, 0)

            # Required to obtain farkas dual
            self.dualsubprob.setParam(COPT.Param.ReqFarkasRay, 1)

            # Construct master problem
            for i in range(self.n_y_vars):
                self.m_y_vars.append(
                    self.masterprob.addVar(lb=0.0, ub=1.0, obj=0.0, vtype=COPT.BINARY, name="y_" + str(i + 1)))
            self.m_q_var = self.masterprob.addVar(lb=0.0, ub=COPT.INFINITY, obj=1.0, vtype=COPT.CONTINUOUS, name="q")

            self.masterprob.setObjective(cp.quicksum(self.y_obj_coff[i] * self.m_y_vars[i] \
                                                     for i in range(self.n_y_vars)) + \
                                         self.m_q_var, COPT.MINIMIZE)

            self.masterprob.write("master problem.lp")

            # Construct dual subproblem
            # add variable
            for i in range(len(self.x_demand_cons_rhs)):
                self.ds_alpha_vars.append(
                    self.dualsubprob.addVar(lb=-COPT.INFINITY, ub=COPT.INFINITY, obj=self.x_demand_cons_rhs[i],
                                            vtype=COPT.CONTINUOUS, name="alpha_"+str(i+1)))
            for i in range(len(self.x_link_y_cons_rhs)):
                self.ds_beta_vars.append(self.dualsubprob.addVar(lb=-COPT.INFINITY, ub=0, obj=self.x_link_y_cons_rhs[i],
                                                                 vtype=COPT.CONTINUOUS, name="beta_"+str(i+1)))

            # add constraints
            self.ds_constraints.append(
                self.dualsubprob.addConstr(self.ds_alpha_vars[0] + self.ds_beta_vars[0] <= 1, name="cons_0"))
            self.ds_constraints.append(
                self.dualsubprob.addConstr(self.ds_alpha_vars[1] + self.ds_beta_vars[1] <= 1, name="cons_1"))
            self.ds_constraints.append(
                self.dualsubprob.addConstr(self.ds_alpha_vars[2] + self.ds_beta_vars[2] <= 1, name="cons_2"))
            self.ds_constraints.append(
                self.dualsubprob.addConstr(self.ds_alpha_vars[0] + self.ds_alpha_vars[2] + self.ds_beta_vars[3] <= 1,
                                           name="cons_3"))
            self.ds_constraints.append(
                self.dualsubprob.addConstr(self.ds_alpha_vars[0] + self.ds_alpha_vars[1] + self.ds_beta_vars[4] <= 1,
                                           name="cons_4"))

            self.dualsubprob.setObjective(
                cp.quicksum(self.ds_alpha_vars[i] * self.x_demand_cons_rhs[i] for i in range(len(self.ds_alpha_vars))) + \
                cp.quicksum(self.ds_beta_vars[i] * self.x_link_y_cons_rhs[i] * self.y_bar[i] for i in
                            range(len(self.ds_beta_vars))), COPT.MAXIMIZE)

            self.dualsubprob.write("dual sp problem.lp")
        except cp.CoptError as e:
            print('Return code' + str(e.retcode) + ': ' + e.message)

    def solve(self):
        # Build the master problem and subproblem
        self.build()

        # Create Benders callback object
        bdcallback = BendersCallback(self.n_y_vars, self.n_x_vars, self.m_y_vars, self.x_demand_cons_rhs, \
                                     self.x_link_y_cons_rhs, \
                                     self.dualsubprob, self.m_y_vars, \
                                     self.m_q_var, self.ds_alpha_vars, self.ds_beta_vars)

        # Solve the master problem
        print("               *** Benders Decomposition Loop ***               ")
        self.masterprob.setCallback(bdcallback, COPT.CBCONTEXT_MIPSOL)
        self.masterprob.solve()
        print("                        *** End Loop ***                        \n")

        # Solve the subproblem
        self.dualsubprob.solve()

    def report(self):
        print("               *** Summary Report ***               ")
        print("Best objective: {0}".format(self.masterprob.objval))

        print("Variables solution:")
        for i in range(len(self.m_y_vars)):
            if abs(self.m_y_vars[i].x) > 1e-6:
                print("  y[{0}] = {1}".format(i, self.m_y_vars[i].x))
        print("  q = {}".format(self.m_q_var.x))
        # for i in range(self.n_y_vars):
        #     for j in range(self.nstore):
        #         if abs(self.vship[i][j].x) > 1e-6:
        #             print("  Ship[{0}][{1}] = {2}".format(i, j, self.vship[i][j].x))


if __name__ == "__main__":
    warehouse = Example()
    warehouse.initial_date()
    warehouse.solve()
    warehouse.report()
