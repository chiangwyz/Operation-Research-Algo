import numpy as np
from logger_config import logger


class Data:
    """
    构造函数内初始化要声明成员变量的类型！！！
    """
    def __init__(self):
        # 原材料钢卷长度
        self.Width = 0

        # 钢卷需求的尺寸，使用 NumPy 数组
        self.Customer_demand_sizes = np.array([])

        # 钢卷需求的数量，使用 NumPy 数组
        self.Customer_demands = np.array([])

        # 钢卷需求的客户数量
        self.Customer_numbers = 0

    def read_data(self, data_path: str) -> None:
        with open(data_path, 'r') as f:
            lines = f.readlines()

        self.Width = int(lines[1].strip())
        self.Customer_demand_sizes = np.array(list(map(int, lines[3].split(', '))))
        self.Customer_demands = np.array(list(map(int, lines[5].split(', '))))

        self.Customer_numbers = len(self.Customer_demands)

        logger.info("read data successfully!")

    def print_data(self) -> None:
        logger.info('Width: {}, Demand Sizes: {}, Demands: {}, Customer Numbers: {}'.format(self.Width, self.Customer_demand_sizes, self.Customer_demands, self.Customer_numbers))


if __name__ == '__main__':
    data = Data()
    data.read_data('data.txt')
    data.print_data()
