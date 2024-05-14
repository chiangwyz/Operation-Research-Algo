import numpy as np
import gurobipy as grbpy
from gurobipy import GRB
from math import sqrt
from logger_config import logger

from read_data import Data
from algorithm_parameters import *



def solve_sub_problem(data, price_dual, dual_correction, branching_index: list, pattern_old):
    new_pattern = []

    num_types = len(price_dual)

    # 构造子问题
    sub_model = grbpy.Model("sub problem")

    # var_a = grbpy.tupledict()
    # for i in range(data.Customer_numbers):
    #     var_a[i] = sub_model.addVar(lb=0, ub=GRB.INFINITY, vtype=GRB.INTEGER, name='a({})'.format(i))
    var_a = sub_model.addVars(num_types, vtype=GRB.INTEGER)

    # 背包约束
    # sub_model.addConstr(var_a.prod(data.Customer_demand_sizes), COPT.LESS_EQUAL, data.Width, "width_limit")
    sub_model.addConstr(grbpy.quicksum(var_a[i] * data.Customer_demand_sizes[i] for i in range(num_types)) <= data.Width, name="width constraint")

    # Update objective function of SUB model
    sub_model.setObjective(1 - grbpy.quicksum(price_dual[i] * var_a[i] for i in range(num_types)), GRB.MINIMIZE)

    sub_model.setParam(GRB.Param.OutputFlag, 1)
    sub_model.setParam(GRB.Param.PoolSearchMode, 2)
    sub_model.setParam(GRB.Param.PoolSolutions, POOL_SIZE)

    sub_model.optimize()
    sub_model.write("sub_problem.lp")

    for var in sub_model.getVars():
        logger.info("%s = %s", var.VarName, var.X)

    # 获取子问题求解状态
    logger.info('sub_model.status: %s', GUROBI_Status_Map[sub_model.Status])

    reduced_cost = 0
    pattern = []
    for i in range(sub_model.SolCount):
        candidate_pattern = np.array(sub_model.getAttr(GRB.Attr.Xn, sub_model.getVars()), dtype=np.int32)
        reduced_cost = sub_model.PoolObjVal

        logger.info("%s. best solution with objective value of %s", i+i, sub_model.PoolObjVal)
        logger.info("candidate pattern: %s", candidate_pattern)
        logger.info("reduced_cost: %s", reduced_cost)

        if reduced_cost >= 0 or abs(reduced_cost) <= TOL:
            print("no more profitable pattern available")
            break

        # check if the pattern is already generated
        identical_pattern_index = np.where(np.all(pattern_old.T == candidate_pattern, axis=1))[0]
        if len(identical_pattern_index) > 0:  # candidate pattern is already generated
            print("!!!candidate pattern is already generated!!!")
            print(f"identical with pattern {identical_pattern_index[0]}")
            correction_indices = np.where(identical_pattern_index[0] == branching_index)[0]
            for j in correction_indices:
                reduced_cost -= dual_correction[j]
            print(f"corrected reduced cost: {reduced_cost}")
        else:  # candidate pattern is new
            if reduced_cost < 0 and abs(reduced_cost) > TOL:
                pattern.append(candidate_pattern)
                print("This pattern is added.")

    return reduced_cost, new_pattern


def solve_CSP_with_CG(data: Data, RMP_model: grbpy.Model, quantity_pattern: np.ndarray, pattern: np.ndarray, branching_index: list):
    # 只做列生成并求解。
    num_types = data.Customer_numbers

    RMP_model.optimize()  # 求解LP
    logger.info("RMP_model status: %s", GUROBI_Status_Map[RMP_model.status])

    if RMP_model.status != GRB.INFEASIBLE:
        # Get the dual values of constraints
        dual_list = RMP_model.getAttr(GRB.Attr.Pi, RMP_model.getConstrs())
        price_dual = dual_list[0:num_types]  # 获取前 num_types 个约束的对偶值
        dual_correction = dual_list[num_types:len(dual_list)]  # 获取 添加的分支约束的对偶值

        logger.info("dual dual: %s", price_dual)
        logger.info("dual correction: %s", dual_correction)

        while True:
            # solve pricing sub-problem
            reduced_cost, new_pattern = solve_sub_problem(data, price_dual, dual_correction, branching_index, pattern)
            # check termination condition
            if len(new_pattern) == 0:
                break
            for p in new_pattern:
                # set the new pattern as a new column in the coefficient matrix
                new_column = grbpy.Column(p, RMP_model.getConstrs()[0:num_types])
                # add the new variable
                quantity_pattern.append(
                    RMP_model.addVar(obj=1.0, vtype=GRB.CONTINUOUS, column=new_column, name="add pattern" + str(p)))
                pattern = np.c_[pattern, p]
            # solve RMP
            RMP_model.optimize()

            # get dual
            dual_list = RMP_model.getAttr(GRB.Attr.Pi, RMP_model.getConstrs())
            price_dual = dual_list[0:num_types]
            dual_correction = dual_list[num_types:len(dual_list)]

    return RMP_model, pattern
