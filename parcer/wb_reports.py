import os
from dotenv import load_dotenv
import requests
import logging
import time

from logging_config import setup_logging
from wb_tools import get_yesterday_date_str, WbAnalyticsClient

setup_logging()


def main():
    '''Основная логика программы.'''

    load_dotenv()
    token = os.getenv('TOKEN')

    if not token:
        logging.error('Файл сохранен.')
        return

    client = WbAnalyticsClient(token)
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
    except requests.RequestException as e:

        logging.error(f'❌ Ошибка запроса: {e}')


if __name__ == '__main__':
    start_time = time.time()
    print('Функция main начала работу')
    logging.info('Функция main начала работу')
    main()
    execution_time = round(time.time() - start_time, 3)
    logging.info(
        f'Функция main завершила работу. Время выполнения - {execution_time} сек. или {round(execution_time/60, 2)} мин.')
    print(
        f'Функция main завершила работу. Время выполнения - {execution_time} сек. или {round(execution_time/60, 2)} мин.')
