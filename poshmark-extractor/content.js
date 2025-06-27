// Poshmark Listing Extractor - Content Script
console.log('Poshmark content script loaded');

// Main extraction function
function extractListingData() {
  console.log('Starting data extraction...');
  
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
    '[data-testid="listing-title"]',
    '[data-test-id="listing-title"]',
    'h1[data-testid*="title"]',
    'h1[class*="title"]',
    '.listing-title',
    '.product-title',
    'h1',
    '[class*="Title"]'
  ];
  
  return getTextBySelectors(selectors);
}

// Extract price
function extractPrice() {
  const selectors = [
    '[data-testid="listing-price"]',
    '[data-test-id="listing-price"]',
    '[data-testid*="price"]',
    '[data-test-id*="price"]',
    '.price',
    '.listing-price',
    '.current-price',
    '[class*="price"]',
    '[class*="Price"]'
  ];
  
  let price = getTextBySelectors(selectors);
  if (price) {
    // Clean up price - remove dollar sign and spaces
    price = price.replace(/[$,\s]/g, '').trim();
    // Extract just the number
    const priceMatch = price.match(/(\d+(?:\.\d{2})?)/);
    return priceMatch ? priceMatch[1] : price;
  }
  return null;
}

// Extract original price
function extractOriginalPrice() {
  const selectors = [
    '[data-testid="original-price"]',
    '[data-test-id="original-price"]',
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
    return priceMatch ? priceMatch[1] : price;
  }
  return null;
}

// Extract brand
function extractBrand() {
  const selectors = [
    '[data-testid="listing-brand"]',
    '[data-test-id="listing-brand"]',
    '[data-testid*="brand"]',
    '[data-test-id*="brand"]',
    '.brand',
    '.brand-name',
    '.listing-brand',
    '[class*="brand"]',
    '[class*="Brand"]'
  ];
  
  return getTextBySelectors(selectors);
}

// Extract size
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
  
  let size = getTextBySelectors(selectors);
  if (size) {
    // Clean up size text - remove "Size" label and extra whitespace
    size = size.replace(/^Size\s*/i, '').replace(/\s+/g, ' ').trim();
    if (size === 'OS' || size.includes('OS')) {
      return 'One Size';
    }
  }
  return size;
}

// Extract category
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
  
  let category = getTextBySelectors(selectors);
  if (category) {
    // Clean up category text and format as breadcrumb
    category = category.replace(/\s+/g, ' ').trim();
    category = category.replace(/\n\s+/g, ' > ');
    return category;
  }
  return null;
}

// Extract condition
function extractCondition() {
  const selectors = [
    '[data-testid="listing-condition"]',
    '[data-test-id="listing-condition"]',
    '[data-testid*="condition"]',
    '[data-test-id*="condition"]',
    '.condition',
    '.item-condition',
    '.listing-condition',
    '[class*="condition"]',
    '[class*="Condition"]'
  ];
  
  return getTextBySelectors(selectors);
}

// Extract description
function extractDescription() {
  const selectors = [
    '[data-testid="listing-description"]',
    '[data-test-id="listing-description"]',
    '[data-testid*="description"]',
    '[data-test-id*="description"]',
    '.description',
    '.listing-description',
    '.product-description',
    '[class*="description"]',
    '[class*="Description"]'
  ];
  
  return getTextBySelectors(selectors);
}

// Extract images
function extractImages() {
  const images = [];
  
  // Try different selectors for images
  const imageSelectors = [
    '[data-testid*="image"] img',
    '[data-test-id*="image"] img',
    '.listing-images img',
    '.product-images img',
    '.gallery img',
    '[class*="image"] img',
    '[class*="photo"] img',
    'img[src*="cloudfront"]',
    'img[src*="poshmark"]'
  ];
  
  imageSelectors.forEach(selector => {
    try {
      const imgs = document.querySelectorAll(selector);
      imgs.forEach(img => {
        if (img.src && img.src.includes('cloudfront')) {
          // Get high-res version by removing size parameters
          let src = img.src;
          // Remove size parameters to get full resolution
          src = src.replace(/\/s_\d+x\d+/, '');
          src = src.replace(/\/m_/, '/m_wp_');
          if (!images.includes(src)) {
            images.push(src);
          }
        }
      });
    } catch (error) {
      console.log(`Image selector failed: ${selector}`, error);
    }
  });
  
  return images;
}

// Extract seller info
function extractSellerInfo() {
  const seller = {};
  
  // Try multiple approaches for seller name
  const nameSelectors = [
    '[data-testid="seller-name"]',
    '[data-test-id="seller-name"]',
    '[data-testid="seller-username"]',
    '[data-test-id="seller-username"]', 
    '.seller-name',
    '.username',
    '.seller-info .name',
    '[class*="seller"] [class*="name"]',
    '[class*="user"] [class*="name"]',
    'a[href*="/closet/"]', // Poshmark closet links
    '.seller-card .name',
    '.profile-name'
  ];
  
  let sellerName = getTextBySelectors(nameSelectors);
  if (sellerName) {
    // Clean seller name
    sellerName = sellerName.replace(/^@/, '').trim();
    seller.name = sellerName;
  }

  // Try to find seller rating
  const ratingSelectors = [
    '.seller-rating',
    '.rating',
    '[data-testid="seller-rating"]',
    '[data-test-id="seller-rating"]',
    '[class*="rating"]',
    '.stars',
    '[class*="star"]'
  ];
  
  let rating = getTextBySelectors(ratingSelectors);
  if (rating) {
    // Extract numeric rating
    const ratingMatch = rating.match(/(\d+(?:\.\d+)?)/);
    seller.rating = ratingMatch ? ratingMatch[1] : rating.trim();
  }

  return seller;
}

// Extract stats (likes, comments)
function extractStats() {
  const stats = {};
  
  // Better selectors for likes
  const likeSelectors = [
    '[data-testid="like-count"]',
    '[data-test-id="like-count"]',
    '[data-testid*="like"]',
    '[data-test-id*="like"]',
    '.like-count',
    '.likes',
    '[class*="like"]',
    'button[class*="like"] + span',
    'svg[class*="heart"] + span',
    '[aria-label*="like"]'
  ];
  
  let likes = getTextBySelectors(likeSelectors);
  if (likes) {
    // Extract just the number
    const likeMatch = likes.match(/(\d+)/);
    stats.likes = likeMatch ? likeMatch[1] : likes.trim();
  }

  // Better selectors for comments
  const commentSelectors = [
    '[data-testid="comment-count"]',
    '[data-test-id="comment-count"]',
    '[data-testid*="comment"]',
    '[data-test-id*="comment"]',
    '.comment-count',
    '.comments',
    '[class*="comment"]',
    'button[class*="comment"] + span',
    '[aria-label*="comment"]'
  ];
  
  let comments = getTextBySelectors(commentSelectors);
  if (comments) {
    // Clean up comment text and extract number
    comments = comments.replace(/\s+/g, ' ').trim();
    const commentMatch = comments.match(/(\d+)/);
    stats.comments = commentMatch ? commentMatch[1] : comments;
  }

  return stats;
}

// Extract tags/hashtags
function extractTags() {
  const tags = [];
  
  // Look for tags in different places
  const tagSelectors = [
    '[data-testid*="tag"]',
    '[data-test-id*="tag"]',
    '.tags',
    '.hashtags',
    '.listing-tags',
    '[class*="tag"]',
    '[class*="badge"]'
  ];
  
  tagSelectors.forEach(selector => {
    try {
      const elements = document.querySelectorAll(selector);
      elements.forEach(el => {
        const text = el.textContent.trim();
        if (text && !tags.includes(text)) {
          tags.push(text);
        }
      });
    } catch (error) {
      console.log(`Tag selector failed: ${selector}`, error);
    }
  });
  
  // Also extract tags from description hashtags
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
      console.log(`Selector failed: ${selector}`, error);
    }
  }
  return null;
}

// Create floating extract button
function createFloatingButton() {
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
          <path d="M12 2v2c5.52 0 10 4.48 10 10s-4.48 10-10 10S2 19.52 2 14h2c0 4.42 3.58 8 8 8s8-3.58 8-8-3.58-8-8-8z"/>
        </svg>
        Extracting...
      `;
      
      const data = extractListingData();
      
      // Download JSON file
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `poshmark-listing-${Date.now()}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      // Show success message
      showSuccessMessage();
      
    } catch (error) {
      console.error('Extraction failed:', error);
      alert('Extraction failed: ' + error.message);
    } finally {
      button.classList.remove('loading');
      button.innerHTML = `
        <svg viewBox="0 0 24 24" fill="currentColor">
          <path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/>
        </svg>
        Extract
      `;
    }
  });
  
  document.body.appendChild(button);
}

// Show success message
function showSuccessMessage() {
  const existingMsg = document.getElementById('extraction-success');
  if (existingMsg) {
    existingMsg.remove();
  }

  const message = document.createElement('div');
  message.id = 'extraction-success';
  message.textContent = '✓ Data extracted and downloaded!';
  document.body.appendChild(message);
  
  setTimeout(() => {
    if (message.parentNode) {
      message.parentNode.removeChild(message);
    }
  }, 3000);
}

// Listen for messages from popup
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

// Initialize when page loads
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', createFloatingButton);
} else {
  createFloatingButton();
}

console.log('Poshmark content script initialized');