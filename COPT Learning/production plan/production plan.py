
import coptpy as cp
from coptpy import COPT

# Create environment
env = cp.Envr()

# Create model
model = env.createModel(name="production plan")
print(model.status == COPT.UNSTARTED)

# Add variables
x1 = model.addVar(name="x1")
x2 = model.addVar(name="x2")

print("决策变量x1的名称：", x1.getName())
print("决策变量x2的变量类型：", x1.getType())
print("决策变量个数：", model.getAttr("cols"))

# Add constraints：添加单边约束
model.addConstr(1 * x1 + 2 * x2 <= 12)
model.addConstr(x1 + 2 * x2 <= 8)
model.addConstr(4 * x1 <= 16)
model.addConstr(4 * x2 <= 12)
print("约束数量：", model.getAttr("rows"))

# Set objective function
model.setObjective( 2 * x1 + 3 * x2, sense=COPT.MAXIMIZE)
print("模型优化方向是：", model.ObjSense)

# Solve the problem:set parameter
model.setParam(COPT.Param.TimeLimit, 10.0)

# Solve the model
model.solve()

# Analyze solution
if model.status == COPT.OPTIMAL:
    # Optimal objective value
    print("\n\n最优解与最优方案为:\n")
    print("最大利润为：{0:.4f}".format(model.objval))
    allvars = model.getVars()
    # Variable value
    print("\nValue of each variable:\n")
    for var in allvars:
        print("决策变量{0},最优值为 {1:.4f}，基状态为：{2}".format(var.name, var.x, var.basis))
