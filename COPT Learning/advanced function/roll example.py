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
ncut = mcut.addVars(nkind, nroll, vtype=COPT.INTEGER, nameprefix='ncut')
ifcut = mcut.addVars(nroll, vtype=COPT.BINARY, nameprefix='ifcut')

print("模型中所有变量个数：{}".format(mcut.getAttr("Cols")))
print("模型中所有变量个数：{}".format(mcut.Cols))

print("二进制变量个数：{}".format(mcut.Bins))
print("整数型变量个数：{}".format(mcut.Ints))

print("模型中所有约束个数：{}".format(mcut.Rows))

# Add constraints to problem
mcut.addConstrs(ncut.sum(i, '*') >= rolldemand[i] for i in range(nkind))
print("模型当前约束数目：{}".format(mcut.Rows))

mcut.addConstrs(quicksum(ncut[i, k] * rollsize[i] for i in range(nkind)) <= rollwidth * ifcut[k]
                for k in range(nroll))
print("模型当前约束数目：{}".format(mcut.Rows))

mcut.addConstrs((ifcut[i - 1] >= ifcut[i] for i in range(1, nroll)))
print("模型当前约束数目：{}".format(mcut.Rows))

# Set objective function
mcut.setObjective(ifcut.sum("*"), COPT.MINIMIZE)

# mcut.setParam(COPT.Param.TimeLimit, 200)
mcut.setParam(COPT.Param.TimeLimit, 20)
mcut.solve()

