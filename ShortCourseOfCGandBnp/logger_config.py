import logging
from colorlog import ColoredFormatter
from datetime import datetime


class CustomFileHandler(logging.FileHandler):
    def __init__(self, filename, mode='w', encoding=None, delay=False):
        super().__init__(filename, mode, encoding, delay)


class CustomFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        if datefmt:
            s = datetime.fromtimestamp(record.created).strftime(datefmt)
        else:
            t = datetime.fromtimestamp(record.created)
            s = t.strftime("%Y-%m-%d %H:%M:%S")
            s = "%s,%03d" % (s, record.msecs)
        return s


class LoggerFactory:
    @staticmethod
    def get_colored_logger(log_name: str = "app.log") -> logging.Logger:
        """
        返回一个配置好的、带颜色的logger对象，其名称设置为调用该方法的模块名，并且在日志消息中包含行号。

        Parameters:
            log_name (str): 日志文件的名称。
        """
        # 直接使用__name__作为logger的名称
        name = __name__

        # 创建一个logger
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        # 防止日志消息被重复处理
        if not logger.handlers:
            # 创建一个handler，用于输出到控制台
            ch = logging.StreamHandler()
            ch.setLevel(logging.DEBUG)

            # 创建一个文件Handler
            fh = CustomFileHandler(log_name)  # 使用自定义的文件处理器
            fh.setLevel(logging.INFO)

            # 创建一个带颜色的formatter，包括文件名和行号
            formatter = ColoredFormatter(
                "%(log_color)s%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s%(reset)s",
                datefmt="%Y-%m-%d %H:%M:%S",
                reset=True,
                log_colors={
                    'DEBUG': 'cyan',
                    'INFO': 'green',
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'bold_red',
                },
                secondary_log_colors={},
                style='%'
            )

            # 设置handler的formatter
            ch.setFormatter(formatter)

            # 文件日志使用自定义格式（显示到毫秒）
            file_formatter = CustomFormatter(
                "%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S,%f"
            )

            # ch.setFormatter(file_formatter)
            fh.setFormatter(file_formatter)

            # 给logger添加handler
            logger.addHandler(ch)
            logger.addHandler(fh)

        return logger


# 创建一个全局logger
logger = LoggerFactory.get_colored_logger("primal_and_dual.log")

if __name__ == '__main__':
    # 使用示例
    logger = LoggerFactory.get_colored_logger()

    logger.debug('This is a debug message')
    logger.info('This is an info message')
    logger.warning('This is a warning message')
    logger.error('This is an error message')
    logger.critical('This is a critical message')
