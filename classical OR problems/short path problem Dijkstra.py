"""
author: Dapei Jiang
Time: 2024-1-9 15:02:06
shortest path problem with Dijkstra algorithm.
Example reference:
Cappanera, P., & Scaparra, M. P. (2011).
Optimal allocation of protective resources in shortest-path networks. Transportation Science, 45(1), 64-80.
"""

import networkx as nx
import matplotlib.pyplot as plt
import copy
import re
import math


class ShortestPathProblemDijkstra:
    def __init__(self):
        self.nodes = ['1', '2', '3', '4', '5', '6', '7']
        self.original_node = "1"
        self.destination_node = "7"

        self.arcs = {
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

        # plot map need
        self.nodes_coordination = {
            '1': [0, 1],
            '2': [1, 2],
            '3': [1, 0],
            '4': [2, 1],
            '5': [3, 2],
            '6': [3, 0],
            '7': [4, 1]
        }

        # 绘图使用
        self.Graph = nx.DiGraph()
        self.nodes_position = {}

    def build_graph(self):
        cnt = 0

        # add nodes
        for name in self.nodes:
            cnt += 1
            x_coor = self.nodes_coordination[name][0]
            y_coor = self.nodes_coordination[name][1]
            self.Graph.add_node(name,
                           ID=cnt,
                           node_type='normal',
                           demand=0,
                           x_coordinate=x_coor,
                           y_coordinate=y_coor,
                           min_dis=0)
            self.nodes_position[name] = (x_coor, y_coor)

        # add edges
        for key, value in self.arcs.items():
            self.Graph.add_edge(key[0], key[1], length=value, traveTime=0)

    def Dijkstra(self, org, des):
        # 定义无穷大
        big_M = 9999999
        # 初始化当前节点最短距离与其他节点最短距离
        Queue = []
        for node in self.Graph.nodes:
            Queue.append(node)
            if node == org:
                self.Graph.nodes[node]['min_dis'] = 0
            else:
                self.Graph.nodes[node]['min_dis'] = big_M

        # 循环开始
        while len(Queue) > 0:
            # 选取下一个节点： 寻找具有最小 min_dis 的节点
            current_node = None
            min_dis = big_M
            for node in Queue:
                if self.Graph.nodes[node]['min_dis'] < min_dis:
                    current_node = node
                    min_dis = self.Graph.nodes[node]['min_dis']

            if current_node is not None:
                Queue.remove(current_node)

            # 遍历历每个邻节点
            for child in self.Graph.successors(current_node):
                arc_key = (current_node, child)
                dis_temp = self.Graph.nodes[current_node]['min_dis'] + self.Graph.edges[arc_key]['length']
                if dis_temp < self.Graph.nodes[child]['min_dis']:
                    self.Graph.nodes[child]['min_dis'] = dis_temp
                    self.Graph.nodes[child]['previous_node'] = current_node


        optimal_distance = self.Graph.nodes[des]['min_dis']
        current_node = des
        optimal_path = [current_node]
        while current_node != org:
            current_node = self.Graph.nodes[current_node]['previous_node']
            optimal_path.insert(0, current_node)

        return optimal_distance, optimal_path

    def plot_network(self):
        # 创建包含路径中所有边的列表
        path_edges = [(optimal_path[i], optimal_path[i + 1]) for i in range(len(optimal_path) - 1)]

        # 定义路径中的边和其它边的颜色
        color_map = ['red' if edge in path_edges else 'black' for edge in self.Graph.edges()]

        # 绘制图形，使用 color_map 为边着色
        nx.draw(self.Graph, self.nodes_position, with_labels=True, node_color='skyblue', node_size=1500, arrowstyle='->', arrowsize=20, edge_color=color_map, width=2)

        # 获取边的权重并作为边的标签
        edge_labels = nx.get_edge_attributes(self.Graph, 'length')

        # 在图上绘制边的标签
        nx.draw_networkx_edge_labels(self.Graph, self.nodes_position, edge_labels=edge_labels)

        # 画图
        plt.show()


if __name__ == "__main__":
    SPP = ShortestPathProblemDijkstra()
    SPP.build_graph()
    optimal_distance, optimal_path = SPP.Dijkstra(SPP.original_node, SPP.destination_node)
    print('optimal distance : ', optimal_distance)
    print('optimal path : ', optimal_path)
    SPP.plot_network()
