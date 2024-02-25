"""
This is a COPT learning document, not for commercial use. It is mainly for recording and archiving the study and use of COPT interfaces.
For specific details, please refer to: https://coridm.d2d.ai/courses/32/supplement/793
"""

import coptpy as cp
from coptpy import COPT
import itertools
import pandas as pd
import numpy as np


# Create COPT environment
env = cp.Envr()
# Create COPT problem
model = env.createModel("location transport")

# M = 8
buildlimit = 8
# n = 30
citylimit = 30
# cities
ncity = citylimit
cities = ['city' + str(i) for i in range(ncity)]

# print("cities =", cities)

supply_list = pd.read_csv("supply.txt")["supply"].tolist()
demand_list = pd.read_csv("demand.txt")["demand"].tolist()
shipcost_list = np.array(pd.read_csv("trans_dt.txt", index_col=0)).reshape(-1)
print("单位运输费用规模：{}".format(shipcost_list.shape))


supply = dict(zip(cities, supply_list))
demand = dict(zip(cities, demand_list))
shipcost = cp.tupledict(zip(itertools.product(cities, cities), shipcost_list))

# show the shipcost
count = 0
for key in shipcost:
    print("key: {0}  value:{1}".format(key, shipcost[key]))
    count +=1
    if count == 15:
        break

# Add variables to problem
vbuild = model.addVars(cities, vtype=COPT.BINARY, nameprefix='build')
vship  = model.addVars(cities, cities, vtype=COPT.INTEGER, nameprefix='ship')
print("模型中决策变量数量：{}".format(model.getAttr(attrname="cols")))

# Add constraints to problem
model.addConstr(vbuild.sum('*') <= buildlimit, name='limit')
print("模型当前约束数量：{}".format(model.getAttr(attrname="rows")))

model.addConstrs((vship.sum(i, '*') <= supply[i] * vbuild[i] for i in cities), nameprefix='supply')
print("模型当前约束数量：{}".format(model.getAttr(attrname="Rows")))

model.addConstrs((vship.sum('*', j) >= demand[j] for j in cities), nameprefix='demand')
print("模型当前约束数量：{}".format(model.getAttr(attrname="Rows")))

# Set objective function
model.setObjective(vship.prod(coeff=shipcost), COPT.MINIMIZE)

model.write("location transport.lp")

# model.getParam(COPT.Param.CutLevel)
print(model.getParamInfo(COPT.Param.TimeLimit))
print(model.getParamInfo(COPT.Param.NodeLimit))
print(model.getParamInfo(COPT.Param.RelGap))
print(model.getParamInfo(COPT.Param.IntTol))
print(model.getParamInfo(COPT.Param.FeasTol))


# Set optimization parameters
model.setParam(COPT.Param.TimeLimit, 100)


# Solve the problem
model.solve()


# map: num --> model status
status_map = {
    0:"COPT.UNSTARTED",
    1:"COPT.OPTIMAL",
    2:"COPT.INFEASIBLE",
    3:"COPT.UNBOUNDED",
    4:"COPT.INF_OR_UNB",
    5:"COPT.NUMERICAL",
    6:"COPT.NODELIMIT",
    7:"COPT.TIMEOUT",
    8:"COPT.UNFINISHED",
    9:"COPT.INTERRUPTED"
}


# Display solution
if model.status == COPT.OPTIMAL or \
    model.status in [COPT.TIMEOUT, COPT.NODELIMIT, COPT.INTERRUPTED] and \
    model.hasmipsol:
    print('模型求解状态：{0}'.format(status_map[model.status]))
    print('')
    print('最小总运输成本: {0:.6f}'.format(model.objval))
    print('')
    print("---"*7,"最优仓库选址方案：","---"*7)
    for key in vbuild:
        if vbuild[key].x > 1e-6:
            print('选择{0:6s}建造仓库'.format(key))
    print('')
    print("---"*7,"最优商品运输方案：","---"*7)
    for key in vship:
        if vship[key].x > 1e-6:
            print("{0} --> {1}: {2:6f} 件".format(key[0], key[1], vship[key].x))
else:
  print('Unexpected solution status')