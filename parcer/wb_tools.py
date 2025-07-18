import csv
import os
import json
import time
import requests
from datetime import datetime as dt, timedelta

from constants import WB_PRODUCT_DATA


class WbAnalyticsClient:
    BASE_URL = WB_PRODUCT_DATA

    def __init__(self, token: str):
        if not token:
            raise ValueError('API token is required')
        self.token = token
        self.headers = {
            "Authorization": self.token,
            "Content-Type": "application/json"
        }

    def get_stock_report(
        self,
        start_date: str,
        end_date: str,
        offset: int = 0,
        limit: int = 1000
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
            self.BASE_URL, headers=self.headers, json=payload)
        print(f'[{response.status_code}] offset={offset}')
        response.raise_for_status()
        return response.json()

    def get_all_stock_reports(
        self,
        start_date: str,
        end_date: str,
        limit: int = 1000
    ) -> list:
        offset = 0
        all_data = []

        while True:
            try:
                result = self.get_stock_report(
                    start_date, end_date, offset=offset, limit=limit)
            except requests.HTTPError as e:
                if e.response.status_code == 429:
                    print('⏳ Превышен лимит запросов (429). Ждём 60 секунд...')
                    time.sleep(60)
                    continue
                else:
                    raise

            data = result.get('data', [])
            if not data['items']:
                print('✅ Все страницы загружены.')
                break

            all_data.extend(data['items'])
            offset += limit

            time.sleep(20)
        return all_data

    @staticmethod
    def save_to_json(data: list, date_str: str, folder: str = 'data'):
        os.makedirs(folder, exist_ok=True)
        filename = os.path.join(folder, f'stocks_{date_str}.json')

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f'✅ Данные сохранены в {filename}')

    @staticmethod
    def save_to_csv(data: list, date_str: str, folder: str = 'data'):
        rows = []

        os.makedirs(folder, exist_ok=True)
        filename = os.path.join(folder, f'wb_stocks_{date_str}.csv')

        for item in data:
            rows.append({
                'наименование': item.get('name', '').strip('""'),
                'артикул': item.get('nmID', ''),
                'остаток': item.get('metrics', {}).get('stockCount', 0)
            })
        with open(
            filename,
            'w',
            encoding='utf-8',
            newline=''
        ) as f:
            writer = csv.DictWriter(
                f,
                fieldnames=['наименование', 'артикул', 'остаток'],
                delimiter=';'
            )
            writer.writeheader()
            writer.writerows(rows)
        print(f'✅ Данные сохранены в {filename}')


def get_yesterday_date_str() -> str:
    yesterday = dt.now() - timedelta(days=1)
    return yesterday.strftime('%Y-%m-%d')
