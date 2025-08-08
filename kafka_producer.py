"""
Kafka Producer cho Real-time Pricing Data
Bắn liên tục rates và weights data để test system
"""
import json
import time
import random
from datetime import datetime
from kafka import KafkaProducer
from typing import List

class PricingDataProducer:
    """Producer để bắn pricing data liên tục"""
    
    def __init__(self, bootstrap_servers: str = 'localhost:9092'):
        self.bootstrap_servers = bootstrap_servers
        self.producer = None
        self.running = False
        
        # Sample product SKUs
        self.product_skus = [
            "RING_GOLD_001", "RING_GOLD_002", "RING_SILVER_001",
            "NECKLACE_GOLD_001", "BRACELET_GOLD_001", "EARRING_SILVER_001",
            "PENDANT_GOLD_001", "CHAIN_SILVER_001", "RING_DIAMOND_001",
            "WEDDING_RING_GOLD_001"
        ]
        
    def connect(self):
        """Kết nối tới Kafka"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda v: v.encode('utf-8') if v else None
            )
            print("✅ Connected to Kafka successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to Kafka: {e}")
            return False
            
    def publish_rate_update(self, material: str, rate: float):
        """Publish rate update"""
        if not self.producer:
            return False
            
        data = {
            "rate": rate,
            "rate_version": int(datetime.utcnow().timestamp() * 1000),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        try:
            self.producer.send('rates', key=material, value=data)
            print(f"📈 Published rate update: {material} = {rate:,.0f} VND")
            return True
        except Exception as e:
            print(f"❌ Failed to publish rate: {e}")
            return False
            
    def publish_weights_update(self, sku: str, material: str, weight_gram: float, 
                             stone_weight: float = 0, labor_cost: float = 500000, 
                             markup_percent: float = 15):
        """Publish product weights update"""
        if not self.producer:
            return False
            
        data = {
            "material": material,
            "weight_gram": weight_gram,
            "stone_weight": stone_weight,
            "labor_cost": labor_cost,
            "markup_percent": markup_percent,
            "weights_version": int(datetime.utcnow().timestamp() * 1000),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        try:
            self.producer.send('weights', key=sku, value=data)
            print(f"⚖️  Published weights: {sku} = {weight_gram}g {material}")
            return True
        except Exception as e:
            print(f"❌ Failed to publish weights: {e}")
            return False
            
    def start_continuous_publishing(self, interval_seconds: int = 10):
        """Bắt đầu bắn data liên tục"""
        if not self.connect():
            return
            
        self.running = True
        print(f"🚀 Starting continuous publishing every {interval_seconds} seconds...")
        print("Press Ctrl+C to stop")
        
        try:
            counter = 0
            while self.running:
                counter += 1
                
                # 1. Update rates (gold/silver) mỗi 30 giây
                if counter % 3 == 0:
                    # Gold rate fluctuation ±2%
                    base_gold_rate = 75500000
                    gold_rate = base_gold_rate * (1 + random.uniform(-0.02, 0.02))
                    self.publish_rate_update("gold", gold_rate)
                    
                    # Silver rate fluctuation ±3%
                    base_silver_rate = 850000
                    silver_rate = base_silver_rate * (1 + random.uniform(-0.03, 0.03))
                    self.publish_rate_update("silver", silver_rate)
                
                # 2. Update random product weights
                sku = random.choice(self.product_skus)
                material = random.choice(["gold", "silver"])
                
                # Realistic weights
                if "RING" in sku:
                    weight = random.uniform(2.0, 8.0)
                elif "NECKLACE" in sku:
                    weight = random.uniform(10.0, 25.0)
                elif "BRACELET" in sku:
                    weight = random.uniform(8.0, 15.0)
                elif "EARRING" in sku:
                    weight = random.uniform(1.5, 4.0)
                else:
                    weight = random.uniform(3.0, 12.0)
                
                stone_weight = random.uniform(0, weight * 0.1)
                labor_cost = random.uniform(300000, 800000)
                markup_percent = random.uniform(10, 25)
                
                self.publish_weights_update(
                    sku, material, weight, stone_weight, labor_cost, markup_percent
                )
                
                print(f"📊 Batch {counter} completed")
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            print("\n🛑 Stopping producer...")
            self.stop()
        except Exception as e:
            print(f"❌ Error in continuous publishing: {e}")
            
    def stop(self):
        """Dừng producer"""
        self.running = False
        if self.producer:
            self.producer.flush()
            self.producer.close()
        print("✅ Producer stopped")

def main():
    """Main function"""
    print("=== Kafka Pricing Data Producer ===")
    print("This will continuously publish pricing data to Kafka")
    print()
    
    producer = PricingDataProducer()
    
    # Test connection first
    if not producer.connect():
        print("❌ Cannot connect to Kafka. Make sure Kafka is running on localhost:9092")
        print("Run: docker-compose up -d")
        return
        
    # Publish some initial data
    print("📤 Publishing initial data...")
    
    # Initial rates
    producer.publish_rate_update("gold", 75500000)
    producer.publish_rate_update("silver", 850000)
    
    # Initial weights for all products
    for sku in producer.product_skus:
        material = "gold" if "GOLD" in sku else "silver"
        weight = random.uniform(3.0, 10.0)
        producer.publish_weights_update(sku, material, weight)
    
    print("✅ Initial data published")
    print()
    
    # Start continuous publishing
    producer.start_continuous_publishing(interval_seconds=5)

if __name__ == "__main__":
    main()
