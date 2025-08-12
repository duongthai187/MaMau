"""
BTMH Gold Attribute Management System
Tích hợp với module gold_attribute_line trên Odoo
CRUD cho: Nhóm thuộc tính, Thuộc tính vàng, Product Template
"""
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

def format_datetime(dt_value, format_str='%d/%m/%Y %H:%M'):
    """Helper function to safely format datetime values"""
    if dt_value is None:
        return None
    # If it's already a string, return as is (assuming it's already formatted)
    if isinstance(dt_value, str):
        return dt_value
    # If it has strftime method (datetime object), format it
    if hasattr(dt_value, 'strftime'):
        return dt_value.strftime(format_str)
    # Otherwise return as string
    return str(dt_value)

# Import Odoo client và config
from odoo_client import odoo_client
from config import get_odoo_config, GOLD_ATTRIBUTE_CATEGORIES, GOLD_FIELD_TYPES

# ================================
# MODELS
# ================================

class APIResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    message: Optional[str] = None
    total: Optional[int] = None
    page: Optional[int] = None
    limit: Optional[int] = None

# Attribute Group Models
class AttributeGroupCreate(BaseModel):
    name: str
    code: Optional[str] = None
    sequence: Optional[int] = 10

class AttributeGroupUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    sequence: Optional[int] = None

# Gold Attribute Models
class GoldAttributeCreate(BaseModel):
    name: str
    display_name: Optional[str] = None
    short_name: Optional[str] = None
    field_type: str  # char, float, integer, boolean, date, selection
    required: Optional[bool] = False
    editable: Optional[bool] = True
    active: Optional[bool] = True
    default_value: Optional[str] = None
    description: Optional[str] = None
    unit: Optional[str] = None
    validation_regex: Optional[str] = None
    selection_options: Optional[str] = None
    category: Optional[str] = "technical"  # technical, display, document
    group_id: Optional[int] = None

class GoldAttributeUpdate(BaseModel):
    name: Optional[str] = None
    display_name: Optional[str] = None
    short_name: Optional[str] = None
    field_type: Optional[str] = None
    required: Optional[bool] = None
    editable: Optional[bool] = None
    active: Optional[bool] = None
    default_value: Optional[str] = None
    description: Optional[str] = None
    unit: Optional[str] = None
    validation_regex: Optional[str] = None
    selection_options: Optional[str] = None
    category: Optional[str] = None
    group_id: Optional[int] = None

# Product Template Models
class ProductTemplateCreate(BaseModel):
    name: str
    default_code: Optional[str] = None
    categ_id: Optional[int] = None
    type: str = "product"
    sale_ok: bool = True
    purchase_ok: bool = True
    list_price: Optional[float] = 0.0
    standard_price: Optional[float] = 0.0
    description: Optional[str] = None
    gold_attributes: Optional[Dict[str, Any]] = None

class ProductTemplateUpdate(BaseModel):
    name: Optional[str] = None
    default_code: Optional[str] = None
    categ_id: Optional[int] = None
    type: Optional[str] = None
    sale_ok: Optional[bool] = None
    purchase_ok: Optional[bool] = None
    list_price: Optional[float] = None
    standard_price: Optional[float] = None
    description: Optional[str] = None
    gold_attributes: Optional[Dict[str, Any]] = None

# ================================
# APP SETUP
# ================================

app = FastAPI(
    title="BTMH Gold Attribute Management",
    description="Hệ thống quản lý thuộc tính vàng tích hợp với Odoo",
    version="3.0.0"
)

# CORS
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

# Cấu hình Odoo client từ config
odoo_config = get_odoo_config()
odoo_client.url = odoo_config['url']
odoo_client.db = odoo_config['db']
odoo_client.username = odoo_config['username']
odoo_client.password = odoo_config['password']

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    print("🚀 Starting BTMH Gold Attribute Management...")
    
    try:
        odoo_client.connect()
        print("✅ Odoo connection established")
    except Exception as e:
        print(f"❌ Odoo connection failed: {e}")

# ================================
# MAIN ROUTES
# ================================

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Trang chủ"""
    return templates.TemplateResponse("gold_management.html", {"request": request})

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test Odoo connection
        version = odoo_client.version()
        return {
            "status": "healthy",
            "odoo_connected": True,
            "odoo_version": version,
            "timestamp": datetime.utcnow().isoformat(),
            "version": "3.0.0"
        }
    except Exception as e:
        return {
            "status": "error",
            "odoo_connected": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# ================================
# ATTRIBUTE GROUPS APIs
# ================================

@app.get("/api/attribute-groups", response_model=APIResponse)
async def get_attribute_groups(
    search: Optional[str] = Query(None, description="Tìm kiếm theo tên"),
    page: int = Query(1, ge=1, description="Trang"),
    limit: int = Query(20, ge=1, le=100, description="Số record mỗi trang")
):
    """Lấy danh sách nhóm thuộc tính"""
    try:
        print(f"🔍 Getting attribute groups: search={search}, page={page}, limit={limit}")
        
        # Build search domain
        domain = []
        if search:
            domain.append(['name', 'ilike', search])
        
        # Calculate offset
        offset = (page - 1) * limit
        
        print(f"📊 Search domain: {domain}, offset: {offset}, limit: {limit}")
        
        # Get data
        groups = odoo_client.search_read(
            'product.template.attribute.group',
            domain,
            ['name', 'code', 'sequence', 'create_date', 'write_date'],
            offset=offset,
            limit=limit,
            order='sequence, name'
        )
        
        print(f"✅ Found {len(groups)} groups")
        
        # Đếm số thuộc tính trong mỗi nhóm
        for group in groups:
            try:
                attr_count = odoo_client.search_count('gold.attribute.line', [['group_id', '=', group['id']]])
                group['attribute_count'] = attr_count
            except Exception as e:
                print(f"⚠️ Error counting attributes for group {group['id']}: {e}")
                group['attribute_count'] = 0
            
            # Format dates
            group['create_date'] = format_datetime(group.get('create_date'))
            group['write_date'] = format_datetime(group.get('write_date'))
        
        # Get total count
        total = odoo_client.search_count('product.template.attribute.group', domain)
        
        print(f"📈 Total: {total}")
        
        return APIResponse(
            success=True,
            data=groups,
            total=total,
            page=page,
            limit=limit
        )
        
    except Exception as e:
        print(f"❌ Error in get_attribute_groups: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/attribute-groups/{group_id}", response_model=APIResponse)
async def get_attribute_group(group_id: int):
    """Lấy thông tin nhóm thuộc tính"""
    try:
        group = odoo_client.read('product.template.attribute.group', [group_id], [
            'name', 'code', 'sequence', 'create_date', 'write_date'
        ])
        
        if not group:
            raise HTTPException(status_code=404, detail="Không tìm thấy nhóm thuộc tính")
        
        group = group[0]
        
        # Lấy danh sách thuộc tính trong nhóm
        attributes = odoo_client.search_read(
            'gold.attribute.line',
            [['group_id', '=', group_id]],
            ['name', 'display_name', 'field_type', 'required', 'active'],
            order='name'
        )
        
        group['attributes'] = attributes
        group['attribute_count'] = len(attributes)
        
        # Format dates
        group['create_date'] = format_datetime(group.get('create_date'))
        group['write_date'] = format_datetime(group.get('write_date'))
        
        return APIResponse(success=True, data=group)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/attribute-groups", response_model=APIResponse)
async def create_attribute_group(group: AttributeGroupCreate):
    """Tạo nhóm thuộc tính mới"""
    try:
        # Validate unique name
        existing = odoo_client.search('product.template.attribute.group', [['name', '=', group.name]])
        if existing:
            raise HTTPException(status_code=400, detail="Tên nhóm đã tồn tại")
        
        # Create new group
        group_data = group.dict(exclude_none=True)
        group_id = odoo_client.create('product.template.attribute.group', group_data)
        
        # Return created group
        created_group = odoo_client.read('product.template.attribute.group', [group_id], [
            'name', 'code', 'sequence', 'create_date', 'write_date'
        ])[0]
        
        created_group['attribute_count'] = 0
        
        created_group['create_date'] = format_datetime(created_group.get('create_date'))
        created_group['write_date'] = format_datetime(created_group.get('write_date'))
        
        return APIResponse(success=True, data=created_group, message="Tạo nhóm thuộc tính thành công")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/attribute-groups/{group_id}", response_model=APIResponse)
async def update_attribute_group(group_id: int, group: AttributeGroupUpdate):
    """Cập nhật nhóm thuộc tính"""
    try:
        # Check if group exists
        existing = odoo_client.read('product.template.attribute.group', [group_id], ['id'])
        if not existing:
            raise HTTPException(status_code=404, detail="Không tìm thấy nhóm thuộc tính")
        
        # Validate unique name if updating name
        if group.name:
            duplicate = odoo_client.search('product.template.attribute.group', [
                ['name', '=', group.name],
                ['id', '!=', group_id]
            ])
            if duplicate:
                raise HTTPException(status_code=400, detail="Tên nhóm đã tồn tại")
        
        # Update group
        update_data = group.dict(exclude_none=True)
        if update_data:
            odoo_client.write('product.template.attribute.group', [group_id], update_data)
        
        # Return updated group
        updated_group = odoo_client.read('product.template.attribute.group', [group_id], [
            'name', 'code', 'sequence', 'create_date', 'write_date'
        ])[0]
        
        # Get attribute count
        attr_count = odoo_client.search_count('gold.attribute.line', [['group_id', '=', group_id]])
        updated_group['attribute_count'] = attr_count
        
        # Format dates
        updated_group['create_date'] = format_datetime(updated_group.get('create_date'))
        updated_group['write_date'] = format_datetime(updated_group.get('write_date'))
        
        return APIResponse(success=True, data=updated_group, message="Cập nhật nhóm thuộc tính thành công")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/attribute-groups/{group_id}", response_model=APIResponse)
async def delete_attribute_group(group_id: int):
    """Xóa nhóm thuộc tính"""
    try:
        # Check if group exists
        existing = odoo_client.read('product.template.attribute.group', [group_id], ['id'])
        if not existing:
            raise HTTPException(status_code=404, detail="Không tìm thấy nhóm thuộc tính")
        
        # Check if group has attributes
        attr_count = odoo_client.search_count('gold.attribute.line', [['group_id', '=', group_id]])
        if attr_count > 0:
            raise HTTPException(status_code=400, detail=f"Không thể xóa nhóm có {attr_count} thuộc tính. Vui lòng xóa các thuộc tính trước.")
        
        # Delete group
        odoo_client.unlink('product.template.attribute.group', [group_id])
        
        return APIResponse(success=True, message="Xóa nhóm thuộc tính thành công")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ================================
# GOLD ATTRIBUTES APIs
# ================================

@app.get("/api/gold-attributes", response_model=APIResponse)
async def get_gold_attributes(
    search: Optional[str] = Query(None, description="Tìm kiếm theo tên"),
    group_id: Optional[int] = Query(None, description="Lọc theo nhóm"),
    field_type: Optional[str] = Query(None, description="Lọc theo kiểu dữ liệu"),
    active: Optional[bool] = Query(None, description="Lọc theo trạng thái"),
    page: int = Query(1, ge=1, description="Trang"),
    limit: int = Query(20, ge=1, le=100, description="Số record mỗi trang")
):
    """Lấy danh sách thuộc tính vàng"""
    try:
        # Build search domain
        domain = []
        if search:
            domain.append('|')
            domain.append(['name', 'ilike', search])
            domain.append(['display_name', 'ilike', search])
        
        if group_id:
            domain.append(['group_id', '=', group_id])
        
        if field_type:
            domain.append(['field_type', '=', field_type])
        
        if active is not None:
            domain.append(['active', '=', active])
        
        # Calculate offset
        offset = (page - 1) * limit
        
        # Get data
        attributes = odoo_client.search_read(
            'gold.attribute.line',
            domain,
            ['name', 'display_name', 'short_name', 'field_type', 'required', 
             'editable', 'active', 'default_value', 'unit', 'description', 
             'category', 'group_id', 'selection_options', 'create_date', 'write_date'],
            offset=offset,
            limit=limit,
            order='name'
        )
        
        # Lấy tên groups
        group_ids = [attr['group_id'][0] for attr in attributes if attr.get('group_id')]
        group_dict = {}
        if group_ids:
            groups = odoo_client.read('product.template.attribute.group', group_ids, ['name'])
            group_dict = {g['id']: g['name'] for g in groups}
        
        # Thêm thông tin groups và format data
        for attr in attributes:
            if attr.get('group_id'):
                attr['group_name'] = group_dict.get(attr['group_id'][0], '')
            else:
                attr['group_name'] = 'Không có nhóm'
            
            # Parse selection options
            if attr.get('selection_options') and attr['field_type'] == 'selection':
                try:
                    # Split by newlines and filter empty strings
                    options = [opt.strip() for opt in attr['selection_options'].split('\n') if opt.strip()]
                    attr['selection_options_list'] = options
                except:
                    attr['selection_options_list'] = []
            else:
                attr['selection_options_list'] = []
            
            # Format dates
            attr['create_date'] = format_datetime(attr.get('create_date'))
            attr['write_date'] = format_datetime(attr.get('write_date'))
        
        # Get total count
        total = odoo_client.search_count('gold.attribute.line', domain)
        
        return APIResponse(
            success=True,
            data=attributes,
            total=total,
            page=page,
            limit=limit
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/gold-attributes/{attr_id}", response_model=APIResponse)
async def get_gold_attribute(attr_id: int):
    """Lấy thông tin thuộc tính vàng"""
    try:
        attr = odoo_client.read('gold.attribute.line', [attr_id], [
            'name', 'display_name', 'short_name', 'field_type', 'required', 
            'editable', 'active', 'default_value', 'description', 'unit',
            'validation_regex', 'selection_options', 'category', 'group_id',
            'create_date', 'write_date'
        ])
        
        if not attr:
            raise HTTPException(status_code=404, detail="Không tìm thấy thuộc tính")
        
        attr = attr[0]
        
        # Lấy tên group
        if attr.get('group_id'):
            group = odoo_client.read('product.template.attribute.group', [attr['group_id'][0]], ['name'])
            attr['group_name'] = group[0]['name'] if group else ''
        else:
            attr['group_name'] = 'Không có nhóm'
        
        # Format dates
        attr['create_date'] = format_datetime(attr.get('create_date'))
        attr['write_date'] = format_datetime(attr.get('write_date'))
        
        return APIResponse(success=True, data=attr)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/gold-attributes", response_model=APIResponse)
async def create_gold_attribute(attr: GoldAttributeCreate):
    """Tạo thuộc tính vàng mới"""
    try:
        # Validate unique name
        existing = odoo_client.search('gold.attribute.line', [['name', '=', attr.name]])
        if existing:
            raise HTTPException(status_code=400, detail="Tên thuộc tính đã tồn tại")
        
        # Validate group if provided
        if attr.group_id:
            group_exists = odoo_client.read('product.template.attribute.group', [attr.group_id], ['id'])
            if not group_exists:
                raise HTTPException(status_code=400, detail="Nhóm thuộc tính không tồn tại")
        
        # Validate field_type
        valid_types = ['char', 'float', 'integer', 'boolean', 'date', 'selection']
        if attr.field_type not in valid_types:
            raise HTTPException(status_code=400, detail=f"Kiểu dữ liệu không hợp lệ. Các kiểu hợp lệ: {', '.join(valid_types)}")
        
        # Create new attribute
        attr_data = attr.dict(exclude_none=True)
        attr_id = odoo_client.create('gold.attribute.line', attr_data)
        
        # Return created attribute
        created_attr = odoo_client.read('gold.attribute.line', [attr_id], [
            'name', 'display_name', 'short_name', 'field_type', 'required', 
            'editable', 'active', 'default_value', 'description', 'unit',
            'validation_regex', 'selection_options', 'category', 'group_id',
            'create_date', 'write_date'
        ])[0]
        
        # Lấy tên group
        if created_attr.get('group_id'):
            group = odoo_client.read('product.template.attribute.group', [created_attr['group_id'][0]], ['name'])
            created_attr['group_name'] = group[0]['name'] if group else ''
        else:
            created_attr['group_name'] = 'Không có nhóm'
        
        # Format dates
        created_attr['create_date'] = format_datetime(created_attr.get('create_date'))
        created_attr['write_date'] = format_datetime(created_attr.get('write_date'))
        
        return APIResponse(success=True, data=created_attr, message="Tạo thuộc tính vàng thành công")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/gold-attributes/{attr_id}", response_model=APIResponse)
async def update_gold_attribute(attr_id: int, attr: GoldAttributeUpdate):
    """Cập nhật thuộc tính vàng"""
    try:
        # Check if attribute exists
        existing = odoo_client.read('gold.attribute.line', [attr_id], ['id'])
        if not existing:
            raise HTTPException(status_code=404, detail="Không tìm thấy thuộc tính")
        
        # Validate unique name if updating name
        if attr.name:
            duplicate = odoo_client.search('gold.attribute.line', [
                ['name', '=', attr.name],
                ['id', '!=', attr_id]
            ])
            if duplicate:
                raise HTTPException(status_code=400, detail="Tên thuộc tính đã tồn tại")
        
        # Validate group if provided
        if attr.group_id:
            group_exists = odoo_client.read('product.template.attribute.group', [attr.group_id], ['id'])
            if not group_exists:
                raise HTTPException(status_code=400, detail="Nhóm thuộc tính không tồn tại")
        
        # Validate field_type if provided
        if attr.field_type:
            valid_types = ['char', 'float', 'integer', 'boolean', 'date', 'selection']
            if attr.field_type not in valid_types:
                raise HTTPException(status_code=400, detail=f"Kiểu dữ liệu không hợp lệ. Các kiểu hợp lệ: {', '.join(valid_types)}")
        
        # Update attribute
        update_data = attr.dict(exclude_none=True)
        if update_data:
            odoo_client.write('gold.attribute.line', [attr_id], update_data)
        
        # Return updated attribute
        updated_attr = odoo_client.read('gold.attribute.line', [attr_id], [
            'name', 'display_name', 'short_name', 'field_type', 'required', 
            'editable', 'active', 'default_value', 'description', 'unit',
            'validation_regex', 'selection_options', 'category', 'group_id',
            'create_date', 'write_date'
        ])[0]
        
        # Lấy tên group
        if updated_attr.get('group_id'):
            group = odoo_client.read('product.template.attribute.group', [updated_attr['group_id'][0]], ['name'])
            updated_attr['group_name'] = group[0]['name'] if group else ''
        else:
            updated_attr['group_name'] = 'Không có nhóm'
        
        # Format dates
        updated_attr['create_date'] = format_datetime(updated_attr.get('create_date'))
        updated_attr['write_date'] = format_datetime(updated_attr.get('write_date'))
        
        return APIResponse(success=True, data=updated_attr, message="Cập nhật thuộc tính vàng thành công")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/gold-attributes/{attr_id}", response_model=APIResponse)
async def delete_gold_attribute(attr_id: int):
    """Xóa thuộc tính vàng"""
    try:
        # Check if attribute exists
        existing = odoo_client.read('gold.attribute.line', [attr_id], ['id'])
        if not existing:
            raise HTTPException(status_code=404, detail="Không tìm thấy thuộc tính")
        
        # TODO: Check if attribute is being used by any product templates
        # Có thể thêm logic kiểm tra xem có product template nào đang sử dụng attribute này không
        
        # Delete attribute
        odoo_client.unlink('gold.attribute.line', [attr_id])
        
        return APIResponse(success=True, message="Xóa thuộc tính vàng thành công")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ================================
# PRODUCT TEMPLATES APIs
# ================================

@app.get("/api/product-templates", response_model=APIResponse)
async def get_product_templates(
    search: Optional[str] = Query(None, description="Tìm kiếm theo tên"),
    categ_id: Optional[int] = Query(None, description="Lọc theo danh mục"),
    page: int = Query(1, ge=1, description="Trang"),
    limit: int = Query(20, ge=1, le=100, description="Số record mỗi trang"),
    request: Request = None
):
    """Lấy danh sách mã mẫu sản phẩm với attribute filters"""
    try:
        print(f"🔍 Product templates request params: {dict(request.query_params)}")
        
        # Build search domain
        domain = []
        if search:
            domain.append('|')
            domain.append(['name', 'ilike', search])
            domain.append(['default_code', 'ilike', search])
        
        if categ_id:
            domain.append(['categ_id', '=', categ_id])
        
        # Handle attribute filters (attr_1=value, attr_2=value, etc.)
        attribute_filters = {}
        for param_name, param_value in request.query_params.items():
            if param_name.startswith('attr_') and param_value:
                attr_id = param_name.replace('attr_', '')
                try:
                    attribute_filters[int(attr_id)] = param_value
                except ValueError:
                    continue
        
        # Apply attribute filters to search domain  
        if attribute_filters:
            print(f"📋 Applying attribute filters: {attribute_filters}")
            
            # For attribute filtering, we'll use a simplified approach
            # Since this is a demo, we'll filter product templates based on
            # their name or other fields that might correlate with attributes
            for attr_id, attr_value in attribute_filters.items():
                print(f"  🔍 Filtering attribute {attr_id} = {attr_value}")
                
                try:
                    # Get the attribute info
                    attr_info = odoo_client.read('gold.attribute.line', [int(attr_id)], 
                                               ['field_type', 'name'])
                    if not attr_info:
                        print(f"    ❌ Attribute {attr_id} not found")
                        continue
                    
                    attr_info = attr_info[0]
                    attr_name = attr_info.get('name', f'Attribute {attr_id}')
                    field_type = attr_info.get('field_type', 'char')
                    
                    print(f"    📋 Filtering by '{attr_name}' ({field_type}) = {attr_value}")
                    
                    # For demo purposes, we'll create a simple name-based filter
                    # In real implementation, you would filter based on actual attribute relationships
                    if field_type == 'selection' and attr_value:
                        # For selection fields, add name filter
                        domain.append(['name', 'ilike', attr_value])
                        print(f"    ✅ Added name filter for selection: {attr_value}")
                    elif field_type in ['char', 'text'] and attr_value:
                        # For text fields, add description filter  
                        domain.append('|')
                        domain.append(['name', 'ilike', attr_value])
                        domain.append(['description', 'ilike', attr_value])
                        print(f"    ✅ Added text filter: {attr_value}")
                    elif field_type in ['float', 'integer'] and attr_value:
                        # For numeric fields, we might filter by price ranges
                        try:
                            numeric_value = float(attr_value)
                            if numeric_value > 0:
                                # Example: filter by list_price if it's a price-related attribute
                                domain.append(['list_price', '>=', numeric_value * 0.8])
                                domain.append(['list_price', '<=', numeric_value * 1.2])
                                print(f"    ✅ Added price range filter: {numeric_value * 0.8} - {numeric_value * 1.2}")
                        except ValueError:
                            print(f"    ❌ Invalid numeric value: {attr_value}")
                    elif field_type == 'boolean':
                        # For boolean, we might filter by active status or sale_ok
                        bool_value = attr_value.lower() in ['true', '1', 'yes', 'co']
                        domain.append(['sale_ok', '=', bool_value])
                        print(f"    ✅ Added boolean filter: sale_ok = {bool_value}")
                        
                except Exception as e:
                    print(f"    ❌ Error filtering attribute {attr_id}: {e}")
                    continue
                    
            # Log final domain
            print(f"🎯 Final search domain: {domain}")
        
        # Calculate offset
        offset = (page - 1) * limit
        
        # Get data
        templates = odoo_client.search_read(
            'product.template',
            domain,
            ['name', 'default_code', 'categ_id', 'type', 'sale_ok', 'purchase_ok',
             'list_price', 'standard_price', 'create_date', 'write_date'],
            offset=offset,
            limit=limit,
            order='name'
        )
        
        # Lấy tên categories
        categ_ids = [tmpl['categ_id'][0] for tmpl in templates if tmpl.get('categ_id')]
        categ_dict = {}
        if categ_ids:
            categories = odoo_client.read('product.category', categ_ids, ['name'])
            categ_dict = {c['id']: c['name'] for c in categories}
        
        # Thêm thông tin category và format data
        for tmpl in templates:
            if tmpl.get('categ_id'):
                tmpl['categ_name'] = categ_dict.get(tmpl['categ_id'][0], '')
            else:
                tmpl['categ_name'] = ''
            
            # Format dates
            tmpl['create_date'] = format_datetime(tmpl.get('create_date'))
            tmpl['write_date'] = format_datetime(tmpl.get('write_date'))
        
        # Get total count
        total = odoo_client.search_count('product.template', domain)
        
        return APIResponse(
            success=True,
            data=templates,
            total=total,
            page=page,
            limit=limit
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/product-templates/{template_id}", response_model=APIResponse)
async def get_product_template(template_id: int):
    """Lấy thông tin mã mẫu sản phẩm và thuộc tính vàng"""
    try:
        # Get product template info
        template = odoo_client.read('product.template', [template_id], [
            'name', 'default_code', 'categ_id', 'type', 'sale_ok', 'purchase_ok',
            'list_price', 'standard_price', 'description', 'create_date', 'write_date'
        ])
        
        if not template:
            raise HTTPException(status_code=404, detail="Không tìm thấy mã mẫu sản phẩm")
        
        template = template[0]
        
        # Get category name
        if template.get('categ_id'):
            category = odoo_client.read('product.category', [template['categ_id'][0]], ['name'])
            template['categ_name'] = category[0]['name'] if category else ''
        else:
            template['categ_name'] = ''
        
        # Get gold attributes (via product.template.attribute.line)
        # Mapping gold attributes thông qua product.attribute names bắt đầu với "gold_"
        attr_lines = odoo_client.search_read(
            'product.template.attribute.line',
            [['product_tmpl_id', '=', template_id]],
            ['attribute_id', 'value_ids']
        )
        
        gold_attributes = {}
        for line in attr_lines:
            attr_id = line['attribute_id'][0]
            attr_info = odoo_client.read('product.attribute', [attr_id], ['name', 'display_name'])
            
            if attr_info and attr_info[0]['name'].startswith('gold_'):
                # Đây là gold attribute
                gold_attr_name = attr_info[0]['name'][5:]  # Remove 'gold_' prefix
                
                # Find corresponding gold.attribute.line
                gold_attrs = odoo_client.search_read(
                    'gold.attribute.line',
                    [['name', '=', gold_attr_name]],
                    ['id', 'display_name', 'field_type', 'unit']
                )
                
                if gold_attrs:
                    gold_attr = gold_attrs[0]
                    
                    # Get values
                    if line['value_ids']:
                        values = odoo_client.read('product.attribute.value', line['value_ids'], ['name'])
                        if len(values) == 1:
                            gold_attributes[gold_attr['id']] = values[0]['name']
                        else:
                            gold_attributes[gold_attr['id']] = [v['name'] for v in values]
                    else:
                        gold_attributes[gold_attr['id']] = None
        
        template['gold_attributes'] = gold_attributes
        
        # Format dates
        template['create_date'] = format_datetime(template.get('create_date'))
        template['write_date'] = format_datetime(template.get('write_date'))
        
        return APIResponse(success=True, data=template)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ================================
# HELPER APIs
# ================================

@app.get("/api/categories", response_model=APIResponse)
async def get_categories():
    """Lấy danh sách danh mục sản phẩm"""
    try:
        categories = odoo_client.search_read(
            'product.category',
            [],
            ['name', 'parent_id'],
            order='name'
        )
        return APIResponse(success=True, data=categories)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/field-types", response_model=APIResponse)
async def get_field_types():
    """Lấy danh sách kiểu dữ liệu cho gold attributes"""
    field_types = [
        {'value': 'char', 'label': 'Văn bản'},
        {'value': 'float', 'label': 'Số thập phân'},
        {'value': 'integer', 'label': 'Số nguyên'},
        {'value': 'boolean', 'label': 'Đúng/Sai'},
        {'value': 'date', 'label': 'Ngày'},
        {'value': 'selection', 'label': 'Lựa chọn'}
    ]
    return APIResponse(success=True, data=field_types)

@app.post("/api/product-templates", response_model=APIResponse)
async def create_product_template(template: ProductTemplateCreate):
    """Tạo mã mẫu sản phẩm mới"""
    try:
        # Validate category if provided
        if template.categ_id:
            category_exists = odoo_client.read('product.category', [template.categ_id], ['id'])
            if not category_exists:
                raise HTTPException(status_code=400, detail="Danh mục sản phẩm không tồn tại")
        
        # Create basic template data
        template_data = template.dict(exclude={'gold_attributes'})
        template_data = {k: v for k, v in template_data.items() if v is not None}
        
        # Create product template
        template_id = odoo_client.create('product.template', template_data)
        
        # Process gold attributes if provided
        if template.gold_attributes:
            await _process_gold_attributes(template_id, template.gold_attributes)
        
        # Return created template
        created_template = odoo_client.read('product.template', [template_id], [
            'name', 'default_code', 'categ_id', 'type', 'sale_ok', 'purchase_ok',
            'list_price', 'standard_price', 'create_date', 'write_date'
        ])[0]
        
        # Get category name
        if created_template.get('categ_id'):
            category = odoo_client.read('product.category', [created_template['categ_id'][0]], ['name'])
            created_template['categ_name'] = category[0]['name'] if category else ''
        else:
            created_template['categ_name'] = ''
        
        # Format dates
        created_template['create_date'] = format_datetime(created_template.get('create_date'))
        created_template['write_date'] = format_datetime(created_template.get('write_date'))
        
        return APIResponse(success=True, data=created_template, message="Tạo mã mẫu sản phẩm thành công")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/product-templates/{template_id}", response_model=APIResponse)
async def update_product_template(template_id: int, template: ProductTemplateUpdate):
    """Cập nhật mã mẫu sản phẩm"""
    try:
        # Check if template exists
        existing = odoo_client.read('product.template', [template_id], ['id'])
        if not existing:
            raise HTTPException(status_code=404, detail="Không tìm thấy mã mẫu sản phẩm")
        
        # Validate category if provided
        if template.categ_id:
            category_exists = odoo_client.read('product.category', [template.categ_id], ['id'])
            if not category_exists:
                raise HTTPException(status_code=400, detail="Danh mục sản phẩm không tồn tại")
        
        # Update basic template data
        update_data = template.dict(exclude={'gold_attributes'})
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
        if update_data:
            odoo_client.write('product.template', [template_id], update_data)
        
        # Process gold attributes if provided
        if template.gold_attributes is not None:
            await _process_gold_attributes(template_id, template.gold_attributes)
        
        # Return updated template
        updated_template = odoo_client.read('product.template', [template_id], [
            'name', 'default_code', 'categ_id', 'type', 'sale_ok', 'purchase_ok',
            'list_price', 'standard_price', 'create_date', 'write_date'
        ])[0]
        
        # Get category name
        if updated_template.get('categ_id'):
            category = odoo_client.read('product.category', [updated_template['categ_id'][0]], ['name'])
            updated_template['categ_name'] = category[0]['name'] if category else ''
        else:
            updated_template['categ_name'] = ''
        
        # Format dates
        updated_template['create_date'] = format_datetime(updated_template.get('create_date'))
        updated_template['write_date'] = format_datetime(updated_template.get('write_date'))
        
        return APIResponse(success=True, data=updated_template, message="Cập nhật mã mẫu sản phẩm thành công")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/product-templates/{template_id}", response_model=APIResponse)
async def delete_product_template(template_id: int):
    """Xóa mã mẫu sản phẩm"""
    try:
        # Check if template exists
        existing = odoo_client.read('product.template', [template_id], ['id'])
        if not existing:
            raise HTTPException(status_code=404, detail="Không tìm thấy mã mẫu sản phẩm")
        
        # TODO: Check if template has variants or is used in other documents
        
        # Delete associated attribute lines first
        attr_lines = odoo_client.search('product.template.attribute.line', [['product_tmpl_id', '=', template_id]])
        if attr_lines:
            odoo_client.unlink('product.template.attribute.line', attr_lines)
        
        # Delete template
        odoo_client.unlink('product.template', [template_id])
        
        return APIResponse(success=True, message="Xóa mã mẫu sản phẩm thành công")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def _process_gold_attributes(template_id: int, gold_attributes: Dict[str, Any]):
    """Xử lý thuộc tính vàng cho product template"""
    try:
        # Remove existing attribute lines for this template
        existing_lines = odoo_client.search('product.template.attribute.line', [['product_tmpl_id', '=', template_id]])
        if existing_lines:
            odoo_client.unlink('product.template.attribute.line', existing_lines)
        
        # Process each gold attribute
        for attr_id_str, value in gold_attributes.items():
            if not value:  # Skip empty values
                continue
                
            attr_id = int(attr_id_str)
            
            # Get gold attribute info
            gold_attr = odoo_client.read('gold.attribute.line', [attr_id], ['name', 'field_type'])
            if not gold_attr:
                continue
                
            gold_attr = gold_attr[0]
            product_attr_name = f"gold_{gold_attr['name']}"
            
            # Get or create corresponding product.attribute
            product_attrs = odoo_client.search('product.attribute', [['name', '=', product_attr_name]])
            
            if not product_attrs:
                # Create product.attribute
                product_attr_id = odoo_client.create('product.attribute', {
                    'name': product_attr_name,
                    'sequence': 10,
                    'create_variant': 'no_variant'
                })
            else:
                product_attr_id = product_attrs[0]
            
            # Create or get attribute value
            value_str = str(value) if gold_attr['field_type'] != 'boolean' else ('True' if value else 'False')
            
            attr_values = odoo_client.search('product.attribute.value', [
                ['attribute_id', '=', product_attr_id],
                ['name', '=', value_str]
            ])
            
            if not attr_values:
                # Create attribute value
                attr_value_id = odoo_client.create('product.attribute.value', {
                    'name': value_str,
                    'attribute_id': product_attr_id,
                    'sequence': 10
                })
            else:
                attr_value_id = attr_values[0]
            
            # Create product.template.attribute.line
            odoo_client.create('product.template.attribute.line', {
                'product_tmpl_id': template_id,
                'attribute_id': product_attr_id,
                'value_ids': [(6, 0, [attr_value_id])]
            })
            
    except Exception as e:
        print(f"Error processing gold attributes: {e}")
@app.get("/api/categories-options", response_model=APIResponse)
async def get_categories_options():
    """Lấy danh sách phân loại cho gold attributes"""
    return APIResponse(success=True, data=GOLD_ATTRIBUTE_CATEGORIES)

@app.get("/api/product-types", response_model=APIResponse)
async def get_product_types():
    """Lấy danh sách loại sản phẩm"""
    product_types = [
        {'value': 'product', 'label': 'Sản phẩm tồn kho'},
        {'value': 'consu', 'label': 'Sản phẩm tiêu hao'},
        {'value': 'service', 'label': 'Dịch vụ'}
    ]
    return APIResponse(success=True, data=product_types)

@app.get("/api/product-template-attributes", response_model=APIResponse)
async def get_product_template_attributes():
    """Lấy danh sách thuộc tính và giá trị có trong product templates"""
    try:
        # Get all active gold attributes
        attributes = odoo_client.search_read('gold.attribute.line', 
            [['active', '=', True]], 
            ['id', 'name', 'field_type', 'selection_options'])
        
        result_attributes = []
        
        for attr in attributes:
            attr_data = {
                'id': attr['id'],
                'name': attr['name'],
                'field_type': attr['field_type'],
                'values': []
            }
            
            if attr['field_type'] == 'selection' and attr.get('selection_options'):
                # For selection type, use predefined options
                try:
                    options = [opt.strip() for opt in attr['selection_options'].split('\n') if opt.strip()]
                    attr_data['values'] = [{'value': opt, 'label': opt} for opt in options]
                except:
                    attr_data['values'] = []
                    
            elif attr['field_type'] in ['char', 'float', 'integer']:
                # For other types, we'll handle them with input fields instead of dropdowns
                # But we still include them in the list
                attr_data['values'] = []  # Will be handled differently in frontend
                
            elif attr['field_type'] == 'boolean':
                # For boolean, provide Yes/No options
                attr_data['values'] = [
                    {'value': 'true', 'label': 'Có'},
                    {'value': 'false', 'label': 'Không'}
                ]
            
            # Only include attributes that can be filtered
            if attr['field_type'] in ['selection', 'char', 'float', 'integer', 'boolean']:
                result_attributes.append(attr_data)
        
        return APIResponse(success=True, data=result_attributes)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    from config import get_app_config
    app_config = get_app_config()
    uvicorn.run(
        "main_app:app", 
        host=app_config['host'], 
        port=app_config['port'], 
        reload=app_config['reload']
    )
