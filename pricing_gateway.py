"""
FastAPI Gateway với Server-Sent Events cho real-time pricing
"""
import asyncio
import json
from datetime import datetime
from typing import Dict, Set
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
from pricing_models import PricingSnapshot, PricingRequest, PricingResponse, OfflineStrategy
from kafka_pricing_consumer import KafkaPricingConsumer

class PricingGateway:
    """FastAPI Gateway cho real-time pricing"""
    
    def __init__(self):
        self.app = FastAPI(title="Real-time Pricing Gateway", version="1.0.0")
        self.kafka_consumer = KafkaPricingConsumer()
        
        # SSE connections management
        self.sse_connections: Set[asyncio.Queue] = set()
        
        # Setup routes
        self._setup_routes()
        
        # Setup Kafka callback
        self.kafka_consumer.on_pricing_update = self._on_pricing_update
        
    def _setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.on_event("startup")
        async def startup_event():
            """Start Kafka consumer on startup"""
            self.kafka_consumer.start()
            print("Pricing Gateway started")
            
        @self.app.on_event("shutdown")
        async def shutdown_event():
            """Stop Kafka consumer on shutdown"""
            self.kafka_consumer.stop()
            print("Pricing Gateway stopped")
            
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            stats = self.kafka_consumer.get_calculator().get_stats()
            return {
                "status": "healthy",
                "kafka_connected": self.kafka_consumer.running,
                "sse_connections": len(self.sse_connections),
                "calculator_stats": stats
            }
            
        @self.app.get("/api/pricing/{sku}")
        async def get_pricing(sku: str, strategy: OfflineStrategy = OfflineStrategy.FREEZE):
            """Lấy giá sản phẩm"""
            calculator = self.kafka_consumer.get_calculator()
            snapshot = calculator.get_pricing(sku)
            
            if not snapshot:
                return PricingResponse(
                    success=False,
                    error=f"No pricing data for SKU: {sku}"
                )
                
            # Kiểm tra expiry và apply strategy
            is_expired = snapshot.is_expired
            strategy_applied = None
            
            if is_expired:
                if strategy == OfflineStrategy.DENY:
                    return PricingResponse(
                        success=False,
                        error=f"Pricing data expired for SKU: {sku}",
                        is_expired=True
                    )
                elif strategy == OfflineStrategy.SURCHARGE:
                    # Cộng thêm 5% surcharge
                    snapshot.final_price *= 1.05
                    strategy_applied = OfflineStrategy.SURCHARGE
                else:  # FREEZE
                    strategy_applied = OfflineStrategy.FREEZE
                    
            return PricingResponse(
                success=True,
                data=snapshot,
                is_cached=True,
                is_expired=is_expired,
                strategy_applied=strategy_applied
            )
            
        @self.app.get("/api/pricing")
        async def get_all_pricing():
            """Lấy tất cả giá sản phẩm"""
            calculator = self.kafka_consumer.get_calculator()
            all_pricing = calculator.get_all_pricing()
            return {
                "success": True,
                "data": all_pricing,
                "count": len(all_pricing)
            }
            
        @self.app.get("/events/pricing")
        async def pricing_events(request: Request):
            """Server-Sent Events endpoint cho pricing updates"""
            return EventSourceResponse(self._pricing_event_stream(request))
            
        @self.app.post("/test/publish")
        async def publish_test_data(background_tasks: BackgroundTasks):
            """Publish test data để test hệ thống"""
            background_tasks.add_task(self.kafka_consumer.publish_test_data)
            return {"message": "Test data publishing..."}
            
    async def _pricing_event_stream(self, request: Request):
        """SSE stream cho pricing updates"""
        # Tạo queue cho connection này
        queue = asyncio.Queue()
        self.sse_connections.add(queue)
        
        try:
            # Gửi initial data
            calculator = self.kafka_consumer.get_calculator()
            all_pricing = calculator.get_all_pricing()
            
            yield {
                "event": "initial",
                "data": json.dumps({
                    "type": "initial",
                    "pricing": {sku: snapshot.dict() for sku, snapshot in all_pricing.items()},
                    "timestamp": datetime.utcnow().isoformat()
                })
            }
            
            # Stream updates
            while True:
                try:
                    # Check if client disconnected
                    if await request.is_disconnected():
                        break
                        
                    # Wait for pricing update with timeout
                    try:
                        event_data = await asyncio.wait_for(queue.get(), timeout=30.0)
                        yield event_data
                    except asyncio.TimeoutError:
                        # Send keepalive
                        yield {
                            "event": "keepalive",
                            "data": json.dumps({
                                "type": "keepalive",
                                "timestamp": datetime.utcnow().isoformat()
                            })
                        }
                        
                except Exception as e:
                    print(f"Error in SSE stream: {e}")
                    break
                    
        finally:
            # Cleanup connection
            self.sse_connections.discard(queue)
            
    def _on_pricing_update(self, sku: str, snapshot: PricingSnapshot):
        """Callback khi có pricing update từ Kafka"""
        event_data = {
            "event": "pricing_update",
            "data": json.dumps({
                "type": "pricing_update",
                "sku": sku,
                "pricing": snapshot.dict(),
                "timestamp": datetime.utcnow().isoformat()
            })
        }
        
        # Broadcast tới tất cả SSE connections
        disconnected = set()
        for queue in self.sse_connections:
            try:
                queue.put_nowait(event_data)
            except:
                # Queue full hoặc connection dead
                disconnected.add(queue)
                
        # Cleanup dead connections
        self.sse_connections -= disconnected
        
        print(f"Broadcasted pricing update for {sku} to {len(self.sse_connections)} connections")
        
    def get_app(self) -> FastAPI:
        """Lấy FastAPI app instance"""
        return self.app

# Global instance
pricing_gateway = PricingGateway()
app = pricing_gateway.get_app()
