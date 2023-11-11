
import networkx as nx
import matplotlib.pyplot as plt

# 定义距离矩阵
dist_matrix = [[2.0, 3.0, 4.0], [3.0, 2.0, 1.0], [1.0, 4.0, 3.0], [4.0, 5.0, 2.0]]

# 创建无向图
G = nx.Graph()

# 将节点添加到图中
for i in range(4):
    G.add_node(i)

# 将需求点的编号加上一个偏移量，以便于区分
demand_offset = 8
for i in range(4):
    G.add_node(i+demand_offset)

# 在图中添加边，边的权重为距离矩阵中的值
for i in range(4):
    for j in range(3):
        weight = dist_matrix[i][j]
        # 如果两个节点都是供应点，则添加一条边
        if i < demand_offset and j >= demand_offset:
            continue
        elif i >= demand_offset and j < demand_offset:
            continue
        else:
            G.add_edge(i, j+demand_offset, weight=weight)

# 绘制图形
pos = nx.spring_layout(G)
supply_pos = {}
demand_pos = {}
for n in G.nodes():
    if n < demand_offset:
        supply_pos[n] = pos[n]
    else:
        demand_pos[n] = pos[n]
nx.draw_networkx_nodes(G, pos=supply_pos, node_size=700, node_shape='o')
nx.draw_networkx_nodes(G, pos=demand_pos, node_size=700, node_shape='v')
nx.draw_networkx_edges(G, pos=pos, width=6)
nx.draw_networkx_labels(G, pos=pos)
plt.show()