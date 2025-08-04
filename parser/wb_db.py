from pprint import pprint
import logging
from collections import defaultdict
from datetime import datetime as dt
import mysql.connector
from parser.constants import (
    CREATE_DATES_TABLE,
    CREATE_PRODUCTS_TABLE,
    CREATE_SALES_TABLE,
    CREATE_STOCKS_TABLE,
    NAME_OF_SHOP,
    TWO_WEEK
)
from parser.db_config import config
from parser.decorators import connection_db
from parser.exceptions import RefTableError, TableNameError, TypeDataError
from parser.logging_config import setup_logging


setup_logging()


class WbDataBaseClient:
    """Класс, который работает с базой данных."""

    @staticmethod
    def _allowed_tables() -> list:
        """
        Защищенный метод возвращает список существующих
        таблиц в базе данных.
        """
        connection = mysql.connector.connect(**config)
        try:
            with connection.cursor() as cursor:
                cursor.execute("SHOW TABLES")
                return [table[0] for table in cursor.fetchall()]
        finally:
            connection.close()

    @staticmethod
    @connection_db
    def _create_table_if_not_exist(
        type_table: str,
        type_data: str,
        shop_name: str = NAME_OF_SHOP,
        ref_dates_table: str = '',
        ref_products_table: str = '',
        connection=None,
        cursor=None

    ):
        """
        Защищенный метод создает таблицу в базе данных если ее не существует.
        Если таблица есть в базе данных возварщает ее имя.
        """
        table_name = f'{type_table}_{type_data}_{shop_name}'
        if table_name in WbDataBaseClient._allowed_tables():
            logging.info(f'Таблица {table_name} найдена в базе')
            return table_name

        table_config = {
            'dates': {
                'template': CREATE_DATES_TABLE,
                'requires_refs': False,
                'format_args': {'table_name': table_name}
            },
            'products': {
                'template': CREATE_PRODUCTS_TABLE,
                'requires_refs': False,
                'format_args': {'table_name': table_name}
            },
            'sales': {
                'template': CREATE_SALES_TABLE,
                'requires_refs': True,
                'format_args': {
                    'table_name': table_name,
                    'ref_dates_table': ref_dates_table,
                    'ref_products_table': ref_products_table
                }
            },
            'stocks': {
                'template': CREATE_STOCKS_TABLE,
                'requires_refs': True,
                'format_args': {
                    'table_name': table_name,
                    'ref_dates_table': ref_dates_table,
                    'ref_products_table': ref_products_table
                }
            }
        }

        if type_data not in table_config:
            logging.error(f'Неразрешенный тип данных таблицы: {type_data}')
            raise TypeDataError

        config = table_config[type_data]

        if config['requires_refs'] and not (ref_dates_table and ref_products_table):
            logging.error('Отсутствуют таблицы для ссылки')
            raise RefTableError
        create_table_query = config['template'].format(**config['format_args'])
        cursor.execute(create_table_query)
        logging.info(f'Таблица {table_name} успешно создана')
        return table_name

    def parse_product_data(
        self,
        data: list[dict],
        date_str: str
    ) -> list[dict]:
        """
        Метод обрабатывает полученный словарь,
        вытягивает и группирует нужные данные.
        """
        stocks = []

        for item in data:
            stocks.append(
                {
                    'дата': date_str,
                    'наименование': item.get('name', '').strip('""'),
                    'артикул': item.get('nmID', ''),
                    'остаток': item.get('metrics', {}).get('stockCount', 0)
                }
            )
        return stocks

    def parse_avg_sales(self, data: list[dict], date_str: str) -> list[dict]:
        """
        Метод обрабатывает полученный словарь,
        вытягивает и группирует нужные данные.
        """
        avg_sales = []
        sales_by_article = defaultdict(int)

        for item in data:
            if item.get('isRealization') and not item.get('isCancel'):
                article = item['nmId']
                sales_by_article[article] += 1

        for article, total_sales in sales_by_article.items():
            avg_per_day = total_sales // TWO_WEEK
            avg_sales.append({
                'дата': date_str,
                'артикул': article,
                'среднее значение': avg_per_day
            })
        return avg_sales

    def validate_date_db(self, date_str: str) -> tuple:
        """
        Метод обрабатывает дату, раскладывает ее на
        день, месяц, год и день недели. Готовит SQL-запрос и параметры
        для сохранения в базу данных.
        """
        date = dt.strptime(date_str, '%Y-%m-%d').date()
        day = date.day
        month = date.month
        year = date.year
        weekday = date.isoweekday()

        table_name = self._create_table_if_not_exist('catalog', 'dates')

        query = f'''
            INSERT INTO {table_name} (
            full_date,
            day,
            month,
            year,
            day_of_week
            )
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE id = id
        '''
        return query, (date, day, month, year, weekday)

    def validate_products_db(self, data: list) -> tuple:
        """
        Метод принимает обработанные данные,
        полученные из метода parse_product_data.
        Готовит SQL-запрос и параметры для сохранения в базу данных.
        """
        table_name = self._create_table_if_not_exist('catalog', 'products')

        query = f'''
            INSERT INTO {table_name} (article, name)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE
            name = VALUES(name)
        '''
        params = [(item['артикул'], item['наименование']) for item in data]
        return query, params

    def validate_stocks_db(self, data: list) -> tuple:
        """
        Метод принимает обработанные данные,
        полученные из метода parse_product_data.
        Готовит SQL-запрос и параметры для сохранения в базу данных.
        """
        date = dt.strptime(data[0].get('дата'), "%Y-%m-%d").date()
        table_name = self._create_table_if_not_exist(
            'reports',
            'stocks',
            ref_dates_table=f'catalog_dates_{NAME_OF_SHOP}',
            ref_products_table=f'catalog_products_{NAME_OF_SHOP}'
        )

        query = f'''
            INSERT INTO {table_name} (date, article, stock)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
            stock = VALUES(stock)
        '''
        params = [(date, item['артикул'], item['остаток']) for item in data]
        return query, params

    def validate_sales_db(self, data: list) -> tuple:
        """
        Метод принимает обработанные данные,
        полученные из метода parse_avg_sales.
        Готовит SQL-запрос и параметры для сохранения в базу данных.
        """
        date = dt.strptime(data[0].get('дата'), "%Y-%m-%d").date()
        table_name = self._create_table_if_not_exist(
            'reports',
            'sales',
            ref_dates_table=f'catalog_dates_{NAME_OF_SHOP}',
            ref_products_table=f'catalog_products_{NAME_OF_SHOP}'
        )

        query = f'''
            INSERT INTO {table_name} (date, article, sale)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
            sale = VALUES(sale)
        '''
        params = [
            (date, item['артикул'], item['среднее значение']) for item in data
        ]
        return query, params

    @connection_db
    def save_to_db(
        self,
        query_data: tuple,
        connection=None,
        cursor=None
    ) -> None:
        """Метод сохраняется обработанные данные в базу данных."""
        query, params = query_data
        if isinstance(params, list):
            cursor.executemany(query, params)
        else:
            cursor.execute(query, params)
        connection.commit()
        logging.info('✅ Данные успешно сохранены!')

    @connection_db
    def clean_db(self, connection=None, cursor=None, **tables: bool) -> None:
        """
        Метод очищает базу данных. В tables передаются имеющиеся в базе данных
        таблицы, которые нужно удалить, учитывая связь таблиц по PK и FK
        (таблицы reports_sales и reports_stocks удаляются автоматически
        если удалить catalog_products).
        """
        for table in tables:
            if table not in WbDataBaseClient._allowed_tables():
                logging.error('Такой таблицы не существует.')
                raise TableNameError()
            delete_query = f'DELETE FROM {table}'
            cursor.execute(delete_query)
            connection.commit()
            logging.debug(
                f'Таблица `{table}` очищена. '
                f'Удалено строк: {cursor.rowcount}'
            )
