"""
日志模块
提供多进程安全的日志记录功能
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
import multiprocessing


class ColoredFormatter(logging.Formatter):
    """带颜色的日志格式化器(控制台输出)"""

    # ANSI颜色代码
    COLORS = {
        'DEBUG': '\033[36m',      # 青色
        'INFO': '\033[32m',       # 绿色
        'WARNING': '\033[33m',    # 黄色
        'ERROR': '\033[31m',      # 红色
        'CRITICAL': '\033[35m',   # 紫色
    }
    RESET = '\033[0m'

    def format(self, record):
        # 添加颜色
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.RESET}"

        return super().format(record)


class Logger:
    """日志管理器"""

    _instance: Optional[logging.Logger] = None
    _initialized: bool = False

    @classmethod
    def initialize(cls, config):
        """
        初始化日志系统

        Args:
            config: LoggingConfig对象
        """
        if cls._initialized:
            return cls._instance

        # 创建logger
        logger = logging.getLogger('HtmlDoc2PDF')
        logger.setLevel(getattr(logging, config.level.upper()))
        logger.handlers.clear()  # 清除已有的handlers

        # 文件handler
        if config.file:
            # 创建日志目录
            log_path = Path(config.file)

            # 如果包含{timestamp},替换为当前时间
            if '{timestamp}' in str(log_path):
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                log_path = Path(str(log_path).replace('{timestamp}', timestamp))

            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(log_path, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)  # 文件记录所有级别

            # 文件格式(不带颜色)
            file_format = config.format.replace('{time}', '%(asctime)s')
            file_format = file_format.replace('{level}', '%(levelname)-8s')
            file_format = file_format.replace('{process}', 'PID:%(process)d')
            file_format = file_format.replace('{message}', '%(message)s')

            file_formatter = logging.Formatter(file_format, datefmt='%Y-%m-%d %H:%M:%S')
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

        # 控制台handler
        if config.console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, config.level.upper()))

            # 控制台格式(带颜色)
            console_format = config.format.replace('{time}', '%(asctime)s')
            console_format = console_format.replace('{level}', '%(levelname)-8s')
            console_format = console_format.replace('{process}', 'PID:%(process)d')
            console_format = console_format.replace('{message}', '%(message)s')

            console_formatter = ColoredFormatter(console_format, datefmt='%H:%M:%S')
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)

        cls._instance = logger
        cls._initialized = True

        return logger

    @classmethod
    def get_logger(cls) -> logging.Logger:
        """获取logger实例"""
        if cls._instance is None:
            raise RuntimeError("Logger未初始化,请先调用Logger.initialize()")
        return cls._instance


def get_logger() -> logging.Logger:
    """获取logger实例的快捷函数"""
    return Logger.get_logger()


# 多进程日志辅助函数
def setup_worker_logger(config):
    """
    在worker进程中设置logger

    Args:
        config: LoggingConfig对象
    """
    Logger.initialize(config)


if __name__ == "__main__":
    # 测试代码
    from src.config import LoggingConfig

    print("测试日志模块...")

    # 创建配置
    config = LoggingConfig(
        level="DEBUG",
        file="./logs/test_{timestamp}.log",
        console=True,
        format="[{time}] [{level}] {message}"
    )

    # 初始化logger
    Logger.initialize(config)
    logger = get_logger()

    # 测试不同级别的日志
    logger.debug("这是一条DEBUG消息")
    logger.info("这是一条INFO消息")
    logger.warning("这是一条WARNING消息")
    logger.error("这是一条ERROR消息")

    print(f"\n日志已写入: {config.file}")
    print("日志模块测试完成!")
