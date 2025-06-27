// Admin panel JavaScript for Twinfolks Door Decor

let wreathsData = [];
let editingWreath = null;
let isLoggedIn = false;

// Admin password (in real app, this should be more secure)
const ADMIN_PASSWORD = 'twinfolks2025';

// DOM elements
const loginContainer = document.getElementById('loginContainer');
const adminContainer = document.getElementById('adminContainer');
const adminPassword = document.getElementById('adminPassword');
const loginButton = document.getElementById('loginButton');
const logoutButton = document.getElementById('logoutButton');

// Admin controls
const addWreathBtn = document.getElementById('addWreathBtn');
const jsonUpload = document.getElementById('jsonUpload');
const downloadDataBtn = document.getElementById('downloadDataBtn');
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
const editDescription = document.getElementById('editDescription');
const editHashtags = document.getElementById('editHashtags');
const editPoshmark = document.getElementById('editPoshmark');
const editFacebook = document.getElementById('editFacebook');
const editMercari = document.getElementById('editMercari');
const editOther = document.getElementById('editOther');

const cancelEditBtn = document.getElementById('cancelEditBtn');
const saveEditBtn = document.getElementById('saveEditBtn');

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    checkLoginStatus();
    setupEventListeners();
});

// Check if user is logged in
function checkLoginStatus() {
    const savedLogin = localStorage.getItem('twinfolks_admin_login');
    if (savedLogin === 'true') {
        showAdminPanel();
    } else {
        showLoginScreen();
    }
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
    loadWreaths();
}

// Handle login
function handleLogin() {
    const password = adminPassword.value.trim();
    if (password === ADMIN_PASSWORD) {
        localStorage.setItem('twinfolks_admin_login', 'true');
        showAdminPanel();
        adminPassword.value = '';
    } else {
        alert('Incorrect password');
        adminPassword.value = '';
    }
}

// Handle logout
function handleLogout() {
    localStorage.removeItem('twinfolks_admin_login');
    showLoginScreen();
}

// Load wreaths data
async function loadWreaths() {
    try {
        const response = await fetch('wreaths.json');
        if (!response.ok) {
            // If file doesn't exist, start with empty array
            wreathsData = [];
        } else {
            wreathsData = await response.json();
        }
        displayWreaths();
        updateItemCount();
    } catch (error) {
        console.error('Error loading wreaths:', error);
        wreathsData = [];
        displayWreaths();
        updateItemCount();
    }
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
                    ${wreathsData.length === 0 ? 'No wreaths added yet.' : 'No items match current filter.'}
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
                <button onclick="deleteWreath('${wreath.id}')" 
                        class="text-red-600 hover:text-red-800">
                    <i class="fas fa-trash"></i>
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
        saveWreaths();
        displayWreaths();
        updateItemCount();
    }
}

// Delete wreath
function deleteWreath(wreathId) {
    if (confirm('Are you sure you want to delete this wreath?')) {
        wreathsData = wreathsData.filter(w => w.id !== wreathId);
        saveWreaths();
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
    
    saveWreaths();
    displayWreaths();
    updateItemCount();
    closeEditModalHandler();
}

// Cancel edit
function cancelEdit() {
    closeEditModalHandler();
}

// Save wreaths to JSON (for download)
function saveWreaths() {
    // In a real app, this would save to a database
    // For now, we'll just prepare for download
    localStorage.setItem('twinfolks_wreaths_backup', JSON.stringify(wreathsData));
}

// Download data as JSON
function downloadData() {
    const dataStr = JSON.stringify(wreathsData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `twinfolks-wreaths-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

// Handle JSON upload
function handleJSONUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = function(e) {
        try {
            const jsonData = JSON.parse(e.target.result);
            
            // Check if it's a single wreath or array
            if (Array.isArray(jsonData)) {
                // Multiple wreaths
                jsonData.forEach(wreath => addImportedWreath(wreath));
            } else {
                // Single wreath
                addImportedWreath(jsonData);
            }
            
            saveWreaths();
            displayWreaths();
            updateItemCount();
            alert('JSON data imported successfully!');
        } catch (error) {
            alert('Error reading JSON file: ' + error.message);
        }
    };
    reader.readAsText(file);
    
    // Reset file input
    event.target.value = '';
}

// Add imported wreath
function addImportedWreath(data) {
    const wreath = {
        id: data.url ? data.url.split('-').pop() : Date.now().toString() + Math.random().toString(36).substr(2, 9),
        title: data.title || "Imported Wreath",
        localPrice: 0, // User needs to set this
        sold: false,
        hashtags: data.tags || data.hashtags || [],
        category: "holiday",
        dateAdded: new Date().toISOString().split('T')[0],
        description: data.description || "",
        platforms: {
            poshmark: data.url || "",
            fbMarketplace: "",
            mercari: "",
            other1: ""
        },
        images: data.images || []
    };
    
    // Check if wreath already exists
    const existingIndex = wreathsData.findIndex(w => w.id === wreath.id);
    if (existingIndex >= 0) {
        // Update existing
        wreathsData[existingIndex] = wreath;
    } else {
        // Add new
        wreathsData.unshift(wreath);
    }
}

// Update item count
function updateItemCount() {
    const filteredWreaths = showSoldItems.checked ? 
        wreathsData : wreathsData.filter(w => !w.sold);
    
    const count = filteredWreaths.length;
    itemCount.textContent = `${count} item${count !== 1 ? 's' : ''}`;
}

// Setup event listeners
function setupEventListeners() {
    // Login
    loginButton.addEventListener('click', handleLogin);
    adminPassword.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleLogin();
    });
    
    // Logout
    logoutButton.addEventListener('click', handleLogout);
    
    // Admin controls
    addWreathBtn.addEventListener('click', addNewWreath);
    jsonUpload.addEventListener('change', handleJSONUpload);
    downloadDataBtn.addEventListener('click', downloadData);
    showSoldItems.addEventListener('change', () => {
        displayWreaths();
        updateItemCount();
    });
    
    // Edit modal
    closeEditModal.addEventListener('click', closeEditModalHandler);
    cancelEditBtn.addEventListener('click', cancelEdit);
    saveEditBtn.addEventListener('click', saveEdit);
    addImageBtn.addEventListener('click', addImage);
    
    // Add image on Enter key
    newImageUrl.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') addImage();
    });
    
    // Close modal when clicking outside
    editModal.addEventListener('click', (e) => {
        if (e.target === editModal) {
            closeEditModalHandler();
        }
    });
    
    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (isLoggedIn && editModal.classList.contains('active') && e.key === 'Escape') {
            closeEditModalHandler();
        }
    });
}

// Make functions global for onclick handlers
window.toggleSold = toggleSold;
window.deleteWreath = deleteWreath;
window.editWreath = editWreath;
window.removeImage = removeImage;