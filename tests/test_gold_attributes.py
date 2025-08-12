"""
Test script để kiểm tra tích hợp gold_attribute_line module
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from gold_attribute_odoo_integration import gold_attribute_service
from pprint import pprint

def test_attribute_groups():
    """Test CRUD cho attribute groups"""
    print("=== TEST ATTRIBUTE GROUPS ===")
    
    # 1. Lấy danh sách nhóm thuộc tính
    print("\n1. Lấy danh sách nhóm thuộc tính:")
    groups, total = gold_attribute_service.get_attribute_groups()
    print(f"Tổng số nhóm: {total}")
    for group in groups[:3]:  # Hiển thị 3 nhóm đầu
        print(f"  - {group['name']} (ID: {group['id']}, Attributes: {group['attribute_count']})")
    
    # 2. Tạo nhóm mới (test)
    print("\n2. Tạo nhóm thuộc tính mới (test):")
    try:
        test_group_data = {
            'name': 'Test Group - API Integration',
            'code': 'TEST_API',
            'sequence': 999
        }
        group_id = gold_attribute_service.create_attribute_group(test_group_data)
        print(f"  - Đã tạo nhóm ID: {group_id}")
        
        # 3. Lấy thông tin nhóm vừa tạo
        print("\n3. Lấy thông tin nhóm vừa tạo:")
        group_info = gold_attribute_service.get_attribute_group(group_id)
        if group_info:
            print(f"  - Tên: {group_info['name']}")
            print(f"  - Mã: {group_info['code']}")
            print(f"  - Số thuộc tính: {group_info['attribute_count']}")
        
        # 4. Xóa nhóm test
        print("\n4. Xóa nhóm test:")
        success = gold_attribute_service.delete_attribute_group(group_id)
        print(f"  - Kết quả xóa: {success}")
        
    except Exception as e:
        print(f"  - Lỗi: {e}")

def test_gold_attributes():
    """Test CRUD cho gold attributes"""
    print("\n=== TEST GOLD ATTRIBUTES ===")
    
    # 1. Lấy danh sách thuộc tính
    print("\n1. Lấy danh sách thuộc tính vàng:")
    attributes, total = gold_attribute_service.get_gold_attributes()
    print(f"Tổng số thuộc tính: {total}")
    for attr in attributes[:3]:  # Hiển thị 3 thuộc tính đầu
        print(f"  - {attr['name']} ({attr['field_type']}) - Nhóm: {attr.get('group_name', 'N/A')}")

def test_product_gold_attributes():
    """Test tích hợp với product templates"""
    print("\n=== TEST PRODUCT GOLD ATTRIBUTES ===")
    
    # Lấy một product template để test
    try:
        from odoo_client import odoo_client
        
        # Tìm product đầu tiên
        products = odoo_client.search_read('product.template', [], ['name'], limit=1)
        if not products:
            print("Không có product template nào để test")
            return
        
        product_id = products[0]['id']
        product_name = products[0]['name']
        print(f"\n1. Test với product: {product_name} (ID: {product_id})")
        
        # 2. Lấy gold attributes hiện tại
        print("\n2. Lấy gold attributes hiện tại:")
        current_attrs = gold_attribute_service.get_product_gold_attributes(product_id)
        print(f"  - Số attributes hiện tại: {len(current_attrs)}")
        for attr in current_attrs:
            print(f"    + {attr['attribute_name']}: {attr['display_value']}")
        
        # 3. Test set gold attribute (chỉ nếu có attributes)
        attributes, _ = gold_attribute_service.get_gold_attributes(limit=1)
        if attributes:
            attr_id = attributes[0]['id']
            attr_name = attributes[0]['name']
            attr_type = attributes[0]['field_type']
            
            print(f"\n3. Test set gold attribute:")
            print(f"  - Attribute: {attr_name} ({attr_type})")
            
            # Set giá trị tùy theo type
            if attr_type == 'char':
                test_value = "Test Value API"
            elif attr_type == 'float':
                test_value = 99.5
            elif attr_type == 'integer':
                test_value = 100
            elif attr_type == 'boolean':
                test_value = True
            else:
                test_value = "Test"
            
            success = gold_attribute_service.set_product_gold_attribute_value(product_id, attr_id, test_value)
            print(f"  - Kết quả set: {success}")
            
            # 4. Kiểm tra lại
            print("\n4. Kiểm tra lại sau khi set:")
            updated_attrs = gold_attribute_service.get_product_gold_attributes(product_id)
            for attr in updated_attrs:
                if attr['attribute_id'] == attr_id:
                    print(f"  - {attr['attribute_name']}: {attr['display_value']}")
                    break
    
    except Exception as e:
        print(f"Lỗi test product attributes: {e}")

def test_statistics():
    """Test thống kê"""
    print("\n=== TEST STATISTICS ===")
    
    try:
        stats = gold_attribute_service.get_gold_attribute_statistics()
        print("\nThống kê gold attributes:")
        print(f"- Tổng số nhóm: {stats.get('total_groups', 0)}")
        print(f"- Tổng số thuộc tính: {stats.get('total_attributes', 0)}")
        print(f"- Thuộc tính active: {stats.get('active_attributes', 0)}")
        print(f"- Sản phẩm có gold attributes: {stats.get('products_with_gold_attributes', 0)}")
        print(f"- Tổng số values: {stats.get('total_attribute_values', 0)}")
        
        print(f"\nThống kê theo field type:")
        for field_type, count in stats.get('by_field_type', {}).items():
            print(f"  - {field_type}: {count}")
            
    except Exception as e:
        print(f"Lỗi test statistics: {e}")

if __name__ == "__main__":
    print("KIỂM TRA TÍCH HỢP GOLD_ATTRIBUTE_LINE MODULE")
    print("=" * 50)
    
    try:
        test_attribute_groups()
        test_gold_attributes()
        test_product_gold_attributes()
        test_statistics()
        
        print("\n" + "=" * 50)
        print("✅ HOÀN THÀNH KIỂM TRA!")
        
    except Exception as e:
        print(f"\n❌ LỖI TỔNG QUÁT: {e}")
        import traceback
        traceback.print_exc()
