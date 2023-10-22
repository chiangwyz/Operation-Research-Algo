import numpy as np
import copy
from coptpy import *
import matplotlib.pyplot as plt


class Node:
    def __init__(self):
        self.model = None
        self.cnt = None
        self.x_sol = {}  # solution of sub-problem
        self.x_int_sol = {}  # round integer of solution
        self.local_LB = 0  # local bound of node, sub-problem
        self.local_UB = np.inf
        self.is_integer = False  # is integer solution
        self.branch_var_list = []  # store branch variable

    # deep copy the whole node
    @staticmethod
    def deepcopy(node):
        new_node = Node()
        new_node.local_LB = 0
        new_node.local_UB = np.inf
        new_node.x_sol = copy.deepcopy(node.x_sol)  # solution of sub-problem
        new_node.x_int_sol = copy.deepcopy(node.x_int_sol)  # round integer of solution
        new_node.branch_var_list = []  # do not copy, or that always use the same branch_var_list in sub-problem
        # deepcopy, or that the subproblem add all the new constraints sub-problem->infeasible
        new_node.model = node.model.clone()  # COPT can deepcopy model
        new_node.cnt = node.cnt
        new_node.is_integer = node.is_integer

        return new_node


def branch_and_bound(nasa, values):
    # 注意COPT求解LP的方法
    nasa.solveLP()
    global_LB = 0
    global_UB = nasa.objval
    eps = 1e-3
    incumbent_node = None
    Gap = np.inf

    ############## branch and bound begins ##############
    Queue = []
    # create root node
    node = Node()
    node.local_LB = 0
    node.local_UB = global_UB  # root node
    node.model = nasa.clone()
    node.cnt = 0
    node.model.setParam('Logging', 1)
    Queue.append(node)
    # cycle
    cnt = 0
    Global_UB_change = []
    Global_LB_change = []
    while len(Queue) > 0 and global_UB - global_LB > eps:
        cnt += 1
        # Use depth-first search, last in, first out
        # pop: removes the last element from a list and returns the value of that element
        # current_node = Queue.pop()

        current_node = select_node_by_best_first(Queue)

        if current_node:
            Queue.remove(current_node)
        else:
            current_node = Queue.pop()

        # solve the current node
        current_node.model.solveLP()
        Solution_status = current_node.model.status
        # check the current solution(is_Integer, is_pruned)
        Is_Integer = True
        Is_pruned = False

        ############## check whether the sub-problem is feasible ##############
        if Solution_status == COPT.OPTIMAL:
            ############## check whether the current solution is integer##############
            for var in current_node.model.getVars():
                current_node.x_sol[var.getName()] = var.x
                print(var.getName(), '=', var.x)
                # round the fractional solution, round down
                current_node.x_int_sol[var.getName()] = int(var.x)
                if abs(int(var.x) - var.x) >= eps:
                    Is_Integer = False  # judge whether the solution is integer or not
                    current_node.branch_var_list.append(var.getName())
            # Update LB and UB

            ############## is integer, incumbent ##############
            if Is_Integer == True:
                current_node.local_LB = current_node.model.objval
                current_node.local_UB = current_node.model.objval
                current_node.is_integer = True
                if current_node.local_LB > global_LB:
                    global_LB = current_node.local_LB
                    incumbent_node = Node.deepcopy(current_node)
            if Is_Integer == False:
                current_node.is_integer = False
                current_node.local_UB = current_node.model.objval
                current_node.local_LB = 0
                for var_name in current_node.x_int_sol.keys():
                    current_node.local_LB += current_node.x_int_sol[var_name] * current_node.model.getVarByName(var_name).obj
                if (current_node.local_LB > global_LB or (
                        current_node.local_LB == global_LB and current_node.is_integer == True)):
                    global_LB = current_node.local_LB
                    incumbent_node = Node.deepcopy(current_node)
                    incumbent_node.local_LB = current_node.local_LB
                    incumbent_node.local_UB = current_node.local_UB
            if (Is_Integer == True):
                Is_pruned = True
            if (Is_Integer == False and current_node.local_UB < global_LB):
                Is_Integer = True
            Gap = round(100 * (global_UB - global_LB) / global_LB, 2)
            print('\n---------------\n', cnt, '\t Gap = ', Gap, '%')

        ############## prune by infeasibility ##############
        elif Solution_status != COPT.OPTIMAL:
            Is_Integer = False
            Is_pruned = True
            continue
        ############## branch ##############
        if Is_pruned == False:
            branch_var_name = current_node.branch_var_list[0]
            left_var_bound = int(current_node.x_sol[branch_var_name])
            right_var_bound = int(current_node.x_sol[branch_var_name]) + 1

            # create two child nodes
            left_node = Node.deepcopy(current_node)
            right_node = Node.deepcopy(current_node)

            # create left child nodes
            temp_var = left_node.model.getVarByName(branch_var_name)
            left_node.model.addConstr(temp_var <= left_var_bound, name='branch_left_' + str(cnt))
            left_node.model.setParam('Logging', 1)
            cnt += 1
            left_node.cnt = cnt

            # create right child nodes
            temp_var = right_node.model.getVarByName(branch_var_name)
            right_node.model.addConstr(temp_var >= right_var_bound, name='branch_right_' + str(cnt))
            right_node.model.setParam('Logging', 1)
            cnt += 1
            right_node.cnt = cnt

            Queue.append(left_node)
            Queue.append(right_node)

            ############## update Upper bound ##############
            temp_global_UB = 0
            for node in Queue:
                node.model.solveLP()
                if node.model.status == COPT.OPTIMAL:
                    if node.model.objval >= temp_global_UB:
                        temp_global_UB = node.model.objval
            # if global_LB <= temp_global_UB <= global_UB:
            global_UB = temp_global_UB
            Global_LB_change.append(global_LB)
            Global_UB_change.append(global_UB)
    # all the nodes are explored,update the LB and UB
    global_UB = global_LB
    Gap = round(100 * (global_UB - global_LB) / global_LB, 2)
    Global_LB_change.append(global_LB)
    Global_UB_change.append(global_UB)

    print('\n\n\n\n')
    print('---------------------------------------')
    print('       Branch and Bound terminates     ')
    print('       Optimal solution found          ')
    print('---------------------------------------')
    print('\nFinal Gap:', Gap, ' %')
    print("\n cnt ={}".format(cnt))
    print('Optimal Solution:', incumbent_node.x_int_sol)
    print('Optimal Obj:', global_LB)

    return incumbent_node, Gap, Global_UB_change, Global_LB_change


def select_node_by_best_first(Node_List):
    """
    perform best first rule to search in the BB tree
    """
    # 判断Node_List是否为空
    if not Node_List:
        return None

    best_UB = 0
    selected_node = None
    for node in Node_List:
        node.model.solveLP()
        if node.model.status == COPT.OPTIMAL and node.model.objval >= best_UB:
            best_UB = node.model.objval
            selected_node = node

    return selected_node



def plot_up_and_lb(Global_UB_change, Global_LB_change):
    font_dict = {"family": 'Arial',  # "Kaiti",
                 "style": "oblique",
                 "weight": "normal",
                 "color": "green",
                 "size": 20
                 }

    plt.rcParams['figure.figsize'] = (12.0, 8.0)  # 单位是inches
    plt.rcParams["font.family"] = 'Arial'  # "SimHei"
    plt.rcParams["font.size"] = 16

    x_cor = range(1, len(Global_LB_change) + 1)
    plt.plot(x_cor, Global_LB_change, label='LB')
    plt.plot(x_cor, Global_UB_change, label='UB')
    plt.legend()
    plt.xlabel('Iteration', fontdict=font_dict)
    plt.ylabel('LB and UB updates', fontdict=font_dict)
    plt.title('Bounds updates during branch and bound procedure (COPT)\n', fontsize=23)
    plt.savefig('Bound_updates (math.floor + best first) .eps')
    plt.savefig('Bound_updates (math.floor + best first) .pdf')

    plt.show()


def main():
    # Create COPT environment
    env = Envr()
    # create model
    nasa = env.createModel("nasa")

    tasks = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14"]
    values = {"1": 200, "2": 3, "3": 20, "4": 50, "5": 70, "6": 20, "7": 5, "8": 10, "9": 200, "10": 150, "11": 18,
              "12": 8,
              "13": 300, "14": 185}
    stage1 = {"1": 6, "2": 2, "3": 3, "4": 0, "5": 0, "6": 0, "7": 1, "8": 0, "9": 4, "10": 0, "11": 0, "12": 5,
              "13": 0,
              "14": 0}
    stage2 = {"1": 0, "2": 3, "3": 5, "4": 0, "5": 5, "6": 0, "7": 8, "8": 0, "9": 5, "10": 8, "11": 0, "12": 7,
              "13": 1,
              "14": 4}
    stage3 = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 8, "6": 1, "7": 0, "8": 0, "9": 0, "10": 4, "11": 2, "12": 0,
              "13": 4,
              "14": 5}
    stage4 = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 8, "7": 0, "8": 5, "9": 0, "10": 0, "11": 7, "12": 0,
              "13": 1,
              "14": 3}
    stage5 = {"1": 0, "2": 0, "3": 0, "4": 10, "5": 0, "6": 4, "7": 0, "8": 0, "9": 0, "10": 0, "11": 0, "12": 0,
              "13": 1,
              "14": 3}

    # 决策变量
    x = {}
    for i in tasks:
        x[i] = nasa.addVar(lb=0, ub=1, vtype=COPT.BINARY, name='x[{}]'.format(i))
    # 定义目标函数
    obj = LinExpr(0)
    for i in tasks:
        obj.addTerms(x[i], values[i])
    nasa.setObjective(obj, sense=COPT.MAXIMIZE)

    # 添加约束
    lhs = LinExpr(0)
    for i in tasks:
        lhs.addTerms(x[i], stage1[i])
    nasa.addConstr(lhs <= 10, name='阶段1')

    lhs = LinExpr(0)
    for i in tasks:
        lhs.addTerms(x[i], stage2[i])
    nasa.addConstr(lhs <= 12, name='阶段2')

    lhs = LinExpr(0)
    for i in tasks:
        lhs.addTerms(x[i], stage3[i])
    nasa.addConstr(lhs <= 14, name='阶段3')

    lhs = LinExpr(0)
    for i in tasks:
        lhs.addTerms(x[i], stage4[i])
    nasa.addConstr(lhs <= 14, name='阶段4')

    lhs = LinExpr(0)
    for i in tasks:
        lhs.addTerms(x[i], stage5[i])
    nasa.addConstr(lhs <= 14, name='阶段5')

    nasa.addConstr(x['4'] + x['5'] <= 1, name='互斥条件1')
    nasa.addConstr(x['8'] + x['11'] <= 1, name='互斥条件2')
    nasa.addConstr(x['9'] + x['14'] <= 1, name='互斥条件3')

    nasa.addConstr(x['11'] - x['2'] <= 0, name='依赖任务1')
    nasa.addConstr(x['4'] - x['3'] <= 0, name='依赖任务2')
    nasa.addConstr(x['5'] - x['3'] <= 0, name='依赖任务3')
    nasa.addConstr(x['6'] - x['3'] <= 0, name='依赖任务4')
    nasa.addConstr(x['7'] - x['3'] <= 0, name='依赖任务5')

    nasa.solve()

    # LP的线性松弛解
    print("LP 线性松弛解为：")
    for var in nasa.getVars():
        print("{} = {}".format(var.getName(), var.x))

    # solve the IP model by B&B
    incumbent_node, Gap, Global_UB_change, Global_LB_change = branch_and_bound(nasa, values)

    plot_up_and_lb(Global_UB_change, Global_LB_change)


if __name__ == '__main__':
    main()
