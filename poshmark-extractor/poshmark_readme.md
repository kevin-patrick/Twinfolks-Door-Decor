# Poshmark Listing Extractor Chrome Extension

A Chrome extension that extracts listing data from Poshmark pages for cross-platform selling. Perfect for sellers who want to list their items on multiple platforms without manually re-entering all the information.

## Features

- 🔍 **Automatic Data Extraction**: Extracts title, price, brand, size, condition, description, images, and more
- 💾 **Multiple Export Formats**: JSON, CSV, eBay template, and plain text
- 🎯 **Smart eBay Integration**: Automatically maps Poshmark categories and conditions to eBay equivalents
- 📱 **User-Friendly Interface**: Simple popup interface with data preview
- ⚡ **One-Click Operation**: Extract button appears on Poshmark listing pages
- 🔄 **Persistent Storage**: Remembers last extracted data

## Installation

1. **Download the Extension Files**
   - Save all the provided files in a folder called `poshmark-extractor`
   - You'll need: `manifest.json`, `content.js`, `content.css`, `popup.html`, `popup.js`, `background.js`

2. **Load into Chrome**
   - Open Chrome and go to `chrome://extensions/`
   - Enable "Developer mode" (toggle in top-right)
   - Click "Load unpacked"
   - Select the `poshmark-extractor` folder

3. **Add Extension Icons** (Optional)
   - Create an `icons` folder in your extension directory
   - Add icon files: `icon16.png`, `icon48.png`, `icon128.png`
   - Or remove the icons section from manifest.json

## Usage

### Method 1: Floating Extract Button
1. Navigate to any Poshmark listing page
2. Look for the purple "Extract" button in the top-right corner
3. Click the button to extract and download data as JSON

### Method 2: Extension Popup
1. Navigate to any Poshmark listing page
2. Click the extension icon in Chrome's toolbar
3. Click "Extract Listing Data" in the popup
4. Preview the extracted data
5. Choose your export format:
   - **JSON**: Raw data for developers
   - **CSV**: Spreadsheet-compatible format
   - **eBay Template**: Ready-to-use eBay listing template
   - **Text Format**: Human-readable summary

### Method 3: Right-Click Menu
1. Right-click anywhere on a Poshmark listing page
2. Select "Extract Poshmark Listing" from the context menu

## Extracted Data Fields

- **Basic Info**: Title, price, original price, brand, size
- **Details**: Category, condition, description
- **Images**: All listing photos with URLs
- **Seller Info**: Username and rating
- **Statistics**: Like count, comment count
- **Metadata**: Extraction timestamp, source URL

## Export Formats

### eBay Template
The extension automatically:
- Maps Poshmark categories to eBay categories
- Converts condition descriptions to eBay standards
- Suggests pricing (20% markup over Poshmark price)
- Formats description for eBay listing

### CSV Format
Perfect for:
- Spreadsheet analysis
- Bulk processing multiple listings
- Integration with inventory management systems

## Tips for Best Results

1. **Wait for Page Load**: Ensure the Poshmark page is fully loaded before extracting
2. **Check Data Preview**: Always review extracted data before exporting
3. **Image Handling**: The extension captures image URLs - you'll need to download and re-upload images to other platforms
4. **Pricing Strategy**: Consider platform fees when using the suggested eBay pricing

## Troubleshooting

### Extension Not Working
- Ensure you're on a Poshmark listing page (URL contains `/listing/`)
- Refresh the page and try again
- Check browser console for error messages

### Missing Data
- Some fields may be empty if Poshmark doesn't display that information
- Try scrolling down to load all page content
- Newer or updated Poshmark layouts may require selector updates

### Export Issues
- Ensure your browser allows file downloads
- Check your downloads folder for exported files
- Try a different export format if one isn't working

## Technical Notes

### Browser Compatibility
- Designed for Chrome/Chromium browsers
- Uses Manifest V3 (latest Chrome extension format)
- Requires modern JavaScript features

### Data Accuracy
- Extraction relies on Poshmark's HTML structure
- May require updates if Poshmark changes their layout
- Always verify extracted data before using

### Privacy & Security
- Extension only accesses Poshmark listing pages
- No data is sent to external servers
- All processing happens locally in your browser

## Legal Considerations

- ✅ **Your Own Listings**: Perfectly fine to extract data from your own listings
- ⚠️ **Terms of Service**: Review Poshmark's ToS regarding automated access
- 📋 **Content Ownership**: Ensure you have rights to reuse descriptions and images
- 🔄 **Cross-Platform Rules**: Check each platform's policies on cross-listing

## Future Enhancements

Potential features for future versions:
- Support for Mercari and other platforms
- Bulk extraction for multiple listings
- Direct integration with eBay's API
- Image download and processing
- Automated price optimization

## Support

If you encounter issues:
1. Check this README for troubleshooting tips
2. Verify you're using the latest version
3. Test on different Poshmark listings
4. Check browser developer console for errors

## File Structure

```
poshmark-extractor/
├── manifest.json          # Extension configuration
├── content.js             # Main extraction logic
├── content.css            # Styling for page elements
├── popup.html            # Extension popup interface
├── popup.js              # Popup functionality
├── background.js         # Background script
└── icons/                # Extension icons (optional)
    ├── icon16.png
    ├── icon48.png
    └── icon128.png
```

---

**Happy Cross-Platform Selling!** 🛍️