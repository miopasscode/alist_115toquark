import logging
import os
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler

def setup_logger(log_dir: str = "logs"):
    """配置日志
    
    Args:
        log_dir: 日志目录路径，默认为 "logs"
    """
    # 确保日志目录存在
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 生成基础日志文件名
    log_file = os.path.join(log_dir, "copy_task.log")
    
    # 创建日志格式器
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 创建按天轮转的文件处理器
    file_handler = TimedRotatingFileHandler(
        filename=log_file,
        when='midnight',          # 每天午夜切换新文件
        interval=1,               # 间隔为1天
        backupCount=30,           # 保留30天的日志
        encoding='utf-8',
        delay=False
    )
    file_handler.setFormatter(formatter)
    file_handler.suffix = "%Y%m%d.log"  # 日志文件后缀格式
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # 获取根日志记录器
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # 清除可能存在的旧处理器
    logger.handlers.clear()
    
    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger 