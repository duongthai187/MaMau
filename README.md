# Odoo Product CRUD Client

Ứng dụng Python Flask client để quản lý sản phẩm Odoo thông qua XML-RPC API với giao diện web Bootstrap 5.

## 📋 Tính năng chính

### 🏷️ Quản lý Categories
- Tạo, sửa, xóa danh mục sản phẩm
- Hỗ trợ danh mục cha-con (hierarchy)
- Giao diện tree view trực quan

### 📝 Quản lý Templates  
- **Template Attributes (Cố định)**: Nhập trực tiếp giá trị (VD: Chất liệu = "Cotton")
- **Variant Attributes**: Chọn attributes để tạo variants (VD: Màu sắc, Size)
- Tự động tạo attribute values khi nhập text mới

### 🔄 Quản lý Products (Variants)
- Tạo product variants từ templates
- Kế thừa template attributes + chọn variant attributes
- **Tự động tạo mã sản phẩm**: `TEMPLATE-ATTR1-ATTR2` (VD: JEWELRY-RED-L)
- Hỗ trợ barcode và serial numbers

### ⚙️ Quản lý Attributes & Values
- CRUD đầy đủ cho product.attribute 
- CRUD đầy đủ cho product.attribute.value
- Filtering và tìm kiếm thông minh

### 📦 Quản lý Serial Numbers
- Quản lý stock.lot (serial numbers)
- Liên kết với products

## 🚀 Cài đặt và chạy

### 1. Yêu cầu hệ thống
```bash
Python 3.8+
Flask 2.3.3
```

### 2. Clone repository
```bash
git clone <repository-url>
cd BTMH
```

### 3. Cài đặt dependencies
```bash
pip install flask flask-cors xmlrpc
```

### 4. Cấu hình Odoo connection
Chỉnh sửa file `config.py`:
```python
ODOO_CONFIG = {
    'url': 'https://your-odoo-server.com',  # Thay đổi URL
    'db': 'your-database',                  # Thay đổi database name  
    'username': 'your-username',            # Thay đổi username
    'password': 'your-password'             # Thay đổi password
}
```

### 5. Chạy ứng dụng
```bash
python app.py
```

### 6. Truy cập web interface
```
http://localhost:5000
```

## 📁 Cấu trúc dự án

```
BTMH/
├── app.py                 # Flask server chính với API routes
├── odoo_client.py         # XML-RPC client để kết nối Odoo
├── config.py             # Cấu hình connection và Flask
├── README.md             # File hướng dẫn này
├── templates/            # HTML templates sử dụng Bootstrap 5
│   ├── index.html        # Trang chủ với navigation
│   ├── categories.html   # Quản lý categories
│   ├── templates.html    # Quản lý product templates
│   ├── products.html     # Quản lý products (variants)
│   ├── attributes.html   # Quản lý attributes
│   ├── values.html       # Quản lý attribute values
│   └── serials.html      # Quản lý serial numbers
└── static/               # CSS và JavaScript files
    ├── css/
    │   └── style.css     # Custom styles
    └── js/
        ├── categories.js # Logic cho categories
        ├── templates.js  # Logic cho templates  
        ├── products.js   # Logic cho products
        ├── attributes.js # Logic cho attributes
        ├── values.js     # Logic cho values
        └── serials.js    # Logic cho serials
```

## 🎯 Workflow sử dụng

### 1. Tạo Attributes & Values
```
1. Vào trang "Attributes" → Tạo attributes (VD: Màu sắc, Size, Chất liệu)
2. Vào trang "Values" → Tạo values cho mỗi attribute:
   - Màu sắc: Đỏ, Xanh, Vàng
   - Size: S, M, L, XL
   - Chất liệu: Cotton, Polyester
```

### 2. Tạo Categories
```
1. Vào trang "Categories" 
2. Tạo hierarchy: Thời trang → Áo → Áo sơ mi
```

### 3. Tạo Templates
```
1. Vào trang "Templates" → Click "Tạo Template"
2. Điền thông tin cơ bản (tên, category, giá...)
3. Template Attributes (cố định):
   - Chọn "Chất liệu" → Nhập "100% Cotton"  
   - Chọn "Thương hiệu" → Nhập "Nike"
4. Variant Attributes (để tạo variants):
   - Chọn "Màu sắc" và "Size" (Ctrl+Click)
5. Lưu template
```

### 4. Tạo Products (Variants)
```
1. Vào trang "Products" → Click "Tạo Product"
2. Chọn template đã tạo
3. Hệ thống hiển thị variant attributes để chọn:
   - Màu sắc: Chọn "Đỏ"
   - Size: Chọn "L" 
4. Mã sản phẩm tự động tạo: "NIKE-DO-L"
5. Product sẽ kế thừa: Chất liệu="100% Cotton", Thương hiệu="Nike"
```

## 📊 Models được quản lý

| Model | Mô tả | API Endpoint |
|-------|-------|--------------|
| `product.category` | Danh mục sản phẩm | `/api/categories` |
| `product.template` | Template sản phẩm với attributes | `/api/templates` |  
| `product.product` | Sản phẩm cụ thể (variants) | `/api/products` |
| `product.attribute` | Thuộc tính sản phẩm | `/api/attributes` |
| `product.attribute.value` | Giá trị thuộc tính | `/api/values` |
| `stock.lot` | Serial numbers | `/api/serials` |

## 🔧 API Endpoints

### Categories
```bash
GET    /api/categories          # Lấy danh sách categories
POST   /api/categories          # Tạo category mới  
PUT    /api/categories/{id}     # Cập nhật category
DELETE /api/categories/{id}     # Xóa category
```

### Templates  
```bash
GET    /api/templates           # Lấy danh sách templates
POST   /api/templates           # Tạo template mới với attributes
PUT    /api/templates/{id}      # Cập nhật template
DELETE /api/templates/{id}      # Xóa template
GET    /api/templates/{id}/attributes # Lấy attributes của template
```

### Products
```bash
GET    /api/products            # Lấy danh sách products
POST   /api/products            # Tạo product mới (auto-generate code)
PUT    /api/products/{id}       # Cập nhật product  
DELETE /api/products/{id}       # Xóa product
```

### Attributes & Values
```bash
GET    /api/attributes          # Lấy danh sách attributes
POST   /api/attributes          # Tạo attribute mới
GET    /api/values              # Lấy danh sách values
POST   /api/values              # Tạo value mới
```

## 🎨 Giao diện

- **Framework**: Bootstrap 5
- **JavaScript**: Vanilla JS (ES6+) với async/await
- **Responsive**: Tương thích mobile và desktop
- **Features**: Loading states, alerts, form validation

## ⚡ Tính năng nâng cao

### Auto-generation mã sản phẩm
```javascript
// Ví dụ mã được tạo tự động:
Template: "JEWELRY" + Attributes: ["Đỏ", "Lớn"] 
→ Mã sản phẩm: "JEWELRY-DO-LO"

// Hỗ trợ tiếng Việt với unicodedata normalization
"Đá quý" → "DQ"
"Màu xanh lá cây" → "MAXL"
```

### Smart attribute management
- Tự động tạo attribute values khi nhập text mới
- Phân biệt template attributes (cố định) vs variant attributes
- Inheritance từ template xuống products

### Filtering và search
- Filter products theo attributes
- Search realtime
- Pagination và sorting

## 🐛 Troubleshooting

### Lỗi kết nối Odoo
```
ERROR: Kết nối thất bại
→ Kiểm tra config.py (URL, database, username, password)
→ Kiểm tra Odoo server có online không
→ Kiểm tra firewall/network connection
```

### Lỗi JavaScript
```
ERROR: Cannot read property of undefined
→ Mở Developer Tools (F12) để xem console errors
→ Kiểm tra network requests trong tab Network
→ Restart Flask server: Ctrl+C → python app.py
```

### Lỗi API
```
ERROR: 500 Internal Server Error  
→ Kiểm tra terminal output của Flask server
→ Kiểm tra Odoo permissions cho user
→ Kiểm tra data format trong API calls
```

## 🔒 Security Notes

- Đây là development server, không dùng cho production
- Thông tin kết nối Odoo được lưu plaintext trong config.py
- Không có authentication layer (dựa vào Odoo auth)
- CORS được enable cho development

## 🚀 Production Deployment

Để deploy production:
```bash
# Sử dụng WSGI server như Gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app

# Hoặc sử dụng Apache/Nginx reverse proxy
# Thêm SSL certificate
# Enable proper logging và monitoring
```

## 📞 Hỗ trợ

Nếu gặp vấn đề:
1. Kiểm tra logs trong terminal Flask server
2. Kiểm tra browser Developer Tools (F12) 
3. Kiểm tra Odoo server logs
4. Test API endpoints với Postman/curl

---
**Phiên bản**: 1.0.0  
**Tương thích**: Odoo 18.0, Python 3.8+, Bootstrap 5