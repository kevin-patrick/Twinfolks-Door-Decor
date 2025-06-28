// poshmark-extractor/content.js - Complete enhanced extraction with better data handling

class PoshmarkExtractor {
  constructor() {
    this.isExtracting = false;
    this.setupExtractButton();
    this.setupMessageListener();
  }

  setupExtractButton() {
    // Only add button if we're on a listing page
    if (!window.location.href.includes('poshmark.com/listing/')) {
      return;
    }

    // Remove existing button if present
    const existingBtn = document.getElementById('poshmark-extractor-btn');
    if (existingBtn) {
      existingBtn.remove();
    }

    // Create floating extract button
    const extractBtn = document.createElement('button');
    extractBtn.id = 'poshmark-extractor-btn';
    extractBtn.innerHTML = `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
        <polyline points="7,10 12,15 17,10"/>
        <line x1="12" y1="15" x2="12" y2="3"/>
      </svg>
      Extract
    `;
    
    extractBtn.addEventListener('click', () => this.extractAndDownload());
    document.body.appendChild(extractBtn);
  }

  setupMessageListener() {
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
      if (message.action === 'extractData') {
        // Handle extraction request from popup
        this.handleExtractionRequest()
          .then(result => {
            sendResponse(result);
          })
          .catch(error => {
            console.error('Extraction error:', error);
            sendResponse({
              success: false,
              error: error.message || 'Unknown extraction error'
            });
          });
        
        // Return true to indicate we'll respond asynchronously
        return true;
      }
    });
  }

  async handleExtractionRequest() {
    if (this.isExtracting) {
      throw new Error('Extraction already in progress');
    }

    try {
      this.isExtracting = true;
      const data = await this.extractListingData();
      return {
        success: true,
        data: data
      };
    } finally {
      this.isExtracting = false;
    }
  }

  async extractAndDownload() {
    try {
      if (this.isExtracting) {
        return;
      }

      this.isExtracting = true;
      const btn = document.getElementById('poshmark-extractor-btn');
      
      if (btn) {
        btn.classList.add('loading');
        btn.innerHTML = `
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 12a9 9 0 11-6.219-8.56"/>
          </svg>
          Extracting...
        `;
      }

      const data = await this.extractListingData();
      this.downloadJSON(data);
      this.showSuccessMessage();

    } catch (error) {
      console.error('Extraction failed:', error);
      alert('Extraction failed: ' + error.message);
    } finally {
      this.isExtracting = false;
      this.resetButton();
    }
  }

  async extractListingData() {
    try {
      // Wait a moment for page to fully load
      await this.waitForPageLoad();

      const data = {
        timestamp: new Date().toISOString(),
        url: window.location.href,
        title: this.extractTitle(),
        price: this.extractPrice(),
        originalPrice: this.extractOriginalPrice(),
        brand: this.extractBrand(),
        size: this.extractSize(),
        category: this.extractCategory(),
        condition: this.extractCondition(),
        description: this.extractDescription(),
        images: this.extractImages(),
        seller: this.extractSellerInfo(),
        stats: this.extractStats(),
        tags: this.extractTags()
      };

      // Validate required fields
      if (!data.title && !data.price) {
        throw new Error('Could not find essential listing data. The page may not be fully loaded.');
      }

      return data;
    } catch (error) {
      console.error('Data extraction error:', error);
      throw new Error(`Failed to extract listing data: ${error.message}`);
    }
  }

  waitForPageLoad() {
    return new Promise((resolve) => {
      if (document.readyState === 'complete') {
        setTimeout(resolve, 1000); // Extra wait for dynamic content
      } else {
        window.addEventListener('load', () => {
          setTimeout(resolve, 1000);
        });
      }
    });
  }

  extractTitle() {
    const selectors = [
      '[data-testid="listing-title"]',
      '[data-test-id="listing-title"]',
      'h1[data-testid*="title"]',
      'h1[class*="title"]',
      '.listing-title',
      '.title',
      'h1',
      '[class*="title"]',
      '[class*="Title"]',
      '.item-title'
    ];
    
    return this.getTextBySelectors(selectors);
  }

  extractPrice() {
    const selectors = [
      '[data-testid="listing-price"]',
      '[data-test-id="listing-price"]',
      '.price',
      '.listing-price',
      '[class*="price"]',
      '[class*="Price"]',
      '.current-price',
      '.item-price'
    ];
    
    let price = this.getTextBySelectors(selectors);
    if (price) {
      // Extract numeric value from price string
      const priceMatch = price.match(/\$(\d+(?:,\d{3})*(?:\.\d{2})?)/);
      return priceMatch ? priceMatch[1].replace(/,/g, '') : price.replace(/\D/g, '');
    }
    return null;
  }

  extractOriginalPrice() {
    const selectors = [
      '[data-testid="original-price"]',
      '[data-test-id="original-price"]',
      '.original-price',
      '.was-price',
      '.strikethrough',
      '[class*="original"]',
      '[class*="was"]',
      '.crossed-out'
    ];
    
    let originalPrice = this.getTextBySelectors(selectors);
    if (originalPrice) {
      const priceMatch = originalPrice.match(/\$(\d+(?:,\d{3})*(?:\.\d{2})?)/);
      return priceMatch ? priceMatch[1].replace(/,/g, '') : null;
    }
    return null;
  }

  extractBrand() {
    const selectors = [
      '[data-testid="listing-brand"]',
      '[data-test-id="listing-brand"]',
      '.brand',
      '.listing-brand',
      '[class*="brand"]',
      '[class*="Brand"]',
      '.brand-name'
    ];
    
    return this.getTextBySelectors(selectors);
  }

  extractSize() {
    const selectors = [
      '[data-testid="listing-size"]',
      '[data-test-id="listing-size"]',
      '.size-info',
      '.listing-size',
      '.size',
      '[class*="size"]',
      '[class*="Size"]'
    ];
    
    let size = this.getTextBySelectors(selectors);
    if (size) {
      // Clean up size text
      size = size.replace(/^Size\s*/i, '').replace(/\s+/g, ' ').trim();
      if (size === 'OS' || size.includes('OS')) {
        return 'One Size';
      }
    }
    return size;
  }

  extractCategory() {
    const selectors = [
      '[data-testid="listing-category"]',
      '[data-test-id="listing-category"]',
      '.category-info',
      '.breadcrumb',
      '.category',
      'nav[aria-label*="breadcrumb"] a',
      '[class*="category"]',
      '[class*="breadcrumb"]'
    ];
    
    let category = this.getTextBySelectors(selectors);
    if (category) {
      // Clean up category text
      category = category.replace(/\s+/g, ' ').trim();
      category = category.replace(/\n\s+/g, ' > ');
      return category;
    }
    return null;
  }

  extractCondition() {
    const selectors = [
      '[data-testid="listing-condition"]',
      '[data-test-id="listing-condition"]',
      '.condition',
      '.listing-condition',
      '[class*="condition"]',
      '[class*="Condition"]'
    ];
    
    return this.getTextBySelectors(selectors);
  }

  extractDescription() {
    const selectors = [
      '[data-testid="listing-description"]',
      '[data-test-id="listing-description"]',
      '.description',
      '.listing-description',
      '.item-description',
      '[class*="description"]',
      '[class*="Description"]',
      '.product-description'
    ];
    
    return this.getTextBySelectors(selectors);
  }

  extractImages() {
    const images = [];
    const selectors = [
      '[data-testid="listing-image"] img',
      '[data-test-id="listing-image"] img',
      '.listing-image img',
      '.product-image img',
      '.item-image img',
      '[class*="image"] img',
      '[class*="Image"] img',
      '.carousel img',
      '.gallery img',
      '.photos img',
      '.slider img'
    ];
    
    // Try each selector set
    for (const selector of selectors) {
      try {
        const imgElements = document.querySelectorAll(selector);
        imgElements.forEach(img => {
          const src = img.src || img.getAttribute('data-src') || img.getAttribute('data-lazy-src');
          if (src && src.startsWith('http') && !images.includes(src)) {
            // Filter out tiny images (likely icons)
            if (img.naturalWidth > 100 && img.naturalHeight > 100) {
              images.push(src);
            }
          }
        });
        
        if (images.length > 0) break;
      } catch (error) {
        console.log(`Image selector failed: ${selector}`, error);
      }
    }
    
    return images;
  }

  extractSellerInfo() {
    const seller = {};
    
    // Seller name
    const nameSelectors = [
      '[data-testid="seller-name"]',
      '[data-test-id="seller-name"]',
      '[data-testid="seller-username"]',
      '.seller-name',
      '.username',
      '.seller-info .name',
      '[class*="seller"] [class*="name"]',
      'a[href*="/closet/"]'
    ];
    
    let sellerName = this.getTextBySelectors(nameSelectors);
    if (sellerName) {
      seller.name = sellerName.replace(/^@/, '').trim();
    }

    // Seller rating
    const ratingSelectors = [
      '.seller-rating',
      '.rating',
      '[data-testid="seller-rating"]',
      '[class*="rating"]',
      '.stars'
    ];
    
    let rating = this.getTextBySelectors(ratingSelectors);
    if (rating) {
      const ratingMatch = rating.match(/(\d+(?:\.\d+)?)/);
      seller.rating = ratingMatch ? ratingMatch[1] : rating.trim();
    }

    return seller;
  }

  extractStats() {
    const stats = {};
    
    // Likes
    const likeSelectors = [
      '[data-testid="like-count"]',
      '[data-testid*="like"]',
      '.like-count',
      '.likes',
      '[class*="like"]',
      '[aria-label*="like"]'
    ];
    
    let likes = this.getTextBySelectors(likeSelectors);
    if (likes) {
      const likeMatch = likes.match(/(\d+)/);
      stats.likes = likeMatch ? likeMatch[1] : null;
    }

    // Comments
    const commentSelectors = [
      '[data-testid="comment-count"]',
      '[data-testid*="comment"]',
      '.comment-count',
      '.comments',
      '[class*="comment"]'
    ];
    
    let comments = this.getTextBySelectors(commentSelectors);
    if (comments) {
      stats.comments = comments.replace(/\s+/g, ' ').trim();
    }

    return stats;
  }

  extractTags() {
    const tags = [];
    const selectors = [
      '[data-testid="tag"]',
      '[data-test-id="tag"]',
      '.tag',
      '.tags .tag',
      '.label',
      '.badge',
      '[class*="tag"]',
      '[class*="Tag"]',
      '[class*="label"]',
      '[class*="badge"]'
    ];
    
    for (const selector of selectors) {
      try {
        const tagElements = document.querySelectorAll(selector);
        tagElements.forEach(tag => {
          const text = tag.textContent?.trim();
          if (text && text.length > 0 && text.length < 50 && !tags.includes(text)) {
            tags.push(text);
          }
        });
      } catch (error) {
        console.log(`Tag selector failed: ${selector}`, error);
      }
    }
    
    return tags;
  }

  getTextBySelectors(selectors) {
    for (const selector of selectors) {
      try {
        const element = document.querySelector(selector);
        if (element && element.textContent && element.textContent.trim()) {
          return element.textContent.replace(/\s+/g, ' ').trim();
        }
      } catch (error) {
        console.log(`Selector failed: ${selector}`, error);
      }
    }
    return null;
  }

  downloadJSON(data) {
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

  showSuccessMessage() {
    const message = document.createElement('div');
    message.id = 'extraction-success';
    message.textContent = '✓ Listing data extracted and downloaded!';
    document.body.appendChild(message);
    
    setTimeout(() => {
      if (message.parentNode) {
        message.parentNode.removeChild(message);
      }
    }, 3000);
  }

  resetButton() {
    const btn = document.getElementById('poshmark-extractor-btn');
    if (btn) {
      btn.classList.remove('loading');
      btn.innerHTML = `
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
          <polyline points="7,10 12,15 17,10"/>
          <line x1="12" y1="15" x2="12" y2="3"/>
        </svg>
        Extract
      `;
    }
  }
}

// Initialize extractor when content script loads
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    new PoshmarkExtractor();
  });
} else {
  new PoshmarkExtractor();
}