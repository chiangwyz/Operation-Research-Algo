import numpy as np
import gurobipy as gp
from gurobipy import GRB
from program_parameter import *


def perform_simple_rounding(rel_sol):
    rounded_sol = np.ceil(rel_sol)

    return rounded_sol


down_threshold = 0.2
up_threshold = 0.8


def solve_subproblem(parameter, price_dual):
    # initialization of SP
    SP_model = gp.Model('Subproblem')

    # variables of subproblem
    quantity = SP_model.addVars(parameter.num_types, vtype=GRB.INTEGER)

    # adding objective function
    SP_model.setObjective(gp.quicksum(price_dual[i] * quantity[i] for i in range(parameter.num_types)), GRB.MAXIMIZE)

    # constraint of subproblem
    SP_model.addConstr(gp.quicksum(quantity[i]*parameter.specification[i] for i in range(parameter.num_types)) <= parameter.length_raw, name='capacity constraint')

    # solve Subproblem
    SP_model.Params.OutputFlag = 0
    SP_model.optimize()
    reduced_cost = 1-SP_model.objVal

    # get the new pattern
    new_pattern = np.array(SP_model.getAttr('x', SP_model.getVars()), dtype=int)

    return reduced_cost, new_pattern


def solve_CSP_with_CG(parameter, pattern_matrix, residual_demand):
    # initialize
    num_patterns = np.shape(pattern_matrix)[1]

    # create RMP
    RMP_model = gp.Model('Restricted Masterproblem')

    # variables of RMP
    quantity_pattern = RMP_model.addVars(num_patterns, obj=1, vtype=GRB.CONTINUOUS)

    # constraints of RMP (demand satisfaction)
    RMP_model.addConstrs((gp.quicksum(pattern_matrix[i][j] * quantity_pattern[j] for j in range(num_patterns)) >=
                          residual_demand[i] for i in range(parameter.num_types)), name='demand satisfaction')

    # objective function
    RMP_model.setAttr(GRB.Attr.ModelSense, GRB.MINIMIZE)

    # solver parameter
    RMP_model.Params.OutputFlag = 0

    # main steps
    while True:
        # solve RMP
        RMP_model.optimize()

        # get the dual variable value
        price_dual = RMP_model.getAttr(GRB.Attr.Pi, RMP_model.getConstrs())

        # solve pricing subproblem
        reduced_cost, new_pattern = solve_subproblem(parameter, price_dual)

        # check termination condition
        if np.abs(reduced_cost) <= TOL or reduced_cost >= 0:
            break

        # set the new pattern as a new column in the coefficient matrix
        new_column = gp.Column(new_pattern, RMP_model.getConstrs())

        # add the new variable
        quantity_pattern[num_patterns] = RMP_model.addVar(obj=1.0, vtype=GRB.CONTINUOUS, column=new_column)
        pattern_matrix = np.c_[pattern_matrix, new_pattern]
        num_patterns += 1

    # record and print solution
    quantity_sol = np.zeros(num_patterns)
    for j in range(num_patterns):
        quantity_sol[j] = quantity_pattern[j].x

    return pattern_matrix, quantity_sol


def perform_diving_heuristic(rel_sol, parameter, pattern):
    # initialization
    total_consumption = 0
    residual_demand = parameter.demand
    rounded_sol = np.array([])
    num_new_patterns = len(rel_sol)
    # main steps
    while residual_demand.sum() > 0:
        num_patterns = len(rel_sol)
        rounded_sol = np.pad(rounded_sol, (0, num_new_patterns), 'constant')  # expand array
        num_rounded = 0
        for j in range(num_patterns):
            # round down
            if rel_sol[j] - np.floor(rel_sol[j]) <= down_threshold:
                rounded_sol[j] += np.floor(rel_sol[j])
                num_rounded += 1
            # round up
            elif rel_sol[j] - np.floor(rel_sol[j]) >= up_threshold:
                rounded_sol[j] += np.ceil(rel_sol[j])
                num_rounded += 1

        # none elements rounded
        if num_rounded == 0:
            # determine the least fractional element to round up/down
            fraction = np.abs(np.round(rel_sol) - rel_sol)
            fractional_index = np.array([k for k in range(num_patterns) if fraction[k] > TOL])
            k = fractional_index[np.argmin(fraction[fractional_index])]
            rounded_sol[k] += np.round(rel_sol[k])

        # check if the residual problem stays unchanged
        if rounded_sol.sum() == total_consumption:
            # choose the least fractional element to round up, so that the residual problem becomes smaller
            fraction = np.ceil(rel_sol) - rel_sol
            fractional_index = np.array([k for k in range(num_patterns) if fraction[k] > TOL])
            k = fractional_index[np.argmin(fraction[fractional_index])]
            rounded_sol[k] += np.ceil(rel_sol[k])

        # update total consumption and residual demand
        total_consumption = rounded_sol.sum()
        index = [i for i in range(num_patterns) if rounded_sol[i] > 0]
        sat_matrix = np.zeros((len(index), parameter.num_types), dtype=int)
        for i in range(len(index)):
            sat_matrix[i] = pattern.T[index][i] * rounded_sol[index][i]
        residual_demand = parameter.demand - sat_matrix.sum(axis=0)
        residual_demand = np.maximum(0, residual_demand)

        if residual_demand.sum() == 0:
            break

        pattern, rel_sol = solve_CSP_with_CG(parameter, pattern, residual_demand)
        num_new_patterns = len(rel_sol) - num_patterns

    return rounded_sol, pattern
