"""
author: Jiang Dapei
"""

import numpy as np
from read_data import *
from solution import *
from branching import *
import heapq
import time

import color_logging
from rounding import perform_simple_rounding, perform_diving_heuristic


if __name__ == "__main__":
    # read in date
    input_data = "../branch and price/data.txt"
    data = Data()
    data.read_data(input_data)
    data.print_data()

    # initialize
    t1 = time.time()
    bb_tree = []
    solution = Solution()

    env = cp.Envr()
    rmp_model = env.createModel("restricted master problem")

    pattern = np.zeros((data.Customer_numbers, data.Customer_numbers), dtype=np.int32)
    for i in range(data.Customer_numbers):
        pattern[i][i] = np.floor(data.Width / data.Customer_demand_sizes[i])
        # logger.info("pattern({},{}) = {}".format(i, i, pattern[i][i]))

    logger.info("pattern=\n {}".format(pattern))

    # variables of RMP
    y = rmp_model.addVars(data.Customer_numbers, lb=0.0, ub=COPT.INFINITY, obj=1, vtype=COPT.CONTINUOUS, nameprefix="y")
    # constraints of RMP
    rmp_model.addConstrs(
        (cp.quicksum(pattern[i][j] * y[j] for j in range(data.Customer_numbers)) >= data.Customer_demands[i]
         for i in range(data.Customer_numbers)), nameprefix='demand satisfaction')

    # set parameters
    rmp_model.setParam(COPT.Param.Logging, 1)
    rmp_model.setObjSense(COPT.MINIMIZE)
    rmp_model.writeLp("master problem.lp")

    # root node
    temp_node = Node()
    temp_node.model = rmp_model
    temp_node.pattern = pattern
    heapq.heappush(bb_tree, temp_node)

    # solve root noode
    bb_tree[0].model, bb_tree[0].pattern = solve_CSP_with_CG(data, bb_tree[0].model, bb_tree[0].model.getVars(), bb_tree[0].pattern, bb_tree[0].branching_indices)
    bb_tree[0].obj_value = bb_tree[0].model.ObjVal
    bb_tree[0].pattern_quantity = np.zeros(len(bb_tree[0].model.getVars()))
    for j in range(len(bb_tree[0].pattern_quantity)):
        bb_tree[0].pattern_quantity[j] = bb_tree[0].model.getVars()[j].x

    print(f"{'Iteration':^10} {'LB':^10} {'LB_INT':^10} {'UB':^10} {'gap(%)':^10}")
    num_iterations = 1
    while True:
        if bb_tree[0].obj_value > solution.ub:
            # cut off by bound
            heapq.heappop(bb_tree)
            continue

        # check integrity
        LP_opt_int = False
        fraction = np.abs(np.round(bb_tree[0].pattern_quantity) - bb_tree[0].pattern_quantity)
        # case of integral solution
        if fraction.sum() <= TOL:
            LP_opt_int = True
            # update ub and incumbent
            if bb_tree[0].obj_value < solution.ub:
                solution.ub = bb_tree[0].obj_value
                solution.pattern = bb_tree[0].pattern
                solution.total_consumption = bb_tree[0].obj_value
                solution.incumbent = bb_tree[0].pattern_quantity

        # case of fractional solution
        else:
            # perform rounding heuristic (store in solution.incumbent)
            if rounding_opt == 0:
                rounded_sol = perform_simple_rounding(bb_tree[0].pattern_quantity)
                if np.sum(rounded_sol) < solution.ub:
                    solution.ub = np.sum(rounded_sol)
                    solution.pattern = bb_tree[0].pattern
                    solution.total_consumption = np.sum(rounded_sol)
                    solution.incumbent = rounded_sol

            elif rounding_opt == 1:
                rounded_sol, pattern_r = perform_diving_heuristic(bb_tree[0].pattern_quantity, parameter, bb_tree[0].pattern)
                if np.sum(rounded_sol) < solution.ub:
                    solution.ub = np.sum(rounded_sol)
                    solution.pattern = pattern_r
                    solution.total_consumption = np.sum(rounded_sol)
                    solution.incumbent = rounded_sol

            # identify the element to branch
            fractional_index = [k for k in range(len(fraction)) if fraction[k] > TOL]
            k = fractional_index[np.argmax(fraction[fractional_index])]
            # take the first node as parent node
            parent_node = heapq.heappop(bb_tree)
            # add left branch
            temp_node = add_left_branch(data, parent_node, k)
            if temp_node.model.Status != 3:  # feasible solution
                temp_node.obj_value = temp_node.model.ObjVal
                temp_node.pattern_quantity = np.zeros(len(temp_node.model.getVars()))
                for j in range(len(temp_node.pattern_quantity)):
                    temp_node.pattern_quantity[j] = temp_node.model.getVars()[j].X
                heapq.heappush(bb_tree, temp_node)

            # add right branch
            temp_node = add_right_branch(data, parent_node, k)
            if temp_node.model.Status != 3:  # feasible solution
                temp_node.obj_value = temp_node.model.ObjVal
                temp_node.pattern_quantity = np.zeros(len(temp_node.model.getVars()))
                for j in range(len(temp_node.pattern_quantity)):
                    temp_node.pattern_quantity[j] = temp_node.model.getVars()[j].X
                heapq.heappush(bb_tree, temp_node)

        # update LB
        if bb_tree[0].obj_value > solution.lb:
            solution.lb = bb_tree[0].obj_value
            # update integral LB
            if np.abs(np.round(solution.lb) - solution.lb) <= TOL and np.round(solution.lb) > solution.int_lb:
                solution.int_lb = np.round(solution.lb)
            elif np.abs(np.round(solution.lb) - solution.lb) > TOL and np.ceil(solution.lb) > solution.int_lb:
                solution.int_lb = np.ceil(solution.lb)

        if LP_opt_int:
            heapq.heappop(bb_tree)  # cutoff by optimality

        # info of current iteration
        # solution.gap = (solution.ub - solution.lb) / solution.lb
        solution.gap = (solution.ub - solution.int_lb) / solution.int_lb

        if num_iterations % 1 == 0:
            print(f"{num_iterations:^10} {np.round(solution.lb, 4):^10} {solution.int_lb:^10} {solution.ub:^10} {np.round(solution.gap * 100, 4):^10}")

        # termination criteria
        if solution.gap <= gap_tol or len(bb_tree) == 0:
            break

        num_iterations += 1

    t2 = time.time()
    # print incumbent solution
    print(f"branch and price terminates in {t2 - t1} sec ({num_iterations} iterations) with gap of {solution.gap * 100} %.")
    print("===incumbent solution===")
    print(f"objective value: {solution.total_consumption}")
    for j in range(len(solution.incumbent)):
        if solution.incumbent[j] > 0:
            print(f"pattern {j}:  {solution.pattern.T[j]} with quantity: {solution.incumbent[j]}")
