/**
 * BTMH Gold Management JavaScript
 * Xử lý tất cả tương tác frontend cho hệ thống quản lý thuộc tính vàng
 */

// Global variables
let currentPage = {
    groups: 1,
    attributes: 1,
    templates: 1
};

let currentData = {
    groups: [],
    attributes: [],
    templates: [],
    attributeGroups: [],
    categories: []
};

// Utility functions
function showLoading(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        container.querySelector('.loading').style.display = 'table-row';
    }
}

function hideLoading(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        container.querySelector('.loading').style.display = 'none';
    }
}

function showAlert(message, type = 'info') {
    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

function formatCurrency(value) {
    return new Intl.NumberFormat('vi-VN', {
        style: 'currency',
        currency: 'VND'
    }).format(value || 0);
}

// API functions
async function apiCall(url, method = 'GET', data = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        }
    };
    
    if (data) {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(url, options);
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.detail || 'Có lỗi xảy ra');
        }
        
        return result;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// ================================
// ATTRIBUTE GROUPS
// ================================

async function loadAttributeGroups(page = 1, search = '') {
    showLoading('groupsTableBody');
    
    try {
        const params = new URLSearchParams({
            page: page,
            limit: 20
        });
        
        if (search) {
            params.append('search', search);
        }
        
        const response = await apiCall(`/api/attribute-groups?${params}`);
        
        if (response.success) {
            currentData.groups = response.data;
            currentPage.groups = page;
            renderAttributeGroupsTable(response.data);
            renderPagination('groups', response.total, page, 20);
        }
    } catch (error) {
        showAlert('Lỗi khi tải danh sách nhóm thuộc tính: ' + error.message, 'danger');
    } finally {
        hideLoading('groupsTableBody');
    }
}

function renderAttributeGroupsTable(groups) {
    const tbody = document.getElementById('groupsTableBody');
    const loadingRow = tbody.querySelector('.loading');
    
    // Clear existing data rows
    const dataRows = tbody.querySelectorAll('tr:not(.loading)');
    dataRows.forEach(row => row.remove());
    
    if (groups.length === 0) {
        const emptyRow = document.createElement('tr');
        emptyRow.innerHTML = '<td colspan="7" class="text-center text-muted">Không có dữ liệu</td>';
        tbody.appendChild(emptyRow);
        return;
    }
    
    groups.forEach(group => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${group.id}</td>
            <td><strong>${group.name}</strong></td>
            <td>${group.code || '-'}</td>
            <td>${group.sequence}</td>
            <td><span class="badge bg-info">${group.attribute_count}</span></td>
            <td>${group.create_date || '-'}</td>
            <td>
                <div class="btn-group btn-group-sm" role="group">
                    <button class="btn btn-outline-primary" onclick="editAttributeGroup(${group.id})" title="Sửa">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-outline-danger" onclick="deleteAttributeGroup(${group.id})" title="Xóa">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function showAttributeGroupModal(groupId = null) {
    const modal = new bootstrap.Modal(document.getElementById('attributeGroupModal'));
    const form = document.getElementById('attributeGroupForm');
    const title = document.getElementById('attributeGroupModalTitle');
    
    // Reset form
    form.reset();
    document.getElementById('groupId').value = '';
    
    if (groupId) {
        title.textContent = 'Sửa Nhóm Thuộc Tính';
        loadAttributeGroupData(groupId);
    } else {
        title.textContent = 'Thêm Nhóm Thuộc Tính';
    }
    
    modal.show();
}

async function loadAttributeGroupData(groupId) {
    try {
        const response = await apiCall(`/api/attribute-groups/${groupId}`);
        
        if (response.success) {
            const group = response.data;
            document.getElementById('groupId').value = group.id;
            document.getElementById('groupName').value = group.name;
            document.getElementById('groupCode').value = group.code || '';
            document.getElementById('groupSequence').value = group.sequence;
        }
    } catch (error) {
        showAlert('Lỗi khi tải dữ liệu nhóm thuộc tính: ' + error.message, 'danger');
    }
}

async function saveAttributeGroup() {
    const form = document.getElementById('attributeGroupForm');
    const formData = new FormData(form);
    
    const groupData = {
        name: document.getElementById('groupName').value,
        code: document.getElementById('groupCode').value || null,
        sequence: parseInt(document.getElementById('groupSequence').value) || 10
    };
    
    const groupId = document.getElementById('groupId').value;
    
    try {
        let response;
        if (groupId) {
            response = await apiCall(`/api/attribute-groups/${groupId}`, 'PUT', groupData);
        } else {
            response = await apiCall('/api/attribute-groups', 'POST', groupData);
        }
        
        if (response.success) {
            showAlert(response.message || 'Lưu nhóm thuộc tính thành công', 'success');
            const modal = bootstrap.Modal.getInstance(document.getElementById('attributeGroupModal'));
            modal.hide();
            loadAttributeGroups(currentPage.groups);
            loadAttributeGroupsForFilter(); // Reload for filters
        }
    } catch (error) {
        showAlert('Lỗi khi lưu nhóm thuộc tính: ' + error.message, 'danger');
    }
}

async function editAttributeGroup(groupId) {
    showAttributeGroupModal(groupId);
}

async function deleteAttributeGroup(groupId) {
    if (!confirm('Bạn có chắc chắn muốn xóa nhóm thuộc tính này?')) {
        return;
    }
    
    try {
        const response = await apiCall(`/api/attribute-groups/${groupId}`, 'DELETE');
        
        if (response.success) {
            showAlert(response.message || 'Xóa nhóm thuộc tính thành công', 'success');
            loadAttributeGroups(currentPage.groups);
            loadAttributeGroupsForFilter(); // Reload for filters
        }
    } catch (error) {
        showAlert('Lỗi khi xóa nhóm thuộc tính: ' + error.message, 'danger');
    }
}

// ================================
// GOLD ATTRIBUTES
// ================================

async function loadGoldAttributes(page = 1, search = '', groupId = '', fieldType = '') {
    showLoading('attributesTableBody');
    
    try {
        const params = new URLSearchParams({
            page: page,
            limit: 20
        });
        
        if (search) params.append('search', search);
        if (groupId) params.append('group_id', groupId);
        if (fieldType) params.append('field_type', fieldType);
        
        const response = await apiCall(`/api/gold-attributes?${params}`);
        
        if (response.success) {
            currentData.attributes = response.data;
            currentPage.attributes = page;
            renderGoldAttributesTable(response.data);
            renderPagination('attributes', response.total, page, 20);
        }
    } catch (error) {
        showAlert('Lỗi khi tải danh sách thuộc tính vàng: ' + error.message, 'danger');
    } finally {
        hideLoading('attributesTableBody');
    }
}

function renderGoldAttributesTable(attributes) {
    const tbody = document.getElementById('attributesTableBody');
    const loadingRow = tbody.querySelector('.loading');
    
    // Clear existing data rows
    const dataRows = tbody.querySelectorAll('tr:not(.loading)');
    dataRows.forEach(row => row.remove());
    
    if (attributes.length === 0) {
        const emptyRow = document.createElement('tr');
        emptyRow.innerHTML = '<td colspan="8" class="text-center text-muted">Không có dữ liệu</td>';
        tbody.appendChild(emptyRow);
        return;
    }
    
    attributes.forEach(attr => {
        // Format field type display with selection options
        let fieldTypeDisplay = `<span class="badge bg-secondary">${getFieldTypeLabel(attr.field_type)}</span>`;
        if (attr.field_type === 'selection' && attr.selection_options_list && attr.selection_options_list.length > 0) {
            const optionsText = attr.selection_options_list.join(', ');
            fieldTypeDisplay += `<br><small class="text-muted">${optionsText}</small>`;
        }
        
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${attr.id}</td>
            <td><strong>${attr.name}</strong></td>
            <td>${attr.display_name || '-'}</td>
            <td>${fieldTypeDisplay}</td>
            <td>${attr.group_name}</td>
            <td>${attr.required ? '<i class="fas fa-check text-success"></i>' : '<i class="fas fa-times text-muted"></i>'}</td>
            <td>${attr.active ? '<span class="badge bg-success">Hoạt động</span>' : '<span class="badge bg-secondary">Không hoạt động</span>'}</td>
            <td>
                <div class="btn-group btn-group-sm" role="group">
                    <button class="btn btn-outline-primary" onclick="editGoldAttribute(${attr.id})" title="Sửa">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-outline-danger" onclick="deleteGoldAttribute(${attr.id})" title="Xóa">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function getFieldTypeLabel(fieldType) {
    const types = {
        'char': 'Văn bản',
        'float': 'Số thập phân',
        'integer': 'Số nguyên',
        'boolean': 'Đúng/Sai',
        'date': 'Ngày',
        'selection': 'Lựa chọn'
    };
    return types[fieldType] || fieldType;
}

function showGoldAttributeModal(attrId = null) {
    const modal = new bootstrap.Modal(document.getElementById('goldAttributeModal'));
    const form = document.getElementById('goldAttributeForm');
    const title = document.getElementById('goldAttributeModalTitle');
    
    // Reset form
    form.reset();
    document.getElementById('attrId').value = '';
    document.getElementById('attrFieldType').value = '';
    document.getElementById('attrCategory').value = 'technical';
    document.getElementById('attrRequired').checked = false;
    document.getElementById('attrEditable').checked = true;
    document.getElementById('attrActive').checked = true;
    
    // Hide selection options by default
    document.getElementById('selectionOptionsContainer').style.display = 'none';
    
    if (attrId) {
        title.textContent = 'Sửa Thuộc Tính Vàng';
        loadGoldAttributeData(attrId);
    } else {
        title.textContent = 'Thêm Thuộc Tính Vàng';
    }
    
    modal.show();
}

async function loadGoldAttributeData(attrId) {
    try {
        const response = await apiCall(`/api/gold-attributes/${attrId}`);
        
        if (response.success) {
            const attr = response.data;
            document.getElementById('attrId').value = attr.id;
            document.getElementById('attrName').value = attr.name;
            document.getElementById('attrDisplayName').value = attr.display_name || '';
            document.getElementById('attrShortName').value = attr.short_name || '';
            document.getElementById('attrFieldType').value = attr.field_type;
            document.getElementById('attrGroup').value = attr.group_id ? attr.group_id[0] : '';
            document.getElementById('attrCategory').value = attr.category || 'technical';
            document.getElementById('attrUnit').value = attr.unit || '';
            document.getElementById('attrDefaultValue').value = attr.default_value || '';
            document.getElementById('attrDescription').value = attr.description || '';
            document.getElementById('attrSelectionOptions').value = attr.selection_options || '';
            document.getElementById('attrRequired').checked = attr.required;
            document.getElementById('attrEditable').checked = attr.editable;
            document.getElementById('attrActive').checked = attr.active;
            
            // Show selection options if type is selection
            toggleSelectionOptions();
        }
    } catch (error) {
        showAlert('Lỗi khi tải dữ liệu thuộc tính vàng: ' + error.message, 'danger');
    }
}

function toggleSelectionOptions() {
    const fieldType = document.getElementById('attrFieldType').value;
    const container = document.getElementById('selectionOptionsContainer');
    
    if (fieldType === 'selection') {
        container.style.display = 'block';
    } else {
        container.style.display = 'none';
    }
}

async function saveGoldAttribute() {
    const form = document.getElementById('goldAttributeForm');
    
    const attrData = {
        name: document.getElementById('attrName').value,
        display_name: document.getElementById('attrDisplayName').value || null,
        short_name: document.getElementById('attrShortName').value || null,
        field_type: document.getElementById('attrFieldType').value,
        group_id: parseInt(document.getElementById('attrGroup').value) || null,
        category: document.getElementById('attrCategory').value,
        unit: document.getElementById('attrUnit').value || null,
        default_value: document.getElementById('attrDefaultValue').value || null,
        description: document.getElementById('attrDescription').value || null,
        selection_options: document.getElementById('attrSelectionOptions').value || null,
        required: document.getElementById('attrRequired').checked,
        editable: document.getElementById('attrEditable').checked,
        active: document.getElementById('attrActive').checked
    };
    
    const attrId = document.getElementById('attrId').value;
    
    try {
        let response;
        if (attrId) {
            response = await apiCall(`/api/gold-attributes/${attrId}`, 'PUT', attrData);
        } else {
            response = await apiCall('/api/gold-attributes', 'POST', attrData);
        }
        
        if (response.success) {
            showAlert(response.message || 'Lưu thuộc tính vàng thành công', 'success');
            const modal = bootstrap.Modal.getInstance(document.getElementById('goldAttributeModal'));
            modal.hide();
            loadGoldAttributes(currentPage.attributes);
        }
    } catch (error) {
        showAlert('Lỗi khi lưu thuộc tính vàng: ' + error.message, 'danger');
    }
}

async function editGoldAttribute(attrId) {
    showGoldAttributeModal(attrId);
}

async function deleteGoldAttribute(attrId) {
    if (!confirm('Bạn có chắc chắn muốn xóa thuộc tính vàng này?')) {
        return;
    }
    
    try {
        const response = await apiCall(`/api/gold-attributes/${attrId}`, 'DELETE');
        
        if (response.success) {
            showAlert(response.message || 'Xóa thuộc tính vàng thành công', 'success');
            loadGoldAttributes(currentPage.attributes);
        }
    } catch (error) {
        showAlert('Lỗi khi xóa thuộc tính vàng: ' + error.message, 'danger');
    }
}

// ================================
// PRODUCT TEMPLATES
// ================================

async function loadProductTemplates(page = 1, search = '', categoryId = '') {
    return loadProductTemplatesWithFilters(page, search, categoryId, {});
}

async function loadProductTemplatesWithFilters(page = 1, search = '', categoryId = '', attributeFilters = {}) {
    showLoading('templatesTableBody');
    
    try {
        const params = new URLSearchParams({
            page: page,
            limit: 20
        });
        
        if (search) params.append('search', search);
        if (categoryId) params.append('categ_id', categoryId);
        
        // Add attribute filters to URL params
        Object.keys(attributeFilters).forEach(attrId => {
            params.append(`attr_${attrId}`, attributeFilters[attrId]);
        });
        
        console.log('🔍 Loading templates with filters:', {
            page, search, categoryId, attributeFilters
        });
        
        const response = await apiCall(`/api/product-templates?${params}`);
        
        if (response.success) {
            currentData.templates = response.data;
            currentPage.templates = page;
            renderProductTemplatesTable(response.data);
            renderPagination('templates', response.total, page, 20);
        }
    } catch (error) {
        showAlert('Lỗi khi tải danh sách mã mẫu sản phẩm: ' + error.message, 'danger');
    } finally {
        hideLoading('templatesTableBody');
    }
}

function renderProductTemplatesTable(templates) {
    const tbody = document.getElementById('templatesTableBody');
    const loadingRow = tbody.querySelector('.loading');
    
    // Clear existing data rows
    const dataRows = tbody.querySelectorAll('tr:not(.loading)');
    dataRows.forEach(row => row.remove());
    
    if (templates.length === 0) {
        const emptyRow = document.createElement('tr');
        emptyRow.innerHTML = '<td colspan="8" class="text-center text-muted">Không có dữ liệu</td>';
        tbody.appendChild(emptyRow);
        return;
    }
    
    templates.forEach(template => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${template.id}</td>
            <td><strong>${template.name}</strong></td>
            <td>${template.default_code || '-'}</td>
            <td>${template.categ_name || '-'}</td>
            <td>${formatCurrency(template.list_price)}</td>
            <td>${formatCurrency(template.standard_price)}</td>
            <td>${template.create_date || '-'}</td>
            <td>
                <div class="btn-group btn-group-sm" role="group">
                    <button class="btn btn-outline-info" onclick="viewProductTemplate(${template.id})" title="Xem">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn btn-outline-primary" onclick="editProductTemplate(${template.id})" title="Sửa">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-outline-danger" onclick="deleteProductTemplate(${template.id})" title="Xóa">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function showProductTemplateModal(templateId = null) {
    const modal = new bootstrap.Modal(document.getElementById('productTemplateModal'));
    const form = document.getElementById('productTemplateForm');
    const title = document.getElementById('productTemplateModalTitle');
    
    // Reset form
    form.reset();
    document.getElementById('templateId').value = '';
    document.getElementById('templateType').value = 'product';
    document.getElementById('templateSaleOk').checked = true;
    document.getElementById('templatePurchaseOk').checked = true;
    
    if (templateId) {
        title.textContent = 'Sửa Mã Mẫu Sản Phẩm';
        loadProductTemplateData(templateId);
    } else {
        title.textContent = 'Thêm Mã Mẫu Sản Phẩm';
        loadGoldAttributesForTemplate();
    }
    
    modal.show();
}

async function loadProductTemplateData(templateId) {
    try {
        const response = await apiCall(`/api/product-templates/${templateId}`);
        
        if (response.success) {
            const template = response.data;
            document.getElementById('templateId').value = template.id;
            document.getElementById('templateName').value = template.name;
            document.getElementById('templateCode').value = template.default_code || '';
            document.getElementById('templateCategory').value = template.categ_id ? template.categ_id[0] : '';
            document.getElementById('templateType').value = template.type;
            document.getElementById('templateListPrice').value = template.list_price;
            document.getElementById('templateStandardPrice').value = template.standard_price;
            document.getElementById('templateDescription').value = template.description || '';
            document.getElementById('templateSaleOk').checked = template.sale_ok;
            document.getElementById('templatePurchaseOk').checked = template.purchase_ok;
            
            // Load gold attributes for this template
            loadGoldAttributesForTemplate(template.gold_attributes);
        }
    } catch (error) {
        showAlert('Lỗi khi tải dữ liệu mã mẫu sản phẩm: ' + error.message, 'danger');
    }
}

async function loadGoldAttributesForTemplate(existingValues = {}) {
    try {
        const response = await apiCall('/api/gold-attributes?active=true&limit=100');
        
        if (response.success) {
            const container = document.getElementById('goldAttributesContainer');
            container.innerHTML = '';
            
            const attributes = response.data;
            
            if (attributes.length === 0) {
                container.innerHTML = '<p class="text-muted">Chưa có thuộc tính vàng nào được định nghĩa.</p>';
                return;
            }
            
            // Group attributes by group
            const groupedAttrs = {};
            attributes.forEach(attr => {
                const groupName = attr.group_name || 'Không có nhóm';
                if (!groupedAttrs[groupName]) {
                    groupedAttrs[groupName] = [];
                }
                groupedAttrs[groupName].push(attr);
            });
            
            // Render groups
            Object.keys(groupedAttrs).forEach(groupName => {
                const groupDiv = document.createElement('div');
                groupDiv.className = 'mb-4';
                groupDiv.innerHTML = `<h6 class="text-muted border-bottom pb-2">${groupName}</h6>`;
                
                const attrsDiv = document.createElement('div');
                attrsDiv.className = 'row';
                
                groupedAttrs[groupName].forEach(attr => {
                    const colDiv = document.createElement('div');
                    colDiv.className = 'col-md-6 mb-3';
                    
                    const value = existingValues[attr.id] || attr.default_value || '';
                    
                    let inputHtml = '';
                    switch (attr.field_type) {
                        case 'boolean':
                            inputHtml = `
                                <div class="form-check">
                                    <input class="form-check-input" type="checkbox" id="goldAttr_${attr.id}" ${value ? 'checked' : ''}>
                                    <label class="form-check-label" for="goldAttr_${attr.id}">
                                        ${attr.display_name || attr.name}
                                        ${attr.required ? ' <span class="text-danger">*</span>' : ''}
                                    </label>
                                </div>
                            `;
                            break;
                        case 'selection':
                            const options = attr.selection_options ? attr.selection_options.split('\n').filter(o => o.trim()) : [];
                            inputHtml = `
                                <label for="goldAttr_${attr.id}" class="form-label">
                                    ${attr.display_name || attr.name}
                                    ${attr.required ? ' <span class="text-danger">*</span>' : ''}
                                </label>
                                <select class="form-select" id="goldAttr_${attr.id}" ${attr.required ? 'required' : ''}>
                                    <option value="">Chọn...</option>
                                    ${options.map(opt => `<option value="${opt.trim()}" ${value === opt.trim() ? 'selected' : ''}>${opt.trim()}</option>`).join('')}
                                </select>
                            `;
                            break;
                        case 'date':
                            inputHtml = `
                                <label for="goldAttr_${attr.id}" class="form-label">
                                    ${attr.display_name || attr.name}
                                    ${attr.required ? ' <span class="text-danger">*</span>' : ''}
                                </label>
                                <input type="date" class="form-control" id="goldAttr_${attr.id}" value="${value}" ${attr.required ? 'required' : ''}>
                            `;
                            break;
                        case 'float':
                        case 'integer':
                            inputHtml = `
                                <label for="goldAttr_${attr.id}" class="form-label">
                                    ${attr.display_name || attr.name}
                                    ${attr.unit ? ` (${attr.unit})` : ''}
                                    ${attr.required ? ' <span class="text-danger">*</span>' : ''}
                                </label>
                                <input type="number" class="form-control" id="goldAttr_${attr.id}" value="${value}" 
                                       ${attr.field_type === 'float' ? 'step="0.01"' : ''} ${attr.required ? 'required' : ''}>
                            `;
                            break;
                        default: // char
                            inputHtml = `
                                <label for="goldAttr_${attr.id}" class="form-label">
                                    ${attr.display_name || attr.name}
                                    ${attr.unit ? ` (${attr.unit})` : ''}
                                    ${attr.required ? ' <span class="text-danger">*</span>' : ''}
                                </label>
                                <input type="text" class="form-control" id="goldAttr_${attr.id}" value="${value}" ${attr.required ? 'required' : ''}>
                            `;
                    }
                    
                    if (attr.description) {
                        inputHtml += `<div class="form-text">${attr.description}</div>`;
                    }
                    
                    colDiv.innerHTML = inputHtml;
                    attrsDiv.appendChild(colDiv);
                });
                
                groupDiv.appendChild(attrsDiv);
                container.appendChild(groupDiv);
            });
        }
    } catch (error) {
        console.error('Error loading gold attributes:', error);
        const container = document.getElementById('goldAttributesContainer');
        container.innerHTML = '<p class="text-danger">Lỗi khi tải thuộc tính vàng.</p>';
    }
}

async function saveProductTemplate() {
    const form = document.getElementById('productTemplateForm');
    
    // Collect basic template data
    const templateData = {
        name: document.getElementById('templateName').value,
        default_code: document.getElementById('templateCode').value || null,
        categ_id: parseInt(document.getElementById('templateCategory').value) || null,
        type: document.getElementById('templateType').value,
        list_price: parseFloat(document.getElementById('templateListPrice').value) || 0,
        standard_price: parseFloat(document.getElementById('templateStandardPrice').value) || 0,
        description: document.getElementById('templateDescription').value || null,
        sale_ok: document.getElementById('templateSaleOk').checked,
        purchase_ok: document.getElementById('templatePurchaseOk').checked
    };
    
    // Collect gold attributes data
    const goldAttributes = {};
    const attrInputs = document.querySelectorAll('[id^="goldAttr_"]');
    attrInputs.forEach(input => {
        const attrId = input.id.replace('goldAttr_', '');
        let value = null;
        
        if (input.type === 'checkbox') {
            value = input.checked;
        } else if (input.value.trim()) {
            value = input.value.trim();
        }
        
        if (value !== null && value !== '') {
            goldAttributes[attrId] = value;
        }
    });
    
    templateData.gold_attributes = goldAttributes;
    
    const templateId = document.getElementById('templateId').value;
    
    try {
        let response;
        if (templateId) {
            response = await apiCall(`/api/product-templates/${templateId}`, 'PUT', templateData);
        } else {
            response = await apiCall('/api/product-templates', 'POST', templateData);
        }
        
        if (response.success) {
            showAlert(response.message || 'Lưu mã mẫu sản phẩm thành công', 'success');
            const modal = bootstrap.Modal.getInstance(document.getElementById('productTemplateModal'));
            modal.hide();
            loadProductTemplates(currentPage.templates);
        }
    } catch (error) {
        showAlert('Lỗi khi lưu mã mẫu sản phẩm: ' + error.message, 'danger');
    }
}

async function viewProductTemplate(templateId) {
    // Implement view functionality
    showAlert('Chức năng xem chi tiết đang được phát triển', 'info');
}

async function editProductTemplate(templateId) {
    showProductTemplateModal(templateId);
}

async function deleteProductTemplate(templateId) {
    if (!confirm('Bạn có chắc chắn muốn xóa mã mẫu sản phẩm này?')) {
        return;
    }
    
    try {
        const response = await apiCall(`/api/product-templates/${templateId}`, 'DELETE');
        
        if (response.success) {
            showAlert(response.message || 'Xóa mã mẫu sản phẩm thành công', 'success');
            loadProductTemplates(currentPage.templates);
        }
    } catch (error) {
        showAlert('Lỗi khi xóa mã mẫu sản phẩm: ' + error.message, 'danger');
    }
}

// ================================
// PAGINATION
// ================================

function renderPagination(type, total, currentPage, limit) {
    const totalPages = Math.ceil(total / limit);
    const startRecord = (currentPage - 1) * limit + 1;
    const endRecord = Math.min(currentPage * limit, total);
    
    // Update pagination info
    const paginationInfo = document.getElementById(`${type}Pagination`);
    if (paginationInfo) {
        paginationInfo.textContent = `Hiển thị ${startRecord}-${endRecord} của ${total} bản ghi`;
    }
    
    // Update pagination nav
    const paginationNav = document.getElementById(`${type}PaginationNav`);
    if (paginationNav && totalPages > 1) {
        let navHtml = '';
        
        // Previous button
        if (currentPage > 1) {
            navHtml += `<li class="page-item"><a class="page-link" href="#" onclick="load${type.charAt(0).toUpperCase() + type.slice(1)}(${currentPage - 1})">Trước</a></li>`;
        }
        
        // Page numbers
        const startPage = Math.max(1, currentPage - 2);
        const endPage = Math.min(totalPages, currentPage + 2);
        
        if (startPage > 1) {
            navHtml += `<li class="page-item"><a class="page-link" href="#" onclick="load${type.charAt(0).toUpperCase() + type.slice(1)}(1)">1</a></li>`;
            if (startPage > 2) {
                navHtml += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
            }
        }
        
        for (let i = startPage; i <= endPage; i++) {
            const activeClass = i === currentPage ? 'active' : '';
            navHtml += `<li class="page-item ${activeClass}"><a class="page-link" href="#" onclick="load${type.charAt(0).toUpperCase() + type.slice(1)}(${i})">${i}</a></li>`;
        }
        
        if (endPage < totalPages) {
            if (endPage < totalPages - 1) {
                navHtml += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
            }
            navHtml += `<li class="page-item"><a class="page-link" href="#" onclick="load${type.charAt(0).toUpperCase() + type.slice(1)}(${totalPages})">${totalPages}</a></li>`;
        }
        
        // Next button
        if (currentPage < totalPages) {
            navHtml += `<li class="page-item"><a class="page-link" href="#" onclick="load${type.charAt(0).toUpperCase() + type.slice(1)}(${currentPage + 1})">Sau</a></li>`;
        }
        
        paginationNav.innerHTML = navHtml;
    } else if (paginationNav) {
        paginationNav.innerHTML = '';
    }
}

// Wrapper functions for pagination
function loadGroups(page) {
    const search = document.getElementById('groupSearch').value;
    loadAttributeGroups(page, search);
}

function loadAttributes(page) {
    const search = document.getElementById('attrSearch').value;
    const groupId = document.getElementById('attrGroupFilter').value;
    const fieldType = document.getElementById('attrTypeFilter').value;
    loadGoldAttributes(page, search, groupId, fieldType);
}

function loadTemplates(page) {
    const search = document.getElementById('templateSearch').value;
    const categoryId = document.getElementById('templateCategoryFilter').value;
    const filters = collectAttributeFilters();
    loadProductTemplatesWithFilters(page, search, categoryId, filters);
}

// ================================
// HELPER FUNCTIONS
// ================================

async function loadAttributeGroupsForFilter() {
    try {
        const response = await apiCall('/api/attribute-groups?limit=100');
        
        if (response.success) {
            currentData.attributeGroups = response.data;
            
            // Update filter dropdown
            const attrGroupFilter = document.getElementById('attrGroupFilter');
            const attrGroup = document.getElementById('attrGroup');
            
            if (attrGroupFilter) {
                attrGroupFilter.innerHTML = '<option value="">Tất cả nhóm</option>';
                response.data.forEach(group => {
                    attrGroupFilter.innerHTML += `<option value="${group.id}">${group.name}</option>`;
                });
            }
            
            if (attrGroup) {
                attrGroup.innerHTML = '<option value="">Không có nhóm</option>';
                response.data.forEach(group => {
                    attrGroup.innerHTML += `<option value="${group.id}">${group.name}</option>`;
                });
            }
        }
    } catch (error) {
        console.error('Error loading attribute groups for filter:', error);
    }
}

async function loadCategoriesForFilter() {
    try {
        const response = await apiCall('/api/categories');
        
        if (response.success) {
            currentData.categories = response.data;
            
            // Update filter dropdown
            const templateCategoryFilter = document.getElementById('templateCategoryFilter');
            const templateCategory = document.getElementById('templateCategory');
            
            if (templateCategoryFilter) {
                templateCategoryFilter.innerHTML = '<option value="">Tất cả danh mục</option>';
                response.data.forEach(category => {
                    templateCategoryFilter.innerHTML += `<option value="${category.id}">${category.name}</option>`;
                });
            }
            
            if (templateCategory) {
                templateCategory.innerHTML = '<option value="">Chọn danh mục</option>';
                response.data.forEach(category => {
                    templateCategory.innerHTML += `<option value="${category.id}">${category.name}</option>`;
                });
            }
        }
    } catch (error) {
        console.error('Error loading categories for filter:', error);
    }
}

async function loadAttributesForProductTemplateFilters() {
    try {
        const response = await apiCall('/api/product-template-attributes');
        
        if (response.success) {
            renderAttributeFilters(response.data);
        }
    } catch (error) {
        console.error('Error loading attributes for product template filters:', error);
    }
}

function renderAttributeFilters(attributes) {
    const container = document.getElementById('attributeFiltersContainer');
    if (!container) return;
    
    // Clear existing filters
    container.innerHTML = '';
    
    // Filter out attributes that can be filtered
    const filterableAttributes = attributes.filter(attr => 
        attr.field_type === 'selection' || 
        attr.field_type === 'boolean' || 
        attr.field_type === 'char' || 
        attr.field_type === 'float' || 
        attr.field_type === 'integer'
    );
    
    if (filterableAttributes.length === 0) return;
    
    // Decide rendering strategy based on attribute count
    if (filterableAttributes.length <= 5) {
        // Show all filters directly
        renderDirectAttributeFilters(container, filterableAttributes);
    } else {
        // Show dropdown selector + dynamic filter
        renderSelectableAttributeFilters(container, filterableAttributes);
    }
}

function renderDirectAttributeFilters(container, attributes) {
    const filtersRow = document.createElement('div');
    filtersRow.className = 'row g-2';
    
    attributes.forEach(attr => {
        const colDiv = document.createElement('div');
        colDiv.className = 'col-md-2';
        
        // Create filter based on attribute type
        let filterElement;
        
        if (attr.field_type === 'selection' && attr.values && attr.values.length > 0) {
            // Dropdown for selection type
            filterElement = document.createElement('select');
            filterElement.className = 'form-select form-select-sm';
            filterElement.id = `attr-filter-${attr.id}`;
            filterElement.innerHTML = `<option value="">Tất cả ${attr.name}</option>`;
            
            attr.values.forEach(value => {
                filterElement.innerHTML += `<option value="${value.value}">${value.label}</option>`;
            });
            
        } else if (attr.field_type === 'boolean') {
            // Dropdown for boolean type
            filterElement = document.createElement('select');
            filterElement.className = 'form-select form-select-sm';
            filterElement.id = `attr-filter-${attr.id}`;
            filterElement.innerHTML = `
                <option value="">Tất cả ${attr.name}</option>
                <option value="true">Có</option>
                <option value="false">Không</option>
            `;
            
        } else if (attr.field_type === 'char') {
            // Text input for char type
            filterElement = document.createElement('input');
            filterElement.type = 'text';
            filterElement.className = 'form-control form-control-sm';
            filterElement.id = `attr-filter-${attr.id}`;
            filterElement.placeholder = `Tìm ${attr.name}...`;
            
        } else if (attr.field_type === 'float' || attr.field_type === 'integer') {
            // Number input for numeric types
            filterElement = document.createElement('input');
            filterElement.type = 'number';
            filterElement.className = 'form-control form-control-sm';
            filterElement.id = `attr-filter-${attr.id}`;
            filterElement.placeholder = `${attr.name}...`;
            if (attr.field_type === 'float') {
                filterElement.step = '0.01';
            }
        }
        
        if (filterElement) {
            // Add event listener
            if (filterElement.tagName === 'SELECT') {
                filterElement.addEventListener('change', function() {
                    applyAttributeFilters();
                });
            } else {
                // For input fields, use debounced input
                let timeout;
                filterElement.addEventListener('input', function() {
                    clearTimeout(timeout);
                    timeout = setTimeout(() => {
                        applyAttributeFilters();
                    }, 500);
                });
            }
            
            colDiv.appendChild(filterElement);
            filtersRow.appendChild(colDiv);
        }
    });
    
    if (filtersRow.children.length > 0) {
        const titleDiv = document.createElement('div');
        titleDiv.className = 'mb-2';
        titleDiv.innerHTML = '<small class="text-muted"><i class="fas fa-filter me-1"></i>Lọc theo thuộc tính:</small>';
        
        container.appendChild(titleDiv);
        container.appendChild(filtersRow);
    }
}

function renderSelectableAttributeFilters(container, attributes) {
    const selectableRow = document.createElement('div');
    selectableRow.className = 'row g-2 align-items-center';
    
    // Attribute selector
    const selectorCol = document.createElement('div');
    selectorCol.className = 'col-md-3';
    
    const attrSelect = document.createElement('select');
    attrSelect.className = 'form-select form-select-sm';
    attrSelect.id = 'attributeSelector';
    attrSelect.innerHTML = '<option value="">Chọn thuộc tính để lọc</option>';
    
    attributes.forEach(attr => {
        attrSelect.innerHTML += `<option value="${attr.id}" data-type="${attr.field_type}">${attr.name} (${getFieldTypeLabel(attr.field_type)})</option>`;
    });
    
    // Value filter container (initially hidden)
    const valueCol = document.createElement('div');
    valueCol.className = 'col-md-3';
    valueCol.style.display = 'none';
    valueCol.id = 'valueFilterContainer';
    
    // Event listener for attribute selector
    attrSelect.addEventListener('change', function() {
        const selectedAttrId = this.value;
        const selectedOption = this.options[this.selectedIndex];
        const attrType = selectedOption.getAttribute('data-type');
        const valueContainer = document.getElementById('valueFilterContainer');
        
        // Clear previous filter
        valueContainer.innerHTML = '';
        
        if (selectedAttrId) {
            const selectedAttr = attributes.find(attr => attr.id.toString() === selectedAttrId);
            if (selectedAttr) {
                let filterElement;
                
                if (selectedAttr.field_type === 'selection' && selectedAttr.values.length > 0) {
                    // Dropdown for selection
                    filterElement = document.createElement('select');
                    filterElement.className = 'form-select form-select-sm';
                    filterElement.id = 'valueFilter';
                    filterElement.innerHTML = `<option value="">Tất cả ${selectedAttr.name}</option>`;
                    selectedAttr.values.forEach(value => {
                        filterElement.innerHTML += `<option value="${value.value}">${value.label}</option>`;
                    });
                    
                } else if (selectedAttr.field_type === 'boolean') {
                    // Dropdown for boolean
                    filterElement = document.createElement('select');
                    filterElement.className = 'form-select form-select-sm';
                    filterElement.id = 'valueFilter';
                    filterElement.innerHTML = `
                        <option value="">Tất cả ${selectedAttr.name}</option>
                        <option value="true">Có</option>
                        <option value="false">Không</option>
                    `;
                    
                } else if (selectedAttr.field_type === 'char') {
                    // Text input for char
                    filterElement = document.createElement('input');
                    filterElement.type = 'text';
                    filterElement.className = 'form-control form-control-sm';
                    filterElement.id = 'valueFilter';
                    filterElement.placeholder = `Tìm ${selectedAttr.name}...`;
                    
                } else if (selectedAttr.field_type === 'float' || selectedAttr.field_type === 'integer') {
                    // Number input for numeric
                    filterElement = document.createElement('input');
                    filterElement.type = 'number';
                    filterElement.className = 'form-control form-control-sm';
                    filterElement.id = 'valueFilter';
                    filterElement.placeholder = `${selectedAttr.name}...`;
                    if (selectedAttr.field_type === 'float') {
                        filterElement.step = '0.01';
                    }
                }
                
                if (filterElement) {
                    // Add event listener
                    if (filterElement.tagName === 'SELECT') {
                        filterElement.addEventListener('change', function() {
                            applyAttributeFilters();
                        });
                    } else {
                        let timeout;
                        filterElement.addEventListener('input', function() {
                            clearTimeout(timeout);
                            timeout = setTimeout(() => {
                                applyAttributeFilters();
                            }, 500);
                        });
                    }
                    
                    valueContainer.appendChild(filterElement);
                    valueContainer.style.display = 'block';
                }
            }
        } else {
            valueContainer.style.display = 'none';
            applyAttributeFilters(); // Clear filters
        }
    });
    
    selectorCol.appendChild(attrSelect);
    selectableRow.appendChild(selectorCol);
    selectableRow.appendChild(valueCol);
    
    const titleDiv = document.createElement('div');
    titleDiv.className = 'mb-2';
    titleDiv.innerHTML = '<small class="text-muted"><i class="fas fa-filter me-1"></i>Lọc theo thuộc tính:</small>';
    
    container.appendChild(titleDiv);
    container.appendChild(selectableRow);
}

function applyAttributeFilters() {
    // Collect all filter values
    const filters = collectAttributeFilters();
    
    // Get other search parameters
    const search = document.getElementById('templateSearch').value;
    const categoryId = document.getElementById('templateCategoryFilter').value;
    
    // Apply filters to product templates
    loadProductTemplatesWithFilters(1, search, categoryId, filters);
}

function collectAttributeFilters() {
    const filters = {};
    const container = document.getElementById('attributeFiltersContainer');
    if (!container) return filters;
    
    // Check if we're using direct filters (<=5 attributes) or selectable filters (>5)
    const directFilters = container.querySelectorAll('[id^="attr-filter-"]');
    
    if (directFilters.length > 0) {
        // Direct filters mode
        directFilters.forEach(filter => {
            const attrId = filter.id.replace('attr-filter-', '');
            const value = filter.value.trim();
            if (value) {
                filters[attrId] = value;
            }
        });
    } else {
        // Selectable filter mode
        const attributeSelector = document.getElementById('attributeSelector');
        const valueFilter = document.getElementById('valueFilter');
        
        if (attributeSelector && valueFilter && attributeSelector.value) {
            const attrId = attributeSelector.value;
            const value = valueFilter.value ? valueFilter.value.trim() : '';
            if (value) {
                filters[attrId] = value;
            }
        }
    }
    
    return filters;
}

// ================================
// EVENT HANDLERS
// ================================

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tabs
    const tabs = document.querySelectorAll('#mainTabs .nav-link');
    tabs.forEach(tab => {
        tab.addEventListener('shown.bs.tab', function(e) {
            const target = e.target.getAttribute('href');
            switch (target) {
                case '#attribute-groups':
                    loadAttributeGroups();
                    break;
                case '#gold-attributes':
                    loadGoldAttributes();
                    loadAttributeGroupsForFilter();
                    break;
                case '#product-templates':
                    loadProductTemplates();
                    loadCategoriesForFilter();
                    loadAttributesForProductTemplateFilters();
                    break;
            }
        });
    });
    
    // Search handlers with debounce
    let searchTimeout;
    
    // Group search
    document.getElementById('groupSearch').addEventListener('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            loadAttributeGroups(1, this.value);
        }, 500);
    });
    
    // Attribute search
    document.getElementById('attrSearch').addEventListener('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            const groupId = document.getElementById('attrGroupFilter').value;
            const fieldType = document.getElementById('attrTypeFilter').value;
            loadGoldAttributes(1, this.value, groupId, fieldType);
        }, 500);
    });
    
    // Attribute filters
    document.getElementById('attrGroupFilter').addEventListener('change', function() {
        const search = document.getElementById('attrSearch').value;
        const fieldType = document.getElementById('attrTypeFilter').value;
        loadGoldAttributes(1, search, this.value, fieldType);
    });
    
    document.getElementById('attrTypeFilter').addEventListener('change', function() {
        const search = document.getElementById('attrSearch').value;
        const groupId = document.getElementById('attrGroupFilter').value;
        loadGoldAttributes(1, search, groupId, this.value);
    });
    
    // Template search
    document.getElementById('templateSearch').addEventListener('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            applyAttributeFilters();
        }, 500);
    });
    
    // Template category filter
    document.getElementById('templateCategoryFilter').addEventListener('change', function() {
        applyAttributeFilters();
    });
    
    // Field type change handler for gold attributes
    document.getElementById('attrFieldType').addEventListener('change', toggleSelectionOptions);
    
    // Load initial data
    loadAttributeGroups();
    loadAttributeGroupsForFilter();
    loadCategoriesForFilter();
    loadAttributesForProductTemplateFilters();
});
