"""
定义可行的solution
"""


class Solution(object):
    def __init__(self):
        self.lb = 1e-8
        self.ub = float("inf")
        self.pattern = None
        self.total_consumption = 0
        self.incumbent = None
        self.int_lb = 1e-8
        self.int_ub = float("inf")
        self.gap = 100


