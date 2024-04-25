#
# This file is part of the Cardinal Optimizer, all rights reserved.
#

import coptpy as cp
from coptpy import COPT

rollwidth  = 115
rollsize   = [40, 55, 40, 70, 50, 70, 70, 30, 25, 30]
rolldemand = [42, 49, 16, 10, 37, 48, 10, 32, 35, 13]
nkind      = len(rollsize)
ndemand    = 200

# Create COPT environment
env = cp.Envr()

# Create COPT problem
mcut = env.createModel()

# Add variables to problem
ncut  = mcut.addVars(nkind, ndemand, vtype=COPT.INTEGER, nameprefix='x')
ifcut = mcut.addVars(ndemand, vtype=COPT.BINARY, nameprefix='c')

# Add constraints to problem
mcut.addConstrs(ncut.sum(i, '*') >= rolldemand[i] for i in range(nkind))
mcut.addConstrs(cp.quicksum(ncut[i, j] * rollsize[i] for i in range(nkind)) <= rollwidth * ifcut[j] \
                for j in range(ndemand))

# Optional: Symmetry breaking constraints
mcut.addConstrs((ifcut[i - 1] >= ifcut[i] for i in range(1, ndemand)))

# Set objective function
mcut.setObjective(ifcut.sum('*'), COPT.MINIMIZE)

# Set optimization parameters
mcut.setParam(COPT.Param.TimeLimit, 120)

# Solve the problem
mcut.solve()

# Display the solution
if mcut.status == COPT.OPTIMAL or \
   mcut.status in [COPT.TIMEOUT, COPT.NODELIMIT, COPT.INTERRUPTED] and \
   mcut.hasmipsol:
  print('\nBest MIP objective value: {0:.0f}'.format(mcut.objval))

  print('Cut patterns: ')
  for key in ncut:
    if ncut[key].x > 1e-6:
      print('  {0:8s} = {1:.0f}'.format(ncut[key].name, ncut[key].x))
