"""
FastAPI Application - Migrated from Flask
Odoo Product CRUD Client với Real-time Pricing
"""
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
import unicodedata
import asyncio
import json
from datetime import datetime
from typing import List, Optional, Dict, Set
import uvicorn

from odoo_client import odoo_client
from config import FASTAPI_CONFIG
from models import *
from pricing_models import PricingSnapshot, PricingRequest, PricingResponse, OfflineStrategy
from kafka_pricing_consumer import KafkaPricingConsumer
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

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Trang chủ"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/attributes", response_class=HTMLResponse)
async def attributes_page(request: Request):
    """Trang quản lý attributes"""
    return templates.TemplateResponse("attributes.html", {"request": request})

@app.get("/values", response_class=HTMLResponse)
async def values_page(request: Request):
    """Trang quản lý attribute values"""
    return templates.TemplateResponse("values.html", {"request": request})

@app.get("/categories", response_class=HTMLResponse)
async def categories_page(request: Request):
    """Trang quản lý categories"""
    return templates.TemplateResponse("categories.html", {"request": request})

@app.get("/templates", response_class=HTMLResponse)
async def templates_page(request: Request):
    """Trang quản lý product templates"""
    return templates.TemplateResponse("templates.html", {"request": request})

@app.get("/products", response_class=HTMLResponse)
async def products_page(request: Request):
    """Trang quản lý products"""
    return templates.TemplateResponse("products.html", {"request": request})

@app.get("/serials", response_class=HTMLResponse)
async def serials_page(request: Request):
    """Trang quản lý serial numbers"""
    return templates.TemplateResponse("serials.html", {"request": request})

@app.get("/pricing", response_class=HTMLResponse)
async def pricing_page(request: Request):
    """Trang demo real-time pricing"""
    return templates.TemplateResponse("pricing.html", {"request": request})

@app.get("/pricings", response_class=HTMLResponse)
async def pricing_page_redirect(request: Request):
    """Redirect /pricings to /pricing"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/pricing", status_code=301)

@app.get("/rates", response_class=HTMLResponse)
async def rates_page(request: Request):
    """Trang quản lý tỷ giá real-time"""
    return templates.TemplateResponse("rates.html", {"request": request})

# ================================
# API ROUTES - ATTRIBUTES
# ================================

@app.get("/api/attributes", response_model=APIResponse)
async def get_attributes():
    """Lấy danh sách product attributes"""
    try:
        attributes = odoo_client.search_read(
            'product.attribute',
            [],
            ['id', 'name', 'display_type', 'sequence']
        )
        attributes.sort(key=lambda x: x['sequence'])
        return APIResponse(success=True, data=attributes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/attributes", response_model=APIResponse)
async def create_attribute(attribute: AttributeCreate):
    """Tạo product attribute mới"""
    try:
        attribute_id = odoo_client.create('product.attribute', attribute.dict())
        return APIResponse(success=True, data={"id": attribute_id})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/attributes/{attribute_id}", response_model=APIResponse)
async def update_attribute(attribute_id: int, attribute: AttributeUpdate):
    """Cập nhật product attribute"""
    try:
        update_data = {k: v for k, v in attribute.dict().items() if v is not None}
        success = odoo_client.write('product.attribute', attribute_id, update_data)
        return APIResponse(success=success)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/attributes/{attribute_id}", response_model=APIResponse)
async def delete_attribute(attribute_id: int):
    """Xóa product attribute"""
    try:
        success = odoo_client.unlink('product.attribute', attribute_id)
        return APIResponse(success=success)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ================================
# API ROUTES - ATTRIBUTE VALUES
# ================================

@app.get("/api/values", response_model=APIResponse)
async def get_values():
    """Lấy danh sách attribute values"""
    try:
        values = odoo_client.search_read(
            'product.attribute.value',
            [],
            ['id', 'name', 'attribute_id', 'sequence']
        )
        values.sort(key=lambda x: (x['attribute_id'][1], x['sequence']))
        return APIResponse(success=True, data=values)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/values", response_model=APIResponse)
async def create_value(value: AttributeValueCreate):
    """Tạo attribute value mới"""
    try:
        value_id = odoo_client.create('product.attribute.value', value.dict())
        return APIResponse(success=True, data={"id": value_id})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/values/{value_id}", response_model=APIResponse)
async def update_value(value_id: int, value: AttributeValueUpdate):
    """Cập nhật attribute value"""
    try:
        update_data = {k: v for k, v in value.dict().items() if v is not None}
        success = odoo_client.write('product.attribute.value', value_id, update_data)
        return APIResponse(success=success)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/values/{value_id}", response_model=APIResponse)
async def delete_value(value_id: int):
    """Xóa attribute value"""
    try:
        success = odoo_client.unlink('product.attribute.value', value_id)
        return APIResponse(success=success)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ================================
# API ROUTES - CATEGORIES
# ================================

@app.get("/api/categories", response_model=APIResponse)
async def get_categories():
    """Lấy danh sách product categories"""
    try:
        categories = odoo_client.search_read(
            'product.category',
            [],
            ['id', 'name', 'parent_id', 'sequence']
        )
        categories.sort(key=lambda x: (x.get('parent_id', [False, ''])[1], x['sequence']))
        return APIResponse(success=True, data=categories)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/categories", response_model=APIResponse)  
async def create_category(category: CategoryCreate):
    """Tạo product category mới"""
    try:
        category_id = odoo_client.create('product.category', category.dict())
        return APIResponse(success=True, data={"id": category_id})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/categories/{category_id}", response_model=APIResponse)
async def update_category(category_id: int, category: CategoryUpdate):
    """Cập nhật product category"""
    try:
        update_data = {k: v for k, v in category.dict().items() if v is not None}
        success = odoo_client.write('product.category', category_id, update_data)
        return APIResponse(success=success)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/categories/{category_id}", response_model=APIResponse)
async def delete_category(category_id: int):
    """Xóa product category"""
    try:
        success = odoo_client.unlink('product.category', category_id)
        return APIResponse(success=success)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ================================
# API ROUTES - TEMPLATES
# ================================

@app.get("/api/templates", response_model=APIResponse)
async def get_templates():
    """Lấy danh sách product templates"""
    try:
        templates = odoo_client.search_read(
            'product.template',
            [],
            ['id', 'name', 'categ_id', 'list_price', 'standard_price', 'default_code', 'barcode']
        )
        templates.sort(key=lambda x: x['id'], reverse=True)
        return APIResponse(success=True, data=templates)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/templates", response_model=APIResponse)
async def create_template(template: TemplateCreate):
    """Tạo product template mới với attributes"""
    try:
        # Tạo template data cơ bản
        template_data = {
            'name': template.name,
            'categ_id': template.categ_id,
            'list_price': template.list_price or 0,
            'standard_price': template.standard_price or 0,
        }
        
        if template.default_code:
            template_data['default_code'] = template.default_code
        if template.barcode:
            template_data['barcode'] = template.barcode
            
        # Tạo template
        template_id = odoo_client.create('product.template', template_data)
        
        # Xử lý attributes nếu có
        if template.attribute_line_ids:
            for attr_line in template.attribute_line_ids:
                attr_id = attr_line['attribute_id']
                value_ids = attr_line['value_ids']
                
                # Tạo attribute values nếu chưa có (text input)
                if 'text_values' in attr_line:
                    for text_value in attr_line['text_values']:
                        if text_value.strip():
                            value_id = odoo_client.create('product.attribute.value', {
                                'name': text_value.strip(),
                                'attribute_id': attr_id
                            })
                            value_ids.append(value_id)
                
                # Tạo attribute line
                if value_ids:
                    odoo_client.create('product.template.attribute.line', {
                        'product_tmpl_id': template_id,
                        'attribute_id': attr_id,
                        'value_ids': [(6, 0, value_ids)]
                    })
        
        return APIResponse(success=True, data={"id": template_id})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/templates/{template_id}/attributes", response_model=APIResponse)
async def get_template_attributes(template_id: int):
    """Lấy attributes của template"""
    try:
        attribute_lines = odoo_client.search_read(
            'product.template.attribute.line',
            [['product_tmpl_id', '=', template_id]],
            ['id', 'attribute_id', 'value_ids']
        )
        
        for line in attribute_lines:
            if line['value_ids']:
                values = odoo_client.search_read(
                    'product.attribute.value',
                    [['id', 'in', line['value_ids']]],
                    ['id', 'name', 'sequence']
                )
                line['values'] = sorted(values, key=lambda x: x['sequence'])
            else:
                line['values'] = []
                
        return APIResponse(success=True, data=attribute_lines)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/templates/{template_id}", response_model=APIResponse)
async def update_template(template_id: int, template: TemplateUpdate):
    """Cập nhật product template"""
    try:
        update_data = {k: v for k, v in template.dict().items() if v is not None}
        success = odoo_client.write('product.template', template_id, update_data)
        return APIResponse(success=success)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/templates/{template_id}", response_model=APIResponse)
async def delete_template(template_id: int):
    """Xóa product template"""
    try:
        success = odoo_client.unlink('product.template', template_id)
        return APIResponse(success=success)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/templates/suggest", response_model=APIResponse)
async def suggest_templates(request: Request):
    """Gợi ý templates tương đồng dựa trên category và tên"""
    try:
        data = await request.json()
        domain = []
        
        if data.get('categ_id'):
            domain.append(['categ_id', '=', data['categ_id']])
        if data.get('name'):
            domain.append(['name', 'ilike', data['name']])
            
        templates = odoo_client.search_read(
            'product.template',
            domain,
            ['id', 'name', 'categ_id', 'list_price', 'standard_price', 'default_code', 'barcode']
        )
        return APIResponse(success=True, data=templates)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ================================
# API ROUTES - PRODUCTS
# ================================

@app.get("/api/products", response_model=APIResponse)
async def get_products():
    """Lấy danh sách products"""
    try:
        products = odoo_client.search_read(
            'product.product',
            [],
            ['id', 'name', 'product_tmpl_id', 'default_code', 'barcode', 'active']
        )
        products.sort(key=lambda x: x['id'], reverse=True)
        return APIResponse(success=True, data=products)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/products", response_model=APIResponse)
async def create_product(product: ProductCreate):
    """Tạo product mới với auto-generation mã sản phẩm"""
    try:
        template = odoo_client.search_read(
            'product.template',
            [['id', '=', product.product_tmpl_id]],
            ['default_code', 'name']
        )
        
        if not template:
            raise HTTPException(status_code=404, detail="Template không tồn tại")
        
        template_info = template[0]
        
        # Auto-generate code nếu chưa có
        if not product.default_code:
            code = template_info.get('default_code', template_info.get('name', 'PRODUCT'))
            
            if product.attribute_value_ids:
                for value_id in product.attribute_value_ids:
                    value = odoo_client.search_read(
                        'product.attribute.value',
                        [['id', '=', value_id]],
                        ['name']
                    )
                    if value:
                        value_code = generate_attribute_code(value[0]['name'])
                        code += '-' + value_code
            
            product.default_code = code
        
        product_data = {
            'name': product.name,
            'product_tmpl_id': product.product_tmpl_id,
            'default_code': product.default_code,
        }
        
        if product.barcode:
            product_data['barcode'] = product.barcode
        
        product_id = odoo_client.create('product.product', product_data)
        
        # Gán attribute values nếu có
        if product.attribute_value_ids and product_id:
            for value_id in product.attribute_value_ids:
                odoo_client.create('product.template.attribute.value', {
                    'product_tmpl_id': product.product_tmpl_id,
                    'attribute_value_id': value_id,
                    'ptav_product_variant_ids': [(6, 0, [product_id])]
                })
        
        return APIResponse(success=True, data={"id": product_id, "code": product.default_code})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/products/{product_id}", response_model=APIResponse)
async def update_product(product_id: int, product: ProductUpdate):
    """Cập nhật product"""
    try:
        update_data = {k: v for k, v in product.dict().items() if v is not None}
        success = odoo_client.write('product.product', product_id, update_data)
        return APIResponse(success=success)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/products/{product_id}", response_model=APIResponse)
async def delete_product(product_id: int):
    """Xóa product"""
    try:
        success = odoo_client.unlink('product.product', product_id)
        return APIResponse(success=success)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/products/all-attributes", response_model=APIResponse)
async def get_all_product_attributes():
    """Lấy tất cả attributes có trong products để làm filter"""
    try:
        attributes = odoo_client.search_read(
            'product.attribute',
            [],
            ['id', 'name', 'display_type']
        )
        
        for attr in attributes:
            values = odoo_client.search_read(
                'product.attribute.value',
                [['attribute_id', '=', attr['id']]],
                ['id', 'name', 'sequence']
            )
            attr['values'] = sorted(values, key=lambda x: x['sequence'])
        
        return APIResponse(success=True, data=attributes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ================================
# API ROUTES - SERIALS
# ================================

@app.get("/api/serials", response_model=APIResponse)
async def get_serials():
    """Lấy danh sách serial numbers"""
    try:
        serials = odoo_client.search_read(
            'stock.lot',
            [],
            ['id', 'name', 'product_id', 'company_id']
        )
        serials.sort(key=lambda x: x['id'], reverse=True)
        return APIResponse(success=True, data=serials)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/serials", response_model=APIResponse)
async def create_serial(serial: SerialCreate):
    """Tạo serial number mới"""
    try:
        serial_id = odoo_client.create('stock.lot', serial.dict())
        return APIResponse(success=True, data={"id": serial_id})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/serials/{serial_id}", response_model=APIResponse)
async def update_serial(serial_id: int, serial: SerialUpdate):
    """Cập nhật serial number"""
    try:
        update_data = {k: v for k, v in serial.dict().items() if v is not None}
        success = odoo_client.write('stock.lot', serial_id, update_data)
        return APIResponse(success=success)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/serials/{serial_id}", response_model=APIResponse)
async def delete_serial(serial_id: int):
    """Xóa serial number"""
    try:
        success = odoo_client.unlink('stock.lot', serial_id)
        return APIResponse(success=success)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ================================
# UTILITY FUNCTIONS
# ================================

def generate_attribute_code(name):
    """Tạo mã từ tên attribute"""
    name = name.strip().upper()
    
    vietnamese_map = {
        'Á': 'A', 'À': 'A', 'Ã': 'A', 'Ạ': 'A', 'Ả': 'A',
        'Ă': 'A', 'Ắ': 'A', 'Ằ': 'A', 'Ẵ': 'A', 'Ặ': 'A', 'Ẳ': 'A',
        'Â': 'A', 'Ấ': 'A', 'Ầ': 'A', 'Ẫ': 'A', 'Ậ': 'A', 'Ẩ': 'A',
        'É': 'E', 'È': 'E', 'Ẽ': 'E', 'Ẹ': 'E', 'Ẻ': 'E',
        'Ê': 'E', 'Ế': 'E', 'Ề': 'E', 'Ễ': 'E', 'Ệ': 'E', 'Ể': 'E',
        'Í': 'I', 'Ì': 'I', 'Ĩ': 'I', 'Ị': 'I', 'Ỉ': 'I',
        'Ó': 'O', 'Ò': 'O', 'Õ': 'O', 'Ọ': 'O', 'Ỏ': 'O',
        'Ô': 'O', 'Ố': 'O', 'Ồ': 'O', 'Ỗ': 'O', 'Ộ': 'O', 'Ổ': 'O',
        'Ơ': 'O', 'Ớ': 'O', 'Ờ': 'O', 'Ỡ': 'O', 'Ợ': 'O', 'Ở': 'O',
        'Ú': 'U', 'Ù': 'U', 'Ũ': 'U', 'Ụ': 'U', 'Ủ': 'U',
        'Ư': 'U', 'Ứ': 'U', 'Ừ': 'U', 'Ữ': 'U', 'Ự': 'U', 'Ử': 'U',
        'Ý': 'Y', 'Ỳ': 'Y', 'Ỹ': 'Y', 'Ỵ': 'Y', 'Ỷ': 'Y',
        'Đ': 'D'
    }
    
    for vn, en in vietnamese_map.items():
        name = name.replace(vn, en)
    
    import re
    name = re.sub(r'[^A-Z0-9]', '', name)
    
    return name[:10]

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
            rate_version=int(datetime.utcnow().timestamp() * 1000)
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

if __name__ == "__main__":
    import uvicorn
    from config import FASTAPI_CONFIG
    
    uvicorn.run(
        "app_fastapi:app",
        host=FASTAPI_CONFIG['host'],
        port=FASTAPI_CONFIG['port'],
        reload=FASTAPI_CONFIG['reload']
    )
