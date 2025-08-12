# BTMH - Product Management System

🚀 **Modern FastAPI-based Product Management System** tích hợp với Odoo server, được **hoàn toàn refactored** với architecture hiện đại.

## ✨ Tính năng chính

### ✅ Đã hoàn thành và hoạt động hoàn hảo
- **🏷️ Product Template CRUD** - Quản lý mã mẫu sản phẩm hoàn chỉnh
- **💎 Gold Attributes Integration** - Tích hợp thuộc tính vàng với Odoo persistence
- **💰 Real-time Pricing System** - Hệ thống định giá thời gian thực với Kafka
- **🔍 Advanced Search & Filter** - Tìm kiếm và lọc theo gold attributes
- **📊 Data Persistence** - Lưu trữ trong Odoo database (không cần client-side storage)
- **🏗️ Modern Architecture** - Clean src/ structure với separation of concerns

## 🏗️ Project Structure (Refactored)

```
d:\BTMH\
├── 🚀 app.py                      # Main FastAPI application  
├── 📦 src/                        # Organized source code
│   ├── core/                      # Core configurations & clients
│   ├── models/                    # Pydantic data models
│   └── services/                  # Business logic services
├── 🎨 static/                     # Frontend assets
├── 📄 templates/                  # HTML templates
├── 🧪 tests/                      # Unit tests
├── 📚 docs/                       # Complete documentation
├── 🐳 docker-compose.yml          # Kafka infrastructure
└── 📋 requirements.txt            # Clean dependencies
```

## 🎯 Key Achievements

### Gold Attributes Integration ✅
```bash
✅ Hoàn toàn tích hợp với Odoo module gold_attribute_line
✅ CRUD operations với persistent data trong Odoo
✅ Search chỉ kích hoạt khi nhấn button "Filter"  
✅ Filter system hoàn toàn thay thế bằng gold attributes
✅ Bulk update multiple attributes cùng lúc
✅ Service layer architecture với proper error handling
```

### Code Quality & Architecture ✅
```bash
✅ Clean src/ structure với separation of concerns
✅ Removed 14 obsolete files và duplicate code
✅ Proper imports với relative paths
✅ Service instances với centralized business logic
✅ Complete documentation và API examples
✅ Modern FastAPI patterns với type hints
```

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Clone repository
git clone <repository_url>
cd BTMH

# Setup environment variables
cp .env.example .env
# Edit .env with your Odoo credentials

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Application
```bash
# Basic setup (CRUD only)
python app_fastapi.py

# Full setup with Kafka (Real-time pricing)
docker-compose up -d  # Start Kafka
python app_fastapi.py # Start main app
```

### 3. Access Application
- **Main Interface**: http://localhost:5000
- **API Docs**: http://localhost:5000/docs
- **Health Check**: http://localhost:5000/health

## 📡 API Examples

### Gold Attributes
```bash
# Get gold attributes for product
curl "http://localhost:5000/api/product-templates/1/gold-attributes"

# Set multiple gold attributes
curl -X POST "http://localhost:5000/api/product-templates/1/gold-attributes" \
  -H "Content-Type: application/json" \
  -d '{"1": "Round", "2": "18K"}'

# Get filter options
curl "http://localhost:5000/api/gold-attributes/filter-options"
```

### Product Search with Filters
```bash
# Search with gold attribute filters
curl "http://localhost:5000/api/product-templates?search_filter=true&search=Test&gold_attribute_filters={\"1\":\"Round\"}"
```

## 🚀 Tính năng chính

### 1. **CRUD Operations** 
- Quản lý danh mục sản phẩm (product.category)
- Quản lý template sản phẩm (product.template) 
- Quản lý sản phẩm cụ thể (product.product)
- Giao diện web responsive với Bootstrap 5

### 2. **Real-time Pricing System**
- Tính toán giá theo tỷ giá vàng/bạc thời gian thực
- Kafka streaming cho cập nhật liên tục
- Server-Sent Events (SSE) cho real-time UI updates
- Cache pricing với TTL (Time-To-Live)
- Pricing calculator với material weights

### 3. **Monitoring & Health Check**
- Health check endpoint với system stats
- Kafka connection monitoring
- SSE connections tracking
- Calculator performance metrics

## 📁 Cấu trúc dự án

```
d:\BTMH\
├── app_fastapi.py              # FastAPI main application
├── odoo_client.py              # Odoo XML-RPC client
├── config.py                   # Configuration settings
├── models.py                   # Pydantic models cho CRUD
├── pricing_models.py           # Pydantic models cho pricing
├── pricing_calculator.py       # Pricing calculation logic
├── kafka_pricing_consumer.py   # Kafka consumer service
├── kafka_producer.py           # Kafka producer for test data
├── test_pricing.py             # Test script cho pricing system
├── docker-compose.yml          # Kafka infrastructure
├── templates/                  # Jinja2 HTML templates
│   ├── base.html
│   ├── categories.html
│   ├── products.html
│   ├── templates.html
│   └── pricing.html
└── static/                     # CSS và JavaScript files
    ├── style.css
    └── app.js
```

## 🛠️ Cài đặt và Chạy

### 1. **Cài đặt Dependencies**

```bash
pip install fastapi uvicorn jinja2 python-multipart
pip install kafka-python requests pydantic
pip install sse-starlette
```

### 2. **Cấu hình Odoo Connection**

Cập nhật file `config.py`:
```python
ODOO_CONFIG = {
    'url': 'http://your-odoo-server:8069',
    'db': 'your-database',
    'username': 'your-username', 
    'password': 'your-password'
}
```

### 3. **Khởi động Kafka Infrastructure**

```bash
# Khởi động Kafka services
docker-compose up -d

# Kiểm tra services
docker-compose ps
```

### 4. **Chạy Kafka Producer (tùy chọn)**

```bash
# Terminal 1: Chạy producer để generate test data
python kafka_producer.py
```

### 5. **Khởi động FastAPI Application**

```bash
# Terminal 2: Chạy main app
python app_fastapi.py
```

### 6. **Test Hệ thống**

```bash
# Terminal 3: Chạy test script
python test_pricing.py
```

## 🌐 Endpoints

### **Web Interface**
- **Main UI**: http://localhost:5000
- **Pricing Dashboard**: http://localhost:5000/pricing  
- **API Documentation**: http://localhost:5000/docs
- **Kafka UI**: http://localhost:8080

### **API Endpoints**

#### CRUD Operations
```
GET    /api/categories          # Lấy danh sách categories
POST   /api/categories          # Tạo category mới
PUT    /api/categories/{id}     # Cập nhật category
DELETE /api/categories/{id}     # Xóa category

GET    /api/templates           # Lấy danh sách templates  
POST   /api/templates           # Tạo template mới
PUT    /api/templates/{id}      # Cập nhật template
DELETE /api/templates/{id}      # Xóa template

GET    /api/products            # Lấy danh sách products
POST   /api/products            # Tạo product mới
PUT    /api/products/{id}       # Cập nhật product
DELETE /api/products/{id}       # Xóa product
```

#### Pricing System
```
GET    /api/pricing             # Lấy tất cả pricing data
GET    /api/pricing/{sku}       # Lấy pricing cho SKU cụ thể
POST   /api/pricing/calculate   # Tính pricing cho request
GET    /api/pricing/rates       # Lấy current rates
GET    /events/pricing          # SSE stream cho real-time updates
```

#### System Monitoring  
```
GET    /health                  # Health check với system stats
POST   /test/publish            # Publish test pricing data
```

## 📊 Pricing System Architecture

### **Kafka Topics**
- `pricing_rates`: Tỷ giá vàng/bạc updates
- `product_weights`: Trọng lượng sản phẩm updates

### **Data Flow**
```
Kafka Producer → Kafka Topics → Kafka Consumer → Pricing Calculator → SSE Events → Web UI
```

### **Pricing Models**

```python
# Rate model
{
    "material": "gold|silver",
    "rate_vnd": 75000000,
    "timestamp": "2025-08-08T04:14:14.856584+00:00"
}

# Product Weights model  
{
    "sku": "RING_GOLD_001",
    "weight_gram": 4.98921118664839,
    "material": "gold",
    "timestamp": "2025-08-08T04:14:14.856584+00:00"
}

# Pricing Response
{
    "sku": "RING_GOLD_001",
    "final_price": 465281422,
    "material": "gold", 
    "weight_gram": 4.98921118664839,
    "rate_vnd": 75000000,
    "calculated_at": "2025-08-08T04:14:14.856584+00:00"
}
```

## 🧪 Testing

### **Test Script Features**
- Health check validation
- Pricing API testing
- Kafka connectivity verification  
- SSE connections monitoring
- End-to-end system testing

### **Sample Test Output**
```
=== Real-time Pricing System Test ===

🔍 Health Check:
  Status: healthy
  Kafka Connected: True
  SSE Connections: 2
  Calculator Stats: {'rates_count': 2, 'weights_count': 4, 'pricing_cache_count': 6, 'valid_pricing_count': 6, 'materials': ['gold', 'silver'], 'last_update': '2025-08-08T04:14:14.856584+00:00'}

🔍 Testing Pricing API:
  All pricing count: 6
  NECKLACE_GOLD_001: 16,592,984 VND
  PENDANT_GOLD_001: 923,262,796 VND
  WEDDING_RING_GOLD_001: 3,584,744 VND

✅ Test completed!
```

## 🚀 Quick Start Guide

### **Scenario 1: Chỉ CRUD (Không cần Kafka)**
```bash
# 1. Cài đặt dependencies
pip install fastapi uvicorn jinja2 python-multipart pydantic

# 2. Cấu hình Odoo trong config.py

# 3. Chạy app
python app_fastapi.py

# 4. Truy cập http://localhost:5000
```

### **Scenario 2: Full System với Real-time Pricing**
```bash
# 1. Start Kafka infrastructure
docker-compose up -d

# 2. Start data producer (Terminal 1)
python kafka_producer.py

# 3. Start FastAPI app (Terminal 2)  
python app_fastapi.py

# 4. Test system (Terminal 3)
python test_pricing.py

# 5. Truy cập http://localhost:5000/pricing
```

## 🔍 Troubleshooting

### **Common Issues**

1. **Kafka Connection Failed**
   ```bash
   # Kiểm tra Kafka services
   docker-compose ps
   
   # Restart Kafka
   docker-compose restart kafka
   ```

2. **Odoo Connection Error**  
   ```python
   # Kiểm tra config trong config.py
   # Verify Odoo server accessibility
   ```

3. **SSE Not Working**
   ```bash
   # Kiểm tra browser developer tools
   # Verify /events/pricing endpoint
   ```

4. **Pricing Data Empty**
   ```bash
   # Chạy Kafka producer
   python kafka_producer.py
   
   # Trigger test data
   curl -X POST http://localhost:5000/test/publish
   ```

---

**Happy Coding! 🚀**