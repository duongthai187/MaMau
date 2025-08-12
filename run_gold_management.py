"""
BTMH Gold Management Runner
Script để chạy ứng dụng quản lý thuộc tính vàng
"""
import os
import sys
import uvicorn
from main_app import app
from config import get_app_config, get_odoo_config

def main():
    """Main entry point"""
    print("🚀 BTMH Gold Management System")
    print("=" * 50)
    
    # Show configuration
    odoo_config = get_odoo_config()
    app_config = get_app_config()
    
    print(f"📊 Odoo Server: {odoo_config['url']}")
    print(f"🗄️  Database: {odoo_config['db']}")
    print(f"👤 Username: {odoo_config['username']}")
    print(f"🌐 App Host: {app_config['host']}:{app_config['port']}")
    print(f"🔄 Debug Mode: {app_config['debug']}")
    print("=" * 50)
    
    # Test Odoo connection before starting server
    print("🔌 Testing Odoo connection...")
    try:
        from odoo_client import odoo_client
        odoo_client.connect()
        print("✅ Odoo connection successful!")
    except Exception as e:
        print(f"❌ Odoo connection failed: {e}")
        print("⚠️  Server will start but may not function properly")
    
    print("\n🌐 Starting web server...")
    print(f"📱 Open browser: http://localhost:{app_config['port']}")
    print("🛑 Press Ctrl+C to stop\n")
    
    # Start server
    uvicorn.run(
        "main_app:app",
        host=app_config['host'],
        port=app_config['port'],
        reload=app_config['reload'],
        log_level="info"
    )

if __name__ == "__main__":
    main()
