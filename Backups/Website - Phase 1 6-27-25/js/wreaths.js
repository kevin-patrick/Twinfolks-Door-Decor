/* 
 * Filename: wreaths.js
 * Location: website/js/wreaths.js
 * Purpose: Enhanced website JavaScript with filtering, sorting, and category management
 */

// Main website JavaScript for Twinfolks Door Decor - Enhanced Version

let wreathsData = [];
let filterConfig = {};
let currentWreath = null;
let currentImageIndex = 0;
let activeFilters = new Set();
let currentSort = 'featured';

// DOM elements
const wreathGrid = document.getElementById('wreathGrid');
const loadingMessage = document.getElementById('loadingMessage');
const itemCount = document.getElementById('itemCount');
const showAvailableOnly = document.getElementById('showAvailableOnly');
const filtersContainer = document.getElementById('filtersContainer');
const sortSelect = document.getElementById('sortSelect');
const clearFiltersBtn = document.getElementById('clearFiltersBtn');

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
    initializeApp();
});

async function initializeApp() {
    try {
        // Load both wreaths and filter configuration
        await Promise.all([
            loadWreaths(),
            loadFilterConfig()
        ]);
        
        setupFilterUI();
        setupEventListeners();
        applyFiltersAndSort();
    } catch (error) {
        console.error('Error initializing app:', error);
        loadingMessage.innerHTML = '<p class="text-red-500">Error loading application. Please refresh the page.</p>';
    }
}

// Load wreaths data
async function loadWreaths() {
    try {
        const response = await fetch('wreaths.json');
        if (!response.ok) {
            throw new Error('Failed to load wreaths data');
        }
        wreathsData = await response.json();
        
        // Add featured field if it doesn't exist (backward compatibility)
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
            throw new Error('Failed to load filter configuration');
        }
        filterConfig = await response.json();
    } catch (error) {
        console.error('Error loading filter config:', error);
        // Create basic config if file doesn't exist
        filterConfig = {
            categories: [],
            sortOptions: [
                { id: 'featured', name: 'Featured', default: true },
                { id: 'alphabetical-az', name: 'A-Z' },
                { id: 'alphabetical-za', name: 'Z-A' },
                { id: 'price-low', name: 'Price: Low to High' },
                { id: 'price-high', name: 'Price: High to Low' }
            ]
        };
    }
}

// Setup filter UI
function setupFilterUI() {
    // Clear existing filters
    filtersContainer.innerHTML = '';
    
    // Create availability filter
    const availabilityFilter = document.createElement('div');
    availabilityFilter.className = 'filter-group';
    availabilityFilter.innerHTML = `
        <div class="flex items-center space-x-2">
            <input type="checkbox" id="showAvailableOnly" class="rounded" />
            <label for="showAvailableOnly" class="text-sm font-medium">Available Only</label>
        </div>
    `;
    filtersContainer.appendChild(availabilityFilter);
    
    // Create category filters
    filterConfig.categories.forEach(category => {
        const categoryDiv = document.createElement('div');
        categoryDiv.className = 'filter-group';
        
        const categoryHeader = document.createElement('h4');
        categoryHeader.className = 'text-sm font-semibold text-gray-700 mb-2';
        categoryHeader.textContent = category.name;
        categoryDiv.appendChild(categoryHeader);
        
        const subcategoriesDiv = document.createElement('div');
        subcategoriesDiv.className = 'space-y-1';
        
        category.subcategories.forEach(subcategory => {
            const subcategoryDiv = document.createElement('div');
            subcategoryDiv.className = 'flex items-center space-x-2';
            subcategoryDiv.innerHTML = `
                <input type="checkbox" 
                       id="filter-${subcategory.id}" 
                       value="${subcategory.id}"
                       data-hashtags="${subcategory.hashtags.join(',')}"
                       class="category-filter rounded" />
                <label for="filter-${subcategory.id}" class="text-sm">${subcategory.name}</label>
            `;
            subcategoriesDiv.appendChild(subcategoryDiv);
        });
        
        categoryDiv.appendChild(subcategoriesDiv);
        filtersContainer.appendChild(categoryDiv);
    });
    
    // Setup sort dropdown
    sortSelect.innerHTML = '';
    filterConfig.sortOptions.forEach(option => {
        const optionElement = document.createElement('option');
        optionElement.value = option.id;
        optionElement.textContent = option.name;
        if (option.default) {
            optionElement.selected = true;
            currentSort = option.id;
        }
        sortSelect.appendChild(optionElement);
    });
}

// Apply filters and sorting
function applyFiltersAndSort() {
    let filteredWreaths = [...wreathsData];
    
    // Apply availability filter
    const availabilityCheckbox = document.getElementById('showAvailableOnly');
    if (availabilityCheckbox && availabilityCheckbox.checked) {
        filteredWreaths = filteredWreaths.filter(w => !w.sold);
    }
    
    // Apply category filters (AND logic)
    const categoryFilters = document.querySelectorAll('.category-filter:checked');
    if (categoryFilters.length > 0) {
        categoryFilters.forEach(filter => {
            const hashtags = filter.dataset.hashtags.split(',');
            filteredWreaths = filteredWreaths.filter(wreath => {
                if (!wreath.hashtags) return false;
                return hashtags.some(hashtag => 
                    wreath.hashtags.some(wreathTag => 
                        wreathTag.toLowerCase().includes(hashtag.toLowerCase())
                    )
                );
            });
        });
    }
    
    // Apply sorting
    filteredWreaths = sortWreaths(filteredWreaths, currentSort);
    
    // Display results
    displayWreaths(filteredWreaths);
    updateItemCount(filteredWreaths.length);
    updateClearFiltersButton();
}

// Sort wreaths based on selected option
function sortWreaths(wreaths, sortOption) {
    const sortedWreaths = [...wreaths];
    
    switch (sortOption) {
        case 'featured':
            return sortedWreaths.sort((a, b) => {
                // Featured items first, then by date added (newest first)
                if (a.featured && !b.featured) return -1;
                if (!a.featured && b.featured) return 1;
                const dateA = new Date(a.dateAdded || '1970-01-01');
                const dateB = new Date(b.dateAdded || '1970-01-01');
                return dateB - dateA;
            });
            
        case 'alphabetical-az':
            return sortedWreaths.sort((a, b) => a.title.localeCompare(b.title));
            
        case 'alphabetical-za':
            return sortedWreaths.sort((a, b) => b.title.localeCompare(a.title));
            
        case 'price-low':
            return sortedWreaths.sort((a, b) => (a.localPrice || 0) - (b.localPrice || 0));
            
        case 'price-high':
            return sortedWreaths.sort((a, b) => (b.localPrice || 0) - (a.localPrice || 0));
            
        case 'newest':
            return sortedWreaths.sort((a, b) => {
                const dateA = new Date(a.dateAdded || '1970-01-01');
                const dateB = new Date(b.dateAdded || '1970-01-01');
                return dateB - dateA;
            });
            
        default:
            return sortedWreaths;
    }
}

// Display wreaths in grid
function displayWreaths(wreaths) {
    wreathGrid.innerHTML = '';
    
    if (wreaths.length === 0) {
        wreathGrid.innerHTML = '<div class="col-span-full text-center py-8"><p class="text-gray-500">No wreaths match your current filters.</p></div>';
        loadingMessage.style.display = 'none';
        return;
    }
    
    wreaths.forEach(wreath => {
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
        ${wreath.featured ? '<div class="absolute top-2 right-2 bg-yellow-500 text-white px-2 py-1 text-xs rounded z-10">★ FEATURED</div>' : ''}
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

// Clear all filters
function clearAllFilters() {
    // Uncheck all filter checkboxes
    document.querySelectorAll('.category-filter').forEach(checkbox => {
        checkbox.checked = false;
    });
    
    const availabilityCheckbox = document.getElementById('showAvailableOnly');
    if (availabilityCheckbox) {
        availabilityCheckbox.checked = false;
    }
    
    // Reset sort to default
    const defaultSort = filterConfig.sortOptions.find(option => option.default);
    if (defaultSort) {
        currentSort = defaultSort.id;
        sortSelect.value = defaultSort.id;
    }
    
    // Apply filters
    applyFiltersAndSort();
}

// Update clear filters button visibility
function updateClearFiltersButton() {
    const hasActiveFilters = document.querySelectorAll('.category-filter:checked').length > 0 ||
                           document.getElementById('showAvailableOnly')?.checked;
    
    if (clearFiltersBtn) {
        clearFiltersBtn.style.display = hasActiveFilters ? 'block' : 'none';
    }
}

// Update item count
function updateItemCount(count) {
    if (itemCount) {
        itemCount.textContent = `${count} wreath${count !== 1 ? 's' : ''}`;
    }
}

// Setup event listeners
function setupEventListeners() {
    // Filter change events
    document.addEventListener('change', (e) => {
        if (e.target.classList.contains('category-filter') || e.target.id === 'showAvailableOnly') {
            applyFiltersAndSort();
        }
    });
    
    // Sort change event
    if (sortSelect) {
        sortSelect.addEventListener('change', (e) => {
            currentSort = e.target.value;
            applyFiltersAndSort();
        });
    }
    
    // Clear filters button
    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', clearAllFilters);
    }
    
    // Modal close buttons
    if (closeModal) closeModal.addEventListener('click', closeWreathModal);
    if (closeOrderModal) closeOrderModal.addEventListener('click', closeOrderModalHandler);
    
    // Order button
    if (orderButton) orderButton.addEventListener('click', openOrderModal);
    
    // Carousel navigation
    if (prevImageBtn) {
        prevImageBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            prevImage();
        });
    }
    
    if (nextImageBtn) {
        nextImageBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            nextImage();
        });
    }
    
    // Close modals when clicking outside
    if (wreathModal) {
        wreathModal.addEventListener('click', (e) => {
            if (e.target === wreathModal) {
                closeWreathModal();
            }
        });
    }
    
    if (orderModal) {
        orderModal.addEventListener('click', (e) => {
            if (e.target === orderModal) {
                closeOrderModalHandler();
            }
        });
    }
    
    // Keyboard navigation
    document.addEventListener('keydown', (e) => {
        if (wreathModal && wreathModal.classList.contains('active')) {
            if (e.key === 'Escape') {
                closeWreathModal();
            } else if (e.key === 'ArrowLeft') {
                prevImage();
            } else if (e.key === 'ArrowRight') {
                nextImage();
            }
        }
        
        if (orderModal && orderModal.classList.contains('active') && e.key === 'Escape') {
            closeOrderModalHandler();
        }
    });
}

// Modal and carousel functions (keeping existing functionality)
function openWreathModal(wreath) {
    currentWreath = wreath;
    currentImageIndex = 0;
    
    // Populate modal content
    if (modalTitle) modalTitle.textContent = wreath.title;
    if (modalPrice) modalPrice.textContent = `$${wreath.localPrice} Local Pickup`;
    if (modalDescription) modalDescription.textContent = wreath.description || '';
    
    // Show/hide sold badge
    if (wreath.sold) {
        if (soldBadge) soldBadge.classList.remove('hidden');
        if (orderButton) orderButton.style.display = 'none';
    } else {
        if (soldBadge) soldBadge.classList.add('hidden');
        if (orderButton) orderButton.style.display = 'block';
    }
    
    // Populate hashtags
    if (modalHashtags) {
        modalHashtags.innerHTML = '';
        if (wreath.hashtags && wreath.hashtags.length > 0) {
            wreath.hashtags.forEach(tag => {
                const tagElement = document.createElement('span');
                tagElement.className = 'bg-gray-100 text-gray-700 px-2 py-1 text-xs rounded';
                tagElement.textContent = `#${tag}`;
                modalHashtags.appendChild(tagElement);
            });
        }
    }
    
    // Setup carousel
    setupCarousel();
    
    // Show modal
    if (wreathModal) {
        wreathModal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function setupCarousel() {
    if (!currentWreath.images || currentWreath.images.length === 0) {
        if (carouselImage) carouselImage.style.display = 'none';
        if (prevImageBtn) prevImageBtn.style.display = 'none';
        if (nextImageBtn) nextImageBtn.style.display = 'none';
        if (imageDots) imageDots.innerHTML = '';
        return;
    }
    
    // Show first image
    if (carouselImage) {
        carouselImage.src = currentWreath.images[currentImageIndex];
        carouselImage.style.display = 'block';
    }
    
    // Show/hide navigation buttons
    if (currentWreath.images.length > 1) {
        if (prevImageBtn) prevImageBtn.style.display = 'flex';
        if (nextImageBtn) nextImageBtn.style.display = 'flex';
        setupImageDots();
    } else {
        if (prevImageBtn) prevImageBtn.style.display = 'none';
        if (nextImageBtn) nextImageBtn.style.display = 'none';
        if (imageDots) imageDots.innerHTML = '';
    }
}

function setupImageDots() {
    if (!imageDots) return;
    
    imageDots.innerHTML = '';
    currentWreath.images.forEach((_, index) => {
        const dot = document.createElement('button');
        dot.className = `dot ${index === currentImageIndex ? 'active' : ''}`;
        dot.onclick = () => setImageIndex(index);
        imageDots.appendChild(dot);
    });
}

function setImageIndex(index) {
    currentImageIndex = index;
    if (carouselImage) {
        carouselImage.src = currentWreath.images[currentImageIndex];
    }
    updateImageDots();
}

function updateImageDots() {
    if (!imageDots) return;
    
    const dots = imageDots.querySelectorAll('.dot');
    dots.forEach((dot, index) => {
        dot.classList.toggle('active', index === currentImageIndex);
    });
}

function prevImage() {
    if (currentWreath.images && currentWreath.images.length > 1) {
        currentImageIndex = currentImageIndex === 0 ? 
            currentWreath.images.length - 1 : currentImageIndex - 1;
        setImageIndex(currentImageIndex);
    }
}

function nextImage() {
    if (currentWreath.images && currentWreath.images.length > 1) {
        currentImageIndex = currentImageIndex === currentWreath.images.length - 1 ? 
            0 : currentImageIndex + 1;
        setImageIndex(currentImageIndex);
    }
}

function closeWreathModal() {
    if (wreathModal) {
        wreathModal.classList.remove('active');
        document.body.style.overflow = 'auto';
        currentWreath = null;
    }
}

function openOrderModal() {
    if (!currentWreath) return;
    
    // Populate order info
    if (orderTitle) orderTitle.textContent = currentWreath.title;
    if (orderPrice) orderPrice.textContent = `$${currentWreath.localPrice} Local Pickup`;
    if (formWreathTitle) formWreathTitle.value = currentWreath.title;
    if (formWreathPrice) formWreathPrice.value = currentWreath.localPrice;
    
    // Show order modal
    if (orderModal) {
        orderModal.classList.add('active');
    }
}

function closeOrderModalHandler() {
    if (orderModal) {
        orderModal.classList.remove('active');
    }
}