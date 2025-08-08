"""
Kafka Consumer Service - Consume pricing data và update calculator
"""
import json
import asyncio
import threading
from datetime import datetime
from typing import Dict, Callable, Optional
from kafka import KafkaConsumer
from pricing_models import Rate, ProductWeights, PricingSnapshot, MaterialType
from pricing_calculator import PricingCalculator

class KafkaPricingConsumer:
    """Kafka consumer cho pricing system"""
    
    def __init__(self, 
                 bootstrap_servers: str = "localhost:9092",
                 group_id: str = "pricing-gateway"):
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.calculator = PricingCalculator()
        self.consumer = None
        self.running = False
        self.thread = None
        
        # Callbacks cho updates
        self.on_pricing_update: Optional[Callable[[str, PricingSnapshot], None]] = None
        
    def start(self):
        """Bắt đầu consume Kafka"""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._consume_loop, daemon=True)
        self.thread.start()
        print("Kafka pricing consumer started")
        
    def stop(self):
        """Dừng consumer"""
        self.running = False
        if self.consumer:
            self.consumer.close()
        if self.thread:
            self.thread.join(timeout=5)
        print("Kafka pricing consumer stopped")
        
    def _consume_loop(self):
        """Main consume loop"""
        try:
            self.consumer = KafkaConsumer(
                'rates', 'weights', 'pricing.snapshot',
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda m: m.decode('utf-8') if m else None,
                auto_offset_reset='latest',  # Chỉ consume message mới
                enable_auto_commit=True,
                consumer_timeout_ms=1000
            )
            
            print(f"Connected to Kafka: {self.bootstrap_servers}")
            
            while self.running:
                try:
                    msg_pack = self.consumer.poll(timeout_ms=1000)
                    for topic_partition, messages in msg_pack.items():
                        for message in messages:
                            self._process_message(message)
                except Exception as e:
                    print(f"Error in consume loop: {e}")
                    if self.running:
                        import time
                        time.sleep(1)
                        
        except Exception as e:
            print(f"Failed to connect to Kafka: {e}")
            
    def _process_message(self, message):
        """Xử lý message từ Kafka"""
        try:
            topic = message.topic
            key = message.key
            value = message.value
            
            if topic == 'rates':
                self._handle_rate_update(key, value)
            elif topic == 'weights':
                self._handle_weights_update(key, value)
            elif topic == 'pricing.snapshot':
                self._handle_pricing_snapshot(key, value)
                
        except Exception as e:
            print(f"Error processing message from {message.topic}: {e}")
            
    def _handle_rate_update(self, material: str, data: dict):
        """Xử lý update tỷ giá"""
        try:
            rate = Rate(
                material=MaterialType(material),
                rate=data['rate'],
                rate_version=data['rate_version'],
                timestamp=datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
            )
            
            updated = self.calculator.update_rate(rate)
            if updated:
                # Notify về tất cả sản phẩm bị ảnh hưởng
                self._notify_affected_products(material)
                
        except Exception as e:
            print(f"Error handling rate update for {material}: {e}")
            
    def _handle_weights_update(self, sku: str, data: dict):
        """Xử lý update trọng số sản phẩm"""
        try:
            weights = ProductWeights(
                sku=sku,
                material=MaterialType(data['material']),
                weight_gram=data['weight_gram'],
                stone_weight=data.get('stone_weight', 0),
                labor_cost=data.get('labor_cost', 0),
                markup_percent=data.get('markup_percent', 0),
                weights_version=data['weights_version'],
                timestamp=datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
            )
            
            updated = self.calculator.update_weights(weights)
            if updated:
                # Notify về sản phẩm này
                snapshot = self.calculator.get_pricing(sku)
                if snapshot and self.on_pricing_update:
                    self.on_pricing_update(sku, snapshot)
                    
        except Exception as e:
            print(f"Error handling weights update for {sku}: {e}")
            
    def _handle_pricing_snapshot(self, sku: str, data: dict):
        """Xử lý pricing snapshot từ aggregator khác"""
        try:
            snapshot = PricingSnapshot(**data)
            
            # Kiểm tra version để tránh cũ hơn
            current = self.calculator.get_pricing(sku)
            if current and snapshot.snapshot_version <= current.snapshot_version:
                return
                
            # Update cache trực tiếp
            self.calculator.pricing_cache[sku] = snapshot
            
            # Notify
            if self.on_pricing_update:
                self.on_pricing_update(sku, snapshot)
                
        except Exception as e:
            print(f"Error handling pricing snapshot for {sku}: {e}")
            
    def _notify_affected_products(self, material: str):
        """Notify về tất cả sản phẩm bị ảnh hưởng bởi thay đổi tỷ giá"""
        if not self.on_pricing_update:
            return
            
        for sku, weights in self.calculator.weights.items():
            if weights.material.value == material:
                snapshot = self.calculator.get_pricing(sku)
                if snapshot:
                    self.on_pricing_update(sku, snapshot)
                    
    def get_calculator(self) -> PricingCalculator:
        """Lấy calculator instance"""
        return self.calculator
        
    def publish_test_data(self):
        """Publish test data để test"""
        # This would normally be done by external services
        # Just for testing purposes
        print("Publishing test data...")
        
        # Test rate data
        test_rate = {
            "rate": 75500000,  # 75.5M VND per gram
            "rate_version": int(datetime.utcnow().timestamp() * 1000),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        # Test weights data  
        test_weights = {
            "material": "gold",
            "weight_gram": 5.5,
            "stone_weight": 0.2,
            "labor_cost": 500000,
            "markup_percent": 15,
            "weights_version": int(datetime.utcnow().timestamp() * 1000),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        # Simulate message processing
        self._handle_rate_update("gold", test_rate)
        self._handle_weights_update("PRODUCT_001", test_weights)
