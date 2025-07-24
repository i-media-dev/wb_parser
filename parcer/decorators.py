import logging
import time

import mysql.connector

from db_config import config
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


def connection_db(func):
    def wrapper(*args, **kwargs):
        connection = None
        cursor = None
        result = None
        try:
            connection = mysql.connector.connect(**config)
            cursor = connection.cursor()
            logging.debug('✅ Успешное подключение к базе данных!')
            kwargs['connection'] = connection
            kwargs['cursor'] = cursor
            result = func(*args, **kwargs)
        except mysql.connector.Error as err:
            logging.error(f'❌ Ошибка: {err}')
            if 'connection' in locals():
                connection.rollback()
        finally:
            if cursor is not None:
                cursor.close()
            if connection is not None and connection.is_connected():
                connection.close()
                logging.debug('Соединение закрыто.')
        return result
    return wrapper
