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

# Cấu hình FastAPI từ environment variables
FASTAPI_CONFIG = {
    'host': os.getenv('FASTAPI_HOST', '0.0.0.0'),
    'port': int(os.getenv('FASTAPI_PORT', 5000)),
    'reload': os.getenv('FASTAPI_RELOAD', 'True').lower() == 'true'
}
