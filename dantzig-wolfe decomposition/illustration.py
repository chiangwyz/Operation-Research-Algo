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
    7: (5, 1)  # 例如：节点7的坐标为(3, 0)
}

# 添加节点
G.add_nodes_from(range(1, 8))  # 节点从1到7



# 添加边，包括商品流的信息，这次加入了所有的边和流量
# 商品流的表示现在将只用流量，因为图片中没有指定商品类型
edges_info = {
    (1, 3): 45, (1, 4): 15, (2, 3): 25, (2, 4): 30, (3, 5): 25, (3, 6): 20,
    (4, 5): 60, (4, 6): 10, (5, 7): 20, (6, 7): 1
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

