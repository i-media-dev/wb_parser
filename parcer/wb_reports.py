import os
from dotenv import load_dotenv
import requests
import logging
import time

from wb_db import WbDataBaseClient
from decorators import time_of_function
from logging_config import setup_logging
from wb_tools import get_yesterday_date_str, WbAnalyticsClient

setup_logging()


@time_of_function
def main():
    '''Основная логика программы.'''

    load_dotenv()
    token = os.getenv('TOKEN')

    if not token:
        logging.error('Файл сохранен.')
        return

    client = WbAnalyticsClient(token)
    db_client = WbDataBaseClient()
    date_str = get_yesterday_date_str()

    try:
        all_sales = client.get_all_sales_reports(date_str)
        all_data = client.get_all_stock_reports(
            start_date=date_str,
            end_date=date_str
        )

        logging.info(f'\n✅ Получено записей по остаткам: {len(all_data)}')
        logging.info(
            f'\n✅ Получено записей по продажам за 2 недели: {len(all_sales)}'
        )

        formatter_sales = client.parce_avg_sales(all_sales, date_str)
        formatter_data = client.parce_product_data(all_data, date_str)

        query_date = client.preparing_date_db(date_str)
        query_product = client.preparing_products_db(formatter_data)
        query_stock = client.preparing_stocks_db(formatter_data)
        query_sale = client.preparing_sales_db(formatter_sales)

        client.save_to_json(all_sales, date_str, 'avg_sales')
        client.save_to_json(all_data, date_str)

        client.save_to_db(query_date)
        client.save_to_db(query_product)
        client.save_to_db(query_stock)
        client.save_to_db(query_sale)

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
    except requests.RequestException as e:

        logging.error(f'❌ Ошибка запроса: {e}')


if __name__ == '__main__':
    start_time = time.time()
    print('Функция main начала работу')
    main()
    execution_time = round(time.time() - start_time, 3)
    print(
        'Функция main завершила работу. '
        f'Время выполнения - {execution_time} сек. '
        f'или {round(execution_time/60, 2)} мин.'
    )
