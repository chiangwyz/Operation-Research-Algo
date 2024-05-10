import numpy as np

input_data = "..\\instance\\Instance_2.txt"


class Parameter:
    def __init__(self):
        self.num_types = None
        self.length_raw = None
        self.specification = None
        self.demand = None


def read_in(file_name):
    parameter = Parameter()
    f = open(file_name, "r", encoding='utf-8')

    f.readline()
    parameter.num_types = eval(f.readline())
    #
    f.readline()
    parameter.length_raw = eval(f.readline())
    #
    f.readline()
    specification = f.readline()
    specification = specification.strip('\n')
    specification = specification.split(' ')
    #
    for i in range(parameter.num_types):
        specification[i] = eval(specification[i])
    parameter.specification = np.array(specification)
    #
    f.readline()
    demand = f.readline()
    demand = demand.strip('\n')
    demand = demand.split(' ')
    for i in range(parameter.num_types):
        demand[i] = eval(demand[i])
    parameter.demand = np.array(demand)

    return parameter
