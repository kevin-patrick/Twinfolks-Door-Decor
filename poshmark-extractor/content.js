// Improved content script with better text cleaning
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
    stats.comments = commentMatch ? commentMatch[1] : null;
  }

  return stats;
}

// Improved helper function with better text cleaning
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