// Quản lý Attribute Values
let currentValueId = null;
let attributes = [];

// Load data khi trang tải
document.addEventListener('DOMContentLoaded', function() {
    loadAttributes();
    loadValues();
});

// Load danh sách attributes
async function loadAttributes() {
    try {
        const response = await fetch('/api/attributes');
        const result = await response.json();
        
        if (result.success) {
            attributes = result.data;
            updateAttributeSelect();
        }
    } catch (error) {
        console.error('Lỗi load attributes:', error);
    }
}

// Update attribute select options
function updateAttributeSelect() {
    const select = document.getElementById('attributeId');
    select.innerHTML = '<option value="">Chọn attribute...</option>';
    
    attributes.forEach(attr => {
        const option = document.createElement('option');
        option.value = attr.id;
        option.textContent = attr.name;
        select.appendChild(option);
    });
}

// Load danh sách values
async function loadValues() {
    try {
        const response = await fetch('/api/values');
        const result = await response.json();
        
        if (result.success) {
            updateValuesTable(result.data);
        }
    } catch (error) {
        console.error('Lỗi load values:', error);
        alert('Không thể tải danh sách values');
    }
}

// Update bảng values
function updateValuesTable(values) {
    const tbody = document.getElementById('valuesTable');
    tbody.innerHTML = '';
    
    values.forEach(value => {
        const attributeName = getAttributeName(value.attribute_id);
        
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${value.id}</td>
            <td>${value.name}</td>
            <td>${attributeName}</td>
            <td>
                <button class="btn btn-sm btn-outline-primary me-1" onclick="editValue(${value.id})">
                    Sửa
                </button>
                <button class="btn btn-sm btn-outline-danger" onclick="deleteValue(${value.id})">
                    Xóa
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// Lấy tên attribute từ ID
function getAttributeName(attributeId) {
    if (Array.isArray(attributeId)) {
        attributeId = attributeId[0];
    }
    
    const attr = attributes.find(a => a.id === attributeId);
    return attr ? attr.name : 'N/A';
}

// Xử lý form submit
document.getElementById('valueForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const id = document.getElementById('valueId').value;
    const name = document.getElementById('valueName').value;
    const attributeId = parseInt(document.getElementById('attributeId').value);
    
    if (!name.trim() || !attributeId) {
        alert('Vui lòng điền đầy đủ thông tin');
        return;
    }
    
    const valueData = {
        name: name.trim(),
        attribute_id: attributeId
    };
    
    try {
        let response;
        if (id) {
            // Cập nhật
            response = await fetch(`/api/values/${id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(valueData)
            });
        } else {
            // Tạo mới
            response = await fetch('/api/values', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(valueData)
            });
        }
        
        const result = await response.json();
        
        if (result.success) {
            alert(id ? 'Cập nhật value thành công!' : 'Tạo value thành công!');
            closeModal();
            loadValues();
        } else {
            alert('Có lỗi xảy ra: ' + (result.message || 'Unknown error'));
        }
    } catch (error) {
        console.error('Lỗi:', error);
        alert('Có lỗi xảy ra khi lưu value');
    }
});

// Sửa value
async function editValue(id) {
    try {
        // Tìm value trong danh sách hiện tại
        const response = await fetch('/api/values');
        const result = await response.json();
        
        if (result.success) {
            const value = result.data.find(v => v.id === id);
            if (value) {
                currentValueId = id;
                document.getElementById('valueId').value = id;
                document.getElementById('valueName').value = value.name;
                
                // Set attribute
                let attributeId = value.attribute_id;
                if (Array.isArray(attributeId)) {
                    attributeId = attributeId[0];
                }
                document.getElementById('attributeId').value = attributeId;
                
                document.getElementById('modalTitle').textContent = 'Sửa Attribute Value';
                new bootstrap.Modal(document.getElementById('valueModal')).show();
            }
        }
    } catch (error) {
        console.error('Lỗi load value:', error);
        alert('Không thể tải thông tin value');
    }
}

// Xóa value
async function deleteValue(id) {
    if (!confirm('Bạn có chắc chắn muốn xóa value này?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/values/${id}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('Xóa value thành công!');
            loadValues();
        } else {
            alert('Có lỗi xảy ra khi xóa value');
        }
    } catch (error) {
        console.error('Lỗi xóa value:', error);
        alert('Có lỗi xảy ra khi xóa value');
    }
}

// Đóng modal và reset form
function closeModal() {
    const modal = bootstrap.Modal.getInstance(document.getElementById('valueModal'));
    if (modal) {
        modal.hide();
    }
    resetForm();
}

// Reset form
function resetForm() {
    currentValueId = null;
    document.getElementById('valueForm').reset();
    document.getElementById('valueId').value = '';
    document.getElementById('modalTitle').textContent = 'Thêm Attribute Value';
}

// Event listener cho modal
document.getElementById('valueModal').addEventListener('hidden.bs.modal', resetForm);
