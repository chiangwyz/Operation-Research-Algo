import numpy as np
import coptpy as cp
from coptpy import COPT
from algorithm_parameters import *


down_threshold = 0.2
up_threshold = 0.8


def perform_simple_rounding(rel_sol):
    # 对给定的解进行简单的向上取整
    rounded_sol = np.ceil(rel_sol)

    return rounded_sol


def solve_sub_problem_embed_in_diving_heuristic(data, price_dual):
    # initialization of SP

    env = cp.Envr()
    sub_model = env.createModel("sub problem")

    # variables of subproblem
    quantity = sub_model.addVars(data.customer_demand_numbers, vtype=COPT.INTEGER)

    # adding objective function
    sub_model.setObjective(cp.quicksum(price_dual[i] * quantity[i] for i in range(data.customer_demand_numbers)), COPT.MAXIMIZE)

    # constraint of subproblem
    sub_model.addConstr(cp.quicksum(quantity[i]*data.customer_demand_sizes[i] for i in range(data.customer_demand_numbers)) <= data.Width, name='capacity constraint')

    # solve Subproblem
    sub_model.setParam(COPT.Param.Logging, 1)
    sub_model.solve()
    reduced_cost = 1-sub_model.objval

    # get the new pattern
    new_pattern = np.array(sub_model.getAttr("Cols"), dtype=np.int32)

    return reduced_cost, new_pattern


def solve_CSP_with_CG_embed_in_diving_heuristic(data, pattern_matrix, residual_demand):
    # initialize
    num_patterns = np.shape(pattern_matrix)[1]

    # create RMP
    env = cp.Envr()
    RMP_model = env.createModel("Restricted problem")

    # variables of RMP
    quantity_pattern = RMP_model.addVars(num_patterns, obj=1, vtype=COPT.CONTINUOUS)

    # constraints of RMP (demand satisfaction)
    RMP_model.addConstrs((cp.quicksum(pattern_matrix[i][j] * quantity_pattern[j] for j in range(num_patterns)) >=
                          residual_demand[i] for i in range(data.num_types)), nameprefix='demand satisfaction')

    RMP_model.setParam(COPT.Param.Logging, 1)
    RMP_model.setObjSense(COPT.MINIMIZE)

    # main steps
    while True:
        # solve RMP
        RMP_model.solve()

        # get the dual variable value
        price_dual = RMP_model.getInfo(COPT.Info.Dual, RMP_model.getConstrs())

        # solve pricing subproblem
        reduced_cost, new_pattern = solve_sub_problem_embed_in_diving_heuristic(data, price_dual)

        # check termination condition
        if np.abs(reduced_cost) <= TOL or reduced_cost >= 0:
            break

        # set the new pattern as a new column in the coefficient matrix
        new_column = cp.Column(RMP_model.getConstrs(), new_pattern)

        # add the new variable
        quantity_pattern[num_patterns] = RMP_model.addVar(obj=1.0, vtype=COPT.CONTINUOUS, column=new_column)
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
