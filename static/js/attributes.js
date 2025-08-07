// JavaScript cho quản lý Attributes

let attributes = [];
let attributeValues = [];
let currentAttributeId = null;
let isEditingAttribute = false;
let isEditingValue = false;

// Load dữ liệu khi trang được tải
document.addEventListener('DOMContentLoaded', function() {
    loadAttributes();
    
    // Xử lý form submit cho attributes
    document.getElementById('attributeFormData').addEventListener('submit', function(e) {
        e.preventDefault();
        saveAttribute();
    });
    
    // Xử lý form submit cho values
    document.getElementById('valueFormData').addEventListener('submit', function(e) {
        e.preventDefault();
        saveAttributeValue();
    });
});

// ATTRIBUTES MANAGEMENT
function showCreateAttributeForm() {
    isEditingAttribute = false;
    document.getElementById('attributeForm').style.display = 'block';
    document.getElementById('attributeFormData').reset();
    document.getElementById('attributeId').value = '';
}

function hideAttributeForm() {
    document.getElementById('attributeForm').style.display = 'none';
}

function editAttribute(id) {
    isEditingAttribute = true;
    const attribute = attributes.find(a => a.id === id);
    
    if (attribute) {
        document.getElementById('attributeForm').style.display = 'block';
        document.getElementById('attributeId').value = attribute.id;
        document.getElementById('attributeName').value = attribute.name;
        document.getElementById('displayType').value = attribute.display_type || 'radio';
    }
}

async function loadAttributes() {
    try {
        const response = await fetch('/api/attributes');
        const data = await response.json();
        
        if (data.success) {
            attributes = data.data;
            renderAttributesTable();
        } else {
            showAlert('Lỗi khi tải attributes: ' + data.error, 'danger');
        }
    } catch (error) {
        showAlert('Lỗi kết nối: ' + error.message, 'danger');
    }
}

function renderAttributesTable() {
    const tbody = document.getElementById('attributesTable');
    tbody.innerHTML = '';
    
    attributes.forEach(attribute => {
        const row = document.createElement('tr');
        
        const displayTypeLabels = {
            'radio': 'Radio',
            'select': 'Select',
            'color': 'Color'
        };
        
        row.innerHTML = `
            <td>${attribute.id}</td>
            <td><a href="#" onclick="selectAttribute(${attribute.id})" class="text-decoration-none">${attribute.name}</a></td>
            <td>${displayTypeLabels[attribute.display_type] || attribute.display_type}</td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="editAttribute(${attribute.id})">Sửa</button>
                <button class="btn btn-sm btn-danger" onclick="deleteAttribute(${attribute.id})">Xóa</button>
            </td>
        `;
        
        tbody.appendChild(row);
    });
}

async function saveAttribute() {
    try {
        const formData = {
            name: document.getElementById('attributeName').value,
            display_type: document.getElementById('displayType').value,
            create_variant: 'always'
        };
        
        const attributeId = document.getElementById('attributeId').value;
        let url = '/api/attributes';
        let method = 'POST';
        
        if (isEditingAttribute && attributeId) {
            url += `/${attributeId}`;
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
            showAlert(isEditingAttribute ? 'Cập nhật thành công!' : 'Tạo mới thành công!', 'success');
            hideAttributeForm();
            loadAttributes();
        } else {
            showAlert('Lỗi khi lưu: ' + data.error, 'danger');
        }
    } catch (error) {
        showAlert('Lỗi kết nối: ' + error.message, 'danger');
    }
}

async function deleteAttribute(id) {
    if (!confirm('Bạn có chắc chắn muốn xóa attribute này?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/attributes/${id}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert('Xóa thành công!', 'success');
            loadAttributes();
            
            // Clear values section if this attribute was selected
            if (currentAttributeId === id) {
                clearValueSection();
            }
        } else {
            showAlert('Lỗi khi xóa: ' + data.error, 'danger');
        }
    } catch (error) {
        showAlert('Lỗi kết nối: ' + error.message, 'danger');
    }
}

// ATTRIBUTE VALUES MANAGEMENT
function selectAttribute(attributeId) {
    currentAttributeId = attributeId;
    document.getElementById('selectedAttributeId').value = attributeId;
    document.getElementById('createValueBtn').disabled = false;
    document.getElementById('noAttributeSelected').style.display = 'none';
    document.getElementById('valuesSection').style.display = 'block';
    
    loadAttributeValues(attributeId);
}

function clearValueSection() {
    currentAttributeId = null;
    document.getElementById('createValueBtn').disabled = true;
    document.getElementById('noAttributeSelected').style.display = 'block';
    document.getElementById('valuesSection').style.display = 'none';
    hideValueForm();
}

function showCreateValueForm() {
    if (!currentAttributeId) return;
    
    isEditingValue = false;
    document.getElementById('valueForm').style.display = 'block';
    document.getElementById('valueFormData').reset();
    document.getElementById('valueId').value = '';
    document.getElementById('selectedAttributeId').value = currentAttributeId;
    document.getElementById('valueSequence').value = '1';
}

function hideValueForm() {
    document.getElementById('valueForm').style.display = 'none';
}

function editAttributeValue(id) {
    isEditingValue = true;
    const value = attributeValues.find(v => v.id === id);
    
    if (value) {
        document.getElementById('valueForm').style.display = 'block';
        document.getElementById('valueId').value = value.id;
        document.getElementById('valueName').value = value.name;
        document.getElementById('valueSequence').value = value.sequence;
    }
}

async function loadAttributeValues(attributeId) {
    try {
        const response = await fetch(`/api/attribute-values?attribute_id=${attributeId}`);
        const data = await response.json();
        
        if (data.success) {
            attributeValues = data.data;
            renderValuesTable();
        } else {
            showAlert('Lỗi khi tải values: ' + data.error, 'danger');
        }
    } catch (error) {
        showAlert('Lỗi kết nối: ' + error.message, 'danger');
    }
}

function renderValuesTable() {
    const tbody = document.getElementById('valuesTable');
    tbody.innerHTML = '';
    
    attributeValues.forEach(value => {
        const row = document.createElement('tr');
        
        row.innerHTML = `
            <td>${value.id}</td>
            <td>${value.name}</td>
            <td>${value.sequence}</td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="editAttributeValue(${value.id})">Sửa</button>
                <button class="btn btn-sm btn-danger" onclick="deleteAttributeValue(${value.id})">Xóa</button>
            </td>
        `;
        
        tbody.appendChild(row);
    });
}

async function saveAttributeValue() {
    try {
        const formData = {
            name: document.getElementById('valueName').value,
            attribute_id: parseInt(document.getElementById('selectedAttributeId').value),
            sequence: parseInt(document.getElementById('valueSequence').value)
        };
        
        const valueId = document.getElementById('valueId').value;
        let url = '/api/attribute-values';
        let method = 'POST';
        
        if (isEditingValue && valueId) {
            url += `/${valueId}`;
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
            showAlert(isEditingValue ? 'Cập nhật thành công!' : 'Tạo mới thành công!', 'success');
            hideValueForm();
            loadAttributeValues(currentAttributeId);
        } else {
            showAlert('Lỗi khi lưu: ' + data.error, 'danger');
        }
    } catch (error) {
        showAlert('Lỗi kết nối: ' + error.message, 'danger');
    }
}

async function deleteAttributeValue(id) {
    if (!confirm('Bạn có chắc chắn muốn xóa value này?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/attribute-values/${id}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert('Xóa thành công!', 'success');
            loadAttributeValues(currentAttributeId);
        } else {
            showAlert('Lỗi khi xóa: ' + data.error, 'danger');
        }
    } catch (error) {
        showAlert('Lỗi kết nối: ' + error.message, 'danger');
    }
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
