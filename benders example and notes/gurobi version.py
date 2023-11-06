from gurobipy import *

alpha_obj_coef = [8, 3, 5]

Dual_SP = Model('Dual SP')

""" create decision variables """
alpha = {}
for i in range(3):
    alpha[i] = Dual_SP.addVar(lb=-GRB.INFINITY, ub=GRB.INFINITY, vtype=GRB.CONTINUOUS, name='alpha_' + str(i+1))
beta = {}
for i in range(5):
    beta[i] = Dual_SP.addVar(lb=-GRB.INFINITY, ub=0, vtype=GRB.CONTINUOUS, name='beta_' + str(i+1))

""" create objective """
obj = LinExpr()
for i in range(3):
    obj.addTerms(alpha_obj_coef[i], alpha[i])

Dual_SP.setObjective(obj, GRB.MAXIMIZE)

""" add constraints 1-10 """
Dual_SP.addConstr(alpha[0] + beta[0] <= 1)
Dual_SP.addConstr(alpha[1] + beta[1] <= 1)
Dual_SP.addConstr(alpha[2] + beta[2] <= 1)
Dual_SP.addConstr(alpha[0] + alpha[2] + beta[3] <= 1)
Dual_SP.addConstr(alpha[0] + alpha[1] + beta[4] <= 1)


Dual_SP.setParam('InfUnbdInfo', 1)
Dual_SP.optimize()

print('\n\n\n')
print('Model status:', Dual_SP.status)
if(Dual_SP.status == 2):
    print('Obj:', Dual_SP.ObjVal)
    for i in range(10):
        if(alpha[i].x > 0):
            print('{} = {}'.format(alpha[i].varName, alpha[i].x))
else:
    print('===== Infeasible or Unbounded information =====')
    for i in range(3):
        print('extreme ray: {} = {}'.format(alpha[i].varName, alpha[i].UnbdRay))
    for i in range(5):
        print('extreme ray: {} = {}'.format(beta[i].varName, beta[i].UnbdRay))