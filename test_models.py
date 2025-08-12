"""
Test script để kiểm tra models có tồn tại trong Odoo không
"""
from odoo_client import odoo_client
from config import get_odoo_config

def test_models():
    """Test xem các models cần thiết có tồn tại không"""
    try:
        # Kết nối Odoo
        odoo_client.connect()
        
        models_to_test = [
            'product.template.attribute.group',
            'gold.attribute.line',
            'product.template',
            'product.attribute',
            'product.attribute.value',
            'product.template.attribute.line'
        ]
        
        print("🧪 Testing models existence...")
        print("=" * 50)
        
        for model in models_to_test:
            try:
                # Test access rights
                can_read = odoo_client.check_access_rights(model, 'read')
                can_write = odoo_client.check_access_rights(model, 'write')
                can_create = odoo_client.check_access_rights(model, 'create')
                can_delete = odoo_client.check_access_rights(model, 'unlink')
                
                print(f"✅ {model}")
                print(f"   Permissions: R:{can_read} W:{can_write} C:{can_create} D:{can_delete}")
                
                # Try to get count
                try:
                    count = odoo_client.search_count(model, [])
                    print(f"   Records: {count}")
                except Exception as e:
                    print(f"   Records: Error - {e}")
                
            except Exception as e:
                print(f"❌ {model} - Error: {e}")
        
        print("\n" + "=" * 50)
        print("🔍 Testing specific queries...")
        
        # Test get fields
        try:
            fields = odoo_client.get_fields('product.template.attribute.group')
            print(f"✅ product.template.attribute.group has {len(fields)} fields")
            print(f"   Available fields: {list(fields.keys())[:10]}...")
        except Exception as e:
            print(f"❌ product.template.attribute.group fields error: {e}")
            
        try:
            fields = odoo_client.get_fields('gold.attribute.line')
            print(f"✅ gold.attribute.line has {len(fields)} fields")
            print(f"   Available fields: {list(fields.keys())[:10]}...")
        except Exception as e:
            print(f"❌ gold.attribute.line fields error: {e}")
        
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    test_models()
