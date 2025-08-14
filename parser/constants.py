"""URLs для получения данных из внешнего API."""
WB_PRODUCT_DATA = (
    'https://seller-analytics-api.wildberries.ru/'
    'api/v2/stocks-report/products/products'
)
WB_AVG_SALES = 'https://statistics-api.wildberries.ru/api/v1/supplier/orders'

NAME_OF_SHOP = 'loweis'

TOKENS_TABLE_NAME = 'tokens'

"""Константы, регулирующие запрос."""
DATA_PAGE_LIMIT = 100
TWO_WEEK = 14

"""SQL запросы для взаимодейсвтия с базой данных MySQL."""
# запросы на создание таблиц.
CREATE_TOKEN_TABLE = '''
    CREATE TABLE IF NOT EXISTS {table_name_token} (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `shop_name` varchar(255) NOT NULL,
    `token` VARBINARY(1024) NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `shop_name` (`shop_name`)
);
'''

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
CREATE_SALES_TABLE = '''
    CREATE TABLE IF NOT EXISTS {table_name} (
    `date` date NOT NULL,
    `article` bigint(20) unsigned NOT NULL,
    `sale` int(11) DEFAULT '0',
    PRIMARY KEY (`date`,`article`),
    KEY `article` (`article`),
    CONSTRAINT `fk_{table_name}_date` FOREIGN KEY (
    `date`
    ) REFERENCES {ref_dates_table} (
    `full_date`
    ) ON DELETE CASCADE ON UPDATE CASCADE
);
'''
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

# запросы заполнения таблиц данными.
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

INSERT_PRODUCTS = '''
    INSERT INTO {table_name} (article, name)
    VALUES (%s, %s)
    ON DUPLICATE KEY UPDATE
    name = VALUES(name)
'''

INSERT_STOCKS = '''
    INSERT INTO {table_name} (date, article, stock)
    VALUES (%s, %s, %s)
    ON DUPLICATE KEY UPDATE
    stock = VALUES(stock)
'''

INSERT_SALES = '''
    INSERT INTO {table_name} (date, article, sale)
    VALUES (%s, %s, %s)
    ON DUPLICATE KEY UPDATE
    sale = VALUES(sale)
'''

INSERT_TOKEN = '''
    INSERT INTO {table_name_token} (shop_name, token)
    VALUES (%s, %s)
    ON DUPLICATE KEY UPDATE
    token = VALUES(token)
'''
