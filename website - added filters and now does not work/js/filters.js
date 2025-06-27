/*
 * File: /js/filters.js
 * Purpose: Advanced filtering and sorting system for wreaths
 * Dependencies: filter-config.json
 */

class FilteringSystem {
    constructor() {
        this.config = null;
        this.items = [];
        this.filteredItems = [];
        this.activeFilters = {
            categories: {},
            showAvailableOnly: false,
            searchText: ''
        };
        this.currentSort = 'featured';
        this.callbacks = {
            onFilterChange: null,
            onItemsUpdated: null
        };
    }

    // Initialize the filtering system
    async init(configPath = '/config/filter-config.json') {
        try {
            const response = await fetch(configPath);
            this.config = await response.json();
            this.loadSavedFilters();
            console.log('Filtering system initialized');
        } catch (error) {
            console.error('Failed to load filter configuration:', error);
            // Fallback to basic functionality if config fails
            this.config = { categories: [], sortOptions: [] };
        }
    }

    // Set the items to be filtered
    setItems(items) {
        this.items = items;
        this.applyFilters();
    }

    // Set callback functions
    setCallbacks(callbacks) {
        this.callbacks = { ...this.callbacks, ...callbacks };
    }

    // Generate the filter UI HTML
    generateFilterUI() {
        if (!this.config || !this.config.categories) return '';

        let html = '<div class="filter-container">';
        
        // Add search box
        html += `
            <div class="filter-section search-section">
                <h4>Search</h4>
                <input type="text" id="search-input" placeholder="Search wreaths..." 
                       value="${this.activeFilters.searchText}" 
                       class="search-input">
            </div>
        `;

        // Add show available only toggle
        html += `
            <div class="filter-section available-section">
                <label class="filter-checkbox">
                    <input type="checkbox" id="show-available-only" 
                           ${this.activeFilters.showAvailableOnly ? 'checked' : ''}>
                    <span class="checkmark"></span>
                    Show Available Only
                </label>
            </div>
        `;

        // Add sort dropdown
        html += `
            <div class="filter-section sort-section">
                <h4>Sort By</h4>
                <select id="sort-select" class="sort-dropdown">
                    ${this.config.sortOptions.map(option => 
                        `<option value="${option.id}" ${this.currentSort === option.id ? 'selected' : ''}>
                            ${option.label}
                        </option>`
                    ).join('')}
                </select>
            </div>
        `;

        // Add filter categories
        this.config.categories.forEach(category => {
            if (!category.enabled) return;

            html += `
                <div class="filter-section category-section" data-category="${category.id}">
                    <h4>${category.name}</h4>
                    <div class="filter-options">
            `;

            category.options.forEach(option => {
                const isChecked = this.isFilterActive(category.id, option.id);
                const inputType = category.type === 'radio' ? 'radio' : 'checkbox';
                const inputName = category.type === 'radio' ? `filter-${category.id}` : '';

                html += `
                    <label class="filter-${inputType}">
                        <input type="${inputType}" 
                               ${inputName ? `name="${inputName}"` : ''}
                               data-category="${category.id}" 
                               data-option="${option.id}"
                               ${isChecked ? 'checked' : ''}>
                        <span class="${inputType === 'radio' ? 'radio-mark' : 'checkmark'}"></span>
                        ${option.label}
                    </label>
                `;
            });

            html += `
                    </div>
                </div>
            `;
        });

        html += '</div>';
        return html;
    }

    // Bind event listeners to the filter UI
    bindFilterEvents() {
        // Search input
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.activeFilters.searchText = e.target.value;
                this.applyFilters();
                this.saveFilters();
            });
        }

        // Show available only checkbox
        const availableCheckbox = document.getElementById('show-available-only');
        if (availableCheckbox) {
            availableCheckbox.addEventListener('change', (e) => {
                this.activeFilters.showAvailableOnly = e.target.checked;
                this.applyFilters();
                this.saveFilters();
            });
        }

        // Sort dropdown
        const sortSelect = document.getElementById('sort-select');
        if (sortSelect) {
            sortSelect.addEventListener('change', (e) => {
                this.currentSort = e.target.value;
                this.applySorting();
                this.saveFilters();
            });
        }

        // Filter checkboxes and radio buttons
        document.querySelectorAll('.filter-container input[data-category]').forEach(input => {
            input.addEventListener('change', (e) => {
                const category = e.target.dataset.category;
                const option = e.target.dataset.option;
                
                if (e.target.type === 'radio') {
                    // For radio buttons, clear other selections in the same category
                    this.activeFilters.categories[category] = e.target.checked ? [option] : [];
                } else {
                    // For checkboxes, add/remove from array
                    if (!this.activeFilters.categories[category]) {
                        this.activeFilters.categories[category] = [];
                    }
                    
                    if (e.target.checked) {
                        if (!this.activeFilters.categories[category].includes(option)) {
                            this.activeFilters.categories[category].push(option);
                        }
                    } else {
                        this.activeFilters.categories[category] = 
                            this.activeFilters.categories[category].filter(o => o !== option);
                    }
                }
                
                this.applyFilters();
                this.saveFilters();
            });
        });
    }

    // Check if a specific filter option is active
    isFilterActive(categoryId, optionId) {
        return this.activeFilters.categories[categoryId] && 
               this.activeFilters.categories[categoryId].includes(optionId);
    }

    // Apply all active filters
    applyFilters() {
        let filtered = [...this.items];

        // Apply search filter
        if (this.activeFilters.searchText) {
            const searchTerm = this.activeFilters.searchText.toLowerCase();
            filtered = filtered.filter(item => 
                (item.title && item.title.toLowerCase().includes(searchTerm)) ||
                (item.description && item.description.toLowerCase().includes(searchTerm)) ||
                (item.hashtags && item.hashtags.some(tag => 
                    tag.toLowerCase().includes(searchTerm)
                ))
            );
        }

        // Apply availability filter
        if (this.activeFilters.showAvailableOnly) {
            filtered = filtered.filter(item => 
                !item.sold && item.available !== false
            );
        }

        // Apply category filters
        Object.keys(this.activeFilters.categories).forEach(categoryId => {
            const selectedOptions = this.activeFilters.categories[categoryId];
            if (selectedOptions && selectedOptions.length > 0) {
                const category = this.config.categories.find(c => c.id === categoryId);
                if (category) {
                    filtered = filtered.filter(item => {
                        return selectedOptions.some(optionId => {
                            const option = category.options.find(o => o.id === optionId);
                            if (option && item.hashtags) {
                                return option.hashtags.some(hashtag => 
                                    item.hashtags.includes(hashtag)
                                );
                            }
                            return false;
                        });
                    });
                }
            }
        });

        this.filteredItems = filtered;
        this.applySorting();
    }

    // Apply sorting to filtered items
    applySorting() {
        const sortOption = this.config.sortOptions.find(s => s.id === this.currentSort);
        if (!sortOption) {
            this.notifyItemsUpdated();
            return;
        }

        this.filteredItems.sort((a, b) => {
            let aValue, bValue;

            if (sortOption.field === 'hashtags' && sortOption.value) {
                // Special case for featured items (hashtag-based)
                aValue = a.hashtags && a.hashtags.includes(sortOption.value) ? 1 : 0;
                bValue = b.hashtags && b.hashtags.includes(sortOption.value) ? 1 : 0;
            } else if (sortOption.field === 'price') {
                aValue = this.parsePrice(a.price);
                bValue = this.parsePrice(b.price);
            } else if (sortOption.field === 'dateAdded') {
                aValue = new Date(a.dateAdded || a.created || 0);
                bValue = new Date(b.dateAdded || b.created || 0);
            } else {
                aValue = a[sortOption.field] || '';
                bValue = b[sortOption.field] || '';
            }

            if (sortOption.direction === 'desc') {
                return bValue > aValue ? 1 : bValue < aValue ? -1 : 0;
            } else {
                return aValue > bValue ? 1 : aValue < bValue ? -1 : 0;
            }
        });

        this.notifyItemsUpdated();
    }

    // Parse price from string (e.g., "$45.00" => 45)
    parsePrice(priceStr) {
        if (!priceStr) return 0;
        const match = priceStr.toString().match(/[\d.]+/);
        return match ? parseFloat(match[0]) : 0;
    }

    // Get the current filtered and sorted items
    getFilteredItems() {
        return this.filteredItems;
    }

    // Clear all filters
    clearAllFilters() {
        this.activeFilters = {
            categories: {},
            showAvailableOnly: false,
            searchText: ''
        };
        this.currentSort = 'featured';
        this.applyFilters();
        this.saveFilters();
        
        // Update UI
        document.querySelectorAll('.filter-container input').forEach(input => {
            if (input.type === 'text') {
                input.value = '';
            } else {
                input.checked = false;
            }
        });
        
        const sortSelect = document.getElementById('sort-select');
        if (sortSelect) sortSelect.value = 'featured';
    }

    // Save current filter state to localStorage
    saveFilters() {
        const filterState = {
            activeFilters: this.activeFilters,
            currentSort: this.currentSort
        };
        localStorage.setItem('wreathFilters', JSON.stringify(filterState));
    }

    // Load saved filter state from localStorage
    loadSavedFilters() {
        try {
            const saved = localStorage.getItem('wreathFilters');
            if (saved) {
                const state = JSON.parse(saved);
                this.activeFilters = state.activeFilters || this.activeFilters;
                this.currentSort = state.currentSort || this.currentSort;
            }
        } catch (error) {
            console.warn('Failed to load saved filters:', error);
        }
    }

    // Notify callbacks that items have been updated
    notifyItemsUpdated() {
        if (this.callbacks.onItemsUpdated) {
            this.callbacks.onItemsUpdated(this.filteredItems);
        }
    }

    // Get filter statistics (for UI display)
    getFilterStats() {
        return {
            totalItems: this.items.length,
            filteredItems: this.filteredItems.length,
            activeFilterCount: Object.values(this.activeFilters.categories)
                .reduce((total, filters) => total + filters.length, 0) +
                (this.activeFilters.showAvailableOnly ? 1 : 0) +
                (this.activeFilters.searchText ? 1 : 0)
        };
    }
}

// Export for use in other files
window.FilteringSystem = FilteringSystem;