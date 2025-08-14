import logging
from collections import defaultdict
from datetime import datetime as dt
from parser.constants import (
    CREATE_DATES_TABLE,
    CREATE_PRODUCTS_TABLE,
    CREATE_SALES_TABLE,
    CREATE_STOCKS_TABLE,
    INSERT_DATES,
    INSERT_PRODUCTS,
    INSERT_SALES,
    INSERT_STOCKS,
    NAME_OF_SHOP,
    TWO_WEEK
)
from parser.decorators import connection_db
from parser.exceptions import RefTableError, TableNameError, TypeDataError
from parser.logging_config import setup_logging

setup_logging()


class WbDataBaseClient:
    """Класс, который работает с базой данных."""

    def __init__(self, shop_name: str = NAME_OF_SHOP):
        self.shop_name = shop_name

    @connection_db
    def _allowed_tables(self, cursor=None) -> list:
        """
        Защищенный метод возвращает список существующих
        таблиц в базе данных.
        """
        cursor.execute('SHOW TABLES')
        return [table[0] for table in cursor.fetchall()]

    @connection_db
    def _create_table_if_not_exist(
        self,
        type_table: str,
        type_data: str,
        ref_dates_table: str = '',
        ref_products_table: str = '',
        cursor=None

    ):
        """
        Защищенный метод создает таблицу в базе данных если ее не существует.
        Если таблица есть в базе данных возварщает ее имя.
        """
        table_name = f'{type_table}_{type_data}_{self.shop_name}'
        if table_name in self._allowed_tables():
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

        if config['requires_refs'] and not (
            ref_dates_table and ref_products_table
        ):
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
        query = INSERT_DATES.format(table_name=table_name)
        return query, (date, day, month, year, weekday)

    def validate_products_db(self, data: list) -> tuple:
        """
        Метод принимает обработанные данные,
        полученные из метода parse_product_data.
        Готовит SQL-запрос и параметры для сохранения в базу данных.
        """
        table_name = self._create_table_if_not_exist('catalog', 'products')
        query = INSERT_PRODUCTS.format(table_name=table_name)
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
            ref_dates_table=f'catalog_dates_{self.shop_name}',
            ref_products_table=f'catalog_products_{self.shop_name}'
        )
        query = INSERT_STOCKS.format(table_name=table_name)
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
            ref_dates_table=f'catalog_dates_{self.shop_name}',
            ref_products_table=f'catalog_products_{self.shop_name}'
        )
        query = INSERT_SALES.format(table_name=table_name)
        params = [
            (date, item['артикул'], item['среднее значение']) for item in data
        ]
        return query, params

    @connection_db
    def save_to_db(
        self,
        query_data: tuple,
        cursor=None
    ) -> None:
        """Метод сохраняется обработанные данные в базу данных."""
        query, params = query_data
        if isinstance(params, list):
            cursor.executemany(query, params)
        else:
            cursor.execute(query, params)
        logging.info('✅ Данные успешно сохранены!')

    @connection_db
    def clean_db(self, cursor=None, **tables: bool) -> None:
        """
        Метод очищает базу данных. В tables передаются имеющиеся в базе данных
        таблицы, которые нужно удалить, учитывая связь таблиц по PK и FK
        (таблицы reports_sales и reports_stocks удаляются автоматически
        если удалить catalog_products).
        """
        try:
            existing_tables = self._allowed_tables()
            for table_name, should_clean in tables.items():
                if should_clean and table_name in existing_tables:
                    cursor.execute(f'DELETE FROM {table_name}')
                    logging.info(f'Таблица {table_name} очищена')
                else:
                    raise TableNameError(
                        f'В базе данных отсутствует таблица {table_name}.'
                    )
        except Exception as e:
            logging.error(f'Ошибка очистки: {e}')
            raise
