import logging
import os
from datetime import datetime as dt, timedelta
from dotenv import load_dotenv
from parser.logging_config import setup_logging
from parser.wb_db import WbDataBaseClient
from parser.wb_tools import WbAnalyticsClient


setup_logging()


def initialize_components() -> tuple:
    """
    Инициализирует и возвращает все необходимые
    компоненты для работы приложения.

    Выполняет следующие действия:
    1. Загружает переменные окружения из .env файла.
    2. Получает токен авторизации из переменных окружения.
    3. Создает клиент для работы с API аналитики Wildberries.
    4. Инициализирует клиент базы данных.
    5. Формирует строку с датой за вчерашний день в формате ГГГГ-ММ-ДД.

    Returns:
        tuple: Кортеж с инициализированными компонентами.
    """
    load_dotenv()
    token = os.getenv('TOKEN')
    if not token:
        logging.error('Токен отсутствует или устарел.')
        raise ValueError('Токен отсутствует или устарел.')
    client = WbAnalyticsClient(token)
    db_client = WbDataBaseClient()
    date_str = (dt.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    return db_client, client, date_str


def fetch_data(client: WbAnalyticsClient, date_str: str) -> tuple:
    """
    Получает данные по продажам и остаткам с API Wildberries за указанную дату.

    Функция выполняет два запроса к API:
    1. Получение отчетов по продажам за указанную дату.
    2. Получение отчетов по остаткам на указанную дату.

    Args:
        - client (WbAnalyticsClient): Клиент для работы
        с API Wildberries Analytics.
        - date_str (str): Дата в формате 'YYYY-MM-DD' для получения отчетов.

    Returns:
        tuple: Кортеж с полученными данными в формате:
            - all_sales (list[dict]): Список словарей с данными о продажах.
            - all_data (list[dict]): Список словарей с данными об остатках.
    """
    all_sales = client.get_all_sales_reports(date_str)
    all_data = client.get_all_stock_reports(
        start_date=date_str, end_date=date_str)
    logging.info(f'\n✅ Получено записей по остаткам: {len(all_data)}')
    logging.info(
        f'\n✅ Получено записей по продажам за 2 недели: {len(all_sales)}')
    return all_sales, all_data


def process_data(
    db_client: WbDataBaseClient,
    all_sales: list,
    all_data: list,
    date_str: str
) -> tuple[list[dict], list[dict]]:
    """
    Обрабатывает и форматирует данные перед сохранением в базу данных.

    Принимает сырые данные из API Wildberries, применяет к ним парсинг и
    форматирование с помощью методов клиента,
    подготавливая данные для записи в БД.

    Args:
        - client (WbAnalyticsClient): Клиент для работы с API Wildberries.
        - all_sales (list[dict]): Список словарей с сырыми данными о продажах.
        - all_data (list[dict]): Список словарей с сырыми данными об остатках.
        - date_str (str): Дата в формате 'YYYY-MM-DD' для обработки данных.

    Returns:
        tuple[list[dict], list[dict]]: Кортеж с отформатированными данными:
            - formatter_sales: Отформатированные данные о продажах.
            - formatter_data: Отформатированные данные об остатках.
    """
    formatter_sales = db_client.parse_avg_sales(all_sales, date_str)
    formatter_data = db_client.parse_product_data(all_data, date_str)
    return formatter_sales, formatter_data


def save_to_database(
    db_client: WbDataBaseClient,
    date_str: str,
    formatter_data: list[dict],
    formatter_sales: list[dict]
) -> None:
    """
    Сохраняет данные в базу данных.
    Args:
        - db_client (WbDataBaseClient): Клиент для работы с базой данных.
        - date_str (str): Дата в формате 'YYYY-MM-DD' для сохранения.
        - formatter_data (list[dict]): Отформатированные данные об
        остатках и продуктах.
        - formatter_sales (list[dict]): Отформатированные данные о продажах.
    """
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
    all_data: list[dict],
    all_sales: list[dict]
) -> None:
    """
    Экспортирует данные в JSON файлы.

    Сохраняет два типа данных в отдельные JSON файлы:
    1. Данные о продажах (с префиксом 'avg_sales').
    2. Данные об остатках товаров.

    Args:
        - client (WbAnalyticsClient): Клиент для работы с API Wildberries.
        - date_str (str): Дата в формате 'YYYY-MM-DD' для именования файлов.
        - all_data (list[dict]): Данные об остатках товаров.
        - all_sales (list[dict]): Данные о продажах.
    """
    client.save_to_json(all_sales, date_str, 'avg_sales')
    client.save_to_json(all_data, date_str)
