"""
BTMH FastAPI Application
Odoo Product CRUD Client với Real-time Pricing System và Gold Attributes Integration
"""
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks, Query
from fastapi.responses import HTMLResponse, StreamingResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
import uvicorn
import asyncio
import json
from datetime import datetime
from typing import List, Optional, Dict, Set
from decimal import Decimal
from pydantic import BaseModel

# Import từ src structure
from src.core.odoo_client import odoo_client
from src.core.config import FASTAPI_CONFIG
from src.models.base import APIResponse
from src.models.pricing import Rate, ProductWeights, OfflineStrategy, PricingRequest, PricingResponse
from src.services import gold_attribute_service
from src.services.kafka_service import KafkaPricingConsumer

# Import models cần thiết từ backup
from models import *

# ================================
# MISSING MODELS DEFINITION
# ================================
class AttributeGroupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    sequence: Optional[int] = 10
    active: bool = True

class AttributeGroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    sequence: Optional[int] = None
    active: Optional[bool] = None

class GoldAttributeCreate(BaseModel):
    name: str
    display_name: Optional[str] = None
    short_name: Optional[str] = None
    field_type: str = 'char'
    required: bool = False
    editable: bool = True
    default_value: Optional[str] = None
    unit: Optional[str] = None
    description: Optional[str] = None
    validation_regex: Optional[str] = None
    selection_options: Optional[str] = None
    category: Optional[str] = None
    active: bool = True
    group_id: Optional[int] = None
    sequence: Optional[int] = 10

class GoldAttributeUpdate(BaseModel):
    name: Optional[str] = None
    display_name: Optional[str] = None
    short_name: Optional[str] = None
    field_type: Optional[str] = None
    required: Optional[bool] = None
    editable: Optional[bool] = None
    default_value: Optional[str] = None
    unit: Optional[str] = None
    description: Optional[str] = None
    validation_regex: Optional[str] = None
    selection_options: Optional[str] = None
    category: Optional[str] = None
    active: Optional[bool] = None
    group_id: Optional[int] = None
    sequence: Optional[int] = None

class ProductTemplateCreate(BaseModel):
    name: str
    categ_id: Optional[int] = None
    type: str = 'consu'
    list_price: Optional[float] = 0.0
    standard_price: Optional[float] = 0.0
    sale_ok: bool = True
    purchase_ok: bool = True
    active: bool = True
    default_code: Optional[str] = None
    barcode: Optional[str] = None
    description: Optional[str] = None
    description_sale: Optional[str] = None
    description_purchase: Optional[str] = None
    weight: Optional[float] = None
    volume: Optional[float] = None
    uom_id: Optional[int] = None
    uom_po_id: Optional[int] = None

class ProductTemplateUpdate(BaseModel):
    name: Optional[str] = None
    categ_id: Optional[int] = None
    type: Optional[str] = None
    list_price: Optional[float] = None
    standard_price: Optional[float] = None
    sale_ok: Optional[bool] = None
    purchase_ok: Optional[bool] = None
    active: Optional[bool] = None
    default_code: Optional[str] = None
    barcode: Optional[str] = None
    description: Optional[str] = None
    description_sale: Optional[str] = None
    description_purchase: Optional[str] = None
    weight: Optional[float] = None
    volume: Optional[float] = None
    uom_id: Optional[int] = None
    uom_po_id: Optional[int] = None
    gold_attributes: Optional[Dict[int, str]] = None

# Tạo FastAPI app
app = FastAPI(
    title="BTMH - Product Management System",
    description="FastAPI client để quản lý sản phẩm Odoo với Real-time Pricing và Gold Attributes",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files và templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ================================
# APPLICATION STARTUP
# ================================

# Global variables for real-time features
sse_connections: Set = set()
kafka_consumer = None

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    print("🚀 Starting BTMH Application...")
    
    # Connect to Odoo
    try:
        odoo_client.connect()
        print("✅ Odoo connection established")
    except Exception as e:
        print(f"❌ Odoo connection failed: {e}")
        
    # Start Kafka consumer (optional)
    global kafka_consumer
    try:
        kafka_consumer = KafkaPricingConsumer()
        kafka_consumer.start()
        print("✅ Kafka pricing consumer started")
    except Exception as e:
        print(f"⚠️ Kafka consumer not available: {e}")
        print("   Application will continue without real-time pricing")

# ================================
# MAIN ROUTES
# ================================

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Trang chủ"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    global sse_connections
    try:
        calculator = kafka_consumer.get_calculator() if kafka_consumer else None
        stats = calculator.get_stats() if calculator else {}
        
        return {
            "status": "healthy",
            "kafka_connected": kafka_consumer.running if kafka_consumer else False,
            "sse_connections": len(sse_connections),
            "calculator_stats": stats,
            "timestamp": datetime.utcnow().isoformat(),
            "version": "2.0.0"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "kafka_connected": kafka_consumer.running if kafka_consumer else False,
            "timestamp": datetime.utcnow().isoformat()
        }

# ================================
# GOLD ATTRIBUTES APIs (Refactored)
# ================================

@app.get("/api/gold-attributes/filter-options", response_model=APIResponse)
async def get_gold_attributes_filter_options():
    """Lấy danh sách gold attributes để làm filter options"""
    try:
        # Lấy tất cả gold attributes
        attributes = odoo_client.search_read(
            'gold.attribute.line', 
            [['active', '=', True]], 
            ['name', 'display_name', 'short_name', 'field_type', 'unit', 'group_id']
        )
        
        # Lấy available values cho mỗi attribute
        for attr in attributes:
            attr_id = attr['id']
            # Tìm product.attribute tương ứng
            gold_attr = odoo_client.read('gold.attribute.line', [attr_id], ['name'])
            if gold_attr:
                product_attr_name = f"gold_{gold_attr[0]['name']}"
                product_attrs = odoo_client.search('product.attribute', [['name', '=', product_attr_name]])
                
                if product_attrs:
                    # Lấy các values có sẵn
                    values = odoo_client.search_read(
                        'product.attribute.value',
                        [['attribute_id', '=', product_attrs[0]]],
                        ['name']
                    )
                    attr['available_values'] = [v['name'] for v in values]
                else:
                    attr['available_values'] = []
            
            # Lấy group name
            if attr.get('group_id'):
                group = odoo_client.read('product.template.attribute.group', [attr['group_id'][0]], ['name'])
                attr['group_name'] = group[0]['name'] if group else ''
            else:
                attr['group_name'] = ''
        
        return APIResponse(success=True, data=attributes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/product-templates/{product_id}/gold-attributes", response_model=APIResponse)
async def get_product_template_gold_attributes(product_id: int):
    """Lấy thuộc tính vàng của mã mẫu sản phẩm"""
    try:
        # Lấy gold attributes đã lưu của product template này
        gold_attributes = gold_attribute_service.get_product_gold_attributes(product_id)
        
        # Lấy tất cả gold attributes available
        available_attributes = odoo_client.search_read(
            'gold.attribute.line', 
            [['active', '=', True]], 
            ['name', 'display_name', 'short_name', 'field_type', 'required', 'editable', 
             'default_value', 'unit', 'description', 'validation_regex', 'selection_options',
             'category', 'group_id']
        )
        
        # Lấy tên groups
        group_ids = [attr['group_id'][0] for attr in available_attributes if attr.get('group_id')]
        group_dict = {}
        if group_ids:
            groups = odoo_client.read('product.template.attribute.group', group_ids, ['name'])
            group_dict = {g['id']: g['name'] for g in groups}
        
        # Thêm group name vào attributes
        for attr in available_attributes:
            if attr.get('group_id'):
                attr['group_name'] = group_dict.get(attr['group_id'][0], '')
            else:
                attr['group_name'] = ''
        
        return APIResponse(success=True, data={
            'gold_attributes': gold_attributes,
            'available_attributes': available_attributes
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/product-templates/{product_id}/gold-attributes", response_model=APIResponse)
async def set_product_template_gold_attributes(product_id: int, request: Request):
    """Set thuộc tính vàng cho mã mẫu sản phẩm"""
    try:
        # Parse JSON từ request body
        body_bytes = await request.body()
        body_str = body_bytes.decode('utf-8')
        attributes_data = json.loads(body_str)
        
        # Convert keys to int
        attributes_values = {}
        for key, value in attributes_data.items():
            try:
                attr_id = int(key)
                attributes_values[attr_id] = value
            except (ValueError, TypeError):
                continue
        
        if not attributes_values:
            raise HTTPException(status_code=400, detail="No valid attribute data provided")
        
        # Bulk set attributes
        success = gold_attribute_service.bulk_set_product_gold_attributes(product_id, attributes_values)
        
        if success:
            return APIResponse(
                success=True, 
                message=f"Đã set {len(attributes_values)} gold attributes thành công"
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to set gold attributes")
            
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
# ================================
# PRODUCT TEMPLATES APIs (Core functionality)
# ================================

# Helper function for filtering
async def _filter_products_by_gold_attributes(filters: Dict[int, str]) -> List[int]:
    """Filter products theo gold attributes"""
    try:
        matching_product_ids = set()
        first_filter = True
        
        for gold_attribute_id, expected_value in filters.items():
            if not expected_value or expected_value.strip() == "":
                continue
                
            # Lấy product.attribute tương ứng
            gold_attr = odoo_client.read('gold.attribute.line', [gold_attribute_id], ['name'])
            if not gold_attr:
                continue
                
            product_attr_name = f"gold_{gold_attr[0]['name']}"
            product_attrs = odoo_client.search('product.attribute', [['name', '=', product_attr_name]])
            
            if not product_attrs:
                continue
            
            # Tìm product.attribute.value với value mong muốn
            attr_values = odoo_client.search('product.attribute.value', [
                ['attribute_id', '=', product_attrs[0]], 
                ['name', '=', expected_value]
            ])
            
            if not attr_values:
                continue
            
            # Tìm product.template.attribute.line có value này
            attr_lines = odoo_client.search('product.template.attribute.line', [
                ['attribute_id', '=', product_attrs[0]],
                ['value_ids', 'in', attr_values]
            ])
            
            # Lấy product template IDs
            if attr_lines:
                lines_data = odoo_client.read('product.template.attribute.line', attr_lines, ['product_tmpl_id'])
                current_product_ids = {line['product_tmpl_id'][0] for line in lines_data}
                
                if first_filter:
                    matching_product_ids = current_product_ids
                    first_filter = False
                else:
                    # Intersection cho AND logic
                    matching_product_ids = matching_product_ids.intersection(current_product_ids)
            else:
                # Không có products nào match filter này
                return []
        
        return list(matching_product_ids)
    except Exception as e:
        print(f"Error filtering by gold attributes: {e}")
        return []

@app.get("/api/product-templates", response_model=APIResponse)
async def get_product_templates(
    page: int = 1,
    limit: int = 20,
    search: Optional[str] = None,
    search_filter: Optional[bool] = None,  # Chỉ tìm kiếm khi có parameter này
    categ_id: Optional[int] = None,
    active: Optional[bool] = None,
    # Gold attributes filters
    gold_attribute_filters: Optional[str] = None  # JSON string chứa {attribute_id: value}
):
    """Lấy danh sách mã mẫu sản phẩm với tìm kiếm và lọc nâng cao"""
    try:
        domain = []
        
        # Chỉ áp dụng search khi có search_filter=True (tức là nhấn nút Filter)
        if search_filter and search:
            domain.extend([
                '|', '|', '|',
                ['name', 'ilike', search],
                ['default_code', 'ilike', search],
                ['description', 'ilike', search],
                ['barcode', 'ilike', search]
            ])
            
        if categ_id:
            domain.append(['categ_id', '=', categ_id])
        if active is not None:
            domain.append(['active', '=', active])
        
        # Xử lý gold attributes filters
        filtered_product_ids = None
        if gold_attribute_filters:
            try:
                import json
                filters = json.loads(gold_attribute_filters)
                if filters:
                    filtered_product_ids = await _filter_products_by_gold_attributes(filters)
                    if filtered_product_ids:
                        domain.append(['id', 'in', filtered_product_ids])
                    else:
                        # Không có products nào match filters
                        return APIResponse(success=True, data=[], total=0)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid gold_attribute_filters JSON format")
        
        # Pagination
        offset = (page - 1) * limit
        
        # Lấy dữ liệu
        total = odoo_client.search_count('product.template', domain)
        products = odoo_client.search_read(
            'product.template', 
            domain, 
            ['name', 'default_code', 'list_price', 'standard_price', 'categ_id', 'uom_id',
             'type', 'sale_ok', 'purchase_ok', 'active', 'barcode', 'description',
             'create_date', 'write_date'],
            offset=offset,
            limit=limit,
            order='name asc'
        )
        
        if not products:
            return APIResponse(success=True, data=[], total=total)
        
        # Lấy thông tin bổ sung
        categ_ids = [p['categ_id'][0] for p in products if p.get('categ_id')]
        uom_ids = [p['uom_id'][0] for p in products if p.get('uom_id')]
        
        categ_dict = {}
        uom_dict = {}
        
        if categ_ids:
            categories = odoo_client.read('product.category', categ_ids, ['name'])
            categ_dict = {c['id']: c['name'] for c in categories}
            
        if uom_ids:
            uoms = odoo_client.read('uom.uom', uom_ids, ['name'])
            uom_dict = {u['id']: u['name'] for u in uoms}
        
        # Enrich data
        for product in products:
            # Thêm tên danh mục và đơn vị tính
            if product.get('categ_id'):
                product['categ_name'] = categ_dict.get(product['categ_id'][0], '')
            else:
                product['categ_name'] = ''
                
            # Lấy gold attributes từ Odoo server
            gold_attributes = gold_attribute_service.get_product_gold_attributes(product['id'])
            product['gold_attributes'] = gold_attributes
            
            # Tạo summary ngắn cho gold attributes (hiển thị trong table)
            if gold_attributes:
                summary_parts = []
                for attr in gold_attributes[:3]:  # Chỉ hiển thị 3 đầu tiên
                    short_name = attr.get('attribute_short_name', attr.get('attribute_name', ''))
                    value = attr.get('value', '')
                    if short_name and value:
                        summary_parts.append(f"{short_name}: {value}")
                
                product['gold_attributes_summary'] = '; '.join(summary_parts)
                if len(gold_attributes) > 3:
                    product['gold_attributes_summary'] += f" (+{len(gold_attributes)-3} more)"
            else:
                product['gold_attributes_summary'] = ''
                
            if product.get('uom_id'):
                product['uom_name'] = uom_dict.get(product['uom_id'][0], '')
            else:
                product['uom_name'] = ''
        
        return APIResponse(success=True, data=products, total=total)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/product-templates", response_class=HTMLResponse)
async def product_templates_page(request: Request):
    """Giao diện quản lý mã mẫu sản phẩm"""
    response = templates.TemplateResponse("product_templates.html", {"request": request})
    # Thêm headers chống cache
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.get("/attribute-management", response_class=HTMLResponse)
async def attribute_management_page(request: Request):
    """Giao diện quản lý thuộc tính vàng"""
    response = templates.TemplateResponse("attribute_management_complete.html", {"request": request})
    # Thêm headers chống cache
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# =============================================================================
# ATTRIBUTE GROUPS CRUD APIs (Bổ sung từ app_fastapi.py)
# =============================================================================

@app.get("/api/attribute-groups", response_model=APIResponse)
async def get_attribute_groups(
    page: int = Query(1, ge=1, description="Số trang"),
    limit: int = Query(20, ge=1, le=100, description="Số bản ghi trên trang"),
    search: Optional[str] = Query(None, description="Tìm kiếm theo tên")
):
    """Lấy danh sách nhóm thuộc tính với phân trang và tìm kiếm"""
    try:
        # Tạo domain để tìm kiếm
        domain = []
        if search:
            domain.append(['name', 'ilike', search])
        
        # Tính offset cho phân trang
        offset = (page - 1) * limit
        
        # Lấy dữ liệu từ Odoo
        groups = odoo_client.search_read(
            'product.template.attribute.group',
            domain,
            ['name', 'description', 'sequence', 'active'],
            offset=offset,
            limit=limit,
            order='sequence, name'
        )
        
        # Đếm tổng số bản ghi
        total = odoo_client.search_count('product.template.attribute.group', domain)
        
        return APIResponse(success=True, data=groups, total=total)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/attribute-groups", response_model=APIResponse)
async def create_attribute_group(group: AttributeGroupCreate):
    """Tạo nhóm thuộc tính mới"""
    try:
        group_data = group.dict()
        group_id = odoo_client.create('product.template.attribute.group', group_data)
        return APIResponse(success=True, data={"id": group_id}, message="Tạo nhóm thuộc tính thành công!")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/attribute-groups/{group_id}", response_model=APIResponse)
async def get_attribute_group(group_id: int):
    """Lấy thông tin nhóm thuộc tính theo ID"""
    try:
        group = odoo_client.read('product.template.attribute.group', [group_id])
        if not group:
            raise HTTPException(status_code=404, detail="Không tìm thấy nhóm thuộc tính")
        return APIResponse(success=True, data=group[0])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/attribute-groups/{group_id}", response_model=APIResponse)
async def update_attribute_group(group_id: int, group: AttributeGroupUpdate):
    """Cập nhật nhóm thuộc tính"""
    try:
        group_data = {k: v for k, v in group.dict().items() if v is not None}
        odoo_client.write('product.template.attribute.group', group_id, group_data)
        return APIResponse(success=True, message="Cập nhật nhóm thuộc tính thành công!")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/attribute-groups/{group_id}", response_model=APIResponse)
async def delete_attribute_group(group_id: int):
    """Xóa nhóm thuộc tính"""
    try:
        # Kiểm tra xem có attribute nào đang sử dụng group này không
        attr_count = odoo_client.search_count('gold.attribute.line', [['group_id', '=', group_id]])
        if attr_count > 0:
            raise HTTPException(
                status_code=400, 
                detail=f"Không thể xóa nhóm thuộc tính vì còn {attr_count} thuộc tính đang sử dụng"
            )
        
        odoo_client.unlink('product.template.attribute.group', [group_id])
        return APIResponse(success=True, message="Xóa nhóm thuộc tính thành công!")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# GOLD ATTRIBUTES CRUD APIs (Bổ sung từ app_fastapi.py)
# =============================================================================

@app.get("/api/attributes", response_model=APIResponse)
async def get_attributes(
    page: int = Query(1, ge=1, description="Số trang"),
    limit: int = Query(20, ge=1, le=100, description="Số bản ghi trên trang"),
    search: Optional[str] = Query(None, description="Tìm kiếm theo tên"),
    group_id: Optional[int] = Query(None, description="Lọc theo nhóm thuộc tính"),
    field_type: Optional[str] = Query(None, description="Lọc theo kiểu dữ liệu"),
    active: Optional[bool] = Query(None, description="Lọc theo trạng thái hoạt động")
):
    """Lấy danh sách gold attributes với bộ lọc và phân trang"""
    try:
        # Tạo domain để tìm kiếm và lọc
        domain = []
        if search:
            domain.append(['name', 'ilike', search])
        if group_id is not None:
            domain.append(['group_id', '=', group_id])
        if field_type:
            domain.append(['field_type', '=', field_type])
        if active is not None:
            domain.append(['active', '=', active])
        
        # Tính offset cho phân trang
        offset = (page - 1) * limit
        
        # Lấy dữ liệu từ Odoo
        attributes = odoo_client.search_read(
            'gold.attribute.line',
            domain,
            ['name', 'display_name', 'short_name', 'field_type', 'required', 'editable',
             'default_value', 'unit', 'description', 'validation_regex', 'selection_options',
             'category', 'active', 'group_id', 'sequence'],
            offset=offset,
            limit=limit,
            order='sequence, name'
        )
        
        # Lấy tên nhóm thuộc tính
        group_ids = [attr['group_id'][0] for attr in attributes if attr.get('group_id')]
        group_dict = {}
        if group_ids:
            groups = odoo_client.read('product.template.attribute.group', group_ids, ['name'])
            group_dict = {g['id']: g['name'] for g in groups}
        
        # Thêm tên nhóm vào kết quả
        for attr in attributes:
            if attr.get('group_id'):
                attr['group_name'] = group_dict.get(attr['group_id'][0], '')
            else:
                attr['group_name'] = ''
        
        # Đếm tổng số bản ghi
        total = odoo_client.search_count('gold.attribute.line', domain)
        
        return APIResponse(success=True, data=attributes, total=total)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/attributes", response_model=APIResponse)
async def create_attribute(attribute: GoldAttributeCreate):
    """Tạo gold attribute mới"""
    try:
        attr_data = attribute.dict()
        attr_id = odoo_client.create('gold.attribute.line', attr_data)
        return APIResponse(success=True, data={"id": attr_id}, message="Tạo thuộc tính thành công!")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/attributes/{attribute_id}", response_model=APIResponse)
async def get_attribute(attribute_id: int):
    """Lấy thông tin gold attribute theo ID"""
    try:
        attribute = odoo_client.read('gold.attribute.line', [attribute_id])
        if not attribute:
            raise HTTPException(status_code=404, detail="Không tìm thấy thuộc tính")
        
        # Lấy tên nhóm thuộc tính
        if attribute[0].get('group_id'):
            group = odoo_client.read('product.template.attribute.group', [attribute[0]['group_id'][0]], ['name'])
            attribute[0]['group_name'] = group[0]['name'] if group else ''
        else:
            attribute[0]['group_name'] = ''
            
        return APIResponse(success=True, data=attribute[0])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/attributes/{attribute_id}", response_model=APIResponse)
async def update_attribute(attribute_id: int, attribute: GoldAttributeUpdate):
    """Cập nhật gold attribute"""
    try:
        attr_data = {k: v for k, v in attribute.dict().items() if v is not None}
        odoo_client.write('gold.attribute.line', attribute_id, attr_data)
        return APIResponse(success=True, message="Cập nhật thuộc tính thành công!")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/attributes/{attribute_id}", response_model=APIResponse)
async def delete_attribute(attribute_id: int):
    """Xóa gold attribute"""
    try:
        odoo_client.unlink('gold.attribute.line', [attribute_id])
        return APIResponse(success=True, message="Xóa thuộc tính thành công!")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# API HỖ TRỢ - LẤY DANH SÁCH TÙY CHỌN (Bổ sung từ app_fastapi.py)
# =============================================================================

@app.get("/api/options/categories", response_model=APIResponse)
async def get_category_options():
    """Lấy danh sách danh mục sản phẩm cho dropdown"""
    try:
        categories = odoo_client.search_read('product.category', [], ['name', 'complete_name'], order='complete_name')
        return APIResponse(success=True, data=categories)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/options/uoms", response_model=APIResponse)
async def get_uom_options():
    """Lấy danh sách đơn vị tính cho dropdown"""
    try:
        uoms = odoo_client.search_read('uom.uom', [], ['name', 'category_id'], order='name')
        return APIResponse(success=True, data=uoms)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/options/field-types", response_model=APIResponse)
async def get_field_type_options():
    """Lấy danh sách kiểu dữ liệu cho dropdown"""
    field_types = [
        {'id': 'char', 'name': 'Văn bản'},
        {'id': 'float', 'name': 'Số thập phân'},
        {'id': 'integer', 'name': 'Số nguyên'},
        {'id': 'boolean', 'name': 'Đúng/Sai'},
        {'id': 'date', 'name': 'Ngày'},
        {'id': 'selection', 'name': 'Lựa chọn'}
    ]
    return APIResponse(success=True, data=field_types)

@app.get("/api/options/product-types", response_model=APIResponse)
async def get_product_type_options():
    """Lấy danh sách loại sản phẩm cho dropdown"""
    product_types = [
        {'id': 'product', 'name': 'Sản phẩm có tồn kho'},
        {'id': 'consu', 'name': 'Sản phẩm tiêu hao'},
        {'id': 'service', 'name': 'Dịch vụ'}
    ]
    return APIResponse(success=True, data=product_types)

# =============================================================================
# PRODUCT TEMPLATES CRUD APIs (Bổ sung từ app_fastapi.py)
# =============================================================================

@app.post("/api/product-templates", response_model=APIResponse)
async def create_product_template(product: ProductTemplateCreate):
    """Tạo mã mẫu sản phẩm mới"""
    try:
        product_data = {k: v for k, v in product.dict().items() if v is not None}
        product_id = odoo_client.create('product.template', product_data)
        return APIResponse(success=True, data={"id": product_id}, message="Tạo mã mẫu sản phẩm thành công!")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/product-templates/{product_id}", response_model=APIResponse)
async def get_product_template(product_id: int):
    """Lấy thông tin mã mẫu sản phẩm theo ID"""
    try:
        product = odoo_client.read('product.template', [product_id], [
            'name', 'default_code', 'categ_id', 'type', 'active', 'sale_ok', 'purchase_ok',
            'list_price', 'standard_price', 'weight', 'volume', 'description', 
            'description_sale', 'description_purchase', 'barcode', 'uom_id', 'uom_po_id',
            'create_date', 'write_date'
        ])
        if not product:
            raise HTTPException(status_code=404, detail="Không tìm thấy mã mẫu sản phẩm")
        
        # Lấy tên danh mục và đơn vị tính
        if product[0].get('categ_id'):
            categ = odoo_client.read('product.category', [product[0]['categ_id'][0]], ['name'])
            product[0]['categ_name'] = categ[0]['name'] if categ else ''
        else:
            product[0]['categ_name'] = ''
            
        if product[0].get('uom_id'):
            uom = odoo_client.read('uom.uom', [product[0]['uom_id'][0]], ['name'])
            product[0]['uom_name'] = uom[0]['name'] if uom else ''
        else:
            product[0]['uom_name'] = ''
        
        # Đếm số biến thể
        variant_count = odoo_client.search_count('product.product', [['product_tmpl_id', '=', product_id]])
        product[0]['variant_count'] = variant_count
        
        # Lấy gold attributes từ Odoo server
        try:
            gold_attributes = gold_attribute_service.get_product_gold_attributes(product_id)
            product[0]['gold_attributes'] = gold_attributes
            product[0]['is_jewelry_product'] = len(gold_attributes) > 0
        except Exception as e:
            print(f"Error getting gold attributes for product {product_id}: {e}")
            product[0]['gold_attributes'] = []
            product[0]['is_jewelry_product'] = False
        
        # Tạo gold attributes summary
        gold_attributes = product[0]['gold_attributes']
        if gold_attributes:
            summary_parts = []
            for attr in gold_attributes:
                if attr.get('display_value'):
                    attr_name = attr.get('attribute_short_name') or attr.get('attribute_name', '')
                    summary_parts.append(f"{attr_name}: {attr['display_value']}")
            product[0]['gold_attributes_summary'] = '; '.join(summary_parts)
        else:
            product[0]['gold_attributes_summary'] = ''
        
        return APIResponse(success=True, data=product[0])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/product-templates/{product_id}", response_model=APIResponse)
async def update_product_template(product_id: int, product: ProductTemplateUpdate):
    """Cập nhật mã mẫu sản phẩm với gold attributes tích hợp client-side"""
    try:
        from decimal import Decimal
        
        # Lấy dữ liệu và chỉ giữ những field không None
        product_data = {}
        raw_data = product.dict(exclude_unset=True)
        
        # Extract gold_attributes để xử lý riêng ở client-side
        gold_attributes = raw_data.pop('gold_attributes', None)
        print(f"Extracted gold_attributes: {gold_attributes}, type: {type(gold_attributes)}")
        
        # Validate và clean data để tránh lỗi unhashable type
        for key, value in raw_data.items():
            if value is not None:
                # Đảm bảo không có giá trị list/dict không mong muốn
                if isinstance(value, (list, dict, set, tuple)):
                    print(f"Warning: Skipping field {key} with complex type {type(value)}")
                    continue
                    
                # Convert Decimal về float cho các field số
                if isinstance(value, Decimal):
                    product_data[key] = float(value)
                # Đảm bảo boolean fields đúng kiểu
                elif isinstance(value, bool):
                    product_data[key] = bool(value)
                # String fields
                elif isinstance(value, str):
                    product_data[key] = str(value).strip()
                # Integer fields
                elif isinstance(value, int):
                    product_data[key] = int(value)
                # Float fields
                elif isinstance(value, float):
                    product_data[key] = float(value)
                else:
                    product_data[key] = value
        
        # Kiểm tra product có tồn tại không
        existing_count = odoo_client.search_count('product.template', [['id', '=', product_id]])
        if existing_count == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy mã mẫu sản phẩm")
        
        # Update basic product fields trong Odoo (nếu có)
        if product_data:
            print(f"Updating Odoo product {product_id} with data: {product_data}")
            result = odoo_client.write('product.template', product_id, product_data)
            print(f"Odoo update result: {result}")
        
        # Update gold attributes trong Odoo server
        gold_attrs_result = None
        if gold_attributes and isinstance(gold_attributes, dict):
            print(f"Updating gold attributes for product {product_id}: {gold_attributes}")
            gold_attrs_result = gold_attribute_service.bulk_set_product_gold_attributes(product_id, gold_attributes)
            print(f"Gold attributes result: {gold_attrs_result}")
        
        # Tạo response message
        messages = []
        if product_data:
            messages.append("Cập nhật thông tin sản phẩm thành công")
        if gold_attrs_result:
            messages.append(f"Cập nhật {len(gold_attributes)} gold attributes thành công")
        elif gold_attributes and not gold_attrs_result:
            messages.append("Có lỗi khi cập nhật gold attributes")
        
        final_message = "; ".join(messages) if messages else "Cập nhật thành công"
        
        return APIResponse(
            success=True, 
            message=final_message,
            data={
                'product_updated': bool(product_data),
                'gold_attributes_updated': bool(gold_attrs_result),
                'gold_attributes_count': len(gold_attributes) if gold_attributes else 0
            }
        )
        
    except Exception as e:
        error_msg = str(e)
        print(f"Error updating product: {error_msg}")
        
        # Parse Odoo XML-RPC fault để có thông báo lỗi tốt hơn
        if "unhashable type" in error_msg:
            raise HTTPException(status_code=400, detail="Dữ liệu không hợp lệ: có field chứa giá trị phức tạp không được phép")
        elif "Access denied" in error_msg:
            raise HTTPException(status_code=403, detail="Không có quyền cập nhật sản phẩm")
        elif "TypeError" in error_msg:
            raise HTTPException(status_code=400, detail="Lỗi kiểu dữ liệu: dữ liệu gửi lên không đúng format")
        else:
            raise HTTPException(status_code=500, detail=f"Lỗi server: {error_msg}")

@app.delete("/api/product-templates/{product_id}", response_model=APIResponse)
async def delete_product_template(product_id: int):
    """Xóa mã mẫu sản phẩm"""
    try:
        # Kiểm tra xem có biến thể nào không
        variant_count = odoo_client.search_count('product.product', [['product_tmpl_id', '=', product_id]])
        if variant_count > 0:
            raise HTTPException(status_code=400, detail=f"Không thể xóa sản phẩm vì còn {variant_count} biến thể")
        
        odoo_client.unlink('product.template', [product_id])
        return APIResponse(success=True, message="Xóa mã mẫu sản phẩm thành công!")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# GOLD ATTRIBUTES OPERATIONS (Bổ sung từ app_fastapi.py)
# =============================================================================

@app.delete("/api/product-templates/{product_id}/gold-attributes", response_model=APIResponse)
async def clear_product_gold_attributes_client(product_id: int):
    """Xóa tất cả gold attributes của product"""
    try:
        success = gold_attribute_service.clear_all_product_gold_attributes(product_id)
        if success:
            return APIResponse(success=True, message="Đã xóa tất cả gold attributes")
        else:
            raise HTTPException(status_code=500, detail="Không thể xóa gold attributes")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# API THỐNG KÊ (Bổ sung từ app_fastapi.py)
# =============================================================================

@app.get("/api/product-templates/statistics", response_model=APIResponse)
async def get_product_template_statistics():
    """Lấy thống kê về mã mẫu sản phẩm"""
    try:
        # Tổng số mã mẫu
        total_templates = odoo_client.search_count('product.template', [])
        active_templates = odoo_client.search_count('product.template', [['active', '=', True]])
        inactive_templates = total_templates - active_templates
        
        # Thống kê theo danh mục
        categories = odoo_client.search_read('product.category', [], ['name'])
        by_category = {}
        for cat in categories:
            count = odoo_client.search_count('product.template', [['categ_id', '=', cat['id']]])
            if count > 0:
                by_category[cat['name']] = count
        
        # Thống kê theo loại sản phẩm
        by_type = {}
        for ptype in ['product', 'consu', 'service']:
            count = odoo_client.search_count('product.template', [['type', '=', ptype]])
            if count > 0:
                by_type[ptype] = count
        
        # Giá trung bình
        all_prices = odoo_client.search_read('product.template', [], ['list_price'])
        prices = [p['list_price'] for p in all_prices if p['list_price'] > 0]
        avg_price = sum(prices) / len(prices) if prices else 0
        total_value = sum(prices)
        
        # Lấy thống kê gold attributes từ service
        gold_stats = gold_attribute_service.get_gold_attribute_statistics()
        
        stats = {
            'total_templates': total_templates,
            'active_templates': active_templates,
            'inactive_templates': inactive_templates,
            'by_category': by_category,
            'by_type': by_type,
            'avg_price': avg_price,
            'total_value': total_value,
            'with_gold_attributes': gold_stats.get('products_with_gold_attributes', 0),
            'without_gold_attributes': gold_stats.get('products_without_gold_attributes', total_templates)
        }
        
        return APIResponse(success=True, data=stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/gold-attributes-statistics", response_model=APIResponse)
async def get_gold_attributes_statistics():
    """Lấy thống kê về gold attributes usage"""
    try:
        stats = gold_attribute_service.get_gold_attribute_statistics()
        return APIResponse(success=True, data=stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/gold-attributes", response_class=HTMLResponse)  
async def gold_attributes_page(request: Request):
    """Giao diện quản lý thuộc tính vàng (alternative route)"""
    response = templates.TemplateResponse("gold_attributes_crud.html", {"request": request})
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

if __name__ == "__main__":
    print("🚀 Starting BTMH FastAPI Server...")
    print(f"📍 Host: {FASTAPI_CONFIG['host']}")
    print(f"🔌 Port: {FASTAPI_CONFIG['port']}")
    print(f"🔄 Reload: {FASTAPI_CONFIG['reload']}")
    print("-" * 50)
    
    uvicorn.run(
        "app:app",
        host=FASTAPI_CONFIG['host'],
        port=FASTAPI_CONFIG['port'],
        reload=FASTAPI_CONFIG['reload']
    )
