import logging

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