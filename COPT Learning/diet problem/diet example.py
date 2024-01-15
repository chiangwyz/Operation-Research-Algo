"""
This is a COPT learning document, not for commercial use. It is mainly for recording and archiving the study and use of COPT interfaces.
For specific examples, please refer to: https://coridm.d2d.ai/courses/32/supplement/779
"""

from coptpy import *

# Create environment
env = Envr()

# Create model
model = env.createModel(name="diet_simple")
print(model.status == COPT.UNSTARTED)

# Add variables
x = model.addVar(name="Beef")
y = model.addVar(name="Chicken")
z = model.addVar(name="Fish")
print("决策变量x的名称：",x.getName())
print("决策变量x的变量类型：",x.getType())
print("决策变量个数：",model.getAttr("cols"))

#Add constraints：添加单边约束
# vitamin A
model.addConstr(60*x + 8*y + 8*z >= 700)
# Vitamin C
model.addConstr(20*x + 0*y + 10*z >= 700)
print("约束数量：", model.getAttr("rows"))

# Set objective function
model.setObjective(3.19*x + 2.59*y + 2.29*z, sense=COPT.MINIMIZE)
print("模型优化方向是：", model.ObjSense)

#Solve the problem:set parameter
model.setParam(COPT.Param.TimeLimit, 10.0)

#Solve the model
model.solve()

#Analyze solution
if model.status == COPT.OPTIMAL:
    # Optimal objective value
    print("最小食谱构建费用：{:.4f}".format(model.objval))
    allvars = model.getVars()
    #Variable value
    print("\nValue of each variable:\n")
    for var in allvars:
        print("决策变量{0},最优值为 {1:.4f}，基状态为：{2}".format(var.name, var.x, var.basis))


#
# model.write("diet_simple.mps")
# model.write("diet_simple.bas")
# model.write("diet_simple.sol")
# model.write("diet_simple.par")