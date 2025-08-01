import logging
from collections import defaultdict
from datetime import datetime as dt
import mysql.connector
from parser.constants import ALLOWED_TABLES, TWO_WEEK
from parser.decorators import connection_db
from parser.exceptions import RefTableError, TypeDataError
from parser.logging_config import setup_logging


setup_logging()


class WbDataBaseClient:
    """Класс, который работает с базой данных."""

    ALLOWED_TABLES_IN_DB = ALLOWED_TABLES

    @staticmethod
    @connection_db
    def _create_table_if_not_exist(
        type_table: str,
        type_data: str,
        shop_name: str,
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
        if table_name not in WbDataBaseClient.ALLOWED_TABLES_IN_DB:
            try:
                if type_data == 'dates':
                    create_table_query = f'''
                        CREATE TABLE IF NOT EXISTS {table_name} (
                        `id` int(11) NOT NULL AUTO_INCREMENT,
                        `full_date` date NOT NULL,
                        `day` int(11) NOT NULL,
                        `month` int(11) NOT NULL,
                        `year` int(11) NOT NULL,
                        `day_of_week` int(11) NOT NULL,
                        PRIMARY KEY (`id`),
                        UNIQUE KEY `unique_date_combo` (
                        `full_date`,`day`,`month`,`year`
                        ),
                        KEY `full_date` (`full_date`),
                        KEY `year` (`year`,`month`),
                        KEY `year_2` (`year`,`month`,`day`)
                    ) ENGINE=InnoDB AUTO_INCREMENT=88 DEFAULT CHARSET=utf8;
                    '''
                    cursor.execute(create_table_query)
                    logging.info(f'Таблица {table_name} успешно создана')
                    WbDataBaseClient.ALLOWED_TABLES_IN_DB.append(table_name)
                    return table_name
                if type_data == 'products':
                    create_table_query = f'''
                        CREATE TABLE IF NOT EXISTS {table_name} (
                        `id` int(11) NOT NULL AUTO_INCREMENT,
                        `article` bigint(20) unsigned NOT NULL,
                        `name` varchar(255) NOT NULL,
                        PRIMARY KEY (`id`),
                        UNIQUE KEY `article` (`article`),
                        FULLTEXT KEY `name` (`name`)
                    ) ENGINE=InnoDB AUTO_INCREMENT=247 DEFAULT CHARSET=utf8;
                    '''
                    cursor.execute(create_table_query)
                    logging.info(f'Таблица {table_name} успешно создана')
                    WbDataBaseClient.ALLOWED_TABLES_IN_DB.append(table_name)
                    return table_name
                if type_data == 'sales':
                    if ref_products_table != '' and ref_dates_table != '':
                        create_table_query = f'''
                            CREATE TABLE IF NOT EXISTS {table_name} (
                            `date` date NOT NULL,
                            `article` bigint(20) unsigned NOT NULL,
                            `sale` int(11) DEFAULT '0',
                            PRIMARY KEY (`date`,`article`),
                            KEY `article` (`article`),
                            CONSTRAINT `fk_sales_date` FOREIGN KEY (
                            `date`
                            ) REFERENCES {ref_dates_table} (
                            `full_date`
                            ) ON DELETE CASCADE ON UPDATE CASCADE,
                            CONSTRAINT `fk_sales_product` FOREIGN KEY (
                            `article`
                            ) REFERENCES {ref_products_table} (
                            `article`
                            ) ON UPDATE CASCADE
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8;
                        '''
                        cursor.execute(create_table_query)
                        logging.info(f'Таблица {table_name} успешно создана')
                        WbDataBaseClient.ALLOWED_TABLES_IN_DB.append(
                            table_name)
                        return table_name
                    else:
                        logging.error('Отсутствует таблицы для ссылки')
                        raise RefTableError
                if type_data == 'stocks':
                    if ref_products_table != '' and ref_dates_table != '':
                        create_table_query = f'''
                            CREATE TABLE IF NOT EXISTS {table_name} (
                            `date` date NOT NULL,
                            `article` bigint(20) unsigned NOT NULL,
                            `stock` int(10) unsigned NOT NULL DEFAULT '0',
                            PRIMARY KEY (`date`,`article`),
                            KEY `article` (`article`),
                            CONSTRAINT `fk_stocks_date` FOREIGN KEY (
                            `date`
                            ) REFERENCES {ref_dates_table} (
                            `full_date`
                            ) ON DELETE CASCADE ON UPDATE CASCADE,
                            CONSTRAINT `fk_stocks_product` FOREIGN KEY (
                            `article`
                            ) REFERENCES {ref_products_table} (
                            `article`
                            ) ON UPDATE CASCADE
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8;
                        '''
                        cursor.execute(create_table_query)
                        logging.info(f'Таблица {table_name} успешно создана')
                        WbDataBaseClient.ALLOWED_TABLES_IN_DB.append(
                            table_name)
                        return table_name
                    else:
                        logging.error('Отсутствует таблицы для ссылки')
                        raise RefTableError
                else:
                    logging.error(
                        f'Неразрешенный тип данных таблицы: {type_data}')
                    raise TypeDataError
            except mysql.connector.Error as table_err:
                logging.error(
                    f'❌ Ошибка создания таблицы: {table_err}'
                )
        else:
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

        table_name = WbDataBaseClient._create_table_if_not_exist(
            'catalog', 'dates', 'loweis'
        )
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
        table_name = WbDataBaseClient._create_table_if_not_exist(
            'catalog', 'products', 'loweis'
        )
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
        table_name = WbDataBaseClient._create_table_if_not_exist(
            'reports', 'stocks', 'loweis'
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
        table_name = WbDataBaseClient._create_table_if_not_exist(
            'reports', 'sales', 'loweis'
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
        try:
            query, params = query_data
            if isinstance(params, list):
                cursor.executemany(query, params)
            else:
                cursor.execute(query, params)
            connection.commit()
            logging.info('✅ Данные успешно сохранены!')
        except mysql.connector.Error as table_err:
            logging.error(
                f'❌ Ошибка сохранения данных: {table_err}'
            )
            connection.rollback()

    @connection_db
    def clean_db(self, connection=None, cursor=None, **tables: bool) -> None:
        """
        Метод очищает базу данных. В tables передаются имеющиеся в базе данных
        таблицы, которые нужно удалить, учитывая связь таблиц по PK и FK
        (таблицы reports_sales и reports_stocks удаляются автоматически
        если удалить catalog_products).
        """
        for table in tables:
            if table not in self.ALLOWED_TABLES_IN_DB:
                logging.error(
                    'Такой таблицы не существует. '
                    f'Существующие таблицы в базе данных: {
                        self.ALLOWED_TABLES_IN_DB
                    }'
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
