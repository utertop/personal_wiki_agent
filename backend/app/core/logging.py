import logging


def get_logger(name: str) -> logging.Logger:
    """按模块名获取 logger，统一后续日志入口。"""
    return logging.getLogger(name)
