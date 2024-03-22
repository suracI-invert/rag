from multiprocessing import Queue
from threading import Thread
from queue import Empty
from collections import deque
import logging
import yaml

class CustomFormatter(logging.Formatter):
    GREY = "\x1b[38;20m"
    BLUE = "\x1b[38;5;39m"
    YELLOW = "\x1b[33;20m"
    RED = "\x1b[31;20m"
    BOLD_RED = "\x1b[31;1m"
    RESET = "\x1b[0m"

    DATEFORMAT = '%Y-%m-%d %H:%M:%S'

    FORMAT = "┌───{asctime} |{levelname:<8s} |{processName:<15s} | Module {module} - Line {lineno}" + \
            "\n└─▶ {message}"

    FORMATS = {
        logging.DEBUG: GREY + FORMAT + RESET,
        logging.INFO: BLUE + FORMAT + RESET,
        logging.WARNING: YELLOW + FORMAT + RESET,
        logging.ERROR: RED + FORMAT + RESET,
        logging.CRITICAL: BOLD_RED + FORMAT + RESET,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, style='{', datefmt=self.DATEFORMAT)
        if record.exc_info:
            exc = super().formatException(record.exc_info)
            exc = f'└─▶ {exc}'
            record.exc_text = exc
        s = formatter.format(record)
        return s
    
def load_config(fname):
    with open(f'./config/{fname}') as f:
        loaded_config = yaml.safe_load(f)
    return loaded_config

class MultiProcessesLogger(Thread):
    def __init__(self, logger_queue: Queue, logger_name: str = 'uvicorn.error'):
        super().__init__(name=logger_name)
        self.logger = logging.getLogger(logger_name)
        self.msg_cache = deque()
        self.__q = logger_queue

        self.__quit = False

        self.map_fn = {
            'info': self.logger.info,
            'debug': self.logger.debug,
            'exception': self.logger.exception,
            'warning': self.logger.exception,
            'error': self.logger.error,
            'critical': self.logger.critical
        }

    def run(self):
        while True:
            if self.__quit:
                break
            try:
                levelno, msg = self.__q.get(block=False)
            except Empty:
                pass
            else:
                self.msg_cache.appendleft((levelno, msg))

            if len(self.msg_cache) > 0:
                levelno, msg = self.msg_cache.pop()
                self.map_fn[levelno](msg)
        self.logger.info('Logger closed')
    
    def close(self):
        self.__quit = True
        self.join()