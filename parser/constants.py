"""URLs для получения данных из внешнего API."""
WB_PRODUCT_DATA = (
    'https://seller-analytics-api.wildberries.ru/'
    'api/v2/stocks-report/products/products'
)
WB_AVG_SALES = 'https://statistics-api.wildberries.ru/api/v1/supplier/orders'

NAME_OF_SHOP = 'loweis'

"""Константы, регулирующие запрос."""
DATA_PAGE_LIMIT = 100
TWO_WEEK = 14

"""SQL запросы для взаимодейсвтия с базой данных MySQL."""
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
        ) ON DELETE CASCADE ON UPDATE CASCADE,
        CONSTRAINT `fk_{table_name}_product` FOREIGN KEY (
        `article`
        ) REFERENCES {ref_products_table} (
        `article`
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
