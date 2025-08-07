// Cấu hình kết nối Odoo
module.exports = {
    url: 'http://localhost:8069',  // Thay đổi URL theo server Odoo của bạn
    db: 'your_database_name',      // Tên database Odoo
    username: 'admin',             // Username Odoo
    password: 'admin',             // Password Odoo
    
    // Các endpoint XML-RPC
    endpoints: {
        common: '/xmlrpc/2/common',
        object: '/xmlrpc/2/object'
    }
};
