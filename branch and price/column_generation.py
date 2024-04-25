import numpy as np
import coptpy as cp
from coptpy import COPT
from math import sqrt

from read_data import Data
from algorithm_parameters import *

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


def solve_sub_problem(data, price_dual, dual_correction, branching_index, pattern_a):
    reduced_cost = 0

    new_pattern = []

    # 构造子问题
    env = cp.Envr()
    sub_model = env.createModel("sub problem")

    var_y = cp.tupledict()
    for i in range(data.customer_demand_numbers):
        var_y[i] = sub_model.addVar(lb=0, ub=COPT.INFINITY, vtype=COPT.INTEGER, name='y_' + str(i))

    # 背包约束
    sub_model.addConstr(var_y.prod(data.customer_demand_sizes), COPT.LESS_EQUAL, data.Width, "width_limit")

    # Update objective function of SUB model
    sub_model.setObjective(1 - var_y.prod(price_dual), COPT.MINIMIZE)

    sub_model.setParam(COPT.Param.Logging, 1)
    sub_model.setParam(COPT.Param.PoolSols, pool_size)
    solution_pool = sub_model.getPoolObjVal(pool_size)

    sub_model.solve()

    pattern = []
    print("stored solutions: {}".format(len(COPT.Info.PoolSols)))
    # check each found solutions
    for i in range(sub_model.getInfo(COPT.Info.PoolSols)):
        # SP_model.Params.SolutionNumber = i
        candidate_pattern = np.array(sub_model.getAttr("Cols"), dtype=np.int32)
        print(f"{i + 1}. best solution with objective value of {sub_model.getPoolObjVal(i)}")
        print(f"candidate pattern: {candidate_pattern}")
        reduced_cost = sub_model.getPoolObjVal(i)
        print(f"reduced cost: {reduced_cost}")
        if reduced_cost >= 0 or abs(reduced_cost) <= TOL:
            print("no more profitable pattern available")
            break
        # check if the pattern is already generated
        identical_pattern_index = np.where(np.all(pattern_a.T == candidate_pattern, axis=1))[0]
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


def solve_CSP_with_CG(data: Data, RMP_model: cp.Model, quantity_pattern, pattern, branching_index):
    num_types = data.customer_demand_numbers
    # main steps

    RMP_model.solveLP()  # 求解LP
    if RMP_model.status != COPT.INFEASIBLE:
        # Get the dual values of constraints
        dual_list = RMP_model.getInfo(COPT.Info.Dual, RMP_model.getConstrs())
        price_dual = dual_list[0:num_types]
        dual_correction = dual_list[num_types:len(dual_list)]
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


