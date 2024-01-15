"""
This is a COPT learning document, not for commercial use. It is mainly for recording and archiving the study and use of COPT interfaces.
For specific examples, please refer to: https://coridm.d2d.ai/courses/32/supplement/784
"""

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

# Set constriant name and Obtain original bound
allconstrs = model.getConstrs()
for constr in allconstrs:
    constr_lb = model.getInfo("LB", constr)
    constr_ub = model.getInfo("UB", constr)
    print("约束{0}的下界：{1}，上界：{2}".format(constr.getName(), constr_lb, constr_ub))

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
for var, var_ba in zip(allvars, varbasis):
    print("决策变量：{0}，最优值：{1:4f}，基状态为：{2}".format(var.name, var.x, var_ba))

# change lower bound to 2
model.setInfo("LB", allvars, 2)
# change upper bound to 15
model.setInfo("UB", allvars, 15)

# Set new Bound of Vitamin_A and Vitamin_C
# constr_A = model.getConstrByName("R(Vitamin_A)")
# model.setInfo("LB", constr_A, 1000)
# model.setInfo("UB", constr_A, 20000)
# constr_C = model.getConstrByName("R(Vitamin_C)")
# model.setInfo("LB", constr_C, 1000)
# model.setInfo("UB", constr_C, 20000)

model.setBasis(varbasis, conbasis)
model.solve()

# Analyze solution
if model.status == COPT.OPTIMAL:
    # Optimal objective value
    print("最小食谱构建费用:{:.4f}".format(model.objval))
    allvars = model.getVars()
    #Variable value
    print("\nValue of each variable:\n")
    for var in allvars:
        print("决策变量{0},最优值为 {1:.4f}，基状态为：{2}".format(var.name, var.x, var.basis))


allconstrs = model.getConstrs()
conbasis = model.getConstrBasis()
print("模型所有约束条件的基状态：\n")
for constr,constr_ba in zip(allconstrs, conbasis):
    print("约束条件：{0}，活跃程度：{1:4f}，基状态为：{2}".format(constr.name, model.getInfo("Slack", constr), constr_ba))


