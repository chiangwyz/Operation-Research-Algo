import coptpy as cp
from coptpy import COPT


def DW_Example_Phase1_SP1():
    # Create environment
    env = cp.Envr()

    # Create model
    SP1_model = env.createModel(name="DW_example SP1 Problem")
    print(SP1_model.status == COPT.UNSTARTED)

    SP1_model.setParam(COPT.Param.Logging, 1)

    x = {}

    for i in range(2):
        x[i+1] = SP1_model.addVar(lb=0, ub=COPT.INFINITY, vtype=COPT.CONTINUOUS, name="x"+str(i+1))

    SP1_model.setObjective(0 * x[1] + 0 * x[2] + 1, COPT.MAXIMIZE)

    SP1_model.addConstr(lhs= 3 * x[1] + x[2], sense=COPT.LESS_EQUAL, rhs=12, name="sp1_con1")
    SP1_model.addConstr(lhs= 2 * x[1] + x[2], sense=COPT.LESS_EQUAL, rhs=10, name="sp1_con2")

    SP1_model.write("phase1 sp1.lp")

    SP1_model.solve()

    print("SP1_model objective value {}".format(SP1_model.ObjVal))

    # constraints slack and dual
    constr_list = SP1_model.getConstrs()
    allslacks = SP1_model.getSlacks()
    allduals = SP1_model.getDuals()
    for (constr, dual, slack) in zip(constr_list, allduals, allslacks):
        print("约束{0}，对偶变量的值{1:.4f}，松弛变量的值{1:.4f}".format(constr.getName(), dual, slack))

    allvars = SP1_model.getVars()
    for var in allvars:
        print("变量{0}，最有解{1:.4f}".format(var.getName(), var.x))

if __name__ == "__main__":
    DW_Example_Phase1_SP1()