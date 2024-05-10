from color_logging import LoggerFactory

logger = LoggerFactory.get_colored_logger()


class Data:
    def __init__(self):
        # 原材料钢卷长度
        self.Width = 0

        # 钢卷需求的尺寸
        self.Customer_demand_sizes = []

        # 钢卷需求的数量
        self.Customer_demands = []

        # 钢卷需求的客户数量
        self.Customer_numbers = 0

    def read_data(self, data_path: str) -> None:
        with open(data_path, 'r') as f:
            lines = f.readlines()

        self.Width = int(lines[1].strip())
        self.Customer_demand_sizes = list(map(int, lines[3].split(', ')))
        self.Customer_demands = list(map(int, lines[5].split(', ')))

        self.Customer_numbers = len(self.Customer_demands)

    def print_data(self) -> None:
        logger.info('Width: {}'.format(self.Width))
        logger.info('Demand Sizes: {}'.format(self.Customer_demand_sizes))
        logger.info('Demands: {}'.format(self.Customer_demands))
        logger.info('Customer Numbers: {}'.format(self.Customer_numbers))


if __name__ == '__main__':
    data = Data()
    data.read_data('data.txt')
    data.print_data()
