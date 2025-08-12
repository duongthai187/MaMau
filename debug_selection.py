#!/usr/bin/env python3
"""
Debug script to check selection field structure
"""
from odoo_client import OdooClient
from config import ODOO_CONFIG

def main():
    try:
        # Initialize Odoo client
        odoo_client = OdooClient(
            ODOO_CONFIG['url'], 
            ODOO_CONFIG['db'], 
            ODOO_CONFIG['username'], 
            ODOO_CONFIG['password']
        )
        
        print("🔍 Checking gold attribute selection values...")
        
        # Get all gold attributes
        attrs = odoo_client.search_read('gold.attribute.line', [], [
            'id', 'name', 'field_type', 'selection_options'
        ])
        
        print(f"Found {len(attrs)} gold attributes:")
        for attr in attrs:
            print(f"\n📋 ID: {attr['id']} - {attr['name']}")
            print(f"   Type: {attr.get('field_type', 'N/A')}")
            print(f"   Selection options: {attr.get('selection_options', 'N/A')}")
            
        # Check field definition
        print("\n🔍 Checking field structure...")
        fields_info = odoo_client.fields_get('gold.attribute.line', ['selection_options', 'field_type'])
        print("Fields info:")
        for field, info in fields_info.items():
            print(f"  {field}: {info}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
