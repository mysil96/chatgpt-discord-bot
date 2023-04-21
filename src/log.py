#log.py
import os
import logging
import logging.handlers


class CustomFormatter(logging.Formatter):

    LEVEL_COLORS = [
        (logging.DEBUG, '\x1b[37;1m'),
        (logging.INFO, '\x1b[34;1m'),
        (logging.WARNING, '\x1b[33;1m'),
        (logging.ERROR, '\x1b[31m'),
        (logging.CRITICAL, '\x1b[41m'),
    ]
    FORMATS = {
        level: logging.Formatter(
            f'%(asctime)s {color}%(levelname)-8s\x1b[0m %(name)s -> %(message)s',
            '%Y-%m-%d %H:%M:%S'
        )
        for level, color in LEVEL_COLORS
    }
    
    FILE_FORMAT = logging.Formatter(
        '%(asctime)s %(levelname)-8s %(name)s -> %(message)s',
        '%Y-%m-%d %H:%M:%S'
    )

    def format(self, record):
        formatter = self.FORMATS.get(record.levelno)
        if formatter is None:
            formatter = self.FORMATS[logging.DEBUG]

        if record.exc_info:
            text = formatter.formatException(record.exc_info)
            record.exc_text = f'\x1b[31m{text}\x1b[0m'

        output = formatter.format(record)

        record.exc_text = None
        return output


def setup_logger() -> logging.Logger:
    library, _, _ = __name__.partition('.')
    logger = logging.getLogger(library)
    logger.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(CustomFormatter())
    log_handler = logging.handlers.RotatingFileHandler(
        filename='ChatGPT_Discord_Bot.log',
        encoding='utf-8',
        maxBytes=32 * 1024 * 1024,
        backupCount=2,
    )
    log_handler.setFormatter(CustomFormatter.FILE_FORMAT)
    logger.addHandler(log_handler)
    logger.addHandler(console_handler)

    return logger

logger = setup_logger()