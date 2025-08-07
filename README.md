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
pip (Python package manager)
```

### 2. Clone repository
```bash
git clone https://github.com/duongthai187/MaMau.git
cd MaMau
```

### 3. Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### 4. Cấu hình environment variables
```bash
# Copy file template
cp .env.example .env

# Chỉnh sửa file .env với thông tin Odoo của bạn
# Windows:
notepad .env

# Linux/Mac:
nano .env
```

Nội dung file `.env`:
```env
# Cấu hình kết nối Odoo
ODOO_URL=https://your-odoo-server.com
ODOO_DB=your-database-name
ODOO_USERNAME=your-username
ODOO_PASSWORD=your-password

# Cấu hình Flask
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=True
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
├── config.py             # Cấu hình từ environment variables
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables (không commit)
├── .env.example          # Template cho .env
├── .gitignore           # Git ignore rules
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
→ Kiểm tra file .env (ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)
→ Kiểm tra Odoo server có online không
→ Kiểm tra firewall/network connection
→ Verify Odoo credentials bằng cách login web
```

### Lỗi Environment Variables
```
ERROR: ModuleNotFoundError: No module named 'dotenv'
→ Chạy: pip install python-dotenv

ERROR: KeyError trong config
→ Kiểm tra file .env có tồn tại không
→ Đảm bảo tất cả variables được định nghĩa trong .env
→ Copy từ .env.example nếu cần
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

- **Environment Variables**: Thông tin nhạy cảm được lưu trong file `.env` (không commit vào Git)
- **Development Server**: Đây là development server, không dùng cho production
- **Authentication**: Dựa vào Odoo authentication, không có layer riêng
- **CORS**: Được enable cho development
- **Git Security**: File `.env` đã được thêm vào `.gitignore`

### Bảo mật cho Production:
```bash
# Tạo file .env riêng cho production với:
FLASK_DEBUG=False
# Sử dụng strong passwords
# Enable HTTPS
# Setup proper firewall rules
```

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