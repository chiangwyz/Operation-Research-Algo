import coptpy as cp
from coptpy import COPT
import itertools

# Create environment
env = cp.Envr()
# Create model
model = env.createModel(name="transportation")

origins, supply = cp.multidict({
    'GARY': 1400,
    'CLEV': 2600,
    'PITT': 2900})

print("origins =", origins)

destinations, demand = cp.multidict({
    'FRA': 900,
    'DET': 1200,
    'LAN': 600,
    'WIN': 400,
    'STL': 1700,
    'FRE': 1100,
    'LAF': 1000})

print("destinations =", destinations)

cost_list = [39, 14, 11, 14, 16, 82, 8, 27, 9, 12, 9, 26, 95, 17, 24, 14, 17, 13, 28, 99, 20]

orig_desti = cp.tuplelist()
for each in itertools.product(origins, destinations):
    orig_desti.add(each)
cost = dict(zip(orig_desti, cost_list))
print("orig_desti =", orig_desti)
print("cost =", cost)

# 这里从orig_desti中模糊匹配到了出发地为GARY的所有tuple
print("GARY select =", orig_desti.select('GARY', '*'))

# Add variables
transport = model.addVars(orig_desti)
print("决策变量的个数为：", model.getAttr(attrname="cols"))

# Add Origins constraints:
model.addConstrs(transport.sum(s, "*") <= supply[s] for s in origins)
print("约束条件数量：", model.getAttr(attrname="rows"))

# Add Destinations constraints:
model.addConstrs(transport.sum("*", t) >= demand[t] for t in destinations)
print("约束条件数量：", model.getAttr(attrname="rows"))

#Set Objective
model.setObjective(transport.prod(cost), sense=COPT.MINIMIZE)

#solve the problem
model.solve()

# Analyze solution
if model.status == COPT.OPTIMAL:
    # Optimal objective value
    print("Optimal Value of objective:{:.4f}".format(model.objval))
    allvars = model.getVars()
    #Variable value
    print("\nValue of each variable:")
    for var in allvars:
        print("决策变量{0},最优值为 {1:.4f}，基状态为：{2}".format(var.name, var.x, var.basis))