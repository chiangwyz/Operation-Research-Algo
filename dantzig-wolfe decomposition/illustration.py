import matplotlib.pyplot as plt
import networkx as nx

# 创建一个新的图
G = nx.DiGraph()

# 自定义节点位置
pos = {
    1: (0, 1),
    2: (1, 2),
    3: (1, 0),
    4: (3, 1),
    5: (4, 2),
    6: (4, 0),
    7: (5, 1)
}

# 添加节点
G.add_nodes_from(range(1, 8))  # 节点从1到7

# 添加边，包括商品流的信息
edges_info = {
    (1, 2): [15, 15],
    (1, 3): [45, 45],
    (1, 4): [25, 25],
    (2, 4): [2, 2],
    (2, 5): [30, 60],
    (3, 6): [25, 50],
    (4, 3): [2, 2],
    (4, 7): [50, 100],
    (5, 7): [2, 2],
    (6, 7): [1, 1]
}

# 在图中添加边
for edge, flow in edges_info.items():
    G.add_edge(*edge, flow=flow)

# 绘制节点
nx.draw_networkx_nodes(G, pos, node_color='lightblue', node_size=700)

# 绘制边，并用标签表示流量
edge_labels = {(u, v): f"{data['flow']}" for u, v, data in G.edges(data=True)}

nx.draw_networkx_edges(G, pos, arrowstyle='->', arrowsize=20)
nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
nx.draw_networkx_labels(G, pos, font_size=10)


# 显示图形
plt.title("Multi-Commodity Network Flow Diagram")
plt.axis('off')
plt.show()

