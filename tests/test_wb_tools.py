# import json
import pytest
import requests
from unittest.mock import patch
from parser.wb_tools import WbAnalyticsClient


def test_init_without_token():
    with pytest.raises(ValueError, match='API token is required'):
        WbAnalyticsClient('')


def test_get_sale_report_success(wb_client, requests_mock):
    test_date = '2025-07-10'
    mock_response = [{"nmId": 123, "date": test_date}]

    requests_mock.get(
        wb_client.AVG_SALES_URL,
        json=mock_response,
        status_code=200,
        headers={"Content-Type": "application/json"}
    )

    result = wb_client._get_sale_report(test_date)
    assert result == mock_response


def test_get_stock_report_success(wb_client, requests_mock):
    mock_response = {'data': {'items': [{'test': 'data'}]}}

    requests_mock.post(
        wb_client.PRODUCT_DATA_URL,
        json=mock_response,
        status_code=200
    )
    result = wb_client._get_stock_report('2025-07-01', '2025-07-10')
    assert result == mock_response


def test_get_sale_report_429_error(wb_client, requests_mock):
    test_date = '2025-07-10'
    requests_mock.get(
        wb_client.AVG_SALES_URL,
        status_code=429
    )

    with pytest.raises(requests.HTTPError) as exc_info:
        wb_client._get_sale_report(test_date)
    assert exc_info.value.response.status_code == 429


def test_get_stock_report_429_error(wb_client, requests_mock):
    start_date = '2025-07-01'
    end_date = '2025-07-10'

    requests_mock.post(
        wb_client.PRODUCT_DATA_URL,
        status_code=429,
    )

    with pytest.raises(requests.HTTPError) as exc_info:
        wb_client._get_stock_report(
            start_date=start_date,
            end_date=end_date
        )
    assert exc_info.value.response.status_code == 429


def test_get_all_sales_reports(wb_client):
    mock_data = [
        {"nmId": 123, "date": "2025-07-10", "lastChangeDate": "2025-07-10"}
    ]
    mock_empty = []

    with patch.object(
        wb_client,
        '_get_sale_report',
        side_effect=[mock_data, mock_empty]
    ), patch('time.sleep') as mock_sleep:

        result = wb_client.get_all_sales_reports('2025-07-24')
        assert len(result) == len(mock_data)
        mock_sleep.assert_called_once_with(60)


def test_get_all_stock_reports(wb_client):
    mock_data = {'data': {'items': [{'test': 'data'}]}}
    mock_empty = {'data': {'items': []}}

    with patch.object(
        wb_client,
        '_get_stock_report',
        side_effect=[mock_data, mock_empty]
    ), patch('time.sleep') as mock_sleep:

        result = wb_client.get_all_stock_reports(
            '2025-07-01', '2025-07-10')
        assert len(result) == 1
        mock_sleep.assert_called_once_with(20)

# def test_save_to_json(wb_client, tmp_path):
#     test_data = [{"test": "data"}]
#     test_date = '2025-07-10'
#     test_folder = tmp_path / 'data'

#     wb_client.save_to_json(test_data, test_date, folder=str(test_folder))

#     filename = test_folder / f'stocks_{test_date}.json'
#     assert filename.exists()

#     with open(filename, 'r') as f:
#         loaded_data = json.load(f)
#     assert loaded_data == test_data


def test_get_filename(wb_client, tmp_path):
    result = wb_client._get_filename(
        'json', '2025-07-10', folder=str(tmp_path))
    expected = str(tmp_path / 'stocks_2025-07-10.json')
    assert result == expected
