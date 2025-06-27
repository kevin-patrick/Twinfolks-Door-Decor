// File: website/js/admin-secure.js
// Secure admin panel with serverless function authentication

let wreathsData = [];
let editingWreath = null;
let hasUnsavedChanges = false;
let isAuthenticated = false;
let sessionToken = null;

// Workflow state
let workflowState = {
    downloaded: false,
    loaded: false,
    edited: false,
    exported: false
};

// Initialize when DOM loads
document.addEventListener('DOMContentLoaded', function() {
    checkAuthStatus();
    setupEventListeners();
});

// Check if user is authenticated
function checkAuthStatus() {
    sessionToken = localStorage.getItem('twinfolks_session');
    
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
    document.getElementById('loginContainer').style.display = 'flex';
    document.getElementById('adminContainer').classList.remove('active');
    isAuthenticated = false;
}

// Show admin panel
function showAdminPanel() {
    document.getElementById('loginContainer').style.display = 'none';
    document.getElementById('adminContainer').classList.add('active');
    isAuthenticated = true;
    updateWorkflowSteps();
}

// Handle login
async function handleLogin() {
    const password = document.getElementById('adminPassword').value.trim();
    const loginButton = document.getElementById('loginButton');
    const loginError = document.getElementById('loginError');
    
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
            // Store session token
            sessionToken = result.sessionToken;
            localStorage.setItem('twinfolks_session', sessionToken);
            
            // Clear password field
            document.getElementById('adminPassword').value = '';
            
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
    const loginError = document.getElementById('loginError');
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
    sessionToken = null;
    isAuthenticated = false;
    wreathsData = [];
    hasUnsavedChanges = false;
    workflowState = { downloaded: false, loaded: false, edited: false, exported: false };
    
    showLoginScreen();
}

// Setup event listeners
function setupEventListeners() {
    // Login
    document.getElementById('loginButton').addEventListener('click', handleLogin);
    document.getElementById('adminPassword').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleLogin();
    });
    
    // Logout
    document.getElementById('logoutButton').addEventListener('click', handleLogout);

    // Workflow steps
    document.getElementById('downloadCurrentBtn').addEventListener('click', downloadCurrentData);
    document.getElementById('loadFileBtn').addEventListener('click', () => {
        document.getElementById('loadJsonFile').click();
    });
    document.getElementById('loadJsonFile').addEventListener('change', handleJsonLoad);
    document.getElementById('exportJsonBtn').addEventListener('click', exportUpdatedData);

    // Wreath management
    document.getElementById('addWreathBtn').addEventListener('click', addNewWreath);
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

// Require authentication for admin actions
function requireAuth() {
    if (!isAuthenticated || !sessionToken) {
        alert('Please log in to perform this action.');
        showLoginScreen();
        return false;
    }
    return true;
}

// Download current data from website
async function downloadCurrentData() {
    if (!requireAuth()) return;

    const button = document.getElementById('downloadCurrentBtn');
    const originalText = button.innerHTML;
    
    try {
        button.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i> Downloading...';
        button.disabled = true;

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
        
        // Download the file
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `wreaths-backup-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        // Update workflow state
        workflowState.downloaded = true;
        updateWorkflowSteps();
        
        alert(`Downloaded ${data.length} wreaths successfully!`);
        
    } catch (error) {
        console.error('Download error:', error);
        alert('Failed to download current data. Please check if wreaths.json exists on your website.');
    } finally {
        button.innerHTML = originalText;
        button.disabled = false;
    }
}

// Handle JSON file loading
function handleJsonLoad(event) {
    if (!requireAuth()) return;

    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = function(e) {
        try {
            wreathsData = JSON.parse(e.target.result);
            workflowState.loaded = true;
            updateWorkflowSteps();
            displayWreaths();
            updateWreathCount();
            alert(`Loaded ${wreathsData.length} wreaths successfully!`);
        } catch (error) {
            alert('Error parsing JSON file. Please check the file format.');
            console.error('JSON parse error:', error);
        }
    };
    reader.readAsText(file);
}

// Export updated data
function exportUpdatedData() {
    if (!requireAuth()) return;
    
    if (wreathsData.length === 0) {
        alert('No data to export. Please load wreaths first.');
        return;
    }

    const blob = new Blob([JSON.stringify(wreathsData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'wreaths.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    workflowState.exported = true;
    hasUnsavedChanges = false;
    updateWorkflowSteps();
    alert('Exported wreaths.json successfully! Upload this file to your website.');
}

// Handle import files
function handleImportFiles(event) {
    if (!requireAuth()) return;

    const files = Array.from(event.target.files);
    let importedCount = 0;
    let processedCount = 0;

    files.forEach(file => {
        const reader = new FileReader();
        reader.onload = function(e) {
            try {
                const newWreaths = JSON.parse(e.target.result);
                
                if (Array.isArray(newWreaths)) {
                    // Multiple wreaths
                    newWreaths.forEach(wreath => {
                        if (wreath && typeof wreath === 'object') {
                            if (!wreathsData.some(existing => existing.id === wreath.id)) {
                                wreathsData.push(wreath);
                                importedCount++;
                            }
                        }
                    });
                } else if (newWreaths && typeof newWreaths === 'object') {
                    // Single wreath
                    if (!wreathsData.some(existing => existing.id === newWreaths.id)) {
                        wreathsData.push(newWreaths);
                        importedCount++;
                    }
                }
                
                processedCount++;
                if (processedCount === files.length) {
                    displayWreaths();
                    updateWreathCount();
                    markAsEdited();
                    alert(`Imported ${importedCount} new wreaths from ${files.length} files.`);
                }
            } catch (error) {
                console.error('Error importing file:', file.name, error);
                processedCount++;
            }
        };
        reader.readAsText(file);
    });
}

// Display wreaths in grid
function displayWreaths() {
    const showSold = document.getElementById('showSoldItems').checked;
    const filteredWreaths = showSold ? wreathsData : wreathsData.filter(wreath => !wreath.sold);
    
    const container = document.getElementById('wreathsGrid');
    const emptyState = document.getElementById('emptyState');
    
    if (filteredWreaths.length === 0) {
        container.classList.add('hidden');
        emptyState.classList.remove('hidden');
        return;
    }
    
    emptyState.classList.add('hidden');
    container.classList.remove('hidden');
    
    container.innerHTML = filteredWreaths.map(wreath => `
        <div class="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow ${wreath.sold ? 'opacity-60' : ''}">
            <div class="aspect-square bg-gray-100 rounded-lg mb-3 overflow-hidden">
                ${wreath.images && wreath.images.length > 0 
                    ? `<img src="${wreath.images[0]}" alt="${wreath.title}" class="w-full h-full object-cover" onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjNmNGY2Ii8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzlmYTZiNyIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPk5vIEltYWdlPC90ZXh0Pjwvc3ZnPg=='">`
                    : `<div class="w-full h-full flex items-center justify-center text-gray-400">
                         <i class="fas fa-image text-2xl"></i>
                       </div>`
                }
            </div>
            
            <h3 class="font-medium text-sm mb-2 truncate" title="${wreath.title || 'Untitled'}">${wreath.title || 'Untitled'}</h3>
            
            <div class="flex items-center justify-between mb-2">
                <span class="text-green-600 font-semibold text-sm">
                    $${(wreath.localPrice || 0).toFixed(2)}
                </span>
                ${wreath.sold ? '<span class="bg-red-100 text-red-800 text-xs px-2 py-1 rounded">SOLD</span>' : ''}
            </div>
            
            <div class="flex space-x-2">
                <button onclick="editWreath('${wreath.id}')" class="flex-1 bg-blue-600 text-white text-xs py-2 px-3 rounded hover:bg-blue-700">
                    <i class="fas fa-edit mr-1"></i> Edit
                </button>
            </div>
        </div>
    `).join('');
}

// Edit wreath
function editWreath(wreathId) {
    if (!requireAuth()) return;
    
    const wreath = wreathsData.find(w => w.id === wreathId);
    if (!wreath) return;
    
    editingWreath = wreath;
    populateEditForm(wreath);
    document.getElementById('editModal').classList.remove('hidden');
    document.getElementById('editModal').classList.add('flex');
}

// Populate edit form
function populateEditForm(wreath) {
    document.getElementById('editTitle').value = wreath.title || '';
    document.getElementById('editLocalPrice').value = wreath.localPrice || '';
    document.getElementById('editOriginalPrice').value = wreath.originalPrice || '';
    document.getElementById('editBrand').value = wreath.brand || '';
    document.getElementById('editDescription').value = wreath.description || '';
    document.getElementById('editHashtags').value = wreath.hashtags || '';
    document.getElementById('editSold').checked = wreath.sold || false;
    
    // Populate images
    const imagesList = document.getElementById('imagesList');
    imagesList.innerHTML = (wreath.images || []).map((img, index) => `
        <div class="flex items-center space-x-2 p-2 bg-gray-50 rounded">
            <img src="${img}" alt="Preview" class="w-12 h-12 object-cover rounded" onerror="this.style.display='none'">
            <input type="url" value="${img}" class="flex-1 border border-gray-300 rounded px-2 py-1 text-sm" onchange="updateImage(${index}, this.value)">
            <button type="button" onclick="removeImage(${index})" class="text-red-600 hover:text-red-800">
                <i class="fas fa-trash text-sm"></i>
            </button>
        </div>
    `).join('');
}

// Update image URL
function updateImage(index, newUrl) {
    if (editingWreath && editingWreath.images) {
        editingWreath.images[index] = newUrl;
        markAsEdited();
    }
}

// Remove image
function removeImage(index) {
    if (editingWreath && editingWreath.images) {
        editingWreath.images.splice(index, 1);
        populateEditForm(editingWreath);
        markAsEdited();
    }
}

// Add new image
function addImage() {
    const newImageUrl = document.getElementById('newImageUrl').value.trim();
    if (!newImageUrl) return;
    
    if (editingWreath) {
        if (!editingWreath.images) editingWreath.images = [];
        editingWreath.images.push(newImageUrl);
        document.getElementById('newImageUrl').value = '';
        populateEditForm(editingWreath);
        markAsEdited();
    }
}

// Save edit
function saveEdit() {
    if (!requireAuth() || !editingWreath) return;
    
    // Update wreath data
    editingWreath.title = document.getElementById('editTitle').value.trim();
    editingWreath.localPrice = parseFloat(document.getElementById('editLocalPrice').value) || 0;
    editingWreath.originalPrice = parseFloat(document.getElementById('editOriginalPrice').value) || 0;
    editingWreath.brand = document.getElementById('editBrand').value.trim();
    editingWreath.description = document.getElementById('editDescription').value.trim();
    editingWreath.hashtags = document.getElementById('editHashtags').value.trim();
    editingWreath.sold = document.getElementById('editSold').checked;
    
    closeEditModal();
    displayWreaths();
    markAsEdited();
    alert('Wreath updated successfully!');
}

// Delete current wreath
function deleteCurrentWreath() {
    if (!requireAuth() || !editingWreath) return;
    
    if (confirm('Are you sure you want to delete this wreath? This action cannot be undone.')) {
        const index = wreathsData.findIndex(w => w.id === editingWreath.id);
        if (index !== -1) {
            wreathsData.splice(index, 1);
            closeEditModal();
            displayWreaths();
            updateWreathCount();
            markAsEdited();
            alert('Wreath deleted successfully!');
        }
    }
}

// Close edit modal
function closeEditModal() {
    document.getElementById('editModal').classList.add('hidden');
    document.getElementById('editModal').classList.remove('flex');
    editingWreath = null;
}

// Add new wreath
function addNewWreath() {
    if (!requireAuth()) return;
    
    const newWreath = {
        id: 'new_' + Date.now(),
        title: 'New Wreath',
        localPrice: 0,
        originalPrice: 0,
        brand: '',
        description: '',
        hashtags: '',
        images: [],
        sold: false,
        dateAdded: new Date().toISOString()
    };
    
    wreathsData.unshift(newWreath);
    displayWreaths();
    updateWreathCount();
    markAsEdited();
    editWreath(newWreath.id);
}

// Mark as edited
function markAsEdited() {
    hasUnsavedChanges = true;
    workflowState.edited = true;
    updateWorkflowSteps();
}

// Update wreath count
function updateWreathCount() {
    document.getElementById('wreathCount').textContent = wreathsData.length;
}

// Update workflow steps
function updateWorkflowSteps() {
    const steps = [
        { id: 'step1', completed: workflowState.downloaded },
        { id: 'step2', completed: workflowState.loaded },
        { id: 'step3', completed: workflowState.edited },
        { id: 'step4', completed: workflowState.exported }
    ];
    
    steps.forEach((step, index) => {
        const element = document.getElementById(step.id);
        const span = element.querySelector('span');
        const button = element.querySelector('button');
        
        // Update visual state
        element.classList.remove('completed', 'active');
        if (step.completed) {
            element.classList.add('completed');
            span.className = 'bg-green-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm mr-2';
            span.innerHTML = '<i class="fas fa-check"></i>';
        } else {
            const isActive = index === 0 || steps[index - 1]?.completed;
            if (isActive) {
                element.classList.add('active');
                span.className = 'bg-blue-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm mr-2';
            } else {
                span.className = 'bg-gray-400 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm mr-2';
            }
            span.textContent = index + 1;
        }
        
        // Enable/disable buttons
        if (button) {
            if (step.id === 'step1') {
                button.disabled = false;
                button.className = button.className.replace('bg-gray-400', 'bg-blue-600').replace('hover:bg-gray-500', 'hover:bg-blue-700');
            } else if (step.id === 'step2') {
                button.disabled = !workflowState.downloaded;
                if (!button.disabled) {
                    button.className = button.className.replace('bg-gray-400', 'bg-blue-600').replace('hover:bg-gray-500', 'hover:bg-blue-700');
                }
            } else if (step.id === 'step4') {
                button.disabled = !workflowState.loaded;
                if (!button.disabled) {
                    button.className = button.className.replace('bg-gray-400', 'bg-green-600').replace('hover:bg-gray-500', 'hover:bg-green-700');
                }
            }
        }
    });
}