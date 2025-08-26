from dotenv import load_dotenv
import logging
import requests
from parser.decorators import time_of_function, time_of_script
from parser.logging_config import setup_logging
from parser.wb_token import WBTokensClient
from parser.utils import main_logic


setup_logging()


@time_of_script
@time_of_function
def main():
    """
    Основная логика программы.
    Выполняет последовательность операций:
    1. Инициализация компонентов (БД, API клиент, Токен клиент).
    2. Получение данных из API Wildberries.
    3. Обработка и форматирование данных.
    4. Сохранение данных в базу данных.
    """
    # shop_name_list = ['loweis', 'alavann', 'volna']

    load_dotenv()
    try:
        # db_client, client, date_str = initialize_components()
        token_client = WBTokensClient()
        main_logic(token_client)

        """
        Расширенные возможности скрипта.
        - Очистка данных таблиц - метод clean_db() класса WbDataBaseClient.
        - Экспорт данных в json-файл - функция export_data().
        """
        # db_client.clean_db(reports_sales_some_shop=True)

        # export_data(
        #     client,
        #     date_str,
        #     all_data,
        #     all_sales
        # )

    except requests.RequestException as e:
        logging.error(f'❌ Ошибка запроса: {e}')
    except Exception as e:
        logging.error(f'❌ Неожиданная ошибка: {e}')


if __name__ == '__main__':
    main()
