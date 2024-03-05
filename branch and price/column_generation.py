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


def solve_CSP_with_CG(parameter, RMP_model, quantity_pattern, pattern, branching_index):
    num_types = len(parameter.demand)
    # main steps
    # RMP_model.update()
    # RMP_model.write('RMP.lp')
    RMP_model.solveLP()
    if RMP_model.status != COPT.INFEASIBLE:
        # get the dual variable value
        # Get the dual values of constraints
        dual_list = RMP_model.getInfo(COPT.Info.Dual, RMP_model.getConstrs())
        price_dual = dual_list[0:num_types]
        dual_correction = dual_list[num_types:len(dual_list)]
        while True:
            # solve pricing sub-problem
            reduced_cost, new_pattern = solve_sub_problem(parameter, price_dual, dual_correction, branching_index,
                                                         pattern)
            # check termination condition
            if len(new_pattern) == 0:
                break
            for p in new_pattern:
                # set the new pattern as a new column in the coefficient matrix
                new_column = cp.Column(RMP_model.getConstrs()[0:num_types], p)
                # add the new variable
                quantity_pattern.append(RMP_model.addVar(obj=1.0, vtype=COPT.CONTINUOUS, column=new_column, name="add pattern" + str(p)))
                pattern = np.c_[pattern, p]
            # solve RMP
            RMP_model.solveLP()
            # get dual
            dual_list = RMP_model.getInfo(COPT.Info.Dual, RMP_model.getConstrs())
            price_dual = dual_list[0:num_types]
            dual_correction = dual_list[num_types:len(dual_list)]

    return RMP_model, pattern


def solve_sub_problem(parameter, RMP_model, quantity_pattern, pattern, branching_index):
    num_types = len(parameter.demand)

    reduced_cost = []

    new_pattern = []

    return reduced_cost, new_pattern
