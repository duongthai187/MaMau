"""
Pricing Calculator - Tính giá sản phẩm từ rates + weights
"""
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Optional
from ..models.pricing import Rate, ProductWeights, PricingSnapshot, MaterialType

class PricingCalculator:
    """Calculator để tính giá sản phẩm"""
    
    def __init__(self):
        self.rates: Dict[str, Rate] = {}  # material -> Rate
        self.weights: Dict[str, ProductWeights] = {}  # sku -> ProductWeights
        self.pricing_cache: Dict[str, PricingSnapshot] = {}  # sku -> PricingSnapshot
        
    def update_rate(self, rate: Rate) -> bool:
        """Update tỷ giá và tính lại giá các sản phẩm liên quan"""
        material = rate.material.value
        
        # Kiểm tra version để tránh out-of-order
        if material in self.rates:
            if rate.rate_version <= self.rates[material].rate_version:
                print(f"Ignore old rate version {rate.rate_version} for {material}")
                return False
                
        self.rates[material] = rate
        
        # Tính lại giá cho tất cả sản phẩm dùng material này
        affected_skus = [
            sku for sku, weights in self.weights.items() 
            if weights.material.value == material
        ]
        
        for sku in affected_skus:
            self._recalculate_pricing(sku)
            
        print(f"Updated rate for {material}: {rate.rate:,.0f} VND/gram, affected {len(affected_skus)} products")
        return True
        
    def update_weights(self, weights: ProductWeights) -> bool:
        """Update trọng số sản phẩm và tính lại giá"""
        sku = weights.sku
        
        # Kiểm tra version để tránh out-of-order
        if sku in self.weights:
            if weights.weights_version <= self.weights[sku].weights_version:
                print(f"Ignore old weights version {weights.weights_version} for {sku}")
                return False
                
        self.weights[sku] = weights
        
        # Tính lại giá cho sản phẩm này
        self._recalculate_pricing(sku)
        
        print(f"Updated weights for {sku}: {weights.weight_gram}g {weights.material.value}")
        return True
        
    def _recalculate_pricing(self, sku: str) -> Optional[PricingSnapshot]:
        """Tính lại giá cho một sản phẩm"""
        if sku not in self.weights:
            return None
            
        weights = self.weights[sku]
        material = weights.material.value
        
        if material not in self.rates:
            print(f"No rate available for material {material}, cannot price {sku}")
            return None
            
        rate = self.rates[material]
        
        # Tính giá theo công thức
        base_price = self._calculate_base_price(rate, weights)
        final_price = base_price * (1 + weights.markup_percent / 100)
        
        # Tạo snapshot mới
        snapshot = PricingSnapshot(
            sku=sku,
            base_price=base_price,
            final_price=final_price,
            rate_used=rate.rate,
            weight_gram=weights.weight_gram,
            stone_weight=weights.stone_weight,
            labor_cost=weights.labor_cost,
            markup_percent=weights.markup_percent,
            material=weights.material,
            snapshot_version=int(time.time() * 1000),  # millisecond timestamp as version
            ttl_sec=300,  # 5 minutes TTL
            as_of=datetime.utcnow()
        )
        
        self.pricing_cache[sku] = snapshot
        print(f"Calculated pricing for {sku}: {final_price:,.0f} VND")
        
        return snapshot
        
    def _calculate_base_price(self, rate: Rate, weights: ProductWeights) -> float:
        """Tính giá cơ bản theo công thức"""
        try:
            # Đơn giản hóa: rate * weight_gram + labor_cost
            # Có thể mở rộng để support công thức phức tạp hơn
            base_price = rate.rate * weights.weight_gram + weights.labor_cost
            return max(0, base_price)  # Đảm bảo không âm
        except Exception as e:
            print(f"Error calculating price for {weights.sku}: {e}")
            return 0
            
    def get_pricing(self, sku: str) -> Optional[PricingSnapshot]:
        """Lấy giá hiện tại của sản phẩm"""
        return self.pricing_cache.get(sku)
        
    def get_all_pricing(self) -> Dict[str, PricingSnapshot]:
        """Lấy tất cả giá hiện tại"""
        return self.pricing_cache.copy()
        
    def is_pricing_valid(self, sku: str) -> bool:
        """Kiểm tra giá có còn valid không"""
        snapshot = self.get_pricing(sku)
        return snapshot is not None and not snapshot.is_expired
        
    def get_stats(self) -> dict:
        """Thống kê hệ thống"""
        try:
            last_update = None
            if self.rates:
                timestamps = [r.timestamp for r in self.rates.values()]
                if timestamps:
                    # Chỉ lấy timestamp mới nhất mà không so sánh với datetime.min
                    last_update = max(timestamps).isoformat()
            
            return {
                "rates_count": len(self.rates),
                "weights_count": len(self.weights),
                "pricing_cache_count": len(self.pricing_cache),
                "valid_pricing_count": sum(1 for sku in self.pricing_cache if self.is_pricing_valid(sku)),
                "materials": list(self.rates.keys()),
                "last_update": last_update
            }
        except Exception as e:
            return {
                "rates_count": len(self.rates),
                "weights_count": len(self.weights),
                "pricing_cache_count": len(self.pricing_cache),
                "valid_pricing_count": 0,
                "materials": list(self.rates.keys()),
                "last_update": None,
                "error": str(e)
            }
    
    def get_current_rates(self) -> dict:
        """Lấy tỷ giá hiện tại"""
        current_rates = {}
        for material, rate in self.rates.items():
            current_rates[material] = {
                "rate": rate.rate,
                "timestamp": rate.timestamp.isoformat(),
                "rate_version": rate.rate_version
            }
        return current_rates
