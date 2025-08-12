"""
Data models cho real-time pricing system
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class MaterialType(str, Enum):
    GOLD = "gold"
    SILVER = "silver"

class OfflineStrategy(str, Enum):
    FREEZE = "freeze"
    SURCHARGE = "surcharge" 
    DENY = "deny"

class Rate(BaseModel):
    """Tỷ giá vàng/bạc"""
    material: MaterialType
    rate: float = Field(..., description="Giá per gram (VND)")
    currency: str = "VND"
    rate_version: int = Field(..., description="Version để handle out-of-order")
    timestamp: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z"
        }
    
class ProductWeights(BaseModel):
    """Trọng số và thông tin sản phẩm"""
    sku: str
    material: MaterialType
    weight_gram: float = Field(..., description="Trọng lượng vàng/bạc (gram)")
    stone_weight: Optional[float] = Field(0, description="Trọng lượng đá (gram)")
    labor_cost: float = Field(0, description="Chi phí gia công (VND)")
    markup_percent: float = Field(0, description="Lãi suất (%)")
    formula: str = Field("rate * weight_gram + labor_cost", description="Công thức tính giá")
    weights_version: int = Field(..., description="Version để handle out-of-order")
    timestamp: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z"
        }

class PricingSnapshot(BaseModel):
    """Snapshot giá tính toán"""
    sku: str
    base_price: float = Field(..., description="Giá cơ bản (VND)")
    final_price: float = Field(..., description="Giá cuối cùng sau markup (VND)")
    rate_used: float = Field(..., description="Tỷ giá được sử dụng")
    weight_gram: float
    stone_weight: Optional[float] = 0
    labor_cost: float = 0
    markup_percent: float = 0
    material: MaterialType
    snapshot_version: int = Field(..., description="Version để handle duplicates")
    ttl_sec: int = Field(300, description="Time to live (seconds)")
    as_of: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z"
        }
    
    @property
    def is_expired(self) -> bool:
        """Kiểm tra snapshot có hết hạn không"""
        from datetime import datetime
        return (datetime.utcnow() - self.as_of).total_seconds() > self.ttl_sec

class PricingRequest(BaseModel):
    """Request để lấy giá sản phẩm"""
    sku: str
    offline_strategy: OfflineStrategy = OfflineStrategy.FREEZE
    max_age_sec: Optional[int] = None

class PricingResponse(BaseModel):
    """Response trả về giá sản phẩm"""
    success: bool
    data: Optional[PricingSnapshot] = None
    error: Optional[str] = None
    is_cached: bool = False
    is_expired: bool = False
    strategy_applied: Optional[OfflineStrategy] = None

class RateUpdate(BaseModel):
    """Update tỷ giá từ Kafka"""
    material: MaterialType
    rate: float
    rate_version: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ProductWeights(BaseModel):
    """Trọng số sản phẩm"""
    sku: str
    material: MaterialType
    weight_gram: float
    stone_weight: float = Field(default=0, description="Trọng lượng đá (gram)")
    labor_cost: float = Field(default=0, description="Chi phí gia công (VND)")
    markup_percent: float = Field(default=0, description="% đánh giá thêm")
    weights_version: int = Field(..., description="Version để handle out-of-order")
    
class WeightsUpdate(BaseModel):
    """Update trọng số từ Kafka"""
    sku: str
    material: MaterialType
    weight_gram: float
    stone_weight: Optional[float] = 0
    labor_cost: float = 0
    markup_percent: float = 0
    weights_version: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class PricingSnapshot(BaseModel):
    """Snapshot giá sản phẩm tại thời điểm cụ thể"""
    sku: str
    material_price: float
    labor_cost: float
    stone_cost: float = 0
    total_cost: float
    final_price: float
    markup_percent: float
    weight_gram: float
    stone_weight: float = 0
    rate_version: int
    weights_version: int
    timestamp: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z"
        }
