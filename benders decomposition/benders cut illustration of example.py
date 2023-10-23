"""
将benders cut生成进行展示
"""

import matplotlib.pyplot as plt
import numpy as np

# 创建一个figure和axes对象
fig, ax = plt.subplots(figsize=(15, 10))

# 设置x和y轴的范围
ax.set_xlim([-100, 1100])
ax.set_ylim([1020, 1120])

# 设置X轴的间距为50, Y轴的间距为10
ax.set_xticks(np.arange(-100, 1101, 100))
ax.set_yticks(np.arange(1020, 1121, 10))

# 画出直线y = 2x + 1
# x1 = np.linspace(-10, 10, 400)  # 创建一个从-10到10的等间隔数列
# y1 = 2*x + 1
# ax.plot(x1, y1, label='y1 = 2x1 + 1', color='blue')

# 画出直线 1000 - x = 0，且添加标签
x2 = [1000, 1000]
y2 = [-100, 1200]
ax.plot(x2, y2, color='red')
ax.annotate('cut 1:1000 - x ≥ 0', xy=(1000, 1030), xytext=(1030, 1030),
            arrowprops=dict(facecolor='red', arrowstyle="->"),
            color='black', fontsize=10)

# 画出直线 1100 - 0.055 * y >= z,
x3 = np.linspace(0, 1000, 400)
y3 = 1100 - 0.055 * x3
ax.plot(x3, y3, color='blue')
ax.annotate('cut 2: 1100 - 0.055 * y = z', xy=(900, 1050.5), xytext=(800, 1040),
            arrowprops=dict(facecolor='red', arrowstyle="->"),
            color='black', fontsize=10)

# 画出直线 1055 + 1.045 * y >= z,
x4 = np.linspace(0, 1000, 400)
y4 = 1055 + 1.045 * x4
ax.plot(x4, y4, color='yellow')
ax.annotate('cut 3: 1055 + 1.045 * y >= z', xy=(52.63, 1110), xytext=(100, 1110),
            arrowprops=dict(facecolor='red', arrowstyle="->"),
            color='black', fontsize=10)

# 画出直线 1055 + 0.035 * y >= z,
x5 = np.linspace(0, 1000, 400)
y5 = 1055 + 0.035 * x5
ax.plot(x5, y5, color='orange')
ax.annotate('cut 4: 1055 + 0.035 * y >= z', xy=(800, 1083), xytext=(750, 1090),
            arrowprops=dict(facecolor='red', arrowstyle="->"),
            color='black', fontsize=10)

# 画出直线 1065 - 0.005 * y >= z,
x6 = np.linspace(0, 1000, 400)
y6 = 1065 - 0.005 * x6
ax.plot(x6, y6, color='black')
ax.annotate('cut 5: 1065 - 0.005 * y >= z', xy=(600, 1062), xytext=(500, 1050),
            arrowprops=dict(facecolor='red', arrowstyle="->"),
            color='black', fontsize=10)

# 画出直线 1058 + 0.015 * y >= z,
x7 = np.linspace(0, 1000, 400)
y7 = 1058 + 0.015 * x7
ax.plot(x7, y7, color='brown')
ax.annotate('cut 6: 1058 + 0.015 * y >= z', xy=(650, 1067.75), xytext=(600, 1085),
            arrowprops=dict(facecolor='red', arrowstyle="->"),
            color='black', fontsize=10)

x8 = np.linspace(0, 1000, 400)
y8 = 1061 + 0.005 * x8
ax.plot(x8, y8, color='pink')
ax.annotate('cut 7: 1061 + 0.005 * y >= z', xy=(300, 1062.5), xytext=(200, 1055),
            arrowprops=dict(facecolor='red', arrowstyle="->"),
            color='black', fontsize=10)

# 设置标题和轴标签
ax.set_title("Benders Cuts in Example")
ax.set_xlabel("Y-axis")
ax.set_ylabel("Z-axis")

# 在图上显示图例
# ax.legend()

# 在图上显示网格
ax.grid(True)

# 显示图形，将X轴和Y轴加粗显示
plt.axhline(0, color='black', linewidth=2)  # 加粗的Y轴
plt.axvline(0, color='black', linewidth=2)  # 加粗的X轴

plt.savefig("benders cuts.pdf")
plt.savefig("benders cuts.png", dpi=1200)
plt.show()