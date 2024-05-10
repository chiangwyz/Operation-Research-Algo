class Solution:
    def __init__(self):
        self.total_consumption = 0
        self.incumbent = None
        self.pattern = None
        self.lb = 1e-8
        self.int_lb = 1e-8
        self.ub = float("inf")
        self.gap = 100  # large enough
