// File: website/js/admin-integrated.js
// Complete Integrated Admin Panel with Wreath Editor and JSON Merger

let wreathsData = [];
let editingWreath = null;
let isLoggedIn = false;
let hasUnsavedChanges = false;

// Workflow state
let workflowState = {
    loaded: false,
    imported: false,
    edited: false,
    exported: false
};

// DOM elements
const loginContainer = document.getElementById('loginContainer');
const adminContainer = document.getElementById('adminContainer');
const adminPassword = document.getElementById('adminPassword');
const loginButton = document.getElementById('loginButton');
const loginError = document.getElementById('loginError');
const logoutButton = document.getElementById('logoutButton');

// Status elements
const saveStatus = document.getElementById('saveStatus');
const statusSection = document.getElementById('statusSection');
const statusContent = document.getElementById('statusContent');
const unsavedIndicator = document.getElementById('unsavedIndicator');

// Admin controls
const manualLoadBtn = document.getElementById('manualLoadBtn');
const importJsonFiles = document.getElementById('importJsonFiles');
const addWreathBtn = document.getElementById('addWreathBtn');
const exportJsonBtn = document.getElementById('exportJsonBtn');
const showSoldItems = document.getElementById('showSoldItems');
const itemCount = document.getElementById('itemCount');
const wreathTableBody = document.getElementById('wreathTableBody');

// Edit modal elements
const editModal = document.getElementById('editModal');
const closeEditModal = document.getElementById('closeEditModal');
const imageGrid = document.getElementById('imageGrid');
const newImageUrl = document.getElementById('newImageUrl');
const addImageBtn = document.getElementById('addImageBtn');

// Form elements
const editTitle = document.getElementById('editTitle');
const editPrice = document.getElementById('editPrice');
const editAvailable = document.getElementById('editAvailable');
const editSold = document.getElementById('editSold');
const editDateAdded = document.getElementById('editDateAdded');
const editDescription = document.getElementById('editDescription');
const editHashtags = document.getElementById('editHashtags');
const editPoshmark = document.getElementById('editPoshmark');
const editFacebook = document.getElementById('editFacebook');
const editMercari = document.getElementById('editMercari');
const editOther = document.getElementById('editOther');

const cancelEditBtn = document.getElementById('cancelEditBtn');
const saveEditBtn = document.getElementById('saveEditBtn');
const deleteWreathBtn = document.getElementById('deleteWreathBtn');

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    checkLoginStatus();
    setupEventListeners();
});

// Check if user is logged in
function checkLoginStatus() {
    const sessionToken = localStorage.getItem('twinfolks_session');
    
    if (sessionToken) {
        // Check if session is still valid (8 hours)
        const sessionData = sessionToken.split('_');
        if (sessionData.length >= 2) {
            const timestamp = parseInt(sessionData[1]);
            const sessionAge = Date.now() - timestamp;
            
            // Session expires after 8 hours
            if (sessionAge < 8 * 60 * 60 * 1000) {
                showAdminPanel();
                return;
            }
        }
        localStorage.removeItem('twinfolks_session');
    }
    
    showLoginScreen();
}

// Show login screen
function showLoginScreen() {
    loginContainer.style.display = 'flex';
    adminContainer.classList.remove('active');
    isLoggedIn = false;
}

// Show admin panel
function showAdminPanel() {
    loginContainer.style.display = 'none';
    adminContainer.classList.add('active');
    isLoggedIn = true;
    
    // Auto-load current data
    setTimeout(() => {
        loadCurrentWreathsData();
    }, 500);
    
    updateWorkflowSteps();
}

// Setup event listeners
function setupEventListeners() {
    // Login
    loginButton.addEventListener('click', handleLogin);
    adminPassword.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleLogin();
    });
    logoutButton.addEventListener('click', handleLogout);
    
    // Workflow buttons
    manualLoadBtn.addEventListener('click', loadCurrentWreathsData);
    importJsonFiles.addEventListener('change', handleImportFiles);
    addWreathBtn.addEventListener('click', addNewWreath);
    exportJsonBtn.addEventListener('click', exportWreaths);
    
    // Table filters
    showSoldItems.addEventListener('change', displayWreaths);
    
    // Modal
    closeEditModal.addEventListener('click', closeEditModalHandler);
    cancelEditBtn.addEventListener('click', closeEditModalHandler);
    saveEditBtn.addEventListener('click', saveEdit);
    deleteWreathBtn.addEventListener('click', deleteCurrentWreath);
    addImageBtn.addEventListener('click', addImage);
    
    // Add image on Enter
    newImageUrl.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') addImage();
    });
    
    // Close modal when clicking outside
    editModal.addEventListener('click', (e) => {
        if (e.target === editModal) closeEditModalHandler();
    });
    
    // Unsaved changes warning
    window.addEventListener('beforeunload', (e) => {
        if (hasUnsavedChanges) {
            e.preventDefault();
            e.returnValue = '';
        }
    });
}

// Handle login
async function handleLogin() {
    const password = adminPassword.value.trim();
    
    if (!password) {
        showLoginError('Please enter a password');
        return;
    }
    
    // Show loading state
    loginButton.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Verifying...';
    loginButton.disabled = true;
    loginError.classList.add('hidden');
    
    try {
        const response = await fetch('/.netlify/functions/verify-admin', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ password: password })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Store session token if provided
            if (result.sessionToken) {
                localStorage.setItem('twinfolks_session', result.sessionToken);
            }
            
            // Clear password field
            adminPassword.value = '';
            
            // Show admin panel
            showAdminPanel();
        } else {
            showLoginError('Invalid password. Please try again.');
        }
    } catch (error) {
        console.error('Login error:', error);
        showLoginError('Login failed. Please check your connection and try again.');
    } finally {
        // Reset button
        loginButton.innerHTML = 'Login';
        loginButton.disabled = false;
    }
}

// Show login error
function showLoginError(message) {
    loginError.textContent = message;
    loginError.classList.remove('hidden');
}

// Handle logout
function handleLogout() {
    if (hasUnsavedChanges) {
        if (!confirm('You have unsaved changes. Are you sure you want to logout?')) {
            return;
        }
    }
    
    localStorage.removeItem('twinfolks_session');
    showLoginScreen();
    
    // Reset data
    wreathsData = [];
    hasUnsavedChanges = false;
    workflowState = {
        loaded: false,
        imported: false,
        edited: false,
        exported: false
    };
    updateWorkflowSteps();
}

// Load current wreaths data
async function loadCurrentWreathsData() {
    if (!isLoggedIn) return;
    
    const button = manualLoadBtn;
    const originalText = button.innerHTML;
    
    try {
        button.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i> Loading...';
        button.disabled = true;
        
        updateStatus('Loading current wreaths data...', 'loading');
        
        // Try to fetch current wreaths.json from multiple possible locations
        let response;
        const possiblePaths = ['wreaths.json', 'data/wreaths.json'];
        
        for (const path of possiblePaths) {
            try {
                response = await fetch(path);
                if (response.ok) break;
            } catch (e) {
                console.log(`Could not fetch from ${path}`);
            }
        }
        
        if (!response || !response.ok) {
            throw new Error('Could not find wreaths.json file');
        }
        
        const data = await response.json();
        wreathsData = data;
        
        // Update workflow state
        workflowState.loaded = true;
        updateWorkflowSteps();
        
        displayWreaths();
        updateItemCount();
        
        updateStatus(`Successfully loaded ${wreathsData.length} wreaths`, 'success');
        setSaveStatus('Data loaded successfully', 'success');
        
    } catch (error) {
        console.error('Load error:', error);
        updateStatus('Failed to load wreaths data. Starting with empty database.', 'warning');
        setSaveStatus('Load failed - starting fresh', 'warning');
        
        // Initialize empty database
        wreathsData = [];
        workflowState.loaded = true;
        updateWorkflowSteps();
        displayWreaths();
        updateItemCount();
    } finally {
        button.innerHTML = originalText;
        button.disabled = false;
    }
}

// Handle import files
function handleImportFiles(event) {
    const files = Array.from(event.target.files);
    if (files.length === 0) return;
    
    updateStatus('Importing JSON files...', 'loading');
    
    let processedFiles = 0;
    let successCount = 0;
    const results = [];
    
    files.forEach(file => {
        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const data = JSON.parse(e.target.result);
                const wreath = convertPoshmarkToWreath(data);
                
                // Check for duplicates
                const existingIndex = wreathsData.findIndex(w => w.id === wreath.id);
                if (existingIndex >= 0) {
                    wreathsData[existingIndex] = wreath;
                    results.push(`✅ Updated: ${file.name} - "${wreath.title}"`);
                } else {
                    wreathsData.unshift(wreath);
                    results.push(`✅ Added: ${file.name} - "${wreath.title}"`);
                }
                
                successCount++;
            } catch (error) {
                results.push(`❌ Error: ${file.name} - ${error.message}`);
            }
            
            processedFiles++;
            if (processedFiles === files.length) {
                // All files processed
                workflowState.imported = true;
                markUnsavedChanges();
                updateWorkflowSteps();
                displayWreaths();
                updateItemCount();
                
                updateStatus(`Import complete: ${successCount}/${files.length} files successful`, 'success');
                setSaveStatus(`Imported ${successCount} items`, 'success');
            }
        };
        reader.readAsText(file);
    });
    
    event.target.value = ''; // Reset file input
}

// Convert Poshmark JSON to wreath format
function convertPoshmarkToWreath(poshmarkData) {
    const id = poshmarkData.url ? poshmarkData.url.split('-').pop() : Date.now().toString() + Math.random().toString(36).substr(2, 9);
    
    return {
        id: id,
        title: poshmarkData.title || "Imported Wreath",
        localPrice: 0, // User needs to set this
        sold: false,
        hashtags: poshmarkData.tags ? poshmarkData.tags.map(tag => tag.toLowerCase().replace(/[^a-z0-9]/g, '')) : [],
        category: "holiday",
        dateAdded: new Date().toISOString().split('T')[0],
        description: poshmarkData.description || "",
        platforms: {
            poshmark: poshmarkData.url || "",
            fbMarketplace: "",
            mercari: "",
            other1: ""
        },
        images: poshmarkData.images || []
    };
}

// Display wreaths in table
function displayWreaths() {
    const filteredWreaths = showSoldItems.checked ? 
        wreathsData : wreathsData.filter(w => !w.sold);
    
    wreathTableBody.innerHTML = '';
    
    if (filteredWreaths.length === 0) {
        wreathTableBody.innerHTML = `
            <tr>
                <td colspan="7" class="px-4 py-8 text-center text-gray-500">
                    ${wreathsData.length === 0 ? 'No wreaths loaded. Import some JSON files or add wreaths manually.' : 'No items match current filter.'}
                </td>
            </tr>
        `;
        return;
    }
    
    filteredWreaths.forEach(wreath => {
        const row = createWreathRow(wreath);
        wreathTableBody.appendChild(row);
    });
}

// Create table row for wreath
function createWreathRow(wreath) {
    const row = document.createElement('tr');
    row.className = wreath.sold ? 'bg-gray-50' : '';
    
    const imageUrl = wreath.images && wreath.images.length > 0 ? wreath.images[0] : '';
    const platformIcons = createPlatformIcons(wreath.platforms);
    const hashtagsDisplay = wreath.hashtags ? wreath.hashtags.slice(0, 3).map(tag => `#${tag}`).join(' ') : '';
    
    row.innerHTML = `
        <td class="px-4 py-3">
            <input type="checkbox" ${wreath.sold ? 'checked' : ''} 
                   onchange="toggleSold('${wreath.id}')" class="rounded">
        </td>
        <td class="px-4 py-3">
            <div class="w-16 h-16 bg-gray-100 rounded">
                ${imageUrl ? `
                    <img src="${imageUrl}" alt="${wreath.title}" 
                         class="w-full h-full object-cover rounded"
                         onerror="this.style.display='none'">
                ` : ''}
            </div>
        </td>
        <td class="px-4 py-3">
            <div class="font-medium text-sm">${wreath.title}</div>
            <div class="text-xs text-gray-500">Added: ${wreath.dateAdded || 'Unknown'}</div>
        </td>
        <td class="px-4 py-3">
            <span class="text-sm font-medium">$${wreath.localPrice || 0}</span>
        </td>
        <td class="px-4 py-3">
            ${platformIcons}
        </td>
        <td class="px-4 py-3">
            <div class="text-xs text-gray-600">${hashtagsDisplay}</div>
            ${wreath.hashtags && wreath.hashtags.length > 3 ? 
                `<span class="text-xs text-gray-500">+${wreath.hashtags.length - 3}</span>` : ''}
        </td>
        <td class="px-4 py-3">
            <div class="flex items-center space-x-2">
                <button onclick="editWreath('${wreath.id}')" 
                        class="text-blue-600 hover:text-blue-800">
                    <i class="fas fa-edit"></i>
                </button>
            </div>
        </td>
    `;
    
    return row;
}

// Create platform icons
function createPlatformIcons(platforms) {
    if (!platforms) return '';
    
    let icons = '';
    if (platforms.poshmark) {
        icons += '<a href="' + platforms.poshmark + '" target="_blank" class="text-pink-600 hover:text-pink-800 mr-1"><i class="fas fa-external-link-alt text-sm"></i></a>';
    }
    if (platforms.fbMarketplace) {
        icons += '<a href="' + platforms.fbMarketplace + '" target="_blank" class="text-blue-600 hover:text-blue-800 mr-1"><i class="fas fa-external-link-alt text-sm"></i></a>';
    }
    if (platforms.mercari) {
        icons += '<a href="' + platforms.mercari + '" target="_blank" class="text-orange-600 hover:text-orange-800 mr-1"><i class="fas fa-external-link-alt text-sm"></i></a>';
    }
    if (platforms.other1) {
        icons += '<a href="' + platforms.other1 + '" target="_blank" class="text-gray-600 hover:text-gray-800 mr-1"><i class="fas fa-external-link-alt text-sm"></i></a>';
    }
    
    return icons;
}

// Toggle sold status
function toggleSold(wreathId) {
    const wreath = wreathsData.find(w => w.id === wreathId);
    if (wreath) {
        wreath.sold = !wreath.sold;
        markUnsavedChanges();
        displayWreaths();
        updateItemCount();
    }
}

// Edit wreath
function editWreath(wreathId) {
    const wreath = wreathsData.find(w => w.id === wreathId);
    if (wreath) {
        editingWreath = { ...wreath };
        populateEditForm();
        openEditModal();
    }
}

// Add new wreath
function addNewWreath() {
    editingWreath = {
        id: Date.now().toString(),
        title: "New Wreath",
        localPrice: 0,
        sold: false,
        hashtags: [],
        category: "holiday",
        dateAdded: new Date().toISOString().split('T')[0],
        description: "",
        platforms: {
            poshmark: "",
            fbMarketplace: "",
            mercari: "",
            other1: ""
        },
        images: []
    };
    populateEditForm();
    openEditModal();
}

// Populate edit form
function populateEditForm() {
    editTitle.value = editingWreath.title || '';
    editPrice.value = editingWreath.localPrice || 0;
    
    // Set sold status radio buttons
    if (editingWreath.sold) {
        editSold.checked = true;
    } else {
        editAvailable.checked = true;
    }
    
    editDateAdded.value = editingWreath.dateAdded || new Date().toISOString().split('T')[0];
    editDescription.value = editingWreath.description || '';
    editHashtags.value = editingWreath.hashtags ? editingWreath.hashtags.join(', ') : '';
    editPoshmark.value = editingWreath.platforms?.poshmark || '';
    editFacebook.value = editingWreath.platforms?.fbMarketplace || '';
    editMercari.value = editingWreath.platforms?.mercari || '';
    editOther.value = editingWreath.platforms?.other1 || '';
    
    displayEditImages();
}

// Display images in edit form
function displayEditImages() {
    imageGrid.innerHTML = '';
    
    if (editingWreath.images) {
        editingWreath.images.forEach((img, index) => {
            const imageDiv = document.createElement('div');
            imageDiv.className = 'relative';
            imageDiv.innerHTML = `
                <img src="${img}" alt="Image ${index + 1}" 
                     class="w-full h-24 object-cover rounded border"
                     onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                <div class="w-full h-24 bg-gray-200 rounded border hidden items-center justify-center text-xs text-gray-500">
                    Image not found
                </div>
                <button onclick="removeImage(${index})" 
                        class="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs hover:bg-red-600">
                    ×
                </button>
            `;
            imageGrid.appendChild(imageDiv);
        });
    }
    
    // Add "Add Image" placeholder
    const addDiv = document.createElement('div');
    addDiv.className = 'border-2 border-dashed border-gray-300 rounded-lg p-4 flex flex-col items-center justify-center h-24';
    addDiv.innerHTML = `
        <i class="fas fa-plus text-gray-400 mb-1"></i>
        <span class="text-xs text-gray-500">Add Image</span>
    `;
    imageGrid.appendChild(addDiv);
}

// Remove image
function removeImage(index) {
    if (editingWreath.images) {
        editingWreath.images.splice(index, 1);
        displayEditImages();
    }
}

// Add image
function addImage() {
    const url = newImageUrl.value.trim();
    if (url) {
        if (!editingWreath.images) {
            editingWreath.images = [];
        }
        editingWreath.images.push(url);
        newImageUrl.value = '';
        displayEditImages();
    }
}

// Open edit modal
function openEditModal() {
    editModal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

// Close edit modal
function closeEditModalHandler() {
    editModal.classList.remove('active');
    document.body.style.overflow = 'auto';
    editingWreath = null;
}

// Save edit
function saveEdit() {
    if (!editingWreath) return;
    
    // Update wreath data
    editingWreath.title = editTitle.value.trim();
    editingWreath.localPrice = parseInt(editPrice.value) || 0;
    editingWreath.sold = editSold.checked;
    editingWreath.dateAdded = editDateAdded.value;
    editingWreath.description = editDescription.value.trim();
    editingWreath.hashtags = editHashtags.value.split(',').map(t => t.trim()).filter(Boolean);
    editingWreath.platforms = {
        poshmark: editPoshmark.value.trim(),
        fbMarketplace: editFacebook.value.trim(),
        mercari: editMercari.value.trim(),
        other1: editOther.value.trim()
    };
    
    // Find and update or add wreath
    const existingIndex = wreathsData.findIndex(w => w.id === editingWreath.id);
    if (existingIndex >= 0) {
        wreathsData[existingIndex] = editingWreath;
    } else {
        wreathsData.unshift(editingWreath);
    }
    
    workflowState.edited = true;
    markUnsavedChanges();
    updateWorkflowSteps();
    displayWreaths();
    updateItemCount();
    closeEditModalHandler();
    setSaveStatus('Changes saved to memory', 'success');
}

// Delete current wreath
function deleteCurrentWreath() {
    if (!editingWreath) return;
    
    if (confirm(`Are you sure you want to delete "${editingWreath.title}"?`)) {
        wreathsData = wreathsData.filter(w => w.id !== editingWreath.id);
        markUnsavedChanges();
        displayWreaths();
        updateItemCount();
        closeEditModalHandler();
        setSaveStatus('Wreath deleted', 'success');
    }
}

// Export wreaths
function exportWreaths() {
    const dataStr = JSON.stringify(wreathsData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `wreaths-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    
    workflowState.exported = true;
    hasUnsavedChanges = false;
    updateWorkflowSteps();
    updateStatus('Database exported successfully! Upload this file to your website.', 'success');
    setSaveStatus('Database exported', 'success');
    unsavedIndicator.classList.add('hidden');
}

// Update item count
function updateItemCount() {
    const filteredWreaths = showSoldItems.checked ? 
        wreathsData : wreathsData.filter(w => !w.sold);
    
    const count = filteredWreaths.length;
    const totalCount = wreathsData.length;
    
    if (showSoldItems.checked) {
        itemCount.textContent = `${count} item${count !== 1 ? 's' : ''} total`;
    } else {
        itemCount.textContent = `${count} available of ${totalCount} total`;
    }
}

// Mark unsaved changes
function markUnsavedChanges() {
    hasUnsavedChanges = true;
    setSaveStatus('Unsaved changes', 'warning');
    unsavedIndicator.classList.remove('hidden');
}

// Update workflow steps
function updateWorkflowSteps() {
    // Step 1: Load
    const step1 = document.getElementById('step1');
    if (workflowState.loaded) {
        step1.classList.add('completed');
        step1.querySelector('span').className = 'bg-green-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm mr-2';
        step1.querySelector('span').innerHTML = '✓';
    }
    
    // Step 2: Import (always available after load)
    const step2 = document.getElementById('step2');
    if (workflowState.loaded) {
        step2.classList.add('active');
        step2.querySelector('span').className = 'bg-green-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm mr-2';
        step2.querySelector('span').innerHTML = '2';
    }
    
    // Step 3: Edit (always available after load)
    const step3 = document.getElementById('step3');
    if (workflowState.loaded) {
        step3.classList.add('active');
        step3.querySelector('span').className = 'bg-purple-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm mr-2';
        step3.querySelector('span').innerHTML = '3';
    }
    
    // Step 4: Export (available after any edits or imports)
    const step4 = document.getElementById('step4');
    if (workflowState.loaded) {
        step4.classList.add('active');
        step4.querySelector('span').className = 'bg-orange-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm mr-2';
        step4.querySelector('span').innerHTML = '4';
        exportJsonBtn.disabled = false;
        exportJsonBtn.classList.remove('bg-gray-400');
        exportJsonBtn.classList.add('bg-orange-600', 'hover:bg-orange-700');
    }
}

// Update status section
function updateStatus(message, type) {
    const iconMap = {
        loading: 'fas fa-spinner fa-spin',
        success: 'fas fa-check-circle text-green-600',
        warning: 'fas fa-exclamation-triangle text-yellow-600',
        error: 'fas fa-times-circle text-red-600'
    };
    
    const colorMap = {
        loading: 'text-blue-600',
        success: 'text-green-600',
        warning: 'text-yellow-600',
        error: 'text-red-600'
    };
    
    statusContent.innerHTML = `
        <i class="${iconMap[type]} mr-2"></i>
        <span class="${colorMap[type]}">${message}</span>
    `;
    
    if (type === 'success' || type === 'error') {
        setTimeout(() => {
            statusSection.style.display = 'none';
        }, 5000);
    } else {
        statusSection.style.display = 'block';
    }
}

// Set save status
function setSaveStatus(message, type) {
    saveStatus.textContent = message;
    saveStatus.className = `text-sm ${
        type === 'success' ? 'text-green-600' :
        type === 'warning' ? 'text-yellow-600' :
        type === 'error' ? 'text-red-600' :
        'text-gray-500'
    }`;
}

// Make functions global for onclick handlers
window.toggleSold = toggleSold;
window.editWreath = editWreath;
window.removeImage = removeImage;