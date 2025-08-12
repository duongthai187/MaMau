// JavaScript cho quản lý mã mẫu sản phẩm

let productTemplates = [];
let categories = [];
let goldAttributes = [];
let currentPage = 1;
let totalPages = 1;
let isLoading = false;
let selectedTemplates = new Set();
let currentView = 'card'; // 'card' or 'table'

// Load dữ liệu khi trang được tải
document.addEventListener('DOMContentLoaded', function() {
    // Prevent multiple initializations
    if (window.productTemplatesInitialized) {
        return;
    }
    window.productTemplatesInitialized = true;
    
    loadCategories();
    loadGoldAttributes();
    loadProductTemplates();
    loadStatistics();
    
    // Xử lý form submit
    const productForm = document.getElementById('productForm');
    if (productForm) {
        productForm.addEventListener('submit', function(e) {
            e.preventDefault();
            saveProductTemplate();
        });
    }
    
    // Search input với debounce
    let searchTimeout;
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                currentPage = 1;
                loadProductTemplates();
            }, 500);
        });
    }
});

// ================================
// LOAD DATA FUNCTIONS
// ================================

async function loadCategories() {
    try {
        const response = await fetch('/api/options/categories');
        const data = await response.json();
        
        if (data.success) {
            categories = data.data;
            renderCategoryOptions();
        }
    } catch (error) {
        console.error('Error loading categories:', error);
    }
}

async function loadGoldAttributes() {
    try {
        const response = await fetch('/api/attributes');
        const data = await response.json();
        
        if (data.success) {
            goldAttributes = data.data;
        }
    } catch (error) {
        console.error('Error loading gold attributes:', error);
    }
}

async function loadProductTemplates() {
    if (isLoading) return;
    
    try {
        isLoading = true;
        showLoading(true);
        
        const params = new URLSearchParams({
            page: currentPage,
            limit: 12
        });
        
        // Add filters
        const search = document.getElementById('searchInput').value;
        if (search) params.append('search', search);
        
        const categ_id = document.getElementById('categoryFilter').value;
        if (categ_id) params.append('categ_id', categ_id);
        
        const active = document.getElementById('statusFilter').value;
        if (active) params.append('active', active);
        
        const response = await fetch(`/api/product-templates?${params}`);
        const data = await response.json();
        
        if (data.success) {
            productTemplates = data.data;
            totalPages = Math.ceil(data.total / 12);
            renderProductTemplates();
            renderPagination();
        } else {
            showAlert('Lỗi khi tải dữ liệu: ' + data.error, 'danger');
        }
    } catch (error) {
        console.error('Error loading product templates:', error);
        showAlert('Lỗi kết nối: ' + error.message, 'danger');
    } finally {
        isLoading = false;
        showLoading(false);
    }
}

async function loadStatistics() {
    try {
        const response = await fetch('/api/product-templates/statistics');
        const data = await response.json();
        
        if (data.success) {
            const stats = data.data;
            document.getElementById('totalTemplates').textContent = stats.total_templates;
            document.getElementById('activeTemplates').textContent = stats.active_templates;
            document.getElementById('withGoldAttributes').textContent = stats.with_gold_attributes;
            document.getElementById('avgPrice').textContent = formatCurrency(stats.avg_price);
        }
    } catch (error) {
        console.error('Error loading statistics:', error);
    }
}

// ================================
// RENDER FUNCTIONS
// ================================

function renderCategoryOptions() {
    const categoryFilter = document.getElementById('categoryFilter');
    const productCategory = document.getElementById('productCategory');
    
    // Clear existing options (keep "Tất cả" for filter)
    categoryFilter.innerHTML = '<option value="">Tất cả</option>';
    productCategory.innerHTML = '<option value="">Chọn danh mục</option>';
    
    categories.forEach(category => {
        const option1 = document.createElement('option');
        option1.value = category.id;
        option1.textContent = category.complete_name || category.name;
        categoryFilter.appendChild(option1);
        
        const option2 = document.createElement('option');
        option2.value = category.id;
        option2.textContent = category.complete_name || category.name;
        productCategory.appendChild(option2);
    });
}

function renderProductTemplates() {
    const container = document.getElementById('productContainer');
    container.innerHTML = '';
    
    if (currentView === 'card') {
        renderProductCards();
    } else {
        renderProductTable();
    }
}

function renderProductCards() {
    const container = document.getElementById('productContainer');
    
    productTemplates.forEach(product => {
        const col = document.createElement('div');
        col.className = 'col-md-4 col-lg-3 mb-4';
        
        const statusClass = product.active ? 'success' : 'secondary';
        const statusText = product.active ? 'Hoạt động' : 'Vô hiệu';
        
        const typeLabels = {
            'product': 'Có tồn kho',
            'consu': 'Tiêu hao', 
            'service': 'Dịch vụ'
        };
        
        col.innerHTML = `
            <div class="product-card h-100">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" 
                                   onchange="toggleSelection(${product.id})" 
                                   ${selectedTemplates.has(product.id) ? 'checked' : ''}>
                        </div>
                        <span class="badge bg-${statusClass} status-badge">${statusText}</span>
                    </div>
                    
                    <h6 class="card-title text-truncate" title="${product.name}">${product.name}</h6>
                    
                    <div class="mb-2">
                        <small class="text-muted">Mã: ${product.default_code || 'N/A'}</small><br>
                        <small class="text-muted">Danh mục: ${product.categ_name || 'N/A'}</small><br>
                        <small class="text-muted">Loại: ${typeLabels[product.type] || product.type}</small>
                    </div>
                    
                    <div class="price-info mb-3">
                        <div class="price-badge badge fs-6">
                            ${formatCurrency(product.list_price)}
                        </div>
                        <small class="text-muted d-block">Giá vốn: ${formatCurrency(product.standard_price)}</small>
                    </div>
                    
                    <div class="d-flex gap-1">
                        <button class="btn btn-sm btn-outline-primary" onclick="editProductTemplate(${product.id})" title="Sửa">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-info" onclick="viewGoldAttributes(${product.id})" title="Thuộc tính vàng">
                            <i class="fas fa-gem"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-secondary" onclick="duplicateProductTemplate(${product.id})" title="Nhân bản">
                            <i class="fas fa-copy"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger" onclick="deleteProductTemplate(${product.id})" title="Xóa">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        container.appendChild(col);
    });
    
    if (productTemplates.length === 0) {
        container.innerHTML = `
            <div class="col-12">
                <div class="text-center py-5">
                    <i class="fas fa-cube fa-3x text-muted mb-3"></i>
                    <h5 class="text-muted">Không có mã mẫu nào</h5>
                    <p class="text-muted">Hãy thêm mã mẫu đầu tiên của bạn</p>
                    <button class="btn btn-primary" onclick="showCreateForm()">
                        <i class="fas fa-plus"></i> Thêm mã mẫu
                    </button>
                </div>
            </div>
        `;
    }
}

function renderProductTable() {
    const container = document.getElementById('productContainer');
    
    const tableHtml = `
        <div class="col-12">
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead class="table-light">
                        <tr>
                            <th width="40">
                                <input type="checkbox" onchange="toggleSelectAll(this)">
                            </th>
                            <th>Tên</th>
                            <th>Mã</th>
                            <th>Danh mục</th>
                            <th>Loại</th>
                            <th>Giá bán</th>
                            <th>Trạng thái</th>
                            <th width="150">Thao tác</th>
                        </tr>
                    </thead>
                    <tbody id="productTableBody">
                    </tbody>
                </table>
            </div>
        </div>
    `;
    
    container.innerHTML = tableHtml;
    
    const tbody = document.getElementById('productTableBody');
    
    productTemplates.forEach(product => {
        const row = document.createElement('tr');
        
        const statusClass = product.active ? 'success' : 'secondary';
        const statusText = product.active ? 'Hoạt động' : 'Vô hiệu';
        
        const typeLabels = {
            'product': 'Có tồn kho',
            'consu': 'Tiêu hao',
            'service': 'Dịch vụ'
        };
        
        row.innerHTML = `
            <td>
                <input type="checkbox" onchange="toggleSelection(${product.id})" 
                       ${selectedTemplates.has(product.id) ? 'checked' : ''}>
            </td>
            <td>
                <div class="fw-bold">${product.name}</div>
            </td>
            <td>${product.default_code || '-'}</td>
            <td>${product.categ_name || '-'}</td>
            <td>${typeLabels[product.type] || product.type}</td>
            <td>${formatCurrency(product.list_price)}</td>
            <td>
                <span class="badge bg-${statusClass}">${statusText}</span>
            </td>
            <td>
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-outline-primary" onclick="editProductTemplate(${product.id})" title="Sửa">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-outline-info" onclick="viewGoldAttributes(${product.id})" title="Thuộc tính vàng">
                        <i class="fas fa-gem"></i>
                    </button>
                    <button class="btn btn-outline-danger" onclick="deleteProductTemplate(${product.id})" title="Xóa">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        `;
        
        tbody.appendChild(row);
    });
}

function renderPagination() {
    const nav = document.getElementById('paginationNav');
    
    if (totalPages <= 1) {
        nav.innerHTML = '';
        return;
    }
    
    let paginationHtml = '<ul class="pagination justify-content-center">';
    
    // Previous button
    paginationHtml += `
        <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="changePage(${currentPage - 1})">
                <i class="fas fa-chevron-left"></i>
            </a>
        </li>
    `;
    
    // Page numbers
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);
    
    if (startPage > 1) {
        paginationHtml += '<li class="page-item"><a class="page-link" href="#" onclick="changePage(1)">1</a></li>';
        if (startPage > 2) {
            paginationHtml += '<li class="page-item disabled"><span class="page-link">...</span></li>';
        }
    }
    
    for (let i = startPage; i <= endPage; i++) {
        paginationHtml += `
            <li class="page-item ${i === currentPage ? 'active' : ''}">
                <a class="page-link" href="#" onclick="changePage(${i})">${i}</a>
            </li>
        `;
    }
    
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            paginationHtml += '<li class="page-item disabled"><span class="page-link">...</span></li>';
        }
        paginationHtml += `<li class="page-item"><a class="page-link" href="#" onclick="changePage(${totalPages})">${totalPages}</a></li>`;
    }
    
    // Next button
    paginationHtml += `
        <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="changePage(${currentPage + 1})">
                <i class="fas fa-chevron-right"></i>
            </a>
        </li>
    `;
    
    paginationHtml += '</ul>';
    nav.innerHTML = paginationHtml;
}

// ================================
// ACTION FUNCTIONS
// ================================

function showCreateForm() {
    document.getElementById('modalTitle').textContent = 'Thêm mã mẫu mới';
    document.getElementById('productForm').reset();
    document.getElementById('productId').value = '';
    clearGoldAttributes();
    
    const modal = new bootstrap.Modal(document.getElementById('productModal'));
    modal.show();
}

async function editProductTemplate(id) {
    try {
        showLoading(true);
        
        const response = await fetch(`/api/product-templates/${id}`);
        const data = await response.json();
        
        if (data.success) {
            const product = data.data;
            
            document.getElementById('modalTitle').textContent = 'Chỉnh sửa mã mẫu';
            document.getElementById('productId').value = product.id;
            document.getElementById('productName').value = product.name;
            document.getElementById('defaultCode').value = product.default_code || '';
            document.getElementById('productCategory').value = product.categ_id ? product.categ_id[0] : '';
            document.getElementById('productType').value = product.type || 'product';
            document.getElementById('listPrice').value = product.list_price || 0;
            document.getElementById('standardPrice').value = product.standard_price || 0;
            document.getElementById('barcode').value = product.barcode || '';
            document.getElementById('weight').value = product.weight || '';
            document.getElementById('descriptionSale').value = product.description_sale || '';
            
            // Load gold attributes for this product
            await loadProductGoldAttributes(id);
            
            const modal = new bootstrap.Modal(document.getElementById('productModal'));
            modal.show();
        } else {
            showAlert('Lỗi khi tải thông tin sản phẩm: ' + data.error, 'danger');
        }
    } catch (error) {
        showAlert('Lỗi kết nối: ' + error.message, 'danger');
    } finally {
        showLoading(false);
    }
}

async function saveProductTemplate() {
    try {
        showLoading(true);
        
        const productId = document.getElementById('productId').value;
        const isEdit = !!productId;
        
        const formData = {
            name: document.getElementById('productName').value,
            default_code: document.getElementById('defaultCode').value,
            categ_id: parseInt(document.getElementById('productCategory').value) || null,
            type: document.getElementById('productType').value,
            list_price: parseFloat(document.getElementById('listPrice').value) || 0,
            standard_price: parseFloat(document.getElementById('standardPrice').value) || 0,
            barcode: document.getElementById('barcode').value,
            weight: parseFloat(document.getElementById('weight').value) || null,
            description_sale: document.getElementById('descriptionSale').value
        };
        
        const url = isEdit ? `/api/product-templates/${productId}` : '/api/product-templates';
        const method = isEdit ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert(isEdit ? 'Cập nhật thành công!' : 'Tạo mới thành công!', 'success');
            
            // Robust modal hiding
            try {
                const modal = bootstrap.Modal.getInstance(document.getElementById('productModal'));
                if (modal) {
                    modal.hide();
                }
            } catch (e) {
                console.warn('Error hiding product modal:', e);
                // Fallback
                document.getElementById('productModal').style.display = 'none';
                document.body.classList.remove('modal-open');
                const backdrop = document.querySelector('.modal-backdrop');
                if (backdrop) backdrop.remove();
            }
            
            loadProductTemplates();
            loadStatistics();
        } else {
            showAlert('Lỗi khi lưu: ' + data.error, 'danger');
        }
    } catch (error) {
        showAlert('Lỗi kết nối: ' + error.message, 'danger');
    } finally {
        showLoading(false);
    }
}

async function deleteProductTemplate(id) {
    if (!confirm('Bạn có chắc chắn muốn xóa mã mẫu này?')) {
        return;
    }
    
    try {
        showLoading(true);
        
        const response = await fetch(`/api/product-templates/${id}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert('Xóa thành công!', 'success');
            loadProductTemplates();
            loadStatistics();
        } else {
            showAlert('Lỗi khi xóa: ' + data.error, 'danger');
        }
    } catch (error) {
        showAlert('Lỗi kết nối: ' + error.message, 'danger');
    } finally {
        showLoading(false);
    }
}

// ================================
// GOLD ATTRIBUTES FUNCTIONS
// ================================

async function loadProductGoldAttributes(productId) {
    try {
        const response = await fetch(`/api/product-templates/${productId}/gold-attributes`);
        const data = await response.json();
        
        if (data.success) {
            renderGoldAttributesForm(data.data.gold_attributes, data.data.available_attributes);
        }
    } catch (error) {
        console.error('Error loading gold attributes:', error);
    }
}

function renderGoldAttributesForm(goldAttributes = [], availableAttributes = []) {
    const container = document.getElementById('goldAttributesContainer');
    container.innerHTML = '';
    
    goldAttributes.forEach(attr => {
        addGoldAttributeRow(attr);
    });
}

function addGoldAttribute() {
    addGoldAttributeRow();
}

function addGoldAttributeRow(existingValue = null) {
    const container = document.getElementById('goldAttributesContainer');
    const row = document.createElement('div');
    row.className = 'row g-2 mb-2 gold-attribute-row';
    
    row.innerHTML = `
        <div class="col-md-4">
            <select class="form-select gold-attribute-select">
                <option value="">Chọn thuộc tính</option>
                ${goldAttributes.map(attr => `
                    <option value="${attr.id}" data-type="${attr.field_type}" 
                            ${existingValue && existingValue.attribute_id === attr.id ? 'selected' : ''}>
                        ${attr.display_name || attr.name}
                    </option>
                `).join('')}
            </select>
        </div>
        <div class="col-md-6">
            <input type="text" class="form-control gold-attribute-value" 
                   placeholder="Nhập giá trị..." 
                   value="${existingValue ? existingValue.value || '' : ''}">
        </div>
        <div class="col-md-2">
            <button type="button" class="btn btn-outline-danger btn-sm" onclick="removeGoldAttributeRow(this)">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    container.appendChild(row);
}

function removeGoldAttributeRow(button) {
    button.closest('.gold-attribute-row').remove();
}

function clearGoldAttributes() {
    document.getElementById('goldAttributesContainer').innerHTML = '';
}

async function viewGoldAttributes(productId) {
    try {
        const response = await fetch(`/api/product-templates/${productId}/gold-attributes`);
        const data = await response.json();
        
        if (data.success) {
            // Show gold attributes in a modal or alert
            const attributes = data.data.gold_attributes;
            if (attributes.length === 0) {
                showAlert('Sản phẩm này chưa có thuộc tính vàng nào', 'info');
            } else {
                let message = 'Thuộc tính vàng:\n';
                attributes.forEach(attr => {
                    message += `- ${attr.attribute_name}: ${attr.value}\n`;
                });
                alert(message);
            }
        }
    } catch (error) {
        showAlert('Lỗi khi tải thuộc tính vàng: ' + error.message, 'danger');
    }
}

// ================================
// UTILITY FUNCTIONS
// ================================

function formatCurrency(amount) {
    return new Intl.NumberFormat('vi-VN', {
        style: 'currency',
        currency: 'VND'
    }).format(amount || 0);
}

function showLoading(show) {
    const modal = document.getElementById('loadingModal');
    if (show) {
        // Đảm bảo modal được show
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    } else {
        // Robust hide với multiple fallback methods
        try {
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) {
                bsModal.hide();
            }
        } catch (e) {
            console.warn('Error hiding modal:', e);
        }
        
        // Fallback 1: Force hide với timeout
        setTimeout(() => {
            try {
                const instance = bootstrap.Modal.getInstance(modal);
                if (instance) {
                    instance.hide();
                }
                // Fallback 2: Remove modal classes directly
                modal.classList.remove('show');
                modal.style.display = 'none';
                document.body.classList.remove('modal-open');
                
                // Fallback 3: Remove backdrop
                const backdrop = document.querySelector('.modal-backdrop');
                if (backdrop) {
                    backdrop.remove();
                }
            } catch (e) {
                console.warn('Fallback hide failed:', e);
            }
        }, 100);
    }
}

function showAlert(message, type) {
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x`;
    alert.style.zIndex = '9999';
    alert.style.marginTop = '20px';
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alert);
    
    setTimeout(() => {
        if (alert.parentNode) {
            alert.remove();
        }
    }, 5000);
}

function changePage(page) {
    if (page < 1 || page > totalPages || page === currentPage) return;
    currentPage = page;
    loadProductTemplates();
}

function applyFilters() {
    currentPage = 1;
    loadProductTemplates();
}

function clearFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('categoryFilter').value = '';
    document.getElementById('typeFilter').value = '';
    document.getElementById('statusFilter').value = '';
    currentPage = 1;
    loadProductTemplates();
}

function toggleView() {
    currentView = currentView === 'card' ? 'table' : 'card';
    const icon = document.getElementById('viewToggleIcon');
    icon.className = currentView === 'card' ? 'fas fa-list' : 'fas fa-th-large';
    renderProductTemplates();
}

// ================================
// SELECTION & BULK ACTIONS
// ================================

function toggleSelection(id) {
    if (selectedTemplates.has(id)) {
        selectedTemplates.delete(id);
    } else {
        selectedTemplates.add(id);
    }
    updateBulkActions();
}

function toggleSelectAll(checkbox) {
    if (checkbox.checked) {
        productTemplates.forEach(product => selectedTemplates.add(product.id));
    } else {
        selectedTemplates.clear();
    }
    
    // Update all checkboxes
    document.querySelectorAll('input[type="checkbox"]').forEach(cb => {
        if (cb !== checkbox) {
            cb.checked = checkbox.checked;
        }
    });
    
    updateBulkActions();
}

function updateBulkActions() {
    const bulkActions = document.getElementById('bulkActions');
    const selectedCount = document.getElementById('selectedCount');
    
    if (selectedTemplates.size > 0) {
        bulkActions.style.display = 'block';
        selectedCount.textContent = selectedTemplates.size;
    } else {
        bulkActions.style.display = 'none';
    }
}

function clearSelection() {
    selectedTemplates.clear();
    document.querySelectorAll('input[type="checkbox"]').forEach(cb => {
        cb.checked = false;
    });
    updateBulkActions();
}

async function bulkActivate() {
    await performBulkAction('activate', 'kích hoạt');
}

async function bulkDeactivate() {
    await performBulkAction('deactivate', 'vô hiệu hóa');
}

async function bulkDelete() {
    if (!confirm(`Bạn có chắc chắn muốn xóa ${selectedTemplates.size} mã mẫu đã chọn?`)) {
        return;
    }
    await performBulkAction('delete', 'xóa');
}

async function performBulkAction(action, actionText) {
    try {
        showLoading(true);
        
        const response = await fetch('/api/product-templates/bulk-action', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                template_ids: Array.from(selectedTemplates),
                action: action
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert(data.message, 'success');
            clearSelection();
            loadProductTemplates();
            loadStatistics();
        } else {
            showAlert('Lỗi khi ' + actionText + ': ' + data.error, 'danger');
        }
    } catch (error) {
        showAlert('Lỗi kết nối: ' + error.message, 'danger');
    } finally {
        showLoading(false);
    }
}

// ================================
// ADDITIONAL FEATURES
// ================================

function duplicateProductTemplate(id) {
    // TODO: Implement duplicate functionality
    showAlert('Tính năng nhân bản sẽ được phát triển sau', 'info');
}

function showImportModal() {
    // TODO: Implement import functionality
    showAlert('Tính năng import sẽ được phát triển sau', 'info');
}

function exportTemplates() {
    // TODO: Implement export functionality
    showAlert('Tính năng export sẽ được phát triển sau', 'info');
}
