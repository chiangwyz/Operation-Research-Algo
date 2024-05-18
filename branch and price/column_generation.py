import numpy as np
import gurobipy as grbpy
from gurobipy import GRB
from math import sqrt
from logger_config import logger

from read_data import Data
from algorithm_parameters import *


def solve_sub_problem(data, shadow_price, dual_correction, branching_index: list, pattern_old):
    logger.info("solve_sub_problem!")
    new_pattern = []

    num_types = len(shadow_price)

    # 构造子问题
    sub_model = grbpy.Model("sub problem")

    var_a = grbpy.tupledict()
    for i in range(data.Customer_numbers):
        var_a[i] = sub_model.addVar(lb=0, ub=GRB.INFINITY, vtype=GRB.INTEGER, name='a({})'.format(i))
    # var_a = sub_model.addVars(num_types, vtype=GRB.INTEGER)

    # 背包约束
    sub_model.addConstr(
        grbpy.quicksum(var_a[i] * data.Customer_demand_sizes[i] for i in range(num_types)) <= data.Width,
        name="width constraint")

    # Update objective function of SUB model
    sub_model.setObjective(1 - grbpy.quicksum(shadow_price[i] * var_a[i] for i in range(num_types)), GRB.MINIMIZE)

    sub_model.setParam(GRB.Param.OutputFlag, 1)
    sub_model.setParam(GRB.Param.PoolSearchMode, 2)
    sub_model.setParam(GRB.Param.PoolSolutions, POOL_SIZE)

    sub_model.update()
    sub_model.optimize()
    sub_model.write("sub_problem.lp")

    output = []
    for var in sub_model.getVars():
        output.append(f"{var.VarName} = {var.X}")
    logger.info(", ".join(output))

    # 获取子问题求解状态
    logger.info('sub_model status: %s', GUROBI_Status_Map[sub_model.Status])
    logger.info('sub_model.SolCount: %s', sub_model.SolCount)

    reduced_cost = 0
    for i in range(sub_model.SolCount):
        # 需要设置获取的顺序
        sub_model.setParam(GRB.Param.SolutionNumber, i)
        candidate_pattern = np.array(sub_model.getAttr(GRB.Attr.Xn, sub_model.getVars()), dtype=np.int32)
        reduced_cost = sub_model.PoolObjVal

        logger.info("No %s. best solution with objective value of %s", i, sub_model.PoolObjVal)
        logger.info("candidate pattern: %s", candidate_pattern)
        logger.info("reduced cost: %s", reduced_cost)

        if reduced_cost >= 0 or abs(reduced_cost) <= TOL:
            logger.info("no more profitable pattern available")
            break

        # check if the pattern is already generated
        identical_pattern_index = np.where(np.all(pattern_old.T == candidate_pattern, axis=1))[0]
        if len(identical_pattern_index) > 0:  # candidate pattern is already generated
            logger.info("candidate pattern is already generated!!!")
            logger.info("identical with pattern %s", identical_pattern_index[0])
            correction_indices = np.where(identical_pattern_index[0] == branching_index)[0]
            for j in correction_indices:
                reduced_cost -= dual_correction[j]
            logger.info("corrected reduced cost: %s", reduced_cost)
        else:  # candidate pattern is new
            if reduced_cost < 0 and abs(reduced_cost) > TOL:
                new_pattern.append(candidate_pattern)
                logger.info("The pattern is added.")

    logger.info("End of solving sub problem!")
    return reduced_cost, new_pattern


def solve_CSP_with_CG(data: Data, RMP_model: grbpy.Model, quantity_pattern, pattern: np.ndarray,
                      branching_index: list):
    # 只做列生成并求解
    num_types = data.Customer_numbers

    RMP_model.update()
    RMP_model.optimize()  # 求解LP
    # logger.info("RMP_model status: %s", RMP_model.status)
    logger.info("RMP_model status: %s", GUROBI_Status_Map[RMP_model.status])

    if RMP_model.status != GRB.INFEASIBLE:
        # 获取约束的影子价格
        dual_list = RMP_model.getAttr(GRB.Attr.Pi, RMP_model.getConstrs())
        shadow_price = dual_list[0:num_types]  # 获取前 num_types 个约束的对偶值
        dual_correction = dual_list[num_types:len(dual_list)]  # 获取 添加的分支约束 的对偶值

        logger.info("shadow price: %s", shadow_price)
        logger.info("dual correction: %s", dual_correction)

        while True:
            # solve pricing sub-problem
            reduced_cost, new_pattern = solve_sub_problem(data, shadow_price, dual_correction, branching_index, pattern)
            # check termination condition
            if len(new_pattern) == 0:
                logger.info("cannot found new pattern")
                break

            logger.info("new pattern:\n%s", np.array(new_pattern).T)
            for p in new_pattern:
                logger.info("add new pattern: %s", p)

                # set the new pattern as a new column in the coefficient matrix
                new_column = grbpy.Column(p, RMP_model.getConstrs()[0:num_types])
                # add the new variable
                quantity_pattern.append(
                    RMP_model.addVar(obj=1.0, vtype=GRB.CONTINUOUS, column=new_column, name="add pattern" + str(p)))
                pattern = np.c_[pattern, p]

            # solve RMP
            RMP_model.update()
            RMP_model.optimize()

            # get dual
            dual_list = RMP_model.getAttr(GRB.Attr.Pi, RMP_model.getConstrs())
            shadow_price = dual_list[0:num_types]
            dual_correction = dual_list[num_types:len(dual_list)]

    return RMP_model, pattern
