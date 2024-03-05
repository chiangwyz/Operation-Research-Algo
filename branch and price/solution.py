"""
定义可行的solution
"""


class Solution(object):
    def __init__(self):
        self.lb = 0
        self.ub = 0
        self.pattern = None
        self.total_consumption = 0
        self.incumbent = None
        self.int_lb = 0
        self.int_ub = 0


