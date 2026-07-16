"""
Signal · 结构化日志

用法：
    from api.services.logger import logger

    logger.info("用户登录", user_id="abc")
    logger.error("数据库连接失败", exc_info=True)
    logger.warning("请求超时",  url="/api/search", elapsed_ms=5200)

环境变量：
    LOG_LEVEL=DEBUG|INFO|WARNING|ERROR  (默认 INFO)
    LOG_FORMAT=json|text                (默认 text)
"""

import os
import sys
import json
import logging
from datetime import datetime, timezone


class StructuredFormatter(logging.Formatter):
    """结构化 JSON 日志格式化器"""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)
        # 合并 extra 参数
        for key, value in getattr(record, "extra_fields", {}).items():
            log_entry[key] = value
        return json.dumps(log_entry, ensure_ascii=False)


def setup_logger(name: str = "signal") -> logging.Logger:
    """配置并返回结构化 logger"""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_format = os.getenv("LOG_FORMAT", "text").lower()

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level, logging.INFO))
    logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)

    if log_format == "json":
        handler.setFormatter(StructuredFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            "[%(levelname)s] %(name)s: %(message)s"
        ))

    logger.addHandler(handler)
    return logger


# 全局 logger 实例
logger = setup_logger()


class LoggerMixin:
    """为类注入 logger 的 mixin"""

    @property
    def logger(self) -> logging.Logger:
        return logging.getLogger(f"{__name__}.{self.__class__.__name__}")
