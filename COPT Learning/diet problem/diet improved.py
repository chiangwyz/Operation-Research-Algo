from coptpy import *

# Create environment
env = Envr()
model = env.createModel(name="diet_improved")

# Read model
model.read("diet_advanced.mps")

# model.setLogFile("diet1.log")
model.solve()
# Analyze solution
if model.status == COPT.OPTIMAL:
    # Optimal objective value
    print("\n最小食谱构建费用:{:.4f}".format(model.objval))
    allvars = model.getVars()
    # Variable value
    print("\nValue of each variable:")
    for var in allvars:
        print("决策变量{0},最优值为 {1:.4f}，基状态为：{2}".format(var.name, var.x, var.basis))

"""
get info by model
"""

# obtain original LB/UB
allvars = model.getVars()
print("原来的变量下界：", model.getInfo("LB", allvars))
print("原来的变量上界：", model.getInfo("UB", allvars))

#Set constriant name and Obtain original bound
allconstrs = model.getConstrs()
for constr in allconstrs:
    constr_lb = model.getInfo("LB", constr)
    constr_ub = model.getInfo("UB", constr)
    print("约束{0}的下界：{1}，上界：{2}".format(constr.getName(),constr_lb, constr_ub))

"""
get info by vars or constrs
"""

for var in allvars:
    print("原来的变量下界：", var.getInfo("LB"))
    print("原来的变量上界：", var.getInfo("UB"))
for constr in allconstrs:
    print("原来的约束下界：", constr.getInfo("LB"))
    print("原来的约束上界：", constr.getInfo("UB"))


# save the basis of original variables and constraints
varbasis = model.getVarBasis()
conbasis = model.getConstrBasis()

print("模型所有决策变量的基状态：\n")
for var,var_ba in zip(allvars, varbasis):
    print("决策变量：{0}，最优值：{1:4f}，基状态为：{2}".format(var.name, var.x, var_ba))

# change lower bound to 2
model.setInfo("LB", allvars, 2)
# change upper bound to 15
model.setInfo("UB", allvars, 15)