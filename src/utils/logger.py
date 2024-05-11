import logging
from logging.config import dictConfig
from typing import Any, Dict


def get_logger_config(log_level: str) -> Dict[str, Any]:
    return {
        "version": 1,
        "formatters": {
            "default": {
                "format": '{"logtime": "%(asctime)s.%(msecs)03d", '
                '"loglevel": "%(levelname)s", '
                '"logger": "%(name)s", '
                '"extra": {"filename": "%(filename)s", '
                '"funcName": "%(funcName)s", "lineno": %(lineno)d, "logmessage": %(message)s}}',
                "datefmt": "%Y-%m-%d %H:%M:%S",
            }
        },
        "handlers": {
            "console": {
                "level": log_level,
                "class": "logging.StreamHandler",
                "formatter": "default",
            }
        },
        "loggers": {
            "main": {"handlers": ("console",), "level": "DEBUG", "propagate": True},
        },
    }


def init_logger(log_level: str):
    log_conf = get_logger_config(log_level=log_level)
    dictConfig(log_conf)


global_logger = logging.getLogger("main")
