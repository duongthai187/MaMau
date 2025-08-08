#!/usr/bin/env python3
"""
Script chạy Pricing Gateway với real-time updates
"""

import uvicorn
from pricing_gateway import app

if __name__ == "__main__":
    print("🚀 Starting Real-time Pricing Gateway...")
    print("📡 SSE endpoint: http://localhost:8001/events/pricing")
    print("🔍 Health check: http://localhost:8001/health")
    print("📚 API docs: http://localhost:8001/docs")
    print("-" * 60)
    
    uvicorn.run(
        "pricing_gateway:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
