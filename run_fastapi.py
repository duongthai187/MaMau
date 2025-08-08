#!/usr/bin/env python3
"""
Script khởi chạy FastAPI application
"""

import uvicorn
from config import FASTAPI_CONFIG

if __name__ == "__main__":
    print("🚀 Đang khởi chạy FastAPI server...")
    print(f"📍 Host: {FASTAPI_CONFIG['host']}")
    print(f"🔌 Port: {FASTAPI_CONFIG['port']}")
    print(f" Reload: {FASTAPI_CONFIG['reload']}")
    print("-" * 50)
    
    uvicorn.run(
        "app_fastapi:app",
        host=FASTAPI_CONFIG['host'],
        port=FASTAPI_CONFIG['port'],
        reload=FASTAPI_CONFIG['reload']
    )
