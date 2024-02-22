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