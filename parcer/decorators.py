import time
import logging

from logging_config import setup_logging

setup_logging()


def time_of_function(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = round(time.time() - start_time, 3)
        logging.info(
            f'Функция {func.__name__} завершила работу. '
            f'Время выполнения - {execution_time} сек. '
            f'или {round(execution_time/60, 2)} мин.'
        )
        return result
    return wrapper
