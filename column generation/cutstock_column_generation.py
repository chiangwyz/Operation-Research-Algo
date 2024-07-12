"""
2024-2-21 14:31:24, The code references the official COPT examples. The reader can see documents in https://www.shanshu.ai/copt
"""
import math

import coptpy as cp
from coptpy import COPT

class CutStockCG:
    def __init__(self):
        self.roll_length = 115
        self.roll_size = [40, 55, 40, 70, 50, 70, 70, 30, 25, 30, 25, 20, 45, 20, 60, 30, 35, 30, 55, 50]
        self.roll_demand = [42, 49, 16, 10, 37, 48, 10, 32, 35, 13, 14, 33, 20, 19, 47, 48, 14, 15, 20, 26]
        # self.roll_size = [25, 40, 50, 55, 70]
        # self.roll_demand = [50, 36, 24, 8, 30]
        # self.roll_size = [40, 55, 40, 70, 50, 70, 70, 30, 25, 30]
        # self.roll_demand = [42, 49, 16, 10, 37, 48, 10, 32, 35, 13]
        self.roll_kinds = len(self.roll_size)
        self.initial_patterns = self.roll_kinds

        self.roll_size_dict = {i: self.roll_size[i] for i in range(self.roll_kinds)}

        # 最大加列次数
        self.MAX_CG_cnt = 1000

    def report_RMP(self, RMP_model):
        # 打印RMP的信息
        print("               *** report RMP Solution ***               ")
        if RMP_model.status == COPT.OPTIMAL:
            print("Using {0} rolls".format(RMP_model.objval))

            rmpvars = RMP_model.getVars()
            for var in rmpvars:
                if var.x > 1e-6:
                    print("  {0} = {1:.6f}".format(var.name, var.x))

    def report_Sub(self, Sub_model):
        # 打印子问题的信息
        print("               *** report Sub Solution ***               ")
        if Sub_model.status == COPT.OPTIMAL:
            print("\nPrice: {0:.6f}\n".format(Sub_model.objval))

    def report_MIP(self, mip_model):
        # 打印最后求整数规划的信息
        print("               *** report MIP Solution ***               ")
        if mip_model.status == COPT.OPTIMAL:
            print("Best MIP objective value: {0:.6f} rolls".format(mip_model.objval))

            mipvars = mip_model.getVars()
            for var in mipvars:
                if var.x > 1e-6:
                    print("  {0} = {1}".format(var.name, var.x))

    def main(self):
        self.env = cp.Envr()

        self.master_model = self.env.createModel("master problem")
        self.sub_model = self.env.createModel("sub problem")

        self.master_model.setParam(COPT.Param.Logging, 1)
        self.sub_model.setParam(COPT.Param.Logging, 1)

        """
        build master model
        """
        self.variables_x_master = self.master_model.addVars(self.initial_patterns, nameprefix="vcut")

        self.pattern_for_every_kinds = []
        for i in range(self.roll_kinds):
            row_data = [0.0] * self.initial_patterns
            row_data[i] = math.floor(self.roll_length / self.roll_size[i])
            self.pattern_for_every_kinds.append(row_data)

        # check pattern
        for pattern in self.pattern_for_every_kinds:
            print(pattern)

        self.cons_demand_master = self.master_model.addConstrs((cp.quicksum(self.pattern_for_every_kinds[i][j] * self.variables_x_master[j] for j in range(self.initial_patterns)) \
                                                                     >= self.roll_demand[i] for i in range(self.roll_kinds)), nameprefix="cons_demand_master")

        obj_master = cp.LinExpr(0)
        for idx, var in self.variables_x_master.items():
            obj_master.addTerm(var, 1.0)
            print("idx, var = {0}, {1}".format(idx, var.getName()))

        self.master_model.setObjective(obj_master, COPT.MINIMIZE)



        """
        build the sub model
        """
        self.variable_use_sub = self.sub_model.addVars(self.roll_kinds, vtype=COPT.INTEGER, nameprefix="vuse")

        self.sub_model.addConstr(self.variable_use_sub.prod(self.roll_size_dict), COPT.LESS_EQUAL, self.roll_length, "width_limit")

        # Main CG loop
        print("               *** Column Generation Loop ***               ")
        for i in range(self.MAX_CG_cnt):
            print("Iteration {0}: \n".format(i))

            # Solve the RMP model and report solution
            self.master_model.solve()
            self.report_RMP(self.master_model)

            # Get the dual values of constraints
            price = self.master_model.getInfo(COPT.Info.Dual, self.cons_demand_master)

            for ele in price:
                print("price[{0}] = {1}".format(ele, price[ele]))

            # Update objective function of SUB model
            self.sub_model.setObjective(1 - self.variable_use_sub.prod(price), COPT.MINIMIZE)


            # Solve the SUB model and report solution
            self.sub_model.solve()
            self.report_Sub(self.sub_model)

            # if we can't find reduced cost less than 0, we need to terminate add column to master problem
            if self.sub_model.objval >= -1e-6:
                self.master_model.write("master problem.lp")
                self.sub_model.write("sub problem.lp")
                break

            # Add new variable to RMP model, get sub problem variable's value
            new_pattern = self.sub_model.getInfo(COPT.Info.Value, self.variable_use_sub)
            cutcol = cp.Column(self.cons_demand_master, new_pattern)
            self.master_model.addVar(obj=1.0, name="new_x({0})".format(i), column=cutcol)


        print("                     *** End Loop ***                     \n")

        # At last, we need to solve a MIP to get the Optimal solution
        allvars = self.master_model.getVars()
        self.master_model.setVarType(allvars, COPT.INTEGER)
        self.master_model.write("master problem mip.lp")

        # Solve the MIP model and report solution
        self.master_model.solve()
        self.report_MIP(self.master_model)


if __name__ == "__main__":
    cutstock = CutStockCG()
    cutstock.main()