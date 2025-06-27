// Robust content script for extracting Poshmark listing data
console.log('Poshmark content script loaded');

// Make sure we're on a Poshmark listing page
if (window.location.href.includes('poshmark.com/listing/')) {
  console.log('On Poshmark listing page, initializing extractor');
  initializeExtractor();
} else {
  console.log('Not on a Poshmark listing page');
}

function initializeExtractor() {
  // Add extraction button to the page
  addExtractButton();
  
  // Listen for messages from popup
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    console.log('Content script received message:', message);
    
    if (message.action === 'extractData') {
      try {
        const extractedData = extractListingData();
        console.log('Extraction successful:', extractedData);
        sendResponse({ success: true, data: extractedData });
      } catch (error) {
        console.error('Extraction error:', error);
        sendResponse({ success: false, error: error.message });
      }
    }
    
    return true; // Keep message channel open
  });
}

function addExtractButton() {
  // Don't add if button already exists
  if (document.getElementById('poshmark-extractor-btn')) {
    return;
  }

  const button = document.createElement('div');
  button.id = 'poshmark-extractor-btn';
  button.innerHTML = `
    <svg width="24" height="24" viewBox="0 0 24 24" fill="white">
      <path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/>
    </svg>
    <span>Extract</span>
  `;
  button.addEventListener('click', handleExtract);
  document.body.appendChild(button);
  console.log('Extract button added to page');
}

function extractListingData() {
  console.log('Starting data extraction...');
  
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
}

function extractTitle() {
  const selectors = [
    '[data-testid="listing-title"]',
    'h1[data-test-id="listing-title"]',
    'h1.listing-title',
    'h1.title',
    '.listing-header h1',
    'h1',
    '.listing-title',
    '[class*="title"]'
  ];
  
  return getTextBySelectors(selectors);
}

function extractPrice() {
  const selectors = [
    // Modern Poshmark price selectors
    '[data-testid*="price"]',
    '[data-test-id*="price"]',
    '[class*="price"]',
    '[class*="Price"]',
    
    // Text-based price finding
    'span:contains("$")',
    'div:contains("$")',
    'p:contains("$")',
    
    // General selectors
    '.price-section .price',
    '.listing-price',
    '.price'
  ];
  
  // First try the selectors
  let priceText = getTextBySelectors(selectors);
  
  // If that doesn't work, search all text for price patterns
  if (!priceText) {
    const allText = document.body.innerText;
    const priceMatches = allText.match(/\$\s*(\d+(?:\.\d{2})?)/g);
    if (priceMatches && priceMatches.length > 0) {
      // Take the first reasonable price (usually the listing price)
      priceText = priceMatches[0];
    }
  }
  
  if (priceText) {
    const matches = priceText.match(/\$?\s*(\d+(?:\.\d{2})?)/);
    const cleanPrice = matches ? matches[1] : priceText.replace(/[^\d.]/g, '');
    console.log('Extracted price:', cleanPrice, 'from text:', priceText);
    return cleanPrice;
  }
  
  console.log('No price found');
  return null;
}

function extractOriginalPrice() {
  const selectors = [
    '.original-price',
    '.retail-price',
    '[data-testid="original-price"]',
    '[data-test-id="original-price"]',
    '[class*="original"]',
    '[class*="retail"]'
  ];
  
  const priceText = getTextBySelectors(selectors);
  if (priceText) {
    const matches = priceText.match(/\$?(\d+(?:\.\d{2})?)/);
    return matches ? matches[1] : priceText.replace(/[^\d.]/g, '');
  }
  return null;
}

function extractBrand() {
  const selectors = [
    '[data-testid="listing-brand"]',
    '[data-test-id="listing-brand"]',
    '.brand-name',
    '.listing-brand',
    '.brand',
    '[class*="brand"]',
    '[class*="Brand"]'
  ];
  
  return getTextBySelectors(selectors);
}

function extractSize() {
  const selectors = [
    '[data-testid="listing-size"]',
    '[data-test-id="listing-size"]',
    '.size-info',
    '.listing-size',
    '.size',
    '[class*="size"]',
    '[class*="Size"]'
  ];
  
  return getTextBySelectors(selectors);
}

function extractCategory() {
  const selectors = [
    '[data-testid="listing-category"]',
    '[data-test-id="listing-category"]',
    '.category-info',
    '.breadcrumb',
    '.category',
    'nav a',
    '[class*="category"]',
    '[class*="breadcrumb"]'
  ];
  
  return getTextBySelectors(selectors);
}

function extractCondition() {
  const selectors = [
    '[data-testid="listing-condition"]',
    '[data-test-id="listing-condition"]',
    '.condition-info',
    '.listing-condition',
    '.condition',
    '[class*="condition"]',
    '[class*="Condition"]'
  ];
  
  return getTextBySelectors(selectors);
}

function extractDescription() {
  const selectors = [
    // Modern Poshmark description selectors
    '[data-testid*="description"]',
    '[data-test-id*="description"]',
    '[class*="description"]',
    '[class*="Description"]',
    
    // Generic description areas
    '.listing-details p',
    '.item-description',
    '.listing-description',
    '.description-content',
    '.description',
    
    // Look for longer text blocks that might be descriptions
    'div p',
    'section p'
  ];
  
  let description = getTextBySelectors(selectors);
  
  // If no description found, look for the longest text block
  if (!description) {
    const allParagraphs = document.querySelectorAll('p, div');
    let longestText = '';
    
    allParagraphs.forEach(p => {
      const text = p.textContent.trim();
      if (text.length > longestText.length && text.length > 50) {
        // Skip if it looks like navigation or UI text
        if (!text.includes('Share') && 
            !text.includes('Like') && 
            !text.includes('Comment') &&
            !text.includes('Follow') &&
            text.split(' ').length > 5) {
          longestText = text;
        }
      }
    });
    
    if (longestText) {
      description = longestText;
    }
  }
  
  console.log('Extracted description:', description ? description.substring(0, 100) + '...' : 'None found');
  return description;
}

function extractImages() {
  const images = [];
  const listingId = extractListingIdFromUrl();
  
  console.log('Extracting images for listing:', listingId);
  
  // Find all images on the page
  const allImages = document.querySelectorAll('img');
  
  allImages.forEach(img => {
    const sources = [
      img.src,
      img.dataset.src,
      img.getAttribute('data-src'),
      img.getAttribute('data-original')
    ].filter(Boolean);

    sources.forEach(src => {
      if (src && isListingImage(src, listingId)) {
        // Convert to high-quality WebP format
        const webpUrl = convertToWebpFormat(src);
        if (webpUrl && !images.includes(webpUrl)) {
          images.push(webpUrl);
        }
      }
    });
  });

  // Sort images to maintain order
  images.sort();
  
  console.log(`Found ${images.length} listing images:`, images);
  return images;
}

function extractListingIdFromUrl() {
  // Extract listing ID from current URL
  const url = window.location.href;
  const match = url.match(/listing\/[^\/]+-([a-f0-9]+)/);
  return match ? match[1] : null;
}

function isListingImage(src, listingId) {
  if (!src || !listingId) return false;
  
  // Check if this matches the Poshmark listing image pattern:
  // /posts/{year}/{month}/{day}/{listing-id}/...
  const listingImagePattern = new RegExp(`/posts/\\d{4}/\\d{2}/\\d{2}/${listingId}/`);
  
  return listingImagePattern.test(src) && 
         (src.includes('/m_') || src.includes('/s_')) &&
         !src.includes('logo') &&
         !src.includes('icon') &&
         !src.includes('button') &&
         !src.includes('badge');
}

function convertToWebpFormat(src) {
  if (!src) return null;
  
  // Convert small (s_) and medium (m_) images to high-quality WebP format
  if (src.includes('/s_')) {
    return src.replace('/s_', '/m_wp_').replace(/\.(jpg|jpeg|png)$/, '.webp');
  } else if (src.includes('/m_') && !src.includes('/m_wp_')) {
    return src.replace('/m_', '/m_wp_').replace(/\.(jpg|jpeg|png)$/, '.webp');
  } else if (src.includes('/m_wp_')) {
    // Already in the right format
    return src;
  }
  
  return src;
}

function extractSellerInfo() {
  const seller = {};
  
  const nameSelectors = [
    '[data-testid="seller-name"]',
    '[data-test-id="seller-name"]',
    '.seller-name',
    '.username',
    '[class*="seller"]',
    '[class*="user"]'
  ];
  seller.name = getTextBySelectors(nameSelectors);

  const ratingSelectors = [
    '.seller-rating',
    '.rating',
    '[data-testid="seller-rating"]',
    '[data-test-id="seller-rating"]',
    '[class*="rating"]'
  ];
  seller.rating = getTextBySelectors(ratingSelectors);

  return seller;
}

function extractStats() {
  const stats = {};
  
  const likeSelectors = [
    '[data-testid="like-count"]',
    '[data-test-id="like-count"]',
    '.like-count',
    '.likes',
    '[class*="like"]'
  ];
  stats.likes = getTextBySelectors(likeSelectors);

  const commentSelectors = [
    '.comment-count',
    '.comments',
    '[data-testid="comment-count"]',
    '[data-test-id="comment-count"]',
    '[class*="comment"]'
  ];
  stats.comments = getTextBySelectors(commentSelectors);

  return stats;
}

function extractTags() {
  const tags = [];
  const selectors = [
    '.tags .tag',
    '.hashtags .hashtag',
    '[data-testid="listing-tags"] span',
    '[data-test-id="listing-tags"] span',
    '[class*="tag"]',
    '[class*="hashtag"]'
  ];

  selectors.forEach(selector => {
    const elements = document.querySelectorAll(selector);
    elements.forEach(tag => {
      const text = tag.textContent.trim();
      if (text && !tags.includes(text)) {
        tags.push(text);
      }
    });
  });

  return tags;
}

function getTextBySelectors(selectors) {
  for (const selector of selectors) {
    try {
      const element = document.querySelector(selector);
      if (element && element.textContent && element.textContent.trim()) {
        return element.textContent.trim();
      }
    } catch (error) {
      console.log(`Selector failed: ${selector}`, error);
    }
  }
  return null;
}

async function handleExtract() {
  console.log('Handle extract clicked');
  
  try {
    const data = extractListingData();
    
    // Store data temporarily
    await chrome.storage.local.set({ lastExtractedData: data });
    
    // Show success message
    showSuccessMessage();
    
    // Download as JSON
    downloadAsJSON(data);
  } catch (error) {
    console.error('Extract error:', error);
    showErrorMessage('Extraction failed: ' + error.message);
  }
}

function showSuccessMessage() {
  const message = document.createElement('div');
  message.id = 'extraction-success';
  message.textContent = 'Listing data extracted successfully!';
  document.body.appendChild(message);
  
  setTimeout(() => {
    const element = document.getElementById('extraction-success');
    if (element) element.remove();
  }, 3000);
}

function showErrorMessage(text) {
  const message = document.createElement('div');
  message.id = 'extraction-error';
  message.textContent = text;
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
    const element = document.getElementById('extraction-error');
    if (element) element.remove();
  }, 5000);
}

function downloadAsJSON(data) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `poshmark-listing-${Date.now()}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}