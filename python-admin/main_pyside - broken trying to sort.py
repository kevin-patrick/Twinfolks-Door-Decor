# File: python-admin/main_pyside.py
# Twinfolks Door Decor - Wreath Management System
# FIXED: Settings persistence for project folder location (Priority #3 Bug Fix)

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
                    folder_path = data.get('project_folder', '')
                    
                    if folder_path and Path(folder_path).exists():
                        return Path(folder_path)
            except Exception:
                pass
        
        # Default location if no valid saved location
        return Path.home() / "Documents" / "Twinfolks_Wreaths"
    
    @staticmethod
    def save_current_project_folder(folder_path):
        """Save the current project folder path for future app launches"""
        config_dir = AppLocationManager.get_app_config_dir()
        location_file = config_dir / 'current_project_folder.json'
        
        try:
            data = {
                'project_folder': str(folder_path),
                'last_updated': datetime.now().isoformat(),
                'app_version': '1.0.0'
            }
            
            with open(location_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Warning: Could not save project folder location: {e}")
            return False

class HashtagExtractor:
    """Helper class for extracting hashtags from descriptions"""
    
    @staticmethod
    def extract_hashtags_from_text(text):
        """
        Extract hashtags from text using regex
        Returns: (cleaned_text, hashtags_list)
        """
        if not text:
            return "", []
        
        # Find all hashtags (# followed by word characters)
        hashtag_pattern = r'#(\w+)'
        hashtags = re.findall(hashtag_pattern, text, re.IGNORECASE)
        
        # Remove hashtags from text
        cleaned_text = re.sub(hashtag_pattern, '', text, flags=re.IGNORECASE)
        
        # Clean up extra whitespace
        cleaned_text = ' '.join(cleaned_text.split())
        
        # Convert hashtags to lowercase for consistency
        hashtags = [tag.lower() for tag in hashtags]
        
        return cleaned_text, hashtags
    
    @staticmethod
    def process_wreath_hashtags(wreath_data):
        """
        Process a wreath's description to extract hashtags
        Modifies the wreath_data in place
        """
        description = wreath_data.get('description', '')
        
        if description:
            cleaned_description, extracted_hashtags = HashtagExtractor.extract_hashtags_from_text(description)
            
            # Update description (remove hashtags)
            wreath_data['description'] = cleaned_description
            
            # Update hashtags (combine existing with extracted)
            existing_hashtags = wreath_data.get('hashtags', [])
            if isinstance(existing_hashtags, str):
                existing_hashtags = [existing_hashtags]
            
            # Combine and deduplicate hashtags
            all_hashtags = list(set(existing_hashtags + extracted_hashtags))
            wreath_data['hashtags'] = all_hashtags
        
        return wreath_data

class FileEncodingHelper:
    """Helper class for robust file reading with encoding detection"""
    
    @staticmethod
    def detect_encoding(file_path):
        """Detect file encoding using chardet"""
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)
                return result.get('encoding', 'utf-8')
        except Exception:
            return 'utf-8'
    
    @staticmethod
    def read_json_file_robust(file_path):
        """
        Read JSON file with automatic encoding detection
        Returns: (success, data, encoding_used, error_message)
        """
        encodings_to_try = [
            'utf-8',
            'utf-8-sig',  # UTF-8 with BOM
            'latin-1',
            'cp1252',     # Windows encoding
            'iso-8859-1'
        ]
        
        # First try to auto-detect encoding
        detected_encoding = FileEncodingHelper.detect_encoding(file_path)
        if detected_encoding and detected_encoding not in encodings_to_try:
            encodings_to_try.insert(0, detected_encoding)
        
        for encoding in encodings_to_try:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    data = json.load(f)
                    return True, data, encoding, None
            except (UnicodeDecodeError, UnicodeError):
                continue
            except json.JSONDecodeError as e:
                return False, None, encoding, f"JSON parsing error: {e}"
            except Exception as e:
                return False, None, encoding, f"File reading error: {e}"
        
        return False, None, None, f"Could not decode file with any supported encoding: {encodings_to_try}"
    
    @staticmethod
    def create_backup(file_path, backup_dir=None):
        """Create a timestamped backup of a file"""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return None
                
            if backup_dir is None:
                backup_dir = file_path.parent / "backups"
            else:
                backup_dir = Path(backup_dir)
                
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
            backup_path = backup_dir / backup_name
            
            shutil.copy2(file_path, backup_path)
            return backup_path
        except Exception:
            return None

# File: python-admin/main_pyside.py
# Add these classes BEFORE the WreathImageWidget class

import re

class SortableTitleItem(QTableWidgetItem):
    """Table item that sorts by cleaned text but displays original"""
    
    def __init__(self, title):
        super().__init__(title)
        self.original_title = title
        # Remove punctuation and extra spaces for sorting
        self.clean_title = re.sub(r'[^\w\s]', '', title).strip().lower()
        
    def __lt__(self, other):
        """Custom comparison for sorting"""
        if isinstance(other, SortableTitleItem):
            return self.clean_title < other.clean_title
        return super().__lt__(other)

class SortablePriceItem(QTableWidgetItem):
    """Table item that sorts prices with $0 at top, then ascending"""
    
    def __init__(self, price_value, display_text):
        super().__init__(display_text)
        self.price_value = float(price_value) if price_value else 0.0
        self.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
    def __lt__(self, other):
        """Custom comparison: $0 at top, then ascending"""
        if isinstance(other, SortablePriceItem):
            # Both are $0 - equal
            if self.price_value == 0 and other.price_value == 0:
                return False
            # This is $0, other is not - this comes first  
            if self.price_value == 0 and other.price_value > 0:
                return True
            # Other is $0, this is not - other comes first
            if other.price_value == 0 and self.price_value > 0:
                return False
            # Neither is $0 - normal ascending sort
            return self.price_value < other.price_value
        return super().__lt__(other)

class WreathImageWidget(QLabel):
    """Enhanced widget to display wreath thumbnails"""
    
    def __init__(self, image_url=None):
        super().__init__()
        self.image_url = image_url
        self.setFixedSize(80, 80)  # Larger thumbnail for better visibility
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                border: 1px solid #ddd;
                border-radius: 6px;
                background-color: #f9f9f9;
            }
            QLabel:hover {
                border-color: #007bff;
                background-color: #e3f2fd;
            }
        """)
        
        if image_url:
            self.load_image()
        else:
            self.setText("No Image\n📷")
            self.setToolTip("No image available")
            
    def load_image(self):
        """Load image from URL with better handling"""
        try:
            # Start image loading in background
            self.setText("Loading...\n⏳")
            self.setToolTip(f"Loading: {self.image_url}")
            
            # Use the same download thread as the image viewer
            from image_viewer_pyside import ImageDownloadThread
            self.download_thread = ImageDownloadThread(self.image_url)
            self.download_thread.imageLoaded.connect(self.on_image_loaded)
            self.download_thread.errorOccurred.connect(self.on_image_error)
            self.download_thread.start()
            
        except Exception as e:
            self.setText("❌\nError")
            self.setToolTip(f"Error loading image: {str(e)}")
            
    def on_image_loaded(self, url, pixmap):
        """Handle successful image loading"""
        if url == self.image_url and not pixmap.isNull():
            # Scale image to fit while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(
                78, 78,  # Slightly smaller than widget to account for border
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.setPixmap(scaled_pixmap)
            self.setToolTip(f"Image: {url}\nSize: {pixmap.width()}x{pixmap.height()}")
        else:
            self.on_image_error(url, "Invalid image data")
            
    def on_image_error(self, url, error_message):
        """Handle image loading error"""
        if url == self.image_url:
            self.setText("❌\nFailed")
            self.setToolTip(f"Failed to load: {error_message}")

class WreathTableWidget(QTableWidget):
    """Custom table widget with enhanced functionality"""
    
    def __init__(self):
        super().__init__()
        self.setup_table()
        
    def setup_table(self):
        # Set up columns - UPDATED: Added Description column
        self.setColumnCount(8)
        headers = ['Image', 'Title', 'Sold', 'Featured', 'Price', 'Hashtags', 'Description', 'Actions']
        self.setHorizontalHeaderLabels(headers)
        
        # Configure table appearance
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        
        # Set column widths for better image display
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # Image
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) # Title
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)  # Sold
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # Featured  
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # Price
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive) # Hashtags
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Interactive) # Description
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)  # Actions
        
        # Set fixed widths for specific columns - UPDATED for larger images
        self.setColumnWidth(0, 90)   # Image (larger for 80x80 thumbnails)
        self.setColumnWidth(2, 60)   # Sold
        self.setColumnWidth(3, 70)   # Featured
        self.setColumnWidth(4, 80)   # Price
        self.setColumnWidth(5, 150)  # Hashtags
        self.setColumnWidth(6, 200)  # Description
        self.setColumnWidth(7, 120)  # Actions
        
        # Set row height to accommodate larger thumbnails
        self.verticalHeader().setDefaultSectionSize(90)
        
        # Enable sorting with detection
        self.setSortingEnabled(True)
        self.sortByColumn(1, Qt.SortOrder.AscendingOrder)  # Default sort by Title
        
        # Connect to detect sorting changes
        header = self.horizontalHeader()
        header.sectionClicked.connect(self.on_header_clicked)
        
    # Replace on_header_clicked method again
    def on_header_clicked(self, logical_index):
        """Handle column header clicks for sorting"""
        print(f"🔄 Header clicked! Column: {logical_index}")
        
        # Try stored reference first
        if hasattr(self, 'main_window') and self.main_window:
            print("🔄 Using stored main_window reference")
            main_win = self.main_window
        else:
            print("🔄 Falling back to parent() method")
            main_win = self.parent()
            
        print(f"🔄 Main window: {main_win}")
        print(f"🔄 Has repopulate method: {hasattr(main_win, 'repopulate_after_sort')}")
        
        if hasattr(main_win, 'repopulate_after_sort'):
            print("🔄 Scheduling repopulate after sort...")
            # Use QTimer to delay repopulation until after sort is complete
            from PySide6.QtCore import QTimer
            QTimer.singleShot(200, main_win.repopulate_after_sort)
        else:
            print("❌ Main window doesn't have repopulate_after_sort method")

class TwinfolksWreathManager(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.wreaths_data = []
        self.changes_made = False
        self.settings = {}
        
        # FIXED: Load project folder from persistent location
        self.project_folder = AppLocationManager.get_current_project_folder()
        self.ensure_project_structure()
        
        # Load data from current project folder
        self.load_settings()
        self.load_wreaths()
        
        self.init_ui()
        self.populate_table()
        
    def ensure_project_structure(self):
        """Create project folder structure"""
        folders = [
            self.project_folder,
            self.project_folder / "backups",
            self.project_folder / "imports",
            self.project_folder / "exports",
            self.project_folder / "encoding_backups"  # For encoding fix backups
        ]
        
        for folder in folders:
            folder.mkdir(parents=True, exist_ok=True)
        
        # Create welcome file if this is first time
        welcome_file = self.project_folder / "WELCOME.txt"
        if not welcome_file.exists():
            welcome_content = f"""
Welcome to Twinfolks Wreath Manager!
====================================

This folder contains all your wreath data and project files.

📁 Folder Structure:
- wreaths.json: Your main wreath inventory
- settings.json: Application settings
- backups/: Automatic backups of your data
- imports/: Place JSON files here to import
- exports/: Exported files will be saved here

💡 Tips:
- The app automatically backs up your data before saving changes
- You can manually edit wreaths.json if needed
- Import new Poshmark JSON files by copying them to imports/ folder

Happy wreath managing! 🎄

Current folder location: {self.project_folder}
You can change this location in Edit → Settings
            """.strip()
            
            with open(welcome_file, 'w') as f:
                f.write(welcome_content)
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle(f"Twinfolks Wreath Manager - {self.project_folder}")
        self.setGeometry(100, 100, 1500, 900)  # Even wider for larger image thumbnails
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create toolbar
        self.create_toolbar(layout)
        
        # Create main table
        self.create_main_table(layout)
        
        # Create status bar
        self.create_status_bar()
        
    def create_menu_bar(self):
        """Create the menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        new_action = QAction('New Wreath', self)
        new_action.setShortcut('Ctrl+N')
        new_action.triggered.connect(self.add_new_wreath)
        file_menu.addAction(new_action)
        
        file_menu.addSeparator()
        
        import_action = QAction('Import JSON Files...', self)
        import_action.setShortcut('Ctrl+I')
        import_action.triggered.connect(self.import_json_files)
        file_menu.addAction(import_action)
        
        export_action = QAction('Export Wreaths...', self)
        export_action.setShortcut('Ctrl+E')
        export_action.triggered.connect(self.export_wreaths)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        save_action = QAction('Save', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_wreaths)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Exit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu('Edit')
        
        settings_action = QAction('Settings...', self)
        settings_action.triggered.connect(self.open_settings)
        edit_menu.addAction(settings_action)
        
        # Deploy menu
        deploy_menu = menubar.addMenu('Deploy')
        
        test_deploy_action = QAction('Test Deploy', self)
        test_deploy_action.triggered.connect(self.deploy_to_netlify)
        deploy_menu.addAction(test_deploy_action)
        
    def create_toolbar(self, layout):
        """Create the toolbar"""
        toolbar = QHBoxLayout()
        
        # Left side buttons
        self.add_btn = QPushButton("Add New Wreath")
        self.add_btn.clicked.connect(self.add_new_wreath)
        toolbar.addWidget(self.add_btn)
        
        self.import_btn = QPushButton("Import JSON Files")
        self.import_btn.clicked.connect(self.import_json_files)
        toolbar.addWidget(self.import_btn)
        
        self.save_btn = QPushButton("Save Changes")
        self.save_btn.clicked.connect(self.save_wreaths)
        self.save_btn.setEnabled(False)
        toolbar.addWidget(self.save_btn)
        
        toolbar.addStretch()
        
        # Right side - status
        self.changes_label = QLabel("")
        toolbar.addWidget(self.changes_label)
        
        layout.addLayout(toolbar)
        
    # Replace create_main_table method
    def create_main_table(self, layout):
        """Create the main table widget"""
        self.table_widget = WreathTableWidget()
        
        # Store reference to main window in table widget
        self.table_widget.main_window = self
        print(f"🔧 Stored main window reference in table widget")
        
        layout.addWidget(self.table_widget)
        
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
            
            # Title with custom sorting
            title = wreath.get('title', 'Untitled')
            title_item = SortableTitleItem(title)
            self.table_widget.setItem(row, 1, title_item)
            
            # Sold
            sold_item = QTableWidgetItem("✓" if wreath.get('sold', False) else "")
            sold_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_widget.setItem(row, 2, sold_item)
            
            # Featured
            featured_item = QTableWidgetItem("⭐" if wreath.get('featured', False) else "")
            featured_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_widget.setItem(row, 3, featured_item)
            
            # Price with custom sorting
            price = wreath.get('localPrice', 0) or wreath.get('price', 0)
            display_price = f"${price:.2f}" if price else "$0.00"
            price_item = SortablePriceItem(price, display_price)
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
            
            # Actions with debugging
            try:
                print(f"Creating actions for row {row}, wreath: {wreath.get('title', 'No Title')}")
                
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(2, 2, 2, 2)
                
                # Create edit button
                edit_btn = QPushButton("Edit")
                edit_btn.clicked.connect(lambda checked=False, r=row: self.edit_wreath(r))
                actions_layout.addWidget(edit_btn)
                
                # Create images button  
                images_btn = QPushButton("Images")
                images_btn.clicked.connect(lambda checked=False, r=row: self.view_images(r))
                actions_layout.addWidget(images_btn)
                
                # Set the widget
                self.table_widget.setCellWidget(row, 7, actions_widget)
                print(f"✓ Successfully created actions for row {row}")
                
            except Exception as e:
                print(f"❌ Error creating actions for row {row}: {e}")
                # Create a simple fallback widget
                fallback_widget = QWidget()
                fallback_layout = QHBoxLayout(fallback_widget)
                fallback_layout.addWidget(QLabel("Error"))
                self.table_widget.setCellWidget(row, 7, fallback_widget)
        
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
        """Save application settings"""
        settings_file = self.project_folder / "settings.json"
        try:
            with open(settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            QMessageBox.critical(self, "Settings Error", f"Could not save settings: {e}")
            
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
            # Create backup of problematic file
            backup_path = FileEncodingHelper.create_backup(
                wreaths_file, 
                self.project_folder / "encoding_backups"
            )
            
            error_detail = f"Could not read wreaths.json file:\n{error_msg}"
            if backup_path:
                error_detail += f"\n\nA backup has been created at:\n{backup_path}"
            
            QMessageBox.critical(self, "File Reading Error", error_detail)
            self.wreaths_data = []
            
    def save_wreaths(self):
        """Save wreaths to JSON file"""
        wreaths_file = self.project_folder / "wreaths.json"
        
        # Create backup first
        if self.settings.get('auto_backup', True) and wreaths_file.exists():
            self.create_backup()
        
        try:
            with open(wreaths_file, 'w') as f:
                json.dump(self.wreaths_data, f, indent=2)
            
            self.changes_made = False
            self.save_btn.setEnabled(False)
            self.changes_label.setText("")
            self.update_status()
            
            QMessageBox.information(self, "Save Complete", "Wreaths saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Could not save wreaths: {e}")
            
    def create_backup(self):
        """Create a backup of the current wreaths file"""
        wreaths_file = self.project_folder / "wreaths.json"
        if wreaths_file.exists():
            backup_dir = self.project_folder / "backups"
            FileEncodingHelper.create_backup(wreaths_file, backup_dir)
            
            # Clean old backups
            self.clean_old_backups()
            
    def clean_old_backups(self):
        """Remove old backup files beyond the limit"""
        backup_dir = self.project_folder / "backups"
        if not backup_dir.exists():
            return
            
        backup_limit = self.settings.get('backup_count', 10)
        backup_files = list(backup_dir.glob("wreaths_*.json"))
        backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Remove old backups
        for old_backup in backup_files[backup_limit:]:
            try:
                old_backup.unlink()
            except Exception:
                pass  # Ignore deletion errors
                
    def mark_changes_made(self):
        """Mark that changes have been made"""
        if not self.changes_made:
            self.changes_made = True
            self.save_btn.setEnabled(True)
            self.changes_label.setText("● Unsaved changes")
            self.changes_label.setStyleSheet("color: #dc2626; font-weight: bold;")
            
    def add_new_wreath(self):
        """Add a new wreath"""
        dialog = WreathEditorDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            new_wreath = dialog.get_wreath_data()
            self.wreaths_data.append(new_wreath)
            self.populate_table()
            self.mark_changes_made()
            
    def edit_wreath(self, row):
        """Edit an existing wreath"""
        if row >= len(self.wreaths_data):
            return
            
        wreath = self.wreaths_data[row]
        dialog = WreathEditorDialog(wreath, self)
        if dialog.exec() == QDialog.Accepted:
            updated_wreath = dialog.get_wreath_data()
            self.wreaths_data[row] = updated_wreath
            self.populate_table()
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
    
    # File: python-admin/main_pyside.py
# Replace the entire repopulate_after_sort method

def repopulate_after_sort(self):
    """Repopulate table after sorting to sync widgets with sorted items"""
    print("🔄 repopulate_after_sort called!")
    
    try:
        # Get current sort order by reading the table items
        sorted_wreaths = []
        row_count = self.table_widget.rowCount()
        print(f"🔄 Table has {row_count} rows to reorder")
        
        for row in range(row_count):
            title_item = self.table_widget.item(row, 1)  # Title column
            if title_item and hasattr(title_item, 'original_title'):
                original_title = title_item.original_title
                print(f"🔄 Row {row}: Looking for wreath with title '{original_title}'")
                
                # Find matching wreath by title
                for wreath in self.wreaths_data:
                    if wreath.get('title', 'Untitled') == original_title:
                        sorted_wreaths.append(wreath)
                        print(f"✓ Found matching wreath for row {row}")
                        break
                else:
                    print(f"❌ No matching wreath found for '{original_title}'")
            else:
                print(f"❌ Row {row}: No title item or no original_title attribute")
        
        print(f"🔄 Found {len(sorted_wreaths)} sorted wreaths vs {len(self.wreaths_data)} original")
        
        # Update wreaths_data to match sort order
        if len(sorted_wreaths) == len(self.wreaths_data):
            print("✓ Updating wreaths_data order to match sort")
            self.wreaths_data = sorted_wreaths
        else:
            print("❌ Count mismatch - keeping original order")
            
        # Temporarily disable sorting to prevent recursion
        print("🔄 Disabling sorting temporarily...")
        self.table_widget.setSortingEnabled(False)
        
        # Repopulate with correct order
        print("🔄 Repopulating table...")
        self.populate_table()
        
        # Re-enable sorting
        print("🔄 Re-enabling sorting...")
        self.table_widget.setSortingEnabled(True)
        print("✓ repopulate_after_sort completed successfully")
        
    except Exception as e:
        print(f"❌ Error in repopulate_after_sort: {e}")
        print(f"❌ Exception type: {type(e)}")
        import traceback
        traceback.print_exc()
        
        # Fallback: just repopulate normally
        print("🔄 Falling back to normal populate_table()")
        self.populate_table()

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
            
    def import_json_files(self):
        """Import JSON files with robust encoding handling"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, 'Import JSON Files', 
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
                # Handle different data structures
                wreaths_to_add = []
                
                if isinstance(data, list):
                    # List of wreaths
                    wreaths_to_add = [w for w in data if self.validate_wreath_data(w)]
                elif isinstance(data, dict):
                    # Single wreath or object containing wreaths
                    if self.validate_wreath_data(data):
                        wreaths_to_add = [data]
                    elif 'wreaths' in data and isinstance(data['wreaths'], list):
                        wreaths_to_add = [w for w in data['wreaths'] if self.validate_wreath_data(w)]
                
                # Process and add wreaths
                for wreath in wreaths_to_add:
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
                error_files.append(f"{Path(file_path).name}: {error_msg}")
        
        # Show results
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
                
                # Clean up the temporary flags
                new_settings.pop('folder_changed', None)
                new_settings.pop('old_folder', None)
                new_settings.pop('new_folder', None)
            
            self.settings = new_settings
            self.save_settings()
            
    def deploy_to_netlify(self):
        """Deploy wreaths to Netlify"""
        if not self.settings.get('netlify_site_id') or not self.settings.get('netlify_access_token'):
            QMessageBox.warning(
                self, "Deploy Error", 
                "Please configure your Netlify settings first.\nGo to Edit → Settings..."
            )
            return
            
        # Save first if there are changes
        if self.changes_made:
            reply = QMessageBox.question(
                self, 'Save Changes',
                'You have unsaved changes. Save before deploying?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Yes
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.save_wreaths()
            elif reply == QMessageBox.StandardButton.Cancel:
                return
                
        # Start deployment
        deploy_manager = DeployManager(self.settings, self.wreaths_data, self)
        deploy_manager.deploy()
        
    def closeEvent(self, event):
        """Handle application close event"""
        if self.changes_made:
            reply = QMessageBox.question(
                self, 'Unsaved Changes',
                'You have unsaved changes. Save before closing?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Yes
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.save_wreaths()
                event.accept()
            elif reply == QMessageBox.StandardButton.No:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Twinfolks Wreath Manager")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Twinfolks Door Decor")
    
    # Create and show main window
    window = TwinfolksWreathManager()
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()