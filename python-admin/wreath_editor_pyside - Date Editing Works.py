# File: python-admin/wreath_editor_pyside.py
# Complete working wreath editor for PySide6 version

import uuid
from datetime import datetime
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QDialogButtonBox, 
                            QCheckBox, QTextEdit, QDoubleSpinBox, QGroupBox,
                            QGridLayout, QSpinBox, QDateEdit)
from PySide6.QtCore import QDate
from PySide6.QtCore import Qt

class WreathEditorDialog(QDialog):
    def __init__(self, wreath_data=None, parent=None):
        super().__init__(parent)
        self.wreath_data = wreath_data.copy() if wreath_data else self.create_new_wreath()
        
        self.setWindowTitle("Edit Wreath" if wreath_data else "New Wreath")
        self.setModal(True)
        self.resize(600, 500)
        
        self.init_ui()
        self.populate_fields()
        
    def create_new_wreath(self):
        """Create a new wreath with default values"""
        return {
            'id': str(uuid.uuid4()),
            'title': '',
            'localPrice': 0,
            'price': 0,  # Alternative price field
            'sold': False,
            'featured': False,
            'hashtags': [],
            'description': '',
            'images': [],
            'dateAdded': datetime.now().isoformat()
        }
        
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Basic Information Group
        basic_group = QGroupBox("Basic Information")
        basic_layout = QGridLayout(basic_group)
        
        # Title
        basic_layout.addWidget(QLabel("Title:"), 0, 0)
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Enter wreath title...")
        basic_layout.addWidget(self.title_edit, 0, 1)
        
        # Price
        basic_layout.addWidget(QLabel("Price ($):"), 1, 0)
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setRange(0, 9999.99)
        self.price_spin.setDecimals(2)
        self.price_spin.setPrefix("$")
        basic_layout.addWidget(self.price_spin, 1, 1)
        
        # Date Created
        basic_layout.addWidget(QLabel("Date Created:"), 2, 0)
        self.date_created_edit = QDateEdit()
        self.date_created_edit.setCalendarPopup(True)
        self.date_created_edit.setDate(QDate.currentDate())  # Default to today
        self.date_created_edit.setToolTip("Date this wreath was created")
        basic_layout.addWidget(self.date_created_edit, 2, 1)
        
        layout.addWidget(basic_group)
        
        # Status Group
        status_group = QGroupBox("Status")
        status_layout = QHBoxLayout(status_group)
        
        self.sold_checkbox = QCheckBox("Sold")
        self.featured_checkbox = QCheckBox("Featured")
        status_layout.addWidget(self.sold_checkbox)
        status_layout.addWidget(self.featured_checkbox)
        status_layout.addStretch()
        
        layout.addWidget(status_group)
        
        # Description Group
        desc_group = QGroupBox("Description")
        desc_layout = QVBoxLayout(desc_group)
        
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(120)
        self.description_edit.setPlaceholderText("Enter wreath description...")
        desc_layout.addWidget(self.description_edit)
        
        layout.addWidget(desc_group)
        
        # Hashtags Group
        hashtags_group = QGroupBox("Hashtags")
        hashtags_layout = QVBoxLayout(hashtags_group)
        
        hashtags_layout.addWidget(QLabel("Hashtags (comma separated, without #):"))
        self.hashtags_edit = QLineEdit()
        self.hashtags_edit.setPlaceholderText("fall, autumn, thanksgiving, orange...")
        hashtags_layout.addWidget(self.hashtags_edit)
        
        layout.addWidget(hashtags_group)
        
        # Images info (read-only)
        images_group = QGroupBox("Images")
        images_layout = QVBoxLayout(images_group)
        
        self.images_label = QLabel("Use the 'Images' button in the main table to manage images.")
        self.images_label.setStyleSheet("color: #666; font-style: italic;")
        images_layout.addWidget(self.images_label)
        
        layout.addWidget(images_group)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept_changes)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def populate_fields(self):
        """Populate form fields with current wreath data"""
        self.title_edit.setText(self.wreath_data.get('title', ''))
        
        # Handle both localPrice and price fields
        price = self.wreath_data.get('localPrice', 0) or self.wreath_data.get('price', 0)
        self.price_spin.setValue(price)
        
        self.sold_checkbox.setChecked(self.wreath_data.get('sold', False))
        self.featured_checkbox.setChecked(self.wreath_data.get('featured', False))
        self.description_edit.setPlainText(self.wreath_data.get('description', ''))
        
        # Handle hashtags
        hashtags = self.wreath_data.get('hashtags', [])
        if isinstance(hashtags, list):
            # Remove # symbols if present and join
            clean_hashtags = [tag.lstrip('#') for tag in hashtags]
            self.hashtags_edit.setText(', '.join(clean_hashtags))
        else:
            self.hashtags_edit.setText(str(hashtags))
            
        # Date Created
        date_created = self.wreath_data.get('dateCreated', '1900-01-01')
        try:
            from datetime import datetime
            date_obj = datetime.strptime(date_created, '%Y-%m-%d')
            q_date = QDate(date_obj.year, date_obj.month, date_obj.day)
            self.date_created_edit.setDate(q_date)
        except:
            # Default to today if date is invalid
            self.date_created_edit.setDate(QDate.currentDate())
        
    def accept_changes(self):
        """Save changes and accept dialog"""
        # Validate required fields
        title = self.title_edit.text().strip()
        if not title:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Validation Error", "Please enter a title for the wreath.")
            self.title_edit.setFocus()
            return
            
        # Update wreath data
        self.wreath_data['title'] = title
        self.wreath_data['localPrice'] = self.price_spin.value()
        self.wreath_data['price'] = self.price_spin.value()  # Keep both for compatibility
        self.wreath_data['sold'] = self.sold_checkbox.isChecked()
        self.wreath_data['featured'] = self.featured_checkbox.isChecked()
        self.wreath_data['description'] = self.description_edit.toPlainText().strip()
        
        # Process hashtags
        hashtags_text = self.hashtags_edit.text().strip()
        if hashtags_text:
            # Split by comma and clean up
            hashtags = [tag.strip().lstrip('#').lower() for tag in hashtags_text.split(',') if tag.strip()]
            self.wreath_data['hashtags'] = hashtags
        else:
            self.wreath_data['hashtags'] = []
            
        # Save date created
        q_date = self.date_created_edit.date()
        date_string = f"{q_date.year()}-{q_date.month():02d}-{q_date.day():02d}"
        self.wreath_data['dateCreated'] = date_string
        
        # Ensure required fields exist
            
        self.accept()
        
    def get_wreath_data(self):
        """Return the updated wreath data"""
        return self.wreath_data