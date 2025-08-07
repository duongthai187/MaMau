// JavaScript cho quản lý Products

let products = [];
let templates = [];
let templateAttributes = {};
let attributesData = [];
let isEditing = false;

// Load dữ liệu khi trang được tải
document.addEventListener('DOMContentLoaded', function() {
    loadProducts();
    loadTemplates();
    loadAllAttributesForFilter();
    
    // Xử lý form submit
    document.getElementById('productFormData').addEventListener('submit', function(e) {
        e.preventDefault();
        saveProduct();
    });
    
    // Xử lý khi chọn template
    document.getElementById('productTemplate').addEventListener('change', function() {
        const templateId = this.value;
        if (templateId) {
            loadTemplateAttributes(templateId);
        } else {
            hideAttributesSection();
        }
    });
});

// Hiển thị form tạo mới
function showCreateForm() {
    isEditing = false;
    document.getElementById('formTitle').textContent = 'Tạo Product Mới';
    document.getElementById('productForm').style.display = 'block';
    document.getElementById('productFormData').reset();
    document.getElementById('productId').value = '';
    
    // Reload templates để đảm bảo có templates mới nhất
    loadTemplates();
}

// Ẩn form
function hideForm() {
    document.getElementById('productForm').style.display = 'none';
    document.getElementById('productFormData').reset();
}

// Hiển thị form chỉnh sửa
function editProduct(id) {
    isEditing = true;
    const product = products.find(p => p.id === id);
    
    if (product) {
        document.getElementById('formTitle').textContent = 'Chỉnh sửa Product';
        document.getElementById('productForm').style.display = 'block';
        document.getElementById('productId').value = product.id;
        document.getElementById('productName').value = product.name;
        document.getElementById('productTemplate').value = product.product_tmpl_id[0];
        document.getElementById('defaultCode').value = product.default_code || '';
        document.getElementById('barcode').value = product.barcode || '';
    }
}

// Load danh sách products
async function loadProducts() {
    try {
        showLoading(true);
        const response = await fetch('/api/products');
        const data = await response.json();
        
        if (data.success) {
            products = data.data;
            renderProductsTable();
        } else {
            showAlert('Lỗi khi tải dữ liệu: ' + data.error, 'danger');
        }
    } catch (error) {
        showAlert('Lỗi kết nối: ' + error.message, 'danger');
    } finally {
        showLoading(false);
    }
}

// Load templates cho dropdown
async function loadTemplates() {
    try {
        const response = await fetch('/api/templates');
        const data = await response.json();
        
        if (data.success) {
            templates = data.data;
            renderTemplateOptions();
            renderFilterTemplateOptions();
            showAlert('Đã cập nhật danh sách templates!', 'success');
        }
    } catch (error) {
        console.error('Lỗi khi load templates:', error);
        showAlert('Lỗi khi load templates: ' + error.message, 'danger');
    }
}

// Render options cho template dropdown trong form
function renderTemplateOptions() {
    const select = document.getElementById('productTemplate');
    select.innerHTML = '<option value="">-- Chọn template --</option>';
    
    templates.forEach(template => {
        const option = document.createElement('option');
        option.value = template.id;
        option.textContent = template.name;
        select.appendChild(option);
    });
}

// Render options cho filter template dropdown
function renderFilterTemplateOptions() {
    const select = document.getElementById('filterTemplate');
    select.innerHTML = '<option value="">-- Tất cả templates --</option>';
    
    templates.forEach(template => {
        const option = document.createElement('option');
        option.value = template.id;
        option.textContent = template.name;
        select.appendChild(option);
    });
}

// Load attributes của template được chọn
async function loadTemplateAttributes(templateId) {
    try {
        const response = await fetch(`/api/templates/${templateId}/attributes`);
        const data = await response.json();
        
        if (data.success) {
            templateAttributes[templateId] = data.data;
            if (data.data.length > 0) {
                renderAttributeSelections(data.data);
                showAttributesSection();
            } else {
                hideAttributesSection();
            }
            // Update product code when template changes
            updateProductCode();
        }
    } catch (error) {
        console.error('Lỗi khi load attributes:', error);
    }
}

// Hiển thị section chọn attributes
function showAttributesSection() {
    document.getElementById('attributesSection').style.display = 'block';
}

// Ẩn section chọn attributes
function hideAttributesSection() {
    document.getElementById('attributesSection').style.display = 'none';
}

// Render các dropdown chọn attribute values
function renderAttributeSelections(attributes) {
    const container = document.getElementById('attributeSelections');
    container.innerHTML = '';
    
    attributes.forEach(attribute => {
        const col = document.createElement('div');
        col.className = 'col-md-6 mb-3';
        
        col.innerHTML = `
            <label class="form-label">${attribute.name} *</label>
            <select class="form-select attribute-select" data-attribute-id="${attribute.id}" required>
                <option value="">-- Chọn ${attribute.name} --</option>
                ${attribute.values.map(value => `<option value="${value.id}">${value.name}</option>`).join('')}
            </select>
        `;
        
        container.appendChild(col);
    });
    
    // Add event listeners for auto-code generation
    const selects = container.querySelectorAll('.attribute-select');
    selects.forEach(select => {
        select.addEventListener('change', updateProductCode);
    });
}

// Load tất cả attributes để làm filter
async function loadAllAttributesForFilter() {
    try {
        const response = await fetch('/api/products/all-attributes');
        const data = await response.json();
        
        if (data.success) {
            renderGlobalAttributeFilters(data.data);
        }
    } catch (error) {
        console.error('Lỗi khi load attributes cho filter:', error);
    }
}

// Render global attribute filters (không phụ thuộc template)
function renderGlobalAttributeFilters(attributes) {
    const container = document.getElementById('attributeFilters');
    
    // Xóa existing filters trừ template dropdown
    const existingFilters = container.querySelectorAll('.global-attribute-filter');
    existingFilters.forEach(filter => filter.remove());
    
    // Thêm filter cho mỗi attribute
    attributes.forEach(attribute => {
        if (attribute.values && attribute.values.length > 0) {
            const col = document.createElement('div');
            col.className = 'col-md-3 global-attribute-filter';
            
            col.innerHTML = `
                <label class="form-label">${attribute.name}</label>
                <select class="form-select global-filter" data-attribute-id="${attribute.id}">
                    <option value="">-- Tất cả ${attribute.name} --</option>
                    ${attribute.values.map(value => `<option value="${value.id}">${value.name}</option>`).join('')}
                </select>
            `;
            
            container.appendChild(col);
        }
    });
}

// Load attribute filters cho trang (template-specific - giữ nguyên)
async function loadAttributeFilters() {
    const templateId = document.getElementById('filterTemplate').value;
    const filtersContainer = document.getElementById('attributeFilters');
    
    // Xóa các filter cũ (trừ template dropdown)
    const existingFilters = filtersContainer.querySelectorAll('.attribute-filter');
    existingFilters.forEach(filter => filter.remove());
    
    if (templateId) {
        try {
            const response = await fetch(`/api/templates/${templateId}/attributes`);
            const data = await response.json();
            
            if (data.success && data.data.length > 0) {
                attributesData = data.data;
                renderAttributeFilters(data.data);
            }
        } catch (error) {
            console.error('Lỗi khi load attribute filters:', error);
        }
    }
}

// Render attribute filter dropdowns
function renderAttributeFilters(attributes) {
    const container = document.getElementById('attributeFilters');
    
    attributes.forEach((attribute, index) => {
        const col = document.createElement('div');
        col.className = 'col-md-3 attribute-filter';
        
        col.innerHTML = `
            <label class="form-label">${attribute.name}</label>
            <select class="form-select" id="filter_${attribute.id}">
                <option value="">-- Tất cả ${attribute.name} --</option>
                ${attribute.values.map(value => `<option value="${value.id}">${value.name}</option>`).join('')}
            </select>
        `;
        
        container.appendChild(col);
    });
}

// Áp dụng bộ lọc
async function applyFilters() {
    const templateId = document.getElementById('filterTemplate').value;
    const attributeValueIds = [];
    
    // Lấy các attribute values từ global filters
    const globalFilters = document.querySelectorAll('.global-filter');
    globalFilters.forEach(select => {
        if (select.value) {
            attributeValueIds.push(parseInt(select.value));
        }
    });
    
    try {
        const response = await fetch('/api/products/suggest', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                template_id: templateId ? parseInt(templateId) : null,
                attribute_value_ids: attributeValueIds
            })
        });
        
        const data = await response.json();
        if (data.success) {
            products = data.data;
            renderProductsTable();
            showAlert(`Tìm thấy ${data.data.length} sản phẩm phù hợp!`, 'info');
        }
    } catch (error) {
        showAlert('Lỗi khi lọc sản phẩm: ' + error.message, 'danger');
    }
}

// Xóa bộ lọc
function clearFilters() {
    document.getElementById('filterTemplate').value = '';
    
    // Clear global filters
    const globalFilters = document.querySelectorAll('.global-filter');
    globalFilters.forEach(select => {
        select.value = '';
    });
    
    // Reset về tất cả products
    loadProducts();
}

// Render bảng products
function renderProductsTable() {
    const tbody = document.getElementById('productsTable');
    tbody.innerHTML = '';
    
    products.forEach(product => {
        const row = document.createElement('tr');
        
        const templateName = product.product_tmpl_id ? product.product_tmpl_id[1] : '';
        
        row.innerHTML = `
            <td>${product.id}</td>
            <td>${product.name}</td>
            <td>${templateName}</td>
            <td>${product.default_code || ''}</td>
            <td>${product.barcode || ''}</td>
            <td>${formatCurrency(product.lst_price)}</td>
            <td>
                <button class="btn btn-sm btn-primary btn-action" onclick="editProduct(${product.id})">Sửa</button>
                <button class="btn btn-sm btn-danger btn-action" onclick="deleteProduct(${product.id})">Xóa</button>
            </td>
        `;
        
        tbody.appendChild(row);
    });
}

// Lưu product (tạo mới hoặc cập nhật)
async function saveProduct() {
    try {
        const templateId = document.getElementById('productTemplate').value;
        
        // Lấy attribute values được chọn
        const attributeValueIds = [];
        const attributeSelects = document.querySelectorAll('.attribute-select');
        
        attributeSelects.forEach(select => {
            if (select.value) {
                attributeValueIds.push(parseInt(select.value));
            }
        });
        
        // Validate attributes nếu có
        if (attributeSelects.length > 0 && attributeValueIds.length !== attributeSelects.length) {
            showAlert('Vui lòng chọn đầy đủ tất cả attributes!', 'warning');
            return;
        }
        
        const formData = {
            name: document.getElementById('productName').value,
            product_tmpl_id: parseInt(templateId),
            default_code: document.getElementById('defaultCode').value,
            barcode: document.getElementById('barcode').value,
            attribute_value_ids: attributeValueIds
        };
        
        const productId = document.getElementById('productId').value;
        let url = '/api/products';
        let method = 'POST';
        
        if (isEditing && productId) {
            url += `/${productId}`;
            method = 'PUT';
            delete formData.attribute_value_ids; // Không update attributes khi edit
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
            loadProducts();
        } else {
            showAlert('Lỗi khi lưu: ' + data.error, 'danger');
        }
    } catch (error) {
        showAlert('Lỗi kết nối: ' + error.message, 'danger');
    }
}

// Xóa product
async function deleteProduct(id) {
    if (!confirm('Bạn có chắc chắn muốn xóa product này?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/products/${id}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert('Xóa thành công!', 'success');
            loadProducts();
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

// Tự động cập nhật mã sản phẩm khi chọn template/attributes
function updateProductCode() {
    const templateId = document.getElementById('productTemplate').value;
    const codeInput = document.getElementById('defaultCode');
    
    if (!templateId) {
        codeInput.value = '';
        return;
    }
    
    // Get template info
    const template = templates.find(t => t.id == templateId);
    if (!template) {
        codeInput.value = '';
        return;
    }
    
    // Start with template code or name
    let code = template.default_code || template.name || 'PRODUCT';
    
    // Add attribute codes
    const attributeSelects = document.querySelectorAll('.attribute-select');
    attributeSelects.forEach(select => {
        if (select.value) {
            const selectedOption = select.options[select.selectedIndex];
            if (selectedOption) {
                const valueText = selectedOption.textContent;
                // Generate short code from value name
                const valueCode = generateAttributeCode(valueText);
                code += '-' + valueCode;
            }
        }
    });
    
    codeInput.value = code;
}

// Generate short code from attribute value name
function generateAttributeCode(text) {
    if (!text) return '';
    
    // Remove Vietnamese diacritics
    const normalized = text.normalize('NFD').replace(/[\u0300-\u036f]/g, '');
    
    // Split into words and take first 2-3 chars
    const words = normalized.toUpperCase().split(/\s+/);
    if (words.length === 1) {
        return words[0].substring(0, 3);
    } else {
        return words.map(word => word.substring(0, 2)).join('');
    }
}
