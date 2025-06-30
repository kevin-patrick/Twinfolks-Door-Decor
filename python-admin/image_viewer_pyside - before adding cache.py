# File: python-admin/image_viewer_pyside.py
# Complete working image viewer for PySide6 version

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QDialogButtonBox, QTextEdit, QLineEdit,
                            QPushButton, QListWidget, QListWidgetItem,
                            QMessageBox, QGroupBox, QGridLayout,
                            QScrollArea, QWidget)
from PySide6.QtCore import Qt, QThread, Signal, QSize
from PySide6.QtGui import QPixmap
import requests

class ImageDownloadThread(QThread):
    """Thread for downloading images without blocking UI"""
    imageLoaded = Signal(str, QPixmap)  # url, pixmap
    errorOccurred = Signal(str, str)     # url, error_message
    
    def __init__(self, url):
        super().__init__()
        self.url = url
        
    def run(self):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(self.url, headers=headers, timeout=10)
            response.raise_for_status()
            
            pixmap = QPixmap()
            success = pixmap.loadFromData(response.content)
            
            if success and not pixmap.isNull():
                self.imageLoaded.emit(self.url, pixmap)
            else:
                self.errorOccurred.emit(self.url, "Invalid image format")
                
        except Exception as e:
            self.errorOccurred.emit(self.url, f"Error: {str(e)}")

class SimpleImageThumbnail(QLabel):
    """Simple image thumbnail for testing"""
    
    def __init__(self, image_url, index, parent=None):
        super().__init__(parent)
        self.image_url = image_url
        self.index = index
        self.parent_dialog = parent
        
        # Set size for thumbnails
        self.setFixedSize(300, 300)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                border: 2px solid #ddd;
                border-radius: 8px;
                background-color: #f8f9fa;
                margin: 5px;
            }
        """)
        
        # Initial placeholder
        self.setText(f"Image {index + 1}\nLoading...")
        
        # Load image
        self.load_image()
        
    def load_image(self):
        """Load image from URL"""
        if not self.image_url:
            self.setText(f"Image {self.index + 1}\nNo URL")
            return
            
        self.download_thread = ImageDownloadThread(self.image_url)
        self.download_thread.imageLoaded.connect(self.on_image_loaded)
        self.download_thread.errorOccurred.connect(self.on_image_error)
        self.download_thread.start()
        
    def on_image_loaded(self, url, pixmap):
        """Handle successful image loading"""
        if url == self.image_url:
            # Scale image to fit
            scaled_pixmap = pixmap.scaled(
                290, 290,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.setPixmap(scaled_pixmap)
            self.setToolTip(f"Image {self.index + 1}: {url}")
            
    def on_image_error(self, url, error_message):
        """Handle image loading error"""
        if url == self.image_url:
            self.setText(f"Image {self.index + 1}\n❌ Error\n{error_message[:20]}...")
            self.setToolTip(f"Failed to load: {error_message}")

class ImageViewerDialog(QDialog):
    """Working image viewer dialog"""
    
    def __init__(self, images=None, parent=None):
        super().__init__(parent)
        self.images = images.copy() if images else []
        self.thumbnail_widgets = []
        
        self.setWindowTitle("Manage Images")
        self.setModal(True)
        self.resize(800, 600)
        
        self.init_ui()
        self.create_thumbnails()
        
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Instructions
        instructions = QLabel("🖼️ Image Management\n"
                            "• View and manage wreath images\n"
                            "• Add new image URLs below\n"
                            "• First image becomes the main thumbnail")
        instructions.setStyleSheet("font-weight: bold; color: #555; padding: 10px;")
        layout.addWidget(instructions)
        
        # Current images section
        current_group = QGroupBox("Current Images")
        current_layout = QVBoxLayout(current_group)
        
        # Scroll area for images
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setMinimumHeight(300)
        
        # Container for images
        self.images_container = QWidget()
        self.images_layout = QGridLayout(self.images_container)
        self.images_layout.setSpacing(10)
        
        self.scroll_area.setWidget(self.images_container)
        current_layout.addWidget(self.scroll_area)
        
        # URL list for easy editing
        self.url_list = QTextEdit()
        self.url_list.setMaximumHeight(100)
        self.url_list.setPlaceholderText("Image URLs (one per line)...")
        current_layout.addWidget(QLabel("Edit URLs directly:"))
        current_layout.addWidget(self.url_list)
        
        layout.addWidget(current_group)
        
        # Add new image section
        add_group = QGroupBox("Add New Image")
        add_layout = QVBoxLayout(add_group)
        
        url_row = QHBoxLayout()
        self.new_url_edit = QLineEdit()
        self.new_url_edit.setPlaceholderText("https://example.com/image.jpg")
        self.new_url_edit.returnPressed.connect(self.add_url)
        url_row.addWidget(self.new_url_edit)
        
        add_btn = QPushButton("Add Image")
        add_btn.clicked.connect(self.add_url)
        url_row.addWidget(add_btn)
        
        add_layout.addLayout(url_row)
        
        # Reorder buttons
        reorder_row = QHBoxLayout()
        self.move_up_btn = QPushButton("Move Selected Up")
        self.move_down_btn = QPushButton("Move Selected Down")
        self.remove_btn = QPushButton("Remove Selected")
        self.convert_poshmark_btn = QPushButton("Convert Poshmark URLs to Medium")
        
        self.move_up_btn.clicked.connect(self.move_up)
        self.move_down_btn.clicked.connect(self.move_down)
        self.remove_btn.clicked.connect(self.remove_selected)
        self.convert_poshmark_btn.clicked.connect(self.convert_poshmark_urls)
        
        reorder_row.addWidget(self.move_up_btn)
        reorder_row.addWidget(self.move_down_btn)
        reorder_row.addWidget(self.remove_btn)
        reorder_row.addWidget(self.convert_poshmark_btn)
        
        add_layout.addLayout(reorder_row)
        layout.addWidget(add_group)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept_changes)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Track selected thumbnail
        self.selected_index = -1

    def closeEvent(self, event):
        """Handle dialog closing - stop all running threads"""
        self.clear_thumbnails()
        super().closeEvent(event)

    def create_thumbnails(self):
        """Create thumbnail widgets for all images"""
        # Clear existing thumbnails
        self.clear_thumbnails()
        
        if not self.images:
            no_images_label = QLabel("No images yet.\nAdd some URLs below!")
            no_images_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_images_label.setStyleSheet("color: #666; font-size: 14px; padding: 50px;")
            self.images_layout.addWidget(no_images_label, 0, 0)
        else:
            # Create grid of thumbnails (3 per row)
            for i, image_url in enumerate(self.images):
                thumbnail = SimpleImageThumbnail(image_url, i, self)
                
                # Make clickable for selection
                thumbnail.mousePressEvent = lambda event, idx=i: self.select_thumbnail(idx)
                
                self.thumbnail_widgets.append(thumbnail)
                
                row = i // 3
                col = i % 3
                self.images_layout.addWidget(thumbnail, row, col)
                
        # Update URL list
        self.url_list.setPlainText('\n'.join(self.images))
        
    def clear_thumbnails(self):
        """Clear all thumbnail widgets"""
        # Stop any running download threads first
        for widget in self.thumbnail_widgets:
            if hasattr(widget, 'download_thread') and widget.download_thread.isRunning():
                widget.download_thread.terminate()
                widget.download_thread.wait(1000)  # Wait up to 1 second
        
        while self.images_layout.count():
            child = self.images_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.thumbnail_widgets.clear()
        
    def select_thumbnail(self, index):
        """Select a thumbnail for operations"""
        self.selected_index = index
        
        # Update visual selection
        for i, thumb in enumerate(self.thumbnail_widgets):
            if i == index:
                thumb.setStyleSheet("""
                    QLabel {
                        border: 3px solid #007bff;
                        border-radius: 8px;
                        background-color: #e3f2fd;
                        margin: 5px;
                    }
                """)
            else:
                thumb.setStyleSheet("""
                    QLabel {
                        border: 2px solid #ddd;
                        border-radius: 8px;
                        background-color: #f8f9fa;
                        margin: 5px;
                    }
                """)
        
    def add_url(self):
        """Add a new image URL"""
        url = self.new_url_edit.text().strip()
        
        if not url:
            return
            
        if url in self.images:
            QMessageBox.information(self, "Duplicate Image", "This image URL is already added.")
            return
            
        # Basic URL validation
        if not (url.startswith('http://') or url.startswith('https://')):
            QMessageBox.warning(self, "Invalid URL", "Please enter a valid URL starting with http:// or https://")
            return
            
        # Add to images list
        self.images.append(url)
        self.new_url_edit.clear()
        
        # Recreate thumbnails
        self.create_thumbnails()
        
    def move_up(self):
        """Move selected image up"""
        if self.selected_index > 0:
            # Swap images
            self.images[self.selected_index], self.images[self.selected_index - 1] = \
                self.images[self.selected_index - 1], self.images[self.selected_index]
            
            self.selected_index -= 1
            self.create_thumbnails()
            
    def move_down(self):
        """Move selected image down"""
        if 0 <= self.selected_index < len(self.images) - 1:
            # Swap images
            self.images[self.selected_index], self.images[self.selected_index + 1] = \
                self.images[self.selected_index + 1], self.images[self.selected_index]
            
            self.selected_index += 1
            self.create_thumbnails()
            
    def remove_selected(self):
        """Remove selected image"""
        if 0 <= self.selected_index < len(self.images):
            removed_url = self.images.pop(self.selected_index)
            self.selected_index = -1
            self.create_thumbnails()
            
    def accept_changes(self):
        """Save changes from URL text area"""
        # Get URLs from text area
        text = self.url_list.toPlainText().strip()
        if text:
            urls = [url.strip() for url in text.split('\n') if url.strip()]
            self.images = urls
        else:
            self.images = []
            
        self.accept()
        
    def get_images(self):
        """Return the current list of image URLs"""
        return self.images
    
    def convert_poshmark_urls(self):
        """Convert all Poshmark URLs from small (s_) to medium (m_) format"""
        converted_count = 0
        
        for i, url in enumerate(self.images):
            if 's_wp_' in url:
                # Convert s_wp_ to m_wp_
                new_url = url.replace('s_wp_', 'm_wp_')
                self.images[i] = new_url
                converted_count += 1
            elif '/s_' in url and ('cloudfront' in url or 'poshmark' in url.lower()):
                # Convert CloudFront/Poshmark URLs: /s_ to /m_
                new_url = url.replace('/s_', '/m_')
                self.images[i] = new_url
                converted_count += 1
        
        if converted_count > 0:
            QMessageBox.information(self, "URLs Converted", 
                                  f"Converted {converted_count} Poshmark URL(s) to medium size.")
            # Refresh the display
            self.create_thumbnails()
        else:
            QMessageBox.information(self, "No Conversion Needed", 
                                  "No Poshmark URLs found that need conversion.")