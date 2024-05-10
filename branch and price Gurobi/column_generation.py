import gurobipy as gp
from gurobipy import GRB
import numpy as np
from program_parameter import *


def solve_subproblem(parameter, price_dual, dual_correction, branching_index, pattern_a):
    num_types = len(price_dual)

    # initialization of SP
    SP_model = gp.Model('Subproblem')

    # variables of subproblem
    quantity = SP_model.addVars(num_types, vtype=GRB.INTEGER)

    # adding objective function
    SP_model.setObjective(gp.quicksum(price_dual[i] * quantity[i] for i in range(num_types)), GRB.MAXIMIZE)

    # constraint of subproblem
    SP_model.addConstr(gp.quicksum(quantity[i] * parameter.specification[i] for i in range(num_types)) <= parameter.length_raw, name='capacity constraint')

    # set parameters
    SP_model.Params.OutputFlag = 0
    SP_model.Params.PoolSearchMode = 2  # find the n best solutions
    SP_model.Params.PoolSolutions = pool_size  # 15 solutions are expected

    SP_model.optimize()

    reduced_cost = 0
    pattern = []
    print(f"stored solutions: {SP_model.SolCount}")
    # check each found solutions
    for i in range(SP_model.SolCount):
        SP_model.Params.SolutionNumber = i
        candidate_pattern = np.array(SP_model.getAttr('Xn', SP_model.getVars()), dtype=np.int32)
        print(f"{i + 1}. best solution with objective value of {SP_model.PoolObjVal}")
        print(f"candidate pattern: {candidate_pattern}")
        reduced_cost = 1 - SP_model.PoolObjVal
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

    return reduced_cost, pattern


def solve_CSP_with_CG(parameter, RMP_model, quantity_pattern, pattern, branching_index):
    num_types = len(parameter.demand)
    # main steps
    # RMP_model.update()
    # RMP_model.write('RMP.lp')
    RMP_model.optimize()
    if RMP_model.Status != 3:
        # get the dual variable value
        dual_list = RMP_model.getAttr(GRB.Attr.Pi, RMP_model.getConstrs())
        price_dual = dual_list[0:num_types]
        dual_correction = dual_list[num_types:len(dual_list)]
        print(f"price dual: {price_dual}")
        print(f"dual correction: {dual_correction}")
        while True:
            # solve pricing subproblem
            reduced_cost, new_pattern = solve_subproblem(parameter, price_dual, dual_correction, branching_index, pattern)
            # check termination condition
            if len(new_pattern) == 0:
                break
            for p in new_pattern:
                # set the new pattern as a new column in the coefficient matrix
                new_column = gp.Column(p, RMP_model.getConstrs()[0:num_types])
                # add the new variable
                quantity_pattern.append(RMP_model.addVar(obj=1.0, vtype=GRB.CONTINUOUS, column=new_column))
                pattern = np.c_[pattern, p]
            print('=' * 15)
            # solve RMP
            RMP_model.optimize()
            print(f"objective value: {RMP_model.ObjVal}")
            # get dual
            dual_list = RMP_model.getAttr(GRB.Attr.Pi, RMP_model.getConstrs())
            price_dual = dual_list[0:num_types]
            dual_correction = dual_list[num_types:len(dual_list)]
            print(f"price dual: {price_dual}")
            print(f"dual correction: {dual_correction}")

    return RMP_model, pattern
