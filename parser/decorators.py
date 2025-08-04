import logging
import time

import mysql.connector
from parser.db_config import config
from parser.logging_config import setup_logging

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
            if 'connection' not in kwargs or kwargs['connection'] is None:
                connection = mysql.connector.connect(**config)
                cursor = connection.cursor()
                kwargs['connection'] = connection
                kwargs['cursor'] = cursor
                logging.debug('✅ Создано новое подключение к БД')
            else:
                logging.debug('Используется существующее подключение')
            result = func(*args, **kwargs)
            if connection:
                connection.commit()
            return result
        except Exception as e:
            logging.error(
                f'❌ Ошибка в {func.__name__}: {str(e)}', exc_info=True)
            if connection:
                connection.rollback()
            raise
        finally:
            if cursor and 'cursor' not in kwargs:
                cursor.close()
            if connection and 'connection' not in kwargs:
                connection.close()
                logging.debug('Соединение закрыто')
    return wrapper
