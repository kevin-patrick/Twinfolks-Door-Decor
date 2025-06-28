# File: python-admin/wreath_editor.py
# Individual wreath editor dialog with all fields

import uuid
from datetime import datetime
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QDialogButtonBox, QTabWidget,
                            QWidget, QCheckBox, QSpinBox, QTextEdit, QGroupBox,
                            QGridLayout, QMessageBox, QFrame, QComboBox,
                            QDateEdit, QScrollArea, QDoubleSpinBox)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont

from image_viewer import ImageViewerDialog

class WreathEditorDialog(QDialog):
    """Dialog for editing individual wreath details"""
    
    def __init__(self, wreath_data=None, parent=None):
        super().__init__(parent)
        self.wreath_data = wreath_data.copy() if wreath_data else self.create_new_wreath()
        self.parent_window = parent
        
        self.setWindowTitle("Edit Wreath" if wreath_data else "New Wreath")
        self.setModal(True)
        self.resize(600, 700)
        
        self.init_ui()
        self.populate_fields()
        
    def create_new_wreath(self):
        """Create new wreath with default values"""
        return {
            'id': str(uuid.uuid4()),
            'title': '',
            'localPrice': 0,
            'sold': False,
            'featured': False,
            'hashtags': [],
            'category': 'holiday',
            'dateAdded': datetime.now().strftime('%Y-%m-%d'),
            'description': '',
            'platforms': {
                'poshmark': '',
                'fbMarketplace': '',
                'mercari': '',
                'other1': ''
            },
            'images': []
        }
        
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Create scroll area for the form
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Main form widget
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        
        # Basic Information
        self.create_basic_info_section(form_layout)
        
        # Pricing and Status
        self.create_pricing_status_section(form_layout)
        
        # Description
        self.create_description_section(form_layout)
        
        # Hashtags
        self.create_hashtags_section(form_layout)
        
        # Platform Links
        self.create_platforms_section(form_layout)
        
        # Images
        self.create_images_section(form_layout)
        
        # Set scroll area widget
        scroll_area.setWidget(form_widget)
        layout.addWidget(scroll_area)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept_changes)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def create_basic_info_section(self, layout):
        """Create basic information section"""
        group = QGroupBox("Basic Information")
        group_layout = QGridLayout(group)
        
        # Title
        group_layout.addWidget(QLabel("Title:"), 0, 0)
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Enter wreath title...")
        group_layout.addWidget(self.title_edit, 0, 1, 1, 2)
        
        # Category
        group_layout.addWidget(QLabel("Category:"), 1, 0)
        self.category_combo = QComboBox()
        self.category_combo.addItems([
            'holiday', 'seasonal', 'spring', 'summer', 'fall', 'winter',
            'christmas', 'thanksgiving', 'easter', 'valentine', 'halloween',
            'patriotic', 'wedding', 'custom', 'other'
        ])
        group_layout.addWidget(self.category_combo, 1, 1)
        
        # Date Added
        group_layout.addWidget(QLabel("Date Added:"), 1, 2)
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        group_layout.addWidget(self.date_edit, 1, 3)
        
        # ID (read-only)
        group_layout.addWidget(QLabel("ID:"), 2, 0)
        self.id_label = QLabel()
        self.id_label.setStyleSheet("color: #666; font-family: monospace; font-size: 10px;")
        group_layout.addWidget(self.id_label, 2, 1, 1, 3)
        
        layout.addWidget(group)
        
    def create_pricing_status_section(self, layout):
        """Create pricing and status section"""
        group = QGroupBox("Pricing & Status")
        group_layout = QGridLayout(group)
        
        # Price
        group_layout.addWidget(QLabel("Price ($):"), 0, 0)
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setRange(0, 9999.99)
        self.price_spin.setDecimals(2)
        self.price_spin.setPrefix("$")
        group_layout.addWidget(self.price_spin, 0, 1)
        
        # Sold checkbox
        self.sold_checkbox = QCheckBox("Sold")
        group_layout.addWidget(self.sold_checkbox, 0, 2)
        
        # Featured checkbox
        self.featured_checkbox = QCheckBox("Featured")
        self.featured_checkbox.setToolTip("Featured wreaths appear first on the website")
        group_layout.addWidget(self.featured_checkbox, 0, 3)
        
        layout.addWidget(group)
        
    def create_description_section(self, layout):
        """Create description section"""
        group = QGroupBox("Description")
        group_layout = QVBoxLayout(group)
        
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(100)
        self.description_edit.setPlaceholderText("Enter detailed description of the wreath...")
        group_layout.addWidget(self.description_edit)
        
        layout.addWidget(group)
        
    def create_hashtags_section(self, layout):
        """Create hashtags section"""
        group = QGroupBox("Hashtags")
        group_layout = QVBoxLayout(group)
        
        # Instructions
        instructions = QLabel("Enter hashtags separated by commas (without # symbol)")
        instructions.setStyleSheet("color: #666; font-size: 11px;")
        group_layout.addWidget(instructions)
        
        # Hashtags input
        self.hashtags_edit = QTextEdit()
        self.hashtags_edit.setMaximumHeight(80)
        self.hashtags_edit.setPlaceholderText("fall, autumn, thanksgiving, orange, brown, seasonal...")
        group_layout.addWidget(self.hashtags_edit)
        
        # Quick hashtag buttons
        quick_layout = QHBoxLayout()
        quick_layout.addWidget(QLabel("Quick add:"))
        
        quick_hashtags = [
            "fall", "winter", "spring", "summer", "christmas", "thanksgiving",
            "halloween", "easter", "valentine", "patriotic", "wedding"
        ]
        
        for hashtag in quick_hashtags:
            btn = QPushButton(hashtag)
            btn.setMaximumWidth(80)
            btn.clicked.connect(lambda checked, tag=hashtag: self.add_quick_hashtag(tag))
            quick_layout.addWidget(btn)
            
        quick_layout.addStretch()
        group_layout.addLayout(quick_layout)
        
        layout.addWidget(group)
        
    def create_platforms_section(self, layout):
        """Create platform links section"""
        group = QGroupBox("Platform Links")
        group_layout = QGridLayout(group)
        
        # Poshmark
        group_layout.addWidget(QLabel("Poshmark:"), 0, 0)
        self.poshmark_edit = QLineEdit()
        self.poshmark_edit.setPlaceholderText("https://poshmark.com/listing/...")
        group_layout.addWidget(self.poshmark_edit, 0, 1)
        
        # Facebook Marketplace
        group_layout.addWidget(QLabel("FB Marketplace:"), 1, 0)
        self.fb_marketplace_edit = QLineEdit()
        self.fb_marketplace_edit.setPlaceholderText("https://facebook.com/marketplace/item/...")
        group_layout.addWidget(self.fb_marketplace_edit, 1, 1)
        
        # Mercari
        group_layout.addWidget(QLabel("Mercari:"), 2, 0)
        self.mercari_edit = QLineEdit()
        self.mercari_edit.setPlaceholderText("https://mercari.com/us/item/...")
        group_layout.addWidget(self.mercari_edit, 2, 1)
        
        # Other platform
        group_layout.addWidget(QLabel("Other:"), 3, 0)
        self.other_edit = QLineEdit()
        self.other_edit.setPlaceholderText("Other platform URL...")
        group_layout.addWidget(self.other_edit, 3, 1)
        
        layout.addWidget(group)
        
    def create_images_section(self, layout):
        """Create images section"""
        group = QGroupBox("Images")
        group_layout = QVBoxLayout(group)
        
        # Image count label
        self.image_count_label = QLabel()
        group_layout.addWidget(self.image_count_label)
        
        # Image management buttons
        button_layout = QHBoxLayout()
        
        self.view_images_btn = QPushButton("View & Manage Images")
        self.view_images_btn.clicked.connect(self.open_image_manager)
        button_layout.addWidget(self.view_images_btn)
        
        self.add_image_btn = QPushButton("Add Image URL")
        self.add_image_btn.clicked.connect(self.add_single_image)
        button_layout.addWidget(self.add_image_btn)
        
        self.clear_images_btn = QPushButton("Clear All Images")
        self.clear_images_btn.setStyleSheet("QPushButton { color: #dc2626; }")
        self.clear_images_btn.clicked.connect(self.clear_all_images)
        button_layout.addWidget(self.clear_images_btn)
        
        button_layout.addStretch()
        group_layout.addLayout(button_layout)
        
        # Quick image URL input
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("Quick add URL:"))
        self.quick_image_url = QLineEdit()
        self.quick_image_url.setPlaceholderText("Paste image URL here...")
        self.quick_image_url.returnPressed.connect(self.add_quick_image_url)
        url_layout.addWidget(self.quick_image_url)
        
        add_url_btn = QPushButton("Add")
        add_url_btn.clicked.connect(self.add_quick_image_url)
        url_layout.addWidget(add_url_btn)
        
        group_layout.addLayout(url_layout)
        
        layout.addWidget(group)
        
    def populate_fields(self):
        """Populate form fields with wreath data"""
        # Basic info
        self.title_edit.setText(self.wreath_data.get('title', ''))
        self.category_combo.setCurrentText(self.wreath_data.get('category', 'holiday'))
        
        # Date
        date_str = self.wreath_data.get('dateAdded', datetime.now().strftime('%Y-%m-%d'))
        try:
            date_parts = date_str.split('-')
            if len(date_parts) == 3:
                year, month, day = map(int, date_parts)
                self.date_edit.setDate(QDate(year, month, day))
        except:
            self.date_edit.setDate(QDate.currentDate())
            
        # ID
        self.id_label.setText(self.wreath_data.get('id', ''))
        
        # Pricing and status
        self.price_spin.setValue(self.wreath_data.get('localPrice', 0))
        self.sold_checkbox.setChecked(self.wreath_data.get('sold', False))
        self.featured_checkbox.setChecked(self.wreath_data.get('featured', False))
        
        # Description
        self.description_edit.setPlainText(self.wreath_data.get('description', ''))
        
        # Hashtags
        hashtags = self.wreath_data.get('hashtags', [])
        hashtags_text = ', '.join(hashtags)
        self.hashtags_edit.setPlainText(hashtags_text)
        
        # Platform links
        platforms = self.wreath_data.get('platforms', {})
        self.poshmark_edit.setText(platforms.get('poshmark', ''))
        self.fb_marketplace_edit.setText(platforms.get('fbMarketplace', ''))
        self.mercari_edit.setText(platforms.get('mercari', ''))
        self.other_edit.setText(platforms.get('other1', ''))
        
        # Update image count
        self.update_image_count()
        
    def update_image_count(self):
        """Update the image count label"""
        image_count = len(self.wreath_data.get('images', []))
        if image_count == 0:
            self.image_count_label.setText("No images")
            self.image_count_label.setStyleSheet("color: #dc2626;")
        elif image_count == 1:
            self.image_count_label.setText("1 image (will be used as thumbnail)")
            self.image_count_label.setStyleSheet("color: #059669;")
        else:
            self.image_count_label.setText(f"{image_count} images (first image will be used as thumbnail)")
            self.image_count_label.setStyleSheet("color: #059669;")
            
    def add_quick_hashtag(self, hashtag):
        """Add a quick hashtag"""
        current_text = self.hashtags_edit.toPlainText().strip()
        if current_text:
            if hashtag not in current_text:
                new_text = current_text + f", {hashtag}"
                self.hashtags_edit.setPlainText(new_text)
        else:
            self.hashtags_edit.setPlainText(hashtag)
            
    def add_quick_image_url(self):
        """Add image URL from quick input"""
        url = self.quick_image_url.text().strip()
        if url:
            images = self.wreath_data.get('images', [])
            if url not in images:
                images.append(url)
                self.wreath_data['images'] = images
                self.update_image_count()
                self.quick_image_url.clear()
                QMessageBox.information(self, "Image Added", "Image URL added successfully!")
            else:
                QMessageBox.warning(self, "Duplicate URL", "This image URL is already in the list.")
                
    def add_single_image(self):
        """Add a single image via input dialog"""
        from PyQt6.QtWidgets import QInputDialog
        
        url, ok = QInputDialog.getText(
            self, 'Add Image URL',
            'Enter image URL:',
            text='https://'
        )
        
        if ok and url.strip():
            images = self.wreath_data.get('images', [])
            if url not in images:
                images.append(url)
                self.wreath_data['images'] = images
                self.update_image_count()
                QMessageBox.information(self, "Image Added", "Image URL added successfully!")
            else:
                QMessageBox.warning(self, "Duplicate URL", "This image URL is already in the list.")
                
    def clear_all_images(self):
        """Clear all images with confirmation"""
        if self.wreath_data.get('images'):
            reply = QMessageBox.question(
                self, 'Clear All Images',
                'Are you sure you want to remove all images?\n\nThis action cannot be undone.',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.wreath_data['images'] = []
                self.update_image_count()
                
    def open_image_manager(self):
        """Open the image viewer/manager"""
        images = self.wreath_data.get('images', [])
        dialog = ImageViewerDialog(images, self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_images = dialog.get_images()
            self.wreath_data['images'] = updated_images
            self.update_image_count()
            
    def accept_changes(self):
        """Accept and validate changes"""
        # Validate required fields
        if not self.title_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Title is required.")
            self.title_edit.setFocus()
            return
            
        # Update wreath data
        self.wreath_data['title'] = self.title_edit.text().strip()
        self.wreath_data['category'] = self.category_combo.currentText()
        self.wreath_data['dateAdded'] = self.date_edit.date().toString('yyyy-MM-dd')
        self.wreath_data['localPrice'] = self.price_spin.value()
        self.wreath_data['sold'] = self.sold_checkbox.isChecked()
        self.wreath_data['featured'] = self.featured_checkbox.isChecked()
        self.wreath_data['description'] = self.description_edit.toPlainText().strip()
        
        # Process hashtags
        hashtags_text = self.hashtags_edit.toPlainText().strip()
        if hashtags_text:
            hashtags = [tag.strip() for tag in hashtags_text.split(',') if tag.strip()]
            self.wreath_data['hashtags'] = hashtags
        else:
            self.wreath_data['hashtags'] = []
            
        # Update platform links
        self.wreath_data['platforms'] = {
            'poshmark': self.poshmark_edit.text().strip(),
            'fbMarketplace': self.fb_marketplace_edit.text().strip(),
            'mercari': self.mercari_edit.text().strip(),
            'other1': self.other_edit.text().strip()
        }
        
        self.accept()
        
    def get_wreath_data(self):
        """Get the updated wreath data"""
        return self.wreath_data

# For testing the dialog standalone
if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Test with sample data
    test_wreath = {
        'id': 'test-123',
        'title': 'Beautiful Fall Wreath',
        'localPrice': 45.99,
        'sold': False,
        'featured': True,
        'hashtags': ['fall', 'autumn', 'orange', 'thanksgiving'],
        'category': 'fall',
        'dateAdded': '2024-10-01',
        'description': 'A gorgeous fall wreath with autumn colors and natural elements.',
        'platforms': {
            'poshmark': 'https://poshmark.com/listing/test',
            'fbMarketplace': '',
            'mercari': '',
            'other1': ''
        },
        'images': [
            'https://example.com/image1.jpg',
            'https://example.com/image2.jpg'
        ]
    }
    
    dialog = WreathEditorDialog(test_wreath)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        print("Updated wreath data:", dialog.get_wreath_data())
    
    sys.exit(app.exec())