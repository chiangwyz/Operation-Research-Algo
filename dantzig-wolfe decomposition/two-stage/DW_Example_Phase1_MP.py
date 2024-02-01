import coptpy as cp
from coptpy import COPT


def DW_Example_Phase1():
    # Create environment
    env = cp.Envr()

    # Create model
    model = env.createModel(name="DW_example Master Problem")
    print(model.status == COPT.UNSTARTED)

    model.setParam(COPT.Param.Logging, 1)

    rmp_vars = [model.addVar(lb=0.0, ub=1000, obj=1.0, vtype=COPT.CONTINUOUS, name="s_1")]

    rmp_cons = {}

    col_aij = [-1, 1e-6, 1e-6]

    rmp_cons[0] = model.addConstr(lhs = rmp_vars[0] * col_aij[0], sense=COPT.LESS_EQUAL,rhs=80, name="rmp_link_con")
    
    rmp_cons[1] = model.addConstr(lhs = rmp_vars[0] * col_aij[1], sense=COPT.EQUAL,rhs=1, name="rmp_con_convex_combine_mu")

    rmp_cons[2] = model.addConstr(lhs = rmp_vars[0] * col_aij[2], sense=COPT.EQUAL,rhs=1, name="rmp_con_convex_combine_lam")

    model.setObjSense(COPT.MAXIMIZE)

    # trick to set constraint and variable
    model.setCoeff(rmp_cons[1], rmp_vars[0], 0.0)
    model.setCoeff(rmp_cons[2], rmp_vars[0], 0.0)

    model.setInfo(COPT.Info.LB, rmp_cons[1], 0.0)
    model.setInfo(COPT.Info.UB, rmp_cons[1], 0.0)
    model.setInfo(COPT.Info.LB, rmp_cons[2], 0.0)
    model.setInfo(COPT.Info.UB, rmp_cons[2], 0.0)

    model.write("rmp_ph1.lp")
    model.write("rmp_ph1.mps")

    model.solve()

    # constraints slack and dual
    constr_list = model.getConstrs()
    allslacks = model.getSlacks()
    allduals = model.getDuals()
    for (constr, dual, slack) in zip(constr_list, allduals, allslacks):
        print("约束{0}，对偶变量的值{1:.4f}，松弛变量的值{1:.4f}".format(constr.getName(), dual, slack))


if __name__ == "__main__":
    DW_Example_Phase1()
