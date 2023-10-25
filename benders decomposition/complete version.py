"""
benders decomposition
reference:
1. COPT reference manual
2.《运筹优化常用模型、算法及案例实战——Python+Java实现》
刘兴禄，熊望祺，臧永森，段宏达，曾文佳 2022年，清华大学出版社
"""
import numpy as np
import sys
import coptpy as cp
from coptpy import COPT

EPSILON = 0.001


# design our benders cut
class benders_cut_callback(cp.CallbackBase):
    """
    Customize callback class. User must implement callback().
    For more information of callback methods, refer to CallbackBase.
    """

    def __init__(self, saving_rate, fund_rate, rhs_b, rhs_B, var_y, y_bar, subprob, var_z, var_alpha_0,
                 var_alpha_i, con_every_fund) -> None:
        super().__init__()

        self._iter = 0
        self._saving_rate = saving_rate
        self._fund_rate = fund_rate
        self._rhs_b = rhs_b
        self._rhs_B = rhs_B
        self._y_bar = y_bar
        self._var_z = var_z

        # initialize subproblem and it's variable and constraints
        self._subproblem = subprob
        self._var_y = var_y
        self._var_alpha_0 = var_alpha_0
        self._var_alpha_i = var_alpha_i
        self._con_every_fund = con_every_fund

        # initialize global LB and UB
        self.global_LB = 0
        self.global_UB = np.inf

    def callback(self):
        if self.where() == COPT.CBCONTEXT_MIPSOL:
            print("Iteration: {0} (best objective: {1})".format(self._iter, self.getInfo(COPT.CBInfo.BestObj)))

            # if self._iter >= 1:
            #     for i in range(self._nwarehouse):
            #         self._csupply[i].ub = self.getSolution(self._vmbuild[i]) * self._supply[i]

            print("Solving subproblem...")
            self._subproblem.solve()

            self._y_bar = self.getSolution(self._var_y)
            self.global_UB = min(self.global_UB, self.getSolution(self._var_z))

            if self._subproblem.status == COPT.INFEASIBLE or self._subproblem.status == COPT.UNBOUNDED:
                print("Adding feasibility cut...")
                extreme_ray = []
                extreme_ray.append(self._var_alpha_0.PrimalRay)
                for i in range(len(self._var_alpha_i)):
                    extreme_ray.append(self._var_alpha_i[i].PrimalRay)
                lazyconstr = cp.quicksum(extreme_ray[i] * (self._rhs_b[i] - self._rhs_B[i] * self._var_y) \
                    for i in range(len(self._rhs_b)))
                self.addLazyConstr(lazyconstr >= 0)

                self._iter += 1
            elif self._subproblem.status == COPT.OPTIMAL:
                # update global lower bound
                self.global_LB = max(self.global_LB, self._subproblem.objval + self._saving_rate * self.getSolution(self._var_y))

                if self.global_LB + 1e-6 < self.global_UB:
                    print("Adding optimality cut...")
                    extreme_point = []
                    extreme_point.append(self._var_alpha_0.x)
                    for i in range(len(self._var_alpha_i)):
                        extreme_point.append(self._var_alpha_i[i].x)

                    lazyconstr = cp.quicksum(extreme_point[i] * (self._rhs_b[i] - self._rhs_B[i] * self._var_y) \
                                             for i in range(len(self._var_alpha_i))) + \
                                 self._saving_rate * self._var_y
                    self.addLazyConstr(lazyconstr >= self._var_z)

                self._iter += 1
            else:
                self.interrupt()
        else:
            print("Unregistered callback context\n")
            sys.exit()

        print("")


class Budget:
    def __init__(self):
        # initialize data
        self.saving_rate = 1.045
        self.fund_rate = [1.01, 1.02, 1.03, 1.04, 1.05, 1.06, 1.07, 1.08, 1.09, 1.10]
        self.rhs_b = [1000, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100]
        self.rhs_B = [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.y_bar = 1500

        # initialize sub problem and it's variables and constraints
        self.var_z = None
        self.var_y = None
        self.var_alpha_0 = None
        self.var_alpha_i = []
        self.con_every_fund = []

        # initialize COPT environment
        self.coptenv = cp.Envr()

    def build(self):
        """
        build master-and-sub problem
        :param env:
        :return:
        """
        try:
            self.master_problem_model = self.coptenv.createModel("Master Problem")
            self.dual_sub_problem_model = self.coptenv.createModel("Sub Problem")

            self.master_problem_model.setParam(COPT.Param.Logging, 0)
            self.dual_sub_problem_model.setParam(COPT.Param.Logging, 0)

            # set master problem some parameters
            # self.master_problem_model.setParam("LazyConstraints", 1)
            # self.master_problem_model.setParam("LpMethod", 1)  # set master problem use dual simplex

            # set sub problem some parameters
            # self.dual_sub_problem_model.setParam("Presolve", 0)

            # set to get the unbound ray
            self.dual_sub_problem_model.setParam(COPT.Param.ReqFarkasRay, 1)

            # construct master problem
            """ create decision variables """
            self.var_y = self.master_problem_model.addVar(lb=0, ub=COPT.INFINITY, vtype=COPT.INTEGER, name='y')
            self.var_z = self.master_problem_model.addVar(lb=-COPT.INFINITY, ub=COPT.INFINITY, vtype=COPT.CONTINUOUS,
                                                          name='z')

            self.master_problem_model.setObjective(self.var_z, COPT.MAXIMIZE)

            # construct dual sub problem
            """ create decision variables """
            self.var_alpha_0 = self.dual_sub_problem_model.addVar(lb=0, ub=COPT.INFINITY, vtype=COPT.CONTINUOUS,
                                                                  name='alpha_0')
            for i in range(len(self.fund_rate)):
                self.var_alpha_i.append(
                    self.dual_sub_problem_model.addVar(lb=0, ub=COPT.INFINITY, vtype=COPT.CONTINUOUS,
                                                       name='alpha_' + str(i + 1)))

            """ create constraints """
            for i in range(len(self.fund_rate)):
                self.con_every_fund.append(
                    self.dual_sub_problem_model.addConstr(self.var_alpha_0 + self.var_alpha_i[i], COPT.GREATER_EQUAL,
                                                          self.rhs_b[i + 1], name="alpha_" + str(i)))

            """ create objective """
            obj = cp.LinExpr(0)
            obj.addTerms(self.var_alpha_0, 1000 - self.y_bar)
            for i in range(len(self.fund_rate)):
                obj.addTerms(self.var_alpha_i[i], 100)

            self.dual_sub_problem_model.setObjective(obj, COPT.MINIMIZE)
        except cp.CoptError as e:
            print("Error code:{}, and error message:{}".format(e.retcode, e.message))
        except AttributeError as e:
            print("Encounter an attribute error {}".format(e))

    def solve(self):
        # construct master and sub problem
        self.build()

        benderCallBack = benders_cut_callback(self.saving_rate, self.fund_rate, self.rhs_b,self.rhs_B, self.var_y, self.y_bar, self.dual_sub_problem_model, self.var_z, self.var_alpha_0, self.var_alpha_i, self.con_every_fund)
        
        # Solve the master problem
        print("               *** Benders Decomposition Loop ***               ")
        self.master_problem_model.setCallback(benderCallBack, COPT.CBCONTEXT_MIPSOL)
        self.master_problem_model.solve()
        print("                        *** End Loop ***                        \n")

        # Solve the subproblem
        self.dual_sub_problem_model.solve()


def main():
    budget = Budget()
    budget.solve()


if __name__ == '__main__':
    main()
