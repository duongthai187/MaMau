# BTMH Gold Management System

Hệ thống quản lý thuộc tính vàng tích hợp với module `gold_attribute_line` trên Odoo.

## Tính Năng

### 🏷️ Nhóm Thuộc Tính (product.template.attribute.group)
- ✅ CRUD hoàn chỉnh cho nhóm thuộc tính
- ✅ Tìm kiếm, phân trang
- ✅ Đếm số thuộc tính trong mỗi nhóm
- ✅ Validation tên nhóm duy nhất

### 🔖 Thuộc Tính Vàng (gold.attribute.line)
- ✅ CRUD hoàn chỉnh cho thuộc tính vàng
- ✅ Hỗ trợ các kiểu dữ liệu: char, float, integer, boolean, date, selection
- ✅ Phân loại: technical, display, document
- ✅ Gắn với nhóm thuộc tính
- ✅ Validation và filter theo nhiều tiêu chí

### 📦 Mã Mẫu Sản Phẩm (product.template)
- ✅ CRUD hoàn chỉnh cho product template
- ✅ Tích hợp với thuộc tính vàng
- ✅ Mapping với product.template.attribute.line
- ✅ Hỗ trợ đầy đủ thông tin sản phẩm

## Cấu Trúc Module gold_attribute_line

### Models
1. **product.template.attribute.group**: Nhóm thuộc tính mã mẫu
2. **gold.attribute.line**: Thuộc tính vàng (thay thế product.template.attribute.line)

### Mapping Logic
- `gold.attribute.line` → `product.attribute` (tên: gold_{attribute_name})
- `gold.attribute.line values` → `product.attribute.value`
- `product.template` → `product.template.attribute.line` (liên kết với product.attribute)

## Cài Đặt & Chạy

### 1. Cấu Hình Odoo
Sửa file `config.py`:
```python
ODOO_CONFIG = {
    'url': 'http://your-odoo-server:8069',
    'db': 'your_database_name',
    'username': 'your_username',
    'password': 'your_password',
}
```

### 2. Cài Đặt Dependencies
```bash
pip install -r requirements.txt
```

### 3. Chạy Ứng Dụng
```bash
python run_gold_management.py
```

### 4. Truy Cập
Mở trình duyệt: http://localhost:8000

## API Endpoints

### Nhóm Thuộc Tính
- `GET /api/attribute-groups` - Lấy danh sách nhóm
- `GET /api/attribute-groups/{id}` - Lấy chi tiết nhóm
- `POST /api/attribute-groups` - Tạo nhóm mới
- `PUT /api/attribute-groups/{id}` - Cập nhật nhóm
- `DELETE /api/attribute-groups/{id}` - Xóa nhóm

### Thuộc Tính Vàng
- `GET /api/gold-attributes` - Lấy danh sách thuộc tính
- `GET /api/gold-attributes/{id}` - Lấy chi tiết thuộc tính
- `POST /api/gold-attributes` - Tạo thuộc tính mới
- `PUT /api/gold-attributes/{id}` - Cập nhật thuộc tính
- `DELETE /api/gold-attributes/{id}` - Xóa thuộc tính

### Mã Mẫu Sản Phẩm
- `GET /api/product-templates` - Lấy danh sách mã mẫu
- `GET /api/product-templates/{id}` - Lấy chi tiết mã mẫu
- `POST /api/product-templates` - Tạo mã mẫu mới
- `PUT /api/product-templates/{id}` - Cập nhật mã mẫu
- `DELETE /api/product-templates/{id}` - Xóa mã mẫu

### Helper APIs
- `GET /api/categories` - Danh mục sản phẩm
- `GET /api/field-types` - Kiểu dữ liệu
- `GET /api/categories-options` - Phân loại thuộc tính
- `GET /health` - Health check

## Giao Diện

Giao diện web với 3 tab chính:
1. **Nhóm Thuộc Tính**: Quản lý nhóm thuộc tính
2. **Thuộc Tính Vàng**: Quản lý thuộc tính vàng
3. **Mã Mẫu Sản Phẩm**: Quản lý product template

Mỗi tab có đầy đủ chức năng:
- ✅ Tìm kiếm & filter
- ✅ Phân trang
- ✅ CRUD operations
- ✅ Form validation
- ✅ Real-time feedback

## Cấu Trúc Thư Mục

```
d:\BTMH\
├── main_app.py              # FastAPI app chính
├── run_gold_management.py   # Script chạy ứng dụng
├── odoo_client.py          # XML-RPC client cho Odoo
├── config.py               # Cấu hình ứng dụng
├── requirements.txt        # Dependencies
├── templates/
│   └── gold_management.html # Giao diện web
├── static/
│   └── js/
│       └── gold_management.js # JavaScript frontend
└── gold_attribute_line/    # Module Odoo (tham khảo)
    ├── __manifest__.py
    └── models/
        ├── gold_attribute_line.py
        └── product_template_attribute_group.py
```

## Lưu Ý Quan Trọng

1. **Module Dependency**: Đảm bảo module `gold_attribute_line` đã được cài đặt trên Odoo server
2. **Permissions**: User Odoo cần quyền đọc/ghi các models: `product.template`, `product.attribute`, `gold.attribute.line`, `product.template.attribute.group`
3. **Database**: Đảm bảo database Odoo đã có module `gold_attribute_line` được active
4. **Network**: Đảm bảo kết nối mạng từ máy chạy app đến Odoo server

## Troubleshooting

### Lỗi kết nối Odoo
- Kiểm tra URL, database name, username, password trong `config.py`
- Kiểm tra Odoo server có chạy không
- Kiểm tra firewall/network

### Module không tìm thấy
- Đảm bảo module `gold_attribute_line` đã được install và active trên Odoo
- Kiểm tra quyền truy cập các models

### Lỗi validation
- Kiểm tra dữ liệu đầu vào
- Xem console browser để debug JavaScript
- Kiểm tra log server

## Phát Triển Thêm

Có thể mở rộng:
- [ ] Export/Import Excel
- [ ] Bulk operations
- [ ] Advanced search
- [ ] Audit trail
- [ ] API authentication
- [ ] Real-time notifications
