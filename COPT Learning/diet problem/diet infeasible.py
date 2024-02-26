"""
This is a COPT learning document, not for commercial use. It is mainly for recording and archiving the study and use of COPT interfaces.
For specific examples, please refer to: https://coridm.d2d.ai/courses/32/supplement/779
"""

import coptpy as cp
from coptpy import COPT
import itertools

# Create COPT environment
env = cp.Envr()
# Create COPT model
model = env.createModel(name="diet_infeasible")

# Describe model parameters
# Constraint Bound
nutrition, minNutrition, maxNutrition = cp.multidict({
    'Vitamin A': [700, 10000],
    'Vitamin C': [700, 10000],
    'Vitamin B1': [700, 10000],
    'Vitamin B2': [700, 10000],
    'sodium': [0, 40000],
    'calories': [16000, 24000]
})

# Cost info. of foods (obj coef)
foods, cost = cp.multidict({
    'BEEF': 3.19,
    'CHK': 2.59,
    'FISH': 2.29,
    'HAM': 2.89,
    'MCH': 1.89,
    'MTL': 1.99,
    'SPG': 1.99,
    'TUR': 2.49})

# Nutrition values for the foods
nutri_values_list = [60, 20, 10, 15, 938, 295, 8, 0, 20, 20, 2180, 770, 8, 10, 15, 10, 945, 440, 40, 40, 35, 10, 278,
                     430,
                     15, 35, 15, 15, 1182, 315, 70, 30, 15, 15, 896, 400, 25, 50, 25, 15, 1329, 370, 60, 20, 15, 10,
                     1397, 450]

nutri_food = cp.tuplelist()
for each in itertools.product(foods, nutrition):
    nutri_food.add(each)

nutri_values = cp.tupledict(zip(nutri_food, nutri_values_list))

'''
Create and Solve Model
'''
#Add Variables:
buy = model.addVars(foods, nameprefix="x")

#Set Variable Bounds:
model.setInfo(COPT.Info.LB, buy, 2)
model.setInfo(COPT.Info.UB, buy, 15)

'''
#Add constraints
#Add Lower Bound Constraint
model.addConstrs((quicksum(nutri_values[(f,n)] * buy[f] for f in foods)
                 >= minNutrition[n] for n in nutrition), nameprefix="R_L" )
#Add Upper Bound Constraint
model.addConstrs((quicksum(nutri_values[(f,n)] * buy[f] for f in foods)
                 <= maxNutrition[n] for n in nutrition), nameprefix="R_U" )
'''

# Add Bound Constraints:
for n in nutrition:
    model.addBoundConstr(cp.quicksum(nutri_values[f, n] * buy[f] for f in foods), minNutrition[n], maxNutrition[n], name=n)

#Set Objective
model.setObjective(cp.quicksum(cost[f]*buy[f] for f in foods), sense=COPT.MINIMIZE)

model.solve()
print("---"*30)
print("模型求解状态：", model.status)

# Compute IIS if problem is infeasible
if model.status == COPT.INFEASIBLE:
    # Compute IIS
    model.computeIIS()
    if model.hasIIS:
        allconstrs = model.getConstrs()
        allvars = model.getVars()
        print("---"*7,"不可行检测 result of Variables","---"*7)
        for var in allvars:
            if var.iislb or var.iisub:
                print("{0}:{1}".format(var.name, "Lower Bound" if var.iislb else "Upper Bound"))

        print("---"*7,"不可行检测 result of Constraints","---"*7)
        for constr in allconstrs:
                if constr.iislb or constr.iisub:
                    print("{0}：{1}".format(constr.name, "Lower Bound" if constr.iislb else "Upper Bound"))

# Compute feasibility relaxation if problem is infeasible
if model.status == COPT.INFEASIBLE:
    # Set feasibility relaxation mode
    model.setParam(COPT.Param.FeasRelaxMode, 2)
    # Compute feasibility relaxation
    model.feasRelaxS(vrelax=True, crelax=True)
    # Check if feasibility relaxation solution is available
    if model.hasFeasRelaxSol:
        # Print violations of variables and constraints
        allconstrs = model.getConstrs()
        allvars = model.getVars()
        print("\n======================== FeasRelax result ========================")
        for constr in allconstrs:
            lowRelax = constr.RelaxLB
            uppRelax = constr.RelaxUB
            if lowRelax != 0.0 or uppRelax != 0.0:
                print("约束条件 {0}: violation = ({1}, {2})".format(constr.name, lowRelax, uppRelax))
        print("")
        for var in allvars:
            lowRelax = var.RelaxLB
            uppRelax = var.RelaxUB
            if lowRelax != 0.0 or uppRelax != 0.0:
                print("变量范围 {0}: violation = ({1}, {2})".format(var.name, lowRelax, uppRelax))

# 调整模型
buy['HAM'].setInfo(COPT.Info.UB, 30)
model.solve()


# 也可以通过调整约束的上下界
buy['HAM'].setInfo(COPT.Info.UB, 15)
c_sodium = model.getConstrByName("sodium")
c_sodium.setInfo(COPT.Info.UB, 50000)
model.solve()