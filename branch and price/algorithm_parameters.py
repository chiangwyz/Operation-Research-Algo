TOL = 1e-8
POOL_SIZE = 5
GAP_TOL = 0.0001
ROUNDING_OPT = 1
DOWN_THRESHOLD = 0.2
UP_THRESHOLD = 0.8

# map: num --> model status
GUROBI_Status_Map = {
    1: "GRB.LOADED",
    2: "GRB.OPTIMAL",
    3: "GRB.INFEASIBLE",
    4: "GRB.INF_OR_UNBD",
    5: "GRB.UNBOUNDED",
    6: "GRB.CUTOFF",
    7: "GRB.ITERATION_LIMIT",
    8: "GRB.NODE_LIMIT",
    9: "GRB.TIME_LIMIT",
    10: "GRB.SOLUTION_LIMIT",
    11: "GRB.INTERRUPTED",
    12: "GRB.NUMERIC",
    13: "GRB.SUBOPTIMAL",
    14: "GRB.INPROGRESS",
    15: "GRB.USER_OBJ_LIMIT",
    16: "GRB.WORK_LIMIT",
    17: "GRB.MEM_LIMIT"
}


class BaseSingletonCounter:
    _instances = {}
    count = 0

    def __new__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(BaseSingletonCounter, cls).__new__(cls, *args, **kwargs)
        return cls._instances[cls]

    @classmethod
    def increment(cls):
        cls.count += 1

    @classmethod
    def get_count(cls):
        return cls.count


class SPGlobalCounter(BaseSingletonCounter):
    pass


class MPGlobalCounter(BaseSingletonCounter):
    pass


class CSPGlobalCounter(BaseSingletonCounter):
    pass


class DGGlobalCounter(BaseSingletonCounter):
    pass


class SPDGlobalCounter(BaseSingletonCounter):
    pass


# 使用各自的计数器
sp_global_counter = SPGlobalCounter()
mp_global_counter = MPGlobalCounter()
csp_global_counter = CSPGlobalCounter()
diving_global_counter = DGGlobalCounter()
diving_sp_global_counter = SPDGlobalCounter()
