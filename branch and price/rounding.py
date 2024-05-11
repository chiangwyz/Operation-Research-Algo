import numpy as np
import gurobipy as grbpy
from gurobipy import GRB
from algorithm_parameters import *


def perform_simple_rounding(rel_sol):
    # 对给定的解进行简单的向上取整
    rounded_sol = np.ceil(rel_sol)

    return rounded_sol


def solve_sub_problem_embed_in_diving_heuristic(data, price_dual):
    # initialization of SP

    sub_model = grbpy.Model("sub problem")

    quantity = sub_model.addVars(data.Customer_numbers, vtype=GRB.INTEGER)

    sub_model.setObjective(grbpy.quicksum(price_dual[i] * quantity[i] for i in range(data.Customer_numbers)), GRB.MAXIMIZE)

    sub_model.addConstr(grbpy.quicksum(quantity[i]*data.customer_demand_sizes[i] for i in range(data.Customer_numbers)) <= data.Width, name='capacity constraint')

    sub_model.setParam(GRB.Param.Logging, 1)
    sub_model.optimize()
    reduced_cost = 1 - sub_model.objVal

    new_pattern = np.array(sub_model.getAttr(GRB.Attr.X, sub_model.getVars()), dtype=np.int32)

    return reduced_cost, new_pattern


def solve_CSP_with_CG_embed_in_diving_heuristic(data, pattern_matrix, residual_demand):
    num_patterns = np.shape(pattern_matrix)[1]

    # create RMP
    RMP_model = grbpy.Model("Restricted Master Problem")

    # variables of RMP
    quantity_pattern = RMP_model.addVars(num_patterns, obj=1, vtype=GRB.CONTINUOUS)

    # constraints of RMP (demand satisfaction)
    RMP_model.addConstrs((grbpy.quicksum(pattern_matrix[i][j] * quantity_pattern[j] for j in range(num_patterns)) >=
                          residual_demand[i] for i in range(data.num_types)), name='demand satisfaction')

    RMP_model.setParam(GRB.Param.Logging, 1)
    RMP_model.setObjSense(GRB.MINIMIZE)

    # main steps
    while True:
        # solve RMP
        RMP_model.optimize()

        price_dual = RMP_model.getAttr(GRB.Attr.Pi, RMP_model.getConstrs())

        reduced_cost, new_pattern = solve_sub_problem_embed_in_diving_heuristic(data, price_dual)

        if np.abs(reduced_cost) <= TOL or reduced_cost >= 0:
            break

        # set the new pattern as a new column in the coefficient matrix
        new_column = grbpy.Column(new_pattern, RMP_model.getConstrs())

        # add the new variable
        quantity_pattern[num_patterns] = RMP_model.addVar(obj=1.0, vtype=GRB.CONTINUOUS, column=new_column)
        pattern_matrix = np.c_[pattern_matrix, new_pattern]
        num_patterns += 1

    # record and print solution
    quantity_sol = np.zeros(num_patterns)
    for j in range(num_patterns):
        quantity_sol[j] = quantity_pattern[j].x

    return pattern_matrix, quantity_sol


def perform_diving_heuristic(rel_sol, data, pattern):
    # initialization
    total_consumption = 0
    residual_demand = data.demand
    rounded_sol = np.array([])
    num_new_patterns = len(rel_sol)
    # main steps
    while residual_demand.sum() > 0:
        num_patterns = len(rel_sol)
        rounded_sol = np.pad(rounded_sol, (0, num_new_patterns), 'constant')  # expand array
        num_rounded = 0
        for j in range(num_patterns):
            # round down
            if rel_sol[j] - np.floor(rel_sol[j]) <= DOWN_THRESHOLD:
                rounded_sol[j] += np.floor(rel_sol[j])
                num_rounded += 1
            # round up
            elif rel_sol[j] - np.floor(rel_sol[j]) >= UP_THRESHOLD:
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
        sat_matrix = np.zeros((len(index), data.num_types), dtype=int)
        for i in range(len(index)):
            sat_matrix[i] = pattern.T[index][i] * rounded_sol[index][i]
        residual_demand = data.demand - sat_matrix.sum(axis=0)
        residual_demand = np.maximum(0, residual_demand)

        if residual_demand.sum() == 0:
            break

        pattern, rel_sol = solve_CSP_with_CG_embed_in_diving_heuristic(data, pattern, residual_demand)
        num_new_patterns = len(rel_sol) - num_patterns

    return rounded_sol, pattern
