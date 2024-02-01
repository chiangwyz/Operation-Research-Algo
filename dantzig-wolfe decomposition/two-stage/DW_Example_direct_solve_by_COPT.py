"""
This is an example that illustrated solved by COPT.

A problem expressed by two model with DW decomposition method.

The optimal objective value is 1040.
"""

import coptpy as cp
from coptpy import COPT


def solve_DW_example(flag: bool = True) -> None:
    # Create environment
    env = cp.Envr()

    # Create model
    model = env.createModel(name="DW_example")
    print(model.status == COPT.UNSTARTED)

    if flag:
        # 使用转换前的模型
        x = {}

        # Add variables
        for i in range(4):
            x[i + 1] = model.addVar(lb=0.0, ub=COPT.INFINITY, vtype=COPT.CONTINUOUS, name="x_" + str(i + 1))

        # add constraints
        model.addConstr(3 * x[1] + x[2], COPT.LESS_EQUAL, 12, name="c1")
        model.addConstr(2 * x[1] + x[2], COPT.LESS_EQUAL, 10, name="c2")
        model.addConstr(3 * x[3] + 2* x[4], COPT.LESS_EQUAL, 15, name="c3")
        model.addConstr(x[3] + x[4], COPT.LESS_EQUAL, 4, name="c4")
        model.addConstr(8 * x[1] + 6 * x[2] + 7 * x[3] + 5 * x[4], COPT.LESS_EQUAL, 80, name="c1")

        # set objective
        obj = 90 * x[1] + 80 * x[2] + 70 * x[3] + 60 * x[4]
        model.setObjective(obj, sense=COPT.MAXIMIZE)
        print("模型优化方向是：", model.ObjSense)

        model.write("DW_example.lp")

    else:
        # 使用转换后的模型
        mu = {}
        lam = {}
        s = {}

        # Add variables
        for i in range(4):
            mu[i + 1] = model.addVar(lb=0.0, ub=COPT.INFINITY, vtype=COPT.CONTINUOUS, name="mu_" + str(i + 1))

        for i in range(3):
            lam[i + 1] = model.addVar(lb=0.0, ub=COPT.INFINITY, vtype=COPT.CONTINUOUS, name="lam_" + str(i + 1))

        s[1] = model.addVar(lb=0.0, ub=COPT.INFINITY, vtype=COPT.CONTINUOUS, name="s_1")

        # test
        print("决策变量个数：", model.getAttr("cols"))

        # add constraints
        # link constraint
        model.addConstr(32 * mu[2] + 52 * mu[3] + 60 * mu[4] + 28 * lam[2] + 20 * lam[3] + s[1], COPT.EQUAL, 80,
                        name="c1")

        # mu price convex
        lhs = cp.LinExpr(0)
        for i in range(4):
            lhs.addTerm(mu[i + 1], 1.0)
        model.addConstr(lhs, COPT.EQUAL, 1, name="c2")

        # lam price convex
        lhs = cp.LinExpr(0)
        for i in range(3):
            lhs.addTerm(lam[i + 1], 1.0)
        model.addConstr(lhs, COPT.EQUAL, 1, name="c3")

        print("约束数量：", model.getAttr("rows"))

        # Set objective function
        obj = 360 * mu[2] + 660 * mu[3] + 800 * mu[4] + 280 * lam[2] + 240 * lam[3]
        model.setObjective(obj, sense=COPT.MAXIMIZE)
        print("模型优化方向是：", model.ObjSense)

        # Solve the problem: set parameter
        # model.setParam(COPT.Param.TimeLimit, 10.0)

        model.write("DW_example_price.lp")


    #Solve the model
    model.solve()

    #Analyze solution
    if model.status == COPT.OPTIMAL:
        # Optimal objective value
        print("objective value：{:.4f}".format(model.objval))
        allvars = model.getVars()
        # Variable value
        print("\nValue of each variable:\n")
        for var in allvars:
            print("决策变量{0},最优值为 {1:.4f}，基状态为：{2}".format(var.name, var.x, var.basis))


if __name__ == "__main__":
    solve_DW_example(False)