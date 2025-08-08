# Odoo Product CRUD Client với Real-time Pricing

## 🎯 Tổng quan

Ứng dụng FastAPI client để tương tác với Odoo server thông qua XML-RPC API, bao gồm:
- **CRUD operations** cho Products, Templates, Categories, Attributes, Values, Serials
- **Real-time Pricing System** với Server-Sent Events (SSE)
- **Auto-code generation** cho sản phẩm dựa trên template và attributes
- **Vietnamese support** với Bootstrap 5 UI

## 🏗️ Kiến trúc hệ thống

### Core Application
```
[Odoo Server] ↔ [XML-RPC Client] ↔ [FastAPI] ↔ [Bootstrap UI]
```

### Real-time Pricing
```
[Rates Source] ─┐
                ├→ [Pricing Calculator] → [FastAPI Gateway] → [Browser SSE]
[Weights Source] ─┘
```

## 🚀 Cài đặt và chạy

### 1. Dependencies
```bash
pip install -r requirements.txt
```

### 2. Cấu hình
Tạo file `.env`:
```bash
# Odoo Connection
ODOO_URL=https://your-odoo-server.com
ODOO_DB=your_database
ODOO_USERNAME=your_username
ODOO_PASSWORD=your_password

# FastAPI
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=5000
FASTAPI_RELOAD=True
```

### 3. Chạy ứng dụng
```bash
python run_fastapi.py
```

**Truy cập:**
- **Web Interface**: http://localhost:5000
- **API Documentation**: http://localhost:5000/docs  
- **Real-time Pricing**: http://localhost:5000/pricing

## 📋 Tính năng chính

### 1. Product Management
- ✅ **Categories**: Quản lý danh mục sản phẩm
- ✅ **Attributes**: Thuộc tính sản phẩm (Size, Color, Material...)
- ✅ **Values**: Giá trị thuộc tính (S/M/L, Red/Blue...)
- ✅ **Templates**: Template sản phẩm với attributes
- ✅ **Products**: Sản phẩm cụ thể với auto-code generation
- ✅ **Serials**: Quản lý serial numbers (stock.lot)

### 2. Real-time Pricing
- ✅ **Live Updates**: Pricing thay đổi real-time qua SSE
- ✅ **Auto-reconnect**: Tự động kết nối lại khi mất mạng  
- ✅ **Local Caching**: Cache pricing data với TTL
- ✅ **Offline Strategies**: Freeze/Surcharge/Deny khi data expired
- ✅ **Material Support**: Tỷ giá vàng/bạc riêng biệt

### 3. Advanced Features
- ✅ **Auto-code Generation**: Tự động tạo mã SP từ template + attributes
- ✅ **Vietnamese Support**: Chuyển đổi tiếng Việt không dấu
- ✅ **Responsive UI**: Bootstrap 5 responsive design
- ✅ **API Documentation**: Automatic OpenAPI docs
- ✅ **Type Validation**: Pydantic models validation

## 📡 API Endpoints

### Core CRUD APIs
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/attributes` | GET, POST, PUT, DELETE | Quản lý attributes |
| `/api/values` | GET, POST, PUT, DELETE | Quản lý attribute values |
| `/api/categories` | GET, POST, PUT, DELETE | Quản lý categories |
| `/api/templates` | GET, POST, PUT, DELETE | Quản lý templates |
| `/api/products` | GET, POST, PUT, DELETE | Quản lý products |
| `/api/serials` | GET, POST, PUT, DELETE | Quản lý serials |

### Specialized APIs
| Endpoint | Description |
|----------|-------------|
| `/api/templates/{id}/attributes` | Lấy attributes của template |
| `/api/templates/suggest` | Gợi ý templates tương đồng |
| `/api/products/all-attributes` | Lấy tất cả attributes cho filter |

### Real-time Pricing APIs
| Endpoint | Description |
|----------|-------------|
| `/events/pricing` | SSE stream cho pricing updates |
| `/api/pricing/{sku}` | Lấy giá sản phẩm với offline strategy |
| `/api/pricing` | Lấy tất cả giá hiện tại |
| `/test/publish` | Trigger test pricing data |

## 🗂️ Cấu trúc dự án

```
d:\BTMH\
├── app_fastapi.py              # FastAPI application chính
├── odoo_client.py              # XML-RPC client cho Odoo
├── config.py                   # Cấu hình kết nối
├── models.py                   # Pydantic models cho validation
├── run_fastapi.py              # Script khởi chạy
├── requirements.txt            # Dependencies
├── .env                        # Environment variables
├── templates/                  # HTML templates
│   ├── index.html             # Trang chủ
│   ├── attributes.html        # Quản lý attributes
│   ├── values.html            # Quản lý values
│   ├── categories.html        # Quản lý categories  
│   ├── templates.html         # Quản lý templates
│   ├── products.html          # Quản lý products
│   ├── serials.html           # Quản lý serials
│   └── pricing.html           # Real-time pricing demo
└── static/                    # Static files
    ├── css/style.css          # Custom styles
    └── js/                    # JavaScript files
        ├── attributes.js      # Attributes management
        ├── values.js          # Values management
        ├── categories.js      # Categories management
        ├── templates.js       # Templates management  
        ├── products.js        # Products management
        ├── serials.js         # Serials management
        └── pricing_client.js  # Real-time pricing client
```

## 📊 Real-time Pricing System

### Data Models

#### Rate Update (Tỷ giá)
```json
{
  "material": "gold|silver",
  "rate": 75500000,
  "rate_version": 1704705600000,
  "timestamp": "2025-01-08T10:00:00Z"
}
```

#### Product Weights (Trọng số)
```json
{
  "sku": "PRODUCT_001",
  "material": "gold", 
  "weight_gram": 5.5,
  "stone_weight": 0.2,
  "labor_cost": 500000,
  "markup_percent": 15,
  "weights_version": 1704705600000,
  "timestamp": "2025-01-08T10:00:00Z"
}
```

#### Pricing Snapshot (Kết quả)
```json
{
  "sku": "PRODUCT_001",
  "base_price": 415250000,
  "final_price": 477537500,
  "rate_used": 75500000,
  "weight_gram": 5.5,
  "labor_cost": 500000,
  "markup_percent": 15,
  "material": "gold",
  "snapshot_version": 1704705660000,
  "ttl_sec": 300,
  "as_of": "2025-01-08T10:01:00Z"
}
```

### Offline Strategies

Khi pricing data hết hạn:

1. **Freeze** (default) - Dùng giá cũ, đánh dấu expired
2. **Surcharge** - Cộng thêm 5% rủi ro  
3. **Deny** - Từ chối trả giá

### Browser Client Features

- **Auto-reconnecting SSE** với exponential backoff
- **Local caching** với TTL validation
- **Real-time updates** với visual feedback
- **Offline handling** với configurable strategies
- **Search & filter** by SKU và material
- **Vietnamese currency formatting**

## 🛠️ Development

### Thêm Model mới
1. Thêm Pydantic model trong `models.py`
2. Thêm API endpoints trong `app_fastapi.py`
3. Tạo HTML template trong `templates/`
4. Tạo JavaScript logic trong `static/js/`

### Real-time Pricing Integration

#### Server Side (Python)
```python
from pricing_models import Rate, ProductWeights, PricingSnapshot
from pricing_calculator import PricingCalculator

calculator = PricingCalculator()

# Update rate
rate = Rate(material="gold", rate=75500000, rate_version=123)
calculator.update_rate(rate)

# Update weights  
weights = ProductWeights(sku="SKU001", material="gold", weight_gram=5.5)
calculator.update_weights(weights)

# Get pricing
snapshot = calculator.get_pricing("SKU001")
```

#### Client Side (JavaScript)
```javascript
const pricingClient = new PricingClient();

// Listen for updates
pricingClient.onPricingUpdate = (type, pricing) => {
    console.log('Price updated:', pricing);
    updateUI(pricing);
};

// Get pricing with strategy
const result = await pricingClient.getPricing('SKU001', 'freeze');
if (result.success) {
    displayPrice(result.data);
}
```

## 🔧 Configuration

### Environment Variables
```bash
# Odoo Connection
ODOO_URL=https://admin.hinosoft.com
ODOO_DB=goldsun
ODOO_USERNAME=admin
ODOO_PASSWORD=admin

# FastAPI
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=5000
FASTAPI_RELOAD=True

# Real-time Pricing (Optional)
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_GROUP_ID=pricing-gateway
PRICING_TTL_SEC=300
```

### Odoo Models được sử dụng
- `product.attribute` - Thuộc tính sản phẩm
- `product.attribute.value` - Giá trị thuộc tính
- `product.category` - Danh mục sản phẩm
- `product.template` - Template sản phẩm  
- `product.template.attribute.line` - Liên kết template-attribute
- `product.product` - Sản phẩm cụ thể
- `stock.lot` - Serial numbers

## 🧪 Testing

### Manual Testing
1. Truy cập http://localhost:5000
2. Test CRUD operations trên từng module
3. Test real-time pricing: http://localhost:5000/pricing
4. Click "Test Update" để trigger pricing updates

### API Testing
```bash
# Health check
curl http://localhost:5000/health

# Get all products
curl http://localhost:5000/api/products

# Test real-time pricing
curl -N http://localhost:5000/events/pricing
```

## 🚨 Production Deployment

### Docker Setup
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["python", "run_fastapi.py"]
```

### Environment
- Python 3.11+
- Odoo 18.0+
- FastAPI 0.104+
- Bootstrap 5.1+

### Scaling Considerations
- Use Redis cho pricing cache trong production
- Load balancer cho multiple FastAPI instances
- Kafka cluster cho high-throughput pricing updates
- CDN cho static files

## 📈 Monitoring

### Health Endpoints
- `/health` - Application health
- `/docs` - API documentation
- `/redoc` - Alternative API docs

### Metrics
- API response times
- Odoo connection status  
- SSE connection count
- Pricing cache hit rate
- Error rates per endpoint

## 🤝 Contributing

1. Fork repository
2. Create feature branch
3. Implement changes với tests
4. Update documentation
5. Submit pull request

## 📄 License

MIT License - xem file LICENSE để biết thêm chi tiết.

---

## 🎉 Features Summary

✅ **Complete CRUD** cho tất cả Odoo product entities  
✅ **Real-time Pricing** với SSE và caching  
✅ **Auto-code Generation** cho products  
✅ **Vietnamese Support** trong UI và data processing  
✅ **Bootstrap 5 UI** responsive design  
✅ **FastAPI + Pydantic** type-safe APIs  
✅ **Auto Documentation** với OpenAPI  
✅ **Production Ready** với proper error handling  

**Tổng cộng: 8 modules, 25+ API endpoints, Real-time updates, Production-ready! 🚀**
