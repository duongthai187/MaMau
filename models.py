from pydantic import BaseModel
from typing import List, Optional, Dict, Any

# Category Models
class CategoryCreate(BaseModel):
    name: str
    parent_id: Optional[int] = None

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[int] = None

class Category(BaseModel):
    id: int
    name: str
    parent_id: Optional[List[Any]] = None

# Template Models
class TemplateCreate(BaseModel):
    name: str
    categ_id: int
    list_price: float = 0.0
    standard_price: float = 0.0
    type: str = "consu"
    default_code: str = ""
    template_attributes: Optional[Dict[str, str]] = {}
    variant_attributes: Optional[List[int]] = []

class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    categ_id: Optional[int] = None
    list_price: Optional[float] = None
    standard_price: Optional[float] = None
    type: Optional[str] = None
    default_code: Optional[str] = None

class Template(BaseModel):
    id: int
    name: str
    categ_id: List[Any]
    list_price: float
    standard_price: float
    type: str
    default_code: Optional[str] = None
    active: bool = True

# Product Models
class ProductCreate(BaseModel):
    name: str
    product_tmpl_id: int
    default_code: str = ""
    barcode: Optional[str] = None
    attribute_value_ids: Optional[List[int]] = []

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    default_code: Optional[str] = None
    barcode: Optional[str] = None

class Product(BaseModel):
    id: int
    name: str
    product_tmpl_id: List[Any]
    default_code: Optional[str] = None
    barcode: Optional[str] = None
    active: bool = True

# Attribute Models
class AttributeCreate(BaseModel):
    name: str
    display_type: str = "radio"
    create_variant: str = "always"

class AttributeUpdate(BaseModel):
    name: Optional[str] = None
    display_type: Optional[str] = None
    create_variant: Optional[str] = None

class Attribute(BaseModel):
    id: int
    name: str
    display_type: str
    create_variant: str
    value_ids: List[int]

# Attribute Value Models
class AttributeValueCreate(BaseModel):
    name: str
    attribute_id: int
    sequence: int = 1

class AttributeValueUpdate(BaseModel):
    name: Optional[str] = None
    sequence: Optional[int] = None

class AttributeValue(BaseModel):
    id: int
    name: str
    attribute_id: List[Any]
    sequence: int

# Serial Models
class SerialCreate(BaseModel):
    name: str
    product_id: int
    company_id: int = 1

class SerialUpdate(BaseModel):
    name: Optional[str] = None
    product_id: Optional[int] = None

class Serial(BaseModel):
    id: int
    name: str
    product_id: List[Any]
    company_id: List[Any]

# Response Models
class APIResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    message: Optional[str] = None
