# File: python-admin/main_pyside.py
# Twinfolks Door Decor - Wreath Management System
# FIXED: Settings persistence for project folder location + Working Sorting

import sys
import os
import json
import requests
from pathlib import Path
from datetime import datetime
import shutil
import uuid
import re  # For hashtag extraction
import chardet  # For encoding detection

from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                            QWidget, QPushButton, QTableWidget, QTableWidgetItem, 
                            QHeaderView, QLabel, QLineEdit, QCheckBox, QSpinBox,
                            QTextEdit, QDialog, QDialogButtonBox, QFileDialog,
                            QMessageBox, QProgressBar, QStatusBar, QMenuBar,
                            QMenu, QSplitter, QGroupBox, QGridLayout, QComboBox,
                            QTabWidget, QAbstractItemView, QFrame)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QSize, QStandardPaths
from PySide6.QtGui import QPixmap, QIcon, QAction, QFont, QColor, QPalette

from image_viewer_pyside import ImageViewerDialog
from settings_dialog_pyside import SettingsDialog
from wreath_editor_pyside import WreathEditorDialog
from deploy_manager_pyside import DeployManager

class AppLocationManager:
    """Manages the app's current project folder location in a persistent way"""
    
    @staticmethod
    def get_app_config_dir():
        """Get the application configuration directory"""
        # Use system AppData directory for Windows
        if os.name == 'nt':  # Windows
            app_data = Path(os.environ.get('APPDATA', Path.home() / 'AppData' / 'Roaming'))
            config_dir = app_data / 'TwinfolksWreathManager'
        else:  # macOS/Linux
            config_dir = Path.home() / '.config' / 'TwinfolksWreathManager'
        
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir
    
    @staticmethod
    def get_current_project_folder():
        """Get the currently configured project folder path"""
        config_dir = AppLocationManager.get_app_config_dir()
        location_file = config_dir / 'current_project_folder.json'
        
        if location_file.exists():
            try:
                with open(location_file, 'r') as f:
                    data = json.load(f)
                    folder_path = Path(data.get('project_folder', ''))
                    if folder_path.exists():
                        return folder_path
            except Exception:
                pass  # Fall through to default
        
        # Default to current directory if no saved location or path doesn't exist
        return Path.cwd()
    
    @staticmethod
    def save_current_project_folder(folder_path):
        """Save the current project folder path"""
        config_dir = AppLocationManager.get_app_config_dir()
        location_file = config_dir / 'current_project_folder.json'
        
        try:
            with open(location_file, 'w') as f:
                json.dump({'project_folder': str(folder_path)}, f, indent=2)
        except Exception as e:
            print(f"Could not save project folder location: {e}")

class FileEncodingHelper:
    """Helper class to handle file encoding issues when importing JSON"""
    
    @staticmethod
    def detect_encoding(file_path):
        """Detect the encoding of a file"""
        try:
            with open(file_path, 'rb') as file:
                raw_data = file.read()
                result = chardet.detect(raw_data)
                return result['encoding'] or 'utf-8'
        except Exception:
            return 'utf-8'
    
    @staticmethod
    def read_json_file_robust(file_path):
        """
        Read a JSON file with robust encoding handling
        Returns: (success, data, encoding_used, error_message)
        """
        file_path = Path(file_path)
        
        # List of encodings to try
        encodings_to_try = [
            'utf-8',
            'utf-8-sig',  # UTF-8 with BOM
            'cp1252',     # Windows-1252
            'iso-8859-1', # Latin-1
            'ascii'
        ]
        
        # First, try to detect encoding
        detected_encoding = FileEncodingHelper.detect_encoding(file_path)
        if detected_encoding and detected_encoding not in encodings_to_try:
            encodings_to_try.insert(0, detected_encoding)
        
        last_error = None
        
        for encoding in encodings_to_try:
            try:
                with open(file_path, 'r', encoding=encoding) as file:
                    content = file.read()
                    # Try to parse JSON
                    data = json.loads(content)
                    return True, data, encoding, None
                    
            except UnicodeDecodeError as e:
                last_error = f"Encoding {encoding}: {str(e)}"
                continue
            except json.JSONDecodeError as e:
                return False, None, encoding, f"JSON parsing error with {encoding}: {str(e)}"
            except Exception as e:
                last_error = f"Unexpected error with {encoding}: {str(e)}"
                continue
        
        return False, None, None, f"Could not read file with any encoding. Last error: {last_error}"

class HashtagExtractor:
    """Extract and process hashtags from wreath descriptions"""
    
    @staticmethod
    def extract_hashtags_from_text(text):
        """Extract hashtags from text description"""
        if not text:
            return []
        
        # Find all hashtags (words that start with #)
        hashtag_pattern = r'#(\w+)'
        matches = re.findall(hashtag_pattern, text.lower())
        
        # Clean and deduplicate
        hashtags = []
        for tag in matches:
            tag = tag.strip()
            if tag and tag not in hashtags:
                hashtags.append(tag)
        
        return hashtags
    
    @staticmethod
    def process_wreath_hashtags(wreath):
        """Process hashtags for a single wreath from its description"""
        description = wreath.get('description', '')
        
        # Extract hashtags from description
        extracted_hashtags = HashtagExtractor.extract_hashtags_from_text(description)
        
        # Get existing hashtags
        existing_hashtags = wreath.get('hashtags', [])
        if isinstance(existing_hashtags, str):
            # Convert string to list
            existing_hashtags = [tag.strip() for tag in existing_hashtags.split(',') if tag.strip()]
        elif not isinstance(existing_hashtags, list):
            existing_hashtags = []
        
        # Combine and deduplicate
        all_hashtags = existing_hashtags.copy()
        for tag in extracted_hashtags:
            if tag not in all_hashtags:
                all_hashtags.append(tag)
        
        # Update wreath
        wreath['hashtags'] = all_hashtags
        
        return len(extracted_hashtags)  # Return count of newly extracted hashtags

class ImageDownloadThread(QThread):
    """Thread for downloading images without blocking UI"""
    image_downloaded = Signal(str, QPixmap)  # url, pixmap
    
    # Class-level cache of failed URLs to avoid retrying
    _failed_urls = set()
    
    def __init__(self, url):
        super().__init__()
        self.url = url
        
    def run(self):
        try:
            if not self.url or self.url in ImageDownloadThread._failed_urls:
                return
                
            response = requests.get(self.url, timeout=5)  # Reduced timeout
            response.raise_for_status()
            
            pixmap = QPixmap()
            pixmap.loadFromData(response.content)
            
            if not pixmap.isNull():
                # Scale to 80x80 for table display
                scaled_pixmap = pixmap.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.image_downloaded.emit(self.url, scaled_pixmap)
                
        except Exception as e:
            # Add to failed URLs cache to avoid retrying
            ImageDownloadThread._failed_urls.add(self.url)
            # Only print the first few failures to avoid spam
            if len(ImageDownloadThread._failed_urls) <= 5:
                print(f"Image download failed (will not retry): {self.url}")
            elif len(ImageDownloadThread._failed_urls) == 6:
                print(f"Suppressing further image download error messages...")

class WreathImageWidget(QLabel):
    """Custom widget to display wreath images in table"""
    
    def __init__(self, image_url=None):
        super().__init__()
        self.image_url = image_url
        self.setFixedSize(80, 80)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("border: 1px solid #ccc; background-color: #f5f5f5;")
        
        if image_url:
            self.setText("Loading...")
            self.download_thread = ImageDownloadThread(image_url)
            self.download_thread.image_downloaded.connect(self.set_image)
            self.download_thread.start()
        else:
            self.setText("No Image")
            
    def set_image(self, url, pixmap):
        """Set the downloaded image"""
        if url == self.image_url:
            self.setPixmap(pixmap)
            self.setText("")

class WreathTableWidget(QTableWidget):
    """Custom table widget for wreaths"""
    
    def __init__(self):
        super().__init__()
        self.setup_table()
        
    def setup_table(self):
        # Set column headers
        headers = ["Image", "Title", "Sold", "Featured", "Price", "Hashtags", "Description", "Date Created", "Actions"]
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        
        # Configure table
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setAlternatingRowColors(True)
        self.verticalHeader().setVisible(False)
        
        # Set column widths
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # Image
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)  # Title - draggable
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)  # Sold
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # Featured  
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)  # Price - draggable
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)  # Hashtags - draggable
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Interactive)  # Description - draggable
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Interactive)  # Date Created - draggable
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)  # Actions
        
        # Set specific column widths
        self.setColumnWidth(0, 90)   # Image
        self.setColumnWidth(2, 60)   # Sold
        self.setColumnWidth(3, 80)   # Featured
        self.setColumnWidth(4, 80)   # Price
        self.setColumnWidth(7, 100)  # Date Created
        self.setColumnWidth(8, 160)  # Actions
        
        # We'll connect the signal from the main manager instead
        
        # Set row height to accommodate images
        self.verticalHeader().setDefaultSectionSize(90)
 
class TwinfolksWreathManager(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Load project folder location from persistent storage
        self.project_folder = AppLocationManager.get_current_project_folder()
        
        # Ensure project structure exists
        self.ensure_project_structure()
        
        # Initialize data
        self.wreaths_data = []
        self.filtered_wreaths_data = []  # For filtered display
        self.settings = {}
        self.changes_made = False
        
        # Filter state
        self.active_filters = {"show_all": True, "featured": False, "sold": False, "available": False}
        
        # Load data
        self.load_settings()
        self.load_wreaths()
        
        # Setup UI
        self.init_ui()
        self.populate_table()
        
        # Load saved column widths
        self.load_column_widths()
        
        # Update window title with current folder
        self.setWindowTitle(f"Twinfolks Wreath Manager - {self.project_folder}")
        
    def ensure_project_structure(self):
        """Ensure required directories exist"""
        directories = ['backups', 'imports', 'exports', 'encoding_backups']
        for directory in directories:
            (self.project_folder / directory).mkdir(exist_ok=True)
            
        # Create welcome file if it doesn't exist
        welcome_file = self.project_folder / "WELCOME.txt"
        if not welcome_file.exists():
            with open(welcome_file, 'w') as f:
                f.write("Twinfolks Wreath Manager Project Folder\n")
                f.write(f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write("This folder contains:\n")
                f.write("- wreaths.json (main inventory)\n")
                f.write("- settings.json (app settings)\n")
                f.write("- backups/ (automatic backups)\n")
                f.write("- imports/ (JSON files to import)\n")
                f.write("- exports/ (exported files)\n")
                f.write("- encoding_backups/ (problematic file backups)\n")
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Twinfolks Wreath Manager")
        self.setGeometry(100, 100, 1400, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create components
        self.create_menu_bar()
        self.create_toolbar(layout)
        self.create_main_table(layout)
        self.create_status_bar()
        
    def create_menu_bar(self):
        """Create the menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        import_action = QAction('Import Wreaths...', self)
        import_action.triggered.connect(self.import_wreaths)
        file_menu.addAction(import_action)
        
        export_action = QAction('Export Wreaths...', self)
        export_action.triggered.connect(self.export_wreaths)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        settings_action = QAction('Settings...', self)
        settings_action.triggered.connect(self.open_settings)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Exit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
    def create_toolbar(self, layout):
        """Create the toolbar with buttons and status"""
        toolbar = QHBoxLayout()
        
        # Action buttons
        add_btn = QPushButton("Add New Wreath")
        add_btn.clicked.connect(self.add_new_wreath)
        toolbar.addWidget(add_btn)
        
        save_btn = QPushButton("Save Changes")
        save_btn.clicked.connect(self.save_wreaths)
        toolbar.addWidget(save_btn)
        
        # Changes indicator
        self.changes_label = QLabel("No unsaved changes")
        self.changes_label.setStyleSheet("color: #16a34a; font-weight: bold;")
        toolbar.addWidget(self.changes_label)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
    def create_main_table(self, layout):
        """Create the main table widget"""
        # Filter and Sort controls
        controls_layout = QVBoxLayout()
        
        # Filter toggle buttons
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter:"))
        
        self.show_all_btn = QPushButton("Show All")
        self.show_all_btn.setCheckable(True)
        self.show_all_btn.setChecked(True)  # Default active
        self.show_all_btn.clicked.connect(lambda checked: self.on_filter_clicked("show_all", checked))
        filter_layout.addWidget(self.show_all_btn)
        
        self.featured_only_btn = QPushButton("Featured Only")
        self.featured_only_btn.setCheckable(True)
        self.featured_only_btn.clicked.connect(lambda checked: self.on_filter_clicked("featured", checked))
        filter_layout.addWidget(self.featured_only_btn)
        
        self.sold_only_btn = QPushButton("Sold Only")
        self.sold_only_btn.setCheckable(True)
        self.sold_only_btn.clicked.connect(lambda checked: self.on_filter_clicked("sold", checked))
        filter_layout.addWidget(self.sold_only_btn)
        
        self.available_only_btn = QPushButton("Available Only")
        self.available_only_btn.setCheckable(True)
        self.available_only_btn.clicked.connect(lambda checked: self.on_filter_clicked("available", checked))
        filter_layout.addWidget(self.available_only_btn)
        
        filter_layout.addStretch()
        controls_layout.addLayout(filter_layout)
        
        # Sort controls
        sort_layout = QHBoxLayout()
        
        sort_layout.addWidget(QLabel("Sort by:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems([
            "Featured (Default)",
            "Title A-Z", 
            "Title Z-A",
            "Price Low to High",
            "Price High to Low",
            "Date Created (Oldest First)",
            "Date Created (Newest First)"
        ])
        self.sort_combo.currentTextChanged.connect(self.apply_sort)
        sort_layout.addWidget(self.sort_combo)
        
        sort_layout.addStretch()
        controls_layout.addLayout(sort_layout)
        
        layout.addLayout(controls_layout)
        
        # Main table
        self.table_widget = WreathTableWidget()
        
        # Connect column resize signal for persistence
        header = self.table_widget.horizontalHeader()
        header.sectionResized.connect(self.on_column_resized)
        
        layout.addWidget(self.table_widget)
        
    def apply_sort(self, sort_text):
        """Apply sorting to wreaths data and refresh table"""
        print(f"Sorting by: {sort_text}")  # Debug line
        
        # Prevent rapid sorting changes that can cause thread issues
        if hasattr(self, '_sort_timer'):
            self._sort_timer.stop()
        
        self._sort_timer = QTimer()
        self._sort_timer.setSingleShot(True)
        self._sort_timer.timeout.connect(lambda: self._do_sort(sort_text))
        self._sort_timer.start(1000)  # 1000ms delay
        
    def _do_sort(self, sort_text):
        """Actually perform the sorting"""
        if sort_text == "Featured (Default)":
            # Featured items first, then others
            self.wreaths_data.sort(key=lambda w: (not w.get('featured', False), w.get('title', '').lower()))
        elif sort_text == "Title A-Z":
            # Alphabetical, ignore punctuation
            self.wreaths_data.sort(key=lambda w: re.sub(r'[^\w\s]', '', w.get('title', '')).lower())
        elif sort_text == "Title Z-A":
            # Reverse alphabetical, ignore punctuation  
            self.wreaths_data.sort(key=lambda w: re.sub(r'[^\w\s]', '', w.get('title', '')).lower(), reverse=True)
        elif sort_text == "Price Low to High":
            # $0 at top, then low to high
            self.wreaths_data.sort(key=lambda w: (w.get('localPrice', 0) or w.get('price', 0) or 0))
        elif sort_text == "Price High to Low":
            # High to low, $0 at bottom
            self.wreaths_data.sort(key=lambda w: -(w.get('localPrice', 0) or w.get('price', 0) or 0))
        elif sort_text == "Date Created (Oldest First)":
            # Sort by date created, oldest first (1900 dates will be at top)
            def date_sort_key(w):
                date_str = w.get('dateCreated', '1900-01-01')
                try:
                    from datetime import datetime
                    return datetime.strptime(date_str, '%Y-%m-%d')
                except:
                    return datetime(1900, 1, 1)  # Fallback for invalid dates
            self.wreaths_data.sort(key=date_sort_key)
        elif sort_text == "Date Created (Newest First)":
            # Sort by date created, newest first 
            def date_sort_key(w):
                date_str = w.get('dateCreated', '1900-01-01')
                try:
                    from datetime import datetime
                    return datetime.strptime(date_str, '%Y-%m-%d')
                except:
                    return datetime(1900, 1, 1)  # Fallback for invalid dates
            self.wreaths_data.sort(key=date_sort_key, reverse=True)
        
        self.populate_table()
        
    def create_status_bar(self):
        """Create status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.update_status()
        
    def update_status(self):
        """Update status bar"""
        count = len(self.wreaths_data)
        sold_count = len([w for w in self.wreaths_data if w.get('sold', False)])
        available_count = count - sold_count
        
        status_text = f"Total: {count} | Available: {available_count} | Sold: {sold_count} | Folder: {self.project_folder}"
        self.status_bar.showMessage(status_text)
        
    def populate_table(self):
        """Populate the table with wreath data"""
        self.table_widget.setRowCount(len(self.wreaths_data))
        
        for row, wreath in enumerate(self.wreaths_data):
            # Image
            image_widget = WreathImageWidget(wreath.get('images', [None])[0] if wreath.get('images') else None)
            self.table_widget.setCellWidget(row, 0, image_widget)
            
            # Title
            title_item = QTableWidgetItem(wreath.get('title', 'Untitled'))
            self.table_widget.setItem(row, 1, title_item)
            
            # Sold
            sold_item = QTableWidgetItem("✓" if wreath.get('sold', False) else "")
            sold_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_widget.setItem(row, 2, sold_item)
            
            # Featured
            featured_item = QTableWidgetItem("⭐" if wreath.get('featured', False) else "")
            featured_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_widget.setItem(row, 3, featured_item)
            
            # Price
            price = wreath.get('localPrice', 0) or wreath.get('price', 0)
            price_item = QTableWidgetItem(f"${price:.2f}" if price else "$0.00")
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table_widget.setItem(row, 4, price_item)
            
            # Hashtags
            hashtags = wreath.get('hashtags', [])
            if isinstance(hashtags, list):
                hashtags_text = ', '.join([f"#{tag}" for tag in hashtags[:3]])  # Show first 3
                if len(hashtags) > 3:
                    hashtags_text += f" (+{len(hashtags) - 3} more)"
            else:
                hashtags_text = str(hashtags)
            hashtags_item = QTableWidgetItem(hashtags_text)
            self.table_widget.setItem(row, 5, hashtags_item)
            
            # Description (NEW COLUMN)
            description = wreath.get('description', '')
            # Truncate long descriptions
            display_description = description[:100] + "..." if len(description) > 100 else description
            description_item = QTableWidgetItem(display_description)
            description_item.setToolTip(description)  # Full description in tooltip
            self.table_widget.setItem(row, 6, description_item)
            
            # Date Created
            date_created = wreath.get('dateCreated', '1900-01-01')
            if not date_created or date_created == '':
                date_created = '1900-01-01'
                # Auto-set the date in the data for existing records
                wreath['dateCreated'] = date_created
            
            # Format as MM/DD/YYYY
            try:
                from datetime import datetime
                date_obj = datetime.strptime(date_created, '%Y-%m-%d')
                formatted_date = date_obj.strftime('%m/%d/%Y')
            except:
                formatted_date = '01/01/1900'  # Fallback
                
            date_item = QTableWidgetItem(formatted_date)
            date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Highlight 1900 dates to draw attention
            if formatted_date == '01/01/1900':
                from PySide6.QtGui import QBrush, QColor
                date_item.setBackground(QBrush(QColor("#ffeb3b")))  # Yellow background
                date_item.setForeground(QBrush(QColor("#d84315")))  # Red text
                date_item.setToolTip("This date needs to be updated! Click Edit to set the real creation date.")
            
            self.table_widget.setItem(row, 7, date_item)
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            
            edit_btn = QPushButton("Edit")
            edit_btn.clicked.connect(lambda checked=False, r=row: self.edit_wreath(r))
            actions_layout.addWidget(edit_btn)
            
            images_btn = QPushButton("Images")
            images_btn.clicked.connect(lambda checked=False, r=row: self.view_images(r))
            actions_layout.addWidget(images_btn)
            
            # Delete button
            delete_btn = QPushButton("✗")
            delete_btn.setToolTip("Delete this wreath")
            delete_btn.setStyleSheet("QPushButton { color: red; font-weight: bold; font-size: 14px; }")
            delete_btn.setMaximumWidth(25)
            delete_btn.clicked.connect(lambda checked=False, r=row: self.delete_wreath(r))
            actions_layout.addWidget(delete_btn)
            
            self.table_widget.setCellWidget(row, 8, actions_widget)
        # Initialize filtered data on first load
        if not hasattr(self, 'filtered_wreaths_data'):
            self.filtered_wreaths_data = self.wreaths_data[:]

        self.update_status()
        
    def load_settings(self):
        """Load settings from JSON file with robust encoding handling"""
        settings_file = self.project_folder / "settings.json"
        
        if not settings_file.exists():
            # Create default settings
            self.settings = {
                'project_folder': str(self.project_folder),
                'auto_backup': True,
                'backup_count': 10,
                'netlify_site_id': '',
                'netlify_access_token': ''
            }
            return
            
        # Use robust file reading
        success, data, encoding_used, error_msg = FileEncodingHelper.read_json_file_robust(settings_file)
        
        if success and isinstance(data, dict):
            self.settings = data
            # Ensure project folder is current
            self.settings['project_folder'] = str(self.project_folder)
        else:
            # Use defaults if settings file is corrupted
            self.settings = {
                'project_folder': str(self.project_folder),
                'auto_backup': True,
                'backup_count': 10,
                'netlify_site_id': '',
                'netlify_access_token': ''
            }
            if not success:
                QMessageBox.warning(
                    self, "Settings Warning", 
                    f"Could not load settings.json:\n{error_msg}\n\nUsing default settings."
                )
            
    def save_settings(self):
        """Save settings to JSON file"""
        settings_file = self.project_folder / "settings.json"
        try:
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not save settings: {e}")
            
    def save_column_width(self, column_index, width):
        """Save individual column width to settings"""
        if 'column_widths' not in self.settings:
            self.settings['column_widths'] = {}
        
        self.settings['column_widths'][str(column_index)] = width
        self.save_settings()
        
    def load_column_widths(self):
        """Load and apply saved column widths"""
        if 'column_widths' not in self.settings:
            return
            
        column_widths = self.settings['column_widths']
        for col_str, width in column_widths.items():
            try:
                col_index = int(col_str)
                # Only apply to draggable columns
                if col_index in [1, 4, 5, 6, 7]:
                    self.table_widget.setColumnWidth(col_index, max(width, 50))
            except (ValueError, TypeError):
                continue

    def on_column_resized(self, logical_index, old_size, new_size):
        """Save column widths when user resizes columns"""
        # Only save for draggable columns (1=Title, 4=Price, 5=Hashtags, 6=Description, 7=Date Created)
        draggable_columns = [1, 4, 5, 6, 7]
        if logical_index in draggable_columns:
            # Ensure minimum width of 50px
            if new_size < 50:
                self.table_widget.setColumnWidth(logical_index, 50)
                return
            
            # Save the width
            self.save_column_width(logical_index, new_size)
            print(f"Saved column {logical_index} width: {new_size}")  # Debug line

    def restore_default_column_widths(self):
        """Restore column widths to defaults"""
        # Remove saved column widths from settings
        if 'column_widths' in self.settings:
            del self.settings['column_widths']
            self.save_settings()
        
        # Reset to default widths (Title and Description get more space)
        self.table_widget.setColumnWidth(1, 200)  # Title
        self.table_widget.setColumnWidth(4, 80)   # Price  
        self.table_widget.setColumnWidth(5, 150)  # Hashtags
        self.table_widget.setColumnWidth(6, 250)  # Description
        self.table_widget.setColumnWidth(7, 100)  # Date Created
        self.table_widget.setColumnWidth(8, 160)  # Actions - wider for 3 buttons

    def on_filter_clicked(self, filter_type, checked):
        """Handle filter button clicks with smart logic"""
        if filter_type == "show_all":
            if checked:
                # Show All clicked - turn off all other filters
                self.active_filters = {"show_all": True, "featured": False, "sold": False, "available": False}
                self.featured_only_btn.setChecked(False)
                self.sold_only_btn.setChecked(False)
                self.available_only_btn.setChecked(False)
        else:
            # Other filter clicked
            if checked:
                # Turn off Show All
                self.active_filters["show_all"] = False
                self.show_all_btn.setChecked(False)
                
                # Handle conflicting filters
                if filter_type == "sold" and self.active_filters["available"]:
                    # Sold conflicts with Available
                    self.active_filters["available"] = False
                    self.available_only_btn.setChecked(False)
                elif filter_type == "available" and self.active_filters["sold"]:
                    # Available conflicts with Sold
                    self.active_filters["sold"] = False
                    self.sold_only_btn.setChecked(False)
                
                # Set the new filter
                self.active_filters[filter_type] = True
            else:
                # Filter unchecked
                self.active_filters[filter_type] = False
                
                # If no filters are active, default to Show All
                if not any(self.active_filters[key] for key in ["featured", "sold", "available"]):
                    self.active_filters["show_all"] = True
                    self.show_all_btn.setChecked(True)
        
        # Apply the filtering
        self.apply_filters()
        
    def apply_filters(self):
        """Apply current filters to the wreath data"""
        if self.active_filters["show_all"]:
            # Show all wreaths
            self.filtered_wreaths_data = self.wreaths_data[:]
        else:
            # Filter based on active filters
            self.filtered_wreaths_data = []
            
            for wreath in self.wreaths_data:
                include_wreath = True
                
                # Check featured filter
                if self.active_filters["featured"]:
                    if not wreath.get('featured', False):
                        include_wreath = False
                
                # Check sold filter
                if self.active_filters["sold"]:
                    if not wreath.get('sold', False):
                        include_wreath = False
                
                # Check available filter
                if self.active_filters["available"]:
                    if wreath.get('sold', False):  # If sold, then not available
                        include_wreath = False
                
                if include_wreath:
                    self.filtered_wreaths_data.append(wreath)
        
        # Update the table display
        self.populate_filtered_table()

    def populate_filtered_table(self):
        """Populate table with filtered data"""
        self.table_widget.setRowCount(len(self.filtered_wreaths_data))
        
        for row, wreath in enumerate(self.filtered_wreaths_data):
            # Image
            image_widget = WreathImageWidget(wreath.get('images', [None])[0] if wreath.get('images') else None)
            self.table_widget.setCellWidget(row, 0, image_widget)
            
            # Title
            title_item = QTableWidgetItem(wreath.get('title', 'Untitled'))
            self.table_widget.setItem(row, 1, title_item)
            
            # Sold
            sold_item = QTableWidgetItem("✓" if wreath.get('sold', False) else "")
            sold_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_widget.setItem(row, 2, sold_item)
            
            # Featured
            featured_item = QTableWidgetItem("⭐" if wreath.get('featured', False) else "")
            featured_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_widget.setItem(row, 3, featured_item)
            
            # Price
            price = wreath.get('localPrice', 0) or wreath.get('price', 0)
            price_item = QTableWidgetItem(f"${price:.2f}" if price else "$0.00")
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table_widget.setItem(row, 4, price_item)
            
            # Hashtags
            hashtags = wreath.get('hashtags', [])
            if isinstance(hashtags, list):
                hashtags_text = ', '.join([f"#{tag}" for tag in hashtags[:3]])  # Show first 3
                if len(hashtags) > 3:
                    hashtags_text += f" (+{len(hashtags) - 3} more)"
            else:
                hashtags_text = str(hashtags)
            hashtags_item = QTableWidgetItem(hashtags_text)
            self.table_widget.setItem(row, 5, hashtags_item)
            
            # Description
            description = wreath.get('description', '')
            display_description = description[:100] + "..." if len(description) > 100 else description
            description_item = QTableWidgetItem(display_description)
            description_item.setToolTip(description)
            self.table_widget.setItem(row, 6, description_item)
            
            # Date Created
            date_created = wreath.get('dateCreated', '1900-01-01')
            if not date_created or date_created == '':
                date_created = '1900-01-01'
                wreath['dateCreated'] = date_created
            
            try:
                from datetime import datetime
                date_obj = datetime.strptime(date_created, '%Y-%m-%d')
                formatted_date = date_obj.strftime('%m/%d/%Y')
            except:
                formatted_date = '01/01/1900'
                
            date_item = QTableWidgetItem(formatted_date)
            date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            if formatted_date == '01/01/1900':
                from PySide6.QtGui import QBrush, QColor
                date_item.setBackground(QBrush(QColor("#ffeb3b")))
                date_item.setForeground(QBrush(QColor("#d84315")))
                date_item.setToolTip("This date needs to be updated! Click Edit to set the real creation date.")
            
            self.table_widget.setItem(row, 7, date_item)
            
            # Actions - we need to find the original row index in wreaths_data
            original_row = self.wreaths_data.index(wreath)
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            
            edit_btn = QPushButton("Edit")
            edit_btn.clicked.connect(lambda checked=False, r=original_row: self.edit_wreath(r))
            actions_layout.addWidget(edit_btn)
            
            images_btn = QPushButton("Images")
            images_btn.clicked.connect(lambda checked=False, r=original_row: self.view_images(r))
            actions_layout.addWidget(images_btn)
            
            delete_btn = QPushButton("✗")
            delete_btn.setToolTip("Delete this wreath")
            delete_btn.setStyleSheet("QPushButton { color: red; font-weight: bold; font-size: 14px; }")
            delete_btn.setMaximumWidth(25)
            delete_btn.clicked.connect(lambda checked=False, r=original_row: self.delete_wreath(r))
            actions_layout.addWidget(delete_btn)
            
            self.table_widget.setCellWidget(row, 8, actions_widget)
        
        self.update_status()

    def load_wreaths(self):
        """Load wreaths from JSON file with robust encoding handling"""
        wreaths_file = self.project_folder / "wreaths.json"
        
        if not wreaths_file.exists():
            self.wreaths_data = []
            return
            
        # Use robust file reading
        success, data, encoding_used, error_msg = FileEncodingHelper.read_json_file_robust(wreaths_file)
        
        if success:
            if isinstance(data, list):
                self.wreaths_data = data
                
                # Ensure all wreaths have required fields and process hashtags
                for wreath in self.wreaths_data:
                    if 'featured' not in wreath:
                        wreath['featured'] = False
                    if 'id' not in wreath:
                        wreath['id'] = str(uuid.uuid4())
                    
                    # UPDATED: Process hashtags from description (Priority #2)
                    HashtagExtractor.process_wreath_hashtags(wreath)
                        
            else:
                self.wreaths_data = []
                QMessageBox.warning(
                    self, "Data Format Warning", 
                    "Your wreaths.json file doesn't contain a list of wreaths.\nStarting with empty data."
                )
        else:
            self.wreaths_data = []
            QMessageBox.critical(
                self, "Data Load Error", 
                f"Could not load wreaths.json:\n{error_msg}\n\nStarting with empty data."
            )
            
    def save_wreaths(self):
        """Save wreaths data to JSON file"""
        wreaths_file = self.project_folder / "wreaths.json"
        
        # Create backup if auto-backup is enabled
        if self.settings.get('auto_backup', True):
            self.create_backup()
            
        try:
            with open(wreaths_file, 'w') as f:
                json.dump(self.wreaths_data, f, indent=2)
            
            self.changes_made = False
            self.changes_label.setText("No unsaved changes")
            self.changes_label.setStyleSheet("color: #16a34a; font-weight: bold;")
            
            QMessageBox.information(self, "Save Complete", f"Wreaths saved to:\n{wreaths_file}")
            
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Could not save wreaths: {e}")
            
    def create_backup(self):
        """Create a backup of the current wreaths file"""
        wreaths_file = self.project_folder / "wreaths.json"
        backup_dir = self.project_folder / "backups"
        
        if not wreaths_file.exists():
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"wreaths_backup_{timestamp}.json"
        
        try:
            shutil.copy2(wreaths_file, backup_file)
            
            # Clean up old backups
            backup_count = self.settings.get('backup_count', 10)
            backup_files = sorted(backup_dir.glob("wreaths_backup_*.json"))
            
            if len(backup_files) > backup_count:
                for old_backup in backup_files[:-backup_count]:
                    old_backup.unlink()
                    
        except Exception as e:
            print(f"Backup creation failed: {e}")
            
    def mark_changes_made(self):
        """Mark that changes have been made"""
        if not self.changes_made:
            self.changes_made = True
            self.changes_label.setText("Unsaved changes")
            self.changes_label.setStyleSheet("color: #dc2626; font-weight: bold;")
            
    def add_new_wreath(self):
        """Add a new wreath"""
        dialog = WreathEditorDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            new_wreath = dialog.get_wreath_data()
            self.wreaths_data.append(new_wreath)
            self.apply_filters()
            self.mark_changes_made()

    def delete_wreath(self, row):
        """Delete a wreath with confirmation"""
        if row >= len(self.wreaths_data):
            return
            
        wreath = self.wreaths_data[row]
        title = wreath.get('title', 'Untitled')
        
        # Confirmation dialog
        reply = QMessageBox.question(
            self, 
            "Confirm Delete",
            f"Are you sure you want to delete '{title}'?\n\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No  # Default to No for safety
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Remove from data
            del self.wreaths_data[row]
            
            # Refresh table
            self.apply_filters()
            
            # Mark changes
            self.mark_changes_made()
            
            # Show success message
            QMessageBox.information(self, "Deleted", f"'{title}' has been deleted.")

    def edit_wreath(self, row):
        """Edit an existing wreath"""
        if row >= len(self.wreaths_data):
            return
            
        wreath = self.wreaths_data[row]
        dialog = WreathEditorDialog(wreath, self)
        if dialog.exec() == QDialog.Accepted:
            updated_wreath = dialog.get_wreath_data()
            self.wreaths_data[row] = updated_wreath
            self.apply_filters()
            self.mark_changes_made()
            
    def view_images(self, row):
        """View/edit images for a wreath"""
        if row >= len(self.wreaths_data):
            return
        
        wreath = self.wreaths_data[row]
        images = wreath.get('images', [])
    
        # Store the original first image for comparison
        original_first_image = images[0] if images else None
    
        dialog = ImageViewerDialog(images, self)
        if dialog.exec() == QDialog.Accepted:
            updated_images = dialog.get_images()
            self.wreaths_data[row]['images'] = updated_images
        
        # Get the new first image
        new_first_image = updated_images[0] if updated_images else None
        
        # Only update the image if the first image changed
        if original_first_image != new_first_image:
            self.update_row_image(row)
            print(f"Updated image for row {row}: {original_first_image} -> {new_first_image}")
        
        self.mark_changes_made()
            
    def update_row_image(self, row):
        """Update only the image widget for a specific row"""
        if row >= len(self.wreaths_data) or row >= self.table_widget.rowCount():
            return
        
        wreath = self.wreaths_data[row]
        first_image = wreath.get('images', [None])[0] if wreath.get('images') else None
    
        # Create new image widget
        image_widget = WreathImageWidget(first_image)
        self.table_widget.setCellWidget(row, 0, image_widget)
    
    def delete_wreath(self, row):
        """Delete a wreath with confirmation"""
        if row >= len(self.wreaths_data):
            return
            
        wreath = self.wreaths_data[row]
        title = wreath.get('title', 'Untitled')
        
        reply = QMessageBox.question(
            self, 'Delete Wreath',
            f'Are you sure you want to delete "{title}"?\n\nThis action cannot be undone.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            del self.wreaths_data[row]
            self.populate_table()
            self.mark_changes_made()
            
    def import_wreaths(self):
        """Import wreaths from JSON files"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, 'Import Wreaths', 
            str(self.project_folder / "imports"),
            'JSON Files (*.json)'
        )
        
        if not file_paths:
            return
            
        imported_count = 0
        error_files = []
        
        for file_path in file_paths:
            # Use robust file reading
            success, data, encoding_used, error_msg = FileEncodingHelper.read_json_file_robust(file_path)
            
            if success:
                # Handle different import formats
                wreaths_to_import = []
                
                if isinstance(data, list):
                    # List of wreaths
                    wreaths_to_import = [w for w in data if self.validate_wreath_data(w)]
                elif isinstance(data, dict):
                    # Single wreath or wrapped format
                    if self.validate_wreath_data(data):
                        wreaths_to_import = [data]
                    elif 'wreaths' in data and isinstance(data['wreaths'], list):
                        wreaths_to_import = [w for w in data['wreaths'] if self.validate_wreath_data(w)]
                
                # Import valid wreaths
                for wreath in wreaths_to_import:
                    # Ensure required fields
                    if 'id' not in wreath:
                        wreath['id'] = str(uuid.uuid4())
                    if 'featured' not in wreath:
                        wreath['featured'] = False
                    
                    # UPDATED: Process hashtags from description (Priority #2)
                    HashtagExtractor.process_wreath_hashtags(wreath)
                    
                    self.wreaths_data.append(wreath)
                    imported_count += 1
            else:
                # Save problematic file to encoding_backups
                backup_dir = self.project_folder / "encoding_backups"
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = backup_dir / f"failed_import_{timestamp}_{Path(file_path).name}"
                try:
                    shutil.copy2(file_path, backup_file)
                except Exception:
                    pass  # Backup failed, but continue
                
                error_files.append(f"{Path(file_path).name}: {error_msg}")
        
        if imported_count > 0:
            self.populate_table()
            self.mark_changes_made()
            
            message = f"Successfully imported {imported_count} wreath(s)."
            if error_files:
                message += f"\n\nErrors with {len(error_files)} file(s):\n" + "\n".join(error_files)
            
            QMessageBox.information(self, "Import Complete", message)
        else:
            if error_files:
                QMessageBox.critical(
                    self, "Import Failed", 
                    f"Could not import any files:\n\n" + "\n".join(error_files)
                )
            else:
                QMessageBox.information(self, "Import Complete", "No valid wreaths found to import.")
            
    def validate_wreath_data(self, wreath):
        """Validate wreath data structure"""
        required_fields = ['title']
        return isinstance(wreath, dict) and any(field in wreath for field in required_fields)
        
    def export_wreaths(self):
        """Export wreaths to chosen location"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, 'Export Wreaths', 
            str(self.project_folder / "exports" / "wreaths.json"),
            'JSON Files (*.json)'
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump(self.wreaths_data, f, indent=2)
                QMessageBox.information(self, "Export Complete", f"Wreaths exported to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Could not export wreaths: {e}")
                
    def open_settings(self):
        """Open settings dialog and handle folder changes"""
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec() == QDialog.Accepted:
            new_settings = dialog.get_settings()
            
            # Check if folder location changed
            if new_settings.get('folder_changed', False):
                old_folder = new_settings.get('old_folder', '')
                new_folder = new_settings.get('new_folder', '')
                
                # FIXED: Save the new project folder location persistently
                AppLocationManager.save_current_project_folder(new_folder)
                
                # Update project folder and reload everything
                self.project_folder = Path(new_folder)
                self.ensure_project_structure()
                
                # Update window title
                self.setWindowTitle(f"Twinfolks Wreath Manager - {self.project_folder}")
                
                # Reload data from new location
                self.load_settings()
                self.load_wreaths()
                self.populate_table()
                
                QMessageBox.information(
                    self, "Folder Changed", 
                    f"Project folder updated to:\n{new_folder}\n\nData has been reloaded from the new location.\n\nThis change will persist when you restart the app."
                )
            else:
                # Update other settings
                self.settings.update(new_settings)
                self.save_settings()
                
    def closeEvent(self, event):
        """Handle application close event"""
        if self.changes_made:
            reply = QMessageBox.question(
                self, 'Unsaved Changes',
                'You have unsaved changes. Do you want to save before closing?',
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save
            )
            
            if reply == QMessageBox.StandardButton.Save:
                self.save_wreaths()
                event.accept()
            elif reply == QMessageBox.StandardButton.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Twinfolks Wreath Manager")
    app.setApplicationVersion("1.0")
    
    window = TwinfolksWreathManager()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()