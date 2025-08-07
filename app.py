from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from odoo_client import odoo_client
from config import FLASK_CONFIG

app = Flask(__name__)
CORS(app)

# Kết nối Odoo khi khởi động
with app.app_context():
    odoo_client.connect()

# Routes cho UI
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/categories')
def categories():
    return render_template('categories.html')

@app.route('/templates')
def templates():
    return render_template('templates.html')

@app.route('/products')
def products():
    return render_template('products.html')

@app.route('/serials')
def serials():
    return render_template('serials.html')

@app.route('/attributes')
def attributes():
    return render_template('attributes.html')

# API Routes cho Product Attributes
@app.route('/api/attributes', methods=['GET'])
def get_attributes():
    """Lấy danh sách product attributes"""
    try:
        attributes = odoo_client.search_read(
            'product.attribute',
            [],
            ['id', 'name', 'display_type', 'create_variant', 'value_ids']
        )
        return jsonify({'success': True, 'data': attributes})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/attributes', methods=['POST'])
def create_attribute():
    """Tạo product attribute mới"""
    try:
        data = request.get_json()
        values = {
            'name': data.get('name'),
            'display_type': data.get('display_type', 'radio'),
            'create_variant': data.get('create_variant', 'always'),
        }
        
        attribute_id = odoo_client.create('product.attribute', values)
        if attribute_id:
            return jsonify({'success': True, 'id': attribute_id})
        else:
            return jsonify({'success': False, 'error': 'Không thể tạo attribute'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/attributes/<int:attribute_id>', methods=['PUT'])
def update_attribute(attribute_id):
    """Cập nhật product attribute"""
    try:
        data = request.get_json()
        values = {}
        
        if 'name' in data:
            values['name'] = data['name']
        if 'display_type' in data:
            values['display_type'] = data['display_type']
        if 'create_variant' in data:
            values['create_variant'] = data['create_variant']
            
        success = odoo_client.write('product.attribute', attribute_id, values)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/attributes/<int:attribute_id>', methods=['DELETE'])
def delete_attribute(attribute_id):
    """Xóa product attribute"""
    try:
        success = odoo_client.unlink('product.attribute', attribute_id)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# API Routes cho Attribute Values
@app.route('/api/attribute-values', methods=['GET'])
def get_attribute_values():
    """Lấy danh sách attribute values"""
    try:
        attribute_id = request.args.get('attribute_id')
        domain = []
        if attribute_id:
            domain.append(['attribute_id', '=', int(attribute_id)])
            
        values = odoo_client.search_read(
            'product.attribute.value',
            domain,
            ['id', 'name', 'attribute_id', 'sequence']
        )
        return jsonify({'success': True, 'data': values})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/attribute-values', methods=['POST'])
def create_attribute_value():
    """Tạo attribute value mới"""
    try:
        data = request.get_json()
        values = {
            'name': data.get('name'),
            'attribute_id': data.get('attribute_id'),
            'sequence': data.get('sequence', 1),
        }
        
        value_id = odoo_client.create('product.attribute.value', values)
        if value_id:
            return jsonify({'success': True, 'id': value_id})
        else:
            return jsonify({'success': False, 'error': 'Không thể tạo attribute value'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/attribute-values/<int:value_id>', methods=['PUT'])
def update_attribute_value(value_id):
    """Cập nhật attribute value"""
    try:
        data = request.get_json()
        values = {}
        
        if 'name' in data:
            values['name'] = data['name']
        if 'sequence' in data:
            values['sequence'] = data['sequence']
            
        success = odoo_client.write('product.attribute.value', value_id, values)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/attribute-values/<int:value_id>', methods=['DELETE'])
def delete_attribute_value(value_id):
    """Xóa attribute value"""
    try:
        success = odoo_client.unlink('product.attribute.value', value_id)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# API Routes cho Product Categories
@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Lấy danh sách categories"""
    try:
        categories = odoo_client.search_read(
            'product.category',
            [],
            ['id', 'name', 'parent_id', 'child_id']
        )
        return jsonify({'success': True, 'data': categories})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/categories', methods=['POST'])
def create_category():
    """Tạo category mới"""
    try:
        data = request.get_json()
        values = {
            'name': data.get('name'),
            'parent_id': data.get('parent_id') if data.get('parent_id') else False,
        }
        
        category_id = odoo_client.create('product.category', values)
        if category_id:
            return jsonify({'success': True, 'id': category_id})
        else:
            return jsonify({'success': False, 'error': 'Không thể tạo category'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/categories/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    """Cập nhật category"""
    try:
        data = request.get_json()
        values = {}
        
        if 'name' in data:
            values['name'] = data['name']
        if 'parent_id' in data:
            values['parent_id'] = data['parent_id'] if data['parent_id'] else False
            
        success = odoo_client.write('product.category', category_id, values)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    """Xóa category"""
    try:
        success = odoo_client.unlink('product.category', category_id)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# API Routes cho Product Templates
@app.route('/api/templates', methods=['GET'])
def get_templates():
    """Lấy danh sách product templates"""
    try:
        # Lấy tất cả templates không phân biệt active, không giới hạn limit
        templates = odoo_client.search_read(
            'product.template',
            ['|', ['active', '=', True], ['active', '=', False]],
            ['id', 'name', 'categ_id', 'list_price', 'standard_price', 'type', 'active', 'default_code', 'attribute_line_ids'],
            limit=None  # Không giới hạn số lượng
        )
        print(f"DEBUG: Found {len(templates)} templates")
        # Sắp xếp theo ID giảm dần để templates mới nhất ở đầu
        templates.sort(key=lambda x: x['id'], reverse=True)
        return jsonify({'success': True, 'data': templates})
    except Exception as e:
        print(f"DEBUG: Error getting templates: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/templates/<int:template_id>/attributes', methods=['GET'])
def get_template_attributes(template_id):
    """Lấy attributes của một template cụ thể, phân biệt template attributes và variant attributes"""
    try:
        # Lấy attribute lines của template
        attribute_lines = odoo_client.search_read(
            'product.template.attribute.line',
            [['product_tmpl_id', '=', template_id]],
            ['id', 'attribute_id', 'value_ids']
        )
        
        # Lấy chi tiết attributes và values
        template_attributes = []  # Attributes cố định của template (chỉ 1 value)
        variant_attributes = []   # Attributes để tạo variants (nhiều values)
        
        for line in attribute_lines:
            if line['attribute_id']:
                attribute = odoo_client.search_read(
                    'product.attribute',
                    [['id', '=', line['attribute_id'][0]]],
                    ['id', 'name', 'display_type']
                )
                
                if attribute:
                    attr_data = attribute[0]
                    
                    # Lấy values của attribute này trong template
                    if line['value_ids']:
                        values = odoo_client.search_read(
                            'product.attribute.value',
                            [['id', 'in', line['value_ids']]],
                            ['id', 'name', 'sequence']
                        )
                        attr_data['values'] = sorted(values, key=lambda x: x['sequence'])
                        
                        # Phân loại dựa trên số lượng values
                        if len(values) == 1:
                            # Template attribute (cố định)
                            attr_data['attribute_name'] = attr_data['name']
                            attr_data['attribute_id'] = attr_data['id']
                            template_attributes.append(attr_data)
                        else:
                            # Variant attribute (để tạo variants)
                            attr_data['attribute_name'] = attr_data['name']
                            attr_data['attribute_id'] = attr_data['id']
                            variant_attributes.append(attr_data)
                    else:
                        attr_data['values'] = []
                        variant_attributes.append(attr_data)
        
        return jsonify({
            'success': True, 
            'data': variant_attributes,  # Backward compatibility
            'template_attributes': template_attributes,
            'variant_attributes': variant_attributes
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/templates/suggest', methods=['POST'])
def suggest_templates():
    """Gợi ý templates tương đồng dựa trên category và tên"""
    try:
        data = request.get_json()
        domain = []
        
        # Tạo domain filter dựa trên category và search name
        if data.get('categ_id'):
            domain.append(['categ_id', '=', data['categ_id']])
        if data.get('name'):
            domain.append(['name', 'ilike', data['name']])
            
        templates = odoo_client.search_read(
            'product.template',
            domain,
            ['id', 'name', 'categ_id', 'list_price', 'standard_price', 'default_code', 'barcode']
        )
        return jsonify({'success': True, 'data': templates})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/templates', methods=['POST'])
def create_template():
    """Tạo product template mới với template attributes và variant attributes"""
    try:
        data = request.get_json()
        print(f"DEBUG: Received data: {data}")
        
        values = {
            'name': data.get('name'),
            'categ_id': data.get('categ_id'),
            'list_price': float(data.get('list_price', 0)),
            'standard_price': float(data.get('standard_price', 0)),
            'type': data.get('type', 'consu'),
            'default_code': data.get('default_code', ''),
        }
        print(f"DEBUG: Values to create: {values}")
        
        template_id = odoo_client.create('product.template', values)
        print(f"DEBUG: Created template ID: {template_id}")
        
        if template_id:
            # Xử lý template attributes (attributes cố định của template)
            template_attributes = data.get('template_attributes', {})  # {attr_id: "text_value"}
            for attr_id, text_value in template_attributes.items():
                # Tạo hoặc tìm attribute value với text này
                existing_values = odoo_client.search_read(
                    'product.attribute.value',
                    [['attribute_id', '=', int(attr_id)], ['name', '=', text_value]],
                    ['id']
                )
                
                if existing_values:
                    # Sử dụng value có sẵn
                    value_id = existing_values[0]['id']
                else:
                    # Tạo value mới
                    value_id = odoo_client.create('product.attribute.value', {
                        'attribute_id': int(attr_id),
                        'name': text_value
                    })
                
                # Tạo attribute line với value này
                line_values = {
                    'product_tmpl_id': template_id,
                    'attribute_id': int(attr_id),
                    'value_ids': [(6, 0, [value_id])]  # Chỉ 1 value cố định
                }
                odoo_client.create('product.template.attribute.line', line_values)
                print(f"DEBUG: Created template attribute line for attr {attr_id} = text '{text_value}' (value_id: {value_id})")
            
            # Xử lý variant attributes (attributes để tạo variants) 
            variant_attributes = data.get('variant_attributes', [])  # [attr_id1, attr_id2, ...]
            for attr_id in variant_attributes:
                # Lấy tất cả values của attribute này để có thể tạo variants
                attr_values = odoo_client.search_read(
                    'product.attribute.value',
                    [['attribute_id', '=', int(attr_id)]],
                    ['id']
                )
                
                if attr_values:
                    value_ids = [v['id'] for v in attr_values]
                    line_values = {
                        'product_tmpl_id': template_id,
                        'attribute_id': int(attr_id),
                        'value_ids': [(6, 0, value_ids)]  # Tất cả values để tạo variants
                    }
                    odoo_client.create('product.template.attribute.line', line_values)
                    print(f"DEBUG: Created variant attribute line for attr {attr_id}")
            
            # Backward compatibility với attribute_ids cũ
            if data.get('attribute_ids') and not template_attributes and not variant_attributes:
                for attr_id in data['attribute_ids']:
                    attr_values = odoo_client.search_read(
                        'product.attribute.value',
                        [['attribute_id', '=', attr_id]],
                        ['id']
                    )
                    
                    if attr_values:
                        value_ids = [v['id'] for v in attr_values]
                        line_values = {
                            'product_tmpl_id': template_id,
                            'attribute_id': attr_id,
                            'value_ids': [(6, 0, value_ids)]
                        }
                        odoo_client.create('product.template.attribute.line', line_values)
            
            return jsonify({'success': True, 'id': template_id})
        else:
            return jsonify({'success': False, 'error': 'Không thể tạo template'})
    except Exception as e:
        print(f"DEBUG: Error creating template: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/templates/<int:template_id>', methods=['PUT'])
def update_template(template_id):
    """Cập nhật product template"""
    try:
        data = request.get_json()
        values = {}
        
        if 'name' in data:
            values['name'] = data['name']
        if 'categ_id' in data:
            values['categ_id'] = data['categ_id']
        if 'list_price' in data:
            values['list_price'] = float(data['list_price'])
        if 'standard_price' in data:
            values['standard_price'] = float(data['standard_price'])
        if 'type' in data:
            values['type'] = data['type']
        if 'default_code' in data:
            values['default_code'] = data['default_code']
        if 'barcode' in data:
            values['barcode'] = data['barcode']
            
        success = odoo_client.write('product.template', template_id, values)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/templates/<int:template_id>', methods=['DELETE'])
def delete_template(template_id):
    """Xóa product template"""
    try:
        success = odoo_client.unlink('product.template', template_id)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# API Routes cho Products
@app.route('/api/products', methods=['GET'])
def get_products():
    """Lấy danh sách products"""
    try:
        products = odoo_client.search_read(
            'product.product',
            [],
            ['id', 'name', 'product_tmpl_id', 'default_code', 'barcode', 'active', 'lst_price', 'product_template_attribute_value_ids']
        )
        return jsonify({'success': True, 'data': products})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/products/all-attributes', methods=['GET'])
def get_all_product_attributes():
    """Lấy tất cả attributes có trong products để làm filter"""
    try:
        # Lấy tất cả attributes đang được sử dụng
        attributes = odoo_client.search_read(
            'product.attribute',
            [],
            ['id', 'name', 'display_type']
        )
        
        # Với mỗi attribute, lấy values đang được sử dụng
        for attr in attributes:
            values = odoo_client.search_read(
                'product.attribute.value',
                [['attribute_id', '=', attr['id']]],
                ['id', 'name', 'sequence']
            )
            attr['values'] = sorted(values, key=lambda x: x['sequence'])
        
        return jsonify({'success': True, 'data': attributes})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/products/suggest', methods=['POST'])
def suggest_products():
    """Gợi ý products dựa trên attributes được chọn"""
    try:
        data = request.get_json()
        domain = []
        
        # Filter theo template nếu có
        if data.get('template_id'):
            domain.append(['product_tmpl_id', '=', data['template_id']])
            
        # Filter theo attribute values nếu có
        if data.get('attribute_value_ids'):
            for value_id in data['attribute_value_ids']:
                domain.append(['product_template_attribute_value_ids.product_attribute_value_id', '=', value_id])
        
        products = odoo_client.search_read(
            'product.product',
            domain,
            ['id', 'name', 'product_tmpl_id', 'default_code', 'barcode', 'lst_price', 'product_template_attribute_value_ids']
        )
        
        return jsonify({'success': True, 'data': products})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/products', methods=['POST'])
def create_product():
    """Tạo product mới"""
    try:
        data = request.get_json()
        
        # Lấy thông tin template để tạo mã sản phẩm
        template_info = odoo_client.search_read(
            'product.template',
            [['id', '=', data.get('product_tmpl_id')]],
            ['name', 'default_code']
        )
        
        auto_code = ""
        auto_name = ""
        
        if template_info:
            template = template_info[0]
            base_code = template.get('default_code', '') or 'PROD'
            base_name = template.get('name', '')
            
            # Nếu có attribute values, tạo product variant
            if data.get('attribute_value_ids'):
                # Lấy thông tin attribute values để tạo mã
                value_codes = []
                value_names = []
                
                for value_id in data['attribute_value_ids']:
                    value_info = odoo_client.search_read(
                        'product.attribute.value',
                        [['id', '=', value_id]],
                        ['name', 'attribute_id']
                    )
                    if value_info:
                        value = value_info[0]
                        # Tạo code ngắn từ tên (VD: "Đỏ" -> "DO", "Size L" -> "L")
                        code_part = generate_attribute_code(value['name'])
                        value_codes.append(code_part)
                        value_names.append(value['name'])
                
                # Tạo mã sản phẩm: BASE_CODE-ATTR1-ATTR2
                auto_code = f"{base_code}-{'-'.join(value_codes)}"
                auto_name = f"{base_name} ({', '.join(value_names)})"
                
                # Tạo product template attribute value combinations
                ptav_ids = []
                for value_id in data['attribute_value_ids']:
                    # Tìm hoặc tạo product.template.attribute.value
                    ptav = odoo_client.search_read(
                        'product.template.attribute.value',
                        [['product_tmpl_id', '=', data.get('product_tmpl_id')], 
                         ['product_attribute_value_id', '=', value_id]],
                        ['id']
                    )
                    if ptav:
                        ptav_ids.append(ptav[0]['id'])
                
                values = {
                    'product_tmpl_id': data.get('product_tmpl_id'),
                    'product_template_attribute_value_ids': [(6, 0, ptav_ids)],
                    'default_code': auto_code,
                    'barcode': data.get('barcode', ''),
                }
            else:
                # Tạo product thông thường
                auto_code = data.get('default_code', '') or f"{base_code}-001"
                values = {
                    'name': data.get('name') or auto_name,
                    'product_tmpl_id': data.get('product_tmpl_id'),
                    'default_code': auto_code,
                    'barcode': data.get('barcode', ''),
                }
        
        print(f"DEBUG: Auto-generated code: {auto_code}")
        print(f"DEBUG: Product values: {values}")
        
        product_id = odoo_client.create('product.product', values)
        if product_id:
            return jsonify({'success': True, 'id': product_id, 'generated_code': auto_code})
        else:
            return jsonify({'success': False, 'error': 'Không thể tạo product'})
    except Exception as e:
        print(f"DEBUG: Error creating product: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

def generate_attribute_code(value_name):
    """Tạo mã ngắn từ tên attribute value"""
    # Loại bỏ dấu và chuyển thành chữ hoa
    import unicodedata
    
    # Normalize và loại bỏ dấu
    normalized = unicodedata.normalize('NFD', value_name)
    ascii_text = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
    
    # Chuyển thành chữ hoa và lấy từ khóa
    words = ascii_text.upper().replace(' ', '').replace('-', '')
    
    # Nếu là số hoặc một ký tự -> giữ nguyên
    if len(words) <= 2 or words.isdigit():
        return words
    
    # Lấy 2-3 ký tự đầu
    return words[:3]

@app.route('/api/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """Cập nhật product"""
    try:
        data = request.get_json()
        values = {}
        
        if 'name' in data:
            values['name'] = data['name']
        if 'default_code' in data:
            values['default_code'] = data['default_code']
        if 'barcode' in data:
            values['barcode'] = data['barcode']
            
        success = odoo_client.write('product.product', product_id, values)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Xóa product"""
    try:
        success = odoo_client.unlink('product.product', product_id)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# API Routes cho Stock Lots (Serial Numbers)
@app.route('/api/serials', methods=['GET'])
def get_serials():
    """Lấy danh sách serial numbers"""
    try:
        serials = odoo_client.search_read(
            'stock.lot',
            [],
            ['id', 'name', 'product_id', 'company_id', 'ref', 'create_date']
        )
        return jsonify({'success': True, 'data': serials})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/serials', methods=['POST'])
def create_serial():
    """Tạo serial number mới"""
    try:
        data = request.get_json()
        values = {
            'name': data.get('name'),
            'product_id': data.get('product_id'),
            'ref': data.get('ref', ''),
        }
        
        serial_id = odoo_client.create('stock.lot', values)
        if serial_id:
            return jsonify({'success': True, 'id': serial_id})
        else:
            return jsonify({'success': False, 'error': 'Không thể tạo serial number'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/serials/<int:serial_id>', methods=['PUT'])
def update_serial(serial_id):
    """Cập nhật serial number"""
    try:
        data = request.get_json()
        values = {}
        
        if 'name' in data:
            values['name'] = data['name']
        if 'ref' in data:
            values['ref'] = data['ref']
            
        success = odoo_client.write('stock.lot', serial_id, values)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/serials/<int:serial_id>', methods=['DELETE'])
def delete_serial(serial_id):
    """Xóa serial number"""
    try:
        success = odoo_client.unlink('stock.lot', serial_id)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(
        host=FLASK_CONFIG['host'],
        port=FLASK_CONFIG['port'], 
        debug=FLASK_CONFIG['debug']
    )
