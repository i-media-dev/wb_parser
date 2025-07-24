'''URLs для получения данных из внешнего API'''

WB_PRODUCT_DATA = 'https://seller-analytics-api.wildberries.ru/api/v2/stocks-report/products/products'
WB_AVG_SALES = 'https://statistics-api.wildberries.ru/api/v1/supplier/orders'

'''Константы, регулирующие запрос'''
DATA_PAGE_LIMIT = 100
TWO_WEEK = 14

ALLOWED_TABLES = ['dates', 'products', 'stocks', 'sales']
