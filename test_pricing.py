"""
Test script để verify real-time pricing system
"""
import requests
import json
import time

def test_health():
    """Test health endpoint"""
    try:
        response = requests.get("http://localhost:5000/health")
        data = response.json()
        print("🔍 Health Check:")
        print(f"  Status: {data.get('status')}")
        print(f"  Kafka Connected: {data.get('kafka_connected')}")
        print(f"  SSE Connections: {data.get('sse_connections')}")
        print(f"  Calculator Stats: {data.get('calculator_stats')}")
        return data.get('kafka_connected', False)
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_pricing_api():
    """Test pricing API"""
    print("\n🔍 Testing Pricing API:")
    
    # Test get all pricing
    try:
        response = requests.get("http://localhost:5000/api/pricing")
        data = response.json()
        print(f"  All pricing count: {data.get('count', 0)}")
        
        if data.get('data'):
            for sku, pricing in list(data['data'].items())[:3]:
                print(f"  {sku}: {pricing.get('final_price', 0):,.0f} VND")
                
    except Exception as e:
        print(f"  ❌ Get all pricing failed: {e}")
    
    # Test specific SKU
    try:
        sku = "RING_GOLD_001"
        response = requests.get(f"http://localhost:5000/api/pricing/{sku}")
        data = response.json()
        
        if data.get('success'):
            pricing = data.get('data', {})
            print(f"  {sku}: {pricing.get('final_price', 0):,.0f} VND")
            print(f"    Material: {pricing.get('material')}")
            print(f"    Weight: {pricing.get('weight_gram')}g")
            print(f"    Expired: {data.get('is_expired')}")
        else:
            print(f"  ❌ {sku}: {data.get('error')}")
            
    except Exception as e:
        print(f"  ❌ Get specific pricing failed: {e}")

def test_trigger_update():
    """Test trigger pricing update"""
    print("\n🔍 Testing Trigger Update:")
    
    try:
        response = requests.post("http://localhost:5000/test/publish")
        data = response.json()
        
        if data.get('success'):
            print(f"  ✅ {data.get('message')}")
        else:
            print(f"  ❌ {data.get('error')}")
            
    except Exception as e:
        print(f"  ❌ Trigger update failed: {e}")

def main():
    print("=== Real-time Pricing System Test ===")
    print()
    
    # Test 1: Health check
    kafka_connected = test_health()
    
    # Test 2: Pricing API
    test_pricing_api()
    
    # Test 3: Trigger update (nếu Kafka connected)
    if kafka_connected:
        test_trigger_update()
        
        # Wait và test lại để xem có update không
        print("\n⏳ Waiting 3 seconds for updates...")
        time.sleep(3)
        test_pricing_api()
    else:
        print("\n⚠️  Kafka not connected - some features may not work")
        print("💡 To enable full functionality:")
        print("   1. Run: docker-compose up -d")
        print("   2. Run: python kafka_producer.py")
        print("   3. Restart FastAPI app")
    
    print("\n✅ Test completed!")
    print("\n🌐 Available endpoints:")
    print("  - Web UI: http://localhost:5000")
    print("  - API Docs: http://localhost:5000/docs")
    print("  - Real-time Pricing: http://localhost:5000/pricing")
    print("  - Kafka UI: http://localhost:8080")

if __name__ == "__main__":
    main()
