WB_PRODUCT_DATA = (
    'https://seller-analytics-api.wildberries.ru/'
    'api/v2/stocks-report/products/products'
)
"""URL для получения данных из внешнего API об остатках."""

WB_AVG_SALES = 'https://statistics-api.wildberries.ru/api/v1/supplier/orders'
"""URL для получения данных из внешнего API о продажах."""

NAME_OF_SHOP = 'loweis'
"""Дефолтное название для тестового магазина."""

TOKENS_TABLE_NAME = 'tokens'
"""Дефолтное назвние таблицы токенов."""

DECIMAL_ROUNDING = 2
"""Округление до указанного количества знаков после точки."""

DATA_PAGE_LIMIT = 100
"""Пагинация. Лимит данных на страницу."""

DAYS = 14
"""Количество дней."""

MAX_BYTE_SIZE = 1024
"""Максимальный размер токена в байтах."""

CREATE_TOKEN_TABLE = '''
    CREATE TABLE IF NOT EXISTS {table_name_token} (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `shop_name` varchar(255) NOT NULL,
    `token` VARBINARY(1024) NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `shop_name` (`shop_name`)
);
'''
"""SQL запрос для создания модели токенов."""

CREATE_DATES_TABLE = '''
    CREATE TABLE IF NOT EXISTS {table_name} (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `full_date` date NOT NULL,
    `day` int(11) NOT NULL,
    `month` int(11) NOT NULL,
    `year` int(11) NOT NULL,
    `day_of_week` int(11) NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `unique_date_combo` (
    `full_date`,`day`,`month`,`year`
    ),
    KEY `full_date` (`full_date`),
    KEY `year` (`year`,`month`),
    KEY `year_2` (`year`,`month`,`day`)
);
'''
"""SQL запрос для создания модели дат."""

CREATE_PRODUCTS_TABLE = '''
    CREATE TABLE IF NOT EXISTS {table_name} (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `article` bigint(20) unsigned NOT NULL,
    `name` varchar(255) NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `article` (`article`),
    FULLTEXT KEY `name` (`name`)
);
'''
"""SQL запрос для создания модели продуктов."""

CREATE_SALES_TABLE = '''
    CREATE TABLE IF NOT EXISTS {table_name} (
    `date` date NOT NULL,
    `article` bigint(20) unsigned NOT NULL,
    `sale` float DEFAULT '0',
    PRIMARY KEY (`date`,`article`),
    KEY `article` (`article`),
    CONSTRAINT `fk_{table_name}_date` FOREIGN KEY (
    `date`
    ) REFERENCES {ref_dates_table} (
    `full_date`
    ) ON DELETE CASCADE ON UPDATE CASCADE
);
'''
"""SQL запрос для создания модели продаж."""

CREATE_STOCKS_TABLE = '''
    CREATE TABLE IF NOT EXISTS {table_name} (
    `date` date NOT NULL,
    `article` bigint(20) unsigned NOT NULL,
    `stock` int(10) unsigned NOT NULL DEFAULT '0',
    PRIMARY KEY (`date`,`article`),
    KEY `article` (`article`),
    CONSTRAINT `fk_{table_name}_date` FOREIGN KEY (
    `date`
    ) REFERENCES {ref_dates_table} (
    `full_date`
    ) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_{table_name}_product` FOREIGN KEY (
    `article`
    ) REFERENCES {ref_products_table} (
    `article`
    ) ON DELETE CASCADE ON UPDATE CASCADE
);
'''
"""SQL запрос для создания модели остатков."""

INSERT_DATES = '''
    INSERT INTO {table_name} (
    full_date,
    day,
    month,
    year,
    day_of_week
    )
    VALUES (%s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE id = id
'''
"""SQL запрос для наполнения данными модели дат."""

INSERT_PRODUCTS = '''
    INSERT INTO {table_name} (article, name)
    VALUES (%s, %s)
    ON DUPLICATE KEY UPDATE
    name = VALUES(name)
'''
"""SQL запрос для наполнения данными модели продуктов."""

INSERT_STOCKS = '''
    INSERT INTO {table_name} (date, article, stock)
    VALUES (%s, %s, %s)
    ON DUPLICATE KEY UPDATE
    stock = VALUES(stock)
'''
"""SQL запрос для наполнения данными модели остатков."""

INSERT_SALES = '''
    INSERT INTO {table_name} (date, article, sale)
    VALUES (%s, %s, %s)
    ON DUPLICATE KEY UPDATE
    sale = VALUES(sale)
'''
"""SQL запрос для наполнения данными модели продаж."""

INSERT_TOKEN = '''
    INSERT INTO {table_name_token} (shop_name, token)
    VALUES (%s, %s)
    ON DUPLICATE KEY UPDATE
    token = VALUES(token)
'''
"""SQL запрос для наполнения данными модели токенов."""
