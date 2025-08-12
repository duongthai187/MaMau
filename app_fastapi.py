"""
FastAPI Application - Migrated from Flask
Odoo Product CRUD Client với Real-time Pricing
"""
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, StreamingResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
import unicodedata
import asyncio
import json
from datetime import datetime
from typing import List, Optional, Dict, Set
from decimal import Decimal
import uvicorn

from odoo_client import odoo_client
from config import FASTAPI_CONFIG
from models import *
from product_template_models import *
# Xóa import không cần thiết
# from gold_attribute_client_models import *
from gold_attribute_odoo_integration import gold_attribute_service
from pricing_models import PricingSnapshot, PricingRequest, PricingResponse, OfflineStrategy
from kafka_pricing_consumer import KafkaPricingConsumer

# Helper functions
async def _filter_products_by_gold_attributes(filters: Dict[int, str]) -> List[int]:
    """Filter products theo gold attributes
    Args:
        filters: {gold_attribute_id: value}
    Returns:
        List product template IDs hoặc None nếu không filter
    """
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
                # Nếu không có product.attribute nào, nghĩa là chưa có product nào có attribute này
                return []
                
            product_attr_id = product_attrs[0]
            
            # Tìm product.attribute.value có value match
            attr_values = odoo_client.search('product.attribute.value', [
                ['attribute_id', '=', product_attr_id],
                ['name', 'ilike', expected_value]
            ])
            
            if not attr_values:
                # Không có value nào match
                return []
            
            # Tìm product.template.attribute.line có value này
            attr_lines = odoo_client.search_read(
                'product.template.attribute.line',
                [
                    ['attribute_id', '=', product_attr_id],
                    ['value_ids', 'in', attr_values]
                ],
                ['product_tmpl_id']
            )
            
            current_product_ids = set(line['product_tmpl_id'][0] for line in attr_lines)
            
            if first_filter:
                matching_product_ids = current_product_ids
                first_filter = False
            else:
                # Intersection - chỉ giữ products có tất cả attributes
                matching_product_ids = matching_product_ids.intersection(current_product_ids)
            
            # Nếu không có intersection, return ngay
            if not matching_product_ids:
                return []
        
        return list(matching_product_ids)
        
    except Exception as e:
        print(f"Error filtering products by gold attributes: {e}")
        return None
from gold_models import (
    GoldAttributeCreate, 
    GoldAttributeUpdate, 
    GoldAttributeResponse,
    APIResponse as GoldAPIResponse
)
# Attribute Management Models
from attribute_management_models import (
    # Nhóm thuộc tính
    AttributeGroupBase, AttributeGroupCreate, AttributeGroupUpdate, AttributeGroupResponse,
    # Thuộc tính
    AttributeBase, AttributeCreate, AttributeUpdate, AttributeResponse,
    # Mã mẫu sản phẩm
    ProductTemplateBase, ProductTemplateCreate, ProductTemplateUpdate, ProductTemplateResponse,
    # Models chung
    APIResponse, PaginationParams, FilterParams, SelectOption, CategoryOption, UomOption,
    # Bulk operations
    BulkDeleteRequest, BulkUpdateRequest, ImportRequest
)
# Product Template Models mới
from product_template_models import (
    ProductTemplateCreate as PTCreate, ProductTemplateUpdate as PTUpdate, 
    ProductTemplateResponse as PTResponse, ProductTemplateListResponse,
    ProductTemplateFilter, ProductTemplateBulkAction, ProductTemplateWithAttributeSchema,
    GoldAttributeValueCreate, GoldAttributeValueUpdate, GoldAttributeValueResponse,
    GoldAttributeLineInfo, ProductTemplateStats, AttributeUsageStats,
    ProductTemplateImport, ProductTemplateExport
)
import json
from kafka import KafkaProducer

# Tạo FastAPI app
app = FastAPI(
    title="Quản lý mã mẫu",
    description="FastAPI client để quản lý sản phẩm Odoo thông qua XML-RPC API với Real-time Pricing",
    version="1.0.0"
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
# PRICING SYSTEM INTEGRATION
# ================================

# Kafka producer để gửi rates từ UI
class RateProducer:
    """Producer để gửi tỷ giá từ UI"""
    
    def __init__(self, bootstrap_servers: str = 'localhost:9092'):
        self.bootstrap_servers = bootstrap_servers
        self.producer = None
        
    def connect(self):
        """Kết nối tới Kafka"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda v: v.encode('utf-8') if v else None
            )
            return True
        except Exception as e:
            print(f"❌ Failed to connect to Kafka producer: {e}")
            return False
            
    def publish_rate(self, material: str, rate: float):
        """Publish rate update từ UI"""
        if not self.producer:
            if not self.connect():
                return False
                
        data = {
            "rate": rate,
            "rate_version": int(datetime.utcnow().timestamp() * 1000),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        try:
            self.producer.send('rates', key=material, value=data)
            self.producer.flush()  # Ensure immediate delivery
            return True
        except Exception as e:
            print(f"❌ Failed to publish rate: {e}")
            return False

# Kafka consumer cho real-time pricing
kafka_consumer = KafkaPricingConsumer()

# Kafka producer cho UI input
rate_producer = RateProducer()

# SSE connections management
sse_connections: Set[asyncio.Queue] = set()

def on_pricing_update(sku: str, snapshot: PricingSnapshot):
    """Callback khi có pricing update từ Kafka"""
    global sse_connections
    
    # Sử dụng json() method của Pydantic để handle datetime serialization
    snapshot_json = snapshot.json()
    snapshot_dict = json.loads(snapshot_json)
    
    event_data = {
        "event": "pricing_update",
        "data": json.dumps({
            "type": "pricing_update",
            "sku": sku,
            "pricing": snapshot_dict,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
    }
    
    # Broadcast tới tất cả SSE connections
    disconnected = set()
    for queue in sse_connections:
        try:
            queue.put_nowait(event_data)
        except:
            # Queue full hoặc connection dead
            disconnected.add(queue)
            
    # Cleanup dead connections
    sse_connections -= disconnected
    
    print(f"Broadcasted pricing update for {sku} to {len(sse_connections)} connections")
    sse_connections -= disconnected
    
    print(f"Broadcasted pricing update for {sku} to {len(sse_connections)} connections")

# Setup Kafka callback
kafka_consumer.on_pricing_update = on_pricing_update

# Kết nối Odoo và khởi động pricing system khi khởi động
@app.on_event("startup")
async def startup_event():
    odoo_client.connect()
    # Khởi động Kafka consumer trong background thread (không phải async)
    try:
        kafka_consumer.start()
        print("Kafka pricing consumer started successfully")
    except Exception as e:
        print(f"Warning: Could not start Kafka consumer: {e}")
        print("Application will continue without real-time pricing updates")

# ================================
# HTML ROUTES
# ================================

# Route chính - chuyển hướng đến trang quản lý
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Trang chủ - hiển thị thông tin về hệ thống"""
    return templates.TemplateResponse("index.html", {"request": request})

# Route trang chủ phụ
@app.get("/home", response_class=HTMLResponse) 
async def home(request: Request):
    """Trang chủ phụ"""
    return templates.TemplateResponse("index.html", {"request": request})

# ================================
# REAL-TIME PRICING APIs
# ================================

@app.get("/events/pricing")
async def pricing_events(request: Request):
    """Server-Sent Events cho real-time pricing updates"""
    global sse_connections
    
    async def event_stream():
        queue = asyncio.Queue()
        sse_connections.add(queue)  # sse_connections được access từ global scope trong function cha
        
        try:
            # Gửi connection established event
            yield {
                "event": "connected",
                "data": json.dumps({
                    "type": "connected", 
                    "message": "SSE connection established",
                    "timestamp": datetime.utcnow().isoformat()
                })
            }
            
            while True:
                try:
                    # Đợi event từ queue hoặc timeout sau 30s để gửi keepalive
                    event = await asyncio.wait_for(queue.get(), timeout=30)
                    yield event
                except asyncio.TimeoutError:
                    # Gửi keepalive event
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
            sse_connections.discard(queue)
            
    return EventSourceResponse(event_stream())

@app.get("/api/pricing/{sku}")
async def get_pricing(sku: str, strategy: OfflineStrategy = OfflineStrategy.FREEZE):
    """Lấy giá sản phẩm theo SKU"""
    calculator = kafka_consumer.get_calculator()
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

@app.get("/api/pricing")
async def get_all_pricing():
    """Lấy tất cả giá sản phẩm hiện tại"""
    calculator = kafka_consumer.get_calculator()
    all_pricing = calculator.get_all_pricing()
    return {
        "success": True,
        "data": all_pricing,
        "count": len(all_pricing),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/test/publish")
async def test_publish_pricing(background_tasks: BackgroundTasks):
    """Test endpoint để trigger pricing updates"""
    
    def publish_test_data():
        calculator = kafka_consumer.get_calculator()
        
        # Test rate update
        from pricing_models import Rate, ProductWeights
        
        rate = Rate(
            material="gold", 
            rate=75500000,
            rate_version=int(datetime.utcnow().timestamp() * 1000),
            timestamp=datetime.utcnow()
        )
        calculator.update_rate(rate)
        
        # Test weights update
        weights = ProductWeights(
            sku="TEST_PRODUCT_001",
            material="gold",
            weight_gram=5.5,
            stone_weight=0.2,
            labor_cost=500000,
            markup_percent=15,
            weights_version=int(datetime.utcnow().timestamp() * 1000)
        )
        calculator.update_weights(weights)
        
        # Trigger pricing calculation
        snapshot = calculator.get_pricing("TEST_PRODUCT_001")
        if snapshot:
            on_pricing_update("TEST_PRODUCT_001", snapshot)
    
    background_tasks.add_task(publish_test_data)
    
    return {
        "success": True,
        "message": "Test pricing data published",
        "timestamp": datetime.utcnow().isoformat()
    }

# ================================
# RATE MANAGEMENT API (UI Input)
# ================================

@app.post("/api/rates/update")
async def update_rate_from_ui(request: dict):
    """Update tỷ giá từ UI và gửi qua Kafka"""
    try:
        material = request.get("material")
        rate = float(request.get("rate", 0))
        
        if not material or rate <= 0:
            raise HTTPException(status_code=400, detail="Material và rate phải có giá trị hợp lệ")
        
        if material not in ["gold", "silver"]:
            raise HTTPException(status_code=400, detail="Material phải là 'gold' hoặc 'silver'")
        
        # Gửi qua Kafka
        success = rate_producer.publish_rate(material, rate)
        
        if not success:
            raise HTTPException(status_code=500, detail="Không thể gửi dữ liệu qua Kafka")
        
        return {
            "success": True,
            "message": f"Đã cập nhật tỷ giá {material}: {rate:,.0f} VND",
            "data": {
                "material": material,
                "rate": rate,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Rate phải là số")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi: {str(e)}")

@app.get("/api/rates/current")
async def get_current_rates():
    """Lấy tỷ giá hiện tại"""
    try:
        calculator = kafka_consumer.get_calculator()
        rates = calculator.get_current_rates()
        
        return {
            "success": True,
            "data": rates,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi: {str(e)}")

# ATTRIBUTE MANAGEMENT ROUTES 
# =============================================================================

# Route cho giao diện quản lý
@app.get("/attribute-management", response_class=HTMLResponse)
async def attribute_management(request: Request):
    """Giao diện quản lý hoàn chỉnh cho nhóm thuộc tính và thuộc tính vàng"""
    response = templates.TemplateResponse("attribute_management_complete.html", {"request": request})
    # Thêm headers chống cache để đảm bảo UI mới được load
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.get("/product-templates", response_class=HTMLResponse)
async def product_templates_page(request: Request):
    """Giao diện quản lý mã mẫu sản phẩm"""
    response = templates.TemplateResponse("product_templates.html", {"request": request})
    # Thêm headers chống cache
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# =============================================================================
# 1. API CRUD CHO NHÓM THUỘC TÍNH (product.template.attribute.group)
# =============================================================================

@app.get("/api/attribute-groups", response_model=APIResponse)
async def get_attribute_groups(
    page: int = 1, 
    limit: int = 20, 
    search: Optional[str] = None
):
    """Lấy danh sách nhóm thuộc tính"""
    try:
        domain = []
        if search:
            domain.append(['name', 'ilike', search])
        
        # Lấy dữ liệu với pagination - chỉ lấy field có trong model thực tế
        offset = (page - 1) * limit
        groups = odoo_client.search_read(
            'product.template.attribute.group', 
            domain, 
            ['name', 'code', 'sequence', 'create_date', 'write_date'],
            offset=offset,
            limit=limit,
            order='sequence,name'
        )
        
        # Đếm tổng số bản ghi
        total = odoo_client.search_count('product.template.attribute.group', domain)
        
        # Đếm số thuộc tính trong mỗi nhóm
        for group in groups:
            attr_count = odoo_client.search_count('gold.attribute.line', [['group_id', '=', group['id']]])
            group['attribute_count'] = attr_count
        
        return APIResponse(success=True, data=groups, total=total)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/attribute-groups", response_model=APIResponse)
async def create_attribute_group(group: AttributeGroupCreate):
    """Tạo nhóm thuộc tính mới"""
    try:
        group_data = {k: v for k, v in group.dict().items() if v is not None}
        group_id = odoo_client.create('product.template.attribute.group', group_data)
        return APIResponse(success=True, data={"id": group_id}, message="Tạo nhóm thuộc tính thành công!")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/attribute-groups/{group_id}", response_model=APIResponse)
async def get_attribute_group(group_id: int):
    """Lấy thông tin nhóm thuộc tính theo ID"""
    try:
        group = odoo_client.read('product.template.attribute.group', [group_id], [
            'name', 'code', 'sequence', 'create_date', 'write_date'
        ])
        if not group:
            raise HTTPException(status_code=404, detail="Không tìm thấy nhóm thuộc tính")
        
        # Đếm số thuộc tính trong nhóm
        attr_count = odoo_client.search_count('gold.attribute.line', [['group_id', '=', group_id]])
        group[0]['attribute_count'] = attr_count
        
        return APIResponse(success=True, data=group[0])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/attribute-groups/{group_id}", response_model=APIResponse)
async def update_attribute_group(group_id: int, group: AttributeGroupUpdate):
    """Cập nhật nhóm thuộc tính"""
    try:
        group_data = {k: v for k, v in group.dict().items() if v is not None}
        if not group_data:
            raise HTTPException(status_code=400, detail="Không có dữ liệu để cập nhật")
        
        odoo_client.write('product.template.attribute.group', [group_id], group_data)
        return APIResponse(success=True, message="Cập nhật nhóm thuộc tính thành công!")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/attribute-groups/{group_id}", response_model=APIResponse)
async def delete_attribute_group(group_id: int):
    """Xóa nhóm thuộc tính"""
    try:
        # Kiểm tra xem có thuộc tính nào đang sử dụng nhóm này không
        attr_count = odoo_client.search_count('gold.attribute.line', [['group_id', '=', group_id]])
        if attr_count > 0:
            raise HTTPException(status_code=400, detail=f"Không thể xóa nhóm vì còn {attr_count} thuộc tính đang sử dụng")
        
        odoo_client.unlink('product.template.attribute.group', [group_id])
        return APIResponse(success=True, message="Xóa nhóm thuộc tính thành công!")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# 2. API CRUD CHO THUỘC TÍNH (gold.attribute.line)
# =============================================================================

@app.get("/api/attributes", response_model=APIResponse)
async def get_attributes(
    page: int = 1,
    limit: int = 20,
    search: Optional[str] = None,
    group_id: Optional[int] = None,
    field_type: Optional[str] = None,
    active: Optional[bool] = None
):
    """Lấy danh sách thuộc tính"""
    try:
        domain = []
        if search:
            domain.append(['|', ['name', 'ilike', search], ['display_name', 'ilike', search]])
        if group_id:
            domain.append(['group_id', '=', group_id])
        if field_type:
            domain.append(['field_type', '=', field_type])
        if active is not None:
            domain.append(['active', '=', active])
        
        # Lấy dữ liệu với pagination
        offset = (page - 1) * limit
        attributes = odoo_client.search_read(
            'gold.attribute.line', 
            domain, 
            ['name', 'display_name', 'short_name', 'field_type', 'group_id', 'required', 
             'editable', 'active', 'default_value', 'description', 'unit',
             'validation_regex', 'selection_options', 'category', 'create_date', 'write_date'],
            offset=offset,
            limit=limit,
            order='group_id,name'
        )
        
        # Lấy tên nhóm cho mỗi thuộc tính
        group_ids = [attr['group_id'][0] for attr in attributes if attr.get('group_id')]
        if group_ids:
            groups = odoo_client.read('product.template.attribute.group', group_ids, ['name'])
            group_dict = {g['id']: g['name'] for g in groups}
            
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
async def create_attribute(attribute: AttributeCreate):
    """Tạo thuộc tính mới"""
    try:
        attribute_data = {k: v for k, v in attribute.dict().items() if v is not None}
        attribute_id = odoo_client.create('gold.attribute.line', attribute_data)
        return APIResponse(success=True, data={"id": attribute_id}, message="Tạo thuộc tính thành công!")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/attributes/{attribute_id}", response_model=APIResponse)
async def get_attribute(attribute_id: int):
    """Lấy thông tin thuộc tính theo ID"""
    try:
        attribute = odoo_client.read('gold.attribute.line', [attribute_id], [
            'name', 'display_name', 'short_name', 'field_type', 'group_id', 'required', 
            'editable', 'active', 'default_value', 'description', 'unit',
            'validation_regex', 'selection_options', 'category', 'create_date', 'write_date'
        ])
        if not attribute:
            raise HTTPException(status_code=404, detail="Không tìm thấy thuộc tính")
        
        # Lấy tên nhóm
        if attribute[0].get('group_id'):
            group = odoo_client.read('product.template.attribute.group', [attribute[0]['group_id'][0]], ['name'])
            attribute[0]['group_name'] = group[0]['name'] if group else ''
        else:
            attribute[0]['group_name'] = ''
        
        return APIResponse(success=True, data=attribute[0])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/gold-attributes/filter-options", response_model=APIResponse)
async def get_gold_attributes_filter_options():
    """Lấy danh sách gold attributes để làm filter options"""
    try:
        # Lấy tất cả gold attributes active
        attributes, _ = gold_attribute_service.get_gold_attributes()
        
        filter_options = []
        for attr in attributes:
            if not attr.get('active', True):
                continue
                
            # Lấy danh sách values có sẵn cho attribute này
            gold_attr_name = f"gold_{attr['name']}"
            product_attrs = odoo_client.search('product.attribute', [['name', '=', gold_attr_name]])
            
            available_values = []
            if product_attrs:
                attr_values = odoo_client.search_read(
                    'product.attribute.value',
                    [['attribute_id', '=', product_attrs[0]]],
                    ['name'],
                    order='name'
                )
                available_values = [v['name'] for v in attr_values]
            
            filter_options.append({
                'id': attr['id'],
                'name': attr['name'],
                'display_name': attr.get('display_name') or attr['name'],
                'short_name': attr.get('short_name', ''),
                'field_type': attr.get('field_type', 'char'),
                'unit': attr.get('unit', ''),
                'group_name': attr.get('group_name', ''),
                'available_values': available_values
            })
        
        return APIResponse(success=True, data=filter_options)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/attributes/{attribute_id}", response_model=APIResponse)
async def update_attribute(attribute_id: int, attribute: AttributeUpdate):
    """Cập nhật thuộc tính"""
    try:
        attribute_data = {k: v for k, v in attribute.dict().items() if v is not None}
        if not attribute_data:
            raise HTTPException(status_code=400, detail="Không có dữ liệu để cập nhật")
        
        odoo_client.write('gold.attribute.line', [attribute_id], attribute_data)
        return APIResponse(success=True, message="Cập nhật thuộc tính thành công!")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/attributes/{attribute_id}", response_model=APIResponse)
async def delete_attribute(attribute_id: int):
    """Xóa thuộc tính"""
    try:
        odoo_client.unlink('gold.attribute.line', [attribute_id])
        return APIResponse(success=True, message="Xóa thuộc tính thành công!")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# 3. API CRUD CHO MÃ MẪU SẢN PHẨM (product.template)
# =============================================================================

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
    """Lấy danh sách mã mẫu sản phẩm với filter gold attributes"""
    try:
        domain = []
        
        # Chỉ tìm kiếm khi có search_filter=true
        if search and search_filter:
            # Sử dụng OR đúng cách trong Odoo: '|' chỉ kết hợp 2 điều kiện, cần nested OR cho 3+
            domain.extend([
                '|', '|',
                ['name', 'ilike', search],
                ['default_code', 'ilike', search],
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
                    # Lấy danh sách product IDs có gold attributes phù hợp
                    filtered_product_ids = await _filter_products_by_gold_attributes(filters)
                    if filtered_product_ids is not None:
                        if len(filtered_product_ids) == 0:
                            # Không có product nào match
                            return APIResponse(success=True, data=[], total=0)
                        else:
                            domain.append(['id', 'in', filtered_product_ids])
            except Exception as e:
                print(f"Error parsing gold_attribute_filters: {e}")
        
        # Lấy dữ liệu với pagination
        offset = (page - 1) * limit
        products = odoo_client.search_read(
            'product.template', 
            domain, 
            ['name', 'default_code', 'categ_id', 'type', 'active', 'sale_ok', 'purchase_ok',
             'list_price', 'standard_price', 'weight', 'volume', 'description', 
             'description_sale', 'description_purchase', 'barcode', 'uom_id', 'uom_po_id',
             'create_date', 'write_date'],
            offset=offset,
            limit=limit,
            order='name'
        )
        
        # Lấy tên danh mục và đơn vị tính
        categ_ids = [p['categ_id'][0] for p in products if p.get('categ_id')]
        uom_ids = [p['uom_id'][0] for p in products if p.get('uom_id')]
        
        categ_dict = {}
        if categ_ids:
            categories = odoo_client.read('product.category', categ_ids, ['name'])
            categ_dict = {c['id']: c['name'] for c in categories}
        
        uom_dict = {}
        if uom_ids:
            uoms = odoo_client.read('uom.uom', uom_ids, ['name'])
            uom_dict = {u['id']: u['name'] for u in uoms}
        
        # Đếm số biến thể cho mỗi sản phẩm
        for product in products:
            variant_count = odoo_client.search_count('product.product', [['product_tmpl_id', '=', product['id']]])
            product['variant_count'] = variant_count
            
            # Thêm tên danh mục và đơn vị tính
            if product.get('categ_id'):
                product['categ_name'] = categ_dict.get(product['categ_id'][0], '')
            else:
                product['categ_name'] = ''
                
            # Lấy gold attributes từ Odoo server
            gold_attributes = gold_attribute_service.get_product_gold_attributes(product['id'])
            product['gold_attributes'] = gold_attributes
            product['is_jewelry_product'] = len(gold_attributes) > 0
            
            # Tạo summary
            if gold_attributes:
                summary_parts = []
                for attr in gold_attributes[:3]:  # Chỉ hiển thị 3 attributes đầu
                    if attr.get('display_value'):
                        summary_parts.append(f"{attr['attribute_short_name'] or attr['attribute_name']}: {attr['display_value']}")
                product['gold_attributes_summary'] = '; '.join(summary_parts)
                if len(gold_attributes) > 3:
                    product['gold_attributes_summary'] += f" (+{len(gold_attributes)-3} more)"
            else:
                product['gold_attributes_summary'] = ''
                
            if product.get('uom_id'):
                product['uom_name'] = uom_dict.get(product['uom_id'][0], '')
            else:
                product['uom_name'] = ''
        
        # Đếm tổng số bản ghi
        total = odoo_client.search_count('product.template', domain)
        
        return APIResponse(success=True, data=products, total=total)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/product-templates", response_model=APIResponse)
async def create_product_template(product: ProductTemplateCreate):
    """Tạo mã mẫu sản phẩm mới"""
    try:
        product_data = {k: v for k, v in product.dict().items() if v is not None}
        product_id = odoo_client.create('product.template', product_data)
        return APIResponse(success=True, data={"id": product_id}, message="Tạo mã mẫu sản phẩm thành công!")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
# 4. API HỖ TRỢ - LẤY DANH SÁCH TÙY CHỌN
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
# 5. API TÍCH HỢP GOLD ATTRIBUTE LINE
# =============================================================================

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

@app.put("/api/product-templates/{product_id}/gold-attributes/{attribute_id}", response_model=APIResponse)
async def update_product_template_gold_attribute(
    product_id: int, 
    attribute_id: int, 
    attribute_value: GoldAttributeValueUpdate
):
    """Cập nhật giá trị thuộc tính vàng của mã mẫu"""
    try:
        # Tạm thời chưa implement
        return APIResponse(success=True, message="Tính năng sẽ được implement sau")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/product-templates/{product_id}/gold-attributes/{attribute_id}", response_model=APIResponse)
async def delete_product_template_gold_attribute(product_id: int, attribute_id: int):
    """Xóa giá trị thuộc tính vàng của mã mẫu"""
    try:
        # Tạm thời chưa implement
        return APIResponse(success=True, message="Tính năng sẽ được implement sau")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# 6. API THỐNG KÊ VÀ BÁO CÁO
# =============================================================================



@app.get("/api/gold-attributes/usage-statistics", response_model=APIResponse)
async def get_attribute_usage_statistics():
    """Thống kê sử dụng thuộc tính vàng"""
    try:
        # Lấy tất cả gold attributes
        attributes = odoo_client.search_read(
            'gold.attribute.line', 
            [], 
            ['name', 'display_name', 'category']
        )
        
        # Tạm thời return usage = 0 vì chưa có model lưu values
        usage_stats = []
        for attr in attributes:
            usage_stats.append({
                'attribute_id': attr['id'],
                'attribute_name': attr['name'],
                'usage_count': 0,
                'templates_using': []
            })
        
        return APIResponse(success=True, data=usage_stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# 7. API BULK OPERATIONS
# =============================================================================

@app.post("/api/product-templates/bulk-action", response_model=APIResponse)
async def product_template_bulk_action(bulk_action: ProductTemplateBulkAction):
    """Thực hiện hành động hàng loạt trên mã mẫu"""
    try:
        template_ids = bulk_action.template_ids
        action = bulk_action.action
        data = bulk_action.data or {}
        
        if action == 'activate':
            odoo_client.write('product.template', template_ids, {'active': True})
            message = f"Đã kích hoạt {len(template_ids)} mã mẫu"
            
        elif action == 'deactivate':
            odoo_client.write('product.template', template_ids, {'active': False})
            message = f"Đã vô hiệu hóa {len(template_ids)} mã mẫu"
            
        elif action == 'delete':
            # Kiểm tra variants trước khi xóa
            for template_id in template_ids:
                variant_count = odoo_client.search_count('product.product', [['product_tmpl_id', '=', template_id]])
                if variant_count > 0:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Không thể xóa mã mẫu ID {template_id} vì còn {variant_count} biến thể"
                    )
            odoo_client.unlink('product.template', template_ids)
            message = f"Đã xóa {len(template_ids)} mã mẫu"
            
        elif action == 'update_category':
            if 'categ_id' not in data:
                raise HTTPException(status_code=400, detail="Thiếu categ_id trong data")
            odoo_client.write('product.template', template_ids, {'categ_id': data['categ_id']})
            message = f"Đã cập nhật danh mục cho {len(template_ids)} mã mẫu"
            
        else:
            raise HTTPException(status_code=400, detail=f"Hành động không hợp lệ: {action}")
        
        return APIResponse(success=True, message=message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    global sse_connections
    try:
        calculator = kafka_consumer.get_calculator()
        stats = calculator.get_stats()
        
        return {
            "status": "healthy",
            "kafka_connected": kafka_consumer.running,
            "sse_connections": len(sse_connections),
            "calculator_stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "kafka_connected": kafka_consumer.running,
            "timestamp": datetime.utcnow().isoformat()
        }

# ================================
# CLIENT-SIDE GOLD ATTRIBUTES ENDPOINTS
# ================================

@app.get("/api/product-templates/{product_id}/gold-attributes", response_model=APIResponse)
async def get_product_gold_attributes_client(product_id: int):
    """Lấy gold attributes từ Odoo server"""
    try:
        gold_attributes = gold_attribute_service.get_product_gold_attributes(product_id)
        return APIResponse(success=True, data=gold_attributes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/product-templates/{product_id}/gold-attributes", response_model=APIResponse)
async def set_product_gold_attributes_client(product_id: int, request: Request):
    """Set gold attributes cho product template"""
    try:
        # Lấy data từ request body
        body = await request.json()
        
        # Kiểm tra product có tồn tại không
        existing_count = odoo_client.search_count('product.template', [['id', '=', product_id]])
        if existing_count == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy mã mẫu sản phẩm")
        
        # Convert string keys to int
        converted_attributes = {}
        for key, value in body.items():
            try:
                attribute_id = int(key)
                converted_attributes[attribute_id] = value
            except ValueError:
                print(f"Warning: Invalid attribute ID: {key}")
                continue
        
        print(f"Setting gold attributes for product {product_id}: {converted_attributes}")
        result = gold_attribute_service.bulk_set_product_gold_attributes(product_id, converted_attributes)
        print(f"Result: {result}")
        
        if result:
            message = f"Đã set {len(converted_attributes)} gold attributes thành công"
            return APIResponse(success=True, message=message)
        else:
            return APIResponse(success=False, message="Có lỗi khi set gold attributes")
        
    except Exception as e:
        print(f"Error in set_product_gold_attributes_client: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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

@app.get("/api/gold-attributes-statistics", response_model=APIResponse)
async def get_gold_attributes_statistics():
    """Lấy thống kê về gold attributes usage"""
    try:
        stats = gold_attribute_service.get_gold_attribute_statistics()
        return APIResponse(success=True, data=stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "kafka_connected": kafka_consumer.running,
            "timestamp": datetime.utcnow().isoformat()
        }

if __name__ == "__main__":
    import uvicorn
    from config import FASTAPI_CONFIG
    
    uvicorn.run(
        "app_fastapi:app",
        host=FASTAPI_CONFIG['host'],
        port=FASTAPI_CONFIG['port'],
        reload=FASTAPI_CONFIG['reload']
    )
