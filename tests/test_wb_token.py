import pytest
from cryptography.fernet import Fernet
from unittest.mock import patch
from parser.exceptions import EmptyTokenError, EnvFileError, ModelTokenError
from parser.wb_token import WBTokensClient


def test_keygen_prints_key(client, capsys):
    client.keygen()
    captured = capsys.readouterr()
    assert 'Ключ для шифрования' in captured.out


@patch.dict('os.environ', {'ENCRYPTION_KEY': Fernet.generate_key().decode()})
def test_get_fernet_returns_fernet(client):
    f = client._get_fernet()
    assert hasattr(f, 'encrypt')
    assert hasattr(f, 'decrypt')


@patch.dict('os.environ', {}, clear=True)
def test_get_fernet_raises_envfileerror(client):
    with pytest.raises(EnvFileError):
        client._get_fernet()


def test_input_data(monkeypatch):
    inputs = iter(['shop1', 'token1'])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))
    client = WBTokensClient()
    shop, token = client._input_data()
    assert shop == 'shop1'
    assert token == 'token1'


@patch.dict('os.environ', {'ENCRYPTION_KEY': Fernet.generate_key().decode()})
def test_encrypt_and_decrypt_flow(client, mock_db_cursor):
    mock_db_cursor.fetchall.return_value = [('shop1',)]
    mock_db_cursor.execute.return_value = None
    with pytest.raises(EmptyTokenError):
        client.encrypt('shop1', '', cursor=mock_db_cursor)
    token = 'my_secret_token'
    client.encrypt('shop1', token, cursor=mock_db_cursor)
    assert mock_db_cursor.execute.call_args is not None
    args, kwargs = mock_db_cursor.execute.call_args
    assert 'INSERT' in args[0]
    assert isinstance(args[1][1], bytes)
    cipher_suite = client._get_fernet()
    encrypted_token = cipher_suite.encrypt(token.encode())
    mock_db_cursor.fetchone.return_value = (encrypted_token,)
    with patch.object(client, 'get_exists_shop', return_value=['shop1']):
        decrypted = client.decrypt('shop1', cursor=mock_db_cursor)
        assert decrypted == token


@patch.dict('os.environ', {'ENCRYPTION_KEY': Fernet.generate_key().decode()})
def test_decrypt_raises_if_shop_not_exists(client, mock_db_cursor):
    with patch.object(client, 'get_exists_shop', return_value=[]):
        with patch.object(client, '_ensure_shop_exists') as mock_ensure:
            mock_ensure.return_value = None
            mock_db_cursor.fetchone.return_value = None
            with pytest.raises(ModelTokenError):
                client.decrypt('unknown_shop', cursor=mock_db_cursor)


@patch.dict('os.environ', {'ENCRYPTION_KEY': Fernet.generate_key().decode()})
def test_decrypt_raises_if_token_not_bytes(client, mock_db_cursor):
    with patch.object(client, 'get_exists_shop', return_value=['shop1']):
        mock_db_cursor.fetchone.return_value = ('not_bytes_token',)
        with pytest.raises(ValueError) as excinfo:
            client.decrypt('shop1', cursor=mock_db_cursor)
        assert 'Токен должен быть в бинарном формате' in str(excinfo.value)


def test_encrypt_raises_on_verification_failure(client, mock_db_cursor):
    class FakeFernet:
        def encrypt(self, data):
            return b'encrypted_data'

        def decrypt(self, data):
            return b'wrong_data'
    with patch.object(client, '_get_fernet', return_value=FakeFernet()):
        with pytest.raises(ValueError) as excinfo:
            client.encrypt('shop1', 'token', cursor=mock_db_cursor)
        assert 'Ошибка верификации токена' in str(excinfo.value)


def test_encrypt_raises_on_size_error(client, mock_db_cursor):
    class FakeFernet:
        def encrypt(self, data):
            return b'x' * (1025)

        def decrypt(self, data):
            return b'token'
    with patch.object(client, '_get_fernet', return_value=FakeFernet()):
        with pytest.raises(ValueError) as excinfo:
            client.encrypt('shop1', 'token', cursor=mock_db_cursor)
        assert 'Токен слишком большой для хранения' in str(excinfo.value)


def test_allowed_tables_calls_execute_and_returns_list(client, mock_db_cursor):
    mock_db_cursor.fetchall.return_value = [('table1',), ('table2',)]
    result = client._allowed_tables(cursor=mock_db_cursor)
    mock_db_cursor.execute.assert_called_once_with('SHOW TABLES')
    assert result == ['table1', 'table2']
