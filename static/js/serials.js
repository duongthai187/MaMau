// JavaScript cho quản lý Serial Numbers

let serials = [];
let products = [];
let isEditing = false;

// Load dữ liệu khi trang được tải
document.addEventListener('DOMContentLoaded', function() {
    loadSerials();
    loadProducts();
    
    // Xử lý form submit
    document.getElementById('serialFormData').addEventListener('submit', function(e) {
        e.preventDefault();
        saveSerial();
    });
});

// Hiển thị form tạo mới
function showCreateForm() {
    isEditing = false;
    document.getElementById('formTitle').textContent = 'Tạo Serial Number Mới';
    document.getElementById('serialForm').style.display = 'block';
    document.getElementById('serialFormData').reset();
    document.getElementById('serialId').value = '';
}

// Ẩn form
function hideForm() {
    document.getElementById('serialForm').style.display = 'none';
    document.getElementById('serialFormData').reset();
}

// Hiển thị form chỉnh sửa
function editSerial(id) {
    isEditing = true;
    const serial = serials.find(s => s.id === id);
    
    if (serial) {
        document.getElementById('formTitle').textContent = 'Chỉnh sửa Serial Number';
        document.getElementById('serialForm').style.display = 'block';
        document.getElementById('serialId').value = serial.id;
        document.getElementById('serialName').value = serial.name;
        document.getElementById('serialProduct').value = serial.product_id[0];
        document.getElementById('serialRef').value = serial.ref || '';
    }
}

// Load danh sách serials
async function loadSerials() {
    try {
        showLoading(true);
        const response = await fetch('/api/serials');
        const data = await response.json();
        
        if (data.success) {
            serials = data.data;
            renderSerialsTable();
        } else {
            showAlert('Lỗi khi tải dữ liệu: ' + data.error, 'danger');
        }
    } catch (error) {
        showAlert('Lỗi kết nối: ' + error.message, 'danger');
    } finally {
        showLoading(false);
    }
}

// Load products cho dropdown
async function loadProducts() {
    try {
        const response = await fetch('/api/products');
        const data = await response.json();
        
        if (data.success) {
            products = data.data;
            renderProductOptions();
        }
    } catch (error) {
        console.error('Lỗi khi load products:', error);
    }
}

// Render options cho product dropdown
function renderProductOptions() {
    const select = document.getElementById('serialProduct');
    select.innerHTML = '<option value="">-- Chọn sản phẩm --</option>';
    
    products.forEach(product => {
        const option = document.createElement('option');
        option.value = product.id;
        option.textContent = product.name;
        select.appendChild(option);
    });
}

// Render bảng serials
function renderSerialsTable() {
    const tbody = document.getElementById('serialsTable');
    tbody.innerHTML = '';
    
    serials.forEach(serial => {
        const row = document.createElement('tr');
        
        const productName = serial.product_id ? serial.product_id[1] : '';
        const createDate = serial.create_date ? new Date(serial.create_date).toLocaleDateString('vi-VN') : '';
        
        row.innerHTML = `
            <td>${serial.id}</td>
            <td><strong>${serial.name}</strong></td>
            <td>${productName}</td>
            <td>${serial.ref || ''}</td>
            <td>${createDate}</td>
            <td>
                <button class="btn btn-sm btn-primary btn-action" onclick="editSerial(${serial.id})">Sửa</button>
                <button class="btn btn-sm btn-danger btn-action" onclick="deleteSerial(${serial.id})">Xóa</button>
            </td>
        `;
        
        tbody.appendChild(row);
    });
}

// Lưu serial (tạo mới hoặc cập nhật)
async function saveSerial() {
    try {
        const formData = {
            name: document.getElementById('serialName').value,
            product_id: parseInt(document.getElementById('serialProduct').value),
            ref: document.getElementById('serialRef').value
        };
        
        const serialId = document.getElementById('serialId').value;
        let url = '/api/serials';
        let method = 'POST';
        
        if (isEditing && serialId) {
            url += `/${serialId}`;
            method = 'PUT';
        }
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert(isEditing ? 'Cập nhật thành công!' : 'Tạo mới thành công!', 'success');
            hideForm();
            loadSerials();
        } else {
            showAlert('Lỗi khi lưu: ' + data.error, 'danger');
        }
    } catch (error) {
        showAlert('Lỗi kết nối: ' + error.message, 'danger');
    }
}

// Xóa serial
async function deleteSerial(id) {
    if (!confirm('Bạn có chắc chắn muốn xóa serial number này?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/serials/${id}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert('Xóa thành công!', 'success');
            loadSerials();
        } else {
            showAlert('Lỗi khi xóa: ' + data.error, 'danger');
        }
    } catch (error) {
        showAlert('Lỗi kết nối: ' + error.message, 'danger');
    }
}

// Hiển thị/ẩn loading
function showLoading(show) {
    document.getElementById('loading').style.display = show ? 'block' : 'none';
}

// Hiển thị alert
function showAlert(message, type) {
    // Xóa alert cũ nếu có
    const existingAlert = document.querySelector('.alert');
    if (existingAlert) {
        existingAlert.remove();
    }
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.querySelector('.container').insertBefore(alert, document.querySelector('.container').firstChild);
    
    // Tự động ẩn sau 5 giây
    setTimeout(() => {
        if (alert.parentNode) {
            alert.remove();
        }
    }, 5000);
}
