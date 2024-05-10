from input import *
from solution import *
from branching import *
import heapq
import time
from rounding import perform_simple_rounding, perform_diving_heuristic


if __name__ == "__main__":
    # read in date
    parameter = read_in(input_data)

    # initialize
    t1 = time.time()
    bb_tree = []
    solution = Solution()
    m = gp.Model('Restricted Masterproblem')
    pattern = np.array([[0 for j in range(parameter.num_types)] for i in range(parameter.num_types)], dtype=np.int32)
    for i in range(parameter.num_types):
        pattern[i][i] = np.floor(parameter.length_raw / parameter.specification[i])
    # variables of RMP
    x = m.addVars(parameter.num_types, obj=1, vtype=GRB.CONTINUOUS)
    # constraints of RMP
    m.addConstrs(
        (gp.quicksum(pattern[i][j] * x[j] for j in range(len(x))) >= parameter.demand[i]
         for i in range(parameter.num_types)), name='demand satisfaction')
    # set parameters
    m.Params.OutputFlag = 0
    m.setAttr(GRB.Attr.ModelSense, GRB.MINIMIZE)
    m.update()

    # root node
    temp_node = Node()
    temp_node.model = m
    temp_node.pattern = pattern
    heapq.heappush(bb_tree, temp_node)

    print("perform column generation")
    bb_tree[0].model, bb_tree[0].pattern = solve_CSP_with_CG(parameter, bb_tree[0].model, bb_tree[0].model.getVars(), bb_tree[0].pattern, bb_tree[0].branching_indices)
    bb_tree[0].obj_value = bb_tree[0].model.ObjVal
    bb_tree[0].pattern_quantity = np.zeros(len(bb_tree[0].model.getVars()))
    for j in range(len(bb_tree[0].pattern_quantity)):
        bb_tree[0].pattern_quantity[j] = bb_tree[0].model.getVars()[j].X

    num_iterations = 1
    while True:
        print(f"======Iteration {num_iterations}======")
        # print solution
        print("===LP-relaxation===")
        print(f"objc of relaxation: {bb_tree[0].obj_value}")
        for j in range(len(bb_tree[0].pattern_quantity)):
            print(f"pattern {j}:  {bb_tree[0].pattern.T[j]} with quantity: {bb_tree[0].pattern_quantity[j]}")
        print('=' * 15)
        # cut off by bound
        if bb_tree[0].obj_value > solution.ub:
            print("!!!cut off by bound!!!")
            heapq.heappop(bb_tree)  # cut off by bound
            continue
        # check integrity
        LP_opt_int = False
        fraction = np.abs(np.round(bb_tree[0].pattern_quantity) - bb_tree[0].pattern_quantity)
        # case of integral solution
        if fraction.sum() <= TOL:
            print("===integral solution===")
            LP_opt_int = True
            # update ub and incumbent
            if bb_tree[0].obj_value < solution.ub:
                print("===better integral solution found by solving LP-relaxation===")
                solution.ub = bb_tree[0].obj_value
                solution.pattern = bb_tree[0].pattern
                solution.total_consumption = bb_tree[0].obj_value
                solution.incumbent = bb_tree[0].pattern_quantity
                print(f"objective value: {solution.total_consumption}")
                for j in range(len(solution.incumbent)):
                    print(f"pattern {j}:  {solution.pattern.T[j]} with quantity: {solution.incumbent[j]}")

        # case of fractional solution
        else:
            print("===fractional solution===")
            # perform rounding heuristic (store in solution.incumbent)
            if rounding_opt == 0:
                rounded_sol = perform_simple_rounding(bb_tree[0].pattern_quantity)
                if np.sum(rounded_sol) < solution.ub:
                    print("===better integral solution found by simple rounding===")
                    solution.ub = np.sum(rounded_sol)
                    solution.pattern = bb_tree[0].pattern
                    solution.total_consumption = np.sum(rounded_sol)
                    solution.incumbent = rounded_sol
                    print(f"objective value: {solution.total_consumption}")
                    for j in range(len(solution.incumbent)):
                        print(f"pattern {j}:  {solution.pattern.T[j]} with quantity: {solution.incumbent[j]}")

            elif rounding_opt == 1:
                rounded_sol, pattern_r = perform_diving_heuristic(bb_tree[0].pattern_quantity, parameter, bb_tree[0].pattern)
                if np.sum(rounded_sol) < solution.ub:
                    print("===better integral solution found by diving heuristic===")
                    solution.ub = np.sum(rounded_sol)
                    solution.pattern = pattern_r
                    solution.total_consumption = np.sum(rounded_sol)
                    solution.incumbent = rounded_sol
                    print(f"objective value: {solution.total_consumption}")
                    for j in range(len(solution.incumbent)):
                        print(f"pattern {j}:  {solution.pattern.T[j]} with quantity: {solution.incumbent[j]}")

            # identify the element to branch
            fractional_index = [k for k in range(len(fraction)) if fraction[k] > TOL]
            k = fractional_index[np.argmax(fraction[fractional_index])]
            print('='*15)
            print(f"branch on x_{k}")
            # take the first node as parent node
            parent_node = heapq.heappop(bb_tree)
            print("parent node is removed")
            # add left branch
            temp_node = add_left_branch(parameter, parent_node, k)
            if temp_node.model.Status != 3:  # feasible solution
                temp_node.obj_value = temp_node.model.ObjVal
                temp_node.pattern_quantity = np.zeros(len(temp_node.model.getVars()))
                for j in range(len(temp_node.pattern_quantity)):
                    temp_node.pattern_quantity[j] = temp_node.model.getVars()[j].X
                heapq.heappush(bb_tree, temp_node)
                print("left child node is added")
                # print solution
                print(f"objective value: {temp_node.obj_value}")
                for j in range(len(temp_node.model.getVars())):
                    print(f"pattern {j}:  {temp_node.pattern.T[j]} with quantity: {temp_node.model.getVars()[j].x}")
                print('=' * 15)
            else:
                print("!!!cut off by infeasibility!!!")

            # add right branch
            temp_node = add_right_branch(parameter, parent_node, k)
            if temp_node.model.Status != 3:  # feasible solution
                temp_node.obj_value = temp_node.model.ObjVal
                temp_node.pattern_quantity = np.zeros(len(temp_node.model.getVars()))
                for j in range(len(temp_node.pattern_quantity)):
                    temp_node.pattern_quantity[j] = temp_node.model.getVars()[j].X
                heapq.heappush(bb_tree, temp_node)
                print("right child node is added")
                # print solution
                print(f"objective value: {temp_node.obj_value}")
                for j in range(len(temp_node.model.getVars())):
                    print(f"pattern {j}:  {temp_node.pattern.T[j]} with quantity: {temp_node.model.getVars()[j].x}")
                print('=' * 15)
            else:
                print("!!!cut off by infeasibility!!!")

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
        print(f"LB: {solution.lb}")
        print(f"integral LB: {solution.int_lb}")
        print(f"UB: {solution.ub}")
        print(f"gap: {solution.gap * 100} % ")
        print(f"{len(bb_tree)} nodes left")
        for i in bb_tree:
            print(f"obj: {i.obj_value}")
        print('=' * 15)

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
        print(f"pattern {j}:  {solution.pattern.T[j]} with quantity: {solution.incumbent[j]}")
