"""
Debug trực tiếp API functions
"""
import asyncio
from main_app import get_attribute_groups, get_gold_attributes, get_categories
from fastapi import Query

async def debug_apis():
    """Debug các API functions trực tiếp"""
    print("🧪 Debugging API functions...")
    
    try:
        print("\n📊 Testing get_categories...")
        result = await get_categories()
        print(f"✅ Categories success: {len(result.data) if result.data else 0} records")
        
    except Exception as e:
        print(f"❌ Categories error: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        print("\n📁 Testing get_attribute_groups...")
        result = await get_attribute_groups(search=None, page=1, limit=5)
        print(f"✅ Attribute Groups success: {len(result.data) if result.data else 0} records")
        
    except Exception as e:
        print(f"❌ Attribute Groups error: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        print("\n🔖 Testing get_gold_attributes...")
        result = await get_gold_attributes(search=None, group_id=None, field_type=None, active=None, page=1, limit=5)
        print(f"✅ Gold Attributes success: {len(result.data) if result.data else 0} records")
        
    except Exception as e:
        print(f"❌ Gold Attributes error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_apis())
