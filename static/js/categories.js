// JavaScript cho quản lý Categories

let categories = [];
let isEditing = false;

// Load dữ liệu khi trang được tải
document.addEventListener('DOMContentLoaded', function() {
    loadCategories();
    
    // Xử lý form submit
    document.getElementById('categoryFormData').addEventListener('submit', function(e) {
        e.preventDefault();
        saveCategory();
    });
});

// Hiển thị form tạo mới
function showCreateForm() {
    isEditing = false;
    document.getElementById('formTitle').textContent = 'Tạo Category Mới';
    document.getElementById('categoryForm').style.display = 'block';
    document.getElementById('categoryFormData').reset();
    document.getElementById('categoryId').value = '';
    
    // Load categories cho dropdown parent
    loadParentCategories();
}

// Ẩn form
function hideForm() {
    document.getElementById('categoryForm').style.display = 'none';
    document.getElementById('categoryFormData').reset();
}

// Hiển thị form chỉnh sửa
function editCategory(id) {
    isEditing = true;
    const category = categories.find(c => c.id === id);
    
    if (category) {
        document.getElementById('formTitle').textContent = 'Chỉnh sửa Category';
        document.getElementById('categoryForm').style.display = 'block';
        document.getElementById('categoryId').value = category.id;
        document.getElementById('categoryName').value = category.name;
        
        loadParentCategories(() => {
            const parentId = category.parent_id ? category.parent_id[0] : '';
            document.getElementById('parentCategory').value = parentId;
        });
    }
}

// Load danh sách categories
async function loadCategories() {
    try {
        showLoading(true);
        const response = await fetch('/api/categories');
        const data = await response.json();
        
        if (data.success) {
            categories = data.data;
            renderCategoriesTable();
        } else {
            showAlert('Lỗi khi tải dữ liệu: ' + data.error, 'danger');
        }
    } catch (error) {
        showAlert('Lỗi kết nối: ' + error.message, 'danger');
    } finally {
        showLoading(false);
    }
}

// Load categories cho dropdown parent
function loadParentCategories(callback) {
    const select = document.getElementById('parentCategory');
    select.innerHTML = '<option value="">-- Không có category cha --</option>';
    
    categories.forEach(category => {
        const option = document.createElement('option');
        option.value = category.id;
        option.textContent = category.name;
        select.appendChild(option);
    });
    
    if (callback) callback();
}

// Render bảng categories
function renderCategoriesTable() {
    const tbody = document.getElementById('categoriesTable');
    tbody.innerHTML = '';
    
    categories.forEach(category => {
        const row = document.createElement('tr');
        
        const parentName = category.parent_id ? category.parent_id[1] : '';
        
        row.innerHTML = `
            <td>${category.id}</td>
            <td>${category.name}</td>
            <td>${parentName}</td>
            <td>
                <button class="btn btn-sm btn-primary btn-action" onclick="editCategory(${category.id})">Sửa</button>
                <button class="btn btn-sm btn-danger btn-action" onclick="deleteCategory(${category.id})">Xóa</button>
            </td>
        `;
        
        tbody.appendChild(row);
    });
}

// Lưu category (tạo mới hoặc cập nhật)
async function saveCategory() {
    try {
        const formData = {
            name: document.getElementById('categoryName').value,
            parent_id: document.getElementById('parentCategory').value || null
        };
        
        const categoryId = document.getElementById('categoryId').value;
        let url = '/api/categories';
        let method = 'POST';
        
        if (isEditing && categoryId) {
            url += `/${categoryId}`;
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
            loadCategories();
        } else {
            showAlert('Lỗi khi lưu: ' + data.error, 'danger');
        }
    } catch (error) {
        showAlert('Lỗi kết nối: ' + error.message, 'danger');
    }
}

// Xóa category
async function deleteCategory(id) {
    if (!confirm('Bạn có chắc chắn muốn xóa category này?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/categories/${id}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert('Xóa thành công!', 'success');
            loadCategories();
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
