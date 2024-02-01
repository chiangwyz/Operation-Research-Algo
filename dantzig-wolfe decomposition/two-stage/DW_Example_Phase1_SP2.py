import coptpy as cp
from coptpy import COPT


def DW_Example_Phase1_SP2():
    # Create environment
    env = cp.Envr()

    # Create model
    SP2_model = env.createModel(name="DW_example SP2 Problem")
    print(SP2_model.status == COPT.UNSTARTED)

    SP2_model.setParam(COPT.Param.Logging, 1)

    xx = {}

    for i in range(2):
        xx[i + 1] = SP2_model.addVar(lb=0, ub=COPT.INFINITY, vtype=COPT.CONTINUOUS, name="x" + str(i + 1))

    SP2_model.setObjective(0 * xx[1] + 0 * xx[2] + 1, COPT.MAXIMIZE)

    SP2_model.addConstr(lhs=3 * xx[1] + xx[2], sense=COPT.LESS_EQUAL, rhs=5, name="sp2_con1")
    SP2_model.addConstr(lhs=xx[1] + xx[2], sense=COPT.LESS_EQUAL, rhs=4, name="sp2_con2")

    SP2_model.write("phase1 sp1.lp")

    SP2_model.solve()

    print("SP2_model objective value {}".format(SP2_model.ObjVal))

    # constraints slack and dual
    constr_list = SP2_model.getConstrs()
    allslacks = SP2_model.getSlacks()
    allduals = SP2_model.getDuals()
    for (constr, dual, slack) in zip(constr_list, allduals, allslacks):
        print("约束{0}，对偶变量的值{1:.4f}，松弛变量的值{1:.4f}".format(constr.getName(), dual, slack))

    allvars = SP2_model.getVars()
    for var in allvars:
        print("变量{0}，最有解{1:.4f}".format(var.getName(), var.x))


if __name__ == "__main__":
    DW_Example_Phase1_SP2()
