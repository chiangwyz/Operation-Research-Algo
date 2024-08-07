"""
author: Jiang Dapei
"""

import numpy as np
from read_data import *
from solution import *
from branching import *
import heapq
import time

from logger_config import logger
from rounding import perform_simple_rounding, perform_diving_heuristic


if __name__ == "__main__":
    logger.info("Starting Branch and Price Algorithm!")
    # 读取数据
    input_data = "../branch and price/data.txt"
    data = Data()
    data.read_data(input_data)
    data.print_data()

    t1 = time.time()
    bb_tree = []
    solution = Solution()

    # RMP is a linear programming
    rmp_model = grbpy.Model("Restricted Master Problem")

    pattern = np.zeros((data.Customer_numbers, data.Customer_numbers), dtype=np.int32)
    for i in range(data.Customer_numbers):
        pattern[i][i] = np.floor(data.Width / data.Customer_demand_sizes[i])
        # logger.info("pattern({},{}) = {}".format(i, i, pattern[i][i]))

    logger.info("initial pattern =\n%s", pattern)

    y = rmp_model.addVars(data.Customer_numbers, lb=0.0, ub=GRB.INFINITY, obj=1.0, vtype=GRB.CONTINUOUS, name="y")

    rmp_model.addConstrs(
        (grbpy.quicksum(pattern[i][j] * y[j] for j in range(data.Customer_numbers)) >= data.Customer_demands[i]
         for i in range(data.Customer_numbers)),
        name='demand_satisfaction')

    rmp_model.setParam(GRB.Param.OutputFlag, 1)
    rmp_model.setAttr(GRB.Attr.ModelSense, GRB.MINIMIZE)
    rmp_model.write("master problem root node.lp")

    logger.info("finished root node model build!")

    # root node
    temp_node = Node()
    temp_node.model = rmp_model
    temp_node.pattern = pattern
    heapq.heappush(bb_tree, temp_node)

    # solve root node
    bb_tree[0].model, bb_tree[0].pattern = solve_CSP_with_CG(data, bb_tree[0].model, bb_tree[0].model.getVars(), bb_tree[0].pattern, bb_tree[0].branching_indices)
    bb_tree[0].obj_value = bb_tree[0].model.ObjVal
    bb_tree[0].pattern_quantity = np.zeros(len(bb_tree[0].model.getVars()))
    for j in range(len(bb_tree[0].pattern_quantity)):
        bb_tree[0].pattern_quantity[j] = bb_tree[0].model.getVars()[j].x

    logger.info("finished root node solve!")
    logger.info("bb_tree[0] node obj_value = %s", bb_tree[0].model.ObjVal)
    logger.info("bb_tree[0].pattern =\n%s", bb_tree[0].pattern)
    logger.info("bb_tree[0].pattern_quantity =\n%s", bb_tree[0].pattern_quantity)

    num_iterations = 1
    while True:
        logger.info("iterations = %s, obj of relaxation = %s", num_iterations, bb_tree[0].obj_value)
        for j in range(len(bb_tree[0].pattern_quantity)):
            logger.info("pattern %s: %s with quantity %s", j, bb_tree[0].pattern.T[j], bb_tree[0].pattern_quantity[j])

        if bb_tree[0].obj_value > solution.ub:
            # cut off by bound
            logger.info("cut off by bound")
            heapq.heappop(bb_tree)
            continue

        # check integrity
        LP_opt_int = False
        fraction = np.abs(np.round(bb_tree[0].pattern_quantity) - bb_tree[0].pattern_quantity)
        # case of integral solution
        if fraction.sum() <= TOL:
            logger.info("find an integral solution!")
            LP_opt_int = True
            # update ub and incumbent
            if bb_tree[0].obj_value < solution.ub:
                solution.ub = bb_tree[0].obj_value
                solution.pattern = bb_tree[0].pattern
                solution.total_consumption = bb_tree[0].obj_value
                solution.incumbent = bb_tree[0].pattern_quantity
                logger.info("solution incumbent = %s", solution.incumbent)

        # case of fractional solution
        else:
            # perform rounding heuristic (store in solution.incumbent)
            if ROUNDING_OPT == 0:
                logger.info("perform simple rounding!")
                rounded_sol = perform_simple_rounding(bb_tree[0].pattern_quantity)
                if np.sum(rounded_sol) < solution.ub:
                    solution.ub = np.sum(rounded_sol)
                    solution.pattern = bb_tree[0].pattern
                    solution.total_consumption = np.sum(rounded_sol)
                    solution.incumbent = rounded_sol

            # perform diving heuristics
            elif ROUNDING_OPT == 1:
                logger.info("perform diving heuristic!")
                rounded_sol, pattern_r = perform_diving_heuristic(bb_tree[0].pattern_quantity, data, bb_tree[0].pattern)
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
            if temp_node.model.Status != GRB.INFEASIBLE:  # feasible solution
                temp_node.obj_value = temp_node.model.ObjVal
                temp_node.pattern_quantity = np.zeros(len(temp_node.model.getVars()))
                for j in range(len(temp_node.pattern_quantity)):
                    temp_node.pattern_quantity[j] = temp_node.model.getVars()[j].X
                heapq.heappush(bb_tree, temp_node)

            # add right branch
            temp_node = add_right_branch(data, parent_node, k)
            if temp_node.model.Status != GRB.INFEASIBLE:  # feasible solution
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
            logger.info(f"iterations:{num_iterations:^10} current lb:{np.round(solution.lb, 4):^10} current int lb:{solution.int_lb:^10} current ub:{solution.ub:^10} gap:{np.round(solution.gap * 100, 4):>10}%")

        # termination criteria
        if solution.gap <= GAP_TOL or len(bb_tree) == 0:
            break

        num_iterations += 1

    t2 = time.time()
    # print incumbent solution
    logger.info(f"branch and price terminates in {t2 - t1} sec ({num_iterations} iterations) with gap of {solution.gap * 100} %.")
    logger.info("===incumbent solution===")
    logger.info("objective value: %s", solution.total_consumption)
    for j in range(len(solution.incumbent)):
        if solution.incumbent[j] > 0:
            logger.info(f"pattern {j}:  {solution.pattern.T[j]} with quantity: {solution.incumbent[j]}")

    logger.info("End Branch and Price Algorithm!")