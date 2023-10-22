from coptpy import *

# Create COPT environment
env = Envr()
# create model
master_problem = env.createModel("benders decomposition example step by step")

""" create decision variables """
y = master_problem.addVar(lb=0, ub=COPT.INFINITY, vtype=COPT.INTEGER, name='y')
z = master_problem.addVar(lb=0, ub=COPT.INFINITY, vtype=COPT.INTEGER, name='z')

master_problem.setObjective(z, COPT.MAXIMIZE)

master_problem.addConstr(1000 - y >= 0, name='benders feasibility cut iter 1')

master_problem.solve()
print('\n\n\n')
if master_problem.status == COPT.OPTIMAL:
    print('Obj:', master_problem.objval)
    print('z = %4.1f'.format(z.x))
    print('y = %4.1f'.format(y.x))

# 第一次迭代，子问题
y_bar = 1500

Dual_SP = env.createModel("Dual SP")

""" create decision variables """
alpha_0 = Dual_SP.addVar(lb=0, ub=COPT.INFINITY, vtype=COPT.CONTINUOUS, name='alpha_0')
alpha = {}
for i in range(10):
    alpha[i] = Dual_SP.addVar(lb=0, ub=COPT.INFINITY, vtype=COPT.CONTINUOUS, name='alpha_' + str(i))

""" create objective """
obj = LinExpr(0)
obj.addTerms(alpha_0, 1000 - y_bar)
for i in range(10):
    obj.addTerms(alpha[i], 100)

Dual_SP.setObjective(obj, COPT.MINIMIZE)

""" add constraints 1-10 """
for i in range(10):
    Dual_SP.addConstr(alpha_0 + alpha[i] >= 1 + 0.01 * (i + 1))

# Dual_SP.setParam(COPT.Param.HasPrimalRay, 1)
# 设置极射线
Dual_SP.setParam("ReqFarkasRay", 1)

Dual_SP.solve()
print('\n\n')
print('Model status:', Dual_SP.status)
if Dual_SP.status == COPT.OPTIMAL:
    print('Obj:', Dual_SP.ObjVal)
    for i in range(10):
        if alpha[i].x > 0:
            print('{} = {}'.format(alpha[i].name, alpha[i].x))
else:
    print('===== Infeasible or Unbounded information =====')
    print('extreme ray: {} = {}'.format(alpha_0.name, alpha_0.getInfo(COPT.Info.PrimalRay)))
    for i in range(10):
        print('extreme ray: {} = {}'.format(alpha[i].name, alpha[i].getInfo(COPT.Info.PrimalRay)))