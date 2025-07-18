import os
from dotenv import load_dotenv
import requests

from wb_tools import get_yesterday_date_str, WbAnalyticsClient


def main():
    load_dotenv()
    token = os.getenv('TOKEN')

    if not token:
        print("❌ Токен не найден.")
        return

    client = WbAnalyticsClient(token)
    date_str = get_yesterday_date_str()

    try:
        all_data = client.get_all_stock_reports(
            start_date=date_str,
            end_date=date_str
        )
        print(f'\n✅ Получено записей: {len(all_data)}')
        client.save_to_json(all_data, date_str)
        client.save_to_csv(all_data, date_str)
    except requests.RequestException as e:
        print(f'❌ Ошибка запроса: {e}')


if __name__ == '__main__':
    main()
