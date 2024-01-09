import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import copy
import re
import math

Nodes = ['1', '2', '3', '4', '5', '6', '7']

Arcs = {
    ('1', '2'): 15,
    ('1', '3'): 45,
    ('1', '4'): 25,
    ('2', '4'): 2,
    ('2', '5'): 30,
    ('3', '6'): 25,
    ('4', '3'): 2,
    ('4', '7'): 50,
    ('5', '7'): 2,
    ('6', '7'): 1
}

Coordination = {
    '1': [0, 1],
    '2': [1, 2],
    '3': [1, 0],
    '4': [2, 1],
    '5': [3, 2],
    '6': [3, 0],
    '7': [4, 1]
}

# 构建有向图对象
Graph = nx.DiGraph()
cnt = 0
pos_location = {}
for name in Nodes:
    cnt += 1
    # x_coor = np.random.randint(1, 10)
    # y_coor = np.random.randint(1, 10)
    x_coor = Coordination[name][0]
    y_coor = Coordination[name][1]
    Graph.add_node(name,
                   ID=cnt,
                   node_type='normal',
                   demand=0,
                   x_coordinate=x_coor,
                   y_coordinate=y_coor,
                   min_dis=0,
                   previous=None
                   )
    pos_location[name] = (x_coor, y_coor)

# 增加图的边界
for key in Arcs.keys():
    Graph.add_edge(key[0], key[1], length=Arcs[key], traveTime=0)


def Dijkstra(Graph, org, des):
    # 定义bigM
    big_M = 9999999
    # 将每个点对应的最小距离初始化为无穷大以及初始化队列
    Queue = []
    for node in Graph.nodes:
        Queue.append(node)
        if (node == org):
            Graph.nodes[node]['min_dis'] = 0
        else:
            Graph.nodes[node]['min_dis'] = big_M

    # 循环开始
    while (len(Queue) > 0):
        # 选取下一个节点： 寻找具有最小 min_dis 的节点
        current_node = None
        min_dis = big_M
        for node in Queue:
            if (Graph.nodes[node]['min_dis'] < min_dis):
                current_node = node
                min_dis = Graph.nodes[node]['min_dis']

        if (current_node != None):
            Queue.remove(current_node)

        # 对每个邻居进行循环
        for child in Graph.successors(current_node):
            arc_key = (current_node, child)
            dis_temp = Graph.nodes[current_node]['min_dis'] + Graph.edges[arc_key]['length']
            if (dis_temp < Graph.nodes[child]['min_dis']):
                Graph.nodes[child]['min_dis'] = dis_temp
                Graph.nodes[child]['previous_node'] = current_node

    opt_dis = Graph.nodes[des]['min_dis']
    current_node = des
    opt_path = [current_node]
    while (current_node != org):
        current_node = Graph.nodes[current_node]['previous_node']
        opt_path.insert(0, current_node)

    return Graph, opt_dis, opt_path


Graph, opt_dis, opt_path = Dijkstra(Graph, '1', '7')
print('optimal distance : ', opt_dis)
print('optimal path : ', opt_path)

# 创建包含路径中所有边的列表
path_edges = [(opt_path[i], opt_path[i + 1]) for i in range(len(opt_path) - 1)]

# 定义路径中的边和其它边的颜色
color_map = ['red' if edge in path_edges else 'black' for edge in Graph.edges()]

# 绘制图形，使用 color_map 为边着色
nx.draw(Graph, pos_location, with_labels=True, node_color='skyblue', node_size=1500, arrowstyle='->', arrowsize=20, edge_color=color_map, width=2)

# 获取边的权重并作为边的标签
edge_labels = nx.get_edge_attributes(Graph, 'length')

# 在图上绘制边的标签
nx.draw_networkx_edge_labels(Graph, pos_location, edge_labels=edge_labels)

# 画图
plt.show()

