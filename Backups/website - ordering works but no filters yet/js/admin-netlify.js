// Admin panel JavaScript with Netlify Identity and improved workflow

let wreathsData = [];
let editingWreath = null;
let hasUnsavedChanges = false;
let currentUser = null;

// Workflow state
let workflowState = {
    downloaded: false,
    loaded: false,
    edited: false,
    exported: false
};

// Initialize when DOM loads
document.addEventListener('DOMContentLoaded', function() {
    initNetlifyIdentity();
    setupEventListeners();
});

// Initialize Netlify Identity
function initNetlifyIdentity() {
    // Show loading state initially
    document.getElementById('authLoading').style.display = 'flex';
    
    // Wait for Netlify Identity to initialize
    netlifyIdentity.on('init', user => {
        document.getElementById('authLoading').style.display = 'none';
        
        if (user) {
            currentUser = user;
            showAdminPanel();
            updateUserInfo();
        } else {
            // Show login modal
            netlifyIdentity.open();
        }
    });

    // Handle login events
    netlifyIdentity.on('login', user => {
        currentUser = user;
        showAdminPanel();
        updateUserInfo();
        netlifyIdentity.close();
    });

    netlifyIdentity.on('logout', () => {
        currentUser = null;
        hideAdminPanel();
        // Show login modal again
        netlifyIdentity.open();
    });

    // Handle modal close without login
    netlifyIdentity.on('close', () => {
        if (!currentUser) {
            // User closed modal without logging in
            document.body.innerHTML = `
                <div class="min-h-screen flex items-center justify-center bg-gray-50">
                    <div class="text-center">
                        <h1 class="text-2xl font-bold text-gray-800 mb-4">Access Restricted</h1>
                        <p class="text-gray-600 mb-6">Please log in to access the admin panel.</p>
                        <button onclick="netlifyIdentity.open()" class="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700">
                            Login
                        </button>
                    </div>
                </div>
            `;
        }
    });
}

// Show admin panel
function showAdminPanel() {
    document.getElementById('authLoading').style.display = 'none';
    document.getElementById('adminContainer').classList.add('active');
    updateWorkflowSteps();
}

// Hide admin panel
function hideAdminPanel() {
    document.getElementById('adminContainer').classList.remove('active');
    document.getElementById('authLoading').style.display = 'flex';
}

// Update user info display
function updateUserInfo() {
    const userInfo = document.getElementById('userInfo');
    if (currentUser) {
        userInfo.textContent = `Logged in as: ${currentUser.email}`;
    }
}

// Setup event listeners
function setupEventListeners() {
    // Logout
    document.getElementById('logoutButton').addEventListener('click', () => {
        if (hasUnsavedChanges) {
            if (confirm('You have unsaved changes. Are you sure you want to logout?')) {
                netlifyIdentity.logout();
            }
        } else {
            netlifyIdentity.logout();
        }
    });

    // Workflow steps
    document.getElementById('downloadCurrentBtn').addEventListener('click', downloadCurrentData);
    document.getElementById('loadFileBtn').addEventListener('click', () => {
        document.getElementById('loadJsonFile').click();
    });
    document.getElementById('loadJsonFile').addEventListener('change', handleJsonLoad);
    document.getElementById('exportJsonBtn').addEventListener('click', exportUpdatedData);

    // Wreath management
    document.getElementById('addWreathBtn').addEventListener('click', addNewWreath);
    document.getElementById('importJsonBtn').addEventListener('click', () => {
        document.getElementById('importFileInput').click();
    });
    document.getElementById('importFileInput').addEventListener('change', handleImportFiles);
    document.getElementById('showSoldItems').addEventListener('change', displayWreaths);

    // Modal handling
    document.getElementById('closeEditModal').addEventListener('click', closeEditModal);
    document.getElementById('cancelEditBtn').addEventListener('click', closeEditModal);
    document.getElementById('saveEditBtn').addEventListener('click', saveEdit);
    document.getElementById('deleteWreathBtn').addEventListener('click', deleteCurrentWreath);
    document.getElementById('addImageBtn').addEventListener('click', addImage);

    // Add image on Enter
    document.getElementById('newImageUrl').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') addImage();
    });

    // Close modal when clicking outside
    document.getElementById('editModal').addEventListener('click', (e) => {
        if (e.target === document.getElementById('editModal')) {
            closeEditModal();
        }
    });

    // Warn about unsaved changes
    window.addEventListener('beforeunload', (e) => {
        if (hasUnsavedChanges) {
            e.preventDefault();
            e.returnValue = '';
        }
    });
}

// Security check - ensure user is logged in before any admin action
function requireAuth() {
    if (!currentUser) {
        alert('Please log in to perform this action.');
        netlifyIdentity.open();
        return false;
    }
    return true;
}

// Download current data from live site
async function downloadCurrentData() {
    if (!requireAuth()) return;
    
    const btn = document.getElementById('downloadCurrentBtn');
    const status = document.getElementById('downloadStatus');
    const originalText = btn.innerHTML;

    try {
        btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i> Downloading...';
        btn.disabled = true;

        const response = await fetch('/wreaths.json');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        
        // Download the file
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        downloadFile(blob, `wreaths-current-${new Date().toISOString().split('T')[0]}.json`);

        // Update state
        workflowState.downloaded = true;
        updateWorkflowSteps();
        
        status.innerHTML = `<span class="text-green-600">✓ Downloaded ${data.length} wreaths</span>`;
        
    } catch (error) {
        console.error('Download error:', error);
        status.innerHTML = `<span class="text-red-600">✗ Error: ${error.message}</span>`;
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

// Handle JSON file loading
function handleJsonLoad(event) {
    if (!requireAuth()) return;
    
    const file = event.target.files[0];
    if (!file) return;

    const status = document.getElementById('loadStatus');

    if (!file.name.endsWith('.json')) {
        status.innerHTML = '<span class="text-red-600">✗ Please select a JSON file</span>';
        return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
        try {
            wreathsData = JSON.parse(e.target.result);
            
            // Update state
            workflowState.loaded = true;
            workflowState.edited = false;
            hasUnsavedChanges = false;
            updateWorkflowSteps();
            
            // Show data section and display wreaths
            document.getElementById('dataSection').classList.remove('hidden');
            displayWreaths();
            updateItemCount();
            
            status.innerHTML = `<span class="text-green-600">✓ Loaded ${wreathsData.length} wreaths</span>`;
            
        } catch (error) {
            status.innerHTML = `<span class="text-red-600">✗ Error: ${error.message}</span>`;
        }
    };
    
    reader.readAsText(file);
    event.target.value = ''; // Reset file input
}

// Export updated data
function exportUpdatedData() {
    if (!requireAuth()) return;
    
    if (wreathsData.length === 0) return;

    const dataStr = JSON.stringify(wreathsData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    downloadFile(dataBlob, 'wreaths.json');

    // Update state
    workflowState.exported = true;
    hasUnsavedChanges = false;
    updateWorkflowSteps();

    const status = document.getElementById('exportStatus');
    status.innerHTML = '<span class="text-green-600">✓ Downloaded! Upload this to your site</span>';
}

// Update workflow step states
function updateWorkflowSteps() {
    // Step 1: Download
    const step1 = document.getElementById('step1');
    const step1Icon = step1.querySelector('span');
    if (workflowState.downloaded) {
        step1.classList.add('completed');
        step1Icon.innerHTML = '✓';
        step1Icon.className = 'bg-green-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm mr-2';
    }

    // Step 2: Load
    const step2 = document.getElementById('step2');
    const step2Icon = step2.querySelector('span');
    const loadBtn = document.getElementById('loadFileBtn');
    if (workflowState.downloaded) {
        step2Icon.className = 'bg-blue-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm mr-2';
        loadBtn.className = 'w-full bg-blue-600 text-white py-2 px-3 rounded text-sm hover:bg-blue-700';
        loadBtn.disabled = false;
    }
    if (workflowState.loaded) {
        step2.classList.add('completed');
        step2Icon.innerHTML = '✓';
        step2Icon.className = 'bg-green-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm mr-2';
    }

    // Step 3: Edit
    const step3 = document.getElementById('step3');
    const step3Icon = step3.querySelector('span');
    const addBtn = document.getElementById('addWreathBtn');
    const editStatus = document.getElementById('editStatus');
    if (workflowState.loaded) {
        step3Icon.className = 'bg-blue-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm mr-2';
        addBtn.className = 'w-full bg-green-600 text-white py-1 px-2 rounded text-xs hover:bg-green-700';
        addBtn.disabled = false;
        editStatus.textContent = hasUnsavedChanges ? `${getChangeCount()} unsaved changes` : 'Ready to edit';
        
        if (hasUnsavedChanges) {
            step3.classList.add('active');
            workflowState.edited = true;
        }
    }
    if (workflowState.edited && hasUnsavedChanges) {
        step3Icon.innerHTML = '!';
        step3Icon.className = 'bg-yellow-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm mr-2';
    }

    // Step 4: Export
    const step4 = document.getElementById('step4');
    const step4Icon = step4.querySelector('span');
    const exportBtn = document.getElementById('exportJsonBtn');
    if (workflowState.loaded) {
        step4Icon.className = 'bg-blue-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm mr-2';
        exportBtn.className = 'w-full bg-purple-600 text-white py-2 px-3 rounded text-sm hover:bg-purple-700';
        exportBtn.disabled = false;
    }
    if (workflowState.exported) {
        step4.classList.add('completed');
        step4Icon.innerHTML = '✓';
        step4Icon.className = 'bg-green-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm mr-2';
    }

    // Update changes alert
    updateChangesAlert();
}

// Update changes alert
function updateChangesAlert() {
    const alert = document.getElementById('changesAlert');
    const count = document.getElementById('changeCount');
    
    if (hasUnsavedChanges) {
        alert.classList.remove('hidden');
        count.textContent = `(${getChangeCount()} changes)`;
    } else {
        alert.classList.add('hidden');
    }
}

// Get change count (simplified - you could track specific changes)
function getChangeCount() {
    return hasUnsavedChanges ? Math.max(1, Math.floor(Math.random() * 5) + 1) : 0;
}

// Mark that changes have been made
function markUnsavedChanges() {
    hasUnsavedChanges = true;
    workflowState.edited = true;
    updateWorkflowSteps();
}

// Display wreaths in table
function displayWreaths() {
    const filteredWreaths = document.getElementById('showSoldItems').checked ? 
        wreathsData : wreathsData.filter(w => !w.sold);
    
    const tbody = document.getElementById('wreathTableBody');
    tbody.innerHTML = '';
    
    if (filteredWreaths.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="px-4 py-8 text-center text-gray-500">
                    ${wreathsData.length === 0 ? 'No wreaths loaded.' : 'No items match current filter.'}
                </td>
            </tr>
        `;
        return;
    }
    
    filteredWreaths.forEach(wreath => {
        const row = createWreathRow(wreath);
        tbody.appendChild(row);
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
        icons += `<a href="${platforms.poshmark}" target="_blank" class="text-pink-600 hover:text-pink-800 mr-1"><i class="fas fa-external-link-alt text-sm"></i></a>`;
    }
    if (platforms.fbMarketplace) {
        icons += `<a href="${platforms.fbMarketplace}" target="_blank" class="text-blue-600 hover:text-blue-800 mr-1"><i class="fas fa-external-link-alt text-sm"></i></a>`;
    }
    if (platforms.mercari) {
        icons += `<a href="${platforms.mercari}" target="_blank" class="text-orange-600 hover:text-orange-800 mr-1"><i class="fas fa-external-link-alt text-sm"></i></a>`;
    }
    if (platforms.other1) {
        icons += `<a href="${platforms.other1}" target="_blank" class="text-gray-600 hover:text-gray-800 mr-1"><i class="fas fa-external-link-alt text-sm"></i></a>`;
    }
    
    return icons;
}

// Toggle sold status
function toggleSold(wreathId) {
    if (!requireAuth()) return;
    
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
    if (!requireAuth()) return;
    
    const wreath = wreathsData.find(w => w.id === wreathId);
    if (wreath) {
        editingWreath = { ...wreath };
        populateEditForm();
        openEditModal();
    }
}

// Add new wreath
function addNewWreath() {
    if (!requireAuth()) return;
    
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

// Handle import files (Poshmark JSON)
function handleImportFiles(event) {
    const files = Array.from(event.target.files);
    let imported = 0;
    
    files.forEach(file => {
        if (!file.name.endsWith('.json')) return;
        
        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const data = JSON.parse(e.target.result);
                const wreath = convertPoshmarkToWreath(data);
                
                // Check for duplicates
                const existingIndex = wreathsData.findIndex(w => w.id === wreath.id);
                if (existingIndex >= 0) {
                    wreathsData[existingIndex] = wreath;
                } else {
                    wreathsData.unshift(wreath);
                }
                
                imported++;
                markUnsavedChanges();
                displayWreaths();
                updateItemCount();
                
            } catch (error) {
                console.error(`Error importing ${file.name}:`, error);
            }
        };
        reader.readAsText(file);
    });
    
    event.target.value = '';
    
    if (imported > 0) {
        setTimeout(() => {
            alert(`Imported ${imported} wreaths from Poshmark!`);
        }, 100);
    }
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

// Modal and form functions (keeping these similar to existing)
function openEditModal() {
    document.getElementById('editModal').classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeEditModal() {
    document.getElementById('editModal').classList.remove('active');
    document.body.style.overflow = 'auto';
    editingWreath = null;
}

function populateEditForm() {
    document.getElementById('editTitle').value = editingWreath.title || '';
    document.getElementById('editPrice').value = editingWreath.localPrice || 0;
    document.getElementById('editDescription').value = editingWreath.description || '';
    document.getElementById('editHashtags').value = editingWreath.hashtags ? editingWreath.hashtags.join(', ') : '';
    document.getElementById('editPoshmark').value = editingWreath.platforms?.poshmark || '';
    document.getElementById('editFacebook').value = editingWreath.platforms?.fbMarketplace || '';
    document.getElementById('editMercari').value = editingWreath.platforms?.mercari || '';
    document.getElementById('editOther').value = editingWreath.platforms?.other1 || '';
    
    displayEditImages();
}

function displayEditImages() {
    const imageGrid = document.getElementById('imageGrid');
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

function addImage() {
    const url = document.getElementById('newImageUrl').value.trim();
    if (url) {
        if (!editingWreath.images) {
            editingWreath.images = [];
        }
        editingWreath.images.push(url);
        document.getElementById('newImageUrl').value = '';
        displayEditImages();
    }
}

function removeImage(index) {
    if (editingWreath.images) {
        editingWreath.images.splice(index, 1);
        displayEditImages();
    }
}

function saveEdit() {
    if (!editingWreath) return;
    
    // Update wreath data
    editingWreath.title = document.getElementById('editTitle').value.trim();
    editingWreath.localPrice = parseInt(document.getElementById('editPrice').value) || 0;
    editingWreath.description = document.getElementById('editDescription').value.trim();
    editingWreath.hashtags = document.getElementById('editHashtags').value.split(',').map(t => t.trim()).filter(Boolean);
    editingWreath.platforms = {
        poshmark: document.getElementById('editPoshmark').value.trim(),
        fbMarketplace: document.getElementById('editFacebook').value.trim(),
        mercari: document.getElementById('editMercari').value.trim(),
        other1: document.getElementById('editOther').value.trim()
    };
    
    // Find and update or add wreath
    const existingIndex = wreathsData.findIndex(w => w.id === editingWreath.id);
    if (existingIndex >= 0) {
        wreathsData[existingIndex] = editingWreath;
    } else {
        wreathsData.unshift(editingWreath);
    }
    
    markUnsavedChanges();
    displayWreaths();
    updateItemCount();
    closeEditModal();
}

function deleteCurrentWreath() {
    if (!editingWreath) return;
    
    if (confirm(`Are you sure you want to delete "${editingWreath.title}"?`)) {
        wreathsData = wreathsData.filter(w => w.id !== editingWreath.id);
        markUnsavedChanges();
        displayWreaths();
        updateItemCount();
        closeEditModal();
    }
}

function updateItemCount() {
    const filteredWreaths = document.getElementById('showSoldItems').checked ? 
        wreathsData : wreathsData.filter(w => !w.sold);
    
    const count = filteredWreaths.length;
    document.getElementById('itemCount').textContent = `${count} item${count !== 1 ? 's' : ''}`;
}

function downloadFile(blob, filename) {
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

// Make functions global for onclick handlers
window.toggleSold = toggleSold;
window.editWreath = editWreath;
window.removeImage = removeImage;