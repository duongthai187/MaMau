<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# Odoo Product CRUD Client

Đây là một ứng dụng Python Flask client để tương tác với Odoo server thông qua XML-RPC API.

## Cấu trúc dự án

- `app.py` - Flask server chính với các route API
- `odoo_client.py` - Client XML-RPC để kết nối với Odoo
- `config.py` - Cấu hình kết nối Odoo và Flask
- `templates/` - HTML templates sử dụng Bootstrap
- `static/` - CSS và JavaScript files

## Models được quản lý

1. **product.category** - Danh mục sản phẩm
2. **product.template** - Template sản phẩm  
3. **product.product** - Sản phẩm cụ thể

## Quy tắc code

- Sử dụng tiếng Việt cho UI và comments
- Tuân theo cấu trúc API RESTful
- Xử lý lỗi đầy đủ và thông báo user-friendly
- Sử dụng Bootstrap 5 cho UI responsive
- JavaScript vanilla (không dùng jQuery hay framework khác)
- Follow Python PEP 8 standards
