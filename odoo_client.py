"""
Odoo XML-RPC Client
Kết nối và tương tác với Odoo server thông qua XML-RPC API
"""
import xmlrpc.client
import ssl
from datetime import datetime
from typing import List, Dict, Any, Optional, Union

class OdooClient:
    """Client để kết nối với Odoo server"""
    
    def __init__(self, url=None, db=None, username=None, password=None):
        # Default config - có thể override từ config.py
        self.url = url or "http://localhost:8069"
        self.db = db or "odoo_db"
        self.username = username or "admin"
        self.password = password or "admin"
        
        self.uid = None
        self.common = None
        self.models = None
        self.connected = False
        
        # SSL context for HTTPS connections - lazy initialization
        self._ssl_context = None
    
    @property
    def ssl_context(self):
        """Lazy initialization of SSL context"""
        if self._ssl_context is None:
            self._ssl_context = ssl.create_default_context()
            # For development/testing with self-signed certificates
            self._ssl_context.check_hostname = False
            self._ssl_context.verify_mode = ssl.CERT_NONE
        return self._ssl_context
    
    def _create_server_proxy(self, endpoint):
        """Tạo ServerProxy với SSL context phù hợp"""
        url = f'{self.url}/xmlrpc/2/{endpoint}'
        
        if self.url.startswith('https://'):
            # HTTPS connection with SSL context
            return xmlrpc.client.ServerProxy(url, context=self.ssl_context)
        else:
            # HTTP connection
            return xmlrpc.client.ServerProxy(url)
    
    def connect(self):
        """Kết nối tới Odoo server"""
        try:
            print(f"🔌 Connecting to Odoo: {self.url}")
            print(f"📊 Database: {self.db}")
            print(f"👤 Username: {self.username}")
            
            # Connect to common endpoint
            self.common = self._create_server_proxy('common')
            
            # Test connection and get version
            print("🧪 Testing connection...")
            version_info = self.common.version()
            print(f"✅ Connected to Odoo {version_info.get('server_version', 'Unknown')}")
            
            # Authenticate
            print("🔐 Authenticating...")
            self.uid = self.common.authenticate(self.db, self.username, self.password, {})
            
            if not self.uid:
                raise Exception("Authentication failed - Check username/password")
            
            # Connect to object endpoint
            self.models = self._create_server_proxy('object')
            
            self.connected = True
            print(f"✅ Authenticated as user ID: {self.uid}")
            
            # Test a simple operation
            try:
                self.models.execute_kw(
                    self.db, self.uid, self.password,
                    'res.users', 'check_access_rights',
                    ['read'], {'raise_exception': False}
                )
                print("✅ Basic operations test successful")
            except Exception as e:
                print(f"⚠️ Basic operations test failed: {e}")
            
            return True
            
        except Exception as e:
            print(f"❌ Odoo connection failed: {e}")
            self.connected = False
            
            # Thêm troubleshooting tips
            if "10061" in str(e):
                print("💡 Tips: Check if Odoo server is running and accessible")
            elif "SSL" in str(e) or "certificate" in str(e):
                print("💡 Tips: SSL/Certificate issue - check HTTPS configuration")
            elif "authentication" in str(e).lower():
                print("💡 Tips: Check username, password, and database name")
            elif "unsupported" in str(e):
                print("💡 Tips: Check Odoo URL format (http/https)")
                
            raise e
    
    def version(self):
        """Lấy thông tin version của Odoo"""
        if not self.common:
            self.connect()
        return self.common.version()
    
    def check_access_rights(self, model_name: str, operation: str = 'read') -> bool:
        """Kiểm tra quyền truy cập model"""
        if not self.connected:
            self.connect()
            
        try:
            return self.models.execute_kw(
                self.db, self.uid, self.password,
                model_name, 'check_access_rights',
                [operation], {'raise_exception': False}
            )
        except Exception:
            return False
    
    def search(self, model_name: str, domain: List = None, offset: int = 0, 
               limit: Optional[int] = None, order: str = 'id', count: bool = False) -> Union[List[int], int]:
        """Tìm kiếm records"""
        if not self.connected:
            self.connect()
            
        if domain is None:
            domain = []
        
        kwargs = {'offset': offset, 'order': order}
        if limit is not None:
            kwargs['limit'] = limit
        if count:
            kwargs['count'] = True
            
        return self.models.execute_kw(
            self.db, self.uid, self.password,
            model_name, 'search',
            [domain], kwargs
        )
    
    def search_count(self, model_name: str, domain: List = None) -> int:
        """Đếm số records"""
        if not self.connected:
            self.connect()
            
        if domain is None:
            domain = []
            
        return self.models.execute_kw(
            self.db, self.uid, self.password,
            model_name, 'search_count',
            [domain]
        )
    
    def read(self, model_name: str, ids: List[int], fields: List[str] = None) -> List[Dict]:
        """Đọc dữ liệu records"""
        if not self.connected:
            self.connect()
            
        if not ids:
            return []
            
        kwargs = {}
        if fields:
            kwargs['fields'] = fields
            
        return self.models.execute_kw(
            self.db, self.uid, self.password,
            model_name, 'read',
            [ids], kwargs
        )
    
    def search_read(self, model_name: str, domain: List = None, fields: List[str] = None,
                    offset: int = 0, limit: Optional[int] = None, order: str = 'id') -> List[Dict]:
        """Tìm kiếm và đọc dữ liệu trong một lần call"""
        if not self.connected:
            self.connect()
            
        if domain is None:
            domain = []
            
        kwargs = {'offset': offset, 'order': order}
        if fields:
            kwargs['fields'] = fields
        if limit is not None:
            kwargs['limit'] = limit
            
        return self.models.execute_kw(
            self.db, self.uid, self.password,
            model_name, 'search_read',
            [domain], kwargs
        )
    
    def create(self, model_name: str, values: Dict) -> int:
        """Tạo record mới"""
        if not self.connected:
            self.connect()
            
        return self.models.execute_kw(
            self.db, self.uid, self.password,
            model_name, 'create',
            [values]
        )
    
    def write(self, model_name: str, ids: List[int], values: Dict) -> bool:
        """Cập nhật records"""
        if not self.connected:
            self.connect()
            
        return self.models.execute_kw(
            self.db, self.uid, self.password,
            model_name, 'write',
            [ids, values]
        )
    
    def unlink(self, model_name: str, ids: List[int]) -> bool:
        """Xóa records"""
        if not self.connected:
            self.connect()
            
        return self.models.execute_kw(
            self.db, self.uid, self.password,
            model_name, 'unlink',
            [ids]
        )
    
    def call_method(self, model_name: str, method_name: str, args: List = None, kwargs: Dict = None):
        """Gọi method custom của model"""
        if not self.connected:
            self.connect()
            
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}
            
        return self.models.execute_kw(
            self.db, self.uid, self.password,
            model_name, method_name,
            args, kwargs
        )
    
    def get_fields(self, model_name: str, attributes: List[str] = None) -> Dict:
        """Lấy thông tin fields của model"""
        if not self.connected:
            self.connect()
            
        kwargs = {}
        if attributes:
            kwargs['attributes'] = attributes
            
        return self.models.execute_kw(
            self.db, self.uid, self.password,
            model_name, 'fields_get',
            [], kwargs
        )
    
    def execute_sql(self, query: str, params: tuple = None):
        """Execute raw SQL query (chỉ dùng khi cần thiết)"""
        # Note: XML-RPC không hỗ trợ trực tiếp SQL queries
        # Cần implement server-side method nếu cần
        raise NotImplementedError("Raw SQL execution not supported via XML-RPC")

# Global instance
odoo_client = OdooClient()