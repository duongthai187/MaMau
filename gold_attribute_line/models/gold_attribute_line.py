from odoo import models, fields

class GoldAttributeLine(models.Model):
    _name = 'gold.attribute.line'
    _description = 'Thuộc tính vàng'

    name = fields.Char(string='Tên kỹ thuật', required=True)
    display_name = fields.Char(string='Tên hiển thị')
    short_name = fields.Char(string='Tên viết tắt')
    field_type = fields.Selection([
        ('char', 'Văn bản'),
        ('float', 'Số thập phân'),
        ('integer', 'Số nguyên'),
        ('boolean', 'Đúng/Sai'),
        ('date', 'Ngày'),
        ('selection', 'Lựa chọn'),
    ], string='Kiểu dữ liệu', required=True)
    required = fields.Boolean(string='Bắt buộc', default=False)
    editable = fields.Boolean(string='Cho phép chỉnh sửa', default=True)
    active = fields.Boolean(string='Đang sử dụng', default=True)
    default_value = fields.Char(string='Giá trị mặc định')
    description = fields.Text(string='Mô tả')
    unit = fields.Char(string='Đơn vị tính')
    validation_regex = fields.Char(string='Regex kiểm tra')
    selection_options = fields.Text(string='Tùy chọn lựa chọn')
    category = fields.Selection([
        ('technical', 'Kỹ thuật'),
        ('display', 'Hiển thị'),
        ('document', 'Tài liệu'),
    ], string='Phân loại')

    group_id = fields.Many2one(
        'product.template.attribute.group',
        string='Nhóm thuộc tính mã mẫu'
    )
