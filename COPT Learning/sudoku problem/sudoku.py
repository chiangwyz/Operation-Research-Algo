"""
This is a COPT learning document, not for commercial use. It is mainly for recording and archiving the study and use of COPT interfaces.
For specific examples, please refer to: https://coridm.d2d.ai/courses/32/supplement/790
"""

import coptpy as cp
from coptpy import COPT
import numpy as np
import pandas as pd

# 数独棋盘初始化
sudoku_info = pd.read_csv('sudoku.csv', dtype=int)
print(sudoku_info.head(10))

# build 9x9 matrix
SUDOKU_BOARD = np.zeros([9, 9], dtype=int)
for idx, r in sudoku_info.iterrows():
    print("index{0}:({1},{2})={3}".format(idx, r['row'], r['col'], r['value']))
    SUDOKU_BOARD[r['row'], r['col']] = r['value']


# 数独棋盘可视化工具
def print_board(board):
    row, col = board.shape
    for i in range(row):
        print_row = ''
        for j in range(col):
            sep = ' ' if j % 3 != 0 else '|'
            if board[i, j] == 0:
                print_row += '{}{}'.format(sep, '_')
            else:
                print_row += '{}{}'.format(sep, board[i, j])
        print_row += '|'
        print(print_row)
        if (i + 1) % 3 == 0 and i != row - 1:
            print('-' * len(print_row))


print_board(SUDOKU_BOARD)

# Create COPT environment
env = cp.Envr()
# Create COPT model
model = env.createModel("sudoku")

# Add variables: x
x = model.addVars(9, 9, 9, vtype=COPT.BINARY)
print("模型中决策变量的数量：", model.getAttr(attrname="Cols"))

# Fix variables associated with cells whose values are pre-specified
model.addConstrs(x[i, j, SUDOKU_BOARD[i][j] - 1] == 1 for i in range(9) for j in range(9) if SUDOKU_BOARD[i][j] != 0)
print("棋盘赋初值后约束条件数量：", model.getAttr("rows"))


## Each cell only takes one value
model.addConstrs(x.sum(i, j, "*") == 1
                 for i in range(9)
                 for j in range(9))
print("添加网格约束后，约束条件数量：",model.getAttr("rows"))

# Each value appears once per row
model.addConstrs(x.sum(i, "*", k) == 1
                 for i in range(9)
                 for k in range(9))
print("添加行约束后，模型约束条件数量：",model.getAttr("rows"))

# Each value appears once per column
model.addConstrs(x.sum("*", j, k) == 1
                 for j in range(9)
                 for k in range(9))
print("添加列约束后，模型约束条件数量：",model.getAttr("rows"))

# Each value appears once per subgrid
model.addConstrs(x.sum(range(p*3, (p+1)*3), range(q*3, (q+1)*3), k) == 1
    for k in range(9)
    for p in range(3)
    for q in range(3))
print("添加宫约束后，模型约束条件数量：",model.getAttr("rows"))

model.solve()

# 可视化数独求解结果
sudoku_solution = SUDOKU_BOARD.copy()
for i in range(9):
    for j in range(9):
        for k in range(9):
            if x[i, j, k].x > 0:
                sudoku_solution[i, j] = k + 1

print_board(sudoku_solution)
