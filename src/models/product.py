"""
Models cho quản lý mã mẫu sản phẩm (product.template) 
tích hợp với gold_attribute_line
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal

# ================================
# BASE MODELS
# ================================

class ProductTemplateBase(BaseModel):
    """Base model cho product template"""
    name: str = Field(..., description="Tên mã mẫu")
    categ_id: Optional[int] = Field(None, description="ID danh mục sản phẩm")
    default_code: Optional[str] = Field(None, description="Mã tham chiếu nội bộ")
    barcode: Optional[str] = Field(None, description="Mã vạch")
    sale_ok: bool = Field(True, description="Có thể bán")
    purchase_ok: bool = Field(True, description="Có thể mua")
    type: str = Field("product", description="Loại sản phẩm (product/consu/service)")
    list_price: Decimal = Field(0.0, description="Giá bán")
    standard_price: Decimal = Field(0.0, description="Giá vốn") 
    weight: Optional[Decimal] = Field(None, description="Trọng lượng")
    volume: Optional[Decimal] = Field(None, description="Thể tích")
    description_sale: Optional[str] = Field(None, description="Mô tả bán hàng")
    description_purchase: Optional[str] = Field(None, description="Mô tả mua hàng")
    active: bool = Field(True, description="Đang hoạt động")

class GoldAttributeValueBase(BaseModel):
    """Base model cho giá trị thuộc tính vàng"""
    attribute_id: int = Field(..., description="ID thuộc tính")
    attribute_name: str = Field(..., description="Tên thuộc tính")
    field_type: str = Field(..., description="Kiểu dữ liệu")
    value: Optional[str] = Field(None, description="Giá trị (lưu dạng text)")
    value_float: Optional[float] = Field(None, description="Giá trị số thập phân")
    value_integer: Optional[int] = Field(None, description="Giá trị số nguyên") 
    value_boolean: Optional[bool] = Field(None, description="Giá trị boolean")
    value_date: Optional[str] = Field(None, description="Giá trị ngày")
    unit: Optional[str] = Field(None, description="Đơn vị tính")

# ================================
# REQUEST MODELS
# ================================

class ProductTemplateCreate(ProductTemplateBase):
    """Model cho tạo mã mẫu mới"""
    gold_attributes: Optional[List[GoldAttributeValueBase]] = Field(default_factory=list, description="Thuộc tính vàng")

class ProductTemplateUpdate(BaseModel):
    """Model cho cập nhật mã mẫu"""
    name: Optional[str] = None
    categ_id: Optional[int] = None
    default_code: Optional[str] = None
    barcode: Optional[str] = None
    sale_ok: Optional[bool] = None
    purchase_ok: Optional[bool] = None
    type: Optional[str] = None
    list_price: Optional[Decimal] = None
    standard_price: Optional[Decimal] = None
    weight: Optional[Decimal] = None
    volume: Optional[Decimal] = None
    description_sale: Optional[str] = None
    description_purchase: Optional[str] = None
    active: Optional[bool] = None
    is_jewelry_product: Optional[bool] = None
    # Gold attributes as dict: {attribute_id: value}
    gold_attributes: Optional[Dict[str, Any]] = None

class GoldAttributeValueCreate(BaseModel):
    """Model cho tạo giá trị thuộc tính vàng"""
    product_template_id: int = Field(..., description="ID mã mẫu")
    attribute_id: int = Field(..., description="ID thuộc tính")
    value: Optional[str] = None
    value_float: Optional[float] = None
    value_integer: Optional[int] = None
    value_boolean: Optional[bool] = None
    value_date: Optional[str] = None

class GoldAttributeValueUpdate(BaseModel):
    """Model cho cập nhật giá trị thuộc tính vàng"""
    value: Optional[str] = None
    value_float: Optional[float] = None
    value_integer: Optional[int] = None
    value_boolean: Optional[bool] = None
    value_date: Optional[str] = None

# ================================
# RESPONSE MODELS
# ================================

class GoldAttributeValueResponse(GoldAttributeValueBase):
    """Response model cho giá trị thuộc tính vàng"""
    id: int
    product_template_id: int
    create_date: Optional[datetime] = None
    write_date: Optional[datetime] = None

class ProductTemplateResponse(ProductTemplateBase):
    """Response model cho mã mẫu"""
    id: int
    categ_name: Optional[str] = Field(None, description="Tên danh mục")
    uom_name: Optional[str] = Field(None, description="Tên đơn vị tính")
    uom_po_name: Optional[str] = Field(None, description="Tên đơn vị mua")
    gold_attributes: Optional[List[GoldAttributeValueResponse]] = Field(default_factory=list)
    create_date: Optional[datetime] = None
    write_date: Optional[datetime] = None
    create_uid: Optional[int] = None
    write_uid: Optional[int] = None

class ProductTemplateListResponse(BaseModel):
    """Response model cho danh sách mã mẫu"""
    id: int
    name: str
    default_code: Optional[str] = None
    categ_name: Optional[str] = None
    list_price: Decimal
    standard_price: Decimal
    type: str
    active: bool
    gold_attributes_count: int = Field(0, description="Số lượng thuộc tính vàng")

# ================================
# FILTER & PAGINATION MODELS
# ================================

class ProductTemplateFilter(BaseModel):
    """Model cho bộ lọc mã mẫu"""
    name: Optional[str] = Field(None, description="Tìm theo tên")
    categ_id: Optional[int] = Field(None, description="Lọc theo danh mục")
    default_code: Optional[str] = Field(None, description="Tìm theo mã tham chiếu")
    type: Optional[str] = Field(None, description="Lọc theo loại sản phẩm")
    active: Optional[bool] = Field(None, description="Lọc theo trạng thái")
    has_gold_attributes: Optional[bool] = Field(None, description="Có thuộc tính vàng")
    price_from: Optional[Decimal] = Field(None, description="Giá từ")
    price_to: Optional[Decimal] = Field(None, description="Giá đến")

class ProductTemplateBulkAction(BaseModel):
    """Model cho thao tác hàng loạt"""
    template_ids: List[int] = Field(..., description="Danh sách ID mã mẫu")
    action: str = Field(..., description="Hành động (activate/deactivate/delete/update_category)")
    data: Optional[Dict[str, Any]] = Field(None, description="Dữ liệu cho hành động")

# ================================
# GOLD ATTRIBUTE LINE INTEGRATION
# ================================

class GoldAttributeLineInfo(BaseModel):
    """Thông tin thuộc tính từ gold.attribute.line"""
    id: int
    name: str
    display_name: Optional[str] = None
    short_name: Optional[str] = None
    field_type: str
    required: bool = False
    editable: bool = True
    default_value: Optional[str] = None
    unit: Optional[str] = None
    description: Optional[str] = None
    validation_regex: Optional[str] = None
    selection_options: Optional[str] = None
    category: Optional[str] = None
    group_id: Optional[int] = None
    group_name: Optional[str] = None

class ProductTemplateWithAttributeSchema(BaseModel):
    """Schema kết hợp mã mẫu với thuộc tính"""
    template: ProductTemplateResponse
    available_attributes: List[GoldAttributeLineInfo]
    attribute_groups: List[Dict[str, Any]]

# ================================
# STATISTICS & ANALYTICS
# ================================

class ProductTemplateStats(BaseModel):
    """Thống kê mã mẫu"""
    total_templates: int
    active_templates: int
    inactive_templates: int
    by_category: Dict[str, int]
    by_type: Dict[str, int]
    with_gold_attributes: int
    without_gold_attributes: int
    avg_price: Decimal
    total_value: Decimal

class AttributeUsageStats(BaseModel):
    """Thống kê sử dụng thuộc tính"""
    attribute_id: int
    attribute_name: str
    usage_count: int
    templates_using: List[Dict[str, Any]]

# ================================
# IMPORT/EXPORT MODELS
# ================================

class ProductTemplateImport(BaseModel):
    """Model cho import mã mẫu"""
    templates: List[ProductTemplateCreate]
    skip_errors: bool = Field(False, description="Bỏ qua lỗi")
    update_existing: bool = Field(False, description="Cập nhật nếu đã tồn tại")

class ProductTemplateExport(BaseModel):
    """Model cho export mã mẫu"""
    template_ids: Optional[List[int]] = None
    include_attributes: bool = Field(True, description="Bao gồm thuộc tính")
    format: str = Field("json", description="Định dạng export (json/csv/xlsx)")
    filters: Optional[ProductTemplateFilter] = None
