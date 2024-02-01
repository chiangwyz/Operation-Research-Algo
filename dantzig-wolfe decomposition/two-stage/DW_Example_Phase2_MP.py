import coptpy as cp
from coptpy import COPT


def DW_Example_Phase2_MP():
    # Create environment
    env = cp.Envr()

    # Create MP_model
    MP_model = env.createModel(name="DW_example Master Problem")
    print(MP_model.status == COPT.UNSTARTED)

    MP_model.setParam(COPT.Param.Logging, 1)

    # Read MP_model
    MP_model.read("rmp_ph1.lp")

    constr_list = MP_model.getConstrs()

    new_columns = [[0, 0, 1, 0],
                   [0, 0, 0, 1]]

    for i in range(len(new_columns)):
        rmp_new_col = cp.Column(constr_list, new_columns[i][1:])
        MP_model.addVar(lb=0.0, ub=COPT.INFINITY, obj=new_columns[i][0],
                     vtype=COPT.CONTINUOUS, name="y_" + str(i+1), column=rmp_new_col)

    for constr in constr_list:
        if constr.name.startswith("rmp_con_"):
            MP_model.setInfo(COPT.Info.LB, constr, 1)
            MP_model.setInfo(COPT.Info.UB, constr, 1)

    MP_model.write("rmp_ph2.lp")

    MP_model.solve()

    # constraints slack and dual
    allslacks = MP_model.getSlacks()
    allduals = MP_model.getDuals()
    for (constr, dual, slack) in zip(constr_list, allduals, allslacks):
        print("约束{0}，对偶变量的值{1:.4f}，松弛变量的值{1:.4f}".format(constr.getName(), dual, slack))
    
    allvars = MP_model.getVars()
    for var in allvars:
        print("变量{0}，最有解{1:.4f}".format(var.getName(), var.x))

if __name__ == "__main__":
    DW_Example_Phase2_MP()
