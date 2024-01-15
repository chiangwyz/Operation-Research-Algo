from coptpy import *

# Create environment
env = Envr()
model = env.createModel(name="diet_improved")

# Read model
model.read("diet_advanced.mps")

model.setLogFile("diet1.log")
model.solve()
# Analyze solution
if model.status == COPT.OPTIMAL:
    # Optimal objective value
    print("\n最小食谱构建费用:{:.4f}".format(model.objval))
    allvars = model.getVars()
    #Variable value
    print("\nValue of each variable:")
    for var in allvars:
        print("决策变量{0},最优值为 {1:.4f}，基状态为：{2}".format(var.name, var.x, var.basis))

