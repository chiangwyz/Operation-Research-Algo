import numpy as np
import coptpy as cp
from coptpy import COPT
from math import sqrt

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


def solve_CSP_with_CG(data, RMP_model, quantity_pattern, pattern, branching_index):
    num_types = data.customer_demand_numbers
    # main steps
    # RMP_model.update()
    # RMP_model.write('RMP.lp')
    RMP_model.solveLP()  # 求解LP
    if RMP_model.status != COPT.INFEASIBLE:
        # get the dual variable value
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


def solve_sub_problem(data, price_dual, dual_correction, branching_index, pattern):
    reduced_cost = []

    new_pattern = []


    # 构造子问题
    env = cp.Envr()
    sub_model = env.createModel("sub problem")

    var_y = cp.tupledict()
    for i in range(data.customer_demand_numbers):
        var_y[i] = sub_model.addVar(lb=0, ub=COPT.INFINITY, vtype=COPT.CONTINUOUS, name='y_' + str(i))

    # 背包约束
    sub_model.addConstr(var_y.prod(pattern), COPT.LESS_EQUAL, data.Width, "width_limit")

    # Update objective function of SUB model
    sub_model.setObjective(1 - var_y.prod(price_dual), COPT.MINIMIZE)

    sub_model.solve()

    for key in var_y.keys():
        print('y[{}] = {}'.format(key, var_y[key].x))

    reduced_cost = sub_model.objval

    return reduced_cost, new_pattern
