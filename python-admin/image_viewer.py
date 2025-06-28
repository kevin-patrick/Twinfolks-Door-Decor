# File: python-admin/image_viewer.py
# Image viewer and manager dialog with drag-and-drop reordering

import sys
import requests
from urllib.parse import urlparse
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QScrollArea, QWidget,
                            QDialogButtonBox, QMessageBox, QFrame, QGridLayout,
                            QApplication, QProgressBar, QTextEdit)
from PyQt6.QtCore import Qt, QMimeData, QByteArray, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QDrag, QPainter, QFont

class ImageLoadThread(QThread):
    """Thread for loading images from URLs"""
    imageLoaded = pyqtSignal(int, QPixmap)
    imageError = pyqtSignal(int, str)
    
    def __init__(self, index, url):
        super().__init__()
        self.index = index
        self.url = url
        
    def run(self):
        try:
            response = requests.get(self.url, timeout=10)
            response.raise_for_status()
            
            pixmap = QPixmap()
            if pixmap.loadFromData(response.content):
                self.imageLoaded.emit(self.index, pixmap)
            else:
                self.imageError.emit(self.index, "Invalid image format")
                
        except Exception as e:
            self.imageError.emit(self.index, str(e))

class DraggableImageLabel(QLabel):
    """Image label that supports drag and drop reordering"""
    
    def __init__(self, index, image_url, parent=None):
        super().__init__(parent)
        self.index = index
        self.image_url = image_url
        self.parent_viewer = parent
        self.setAcceptDrops(True)
        
        # Style the image container
        self.setMinimumSize(200, 200)
        self.setMaximumSize(200, 200)
        self.setFrameStyle(QFrame.Shape.Box)
        self.setLineWidth(2)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                border: 2px solid #ccc;
                border-radius: 8px;
                background-color: #f9f9f9;
                margin: 5px;
            }
            QLabel:hover {
                border-color: #3b82f6;
                background-color: #eff6ff;
            }
        """)
        
        # Load the image
        self.load_image()
        
    def load_image(self):
        """Load image from URL"""
        if self.image_url:
            self.setText("Loading...")
            self.setStyleSheet(self.styleSheet() + "font-size: 12px; color: #666;")
            
            # Start loading in background thread
            self.loader = ImageLoadThread(self.index, self.image_url)
            self.loader.imageLoaded.connect(self.on_image_loaded)
            self.loader.imageError.connect(self.on_image_error)
            self.loader.start()
        else:
            self.setText("No Image")
            
    def on_image_loaded(self, index, pixmap):
        """Handle successful image load"""
        if index == self.index:
            # Scale image to fit while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(180, 180, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.setPixmap(scaled_pixmap)
            
    def on_image_error(self, index, error):
        """Handle image load error"""
        if index == self.index:
            self.setText(f"❌\nFailed to load\n{error[:30]}...")
            self.setStyleSheet(self.styleSheet() + "color: red; font-size: 10px;")
            
    def mousePressEvent(self, event):
        """Handle mouse press for drag start"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Start drag operation
            drag = QDrag(self)
            mimeData = QMimeData()
            mimeData.setText(str(self.index))
            drag.setMimeData(mimeData)
            
            # Create drag pixmap
            if self.pixmap():
                drag.setPixmap(self.pixmap().scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio))
            
            # Execute drag
            drag.exec(Qt.DropAction.MoveAction)
            
    def dragEnterEvent(self, event):
        """Handle drag enter"""
        if event.mimeData().hasText():
            event.acceptProposedAction()
            self.setStyleSheet(self.styleSheet() + "border-color: #10b981; background-color: #ecfdf5;")
            
    def dragLeaveEvent(self, event):
        """Handle drag leave"""
        self.setStyleSheet(self.styleSheet().replace("border-color: #10b981; background-color: #ecfdf5;", ""))
        
    def dropEvent(self, event):
        """Handle drop event for reordering"""
        if event.mimeData().hasText():
            source_index = int(event.mimeData().text())
            target_index = self.index
            
            if source_index != target_index and self.parent_viewer:
                self.parent_viewer.reorder_images(source_index, target_index)
                
        self.setStyleSheet(self.styleSheet().replace("border-color: #10b981; background-color: #ecfdf5;", ""))
        event.acceptProposedAction()

class ImageViewerDialog(QDialog):
    """Dialog for viewing and managing wreath images"""
    
    def __init__(self, images, parent=None):
        super().__init__(parent)
        self.images = images.copy()  # Work with a copy
        self.image_widgets = []
        
        self.setWindowTitle("Wreath Images")
        self.setModal(True)
        self.resize(800, 600)
        
        self.init_ui()
        self.populate_images()
        
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Instructions
        instructions = QLabel("💡 Drag and drop images to reorder them. The first image will be the main thumbnail.")
        instructions.setStyleSheet("background-color: #dbeafe; padding: 10px; border-radius: 4px; color: #1e40af;")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Image grid in scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        self.images_widget = QWidget()
        self.images_layout = QGridLayout(self.images_widget)
        self.images_layout.setSpacing(10)
        
        self.scroll_area.setWidget(self.images_widget)
        layout.addWidget(self.scroll_area)
        
        # Add new image section
        add_section = QFrame()
        add_section.setFrameStyle(QFrame.Shape.Box)
        add_section.setStyleSheet("QFrame { border: 1px solid #d1d5db; border-radius: 4px; padding: 10px; }")
        add_layout = QVBoxLayout(add_section)
        
        add_label = QLabel("Add New Image:")
        add_label.setFont(QFont("", 10, QFont.Weight.Bold))
        add_layout.addWidget(add_label)
        
        url_layout = QHBoxLayout()
        self.new_image_url = QLineEdit()
        self.new_image_url.setPlaceholderText("Enter image URL (https://...)") 
        self.new_image_url.returnPressed.connect(self.add_image)
        
        self.add_image_btn = QPushButton("Add Image")
        self.add_image_btn.clicked.connect(self.add_image)
        self.add_image_btn.setStyleSheet("QPushButton { background-color: #10b981; color: white; padding: 5px 15px; border-radius: 4px; }")
        
        url_layout.addWidget(self.new_image_url)
        url_layout.addWidget(self.add_image_btn)
        add_layout.addLayout(url_layout)
        
        # Image URL tips
        tips = QTextEdit()
        tips.setMaximumHeight(80)
        tips.setHtml("""
        <div style="font-size: 11px; color: #666;">
        <b>💡 Tips for Image URLs:</b><br>
        • <b>Imgur:</b> Upload image → Right-click → "Copy image address"<br>
        • <b>Google Drive:</b> Share image → "Anyone with link" → Copy link<br>
        • <b>Avoid:</b> Facebook, Instagram, Google Photos (links often break)
        </div>
        """)
        tips.setReadOnly(True)
        add_layout.addWidget(tips)
        
        layout.addWidget(add_section)
        
        # Statistics
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("color: #666; font-size: 12px; padding: 5px;")
        layout.addWidget(self.stats_label)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.update_stats()
        
    def populate_images(self):
        """Populate the image grid"""
        # Clear existing widgets
        for widget in self.image_widgets:
            widget.setParent(None)
        self.image_widgets.clear()
        
        # Create image widgets
        cols = 3  # Images per row
        for i, image_url in enumerate(self.images):
            row = i // cols
            col = i % cols
            
            # Create container for image and controls
            container = QWidget()
            container_layout = QVBoxLayout(container)
            container_layout.setSpacing(5)
            
            # Image widget
            image_widget = DraggableImageLabel(i, image_url, self)
            container_layout.addWidget(image_widget)
            
            # Controls
            controls_layout = QHBoxLayout()
            
            # Position indicator
            position_label = QLabel(f"#{i + 1}")
            position_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            position_label.setStyleSheet("font-weight: bold; color: #3b82f6;")
            controls_layout.addWidget(position_label)
            
            # Delete button
            delete_btn = QPushButton("Delete")
            delete_btn.setMaximumSize(60, 25)
            delete_btn.setStyleSheet("QPushButton { background-color: #ef4444; color: white; border-radius: 3px; }")
            delete_btn.clicked.connect(lambda checked, index=i: self.delete_image(index))
            controls_layout.addWidget(delete_btn)
            
            container_layout.addLayout(controls_layout)
            
            # Add to grid
            self.images_layout.addWidget(container, row, col)
            self.image_widgets.append(container)
            
        self.update_stats()
        
    def reorder_images(self, source_index, target_index):
        """Reorder images by moving source to target position"""
        if 0 <= source_index < len(self.images) and 0 <= target_index < len(self.images):
            # Move the image
            image = self.images.pop(source_index)
            self.images.insert(target_index, image)
            
            # Refresh the display
            self.populate_images()
            
    def delete_image(self, index):
        """Delete image with confirmation"""
        if 0 <= index < len(self.images):
            reply = QMessageBox.question(
                self, 'Delete Image',
                f'Delete image #{index + 1}?\n\nThis action cannot be undone.',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                del self.images[index]
                self.populate_images()
                
    def add_image(self):
        """Add new image from URL"""
        url = self.new_image_url.text().strip()
        if not url:
            return
            
        # Basic URL validation
        if not url.startswith(('http://', 'https://')):
            QMessageBox.warning(self, "Invalid URL", "Please enter a valid URL starting with http:// or https://")
            return
            
        # Check for common image extensions
        parsed_url = urlparse(url.lower())
        if not any(parsed_url.path.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']):
            reply = QMessageBox.question(
                self, 'Add Image',
                'This URL does not appear to be a direct image link. Add anyway?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
                
        # Add the image
        self.images.append(url)
        self.new_image_url.clear()
        self.populate_images()
        
    def update_stats(self):
        """Update statistics display"""
        count = len(self.images)
        if count == 0:
            self.stats_label.setText("No images")
        elif count == 1:
            self.stats_label.setText("1 image (will be used as thumbnail)")
        else:
            self.stats_label.setText(f"{count} images (first image will be used as thumbnail)")
            
    def get_images(self):
        """Get the current list of images"""
        return self.images

# For testing the dialog standalone
if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Test images
    test_images = [
        "https://picsum.photos/300/300?random=1",
        "https://picsum.photos/300/300?random=2", 
        "https://picsum.photos/300/300?random=3"
    ]
    
    dialog = ImageViewerDialog(test_images)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        print("Final images:", dialog.get_images())
    
    sys.exit(app.exec())