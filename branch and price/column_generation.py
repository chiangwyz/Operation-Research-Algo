import numpy as np
import coptpy as cp
from coptpy import COPT
from math import sqrt

from color_logging import LoggerFactory
from read_data import Data
from algorithm_parameters import *

logger = LoggerFactory.get_colored_logger()

# map: num --> model status
status_map = {
    0: "COPT.UNSTARTED",
    1: "COPT.OPTIMAL",
    2: "COPT.INFEASIBLE",
    3: "COPT.UNBOUNDED",
    4: "COPT.INF_OR_UNB",
    5: "COPT.NUMERICAL",
    6: "COPT.NODELIMIT",
    7: "COPT.TIMEOUT",
    8: "COPT.UNFINISHED",
    9: "COPT.INTERRUPTED"
}


def solve_sub_problem(data, price_dual, dual_correction, branching_index: list, pattern_old):
    new_pattern = []

    num_types = len(price_dual)

    # 构造子问题
    env = cp.Envr()
    sub_model = env.createModel("sub problem")

    var_a = cp.tupledict()
    for i in range(data.Customer_numbers):
        var_a[i] = sub_model.addVar(lb=0, ub=COPT.INFINITY, vtype=COPT.INTEGER, name='a({})'.format(i))
    # var_y = sub_model.addVars(num_types, vtype=COPT.INTEGER)

    # 背包约束
    # sub_model.addConstr(var_a.prod(data.Customer_demand_sizes), COPT.LESS_EQUAL, data.Width, "width_limit")
    sub_model.addConstr(cp.quicksum(var_a[i] * data.Customer_demand_sizes[i] for i in range(num_types)),
                        COPT.LESS_EQUAL, data.Width, name="width constraint")

    # Update objective function of SUB model
    sub_model.setObjective(1 - cp.quicksum(price_dual[i] * var_a[i] for i in range(num_types)), COPT.MINIMIZE)

    sub_model.setParam(COPT.Param.Logging, 1)
    # sub_model.setParam(COPT.Attr.PoolSols, pool_size)
    # solution_pool = sub_model.getPoolObjVal(pool_size)

    sub_model.solve()
    sub_model.writeLp("sub_problem.lp")

    for var in sub_model.getVars():
        logger.info("{} = {}".format(var.name, var.x))

    reduced_cost = 0

    logger.info('sub_model.hasmipsol: {}'.format(sub_model.hasmipsol))
    logger.info('sub_model.haslpsol: {}'.format(sub_model.haslpsol))
    logger.info('sub_model.status: {}'.format(sub_model.status))
    logger.info('sub_model.poolsols: {}'.format(sub_model.getAttr("poolsols")))
    logger.info('sub_model.PoolSols: {}'.format(sub_model.getAttr(COPT.Attr.PoolSols)))
    print("poolsols =", sub_model.getAttr('poolsols'))
    print("COPT.Attr.PoolSols =", sub_model.getAttr(COPT.Attr.PoolSols))

    pattern = []
    for i in range(sub_model.getAttr('PoolSols')):
        candidate_pattern = np.array(sub_model.getPoolSolution(i, var_a), dtype=np.int32)

        logger.info("{}. best solution with objective value of {}".format(i+1, sub_model.getPoolObjVal(i)))
        logger.info("candidate pattern: {}".format(candidate_pattern))
        reduced_cost = sub_model.getPoolObjVal(i)
        logger.info("reduced_cost: {}".format(reduced_cost))
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


def solve_CSP_with_CG(data: Data, RMP_model: cp.Model, quantity_pattern, pattern, branching_index: list):
    # 只做列生成并求解。
    num_types = data.Customer_numbers
    # main steps

    RMP_model.solveLP()  # 求解LP
    logger.info("RMP_model status: {}".format(status_map[RMP_model.status]))

    if RMP_model.status != COPT.INFEASIBLE:
        # Get the dual values of constraints
        dual_list = RMP_model.getInfo(COPT.Info.Dual, RMP_model.getConstrs())
        price_dual = dual_list[0:num_types]  # 获取前 num_types 个约束的对偶值
        dual_correction = dual_list[num_types:len(dual_list)]  # 获取 添加的分支约束的对偶值

        logger.info("dual dual: {}".format(price_dual))
        logger.info("dual correction: {}".format(dual_correction))

        while True:
            # solve pricing sub-problem
            reduced_cost, new_pattern = solve_sub_problem(data, price_dual, dual_correction, branching_index, pattern)
            # check termination condition
            if len(new_pattern) == 0:
                break
            for p in new_pattern:
                # set the new pattern as a new column in the coefficient matrix
                new_column = cp.Column(RMP_model.getConstrs()[0:num_types], p)
                # add the new variable
                quantity_pattern.append(
                    RMP_model.addVar(obj=1.0, vtype=COPT.CONTINUOUS, column=new_column, name="add pattern" + str(p)))
                pattern = np.c_[pattern, p]
            # solve RMP
            RMP_model.solveLP()
            # get dual
            dual_list = RMP_model.getInfo(COPT.Info.Pi, RMP_model.getConstrs())
            price_dual = dual_list[0:num_types]
            dual_correction = dual_list[num_types:len(dual_list)]

    return RMP_model, pattern
