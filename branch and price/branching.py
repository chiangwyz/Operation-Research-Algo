import copy
from column_generation import *


class Node:
    def __init__(self):
        self.obj_value = 0
        self.model = None
        # 分支的变量下标
        self.branching_indices = []
        # 切割模式
        self.pattern = None
        # 切割
        self.pattern_quantity = []

    def __lt__(self, other):
        # 定义小于运算符，用于堆操作
        return self.obj_value < other.obj_value


def add_left_branch(data, parent_node, branch_index) -> Node:
    temp_node = Node()
    temp_node.pattern = parent_node.pattern
    temp_node.branching_indices = parent_node.branching_indices.copy()
    temp_node.branching_indices.append(branch_index)

    temp_node.model = parent_node.model.clone()
    variables = temp_node.model.getVars()
    temp_node.model.addConstr(variables[branch_index] <= np.floor(parent_node.pattern_quantity[branch_index]), name="branching constraint")
    temp_node.model, temp_node.pattern = solve_CSP_with_CG(data, temp_node.model, variables, temp_node.pattern, temp_node.branching_indices)

    return temp_node


def add_right_branch(data, parent_node, branch_index) -> Node:
    temp_node = Node()
    temp_node.pattern = parent_node.pattern
    temp_node.branching_indices = parent_node.branching_indices.copy()
    temp_node.branching_indices.append(branch_index)

    # parent_node.model.update()
    temp_node.model = parent_node.model.clone()
    variables = temp_node.model.getVars()
    temp_node.model.addConstr(variables[branch_index] >= np.ceil(parent_node.pattern_quantity[branch_index]), name="branching constraint")
    temp_node.model, temp_node.pattern = solve_CSP_with_CG(data, temp_node.model, variables, temp_node.pattern, temp_node.branching_indices)

    return temp_node
