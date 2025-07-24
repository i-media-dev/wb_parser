import os

from dotenv import load_dotenv

load_dotenv()


config = {
    'user': os.getenv('LOGIN'),
    'password': os.getenv('PASSWORD'),
    'host': os.getenv('HOST'),
    'database': os.getenv('DB_NAME'),
    'port': 3306,
    'connection_timeout': 10,
    'use_pure': True
}
