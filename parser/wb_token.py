import logging
import os
from cryptography.fernet import Fernet
from parser.constants import (
    CREATE_TOKEN_TABLE,
    INSERT_TOKEN,
    TOKENS_TABLE_NAME
)
from parser.decorators import connection_db
from parser.exceptions import (
    BinaryTokenError,
    EmptyTokenError,
    EnvFileError,
    ModelTokenError,
    SizeTokenError,
    VerificationError
)
from parser.logging_config import setup_logging


setup_logging()


class WBTokensClient:
    """Класс для работы с токенами."""

    def keygen(self) -> None:
        """Генерирует ключ для доступа к методам шифрования/дешифрования."""
        key = Fernet.generate_key()
        print(f'Ключ для шифрования: {key.decode()}')

    @connection_db
    def _allowed_tables(self, cursor=None) -> list:
        """
        Защищенный метод возвращает список существующих
        таблиц в базе данных.
        """
        cursor.execute('SHOW TABLES')
        return [table[0] for table in cursor.fetchall()]

    def _get_fernet(self):
        """Получает сохраненный ключ из .env."""
        key = os.getenv('ENCRYPTION_KEY').encode()
        if not key:
            raise EnvFileError('Отсутствуют переменные окружения')
        return Fernet(key)

    def _input_data(self) -> tuple[str, str]:
        """Интерфейс для ввода данных."""
        shop_name = input('Введите название магазина латиницей: ')
        token = input('Введите аутентификационный токен: ')
        print('Функция продолжает работу...')
        return shop_name, token

    @connection_db
    def get_exists_shop(
        self,
        token_table_name: str = TOKENS_TABLE_NAME,
        cursor=None
    ) -> list:
        """
        Создает таблицу токенов (если ее нет),
        получает названия магазинов из базы данных.
        """
        if token_table_name in self._allowed_tables():
            logging.info(f'Таблица токенов {token_table_name} найдена в базе')
        else:
            create_tokens_table_query = CREATE_TOKEN_TABLE.format(
                table_name_token=token_table_name
            )
            cursor.execute(create_tokens_table_query)
            logging.info(
                f'Таблица токенов {token_table_name} успешно создана'
            )
            return []
        cursor.execute(f'SELECT shop_name FROM {token_table_name}')
        return [table[0] for table in cursor.fetchall()]

    def _ensure_shop_exists(self, shop_name: str, token: str = ''):
        """Позволяет внести новый токен в базу."""
        if shop_name not in self.get_exists_shop():
            if not token:
                shop_name, token = self._input_data()
            self.encrypt(shop_name, token)

    @connection_db
    def encrypt(
        self,
        shop_name: str,
        token: str,
        token_table_name: str = TOKENS_TABLE_NAME,
        cursor=None
    ):
        """Шифрует токен."""
        if not token:
            raise EmptyTokenError('Токен не может быть пустым')
        cipher_suite = self._get_fernet()
        try:
            encrypted = cipher_suite.encrypt(token.encode('utf-8'))
            decrypted = cipher_suite.decrypt(encrypted).decode('utf-8')
            if decrypted != token:
                raise VerificationError('Ошибка верификации токена')
            if len(encrypted) > 1024:
                raise SizeTokenError('Токен слишком большой для хранения')
            query = INSERT_TOKEN.format(table_name_token=token_table_name)
            cursor.execute(query, (shop_name, encrypted))
        except Exception as e:
            logging.error(f'Ошибка шифрования: {str(e)}')
            raise ValueError(f'Не удалось сохранить токен: {str(e)}')

    @connection_db
    def decrypt(
        self,
        shop_name: str,
        token: str = '',
        token_table_name: str = TOKENS_TABLE_NAME,
        cursor=None
    ):
        """Дешифрует токен."""
        if shop_name not in self.get_exists_shop():
            self._ensure_shop_exists(shop_name, token)
        cipher_suite = self._get_fernet()
        cursor.execute(
            f'SELECT token FROM {token_table_name} WHERE shop_name = %s',
            (shop_name,)
        )
        row = cursor.fetchone()
        if not row or not row[0]:
            raise ModelTokenError(f'Токен для магазина {shop_name} не найден')
        try:
            if not isinstance(row[0], bytes):
                raise BinaryTokenError('Токен должен быть в бинарном формате')
            return cipher_suite.decrypt(row[0]).decode('utf-8')
        except Exception as e:
            raise ValueError(f'Ошибка дешифровки токена: {str(e)}')
