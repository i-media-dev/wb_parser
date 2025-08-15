import pytest
from unittest.mock import patch, MagicMock
from parser.wb_tools import WbAnalyticsClient
from parser.wb_db import WbDataBaseClient
from parser.wb_token import WBTokensClient


@pytest.fixture
def mock_db_cursor():
    mock_cursor = MagicMock()
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    with patch('parser.decorators.mysql.connector.connect', return_value=mock_conn):
        yield mock_cursor


@pytest.fixture
def client():
    return WBTokensClient()


@pytest.fixture
def wb_client():
    return WbAnalyticsClient('test_token')


@pytest.fixture
def db_client():
    with patch('mysql.connector.connect'), \
            patch.object(WbDataBaseClient, '_allowed_tables', return_value=[]):
        client = WbDataBaseClient()
        yield client


@pytest.fixture
def mock_stock_data():
    return [{
        "nmID": 12345,
        "name": "Test Product",
        "metrics": {"stockCount": 100}
    }]


@pytest.fixture
def mock_sales_data():
    return [{
        "nmId": 12345,
        "date": "2025-07-10",
        "lastChangeDate": "2025-07-10",
        "isRealization": True,
        "isCancel": False
    } for _ in range(5)]
