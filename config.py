import os
from dotenv import load_dotenv

# Load environment variables từ file .env
load_dotenv()

# Cấu hình kết nối Odoo từ environment variables
ODOO_CONFIG = {
    'url': os.getenv('ODOO_URL'),
    'db': os.getenv('ODOO_DB'),
    'username': os.getenv('ODOO_USERNAME'),
    'password': os.getenv('ODOO_PASSWORD'),
}

# Cấu hình Flask từ environment variables
FLASK_CONFIG = {
    'host': '0.0.0.0',
    'port': 5000,
    'debug': True
}
