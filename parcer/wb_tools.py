import csv
from collections import defaultdict
import logging
import os
import json
import time
import requests
from datetime import datetime as dt, timedelta

from constants import DATA_PAGE_LIMIT, TWO_WEEK, WB_AVG_SALES, WB_PRODUCT_DATA
from decorators import time_of_function
from logging_config import setup_logging

setup_logging()


class WbAnalyticsClient:
    PRODUCT_DATA_URL = WB_PRODUCT_DATA
    AVG_SALES_URL = WB_AVG_SALES

    def __init__(self, token: str):
        if not token:

            logging.error('Токен не действителен или отсутствует.')

            raise ValueError('API token is required')
        self.token = token
        self.headers = {
            "Authorization": self.token,
            "Content-Type": "application/json"
        }

    def _get_sale_report(
            self,
            date: str,
    ):
        params = {
            "dateFrom": date
        }
        response = requests.get(
            self.AVG_SALES_URL,
            headers=self.headers,
            params=params
        )
        logging.info(
            f'\n[{response.status_code}]'
        )
        response.raise_for_status()
        return response.json()

    def _get_stock_report(
        self,
        start_date: str,
        end_date: str,
        offset: int = 0,
        limit: int = DATA_PAGE_LIMIT
    ) -> dict:
        payload = {
            "stockType": "",
            "currentPeriod": {
                "start": start_date,
                "end": end_date
            },
            "skipDeletedNm": True,
            "orderBy": {
                "field": "minPrice",
                "mode": "asc"
            },
            "limit": limit,
            "offset": offset,
            "availabilityFilters": [
                "deficient",
                "actual",
                "balanced",
                "nonActual",
                "nonLiquid",
                "invalidData"
            ]
        }

        response = requests.post(
            self.PRODUCT_DATA_URL,
            headers=self.headers,
            json=payload
        )

        logging.info(
            f'\n[{response.status_code}], limit={limit}, offset={offset}'
        )
        response.raise_for_status()
        return response.json()

    @time_of_function
    def get_all_sales_reports(self, date: str) -> list:
        date_formatted = dt.strptime(date, "%Y-%m-%d").date()
        start_date = (
            date_formatted - timedelta(days=TWO_WEEK)
        ).strftime('%Y-%m-%d')
        all_data = []
        current_date = start_date

        logging.debug('Функция начала работу')
        while True:
            try:
                result = self._get_sale_report(current_date)
            except requests.HTTPError as e:
                if e.response.status_code == 429:

                    logging.warning(
                        '⏳ Превышен лимит запросов (429). Ждём 60 секунд...'
                    )
                    time.sleep(60)
                    continue
                else:
                    logging.error(
                        f'Код ответа сервера: {e.response.status_code}')
                    raise
            if not result:
                logging.info('✅ Все страницы загружены.')
                break
            filtered_result = [
                sale for sale in result
                if start_date <= sale['date'][:10] <= date_formatted.strftime('%Y-%m-%d')
            ]
            all_data.extend(filtered_result)
            current_date = result[-1]['lastChangeDate']
            time.sleep(60)
        logging.debug('Функция завершила работу')
        return all_data

    @time_of_function
    def get_all_stock_reports(
        self,
        start_date: str,
        end_date: str,
        limit: int = DATA_PAGE_LIMIT
    ) -> list:
        offset = 0
        all_data = []

        logging.debug('Функция начала работу')
        while True:
            try:
                result = self._get_stock_report(
                    start_date, end_date, offset=offset, limit=limit)
            except requests.HTTPError as e:
                if e.response.status_code == 429:

                    logging.warning(
                        '⏳ Превышен лимит запросов (429). Ждём 60 секунд...'
                    )
                    time.sleep(60)
                    continue
                else:
                    logging.error(
                        f'Код ответа сервера: {e.response.status_code}')
                    raise
            data = result.get('data', [])
            if not data['items']:
                logging.info('✅ Все страницы загружены.')
                break
            all_data.extend(data['items'])
            offset += limit
            time.sleep(20)
        logging.debug('Функция завершила работу')
        return all_data

    def parce_product_data(self, data, date_str):
        rows = []

        for item in data:
            rows.append(
                {
                    'дата': date_str,
                    'наименование': item.get('name', '').strip('""'),
                    'артикул': item.get('nmID', ''),
                    'остаток': item.get('metrics', {}).get('stockCount', 0)
                }
            )
        return rows

    def parce_avg_sales(self, data, date_str):
        avg_sales = []
        sales_by_article = defaultdict(int)

        for item in data:
            if item.get('isRealization') and not item.get('isCancel'):
                article = item['nmId']
                sales_by_article[article] += 1

        for article, total_sales in sales_by_article.items():
            avg_per_day = total_sales / TWO_WEEK
            avg_sales.append({
                'дата': date_str,
                'артикул': article,
                'среднее значение': round(avg_per_day, 2)
            })
        return avg_sales

    @staticmethod
    def _get_filename(
        format: str,
        date_str: str,
        prefix: str = 'stocks',
        folder: str = 'data'
    ):
        os.makedirs(folder, exist_ok=True)
        filename = os.path.join(folder, f'{prefix}_{date_str}.{format}')
        return filename

    @time_of_function
    def save_to_json(
        self,
        data: list,
        date_str: str,
        prefix: str = 'stocks',
        folder: str = 'data'
    ):
        logging.debug('Сохранение файла...')
        filename = WbAnalyticsClient._get_filename(
            'json', date_str, prefix, folder)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logging.info(f'✅ Данные сохранены в {filename}')
        logging.debug('Файл сохранен.')

    @time_of_function
    def save_to_csv(
        self,
        data: list,
        date_str: str,
        fieldnames: list,
        prefix: str = 'stocks',
        folder: str = 'data'
    ):
        logging.debug('Сохранение файла...')
        filename = WbAnalyticsClient._get_filename(
            'csv', date_str, prefix, folder)
        with open(
            filename,
            'w',
            encoding='utf-8',
            newline=''
        ) as f:
            writer = csv.DictWriter(
                f,
                fieldnames=fieldnames,
                delimiter=';'
            )
            writer.writeheader()
            writer.writerows(data)
        logging.info(f'✅ Данные сохранены в {filename}')
        logging.debug('Файл сохранен.')


def get_yesterday_date_str() -> str:
    yesterday = dt.now() - timedelta(days=1)
    return yesterday.strftime('%Y-%m-%d')
