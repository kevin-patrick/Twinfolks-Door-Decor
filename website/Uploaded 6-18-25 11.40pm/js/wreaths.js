// Main website JavaScript for Twinfolks Door Decor

let wreathsData = [];
let currentWreath = null;
let currentImageIndex = 0;

// DOM elements
const wreathGrid = document.getElementById('wreathGrid');
const loadingMessage = document.getElementById('loadingMessage');
const itemCount = document.getElementById('itemCount');
const showAvailableOnly = document.getElementById('showAvailableOnly');

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
    loadWreaths();
    setupEventListeners();
});

// Load wreaths data
async function loadWreaths() {
    try {
        const response = await fetch('data/wreaths.json');
        if (!response.ok) {
            throw new Error('Failed to load wreaths data');
        }
        wreathsData = await response.json();
        displayWreaths();
        updateItemCount();
    } catch (error) {
        console.error('Error loading wreaths:', error);
        loadingMessage.innerHTML = '<p class="text-red-500">Error loading wreaths. Please try again later.</p>';
    }
}

// Display wreaths in grid
function displayWreaths() {
    const filteredWreaths = showAvailableOnly.checked ? 
        wreathsData.filter(w => !w.sold) : wreathsData;
    
    wreathGrid.innerHTML = '';
    
    if (filteredWreaths.length === 0) {
        wreathGrid.innerHTML = '<div class="col-span-full text-center py-8"><p class="text-gray-500">No wreaths found.</p></div>';
        loadingMessage.style.display = 'none';
        return;
    }
    
    filteredWreaths.forEach(wreath => {
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
    const filteredWreaths = showAvailableOnly.checked ? 
        wreathsData.filter(w => !w.sold) : wreathsData;
    
    const count = filteredWreaths.length;
    itemCount.textContent = `${count} wreath${count !== 1 ? 's' : ''}`;
}

// Setup event listeners
function setupEventListeners() {
    // Filter checkbox
    showAvailableOnly.addEventListener('change', () => {
        displayWreaths();
        updateItemCount();
    });
    
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
    });
    
    // Form submission handling
    const orderForm = document.querySelector('form[name="wreath-orders"]');
    if (orderForm) {
        orderForm.addEventListener('submit', (e) => {
            // Form will redirect to thank-you.html automatically
            // No need for custom handling
        });
    }
}