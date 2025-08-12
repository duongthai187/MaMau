import xmlrpc.client
from .config import ODOO_CONFIG

class OdooClient:
    def __init__(self):
        self.url = ODOO_CONFIG['url']
        self.db = ODOO_CONFIG['db']
        self.username = ODOO_CONFIG['username']
        self.password = ODOO_CONFIG['password']
        self.uid = None
        self.models = None
        
    def connect(self):
        """Kết nối và xác thực với Odoo server"""
        try:
            print(f"Đang kết nối tới {self.url}...")
            
            # Kết nối đến common endpoint
            common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
            
            # Test kết nối trước
            version = common.version()
            print(f"Kết nối thành công! Odoo version: {version}")
            
            # Xác thực và lấy user ID
            self.uid = common.authenticate(self.db, self.username, self.password, {})
            
            if self.uid:
                # Kết nối đến object endpoint
                self.models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
                print(f"Xác thực thành công! User ID: {self.uid}")
                return True
            else:
                print("Xác thực thất bại! Kiểm tra lại username/password hoặc database.")
                return False
                
        except ConnectionError as e:
            print(f"Lỗi kết nối mạng: {e}")
            return False
        except Exception as e:
            print(f"Lỗi kết nối: {e}")
            print("Hướng dẫn kiểm tra:")
            print("1. Kiểm tra URL server có đúng không")
            print("2. Kiểm tra tên database có tồn tại không")
            print("3. Kiểm tra username/password có đúng không")
            print("4. Kiểm tra kết nối internet")
            return False
    
    def search_read(self, model, domain=[], fields=[], limit=None, offset=0, order=None):
        """Tìm kiếm và đọc records"""
        try:
            if not self.models or not self.uid:
                if not self.connect():
                    return []
                
            kwargs = {
                'fields': fields if fields else []
            }
            
            # Thêm offset nếu được chỉ định
            if offset and offset > 0:
                kwargs['offset'] = offset
            
            # Chỉ thêm limit nếu được chỉ định
            if limit is not None:
                kwargs['limit'] = limit
            
            # Thêm order nếu được chỉ định
            if order:
                kwargs['order'] = order
            
            records = self.models.execute_kw(
                self.db, self.uid, self.password,
                model, 'search_read',
                [domain], kwargs
            )
            return records
            
        except Exception as e:
            print(f"Lỗi search_read: {e}")
            # Thử kết nối lại
            if self.connect():
                try:
                    records = self.models.execute_kw(
                        self.db, self.uid, self.password,
                        model, 'search_read',
                        [domain], kwargs
                    )
                    return records
                except Exception as e2:
                    print(f"Lỗi search_read sau khi kết nối lại: {e2}")
            return []
    
    def search_count(self, model, domain):
        """Đếm số lượng records"""
        try:
            if not self.models or not self.uid:
                if not self.connect():
                    return 0
                
            count = self.models.execute_kw(
                self.db, self.uid, self.password,
                model, 'search_count',
                [domain]
            )
            return count
            
        except Exception as e:
            print(f"Lỗi search_count: {e}")
            # Thử kết nối lại
            if self.connect():
                try:
                    count = self.models.execute_kw(
                        self.db, self.uid, self.password,
                        model, 'search_count',
                        [domain]
                    )
                    return count
                except Exception as e2:
                    print(f"Lỗi search_count sau khi kết nối lại: {e2}")
            return 0
    
    def search(self, model, domain, offset=0, limit=None, order=None):
        """Tìm kiếm records và trả về list IDs"""
        try:
            if not self.models or not self.uid:
                if not self.connect():
                    return []
                
            kwargs = {}
            
            # Thêm offset nếu được chỉ định
            if offset and offset > 0:
                kwargs['offset'] = offset
            
            # Chỉ thêm limit nếu được chỉ định
            if limit is not None:
                kwargs['limit'] = limit
            
            # Thêm order nếu được chỉ định
            if order:
                kwargs['order'] = order
            
            ids = self.models.execute_kw(
                self.db, self.uid, self.password,
                model, 'search',
                [domain], kwargs
            )
            return ids
            
        except Exception as e:
            print(f"Lỗi search: {e}")
            # Thử kết nối lại
            if self.connect():
                try:
                    ids = self.models.execute_kw(
                        self.db, self.uid, self.password,
                        model, 'search',
                        [domain], kwargs
                    )
                    return ids
                except Exception as e2:
                    print(f"Lỗi search sau khi kết nối lại: {e2}")
            return []
    
    def read(self, model, record_ids, fields=None):
        """Đọc records theo IDs"""
        try:
            if not self.models or not self.uid:
                if not self.connect():
                    return []
                
            records = self.models.execute_kw(
                self.db, self.uid, self.password,
                model, 'read',
                [record_ids], {'fields': fields if fields else []}
            )
            return records
            
        except Exception as e:
            print(f"Lỗi read: {e}")
            # Thử kết nối lại
            if self.connect():
                try:
                    records = self.models.execute_kw(
                        self.db, self.uid, self.password,
                        model, 'read',
                        [record_ids], {'fields': fields if fields else []}
                    )
                    return records
                except Exception as e2:
                    print(f"Lỗi read sau khi kết nối lại: {e2}")
            return []
    
    def create(self, model, values):
        """Tạo record mới"""
        try:
            if not self.models:
                self.connect()
                
            record_id = self.models.execute_kw(
                self.db, self.uid, self.password,
                model, 'create',
                [values]
            )
            return record_id
            
        except Exception as e:
            print(f"Lỗi create: {e}")
            return False
    
    def write(self, model, record_ids, values):
        """Cập nhật record(s)"""
        try:
            if not self.models:
                self.connect()
            
            # Đảm bảo record_ids là list
            if not isinstance(record_ids, list):
                record_ids = [record_ids]
                
            success = self.models.execute_kw(
                self.db, self.uid, self.password,
                model, 'write',
                [record_ids, values]
            )
            return success
            
        except Exception as e:
            print(f"Lỗi write: {e}")
            return False
    
    def unlink(self, model, record_ids):
        """Xóa record(s)"""
        try:
            if not self.models:
                self.connect()
            
            # Đảm bảo record_ids là list
            if not isinstance(record_ids, list):
                record_ids = [record_ids]
                
            success = self.models.execute_kw(
                self.db, self.uid, self.password,
                model, 'unlink',
                [record_ids]
            )
            return success
            
        except Exception as e:
            print(f"Lỗi unlink: {e}")
            return False
    
    def get_fields(self, model):
        """Lấy thông tin fields của model"""
        try:
            if not self.models:
                self.connect()
                
            fields = self.models.execute_kw(
                self.db, self.uid, self.password,
                model, 'fields_get',
                [], {'attributes': ['string', 'help', 'type', 'required']}
            )
            return fields
            
        except Exception as e:
            print(f"Lỗi get_fields: {e}")
            return {}

# Instance toàn cục
odoo_client = OdooClient()
