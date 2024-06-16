import gurobipy as grbpy
from gurobipy import GRB

"""
To illustrate the primal and dual theory
"""
primal_model = grbpy.Model('Primal problem')

primal_model.setParam(GRB.Param.OutputFlag, 1)
primal_model.setParam(GRB.Param.Presolve, 0)

model_vars = []
for i in range(5):
    model_vars.append(primal_model.addVar(lb=0.0, ub=GRB.INFINITY, vtype=GRB.CONTINUOUS, name="x_"+str(i)))

primal_model.addConstr(model_vars[0] + model_vars[1] + 2 * model_vars[2] + model_vars[3] + 3 * model_vars[4] >= 4, name="constr_1")
primal_model.addConstr(2 * model_vars[0] - 2 * model_vars[1] + 3 * model_vars[2] + model_vars[3] + model_vars[4] >= 3, name="constr_2")

linear_expr = 2 * model_vars[0] + 3 * model_vars[1] + 5 * model_vars[2] + 2 * model_vars[3] + 3 * model_vars[4]
primal_model.setObjective(linear_expr, GRB.MINIMIZE)

primal_model.write("primal_model.lp")
primal_model.optimize()

if primal_model.status == GRB.OPTIMAL:
    print(f"\nObjective: {primal_model.ObjVal:g}")
    for var in primal_model.getVars():
        print("{} = {}".format(var.VarName, var.X))

    for dual in primal_model.getConstrs():
        print("{} = {}".format(dual.ConstrName, dual.Pi))

print("\n\n")


dual_model = grbpy.Model('Dual problem')
dual_model.setParam(GRB.Param.OutputFlag, 1)
dual_model.setParam(GRB.Param.Presolve, 0)

dual_vars = []
for i in range(2):
    dual_vars.append(dual_model.addVar(lb=0.0, ub=GRB.INFINITY, vtype=GRB.CONTINUOUS, name="pi_"+str(i)))

dual_model.addConstr(dual_vars[0] + 2 * dual_vars[1] <= 2, name="constr_1")
dual_model.addConstr(dual_vars[0] - 2 * dual_vars[1] <= 3, name="constr_2")
dual_model.addConstr(2 * dual_vars[0] + 3 * dual_vars[1] <= 5, name="constr_3")
dual_model.addConstr(dual_vars[0] + dual_vars[1] <= 2, name="constr_4")
dual_model.addConstr(3*dual_vars[0] + dual_vars[1] <= 3, name="constr_5")

linear_expr = 4 * dual_vars[0] + 3 * dual_vars[1]
dual_model.setObjective(linear_expr, GRB.MAXIMIZE)

dual_model.write("dual_model.lp")
dual_model.optimize()

if dual_model.status == GRB.OPTIMAL:
    print(f"\nObjective: {dual_model.ObjVal:g}")
    for var in dual_model.getVars():
        print("{} = {}".format(var.VarName, var.X))

    for dual in dual_model.getConstrs():
        print("{} = {}".format(dual.ConstrName, dual.Pi))