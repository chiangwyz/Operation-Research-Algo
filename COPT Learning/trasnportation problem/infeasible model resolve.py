"""
This is a COPT learning document, not for commercial use. It is mainly for recording and archiving the study and use of COPT interfaces.
For specific details, please refer to: https://coridm.d2d.ai/courses/32/supplement/795
"""

from coptpy import *
import itertools
import pandas as pd
import numpy as np

# Create COPT environment
env = Envr()
# Create COPT problem
model = env.createModel("locationtransport")

# 最大仓库建造数：buildlimit = 6
buildlimit = 6
citylimit = 30
ncity = citylimit
cities = ['city' + str(i) for i in range(ncity)]

supply_list = pd.read_csv("supply.txt")["supply"].tolist()
demand_list = pd.read_csv("demand.txt")["demand"].tolist()
shipcost_list = np.array(pd.read_csv("trans_dt.txt", index_col=0)).reshape(-1)

supply = dict(zip(cities, supply_list))
demand = dict(zip(cities, demand_list))
shipcost = tupledict(zip(itertools.product(cities, cities), shipcost_list))


# Add variables to problem
vbuild = model.addVars(cities, vtype=COPT.BINARY, nameprefix='build')
vship  = model.addVars(cities, cities, vtype=COPT.INTEGER, nameprefix='ship')

# Add constraints to problem
model.addConstr(vbuild.sum('*') <= buildlimit, name='limit')
model.addConstrs((vship.sum(i, '*') <= supply[i] * vbuild[i] for i in cities), nameprefix='supply')
model.addConstrs((vship.sum('*', j) >= demand[j] for j in cities), nameprefix='demand')

# Set objective function
model.setObjective(vship.prod(coeff=shipcost), COPT.MINIMIZE)

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

print('模型求解状态：{0}'.format(status_map[model.status]))


# Compute feasibility relaxation if problem is infeasible
if model.status == COPT.INFEASIBLE:
    # Set feasibility relaxation mode
    # model.setParam(COPT.Param.FeasRelaxMode, 2)
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

#Set new Constraint Bound
constr_limit = model.getConstrByName("limit")
model.setInfo(COPT.Info.UB, constr_limit, 7)

model.solve()

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