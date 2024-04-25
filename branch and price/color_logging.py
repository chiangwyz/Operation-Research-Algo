import logging
from colorlog import ColoredFormatter


class LoggerFactory:
    @staticmethod
    def get_colored_logger() -> logging.Logger:
        """
        返回一个配置好的、带颜色的logger对象，其名称设置为调用该方法的模块名，并且在日志消息中包含行号。
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

            # 创建一个带颜色的formatter，包括文件名和行号
            formatter = ColoredFormatter(
                "%(log_color)s%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s%(reset)s",
                datefmt=None,
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

            # 给logger添加handler
            logger.addHandler(ch)

        return logger


if __name__ == '__main__':
    # 使用示例
    logger = LoggerFactory.get_colored_logger()

    logger.debug('This is a debug message')
    logger.info('This is an info message')
    logger.warning('This is a warning message')
    logger.error('This is an error message')
    logger.critical('This is a critical message')
