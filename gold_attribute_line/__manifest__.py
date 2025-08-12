{
    'name': 'Gold Attribute Line',
    'version': '1.0',
    'summary': 'Extend product attribute line for gold-specific data',
    'author': 'AnhND',
    'category': 'Product',
    'depends': ['product'],
    'data': [
        'security/ir.model.access.csv',
        'views/menu_root.xml',
        'views/product_template_attribute_group_views.xml',
        'views/gold_attribute_line_views.xml',
    ],
    'installable': True,
    'application': False,
}
