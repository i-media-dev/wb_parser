import json
import logging
import os
import time
from datetime import datetime as dt, timedelta

import requests

from parser.constants import (
    DATA_PAGE_LIMIT,
    TWO_WEEK,
    WB_AVG_SALES,
    WB_PRODUCT_DATA
)
from parser.decorators import time_of_function
from parser.logging_config import setup_logging

setup_logging()


class WbAnalyticsClient:
    """Класс, который работает с API Wildberries."""

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
    ) -> dict:
        """
        Защищенный метод, формирующий запрос к API Wildberries
        без учета пагинации.
        """
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
        """
        Защищенный метод, формирующий запрос к API Wildberries
        без учета пагинации.
        """
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
    def get_all_sales_reports(self, date: str) -> list[dict]:
        """
        Метод, формирующий запрос к API Wildberries
        с учетом пагинации.
        """
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
                if (
                    start_date <= sale['date'][:10]
                    <= date_formatted.strftime('%Y-%m-%d')
                )
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
    ) -> list[dict]:
        """
        Метод, формирующий запрос к API Wildberries
        с учетом пагинации.
        """
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

    @staticmethod
    def _get_filename(
        format: str,
        date_str: str,
        prefix: str = 'stocks',
        folder: str = 'data'
    ) -> str:
        """Защищенный метод создает директорию и настраиваемое имя файла."""
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
    ) -> None:
        """Метод сохраняет данные в файл формата json."""
        logging.debug('Сохранение файла...')
        filename = WbAnalyticsClient._get_filename(
            'json', date_str, prefix, folder)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logging.info(f'✅ Данные сохранены в {filename}')
        logging.debug('Файл сохранен.')
