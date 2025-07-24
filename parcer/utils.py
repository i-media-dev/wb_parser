import logging
import os
from datetime import datetime as dt, timedelta

from dotenv import load_dotenv

from logging_config import setup_logging
from wb_db import WbDataBaseClient
from wb_tools import WbAnalyticsClient

setup_logging()


def initialize_components():
    '''Инициализирует все необходимые компоненты.'''
    load_dotenv()
    token = os.getenv('TOKEN')
    client = WbAnalyticsClient(token)
    db_client = WbDataBaseClient()
    date_str = (dt.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    return token, db_client, client, date_str


def fetch_data(client, date_str):
    '''Получает данные с API.'''
    all_sales = client.get_all_sales_reports(date_str)
    all_data = client.get_all_stock_reports(
        start_date=date_str, end_date=date_str)
    logging.info(f'\n✅ Получено записей по остаткам: {len(all_data)}')
    logging.info(
        f'\n✅ Получено записей по продажам за 2 недели: {len(all_sales)}')
    return all_sales, all_data


def process_data(client, all_sales, all_data, date_str):
    '''Обрабатывает данные перед сохранением в бд.'''
    formatter_sales = client.parce_avg_sales(all_sales, date_str)
    formatter_data = client.parce_product_data(all_data, date_str)
    return formatter_sales, formatter_data


def save_to_database(db_client, date_str, formatter_data, formatter_sales):
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
    client,
    date_str,
    all_data,
    all_sales,
    formatter_sales,
    formatter_data
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
