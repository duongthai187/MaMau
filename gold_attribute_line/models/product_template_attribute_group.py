from odoo import models, fields

class ProductTemplateAttributeGroup(models.Model):
    _name = 'product.template.attribute.group'
    _description = 'Nhóm thuộc tính mã mẫu'

    name = fields.Char(string='Tên nhóm', required=True)
    code = fields.Char(string='Mã viết tắt')
    sequence = fields.Integer(string='Thứ tự hiển thị', default=10)

    gold_attribute_line_ids = fields.One2many(
        'gold.attribute.line',
        'group_id',
        string='Thuộc tính vàng'
    )
