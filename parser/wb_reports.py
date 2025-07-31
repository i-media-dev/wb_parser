import logging
import time
import requests
from parser.decorators import time_of_function
from parser.logging_config import setup_logging
from parser.utils import (
    # export_data,
    fetch_data,
    initialize_components,
    process_data,
    save_to_database
)


setup_logging()


@time_of_function
def main():
    """
    Основная логика программы.
    Выполняет последовательность операций:
    1. Инициализация компонентов (БД, API клиент).
    2. Получение данных из API Wildberries.
    3. Обработка и форматирование данных.
    4. Сохранение данных в базу данных.
    """
    try:
        db_client, client, date_str = initialize_components()

        all_sales, all_data = fetch_data(client, date_str)

        formatter_sales, formatter_data = process_data(
            db_client, all_sales, all_data, date_str
        )

        save_to_database(db_client, date_str, formatter_data, formatter_sales)

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
    start_time = time.time()
    print('Функция main начала работу')
    main()
    execution_time = round(time.time() - start_time, 3)
    print(
        'Функция main завершила работу. '
        f'Время выполнения - {execution_time} сек. '
        f'или {round(execution_time / 60, 2)} мин.'
    )
