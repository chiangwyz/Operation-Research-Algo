"""
使用benders decomposition 求解投资问题
例子与代码参考 《运筹优化常用模型、算法及案例实战——Python+Java实现》
刘兴禄，熊望祺，臧永森，段宏达，曾文佳 2022年，清华大学出版社
"""

from coptpy import *

# Create COPT environment
env = Envr()
# create model
model = env.createModel("benders decomposition example")


""" create decision variables """
y = model.addVar(lb=0, ub=1000, vtype=COPT.INTEGER, name='y')
x = {}

for i in range(10):
    x[i] = model.addVar(lb=0, ub=100, vtype=COPT.CONTINUOUS, name='x_' + str(i))

""" set objective function """
obj = LinExpr(0)
obj.addTerms(y, 1.045)
for i in range(10):
    obj.addTerms(x[i], 1 + 0.01 * (i + 1))
model.setObjective(obj, COPT.MAXIMIZE)

""" add constraints """
lhs = LinExpr(0)
lhs.addTerms(y, 1)
for i in range(10):
    lhs.addTerms(x[i], 1)
model.addConstr(lhs <= 1000, name='budget')

model.solve()
print('\n\n')
print('Obj:', model.objval)
print('Saving account : ', y.x)
for i in range(10):
    if x[i].x > 0:
        print('Fund ID {}: amount: {}'.format(i+1, x[i].x))