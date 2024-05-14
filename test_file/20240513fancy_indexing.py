import numpy as np

# 假设 fraction 是一个 NumPy 数组
fraction = np.array([0.05, 0.1, 0.3, 0.2, 0.15])

# 定义一个阈值 TOL
TOL = 0.1

# 找出所有大于 TOL 的元素的索引
fractional_index = [k for k in range(len(fraction)) if fraction[k] > TOL]

print("fractional_index =", fractional_index)

# 使用这些索引找到对应的最大值的索引
k = fractional_index[np.argmax(fraction[fractional_index])]

print("k =", k)