import numpy as np

# 假设这是从某个对象属性获取的列表
pattern_quantity = [3.14, 2.71, -1.05, 0.99, 5.49]

# 对列表中的每个元素进行四舍五入
rounded_values = np.round(pattern_quantity)

# 计算四舍五入后的值与原始值之间的绝对差值
fraction = np.abs(rounded_values - pattern_quantity)

print("原始值列表: ", pattern_quantity)
print("四舍五入后的值列表: ", rounded_values)
print("绝对差值列表: ", fraction)

print("绝对差值总和", fraction.sum())
