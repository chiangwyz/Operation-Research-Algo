#
#  This file is part of the Cardinal Optimizer, all rights reserved.
#

import sys
import coptpy as cp
from coptpy import COPT

# Customized Benders callback
class BendersCallback(cp.CallbackBase):
    def __init__(self, nwarehouse, nstore, supply, demand, subprob, maxshipcost, vmbuild, csupply, cdemand):
        super().__init__()

        # Initialize data
        self._iter = 0
        self._nwarehouse = nwarehouse
        self._nstore = nstore
        self._supply = supply
        self._demand = demand

        # Initialize subproblem, variables and constraints
        self._subprob = subprob
        self._maxshipcost = maxshipcost
        self._vmbuild = vmbuild
        self._csupply = csupply
        self._cdemand = cdemand

    def callback(self):
        if self.where() == COPT.CBCONTEXT_MIPSOL:
            print("Iteration: {0} (best objective: {1})".format(self._iter, self.getInfo(COPT.CBInfo.BestObj)))

            if self._iter >= 1:
                for i in range(self._nwarehouse):
                    self._csupply[i].ub = self.getSolution(self._vmbuild[i]) * self._supply[i]

            print("Solving subproblem...")
            self._subprob.solve()

            if self._subprob.status == COPT.INFEASIBLE:
                print("Adding feasibility cut...")
                lazyconstr = cp.quicksum(-self._csupply[i].dualfarkas * self._supply[i] * self._vmbuild[i] \
                                      for i in range(self._nwarehouse)) + \
                             sum(-self._cdemand[i].dualfarkas * self._demand[i] for i in range(self._nstore))
                self.addLazyConstr(lazyconstr >= 0)

                for i in range(self._nwarehouse):
                    print("{} dualfarkas {}".format(i, self._csupply[i].dualfarkas))

                print("lazyconstr: {0}".format(lazyconstr))

                self._iter += 1
            elif self._subprob.status == COPT.OPTIMAL:
                if self._subprob.objval > self.getSolution(self._maxshipcost) + 1e-6:
                    print("Adding optimality cut...")
                    lazyconstr = cp.quicksum(self._csupply[i].pi * self._supply[i] * self._vmbuild[i] \
                                          for i in range(self._nwarehouse)) + \
                                 sum(self._cdemand[i].pi * self._demand[i] for i in range(self._nstore))
                    self.addLazyConstr(self._maxshipcost >= lazyconstr)

                self._iter += 1
            else:
                self.interrupt()
        else:
            print("Unregistered callback context\n")
            sys.exit()

        print("")

class WareHouse:
    def __init__(self):
        # Initialize data
        self.nwarehouse = 0
        self.nstore = 0
        self.supply = []
        self.demand = []
        self.fixcost = []
        self.varcost = []

        # Initialize variables and constraints
        self.vmbuild = []
        self.vship = []
        self.csupply = []
        self.cdemand = []

        # Initialize COPT environment
        self.coptenv = cp.Envr()

    def read(self, filename=None):
        # Input data
        if filename is None:
            self.nwarehouse = 25
            self.nstore = 6

            self.supply = [23070, 18290, 20010, 15080, 17540, 21090, 16650, 18420, \
                           19160, 18860, 22690, 19360, 22330, 15440, 19330, 17110, \
                           15380, 18690, 20720, 21220, 16720, 21540, 16500, 15310, \
                           18970]
            self.demand = [12000, 12000, 14000, 13500, 25000, 29000]
            self.fixcost = [500000] * len(self.supply)
            self.varcost = [[73.78,  14.76,  86.82,  91.19,  51.03,  76.49],
                            [60.28,  20.92,  76.43,  83.99,  58.84,  68.86],
                            [58.18,  21.64,  69.84,  72.39,  61.64,  58.39],
                            [50.37,  21.74,  61.49,  65.72,  60.48,  56.68],
                            [42.73,  35.19,  44.11,  58.08,  65.76,  55.51],
                            [44.62,  39.21,  44.44,  48.32,  76.12,  51.17],
                            [49.31,  51.72,  36.27,  42.96,  84.52,  49.61],
                            [50.79,  59.25,  22.53,  33.22,  94.30,  49.66],
                            [51.93,  72.13,  21.66,  29.39,  93.52,  49.63],
                            [65.90,  13.07,  79.59,  86.07,  46.83,  69.55],
                            [50.79,   9.99,  67.83,  78.81,  49.34,  60.79],
                            [47.51,  12.95,  59.57,  67.71,  51.13,  54.65],
                            [39.36,  19.01,  56.39,  62.37,  57.25,  47.91],
                            [33.55,  30.16,  40.66,  48.50,  60.83,  42.51],
                            [34.17,  40.46,  40.23,  47.10,  66.22,  38.94],
                            [41.68,  53.03,  22.56,  30.89,  77.22,  35.88],
                            [42.75,  62.94,  18.58,  27.02,  80.36,  40.11],
                            [46.46,  71.17,  17.17,  21.16,  91.65,  41.56],
                            [56.83,   8.84,  83.99,  91.88,  41.38,  67.79],
                            [46.21,   2.92,  68.94,  76.86,  38.89,  60.38],
                            [41.67,  11.69,  61.05,  70.06,  43.24,  48.48],
                            [25.57,  17.59,  54.93,  57.07,  44.93,  43.97],
                            [28.16,  29.39,  38.64,  46.48,  50.16,  34.20],
                            [26.97,  41.62,  29.72,  40.61,  59.56,  31.21],
                            [34.24,  54.09,  22.13,  28.43,  69.68,  24.09]]
        else:
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
            # Define the master problem and subproblem
            self.masterprob = self.coptenv.createModel("masterprob")
            self.subprob = self.coptenv.createModel("subprob")

            # Disable log information
            self.masterprob.setParam(COPT.Param.Logging, 0)
            self.subprob.setParam(COPT.Param.Logging, 0)

            # Required to obtain farkas dual
            self.subprob.setParam(COPT.Param.ReqFarkasRay, 1)

            # Construct master problem
            for i in range(self.nwarehouse):
                self.vmbuild.append(self.masterprob.addVar(0.0, 1.0, 0.0, COPT.BINARY))
            self.maxshipcost = self.masterprob.addVar(0.0, COPT.INFINITY, 0.0, COPT.CONTINUOUS)

            self.masterprob.setObjective(cp.quicksum(self.fixcost[i] * self.vmbuild[i] \
                                                  for i in range(self.nwarehouse)) + \
                                         self.maxshipcost, COPT.MINIMIZE)

            # Construct subproblem
            for i in range(self.nwarehouse):
                lvship = []
                for j in range(self.nstore):
                    lvship.append(self.subprob.addVar(0.0, COPT.INFINITY, 0.0, COPT.CONTINUOUS))
                self.vship.append(lvship)
            for i in range(self.nwarehouse):
                self.csupply.append(self.subprob.addConstr(cp.quicksum(self.vship[i][j] for j in range(self.nstore)) \
                                                           <= self.supply[i]))
            for j in range(self.nstore):
                self.cdemand.append(self.subprob.addConstr(cp.quicksum(self.vship[i][j] for i in range(self.nwarehouse)) \
                                                           == self.demand[j]))

            self.subprob.setObjective(cp.quicksum(self.varcost[i][j] * self.vship[i][j] \
                                               for i in range(self.nwarehouse) \
                                               for j in range(self.nstore)), COPT.MINIMIZE)
        except cp.CoptError as e:
            print('Return code' + str(e.retcode) + ': ' + e.message)

    def solve(self):
        # Build the master problem and subproblem
        self.build()

        # Create Benders callback object
        bdcallback = BendersCallback(self.nwarehouse, self.nstore, self.supply, self.demand, \
                                     self.subprob, \
                                     self.maxshipcost, self.vmbuild, \
                                     self.csupply, self.cdemand)

        # Solve the master problem
        print("               *** Benders Decomposition Loop ***               ")
        self.masterprob.setCallback(bdcallback, COPT.CBCONTEXT_MIPSOL)
        self.masterprob.solve()
        print("                        *** End Loop ***                        \n")

        # Solve the subproblem
        self.subprob.solve()

    def report(self):
        print("               *** Summary Report ***               ")
        print("Best objective: {0}".format(self.masterprob.objval))

        print("Variables solution:")
        for i in range(self.nwarehouse):
            if abs(self.vmbuild[i].x) > 1e-6:
                print("  Build[{0}] = {1}".format(i, self.vmbuild[i].x))
        for i in range(self.nwarehouse):
            for j in range(self.nstore):
                if abs(self.vship[i][j].x) > 1e-6:
                    print("  Ship[{0}][{1}] = {2}".format(i, j, self.vship[i][j].x))

if __name__ == "__main__":
    warehouse = WareHouse()
    warehouse.read()
    warehouse.solve()
    warehouse.report()
