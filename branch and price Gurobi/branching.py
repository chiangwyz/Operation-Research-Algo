from column_generation import *


class Node:
    def __init__(self):
        self.obj_value = 0
        self.model = None
        self.branching_indices = []
        self.branching_constr = []  # 仅日志使用
        self.pattern = None
        self.pattern_quantity = []

    def __lt__(self, other):
        # 定义小于运算符，用于堆操作
        return self.obj_value < other.obj_value


def add_left_branch(parameter, parent_node, branch_index):
    temp_node = Node()
    temp_node.pattern = parent_node.pattern
    temp_node.branching_constr = parent_node.branching_constr.copy()
    temp_node.branching_constr.append(f"x_{branch_index} <= {np.floor(parent_node.pattern_quantity[branch_index])}")
    for i in temp_node.branching_constr:
        print(i)
    temp_node.branching_indices = parent_node.branching_indices.copy()
    temp_node.branching_indices.append(branch_index)

    # parent_node.model.update()
    temp_node.model = parent_node.model.copy()
    v = temp_node.model.getVars()
    temp_node.model.addConstr(v[branch_index] <= np.floor(parent_node.pattern_quantity[branch_index]), name="branching constraint")
    temp_node.model, temp_node.pattern = solve_CSP_with_CG(parameter, temp_node.model, v, temp_node.pattern, temp_node.branching_indices)

    return temp_node


def add_right_branch(parameter, parent_node, branch_index):
    temp_node = Node()
    temp_node.pattern = parent_node.pattern
    temp_node.branching_constr = parent_node.branching_constr.copy()
    temp_node.branching_constr.append(f"x_{branch_index} >= {np.ceil(parent_node.pattern_quantity[branch_index])}")
    for i in temp_node.branching_constr:
        print(i)
    temp_node.branching_indices = parent_node.branching_indices.copy()
    temp_node.branching_indices.append(branch_index)

    # parent_node.model.update()
    temp_node.model = parent_node.model.copy()
    v = temp_node.model.getVars()
    temp_node.model.addConstr(v[branch_index] >= np.ceil(parent_node.pattern_quantity[branch_index]), name="branching constraint")
    temp_node.model, temp_node.pattern = solve_CSP_with_CG(parameter, temp_node.model, v, temp_node.pattern, temp_node.branching_indices)

    return temp_node
