"""
BTMH Configuration
Cấu hình kết nối Odoo và các thiết lập ứng dụng
"""
import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ================================
# ODOO CONFIGURATION
# ================================

ODOO_CONFIG = {
    'url': os.getenv('ODOO_URL', 'http://localhost:8069'),
    'db': os.getenv('ODOO_DB', 'odoo_db'),
    'username': os.getenv('ODOO_USERNAME', 'admin'),
    'password': os.getenv('ODOO_PASSWORD', 'admin'),
}

# ================================
# APPLICATION CONFIGURATION
# ================================

APP_CONFIG = {
    'host': os.getenv('APP_HOST', '0.0.0.0'),
    'port': int(os.getenv('APP_PORT', 8000)),
    'debug': os.getenv('APP_DEBUG', 'True').lower() == 'true',
    'reload': os.getenv('APP_RELOAD', 'True').lower() == 'true',
}

# ================================
# BUSINESS LOGIC CONFIGURATION
# ================================

# Gold attributes categories
GOLD_ATTRIBUTE_CATEGORIES = [
    {'value': 'technical', 'label': 'Kỹ thuật'},
    {'value': 'display', 'label': 'Hiển thị'},
    {'value': 'document', 'label': 'Tài liệu'}
]

# Field types for gold attributes
GOLD_FIELD_TYPES = [
    {'value': 'char', 'label': 'Văn bản'},
    {'value': 'float', 'label': 'Số thập phân'},
    {'value': 'integer', 'label': 'Số nguyên'},
    {'value': 'boolean', 'label': 'Đúng/Sai'},
    {'value': 'date', 'label': 'Ngày'},
    {'value': 'selection', 'label': 'Lựa chọn'}
]

# Product types
PRODUCT_TYPES = [
    {'value': 'product', 'label': 'Sản phẩm tồn kho'},
    {'value': 'consu', 'label': 'Sản phẩm tiêu hao'},
    {'value': 'service', 'label': 'Dịch vụ'}
]

# ================================
# PAGINATION SETTINGS
# ================================

PAGINATION = {
    'default_limit': 20,
    'max_limit': 100,
    'default_page': 1
}

# ================================
# LOGGING CONFIGURATION
# ================================

LOGGING_CONFIG = {
    'level': os.getenv('LOG_LEVEL', 'INFO'),
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': os.getenv('LOG_FILE', 'btmh.log')
}

# ================================
# HELPER FUNCTIONS
# ================================

def get_odoo_config() -> Dict[str, Any]:
    """Lấy cấu hình Odoo"""
    return ODOO_CONFIG.copy()

def get_app_config() -> Dict[str, Any]:
    """Lấy cấu hình ứng dụng"""
    return APP_CONFIG.copy()

def update_odoo_config(**kwargs):
    """Cập nhật cấu hình Odoo"""
    global ODOO_CONFIG
    ODOO_CONFIG.update(kwargs)

def update_app_config(**kwargs):
    """Cập nhật cấu hình ứng dụng"""
    global APP_CONFIG
    APP_CONFIG.update(kwargs)