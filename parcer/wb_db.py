from datetime import datetime as dt
import logging
import mysql.connector

from decorators import connection_db
from logging_config import setup_logging

setup_logging()


class WbDataBaseClient:

    def validate_date_db(self, date_str):
        date = dt.strptime(date_str, '%Y-%m-%d').date()
        day = date.day
        month = date.month
        year = date.year
        weekday = date.isoweekday()

        query = '''
            INSERT INTO dates (full_date, day, month, year, day_of_week)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            day_of_week = VALUES(day_of_week)
        '''
        return query, (date, day, month, year, weekday)

    def validate_products_db(self, data):
        query = '''
            INSERT INTO products (article, name)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE
            name = VALUES(name)
        '''
        params = [(item['артикул'], item['наименование']) for item in data]
        return query, params

    def validate_stocks_db(self, data):
        date = dt.strptime(data[0].get('дата'), "%Y-%m-%d").date()

        query = '''
            INSERT INTO stocks (date, article, stock)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
            stock = VALUES(stock)
        '''
        params = [(date, item['артикул'], item['остаток']) for item in data]
        return query, params

    def validate_sales_db(self, data):
        date = dt.strptime(data[0].get('дата'), "%Y-%m-%d").date()

        query = '''
            INSERT INTO sales (date, article, sale)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
            sale = VALUES(sale)
        '''
        params = [(date, item['артикул'], item['среднее значение'])
                  for item in data]
        return query, params

    @connection_db
    def save_to_db(self, query_data, connection=None, cursor=None):
        query, params = query_data
        if isinstance(params, list):
            cursor.executemany(query, params)
        else:
            cursor.execute(query, params)
        connection.commit()
        logging.info('✅ Данные успешно сохранены!')

    @connection_db
    def clean_db(self, connection=None, cursor=None, **tables):
        allowed_tables = ['dates', 'products', 'stocks', 'sales']

        for table in tables:
            if table not in allowed_tables:
                logging.error(
                    'Такой таблицы не существует. '
                    f'Существующие таблицы в базе данных: {allowed_tables}'
                )
                raise ValueError('Invalid table name')
            try:
                delete_query = f'DELETE FROM {table}'
                cursor.execute(delete_query)
                connection.commit()
                logging.debug(
                    f'Таблица `{table}` очищена. '
                    f'Удалено строк: {cursor.rowcount}'
                )
            except mysql.connector.Error as table_err:
                logging.error(
                    f'❌ Ошибка при очистке таблицы {table}: {table_err}'
                )
                connection.rollback()
