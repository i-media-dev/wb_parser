import functools
import json
import logging
import time
from datetime import datetime as dt
from parser.constants import DATE_FORMAT, TIME_FORMAT
from parser.db_config import config
from parser.logging_config import setup_logging

import mysql.connector

setup_logging()


def time_of_function(func):
    """
    Декоратор для измерения времени выполнения функции.

    Замеряет время выполнения декорируемой функции и логирует результат
    в секундах и минутах. Время округляется до 3 знаков после запятой
    для секунд и до 2 знаков для минут.

    Args:
        func (callable): Декорируемая функция, время выполнения которой
        нужно измерить.

    Returns:
        callable: Обёрнутая функция с добавленной функциональностью
        замера времени.
    """
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = round(time.time() - start_time, 3)
        logging.info(
            f'Функция {func.__name__} завершила работу. '
            f'Время выполнения - {execution_time} сек. '
            f'или {round(execution_time / 60, 2)} мин.'
        )
        return result
    return wrapper


def connection_db(func):
    """
    Декоратор для подключения к базе данных.

    Подключается к базе данных, обрабатывает ошибки в процессе подключения,
    логирует все успешные/неуспешные действия, вызывает функцию, выполняющую
    действия в базе данных и закрывает подключение.

    Args:
        func (callable): Декорируемая функция, которая выполняет
        действия с базой данных.

    Returns:
        callable: Обёрнутая функция с добавленной функциональностью
        подключения к базе данных и логирования.
    """
    def wrapper(*args, **kwargs):
        connection = None
        cursor = None
        try:
            connection = mysql.connector.connect(**config)
            cursor = connection.cursor()
            kwargs['cursor'] = cursor
            result = func(*args, **kwargs)
            connection.commit()
            return result
        except Exception as e:
            if connection:
                connection.rollback()
            logging.error(f'Ошибка в {func.__name__}: {str(e)}', exc_info=True)
            raise
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()
    return wrapper


def time_of_script(func):
    """Универсальный декоратор для логирования выполнения."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_ts = time.time()
        date_str = dt.now().strftime(DATE_FORMAT)
        time_str = dt.now().strftime(TIME_FORMAT)
        print(f'Функция main начала работу {date_str} в {time_str}')

        try:
            result = func(*args, **kwargs)
            status = 'SUCCESS'
            error_type = error_message = None
        except Exception as e:
            status = 'ERROR'
            error_type, error_message = type(e).__name__, str(e)
            result = None

        exec_time_min = round((time.time() - start_ts) / 60, 2)
        exec_time_sec = round(time.time() - start_ts, 3)
        print(
            'Функция main завершила '
            f'работу в {dt.now().strftime(TIME_FORMAT)}.'
            f' Время выполнения - {exec_time_min} мин. '
        )

        log_record = {
            "DATE": date_str,
            "STATUS": status,
            "FUNCTION_NAME": func.__name__,
            "EXECUTION_TIME": exec_time_sec,
            "ERROR_TYPE": error_type,
            "ERROR_MESSAGE": error_message,
            "ENDLOGGING": 1
        }

        logging.info(json.dumps(log_record, ensure_ascii=False))

        if status == "ERROR":
            raise

        return result

    return wrapper
