// File: website/js/wreaths.js
// Main website JavaScript for Twinfolks Door Decor with filtering support

let wreathsData = [];
let filterConfig = [];
let currentWreath = null;
let currentImageIndex = 0;
let activeFilters = new Set();
let currentSort = 'featured';
let currentSearchTerm = '';

// DOM elements
const wreathGrid = document.getElementById('wreathGrid');
const loadingMessage = document.getElementById('loadingMessage');
const itemCount = document.getElementById('itemCount');
const showAvailableOnly = document.getElementById('showAvailableOnly');
const sortSelect = document.getElementById('sortSelect');
const filterCategories = document.getElementById('filterCategories');
const clearAllFilters = document.getElementById('clearAllFilters');
const searchInput = document.getElementById('searchInput');
const clearSearch = document.getElementById('clearSearch');

// Mobile sidebar elements
const mobileFilterToggle = document.getElementById('mobileFilterToggle');
const filterSidebar = document.getElementById('filterSidebar');
const sidebarOverlay = document.getElementById('sidebarOverlay');
const closeSidebar = document.getElementById('closeSidebar');

// Modal elements
const wreathModal = document.getElementById('wreathModal');
const orderModal = document.getElementById('orderModal');
const closeModal = document.getElementById('closeModal');
const closeOrderModal = document.getElementById('closeOrderModal');
const orderButton = document.getElementById('orderButton');

// Carousel elements
const carouselImage = document.getElementById('carouselImage');
const prevImageBtn = document.getElementById('prevImage');
const nextImageBtn = document.getElementById('nextImage');
const imageDots = document.getElementById('imageDots');

// Modal content elements
const modalTitle = document.getElementById('modalTitle');
const modalPrice = document.getElementById('modalPrice');
const modalDescription = document.getElementById('modalDescription');
const modalHashtags = document.getElementById('modalHashtags');
const soldBadge = document.getElementById('soldBadge');

// Order form elements
const orderTitle = document.getElementById('orderTitle');
const orderPrice = document.getElementById('orderPrice');
const formWreathTitle = document.getElementById('formWreathTitle');
const formWreathPrice = document.getElementById('formWreathPrice');

// Initialize the app
document.addEventListener('DOMContentLoaded', function() {
    Promise.all([
        loadWreaths(),
        loadFilterConfig()
    ]).then(() => {
        buildFilterUI();
        displayWreaths();
        updateItemCount();
    }).catch(error => {
        console.error('Error initializing app:', error);
        loadingMessage.innerHTML = '<p class="text-red-500">Error loading data. Please try again later.</p>';
    });
    
    setupEventListeners();
});

// Load wreaths data
async function loadWreaths() {
    try {
        const response = await fetch('wreaths.json');
        if (!response.ok) {
            throw new Error('Failed to load wreaths data');
        }
        wreathsData = await response.json();
        
        // Add featured field if missing (for backward compatibility)
        wreathsData.forEach(wreath => {
            if (wreath.featured === undefined) {
                wreath.featured = false;
            }
        });
        
    } catch (error) {
        console.error('Error loading wreaths:', error);
        throw error;
    }
}

// Load filter configuration
async function loadFilterConfig() {
    try {
        const response = await fetch('filter-config.json');
        if (!response.ok) {
            console.warn('Filter config not found, creating minimal config');
            filterConfig = [];
            return;
        }
        filterConfig = await response.json();
    } catch (error) {
        console.error('Error loading filter config:', error);
        filterConfig = [];
    }
}

// Build filter UI dynamically
function buildFilterUI() {
    if (!filterConfig || filterConfig.length === 0) {
        filterCategories.innerHTML = '<p class="text-gray-500 text-sm">No filters available</p>';
        return;
    }

    filterCategories.innerHTML = '';

    filterConfig.forEach(category => {
        const categoryDiv = document.createElement('div');
        categoryDiv.className = 'filter-category';
        
        const categoryHeader = document.createElement('h4');
        categoryHeader.className = 'text-sm font-medium text-gray-900 mb-2';
        categoryHeader.textContent = category.name;
        categoryDiv.appendChild(categoryHeader);

        const subcategoriesDiv = document.createElement('div');
        subcategoriesDiv.className = 'space-y-2';

        category.subcategories.forEach(subcategory => {
            const subDiv = document.createElement('div');
            subDiv.className = 'flex items-center';

            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.id = `filter-${category.name.replace(/\s+/g, '-').toLowerCase()}-${subcategory.name.replace(/\s+/g, '-').toLowerCase()}`;
            checkbox.className = 'mr-2 h-4 w-4 text-blue-600 rounded';
            checkbox.addEventListener('change', () => handleFilterChange(subcategory, checkbox.checked));

            const label = document.createElement('label');
            label.htmlFor = checkbox.id;
            label.className = 'text-sm text-gray-700 cursor-pointer';
            label.textContent = subcategory.name;

            subDiv.appendChild(checkbox);
            subDiv.appendChild(label);
            subcategoriesDiv.appendChild(subDiv);
        });

        categoryDiv.appendChild(subcategoriesDiv);
        filterCategories.appendChild(categoryDiv);

        // Add spacing between categories
        if (category !== filterConfig[filterConfig.length - 1]) {
            const spacer = document.createElement('div');
            spacer.className = 'border-t border-gray-200 my-4';
            filterCategories.appendChild(spacer);
        }
    });
}

// Handle filter changes
function handleFilterChange(subcategory, isChecked) {
    const filterId = `${subcategory.name}|${subcategory.hashtags.join(',')}`;
    
    if (isChecked) {
        activeFilters.add(filterId);
    } else {
        activeFilters.delete(filterId);
    }
    
    displayWreaths();
    updateItemCount();
}

// Clear all filters and search
function clearAllFiltersHandler() {
    activeFilters.clear();
    currentSearchTerm = '';
    searchInput.value = '';
    updateClearSearchButton();
    
    // Uncheck all filter checkboxes
    const checkboxes = filterCategories.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach(checkbox => {
        checkbox.checked = false;
    });
    
    displayWreaths();
    updateItemCount();
}

// Filter wreaths based on active filters and search
function getFilteredWreaths() {
    let filtered = wreathsData;

    // Apply availability filter
    if (showAvailableOnly.checked) {
        filtered = filtered.filter(w => !w.sold);
    }

    // Apply search filter
    if (currentSearchTerm.trim()) {
        const searchTerm = currentSearchTerm.toLowerCase();
        filtered = filtered.filter(wreath => {
            // Search in title
            if (wreath.title && wreath.title.toLowerCase().includes(searchTerm)) {
                return true;
            }
            
            // Search in description
            if (wreath.description && wreath.description.toLowerCase().includes(searchTerm)) {
                return true;
            }
            
            // Search in hashtags
            if (wreath.hashtags && wreath.hashtags.some(tag => 
                tag.toLowerCase().includes(searchTerm)
            )) {
                return true;
            }
            
            return false;
        });
    }

    // Apply category filters (AND logic)
    if (activeFilters.size > 0) {
        filtered = filtered.filter(wreath => {
            return Array.from(activeFilters).every(filterId => {
                const [filterName, hashtagsStr] = filterId.split('|');
                const hashtags = hashtagsStr.split(',');
                
                // Check if wreath has any of the hashtags for this filter
                return hashtags.some(hashtag => {
                    return wreath.hashtags && wreath.hashtags.some(wreathTag => 
                        wreathTag.toLowerCase() === hashtag.toLowerCase()
                    );
                });
            });
        });
    }

    return filtered;
}

// Clean title for proper sorting (handles quotes and punctuation)
function cleanTitleForSorting(title) {
    if (!title) return '';
    // Remove leading quotes, spaces, and other punctuation for sorting
    return title.toLowerCase()
        .replace(/^[\s"'`~!@#$%^&*()_+\-=\[\]{}|;:,.<>?/\\]+/, '')
        .trim();
}

// Sort wreaths
function sortWreaths(wreaths, sortBy) {
    const sorted = [...wreaths];
    
    switch (sortBy) {
        case 'featured':
            // Featured first, then by date added (newest first)
            return sorted.sort((a, b) => {
                if (a.featured && !b.featured) return -1;
                if (!a.featured && b.featured) return 1;
                return new Date(b.dateAdded || 0) - new Date(a.dateAdded || 0);
            });
            
        case 'az':
            return sorted.sort((a, b) => {
                const cleanA = cleanTitleForSorting(a.title);
                const cleanB = cleanTitleForSorting(b.title);
                return cleanA.localeCompare(cleanB);
            });
            
        case 'za':
            return sorted.sort((a, b) => {
                const cleanA = cleanTitleForSorting(a.title);
                const cleanB = cleanTitleForSorting(b.title);
                return cleanB.localeCompare(cleanA);
            });
            
        case 'price-low':
            return sorted.sort((a, b) => (a.localPrice || 0) - (b.localPrice || 0));
            
        case 'price-high':
            return sorted.sort((a, b) => (b.localPrice || 0) - (a.localPrice || 0));
            
        case 'newest':
            return sorted.sort((a, b) => new Date(b.dateAdded || 0) - new Date(a.dateAdded || 0));
            
        default:
            return sorted;
    }
}

// Display wreaths in grid
function displayWreaths() {
    const filteredWreaths = getFilteredWreaths();
    const sortedWreaths = sortWreaths(filteredWreaths, currentSort);
    
    wreathGrid.innerHTML = '';
    
    if (sortedWreaths.length === 0) {
        wreathGrid.innerHTML = '<div class="col-span-full text-center py-8"><p class="text-gray-500">No wreaths found matching your filters.</p></div>';
        loadingMessage.style.display = 'none';
        return;
    }
    
    sortedWreaths.forEach(wreath => {
        const wreathCard = createWreathCard(wreath);
        wreathGrid.appendChild(wreathCard);
    });
    
    loadingMessage.style.display = 'none';
}

// Create individual wreath card
function createWreathCard(wreath) {
    const card = document.createElement('div');
    card.className = `bg-white rounded-lg shadow-sm overflow-hidden cursor-pointer hover:shadow-md transition-shadow relative ${wreath.sold ? 'opacity-75' : ''}`;
    card.onclick = () => openWreathModal(wreath);
    
    const imageUrl = wreath.images && wreath.images.length > 0 ? wreath.images[0] : '';
    
    card.innerHTML = `
        ${wreath.sold ? '<div class="absolute top-2 left-2 bg-red-500 text-white px-2 py-1 text-xs rounded z-10">SOLD</div>' : ''}
        ${wreath.featured ? '<div class="absolute top-2 right-2 bg-yellow-500 text-white px-2 py-1 text-xs rounded z-10"><i class="fas fa-star"></i></div>' : ''}
        <div class="aspect-square bg-gray-100">
            ${imageUrl ? `
                <img 
                    src="${imageUrl}" 
                    alt="${wreath.title}"
                    class="w-full h-full object-cover"
                    loading="lazy"
                    onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';"
                />
                <div class="w-full h-full hidden items-center justify-center text-gray-400 text-sm">
                    ${wreath.title}
                </div>
            ` : `
                <div class="w-full h-full flex items-center justify-center text-gray-400 text-sm">
                    ${wreath.title}
                </div>
            `}
        </div>
        <div class="p-3">
            <h3 class="font-medium text-sm mb-1 line-clamp-2">${wreath.title}</h3>
            <p class="text-lg font-bold text-green-600">$${wreath.localPrice} Local Pickup</p>
            <p class="text-xs text-gray-500">Shipping $10-30</p>
        </div>
    `;
    
    return card;
}

// Open wreath detail modal
function openWreathModal(wreath) {
    currentWreath = wreath;
    currentImageIndex = 0;
    
    // Populate modal content
    modalTitle.textContent = wreath.title;
    modalPrice.textContent = `$${wreath.localPrice} Local Pickup`;
    modalDescription.textContent = wreath.description || '';
    
    // Show/hide sold badge
    if (wreath.sold) {
        soldBadge.classList.remove('hidden');
        orderButton.style.display = 'none';
    } else {
        soldBadge.classList.add('hidden');
        orderButton.style.display = 'block';
    }
    
    // Populate hashtags
    modalHashtags.innerHTML = '';
    if (wreath.hashtags && wreath.hashtags.length > 0) {
        wreath.hashtags.forEach(tag => {
            const tagElement = document.createElement('span');
            tagElement.className = 'bg-gray-100 text-gray-700 px-2 py-1 text-xs rounded';
            tagElement.textContent = `#${tag}`;
            modalHashtags.appendChild(tagElement);
        });
    }
    
    // Setup carousel
    setupCarousel();
    
    // Show modal
    wreathModal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

// Setup image carousel
function setupCarousel() {
    if (!currentWreath.images || currentWreath.images.length === 0) {
        carouselImage.style.display = 'none';
        prevImageBtn.style.display = 'none';
        nextImageBtn.style.display = 'none';
        imageDots.innerHTML = '';
        return;
    }
    
    // Show first image
    carouselImage.src = currentWreath.images[currentImageIndex];
    carouselImage.style.display = 'block';
    
    // Show/hide navigation buttons
    if (currentWreath.images.length > 1) {
        prevImageBtn.style.display = 'flex';
        nextImageBtn.style.display = 'flex';
        setupImageDots();
    } else {
        prevImageBtn.style.display = 'none';
        nextImageBtn.style.display = 'none';
        imageDots.innerHTML = '';
    }
}

// Setup image dots
function setupImageDots() {
    imageDots.innerHTML = '';
    currentWreath.images.forEach((_, index) => {
        const dot = document.createElement('button');
        dot.className = `dot ${index === currentImageIndex ? 'active' : ''}`;
        dot.onclick = () => setImageIndex(index);
        imageDots.appendChild(dot);
    });
}

// Navigate to specific image
function setImageIndex(index) {
    currentImageIndex = index;
    carouselImage.src = currentWreath.images[currentImageIndex];
    updateImageDots();
}

// Update image dots
function updateImageDots() {
    const dots = imageDots.querySelectorAll('.dot');
    dots.forEach((dot, index) => {
        dot.classList.toggle('active', index === currentImageIndex);
    });
}

// Navigate to previous image
function prevImage() {
    if (currentWreath.images && currentWreath.images.length > 1) {
        currentImageIndex = currentImageIndex === 0 ? 
            currentWreath.images.length - 1 : currentImageIndex - 1;
        setImageIndex(currentImageIndex);
    }
}

// Navigate to next image
function nextImage() {
    if (currentWreath.images && currentWreath.images.length > 1) {
        currentImageIndex = currentImageIndex === currentWreath.images.length - 1 ? 
            0 : currentImageIndex + 1;
        setImageIndex(currentImageIndex);
    }
}

// Close wreath modal
function closeWreathModal() {
    wreathModal.classList.remove('active');
    document.body.style.overflow = 'auto';
    currentWreath = null;
}

// Open order modal
function openOrderModal() {
    if (!currentWreath) return;
    
    // Populate order info
    orderTitle.textContent = currentWreath.title;
    orderPrice.textContent = `$${currentWreath.localPrice} Local Pickup`;
    formWreathTitle.value = currentWreath.title;
    formWreathPrice.value = currentWreath.localPrice;
    
    // Show order modal
    orderModal.classList.add('active');
}

// Close order modal
function closeOrderModalHandler() {
    orderModal.classList.remove('active');
}

// Update item count
function updateItemCount() {
    const filteredWreaths = getFilteredWreaths();
    const count = filteredWreaths.length;
    const featuredCount = filteredWreaths.filter(w => w.featured).length;
    
    let countText = `${count} wreath${count !== 1 ? 's' : ''}`;
    if (featuredCount > 0) {
        countText += ` (${featuredCount} featured)`;
    }
    
    itemCount.textContent = countText;
}

// Mobile sidebar functions
function openMobileSidebar() {
    filterSidebar.classList.add('open');
    sidebarOverlay.classList.add('open');
    document.body.style.overflow = 'hidden';
}

function closeMobileSidebar() {
    filterSidebar.classList.remove('open');
    sidebarOverlay.classList.remove('open');
    document.body.style.overflow = 'auto';
}

// Handle search input
function handleSearchInput() {
    currentSearchTerm = searchInput.value;
    updateClearSearchButton();
    displayWreaths();
    updateItemCount();
}

// Handle clear search
function handleClearSearch() {
    currentSearchTerm = '';
    searchInput.value = '';
    updateClearSearchButton();
    displayWreaths();
    updateItemCount();
}

// Update clear search button visibility
function updateClearSearchButton() {
    if (currentSearchTerm.trim()) {
        clearSearch.classList.remove('hidden');
    } else {
        clearSearch.classList.add('hidden');
    }
}

// Setup event listeners
function setupEventListeners() {
    // Filter and sort controls
    showAvailableOnly.addEventListener('change', () => {
        displayWreaths();
        updateItemCount();
    });
    
    sortSelect.addEventListener('change', (e) => {
        currentSort = e.target.value;
        displayWreaths();
    });
    
    clearAllFilters.addEventListener('click', clearAllFiltersHandler);
    
    // Mobile sidebar controls
    mobileFilterToggle.addEventListener('click', openMobileSidebar);
    closeSidebar.addEventListener('click', closeMobileSidebar);
    sidebarOverlay.addEventListener('click', closeMobileSidebar);
    
    // Modal close buttons
    closeModal.addEventListener('click', closeWreathModal);
    closeOrderModal.addEventListener('click', closeOrderModalHandler);
    
    // Order button
    orderButton.addEventListener('click', openOrderModal);
    
    // Carousel navigation
    prevImageBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        prevImage();
    });
    
    nextImageBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        nextImage();
    });
    
    // Close modals when clicking outside
    wreathModal.addEventListener('click', (e) => {
        if (e.target === wreathModal) {
            closeWreathModal();
        }
    });
    
    orderModal.addEventListener('click', (e) => {
        if (e.target === orderModal) {
            closeOrderModalHandler();
        }
    });
    
    // Keyboard navigation
    document.addEventListener('keydown', (e) => {
        if (wreathModal.classList.contains('active')) {
            if (e.key === 'Escape') {
                closeWreathModal();
            } else if (e.key === 'ArrowLeft') {
                prevImage();
            } else if (e.key === 'ArrowRight') {
                nextImage();
            }
        }
        
        if (orderModal.classList.contains('active') && e.key === 'Escape') {
            closeOrderModalHandler();
        }

        // Close mobile sidebar on escape
        if (filterSidebar.classList.contains('open') && e.key === 'Escape') {
            closeMobileSidebar();
        }
    });
    
    // Form submission handling
    const orderForm = document.querySelector('form[name="wreath-orders"]');
    if (orderForm) {
        orderForm.addEventListener('submit', (e) => {
            // Form will redirect to thank-you.html automatically
            // No need for custom handling
        });

    // Search functionality
    searchInput.addEventListener('input', handleSearchInput);
    clearSearch.addEventListener('click', handleClearSearch);
    
    // Clear search on escape key
    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            handleClearSearch();
        }
    });
    }
}