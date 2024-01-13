"""
This is a COPT learning document, not for commercial use. It is mainly for recording and archiving the study and use of COPT interfaces.
For specific examples, please refer to: https://coridm.d2d.ai/courses/32/supplement/782
"""

from coptpy import *

# Create environment
env = Envr()

# Create model
model = env.createModel(name="diet_advanced")

# Constraints info. of nutrition
nutrition, minNutrition, maxNutrition = multidict({
    'Vitamin A':  [700, 10000],
    'Vitamin C':  [700, 10000],
    'Vitamin B1': [700, 10000],
    'Vitamin B2': [700, 10000]})

# Cost info. of foods (obj coef)
foods, cost = multidict({
    'BEEF': 3.19,
    'CHK':  2.59,
    'FISH': 2.29,
    'HAM':  2.89,
    'MCH':  1.89,
    'MTL':  1.99,
    'SPG':  1.99,
    'TUR':  2.49})

# Nutrition values for the foods
nutritionValues = {
    ('BEEF', 'Vitamin A'):  60,
    ('BEEF', 'Vitamin C'):  20,
    ('BEEF', 'Vitamin B1'): 10,
    ('BEEF', 'Vitamin B2'): 15,
    ('CHK', 'Vitamin A'):   8,
    ('CHK', 'Vitamin C'):   0,
    ('CHK', 'Vitamin B1'):  20,
    ('CHK', 'Vitamin B2'):  20,
    ('FISH', 'Vitamin A'):  8,
    ('FISH', 'Vitamin C'):  10,
    ('FISH', 'Vitamin B1'): 15,
    ('FISH', 'Vitamin B2'): 10,
    ('HAM', 'Vitamin A'):   40,
    ('HAM', 'Vitamin C'):   40,
    ('HAM', 'Vitamin B1'):  35,
    ('HAM', 'Vitamin B2'):  10,
    ('MCH', 'Vitamin A'):   15,
    ('MCH', 'Vitamin C'):   35,
    ('MCH', 'Vitamin B1'):  15,
    ('MCH', 'Vitamin B2'):  15,
    ('MTL', 'Vitamin A'):   70,
    ('MTL', 'Vitamin C'):   30,
    ('MTL', 'Vitamin B1'):  15,
    ('MTL', 'Vitamin B2'):  15,
    ('SPG', 'Vitamin A'):   25,
    ('SPG', 'Vitamin C'):   50,
    ('SPG', 'Vitamin B1'):  25,
    ('SPG', 'Vitamin B2'):  15,
    ('TUR', 'Vitamin A'):   60,
    ('TUR', 'Vitamin C'):   20,
    ('TUR', 'Vitamin B1'):  15,
    ('TUR', 'Vitamin B2'):  10}

#Add variables
buy = model.addVars(foods)

var_show = buy['BEEF']
print("决策变量BEEF的名称：",var_show.name)
print("决策变量BEEF的变量类型：",var_show.getType())
print("模型中决策变量的数量：",model.getAttr(attrname="Cols"))

#Add constraints
#Add Lower Bound Constraint
model.addConstrs(quicksum(nutritionValues[(f,n)] * buy[f] for f in foods)
                 >= minNutrition[n] for n in nutrition)
#Add Upper Bound Constraint
model.addConstrs(quicksum(nutritionValues[(f,n)] * buy[f] for f in foods)
                 <= maxNutrition[n] for n in nutrition)
print("约束数量：", model.getAttr(attrname="rows"))

#Set Objective--quicksum()
model.setObjective(quicksum(cost[f]*buy[f] for f in foods), sense=COPT.MINIMIZE)

#solve the problem
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

# variables:basis,reduced cost:
allvars = model.getVars()
for var in allvars:
    print("{0}最优值：{1:.4f}\t基状态：{2}\treduced cost：{3:.4f}".format(var.name, var.x, int(var.basis), var.rc))

# constraints slack and dual
constr_list = model.getConstrs()
allslacks =model.getSlacks()
allduals = model.getDuals()
for (constr, dual, slack) in zip(constr_list, allduals, allslacks):
    print("约束{0}，对偶变量的值{1:.4f}，松弛变量的值{1:.4f}".format(constr.getName(), dual, slack))

