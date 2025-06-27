class PoshmarkPopup {
  constructor() {
    this.currentData = null;
    this.init();
  }

  async init() {
    console.log('Popup initializing...');
    
    // Check if we're on a Poshmark page
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    console.log('Current tab URL:', tab.url);
    
    if (!tab.url.includes('poshmark.com/listing/')) {
      document.getElementById('not-poshmark').classList.remove('hidden');
      document.getElementById('main-interface').classList.add('hidden');
      return;
    }

    // Set up event listeners
    this.setupEventListeners();
    
    // Load any previously extracted data
    await this.loadPreviousData();
  }

  setupEventListeners() {
    document.getElementById('extractBtn').addEventListener('click', () => this.extractData());
    document.getElementById('exportJSON').addEventListener('click', () => this.exportJSON());
    document.getElementById('exportCSV').addEventListener('click', () => this.exportCSV());
    document.getElementById('exportEbay').addEventListener('click', () => this.exportEbayTemplate());
    document.getElementById('exportText').addEventListener('click', () => this.exportText());
  }

  async loadPreviousData() {
    try {
      const result = await chrome.storage.local.get(['lastExtractedData']);
      if (result.lastExtractedData) {
        this.currentData = result.lastExtractedData;
        this.displayData(this.currentData);
      }
    } catch (error) {
      console.error('Error loading previous data:', error);
    }
  }

  async extractData() {
    const extractBtn = document.getElementById('extractBtn');
    const originalText = extractBtn.textContent;
    
    try {
      // Show loading state
      extractBtn.innerHTML = '<span class="loading"></span>Extracting...';
      extractBtn.disabled = true;

      // Get active tab
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      console.log('Sending message to tab:', tab.id);
      
      // Send message to content script with timeout
      const response = await new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
          reject(new Error('Timeout: Content script did not respond'));
        }, 10000); // 10 second timeout

        chrome.tabs.sendMessage(tab.id, { action: 'extractData' }, (response) => {
          clearTimeout(timeout);
          
          if (chrome.runtime.lastError) {
            reject(new Error(chrome.runtime.lastError.message));
            return;
          }
          
          resolve(response);
        });
      });
      
      console.log('Received response:', response);
      
      if (response && response.success && response.data) {
        this.currentData = response.data;
        await chrome.storage.local.set({ lastExtractedData: response.data });
        this.displayData(response.data);
        this.showMessage('Data extracted successfully!', 'success');
      } else {
        throw new Error(response?.error || 'Failed to extract data - no response received');
      }
    } catch (error) {
      console.error('Extraction error:', error);
      
      let errorMessage = error.message;
      if (errorMessage.includes('Could not establish connection')) {
        errorMessage = 'Content script not loaded. Please refresh the page and try again.';
      } else if (errorMessage.includes('Timeout')) {
        errorMessage = 'Extraction timed out. Please refresh the page and try again.';
      }
      
      this.showMessage(`Error: ${errorMessage}`, 'error');
    } finally {
      // Reset button
      extractBtn.textContent = originalText;
      extractBtn.disabled = false;
    }
  }

  displayData(data) {
    const preview = document.getElementById('dataPreview');
    const content = document.getElementById('dataContent');
    const exportSection = document.getElementById('exportSection');
    
    // Clear previous content
    content.innerHTML = '';
    
    // Display key data points
    const displayFields = [
      { key: 'title', label: 'Title' },
      { key: 'price', label: 'Price' },
      { key: 'brand', label: 'Brand' },
      { key: 'size', label: 'Size' },
      { key: 'condition', label: 'Condition' },
      { key: 'category', label: 'Category' }
    ];

    displayFields.forEach(field => {
      if (data[field.key]) {
        const item = document.createElement('div');
        item.className = 'data-item';
        item.innerHTML = `
          <span class="data-label">${field.label}:</span>
          <span class="data-value">${data[field.key]}</span>
        `;
        content.appendChild(item);
      }
    });

    // Show images count
    if (data.images && data.images.length > 0) {
      const item = document.createElement('div');
      item.className = 'data-item';
      item.innerHTML = `
        <span class="data-label">Images:</span>
        <span class="data-value">${data.images.length} images</span>
      `;
      content.appendChild(item);
    }

    // Show extraction info
    const infoItem = document.createElement('div');
    infoItem.className = 'data-item';
    infoItem.innerHTML = `
      <span class="data-label">Extracted:</span>
      <span class="data-value">${new Date(data.timestamp).toLocaleString()}</span>
    `;
    content.appendChild(infoItem);

    preview.classList.remove('hidden');
    exportSection.classList.remove('hidden');
  }

  exportJSON() {
    if (!this.currentData) return;
    
    const blob = new Blob([JSON.stringify(this.currentData, null, 2)], { type: 'application/json' });
    this.downloadFile(blob, `poshmark-listing-${Date.now()}.json`);
    this.showMessage('JSON file downloaded!', 'success');
  }

  exportCSV() {
    if (!this.currentData) return;
    
    const csvHeaders = [
      'Title', 'Price', 'Original Price', 'Brand', 'Size', 'Category', 
      'Condition', 'Description', 'Seller', 'Images Count', 'URL', 'Extracted Date'
    ];
    
    const csvRow = [
      this.escapeCSV(this.currentData.title || ''),
      this.currentData.price || '',
      this.currentData.originalPrice || '',
      this.escapeCSV(this.currentData.brand || ''),
      this.escapeCSV(this.currentData.size || ''),
      this.escapeCSV(this.currentData.category || ''),
      this.escapeCSV(this.currentData.condition || ''),
      this.escapeCSV(this.currentData.description || ''),
      this.escapeCSV(this.currentData.seller?.name || ''),
      this.currentData.images?.length || 0,
      this.currentData.url || '',
      this.currentData.timestamp || ''
    ];
    
    const csv = [csvHeaders.join(','), csvRow.join(',')].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    this.downloadFile(blob, `poshmark-listing-${Date.now()}.csv`);
    this.showMessage('CSV file downloaded!', 'success');
  }

  exportEbayTemplate() {
    if (!this.currentData) return;
    
    const template = this.generateEbayTemplate(this.currentData);
    const blob = new Blob([template], { type: 'text/plain' });
    this.downloadFile(blob, `ebay-template-${Date.now()}.txt`);
    this.showMessage('eBay template downloaded!', 'success');
  }

  exportText() {
    if (!this.currentData) return;
    
    const text = this.generateTextFormat(this.currentData);
    const blob = new Blob([text], { type: 'text/plain' });
    this.downloadFile(blob, `poshmark-listing-${Date.now()}.txt`);
    this.showMessage('Text file downloaded!', 'success');
  }

  generateEbayTemplate(data) {
    const suggestedPrice = data.price ? (parseFloat(data.price) * 1.2).toFixed(2) : 'N/A';
    
    return `EBAY LISTING TEMPLATE
Generated from Poshmark listing

TITLE: ${data.title || 'N/A'}

STARTING PRICE: $${data.price || '0.00'}
BUY IT NOW PRICE: $${suggestedPrice}

CATEGORY: ${this.mapCategoryToEbay(data.category)}

ITEM SPECIFICS:
- Brand: ${data.brand || 'Unbranded'}
- Size: ${data.size || 'N/A'}
- Condition: ${this.mapConditionToEbay(data.condition)}

DESCRIPTION:
${data.description || 'No description available'}

ADDITIONAL NOTES:
- Originally listed on Poshmark
- ${data.images?.length || 0} photos available
- Seller rating: ${data.seller?.rating || 'N/A'}

IMAGES TO UPLOAD: ${data.images?.length || 0}
${data.images?.map((img, index) => `Image ${index + 1}: ${img}`).join('\n') || 'No images found'}

Source URL: ${data.url}
Extracted: ${data.timestamp}`;
  }

  generateTextFormat(data) {
    return `POSHMARK LISTING DATA
=====================

Title: ${data.title || 'N/A'}
Price: $${data.price || 'N/A'}
Original Price: $${data.originalPrice || 'N/A'}
Brand: ${data.brand || 'N/A'}
Size: ${data.size || 'N/A'}
Category: ${data.category || 'N/A'}
Condition: ${data.condition || 'N/A'}

Description:
${data.description || 'No description available'}

Seller Information:
- Name: ${data.seller?.name || 'N/A'}
- Rating: ${data.seller?.rating || 'N/A'}

Statistics:
- Likes: ${data.stats?.likes || 'N/A'}
- Comments: ${data.stats?.comments || 'N/A'}

Images (${data.images?.length || 0}):
${data.images?.map((img, index) => `${index + 1}. ${img}`).join('\n') || 'No images found'}

Tags:
${data.tags?.join(', ') || 'No tags found'}

Source: ${data.url}
Extracted: ${data.timestamp}`;
  }

  mapCategoryToEbay(poshmarkCategory) {
    const categoryMap = {
      'Women': 'Women\'s Clothing',
      'Men': 'Men\'s Clothing',
      'Kids': 'Kids\' Clothing',
      'Shoes': 'Shoes',
      'Bags': 'Handbags & Purses',
      'Accessories': 'Fashion Accessories'
    };
    
    return categoryMap[poshmarkCategory] || 'Clothing, Shoes & Accessories';
  }

  mapConditionToEbay(poshmarkCondition) {
    const conditionMap = {
      'New with tags': 'New with tags',
      'New without tags': 'New without tags',
      'Like new': 'New without tags',
      'Good': 'Pre-owned',
      'Fair': 'Pre-owned',
      'Poor': 'For parts or not working'
    };
    
    return conditionMap[poshmarkCondition] || 'Pre-owned';
  }

  escapeCSV(text) {
    if (!text) return '';
    text = text.toString();
    if (text.includes(',') || text.includes('"') || text.includes('\n')) {
      return `"${text.replace(/"/g, '""')}"`;
    }
    return text;
  }

  downloadFile(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  showMessage(text, type) {
    const messages = document.getElementById('messages');
    const message = document.createElement('div');
    message.className = type;
    message.textContent = text;
    messages.appendChild(message);
    
    setTimeout(() => {
      if (message.parentNode) {
        message.parentNode.removeChild(message);
      }
    }, 3000);
  }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  new PoshmarkPopup();
});