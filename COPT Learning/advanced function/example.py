from coptpy import *
env = Envr()
model = env.createModel("example")

# Add variables: x, y, z
x = model.addVar(lb=0.1, ub=0.6, name="x")
y = model.addVar(lb=0.2, ub=1.5, name="y")
z = model.addVar(lb=0.0, ub=3.0, name="z", vtype=COPT.INTEGER)

# Add constraints
model.addConstr(1.5*x + 1.2*y + 1.8*z <= 2.6)
model.addConstr(0.8*x + 0.6*y + 0.9*z >= 1.2)

# Set objective function
model.setObjective(1.2*x + 1.8*y + 2.1*z, sense=COPT.MAXIMIZE)

# Set parameter
model.setParam(COPT.Param.TimeLimit, 10.0)


# 1. set complete mipstart solution
model.setMipStart(model.getVars(), [0.1, 0.2, 1])
model.loadMipStart()

# 2. set partial mipstart solution
model.setMipStart(z, 1)
model.setMipStart(y, 0.2)
model.loadMipStart()

model.resetAll()

# 3. set the same value for all variables as mipstart solution
model.setMipStart([x, y, z], 0.5)
model.loadMipStart()

# 4. out of bound
model.setMipStart(model.getVars(), [0.7, 0.2, -1])
model.loadMipStart()

model.setParam("MipStartMode", 2)

model.solve()