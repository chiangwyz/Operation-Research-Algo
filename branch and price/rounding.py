import numpy as np
import gurobipy as grbpy
from gurobipy import GRB
from algorithm_parameters import *
from logger_config import logger


def perform_simple_rounding(rel_sol):
    logger.info("start Performing simple rounding")
    # 对给定的解进行简单的向上取整
    rounded_sol = np.ceil(rel_sol)

    logger.info("Rounded sol: %s", rounded_sol)
    logger.info("Ended performing simple rounding")

    return rounded_sol


def solve_sub_problem_embed_in_diving_heuristic(data, price_dual):

    logger.info('Solving sub problem embed in diving heuristic')
    # initialization of SP

    sub_model = grbpy.Model("sub problem")

    quantity = sub_model.addVars(data.Customer_numbers, vtype=GRB.INTEGER)

    sub_model.setObjective(grbpy.quicksum(price_dual[i] * quantity[i] for i in range(data.Customer_numbers)), GRB.MAXIMIZE)

    sub_model.addConstr(grbpy.quicksum(quantity[i]*data.Customer_demand_sizes[i] for i in range(data.Customer_numbers)) <= data.Width, name='capacity_constraint')

    sub_model.setParam(GRB.Param.OutputFlag, 1)
    sub_model.optimize()
    reduced_cost = 1 - sub_model.objVal

    new_pattern = np.array(sub_model.getAttr(GRB.Attr.X, sub_model.getVars()), dtype=np.int32)

    logger.info('Ended solving sub problem embed in diving heuristic')

    return reduced_cost, new_pattern


def solve_CSP_with_CG_embed_in_diving_heuristic(data, pattern_matrix, residual_demand):
    logger.info("Solving CSP with CG_embed in diving heuristic!")

    num_patterns = np.shape(pattern_matrix)[1]

    # create RMP
    rmp_model = grbpy.Model("Restricted Master Problem")

    # variables of RMP
    quantity_pattern = rmp_model.addVars(num_patterns, obj=1, vtype=GRB.CONTINUOUS)

    # constraints of RMP (demand satisfaction)
    rmp_model.addConstrs((grbpy.quicksum(pattern_matrix[i][j] * quantity_pattern[j] for j in range(num_patterns)) >=
                          residual_demand[i] for i in range(data.Customer_numbers)), name='demand_satisfaction')

    rmp_model.setParam(GRB.Param.OutputFlag, 1)
    rmp_model.setAttr(GRB.Attr.ModelSense, GRB.MINIMIZE)

    # main steps
    while True:
        # solve RMP
        rmp_model.optimize()

        price_dual = rmp_model.getAttr(GRB.Attr.Pi, rmp_model.getConstrs())

        reduced_cost, new_pattern = solve_sub_problem_embed_in_diving_heuristic(data, price_dual)

        if np.abs(reduced_cost) <= TOL or reduced_cost >= 0:
            break

        # set the new pattern as a new column in the coefficient matrix
        new_column = grbpy.Column(new_pattern, rmp_model.getConstrs())

        # add the new variable
        quantity_pattern[num_patterns] = rmp_model.addVar(obj=1.0, vtype=GRB.CONTINUOUS, column=new_column)
        pattern_matrix = np.c_[pattern_matrix, new_pattern]
        num_patterns += 1

    # record and print solution
    quantity_sol = np.zeros(num_patterns)
    for j in range(num_patterns):
        quantity_sol[j] = quantity_pattern[j].x

    logger.info("Ended Solve CSP with CG_embed in diving heuristic!")

    return pattern_matrix, quantity_sol


def perform_diving_heuristic(relative_solution, data, pattern):
    logger.info("Performing diving heuristic!")
    logger.info("rel_sol: %s", relative_solution)
    logger.info("pattern: %s", pattern)

    # initialization
    total_consumption = 0
    residual_demand = data.Customer_demands
    rounded_sol = np.array([])
    num_new_patterns = len(relative_solution)
    # main steps
    while residual_demand.sum() > 0:

        num_patterns = len(relative_solution)
        rounded_sol = np.pad(rounded_sol, (0, num_new_patterns), 'constant')  # expand array

        # 先做一些变量的固定
        num_rounded = 0
        for j in range(num_patterns):
            # round down
            if relative_solution[j] - np.floor(relative_solution[j]) <= DOWN_THRESHOLD:
                rounded_sol[j] += np.floor(relative_solution[j])
                num_rounded += 1
            # round up
            elif relative_solution[j] - np.floor(relative_solution[j]) >= UP_THRESHOLD:
                rounded_sol[j] += np.ceil(relative_solution[j])
                num_rounded += 1

        # none elements rounded
        if num_rounded == 0:
            # determine the least fractional element to round up/down
            fraction = np.abs(np.round(relative_solution) - relative_solution)
            fractional_index = np.array([k for k in range(num_patterns) if fraction[k] > TOL])
            k = fractional_index[np.argmin(fraction[fractional_index])]
            rounded_sol[k] += np.round(relative_solution[k])

        # check if the residual problem stays unchanged
        if rounded_sol.sum() == total_consumption:
            # choose the least fractional element to round up, so that the residual problem becomes smaller
            fraction = np.ceil(relative_solution) - relative_solution
            fractional_index = np.array([k for k in range(num_patterns) if fraction[k] > TOL])
            k = fractional_index[np.argmin(fraction[fractional_index])]
            rounded_sol[k] += np.ceil(relative_solution[k])

        # update total consumption and residual demand
        total_consumption = rounded_sol.sum()
        index = [i for i in range(num_patterns) if rounded_sol[i] > 0]
        sat_matrix = np.zeros((len(index), data.Customer_numbers), dtype=int)
        for i in range(len(index)):
            sat_matrix[i] = pattern.T[index][i] * rounded_sol[index][i]
        residual_demand = data.Customer_demands - sat_matrix.sum(axis=0)
        residual_demand = np.maximum(0, residual_demand)

        if residual_demand.sum() == 0:
            break

        pattern, relative_solution = solve_CSP_with_CG_embed_in_diving_heuristic(data, pattern, residual_demand)
        num_new_patterns = len(relative_solution) - num_patterns

    logger.info("Ended performing diving heuristic!")

    return rounded_sol, pattern
