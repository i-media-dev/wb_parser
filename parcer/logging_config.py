import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime as dt


def setup_logging():
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)

    log_filename = dt.now().strftime('%Y-%m-%d.log')
    log_filepath = os.path.join(log_dir, log_filename)

    handler = RotatingFileHandler(
        log_filepath,
        maxBytes=50000000,
        backupCount=3,
        encoding='utf-8'
    )

    logging.basicConfig(
        level=logging.DEBUG,
        format=(
            '%(asctime)s, '
            '%(filename)s, '
            '%(funcName)s, '
            '%(levelname)s, '
            '%(message)s, '
            '%(name)s'
        ),
        handlers=[handler]
    )
