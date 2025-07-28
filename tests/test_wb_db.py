from datetime import datetime as dt
from unittest.mock import patch, MagicMock

from parser.constants import TWO_WEEK


class TestWbDataBaseClient:
    def test_parse_product_data(self, db_client, mock_stock_data):
        result = db_client.parse_product_data(mock_stock_data, '2025-07-10')
        assert len(result) == 1
        assert result[0]['артикул'] == 12345
        assert result[0]['наименование'] == 'Test Product'
        assert result[0]['остаток'] == 100
        assert result[0]['дата'] == '2025-07-10'

    def test_parse_avg_sales(self, db_client, mock_sales_data):
        result = db_client.parse_avg_sales(mock_sales_data, '2025-07-10')
        assert len(result) == 1
        assert result[0]['артикул'] == 12345
        assert result[0]['среднее значение'] == 5 // TWO_WEEK
        assert result[0]['дата'] == '2025-07-10'

    def test_validate_date_db(self, db_client):
        query, params = db_client.validate_date_db('2025-07-10')
        assert query.strip().startswith('INSERT INTO catalog_dates')
        assert params == (dt(2025, 7, 10).date(), 10, 7, 2025, 4)

    def test_validate_products_db(self, db_client, mock_stock_data):
        parsed_data = db_client.parse_product_data(
            mock_stock_data, '2025-07-10')
        query, params = db_client.validate_products_db(parsed_data)
        assert query.strip().startswith('INSERT INTO catalog_products')
        assert params == [(12345, 'Test Product')]

    def test_validate_stocks_db(self, db_client, mock_stock_data):
        parsed_data = db_client.parse_product_data(
            mock_stock_data, '2025-07-10')
        query, params = db_client.validate_stocks_db(parsed_data)
        assert query.strip().startswith('INSERT INTO reports_stocks')
        assert params == [(dt(2025, 7, 10).date(), 12345, 100)]

    def test_validate_sales_db(self, db_client, mock_sales_data):
        parsed_data = db_client.parse_avg_sales(mock_sales_data, '2025-07-10')
        query, params = db_client.validate_sales_db(parsed_data)
        assert query.strip().startswith('INSERT INTO reports_sales')
        assert params == [(dt(2025, 7, 10).date(), 12345, 5 // TWO_WEEK)]

    def test_save_to_db(self, db_client):
        test_data = ('INSERT INTO test VALUES (%s)', [('test',)])

        with patch('mysql.connector.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_connect.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor

            db_client.save_to_db(test_data)

            mock_cursor.executemany.assert_called_once_with(
                'INSERT INTO test VALUES (%s)', [('test',)]
            )
            mock_conn.commit.assert_called_once()

    def test_clean_db(self, db_client):
        with patch('mysql.connector.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_connect.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor

            db_client.clean_db(catalog_products=True, catalog_dates=True)

            assert mock_cursor.execute.call_count == 2
            mock_conn.commit.assert_called()
