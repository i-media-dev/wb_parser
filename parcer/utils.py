import logging
import os
from datetime import datetime as dt, timedelta

from dotenv import load_dotenv

from logging_config import setup_logging
from wb_db import WbDataBaseClient
from wb_tools import WbAnalyticsClient

setup_logging()


def initialize_components() -> tuple:
    '''Инициализирует все необходимые компоненты.'''
    load_dotenv()
    token = os.getenv('TOKEN')
    client = WbAnalyticsClient(token)
    db_client = WbDataBaseClient()
    date_str = (dt.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    return token, db_client, client, date_str


def fetch_data(client: WbAnalyticsClient, date_str: str) -> tuple:
    '''Получает данные с API.'''
    all_sales = client.get_all_sales_reports(date_str)
    all_data = client.get_all_stock_reports(
        start_date=date_str, end_date=date_str)
    logging.info(f'\n✅ Получено записей по остаткам: {len(all_data)}')
    logging.info(
        f'\n✅ Получено записей по продажам за 2 недели: {len(all_sales)}')
    return all_sales, all_data


def process_data(
    client: WbAnalyticsClient,
    all_sales: list,
    all_data: list,
    date_str: str
) -> tuple:
    '''Обрабатывает данные перед сохранением в базу данных.'''
    formatter_sales = client.parce_avg_sales(all_sales, date_str)
    formatter_data = client.parce_product_data(all_data, date_str)
    return formatter_sales, formatter_data


def save_to_database(
    db_client: WbDataBaseClient,
    date_str: str,
    formatter_data: list,
    formatter_sales: list
):
    '''Сохраняет данные в базу данных.'''
    queries = [
        db_client.validate_date_db(date_str),
        db_client.validate_products_db(formatter_data),
        db_client.validate_stocks_db(formatter_data),
        db_client.validate_sales_db(formatter_sales)
    ]

    for query in queries:
        db_client.save_to_db(query)


def export_data(
    client: WbAnalyticsClient,
    date_str: str,
    all_data: list,
    all_sales: list,
    formatter_sales: list,
    formatter_data: list
):
    '''Экспортирует данные в JSON и CSV.'''
    client.save_to_json(all_sales, date_str, 'avg_sales')
    client.save_to_json(all_data, date_str)

    client.save_to_csv(
        formatter_sales,
        date_str,
        ['дата', 'артикул', 'среднее значение'],
        'avg_sales'
    )
    client.save_to_csv(
        formatter_data,
        date_str,
        ['дата', 'наименование', 'артикул', 'остаток']
    )
