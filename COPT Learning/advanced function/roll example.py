from coptpy import *
import numpy as np

# 每根钢管的长度 W
rollwidth = 115
# 各零件的不同规格 w_i
rollsize = [25, 40, 50, 55, 70]
# 零件规格的类型数 |I|
nkind = len(rollsize)
# 各零件的需求量 d_i
rolldemand = [50, 136, 114, 80, 89]
# 钢管的供应量 |K|
nroll = 500
# nroll = int(sum([np.ceil(rolldemand[i] / np.floor(rollwidth / rollsize[i])) for i in range(nkind)]))

# Create COPT environment
env = Envr()
# Create COPT problem
mcut = env.createModel("cutstock")


# Add variables to problem
x = mcut.addVars(nkind, nroll, vtype=COPT.INTEGER, nameprefix='x')
y = mcut.addVars(nroll, vtype=COPT.BINARY, nameprefix='y')

print("模型中所有变量个数：{}".format(mcut.getAttr("Cols")))
print("模型中所有变量个数：{}".format(mcut.Cols))

print("二进制变量个数：{}".format(mcut.Bins))
print("整数型变量个数：{}".format(mcut.Ints))

print("模型中所有约束个数：{}".format(mcut.Rows))

# Add constraints to problem
mcut.addConstrs(x.sum(i, '*') >= rolldemand[i] for i in range(nkind))
print("模型当前约束数目：{}".format(mcut.Rows))

mcut.addConstrs(quicksum(x[i, k] * rollsize[i] for i in range(nkind)) <= rollwidth * y[k]
                for k in range(nroll))
print("模型当前约束数目：{}".format(mcut.Rows))

mcut.addConstrs((y[i - 1] >= y[i] for i in range(1, nroll)))
print("模型当前约束数目：{}".format(mcut.Rows))

# Set objective function
mcut.setObjective(y.sum("*"), COPT.MINIMIZE)

# mcut.setParam(COPT.Param.TimeLimit, 200)
mcut.setParam(COPT.Param.TimeLimit, 60)
mcut.solve()

# Set initial solution
k = 0
# for each i in I
for i in range(nkind):
    n = int(np.floor(rollwidth / rollsize[i])) #n_i
    m = int(np.ceil(rolldemand[i] / n)) #m_i
    # set initial solution for each variable
    for j in range(m-1):
        mcut.setMipStart(x[i, k+j], n)
        mcut.setMipStart(y[k+j], 1)
    mcut.setMipStart(x[i, k+m-1], rolldemand[i]-n*(m-1))
    mcut.setMipStart(y[k+m-1], 1)
    k += m
mcut.loadMipStart()
mcut.setParam(COPT.Param.MipStartMode, 2)

# Solve the problem
mcut.solve()