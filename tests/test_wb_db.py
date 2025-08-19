import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import patch, MagicMock
from parser.exceptions import RefTableError, TableNameError, TypeDataError
from parser.wb_db import WbDataBaseClient


def test_parse_product_data(db_client):
    test_data = [
        {'name': 'Товар 1', 'nmID': 12345, 'metrics': {'stockCount': 10}},
        {'name': 'Товар 2', 'nmID': 67890, 'metrics': {'stockCount': 5}},
    ]
    date_str = '2023-01-01'
    result = db_client.parse_product_data(test_data, date_str)
    assert len(result) == 2
    assert result[0]['наименование'] == 'Товар 1'
    assert result[0]['артикул'] == 12345
    assert result[0]['остаток'] == 10
    assert result[0]['дата'] == '2023-01-01'
    assert result[1]['наименование'] == 'Товар 2'


def test_parse_avg_sales(db_client):
    test_data = [
        {'nmId': 12345, 'isRealization': True, 'isCancel': False},
        {'nmId': 12345, 'isRealization': True, 'isCancel': False},
        {'nmId': 67890, 'isRealization': True, 'isCancel': False},
        {'nmId': 12345, 'isRealization': False, 'isCancel': True},
    ]
    date_str = '2023-01-01'
    result = db_client.parse_avg_sales(test_data, date_str)
    assert len(result) == 2
    assert result[0]['артикул'] in [12345, 67890]
    assert result[1]['артикул'] in [12345, 67890]
    for item in result:
        if item['артикул'] == 12345:
            assert item['среднее значение'] == round(
                Decimal(2) / Decimal(14), 2
            )
        else:
            assert item['среднее значение'] == round(
                Decimal(1) / Decimal(14), 2
            )


def test_validate_date_db(db_client):
    date_str = '2025-01-01'
    with patch.object(
        db_client,
        '_create_table_if_not_exist',
        return_value='catalog_dates_test_shop'
    ):
        query, params = db_client.validate_date_db(date_str)
        assert 'INSERT INTO catalog_dates_test_shop' in query
        assert params[0] == date(2025, 1, 1)
        assert params[1:] == (1, 1, 2025, 3)


def test_validate_products_db(db_client):
    test_data = [
        {'артикул': 12345, 'наименование': 'Товар 1'},
        {'артикул': 67890, 'наименование': 'Товар 2'},
    ]
    with patch.object(
        db_client,
        '_create_table_if_not_exist',
        return_value='catalog_products_test_shop'
    ):
        query, params = db_client.validate_products_db(test_data)
        assert 'INSERT INTO catalog_products_test_shop' in query
        assert len(params) == 2
        assert params[0] == (12345, 'Товар 1')
        assert params[1] == (67890, 'Товар 2')


def test_validate_stocks_db(db_client):
    test_data = [
        {'дата': '2025-01-01', 'артикул': 12345, 'остаток': 10},
        {'дата': '2025-01-01', 'артикул': 67890, 'остаток': 5},
    ]
    with patch.object(
        db_client,
        '_create_table_if_not_exist',
        return_value='reports_stocks_test_shop'
    ):
        query, params = db_client.validate_stocks_db(test_data)
        assert 'INSERT INTO reports_stocks_test_shop' in query
        assert len(params) == 2
        assert params[0] == (date(2025, 1, 1), 12345, 10)
        assert params[1] == (date(2025, 1, 1), 67890, 5)


def test_validate_sales_db(db_client):
    test_data = [
        {'дата': '2025-01-01', 'артикул': 12345, 'среднее значение': 2},
        {'дата': '2025-01-01', 'артикул': 67890, 'среднее значение': 1},
    ]
    with patch.object(
        db_client,
        '_create_table_if_not_exist',
        return_value='reports_sales_test_shop'
    ):
        query, params = db_client.validate_sales_db(test_data)
        assert 'INSERT INTO reports_sales_test_shop' in query
        assert len(params) == 2
        assert params[0] == (date(2025, 1, 1), 12345, 2)
        assert params[1] == (date(2025, 1, 1), 67890, 1)


def test_create_table_if_not_exist_invalid_type(db_client):
    with patch.object(
        db_client,
        '_allowed_tables',
        return_value=[]
    ), pytest.raises(TypeDataError):
        db_client._create_table_if_not_exist('catalog', 'invalid_type')


def test_create_table_if_not_exist_missing_refs(db_client):
    with patch.object(
        db_client,
        '_allowed_tables',
        return_value=[]
    ), pytest.raises(RefTableError):
        db_client._create_table_if_not_exist('reports', 'sales')


def test_clean_db_success(db_client):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    with patch.object(
        WbDataBaseClient,
        '_allowed_tables',
        return_value=['valid_table']
    ), patch('mysql.connector.connect', return_value=mock_conn), patch.object(
        db_client,
        '_allowed_tables',
        return_value=['valid_table']
    ):
        db_client.clean_db(valid_table=True)
        mock_cursor.execute.assert_called_once_with('DELETE FROM valid_table')
        mock_conn.commit.assert_called_once()


def test_clean_db_table_not_exists(db_client):
    with patch.object(
        db_client,
        '_allowed_tables',
        return_value=[]
    ), pytest.raises(TableNameError):
        db_client.clean_db(nonexistent_table=True)
