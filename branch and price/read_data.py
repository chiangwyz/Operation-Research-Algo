from color_logging import LoggerFactory


class Data:
    def __init__(self):
        # 原材料钢卷长度
        self.Width = 0

        # 需求钢卷的尺寸
        self.customer_demand_sizes = []

        # 需求钢卷的数量
        self.customer_demands = []

        # 需求钢卷的客户数量
        self.customer_demand_numbers = 0

    def read_data(self, data_path: str) -> None:
        with open(data_path, 'r') as f:
            lines = f.readlines()

        self.Width = int(lines[0].strip())
        # 将map对象转换为列表，确保demand_sizes和demand_numbers都是整数列表
        self.customer_demand_sizes = list(map(int, lines[1].split(', ')))
        self.customer_demands = list(map(int, lines[2].split(', ')))

        self.customer_demand_numbers = len(self.customer_demands)

    def print_data(self) -> None:
        logger = LoggerFactory.getColoredLogger()

        logger.info('Width: {}'.format(self.Width))
        logger.info('Demand Sizes: {}'.format(self.customer_demand_sizes))
        logger.info('Demands: {}'.format(self.customer_demands))
        logger.info('Demand Numbers: {}'.format(self.customer_demand_numbers))


if __name__ == '__main__':
    data = Data()
    data.read_data('data.txt')
    data.print_data()
