"""
Test API trực tiếp để debug lỗi
"""
import requests
import json

def test_api():
    base_url = "http://localhost:8000"
    
    print("🧪 Testing APIs...")
    
    # Test categories (working)
    try:
        response = requests.get(f"{base_url}/api/categories")
        print(f"✅ Categories: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Found {len(data.get('data', []))} categories")
    except Exception as e:
        print(f"❌ Categories error: {e}")
    
    # Test attribute groups (failing)
    try:
        response = requests.get(f"{base_url}/api/attribute-groups?page=1&limit=5")
        print(f"📊 Attribute Groups: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Found {len(data.get('data', []))} groups")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Attribute Groups error: {e}")
    
    # Test gold attributes
    try:
        response = requests.get(f"{base_url}/api/gold-attributes?page=1&limit=5")
        print(f"🔖 Gold Attributes: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Found {len(data.get('data', []))} attributes")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Gold Attributes error: {e}")

if __name__ == "__main__":
    test_api()
