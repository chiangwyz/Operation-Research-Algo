import numpy as np

rounded_sol1 = np.array([1.5, 2.3, 3.7])
num_new_patterns = 2

print(rounded_sol1)

rounded_sol1 = np.pad(rounded_sol1, (0, num_new_patterns), 'constant')
# 结果为: array([1.5, 2.3, 3.7, 0.0, 0.0])

print(rounded_sol1)
