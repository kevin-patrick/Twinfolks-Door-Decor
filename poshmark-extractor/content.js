// Poshmark Listing Extractor - Content Script (Fixed)
console.log('Poshmark content script loaded');

// Check if we're on a valid Poshmark listing page
function isValidPoshmarkPage() {
  return window.location.href.includes('poshmark.com/listing/');
}

// Main extraction function
function extractListingData() {
  console.log('Starting data extraction...');
  
  if (!isValidPoshmarkPage()) {
    throw new Error('Not a valid Poshmark listing page');
  }
  
  try {
    const data = {
      timestamp: new Date().toISOString(),
      url: window.location.href,
      title: extractTitle(),
      price: extractPrice(),
      originalPrice: extractOriginalPrice(),
      brand: extractBrand(),
      size: extractSize(),
      category: extractCategory(),
      condition: extractCondition(),
      description: extractDescription(),
      images: extractImages(),
      seller: extractSellerInfo(),
      stats: extractStats(),
      tags: extractTags()
    };

    console.log('Extracted data:', data);
    return data;
  } catch (error) {
    console.error('Error during extraction:', error);
    throw error;
  }
}

// Extract title
function extractTitle() {
  const selectors = [
    'h1[data-testid*="title"]',
    'h1[class*="title"]',
    '[data-testid="listing-title"]',
    '.listing-title',
    '.product-title',
    'h1',
    '.item-title'
  ];
  
  return getTextBySelectors(selectors) || 'Unknown Title';
}

// Extract price
function extractPrice() {
  const selectors = [
    '[data-testid*="price"]',
    '.price',
    '.listing-price',
    '.current-price',
    '[class*="price"]:not([class*="original"])',
    '.item-price'
  ];
  
  let price = getTextBySelectors(selectors);
  if (price) {
    // Clean up price - remove dollar sign and spaces
    price = price.replace(/[$,\s]/g, '').trim();
    // Extract just the number
    const priceMatch = price.match(/(\d+(?:\.\d{2})?)/);
    return priceMatch ? priceMatch[1] : null;
  }
  return null;
}

// Extract original price
function extractOriginalPrice() {
  const selectors = [
    '.original-price',
    '.was-price',
    '.crossed-out',
    '[class*="original"]',
    'del',
    's'
  ];
  
  let price = getTextBySelectors(selectors);
  if (price) {
    price = price.replace(/[$,\s]/g, '').trim();
    const priceMatch = price.match(/(\d+(?:\.\d{2})?)/);
    return priceMatch ? priceMatch[1] : null;
  }
  return null;
}

// Extract brand
function extractBrand() {
  const selectors = [
    '[data-testid*="brand"]',
    '.brand',
    '.brand-name',
    '.listing-brand',
    '[class*="brand"]'
  ];
  
  return getTextBySelectors(selectors) || 'Unknown Brand';
}

// Extract size
function extractSize() {
  const selectors = [
    '[data-testid*="size"]',
    '.size-info',
    '.listing-size',
    '.size',
    '[class*="size"]'
  ];
  
  let size = getTextBySelectors(selectors);
  if (size) {
    // Clean up size text - remove "Size" label and extra whitespace
    size = size.replace(/^Size\s*/i, '').replace(/\s+/g, ' ').trim();
    if (size === 'OS' || size.includes('OS')) {
      return 'OS';
    }
  }
  return size || 'OS';
}

// Extract category
function extractCategory() {
  const selectors = [
    '[data-testid*="category"]',
    '.category-info',
    '.breadcrumb',
    '.category',
    'nav a',
    '[class*="category"]'
  ];
  
  let category = getTextBySelectors(selectors);
  if (category) {
    // Clean up category text
    category = category.replace(/\s+/g, ' ').trim();
    return category;
  }
  return 'Home';
}

// Extract condition
function extractCondition() {
  const selectors = [
    '[data-testid*="condition"]',
    '.condition',
    '.item-condition',
    '.listing-condition',
    '[class*="condition"]'
  ];
  
  return getTextBySelectors(selectors) || 'NWT';
}

// Extract description
function extractDescription() {
  const selectors = [
    '[data-testid*="description"]',
    '.description',
    '.listing-description',
    '.product-description',
    '[class*="description"]'
  ];
  
  return getTextBySelectors(selectors) || '';
}

// Extract images
function extractImages() {
  const images = [];
  
  // Try different selectors for images
  const imageSelectors = [
    'img[src*="cloudfront"]',
    'img[src*="poshmark"]',
    '.listing-images img',
    '.product-images img',
    '.gallery img',
    '[class*="image"] img',
    'img'
  ];
  
  imageSelectors.forEach(selector => {
    try {
      const imgs = document.querySelectorAll(selector);
      imgs.forEach(img => {
        if (img.src && img.src.includes('/posts/')) {
          // Only grab images that contain "/posts/" - these are the actual listing images
          let src = img.src;
          
          // Get high-res version by removing size parameters
          src = src.replace(/\/s_\d+x\d+/, '');
          
          // Ensure we get the full quality version
          if (src.includes('/m_') && !src.includes('/m_wp_')) {
            src = src.replace('/m_', '/m_wp_');
          }
          
          // Remove any duplicate entries
          if (!images.includes(src)) {
            images.push(src);
          }
        }
      });
    } catch (error) {
      console.log(`Image selector failed: ${selector}`, error);
    }
  });
  
  // Sort images to ensure consistent ordering
  images.sort();
  
  console.log(`Found ${images.length} listing images`);
  return images;
}

// Extract seller info
function extractSellerInfo() {
  const seller = {};
  
  // Try multiple approaches for seller name
  const nameSelectors = [
    '[data-testid*="seller"]',
    '.seller-name',
    '.username',
    'a[href*="/closet/"]'
  ];
  
  let sellerName = getTextBySelectors(nameSelectors);
  if (sellerName) {
    sellerName = sellerName.replace(/^@/, '').trim();
    seller.name = sellerName;
  } else {
    seller.name = null;
  }

  seller.rating = null; // Hard to extract reliably
  return seller;
}

// Extract stats (likes, comments)
function extractStats() {
  const stats = {};
  
  // Look for likes and comments - these are hard to extract reliably
  // so we'll set them to null for now
  stats.likes = null;
  
  // Try to get comments from the page
  let comments = getTextBySelectors(['.comments', '[class*="comment"]']);
  if (comments) {
    stats.comments = comments;
  } else {
    stats.comments = null;
  }

  return stats;
}

// Extract tags/hashtags
function extractTags() {
  const tags = [];
  
  // Look for existing tags in various places
  const tagSelectors = [
    '.tags',
    '.hashtags',
    '[class*="tag"]',
    '[class*="badge"]'
  ];
  
  tagSelectors.forEach(selector => {
    try {
      const elements = document.querySelectorAll(selector);
      elements.forEach(el => {
        const text = el.textContent.trim();
        if (text && text.length < 50 && !tags.includes(text)) {
          tags.push(text);
        }
      });
    } catch (error) {
      console.log(`Tag selector failed: ${selector}`, error);
    }
  });
  
  // Extract hashtags from description
  const description = extractDescription();
  if (description) {
    const hashtagMatches = description.match(/#[\w]+/g);
    if (hashtagMatches) {
      hashtagMatches.forEach(tag => {
        const cleanTag = tag.replace('#', '');
        if (!tags.includes(cleanTag)) {
          tags.push(cleanTag);
        }
      });
    }
  }
  
  // Add some default tags based on category/condition
  const category = extractCategory();
  const condition = extractCondition();
  
  if (condition && !tags.includes(condition)) {
    tags.push(condition);
  }
  
  return tags;
}

// Helper function to get text by trying multiple selectors
function getTextBySelectors(selectors) {
  for (const selector of selectors) {
    try {
      const element = document.querySelector(selector);
      if (element && element.textContent && element.textContent.trim()) {
        let text = element.textContent.trim();
        // Clean up excessive whitespace and newlines
        text = text.replace(/\s+/g, ' ').trim();
        return text;
      }
    } catch (error) {
      // Silently continue to next selector
    }
  }
  return null;
}

// Safe download function that doesn't rely on extension APIs
function downloadJSONFile(data) {
  try {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `poshmark-listing-${Date.now()}.json`;
    a.style.display = 'none';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    return true;
  } catch (error) {
    console.error('Download failed:', error);
    return false;
  }
}

// Create floating extract button
function createFloatingButton() {
  // Only create button on valid Poshmark pages
  if (!isValidPoshmarkPage()) {
    return;
  }

  // Remove existing button if it exists
  const existingBtn = document.getElementById('poshmark-extractor-btn');
  if (existingBtn) {
    existingBtn.remove();
  }

  const button = document.createElement('button');
  button.id = 'poshmark-extractor-btn';
  button.innerHTML = `
    <svg viewBox="0 0 24 24" fill="currentColor">
      <path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/>
    </svg>
    Extract
  `;
  
  button.addEventListener('click', async () => {
    try {
      button.classList.add('loading');
      button.innerHTML = `
        <svg viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 6v3l4-4-4-4v3c-4.42 0-8 3.58-8 8 0 1.57.46 3.03 1.24 4.26L6.7 14.8c-.45-.83-.7-1.79-.7-2.8 0-3.31 2.69-6 6-6z"/>
        </svg>
        Extracting...
      `;
      
      const data = extractListingData();
      const success = downloadJSONFile(data);
      
      if (success) {
        showSuccessMessage();
      } else {
        throw new Error('Download failed');
      }
      
    } catch (error) {
      console.error('Extraction failed:', error);
      showErrorMessage(error.message);
    } finally {
      // Reset button after delay
      setTimeout(() => {
        if (button && button.parentNode) {
          button.classList.remove('loading');
          button.innerHTML = `
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/>
            </svg>
            Extract
          `;
        }
      }, 1000);
    }
  });
  
  document.body.appendChild(button);
}

// Show success message
function showSuccessMessage() {
  removeExistingMessages();
  
  const message = document.createElement('div');
  message.id = 'extraction-success';
  message.textContent = '✓ Data extracted and downloaded!';
  message.style.cssText = `
    position: fixed;
    top: 80px;
    right: 20px;
    z-index: 10001;
    background: #4caf50;
    color: white;
    padding: 12px 20px;
    border-radius: 8px;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    font-size: 14px;
    font-weight: 500;
    box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);
  `;
  
  document.body.appendChild(message);
  
  setTimeout(() => {
    if (message && message.parentNode) {
      message.parentNode.removeChild(message);
    }
  }, 3000);
}

// Show error message
function showErrorMessage(errorText) {
  removeExistingMessages();
  
  const message = document.createElement('div');
  message.id = 'extraction-error';
  message.textContent = '❌ Error: ' + errorText;
  message.style.cssText = `
    position: fixed;
    top: 80px;
    right: 20px;
    z-index: 10001;
    background: #f44336;
    color: white;
    padding: 12px 20px;
    border-radius: 8px;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    font-size: 14px;
    font-weight: 500;
    box-shadow: 0 4px 12px rgba(244, 67, 54, 0.3);
  `;
  
  document.body.appendChild(message);
  
  setTimeout(() => {
    if (message && message.parentNode) {
      message.parentNode.removeChild(message);
    }
  }, 5000);
}

// Remove existing messages
function removeExistingMessages() {
  const existingSuccess = document.getElementById('extraction-success');
  const existingError = document.getElementById('extraction-error');
  
  if (existingSuccess) existingSuccess.remove();
  if (existingError) existingError.remove();
}

// Listen for messages from popup (with better error handling)
try {
  if (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.onMessage) {
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
      console.log('Content script received message:', message);
      
      if (message.action === 'extractData') {
        try {
          const data = extractListingData();
          sendResponse({ success: true, data: data });
        } catch (error) {
          console.error('Extraction error:', error);
          sendResponse({ success: false, error: error.message });
        }
      }
      
      return true; // Keep message channel open for async response
    });
  }
} catch (error) {
  console.log('Extension context not available, popup communication disabled');
}

// Initialize when page loads
function initializeExtension() {
  if (isValidPoshmarkPage()) {
    createFloatingButton();
    console.log('Poshmark content script initialized');
  }
}

// Wait for page to be ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeExtension);
} else {
  initializeExtension();
}

// Re-initialize if the page changes (for SPAs)
let currentUrl = window.location.href;
setInterval(() => {
  if (window.location.href !== currentUrl) {
    currentUrl = window.location.href;
    setTimeout(initializeExtension, 1000); // Wait for page to settle
  }
}, 1000);