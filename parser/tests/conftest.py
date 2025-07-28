import pytest

from wb_tools import WbAnalyticsClient
from wb_db import WbDataBaseClient


@pytest.fixture
def wb_client():
    return WbAnalyticsClient('test_token')


@pytest.fixture
def db_client():
    return WbDataBaseClient()


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
