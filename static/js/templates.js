// JavaScript cho quản lý Templates

let templates = [];
let categories = [];
let attributes = [];
let isEditing = false;
let templateAttributeCounter = 0;  // Counter cho template attributes

// Load dữ liệu khi trang được tải
document.addEventListener('DOMContentLoaded', function() {
    loadTemplates();
    loadCategories();
    loadAttributes();
    
    // Xử lý form submit
    document.getElementById('templateFormData').addEventListener('submit', function(e) {
        e.preventDefault();
        saveTemplate();
    });
});

// Thêm template attribute dropdown
function addTemplateAttribute() {
    templateAttributeCounter++;
    const container = document.getElementById('templateAttributeSelections');
    
    const div = document.createElement('div');
    div.className = 'col-md-6 mb-3 template-attribute-item';
    div.id = `template-attr-${templateAttributeCounter}`;
    
    div.innerHTML = `
        <div class="input-group">
            <select class="form-control template-attr-select" data-counter="${templateAttributeCounter}">
                <option value="">-- Chọn Attribute --</option>
                ${attributes.map(attr => `<option value="${attr.id}">${attr.name}</option>`).join('')}
            </select>
            <input type="text" class="form-control template-value-input" data-counter="${templateAttributeCounter}" 
                   placeholder="Nhập giá trị..." disabled>
            <button type="button" class="btn btn-outline-danger btn-sm" onclick="removeTemplateAttribute(${templateAttributeCounter})">
                ❌
            </button>
        </div>
        <small class="text-muted">Ví dụ: Cotton, Nike, 100% polyester...</small>
    `;
    
    container.appendChild(div);
    
    // Add event listener cho attribute select
    const attrSelect = div.querySelector('.template-attr-select');
    attrSelect.addEventListener('change', function() {
        const valueInput = div.querySelector('.template-value-input');
        if (this.value) {
            valueInput.disabled = false;
            valueInput.focus();
        } else {
            valueInput.disabled = true;
            valueInput.value = '';
        }
    });
}

// Xóa template attribute
function removeTemplateAttribute(counter) {
    const element = document.getElementById(`template-attr-${counter}`);
    if (element) {
        element.remove();
    }
}

// Load attributes cho dropdown
async function loadAttributes() {
    try {
        const response = await fetch('/api/attributes');
        const data = await response.json();
        
        if (data.success) {
            attributes = data.data;
            console.log('Loaded attributes:', attributes.length);
            renderAttributeOptions();
        }
    } catch (error) {
        console.error('Lỗi khi load attributes:', error);
    }
}

// Render options cho variant attributes dropdown
function renderAttributeOptions() {
    const variantSelect = document.getElementById('variantAttributes');
    console.log('Variant select element:', variantSelect);
    console.log('Attributes to render:', attributes.length);
    
    if (variantSelect) {
        variantSelect.innerHTML = '';
        
        attributes.forEach(attribute => {
            const option = document.createElement('option');
            option.value = attribute.id;
            option.textContent = attribute.name;
            variantSelect.appendChild(option);
        });
        console.log('Rendered options count:', variantSelect.children.length);
    } else {
        console.error('Element variantAttributes not found!');
    }
}

// Hiển thị form tạo mới
function showCreateForm() {
    isEditing = false;
    document.getElementById('formTitle').textContent = 'Tạo Template Mới';
    document.getElementById('templateForm').style.display = 'block';
    document.getElementById('templateFormData').reset();
    document.getElementById('templateId').value = '';
    
    // Reset giá trị mặc định
    document.getElementById('listPrice').value = '0';
    document.getElementById('standardPrice').value = '0';
    document.getElementById('productType').value = 'consu';
    
    // Reset template attributes
    document.getElementById('templateAttributeSelections').innerHTML = '';
    templateAttributeCounter = 0;
    
    // Reset variant attributes
    const variantSelect = document.getElementById('variantAttributes');
    if (variantSelect) {
        for (let option of variantSelect.options) {
            option.selected = false;
        }
    }
}

// Ẩn form
function hideForm() {
    document.getElementById('templateForm').style.display = 'none';
    document.getElementById('templateFormData').reset();
}

// Hiển thị form chỉnh sửa
function editTemplate(id) {
    isEditing = true;
    const template = templates.find(t => t.id === id);
    
    if (template) {
        document.getElementById('formTitle').textContent = 'Chỉnh sửa Template';
        document.getElementById('templateForm').style.display = 'block';
        document.getElementById('templateId').value = template.id;
        document.getElementById('templateName').value = template.name;
        document.getElementById('templateCategory').value = template.categ_id[0];
        document.getElementById('listPrice').value = template.list_price || 0;
        document.getElementById('standardPrice').value = template.standard_price || 0;
        document.getElementById('productType').value = template.type || 'consu';
        document.getElementById('defaultCode').value = template.default_code || '';
    }
}

// Load danh sách templates
async function loadTemplates() {
    try {
        console.log('Starting loadTemplates...');
        showLoading(true);
        const response = await fetch('/api/templates');
        console.log('Response received:', response);
        const data = await response.json();
        console.log('Data parsed:', data);
        
        if (data.success) {
            templates = data.data;
            console.log('Templates loaded:', templates.length);
            renderTemplatesTable();
        } else {
            console.error('API error:', data.error);
            showAlert('Lỗi khi tải dữ liệu: ' + data.error, 'danger');
        }
    } catch (error) {
        console.error('Load templates error:', error);
        showAlert('Lỗi kết nối: ' + error.message, 'danger');
    } finally {
        showLoading(false);
    }
}

// Load categories cho dropdown
async function loadCategories() {
    try {
        const response = await fetch('/api/categories');
        const data = await response.json();
        
        if (data.success) {
            categories = data.data;
            renderCategoryOptions();
        }
    } catch (error) {
        console.error('Lỗi khi load categories:', error);
    }
}

// Render options cho category dropdown
function renderCategoryOptions() {
    const select = document.getElementById('templateCategory');
    select.innerHTML = '<option value="">-- Chọn category --</option>';
    
    categories.forEach(category => {
        const option = document.createElement('option');
        option.value = category.id;
        option.textContent = category.name;
        select.appendChild(option);
    });
}

// Load attributes cho dropdown
async function loadAttributes() {
    try {
        const response = await fetch('/api/attributes');
        const data = await response.json();
        
        if (data.success) {
            attributes = data.data;
            renderAttributeOptions();
        }
    } catch (error) {
        console.error('Lỗi khi load attributes:', error);
    }
}

// Render bảng templates
function renderTemplatesTable() {
    const tbody = document.getElementById('templatesTable');
    tbody.innerHTML = '';
    
    templates.forEach(template => {
        const row = document.createElement('tr');
        
        const categoryName = template.categ_id ? template.categ_id[1] : '';
        const typeLabels = {
            'consu': 'Consumable',
            'service': 'Service', 
            'product': 'Storable Product'
        };
        
        row.innerHTML = `
            <td>${template.id}</td>
            <td>${template.name}</td>
            <td>${categoryName}</td>
            <td>${template.default_code || ''}</td>
            <td>${formatCurrency(template.list_price)}</td>
            <td>${formatCurrency(template.standard_price)}</td>
            <td>${typeLabels[template.type] || template.type}</td>
            <td>
                <button class="btn btn-sm btn-primary btn-action" onclick="editTemplate(${template.id})">Sửa</button>
                <button class="btn btn-sm btn-danger btn-action" onclick="deleteTemplate(${template.id})">Xóa</button>
            </td>
        `;
        
        tbody.appendChild(row);
    });
}

// Lưu template (tạo mới hoặc cập nhật)
async function saveTemplate() {
    try {
        // Lấy template attributes (cố định của template) - từ text input
        const templateAttributes = {};
        const templateAttrItems = document.querySelectorAll('.template-attribute-item');
        templateAttrItems.forEach(item => {
            const attrSelect = item.querySelector('.template-attr-select');
            const valueInput = item.querySelector('.template-value-input');
            
            if (attrSelect.value && valueInput.value.trim()) {
                templateAttributes[attrSelect.value] = valueInput.value.trim();
            }
        });
        
        // Lấy variant attributes (để tạo variants) - chỉ attribute IDs
        const variantAttributeSelect = document.getElementById('variantAttributes');
        const variantAttributes = Array.from(variantAttributeSelect.selectedOptions).map(option => parseInt(option.value));
        
        const formData = {
            name: document.getElementById('templateName').value,
            categ_id: parseInt(document.getElementById('templateCategory').value),
            list_price: parseFloat(document.getElementById('listPrice').value) || 0,
            standard_price: parseFloat(document.getElementById('standardPrice').value) || 0,
            type: document.getElementById('productType').value,
            default_code: document.getElementById('defaultCode').value,
            template_attributes: templateAttributes,  // {attr_id: "text_value"}
            variant_attributes: variantAttributes    // [attr_id1, attr_id2, ...]
        };
        
        console.log('Saving template with data:', formData);
        
        const templateId = document.getElementById('templateId').value;
        let url = '/api/templates';
        let method = 'POST';
        
        if (isEditing && templateId) {
            url += `/${templateId}`;
            method = 'PUT';
            // Khi edit, không update attributes
            delete formData.template_attributes;
            delete formData.variant_attributes;
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
            loadTemplates();
        } else {
            showAlert('Lỗi khi lưu: ' + data.error, 'danger');
        }
    } catch (error) {
        console.error('Error saving template:', error);
        showAlert('Lỗi kết nối: ' + error.message, 'danger');
    }
}

// Xóa template
async function deleteTemplate(id) {
    if (!confirm('Bạn có chắc chắn muốn xóa template này?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/templates/${id}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert('Xóa thành công!', 'success');
            loadTemplates();
        } else {
            showAlert('Lỗi khi xóa: ' + data.error, 'danger');
        }
    } catch (error) {
        showAlert('Lỗi kết nối: ' + error.message, 'danger');
    }
}

// Format tiền tệ
function formatCurrency(amount) {
    return new Intl.NumberFormat('vi-VN', {
        style: 'currency',
        currency: 'VND'
    }).format(amount || 0);
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

// Suggest similar templates based on name and category
async function suggestSimilarTemplates() {
    const templateName = document.getElementById('templateName').value;
    const categoryId = document.getElementById('templateCategory').value;
    
    // Chỉ suggest nếu có tên hoặc category được chọn
    if (!templateName && !categoryId) {
        document.getElementById('suggestedSection').style.display = 'none';
        return;
    }
    
    try {
        const response = await fetch('/api/templates/suggest', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: templateName,
                categ_id: categoryId ? parseInt(categoryId) : null
            })
        });
        
        const data = await response.json();
        
        if (data.success && data.data.length > 0) {
            renderSuggestedTemplates(data.data);
            document.getElementById('suggestedSection').style.display = 'block';
        } else {
            document.getElementById('suggestedSection').style.display = 'none';
        }
    } catch (error) {
        console.error('Lỗi khi suggest templates:', error);
    }
}

// Render suggested templates table
function renderSuggestedTemplates(suggestedTemplates) {
    const tbody = document.getElementById('suggestedTable');
    tbody.innerHTML = '';
    
    suggestedTemplates.forEach(template => {
        const row = document.createElement('tr');
        const categoryName = template.categ_id ? template.categ_id[1] : '';
        
        row.innerHTML = `
            <td><strong>${template.name}</strong></td>
            <td>${categoryName}</td>
            <td>${template.default_code || ''}</td>
            <td>${template.barcode || ''}</td>
            <td>${formatCurrency(template.list_price)}</td>
        `;
        
        tbody.appendChild(row);
    });
}
