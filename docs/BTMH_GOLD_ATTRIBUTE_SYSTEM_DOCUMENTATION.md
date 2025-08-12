# 📋 BTMH Gold Attribute Management System - Documentation

## 🏗️ Tổng Quan Hệ Thống

**BTMH Gold Attribute Management System** là một hệ thống quản lý thuộc tính vàng tích hợp với Odoo 18, được xây dựng bằng FastAPI và JavaScript. Hệ thống cho phép quản lý chi tiết các thuộc tính sản phẩm vàng với giao diện web responsive và tính năng filter động.

---

## 📁 Cấu Trúc Dự Án

```
d:\BTMH\
├── 🎯 CORE APPLICATION
│   ├── main_app.py                    # FastAPI main application cho Gold Attribute System
│   ├── app_fastapi.py                 # FastAPI legacy application (CRUD cơ bản)
│   ├── odoo_client.py                 # Odoo XML-RPC client
│   ├── config.py                      # Configuration settings
│   └── models.py                      # Pydantic models cho CRUD cơ bản
│
├── 🥇 GOLD ATTRIBUTE MODULE (Odoo Add-on)
│   └── gold_attribute_line/
│       ├── __manifest__.py            # Odoo module manifest
│       ├── models/
│       │   ├── gold_attribute_line.py # Model thuộc tính vàng
│       │   └── product_template_attribute_group.py # Model nhóm thuộc tính
│       ├── views/
│       │   ├── gold_attribute_line_views.xml # Views cho thuộc tính vàng
│       │   ├── product_template_attribute_group_views.xml # Views cho nhóm
│       │   └── menu_root.xml          # Menu configuration
│       ├── security/
│       │   ├── ir.model.access.csv    # Access rights
│       │   └── security.xml           # Security groups
│       └── i18n/
│           └── vi.po                  # Tiếng Việt translation
│
├── 🎨 FRONTEND
│   ├── templates/
│   │   ├── gold_management.html       # Main Gold Attribute Management UI
│   │   ├── base.html                  # Base template
│   │   ├── index.html                 # Landing page
│   │   └── [legacy templates...]      # Các template CRUD cũ
│   └── static/
│       ├── js/
│       │   ├── gold_management.js     # Main JavaScript cho Gold System
│       │   └── [legacy js files...]   # JS files cho CRUD cũ
│       └── css/
│           └── style.css              # Custom styles
│
├── 💰 PRICING SYSTEM (Legacy)
│   ├── pricing_models.py             # Pricing data models
│   ├── pricing_calculator.py         # Pricing calculation logic
│   ├── kafka_pricing_consumer.py     # Kafka consumer
│   ├── kafka_producer.py             # Kafka producer
│   └── test_pricing.py               # Pricing system tests
│
├── 🐳 INFRASTRUCTURE
│   ├── docker-compose.yml            # Kafka infrastructure
│   ├── requirements.txt              # Python dependencies
│   └── README.md                     # Original project documentation
│
└── 📚 DOCUMENTATION
    └── docs/
        └── BTMH_GOLD_ATTRIBUTE_SYSTEM_DOCUMENTATION.md # This file
```

---

## 🏛️ Kiến Trúc Hệ Thống

### 📊 Database Models (Odoo)

#### 1. **product.template.attribute.group** - Nhóm Thuộc Tính
```python
class ProductTemplateAttributeGroup(models.Model):
    _name = 'product.template.attribute.group'
    _description = 'Nhóm thuộc tính mã mẫu'

    name = fields.Char(string='Tên nhóm', required=True)
    code = fields.Char(string='Mã viết tắt')
    sequence = fields.Integer(string='Thứ tự hiển thị', default=10)
    gold_attribute_line_ids = fields.One2many('gold.attribute.line', 'group_id')
```

#### 2. **gold.attribute.line** - Thuộc Tính Vàng
```python
class GoldAttributeLine(models.Model):
    _name = 'gold.attribute.line'
    _description = 'Thuộc tính vàng'

    # Basic Info
    name = fields.Char(string='Tên kỹ thuật', required=True)
    display_name = fields.Char(string='Tên hiển thị')
    short_name = fields.Char(string='Tên viết tắt')
    
    # Field Type & Validation
    field_type = fields.Selection([
        ('char', 'Văn bản'),
        ('float', 'Số thập phân'),
        ('integer', 'Số nguyên'),
        ('boolean', 'Đúng/Sai'),
        ('date', 'Ngày'),
        ('selection', 'Lựa chọn'),
    ], string='Kiểu dữ liệu', required=True)
    
    # Configuration
    required = fields.Boolean(default=False)
    editable = fields.Boolean(default=True)
    active = fields.Boolean(default=True)
    default_value = fields.Char()
    selection_options = fields.Text()
    validation_regex = fields.Char()
    
    # Meta Info
    description = fields.Text()
    unit = fields.Char()
    category = fields.Selection([
        ('technical', 'Kỹ thuật'),
        ('display', 'Hiển thị'),
        ('document', 'Tài liệu'),
    ])
    
    # Relationships
    group_id = fields.Many2one('product.template.attribute.group')
```

### 🔌 API Architecture

#### FastAPI Backend (main_app.py)

**Base URL**: `http://localhost:8000`

##### 📋 API Endpoints

###### **Attribute Groups Management**
```http
GET    /api/attribute-groups              # Lấy danh sách nhóm thuộc tính
POST   /api/attribute-groups              # Tạo nhóm mới
GET    /api/attribute-groups/{group_id}   # Lấy chi tiết nhóm
PUT    /api/attribute-groups/{group_id}   # Cập nhật nhóm
DELETE /api/attribute-groups/{group_id}   # Xóa nhóm
```

###### **Gold Attributes Management**
```http
GET    /api/gold-attributes               # Lấy danh sách thuộc tính vàng
POST   /api/gold-attributes               # Tạo thuộc tính mới
GET    /api/gold-attributes/{attr_id}     # Lấy chi tiết thuộc tính
PUT    /api/gold-attributes/{attr_id}     # Cập nhật thuộc tính
DELETE /api/gold-attributes/{attr_id}     # Xóa thuộc tính
```

###### **Product Templates Management**
```http
GET    /api/product-templates             # Lấy danh sách product templates
POST   /api/product-templates             # Tạo product template mới
GET    /api/product-templates/{tmpl_id}   # Lấy chi tiết template
PUT    /api/product-templates/{tmpl_id}   # Cập nhật template
DELETE /api/product-templates/{tmpl_id}   # Xóa template
```

###### **Dynamic Filtering System**
```http
GET    /api/product-template-attributes   # Lấy danh sách attributes cho filter
GET    /api/product-templates?attr_1=Tròn&attr_2=31&categ_id=16  # Filter examples
```

###### **Utility Endpoints**
```http
GET    /api/categories                    # Lấy danh sách product categories
GET    /health                           # Health check
GET    /                                 # Main web interface
```

#### 📄 Request/Response Models

##### APIResponse Base Model
```python
class APIResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    message: Optional[str] = None
    total: Optional[int] = None
    page: Optional[int] = None
    limit: Optional[int] = None
```

##### Attribute Group Models
```python
class AttributeGroupCreate(BaseModel):
    name: str
    code: Optional[str] = None
    sequence: Optional[int] = 10

class AttributeGroupUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    sequence: Optional[int] = None
```

##### Gold Attribute Models
```python
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
    category: Optional[str] = "technical"
    group_id: Optional[int] = None
```

---

## 🎨 Frontend Architecture

### 📱 Web Interface

#### Main UI: `templates/gold_management.html`
- **Single Page Application** với tab-based navigation
- **Bootstrap 5** responsive design
- **FontAwesome** icons
- **Dynamic content loading** với AJAX

#### Tab Structure:
1. **Nhóm Thuộc Tính** - Quản lý attribute groups
2. **Thuộc Tính Vàng** - Quản lý gold attributes
3. **Mã Mẫu Sản Phẩm** - Quản lý product templates với dynamic filtering

### 🔧 JavaScript Architecture: `static/js/gold_management.js`

#### Core Functions:

##### **Data Loading Functions**
```javascript
// Load attribute groups with pagination and search
async function loadAttributeGroups(page = 1, search = '')

// Load gold attributes with filters
async function loadGoldAttributes(page = 1, search = '', groupId = '', fieldType = '')

// Load product templates with dynamic attribute filtering
async function loadProductTemplatesWithFilters(page = 1, search = '', categoryId = '', attributeFilters = {})

// Load attributes for filter UI generation
async function loadAttributesForProductTemplateFilters()
```

##### **Dynamic Filtering System**
```javascript
// Render filter UI based on attribute count
function renderAttributeFilters(attributes) {
    if (attributes.length <= 5) {
        renderDirectAttributeFilters(container, attributes);
    } else {
        renderSelectableAttributeFilters(container, attributes);
    }
}

// Collect filter values from UI
function collectAttributeFilters() {
    // Returns object like: {1: 'Tròn', 2: '31', 4: 'khong'}
}

// Apply filters to product template search
function applyAttributeFilters()
```

##### **CRUD Operations**
```javascript
// Generic API call function
async function apiCall(url, method = 'GET', data = null)

// Modal management
function showAttributeGroupModal(groupData = null)
function showGoldAttributeModal(attributeData = null)

// Form handling
async function saveAttributeGroup()
async function saveGoldAttribute()
```

---

## 🔍 Dynamic Filtering System

### 🎯 Hoạt Động

#### 1. **UI Rendering Logic**
- **≤5 attributes**: Hiển thị tất cả filters trực tiếp
- **>5 attributes**: Dropdown selector + dynamic value filter

#### 2. **Supported Filter Types**

##### **Selection Fields**
```html
<select class="form-select">
    <option value="">Tất cả Hình dáng</option>
    <option value="Tròn">Tròn</option>
    <option value="Vuông">Vuông</option>
    <option value="Nhỏ">Nhỏ</option>
</select>
```

##### **Boolean Fields**
```html
<select class="form-select">
    <option value="">Tất cả Ánh sáng</option>
    <option value="true">Có</option>
    <option value="false">Không</option>
</select>
```

##### **Text Fields**
```html
<input type="text" class="form-control" placeholder="Tìm Mô tả...">
```

##### **Numeric Fields**
```html
<input type="number" class="form-control" placeholder="Khối lượng..." step="0.01">
```

#### 3. **API Parameter Format**
```
GET /api/product-templates?attr_1=Tròn&attr_2=31&attr_3=100&attr_4=khong
```

#### 4. **Backend Filter Processing**
```python
# Parse attribute filters
attribute_filters = {}
for param_name, param_value in request.query_params.items():
    if param_name.startswith('attr_') and param_value:
        attr_id = param_name.replace('attr_', '')
        attribute_filters[int(attr_id)] = param_value

# Apply filters to search domain based on field types
for attr_id, attr_value in attribute_filters.items():
    attr_info = odoo_client.read('gold.attribute.line', [int(attr_id)], ['field_type', 'name'])
    
    if field_type == 'selection':
        domain.append(['name', 'ilike', attr_value])
    elif field_type in ['char', 'text']:
        domain.append('|')
        domain.append(['name', 'ilike', attr_value])
        domain.append(['description', 'ilike', attr_value])
    # ... other field type handlers
```

---

## 🚀 Deployment & Configuration

### 🔧 Environment Setup

#### 1. **Python Dependencies**
```bash
pip install fastapi uvicorn jinja2 python-multipart pydantic
```

#### 2. **Odoo Configuration** (`config.py`)
```python
ODOO_CONFIG = {
    'url': 'https://your-odoo-server.com',
    'db': 'your_database',
    'username': 'admin',
    'password': 'your_password'
}
```

#### 3. **Run Application**
```bash
# Development mode
python main_app.py

# Production mode (recommended)
uvicorn main_app:app --host 0.0.0.0 --port 8000 --workers 4
```

### 🌐 Access Points
- **Main Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## 🔒 Security & Access Control

### 🛡️ Odoo Security
```xml
<!-- security/ir.model.access.csv -->
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_gold_attribute_line,gold.attribute.line,model_gold_attribute_line,base.group_user,1,1,1,1
access_product_template_attribute_group,product.template.attribute.group,model_product_template_attribute_group,base.group_user,1,1,1,1
```

### 🔐 API Security
- **CORS**: Configured for cross-origin requests
- **Input Validation**: Pydantic models ensure data integrity
- **Error Handling**: Comprehensive exception handling with user-friendly messages

---

## 📊 Performance Considerations

### ⚡ Optimization Features

#### 1. **Pagination**
- Default limit: 20 records per page
- Configurable page sizes
- Total count tracking

#### 2. **Search Optimization**
```python
# Optimized search with indexed fields
domain = []
if search:
    domain.append('|')
    domain.append(['name', 'ilike', search])
    domain.append(['default_code', 'ilike', search])
```

#### 3. **Lazy Loading**
- Tab-based content loading
- On-demand filter generation
- Debounced search inputs (500ms delay)

#### 4. **Caching Strategy**
- Frontend: DOM caching for static data
- Backend: Odoo connection pooling
- API: Response compression support

---

## 🧪 Testing & Quality Assurance

### 🔍 Testing Strategy

#### 1. **API Testing**
```bash
# Test attribute filtering
curl "http://localhost:8000/api/product-templates?attr_1=Tròn&attr_2=31"

# Test pagination
curl "http://localhost:8000/api/attribute-groups?page=2&limit=10"

# Test search
curl "http://localhost:8000/api/gold-attributes?search=vàng"
```

#### 2. **Frontend Testing**
- Browser compatibility testing
- Responsive design validation
- JavaScript error monitoring
- User interaction testing

#### 3. **Integration Testing**
- Odoo connection testing
- CRUD operation validation
- Filter system end-to-end testing

### 📋 Quality Metrics

#### **Code Quality**
- Python: PEP 8 compliance
- JavaScript: ES6+ standards
- HTML: W3C validation
- CSS: BEM methodology

#### **Performance Benchmarks**
- API response time: < 500ms
- Page load time: < 2s
- Filter response: < 300ms
- Search results: < 1s

---

## 🚨 Troubleshooting

### 🔧 Common Issues & Solutions

#### 1. **Odoo Connection Issues**
```python
# Check connection
GET /health

# Expected response:
{
    "status": "healthy",
    "odoo_connected": true,
    "odoo_version": "18.0-20250618",
    "user_id": 2
}
```

#### 2. **Filter Not Working**
```javascript
// Debug filter collection
console.log('Collected filters:', collectAttributeFilters());

// Check API parameters
console.log('API URL:', `/api/product-templates?${params}`);
```

#### 3. **Module Not Found**
```bash
# Ensure gold_attribute_line module is installed in Odoo
# Check module manifest and dependencies
```

#### 4. **JavaScript Errors**
```html
<!-- Ensure all required scripts are loaded -->
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
<script src="/static/js/gold_management.js"></script>
```

### 📞 Debug Commands

#### **Server Logs**
```python
# Enable detailed logging in main_app.py
print(f"🔍 Product templates request params: {dict(request.query_params)}")
print(f"📋 Applying attribute filters: {attribute_filters}")
print(f"🎯 Final search domain: {domain}")
```

#### **Browser Console**
```javascript
// Check filter UI rendering
document.getElementById('attributeFiltersContainer').innerHTML

// Debug API calls
loadProductTemplatesWithFilters(1, '', '', {1: 'Tròn', 2: '31'})
```

---

## 🎯 Future Enhancements

### 🔮 Planned Features

#### 1. **Advanced Filtering**
- Range filters for numeric fields
- Date range selectors
- Multi-select for selection fields
- Custom filter operators (contains, starts with, etc.)

#### 2. **Data Export/Import**
- Excel export functionality
- CSV import for bulk operations
- Template-based data migration

#### 3. **Audit Trail**
- Change tracking for all operations
- User activity logging
- Data versioning

#### 4. **Performance Optimization**
- Redis caching layer
- Database query optimization
- CDN for static assets

#### 5. **Mobile Enhancement**
- Progressive Web App (PWA)
- Offline functionality
- Touch-optimized interfaces

---

## 👥 Development Team

### 📬 Contact Information
- **Project**: BTMH Gold Attribute Management System
- **Version**: 3.0.0
- **Last Updated**: August 12, 2025
- **Documentation**: Complete system overview and technical specification

### 🏆 Achievement Summary
✅ **Complete CRUD System** for all three entity types  
✅ **Dynamic Attribute Filtering** with intelligent UI rendering  
✅ **RESTful API Design** with comprehensive documentation  
✅ **Responsive Web Interface** with modern UX/UI  
✅ **Odoo 18 Integration** with custom module development  
✅ **Production-Ready Architecture** with security and performance considerations  

---

## 📚 API Reference Quick Guide

### 🔄 Common HTTP Status Codes
- **200 OK**: Request successful
- **201 Created**: Resource created successfully  
- **400 Bad Request**: Invalid request data
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server error

### 📋 Response Format
```json
{
    "success": true,
    "data": [...],
    "message": "Operation completed successfully",
    "total": 25,
    "page": 1,
    "limit": 20
}
```

### 🎯 Filter Parameter Examples
```bash
# Single attribute filter
?attr_1=Tròn

# Multiple attribute filters  
?attr_1=Tròn&attr_2=31&attr_3=100

# Combined with other filters
?categ_id=16&attr_1=Vuông&attr_2=40&search=vàng
```

---

*End of Documentation - BTMH Gold Attribute Management System v3.0.0*
