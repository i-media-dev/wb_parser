class TypeDataError(ValueError):
    """Ошибка типа данных."""

    def __str__(self):
        return 'Invalid type data'


class RefTableError(ValueError):
    """Ошибка (отсутствие) таблицы для ссылки."""

    def __str__(self):
        return 'References table is not exist'


class TableNameError(ValueError):
    """Ошибка (отсутствие) таблицы в бд."""


class SizeTokenError(ValueError):
    """Ошибка размера токена."""


class VerificationError(ValueError):
    """Ошибка верификации токена."""


class EmptyTokenError(ValueError):
    """Ошибка (отсутствие) токена."""


class BinaryTokenError(ValueError):
    """Ошибка типа данных токена."""


class ModelTokenError(ValueError):
    """Ошибка (отсутствие) таблицы токенов в бд."""


class EnvFileError(ValueError):
    """Ошибка (отсутствие) переменныъ окружения."""


class DataFetchError(Exception):
    """Исключение для ошибок получения данных"""
