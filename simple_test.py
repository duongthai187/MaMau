"""
Simple test để kiểm tra models trong Odoo
"""
import os
from dotenv import load_dotenv
import xmlrpc.client
import ssl

# Load .env
load_dotenv()

# Odoo config
url = os.getenv('ODOO_URL', 'http://localhost:8069')
db = os.getenv('ODOO_DB', 'odoo_db')
username = os.getenv('ODOO_USERNAME', 'admin')
password = os.getenv('ODOO_PASSWORD', 'admin')

print(f"🔌 Connecting to: {url}")
print(f"📊 Database: {db}")
print(f"👤 Username: {username}")

try:
    # SSL context if needed
    if url.startswith('https://'):
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', context=ssl_context)
        models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', context=ssl_context)
    else:
        common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
        models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
    
    # Authenticate
    uid = common.authenticate(db, username, password, {})
    if not uid:
        print("❌ Authentication failed")
        exit(1)
    
    print(f"✅ Authenticated as user ID: {uid}")
    
    # Test models
    models_to_test = [
        'product.template.attribute.group',
        'gold.attribute.line',
        'product.template',
        'product.category'
    ]
    
    print("\n🧪 Testing models...")
    for model in models_to_test:
        try:
            count = models.execute_kw(db, uid, password, model, 'search_count', [[]])
            print(f"✅ {model}: {count} records")
        except Exception as e:
            print(f"❌ {model}: {e}")
    
    print("\n🔍 Testing gold_attribute_line fields...")
    try:
        fields = models.execute_kw(db, uid, password, 'gold.attribute.line', 'fields_get', [])
        print(f"✅ gold.attribute.line has {len(fields)} fields")
        print("   Fields:", list(fields.keys())[:10])
    except Exception as e:
        print(f"❌ gold.attribute.line fields: {e}")
        
    print("\n🔍 Testing product.template.attribute.group fields...")
    try:
        fields = models.execute_kw(db, uid, password, 'product.template.attribute.group', 'fields_get', [])
        print(f"✅ product.template.attribute.group has {len(fields)} fields")
        print("   Fields:", list(fields.keys())[:10])
    except Exception as e:
        print(f"❌ product.template.attribute.group fields: {e}")

except Exception as e:
    print(f"❌ Error: {e}")
