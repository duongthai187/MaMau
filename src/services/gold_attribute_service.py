"""
Odoo Gold Attribute Integration Service
Tích hợp hoàn toàn với module gold_attribute_line trên Odoo server
Thay thế cho client-side storage
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from ..core.odoo_client import odoo_client

class OdooGoldAttributeService:
    """Service để tương tác với gold_attribute_line module trên Odoo"""
    
    def __init__(self):
        self.odoo = odoo_client
        # Cache để tối ưu performance
        self._gold_attr_cache = {}
        self._product_attr_cache = {}
    
    def _get_or_create_product_attribute(self, gold_attribute_id: int) -> Optional[int]:
        """Lấy hoặc tạo product.attribute tương ứng với gold.attribute.line"""
        try:
            # Check cache first
            if gold_attribute_id in self._product_attr_cache:
                return self._product_attr_cache[gold_attribute_id]
            
            # Lấy thông tin gold attribute
            gold_attr = self.odoo.read('gold.attribute.line', [gold_attribute_id], [
                'name', 'display_name', 'field_type'
            ])
            
            if not gold_attr:
                return None
                
            gold_attr = gold_attr[0]
            attr_name = f"gold_{gold_attr['name']}"
            
            # Tìm product.attribute có sẵn
            existing_attr = self.odoo.search('product.attribute', [
                ['name', '=', attr_name]
            ])
            
            if existing_attr:
                product_attr_id = existing_attr[0]
            else:
                # Tạo mới nếu chưa có
                product_attr_id = self.odoo.create('product.attribute', {
                    'name': attr_name,
                    'display_name': gold_attr['display_name'] or gold_attr['name'],
                    'sequence': 10,
                    'create_variant': 'no_variant'  # Không tạo variant cho gold attributes
                })
            
            # Cache result
            self._product_attr_cache[gold_attribute_id] = product_attr_id
            return product_attr_id
            
        except Exception as e:
            print(f"Error getting/creating product attribute: {e}")
            return None
    
    def _get_gold_attributes_mapping(self) -> Dict[str, int]:
        """Lấy mapping từ product.attribute name về gold.attribute.line id"""
        try:
            gold_attrs = self.odoo.search_read('gold.attribute.line', [], ['name'])
            mapping = {}
            for attr in gold_attrs:
                product_attr_name = f"gold_{attr['name']}"
                mapping[product_attr_name] = attr['id']
            return mapping
        except Exception as e:
            print(f"Error getting gold attributes mapping: {e}")
            return {}
    
    # ================================
    # NHÓM THUỘC TÍNH (product.template.attribute.group)
    # ================================
    
    def get_attribute_groups(self, search: Optional[str] = None, page: int = 1, limit: int = 20) -> Tuple[List[Dict], int]:
        """Lấy danh sách nhóm thuộc tính"""
        domain = []
        if search:
            domain.append(['name', 'ilike', search])
        
        offset = (page - 1) * limit
        groups = self.odoo.search_read(
            'product.template.attribute.group',
            domain,
            ['name', 'code', 'sequence', 'create_date', 'write_date'],
            offset=offset,
            limit=limit,
            order='sequence, name'
        )
        
        # Đếm số thuộc tính trong mỗi nhóm
        for group in groups:
            attr_count = self.odoo.search_count('gold.attribute.line', [['group_id', '=', group['id']]])
            group['attribute_count'] = attr_count
        
        total = self.odoo.search_count('product.template.attribute.group', domain)
        return groups, total
    
    def get_attribute_group(self, group_id: int) -> Optional[Dict]:
        """Lấy thông tin nhóm thuộc tính theo ID"""
        group = self.odoo.read('product.template.attribute.group', [group_id], [
            'name', 'code', 'sequence', 'create_date', 'write_date'
        ])
        if not group:
            return None
        
        group = group[0]
        # Đếm số thuộc tính
        attr_count = self.odoo.search_count('gold.attribute.line', [['group_id', '=', group_id]])
        group['attribute_count'] = attr_count
        
        return group
    
    def create_attribute_group(self, group_data: Dict) -> int:
        """Tạo nhóm thuộc tính mới"""
        return self.odoo.create('product.template.attribute.group', group_data)
    
    def update_attribute_group(self, group_id: int, group_data: Dict) -> bool:
        """Cập nhật nhóm thuộc tính"""
        return self.odoo.write('product.template.attribute.group', [group_id], group_data)
    
    def delete_attribute_group(self, group_id: int) -> bool:
        """Xóa nhóm thuộc tính (chỉ khi không có thuộc tính nào)"""
        # Kiểm tra xem có thuộc tính nào trong nhóm không
        attr_count = self.odoo.search_count('gold.attribute.line', [['group_id', '=', group_id]])
        if attr_count > 0:
            raise ValueError(f"Không thể xóa nhóm thuộc tính có {attr_count} thuộc tính")
        
        return self.odoo.unlink('product.template.attribute.group', [group_id])
    
    # ================================
    # THUỘC TÍNH VÀNG (gold.attribute.line)
    # ================================
    
    def get_gold_attributes(self, group_id: Optional[int] = None, search: Optional[str] = None, 
                           page: int = 1, limit: int = 20) -> Tuple[List[Dict], int]:
        """Lấy danh sách thuộc tính vàng"""
        domain = []
        if group_id:
            domain.append(['group_id', '=', group_id])
        if search:
            domain.extend([
                '|', '|',
                ['name', 'ilike', search],
                ['display_name', 'ilike', search],
                ['short_name', 'ilike', search]
            ])
        
        offset = (page - 1) * limit
        attributes = self.odoo.search_read(
            'gold.attribute.line',
            domain,
            ['name', 'display_name', 'short_name', 'field_type', 'required', 'editable', 
             'active', 'default_value', 'description', 'unit', 'category', 'group_id',
             'create_date', 'write_date'],
            offset=offset,
            limit=limit,
            order='group_id, name'
        )
        
        # Lấy tên nhóm cho mỗi thuộc tính
        group_ids = [attr['group_id'][0] for attr in attributes if attr.get('group_id')]
        group_dict = {}
        if group_ids:
            groups = self.odoo.read('product.template.attribute.group', group_ids, ['name'])
            group_dict = {g['id']: g['name'] for g in groups}
        
        for attr in attributes:
            if attr.get('group_id'):
                attr['group_name'] = group_dict.get(attr['group_id'][0], '')
            else:
                attr['group_name'] = ''
        
        total = self.odoo.search_count('gold.attribute.line', domain)
        return attributes, total
    
    def get_gold_attribute(self, attribute_id: int) -> Optional[Dict]:
        """Lấy thông tin thuộc tính vàng theo ID"""
        attribute = self.odoo.read('gold.attribute.line', [attribute_id], [
            'name', 'display_name', 'short_name', 'field_type', 'required', 'editable',
            'active', 'default_value', 'description', 'unit', 'validation_regex',
            'selection_options', 'category', 'group_id', 'create_date', 'write_date'
        ])
        if not attribute:
            return None
        
        attribute = attribute[0]
        
        # Lấy tên nhóm
        if attribute.get('group_id'):
            group = self.odoo.read('product.template.attribute.group', [attribute['group_id'][0]], ['name'])
            attribute['group_name'] = group[0]['name'] if group else ''
        else:
            attribute['group_name'] = ''
        
        return attribute
    
    def create_gold_attribute(self, attribute_data: Dict) -> int:
        """Tạo thuộc tính vàng mới"""
        return self.odoo.create('gold.attribute.line', attribute_data)
    
    def update_gold_attribute(self, attribute_id: int, attribute_data: Dict) -> bool:
        """Cập nhật thuộc tính vàng"""
        return self.odoo.write('gold.attribute.line', [attribute_id], attribute_data)
    
    def delete_gold_attribute(self, attribute_id: int) -> bool:
        """Xóa thuộc tính vàng"""
        return self.odoo.unlink('gold.attribute.line', [attribute_id])
    
    # ================================
    # PRODUCT TEMPLATE - GOLD ATTRIBUTE VALUES 
    # ================================
    
    def get_product_gold_attributes(self, product_template_id: int) -> List[Dict]:
        """Lấy tất cả gold attributes của một product template
        Sử dụng product.template.attribute.line và product.template.attribute.value có sẵn
        """
        try:
            # Lấy mapping gold attributes
            gold_mapping = self._get_gold_attributes_mapping()
            if not gold_mapping:
                return []
            
            # Lấy tất cả product.attribute có tên bắt đầu với "gold_"
            gold_product_attrs = self.odoo.search('product.attribute', [
                ['name', 'in', list(gold_mapping.keys())]
            ])
            
            if not gold_product_attrs:
                return []
            
            # Tìm các attribute lines của product này
            attr_lines = self.odoo.search_read(
                'product.template.attribute.line',
                [
                    ['product_tmpl_id', '=', product_template_id],
                    ['attribute_id', 'in', gold_product_attrs]
                ],
                ['attribute_id', 'value_ids']
            )
            
            if not attr_lines:
                return []
            
            result = []
            
            # Lấy thông tin product.attribute
            product_attrs = self.odoo.read('product.attribute', gold_product_attrs, [
                'name', 'display_name'
            ])
            product_attr_dict = {attr['id']: attr for attr in product_attrs}
            
            for line in attr_lines:
                attribute_id = line['attribute_id'][0]
                product_attr = product_attr_dict.get(attribute_id)
                
                if not product_attr:
                    continue
                
                # Lấy gold attribute ID từ mapping
                gold_attr_id = gold_mapping.get(product_attr['name'])
                if not gold_attr_id:
                    continue
                
                # Lấy thông tin chi tiết gold attribute
                gold_attr = self.odoo.read('gold.attribute.line', [gold_attr_id], [
                    'name', 'display_name', 'short_name', 'field_type', 'unit', 'category'
                ])
                
                if not gold_attr:
                    continue
                    
                gold_attr = gold_attr[0]
                
                # Lấy values được chọn
                if line.get('value_ids'):
                    values = self.odoo.read('product.attribute.value', line['value_ids'], [
                        'name', 'html_color'
                    ])
                    
                    for value in values:
                        result.append({
                            'attribute_id': gold_attr_id,
                            'attribute_name': gold_attr.get('display_name') or gold_attr.get('name', ''),
                            'attribute_short_name': gold_attr.get('short_name', ''),
                            'field_type': gold_attr.get('field_type', 'char'),
                            'unit': gold_attr.get('unit', ''),
                            'category': gold_attr.get('category', ''),
                            'value': value['name'],
                            'display_value': f"{value['name']} {gold_attr.get('unit', '')}".strip()
                        })
                else:
                    # Trường hợp không có value (có thể là custom value)
                    result.append({
                        'attribute_id': gold_attr_id,
                        'attribute_name': gold_attr.get('display_name') or gold_attr.get('name', ''),
                        'attribute_short_name': gold_attr.get('short_name', ''),
                        'field_type': gold_attr.get('field_type', 'char'),
                        'unit': gold_attr.get('unit', ''),
                        'category': gold_attr.get('category', ''),
                        'value': '',
                        'display_value': ''
                    })
            
            return result
            
        except Exception as e:
            print(f"Error getting product gold attributes: {e}")
            return []
    
    def set_product_gold_attribute_value(self, product_template_id: int, 
                                       gold_attribute_id: int, value: Any) -> bool:
        """Set giá trị gold attribute cho product template
        Sử dụng product.template.attribute.line và product.template.attribute.value
        """
        try:
            # Lấy hoặc tạo product.attribute tương ứng
            product_attr_id = self._get_or_create_product_attribute(gold_attribute_id)
            if not product_attr_id:
                return False
            
            # Tạo hoặc tìm product.attribute.value
            value_name = str(value)
            existing_value = self.odoo.search('product.attribute.value', [
                ['attribute_id', '=', product_attr_id],
                ['name', '=', value_name]
            ])
            
            if existing_value:
                attr_value_id = existing_value[0]
            else:
                # Tạo attribute value mới
                attr_value_id = self.odoo.create('product.attribute.value', {
                    'name': value_name,
                    'attribute_id': product_attr_id,
                    'sequence': 10
                })
            
            # Tìm existing attribute line
            existing_line = self.odoo.search('product.template.attribute.line', [
                ['product_tmpl_id', '=', product_template_id],
                ['attribute_id', '=', product_attr_id]
            ])
            
            if existing_line:
                # Update existing line - thay thế value_ids (chỉ một giá trị cho mỗi gold attribute)
                self.odoo.write('product.template.attribute.line', existing_line, {
                    'value_ids': [(6, 0, [attr_value_id])]
                })
            else:
                # Tạo line mới
                self.odoo.create('product.template.attribute.line', {
                    'product_tmpl_id': product_template_id,
                    'attribute_id': product_attr_id,
                    'value_ids': [(6, 0, [attr_value_id])]
                })
            
            return True
                
        except Exception as e:
            print(f"Error setting gold attribute value: {e}")
            return False
    
    def bulk_set_product_gold_attributes(self, product_template_id: int, 
                                       attributes_values: Dict[int, Any]) -> bool:
        """Set nhiều gold attribute values cho product template"""
        try:
            success_count = 0
            for gold_attribute_id, value in attributes_values.items():
                if self.set_product_gold_attribute_value(product_template_id, gold_attribute_id, value):
                    success_count += 1
            
            return success_count == len(attributes_values)
        except Exception as e:
            print(f"Error in bulk set: {e}")
            return False
    
    def delete_product_gold_attribute_value(self, product_template_id: int, 
                                          gold_attribute_id: int) -> bool:
        """Xóa giá trị gold attribute của product template"""
        try:
            # Tìm gold attribute để lấy tên
            gold_attr = self.odoo.read('gold.attribute.line', [gold_attribute_id], ['name'])
            if not gold_attr:
                return False
                
            attr_name = f"gold_{gold_attr[0]['name']}"
            
            # Tìm product.attribute tương ứng
            product_attr = self.odoo.search('product.attribute', [['name', '=', attr_name]])
            if not product_attr:
                return True  # Already deleted
            
            # Xóa product.template.attribute.line
            existing_lines = self.odoo.search('product.template.attribute.line', [
                ['product_tmpl_id', '=', product_template_id],
                ['attribute_id', '=', product_attr[0]]
            ])
            
            if existing_lines:
                return self.odoo.unlink('product.template.attribute.line', existing_lines)
            
            return True
            
        except Exception as e:
            print(f"Error deleting gold attribute value: {e}")
            return False
    
    def clear_all_product_gold_attributes(self, product_template_id: int) -> bool:
        """Xóa tất cả gold attribute values của product template"""
        try:
            # Lấy tất cả gold attributes
            gold_attrs = self.odoo.search_read('gold.attribute.line', [], ['name'])
            
            # Tìm tất cả product.template.attribute.line có liên quan đến gold attributes
            gold_attr_names = [f"gold_{attr['name']}" for attr in gold_attrs]
            
            if not gold_attr_names:
                return True
                
            product_attrs = self.odoo.search('product.attribute', [['name', 'in', gold_attr_names]])
            if not product_attrs:
                return True
                
            # Xóa các attribute lines
            existing_lines = self.odoo.search('product.template.attribute.line', [
                ['product_tmpl_id', '=', product_template_id],
                ['attribute_id', 'in', product_attrs]
            ])
            
            if existing_lines:
                return self.odoo.unlink('product.template.attribute.line', existing_lines)
            
            return True
            
        except Exception as e:
            print(f"Error clearing gold attributes: {e}")
            return False
    
    # ================================
    # STATISTICS & UTILITIES
    # ================================
    
    def get_gold_attribute_statistics(self) -> Dict:
        """Lấy thống kê về gold attributes"""
        stats = {}
        
        # Thống kê nhóm thuộc tính
        total_groups = self.odoo.search_count('product.template.attribute.group', [])
        stats['total_groups'] = total_groups
        
        # Thống kê thuộc tính
        total_attributes = self.odoo.search_count('gold.attribute.line', [])
        active_attributes = self.odoo.search_count('gold.attribute.line', [['active', '=', True]])
        stats['total_attributes'] = total_attributes
        stats['active_attributes'] = active_attributes
        stats['inactive_attributes'] = total_attributes - active_attributes
        
        # Thống kê theo field_type
        field_types = ['char', 'float', 'integer', 'boolean', 'date', 'selection']
        by_type = {}
        for field_type in field_types:
            count = self.odoo.search_count('gold.attribute.line', [['field_type', '=', field_type]])
            if count > 0:
                by_type[field_type] = count
        stats['by_field_type'] = by_type
        
        # Thống kê theo category
        categories = ['technical', 'display', 'document']
        by_category = {}
        for category in categories:
            count = self.odoo.search_count('gold.attribute.line', [['category', '=', category]])
            if count > 0:
                by_category[category] = count
        stats['by_category'] = by_category
        
        # Thống kê theo nhóm
        groups = self.odoo.search_read('product.template.attribute.group', [], ['name'])
        by_group = {}
        for group in groups:
            count = self.odoo.search_count('gold.attribute.line', [['group_id', '=', group['id']]])
            if count > 0:
                by_group[group['name']] = count
        stats['by_group'] = by_group
        
        # Thống kê sản phẩm có gold attributes
        # Đếm số product có attribute lines liên quan đến gold attributes
        gold_attrs = self.odoo.search_read('gold.attribute.line', [], ['name'])
        gold_attr_names = [f"gold_{attr['name']}" for attr in gold_attrs]
        
        products_with_gold = 0
        if gold_attr_names:
            product_attrs = self.odoo.search('product.attribute', [['name', 'in', gold_attr_names]])
            if product_attrs:
                # Đếm product templates có attribute lines với gold attributes
                product_lines = self.odoo.search_read(
                    'product.template.attribute.line',
                    [['attribute_id', 'in', product_attrs]],
                    ['product_tmpl_id']
                )
                # Lấy unique product template IDs
                unique_product_ids = set(line['product_tmpl_id'][0] for line in product_lines)
                products_with_gold = len(unique_product_ids)
        
        total_products = self.odoo.search_count('product.template', [])
        stats['products_with_gold_attributes'] = products_with_gold
        stats['products_without_gold_attributes'] = total_products - products_with_gold
        stats['total_products'] = total_products
        
        # Thống kê tổng số gold attribute values (số attribute lines)
        total_values = 0
        if gold_attr_names:
            product_attrs = self.odoo.search('product.attribute', [['name', 'in', gold_attr_names]])
            if product_attrs:
                total_values = self.odoo.search_count('product.template.attribute.line', [
                    ['attribute_id', 'in', product_attrs]
                ])
        stats['total_attribute_values'] = total_values
        
        return stats
    
    def get_field_type_options(self) -> List[Dict]:
        """Lấy danh sách field type options"""
        return [
            {'value': 'char', 'label': 'Văn bản'},
            {'value': 'float', 'label': 'Số thập phân'},
            {'value': 'integer', 'label': 'Số nguyên'},
            {'value': 'boolean', 'label': 'Đúng/Sai'},
            {'value': 'date', 'label': 'Ngày'},
            {'value': 'selection', 'label': 'Lựa chọn'},
        ]
    
    def get_category_options(self) -> List[Dict]:
        """Lấy danh sách category options"""
        return [
            {'value': 'technical', 'label': 'Kỹ thuật'},
            {'value': 'display', 'label': 'Hiển thị'},
            {'value': 'document', 'label': 'Tài liệu'},
        ]

# Khởi tạo service instance
gold_attribute_service = OdooGoldAttributeService()
