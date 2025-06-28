# File: python-admin/main.py
# Twinfolks Door Decor - Wreath Management System
# Main application entry point

import sys
import os
import json
import requests
from pathlib import Path
from datetime import datetime
import shutil
import uuid

from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                            QWidget, QPushButton, QTableWidget, QTableWidgetItem, 
                            QHeaderView, QLabel, QLineEdit, QCheckBox, QSpinBox,
                            QTextEdit, QDialog, QDialogButtonBox, QFileDialog,
                            QMessageBox, QProgressBar, QStatusBar, QMenuBar,
                            QMenu, QSplitter, QGroupBox, QGridLayout, QComboBox,
                            QTabWidget, QAbstractItemView)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QPixmap, QIcon, QAction, QFont, QColor, QPalette

from image_viewer import ImageViewerDialog
from settings_dialog import SettingsDialog
from wreath_editor import WreathEditorDialog
from deploy_manager import DeployManager

class WreathTableWidget(QTableWidget):
    """Custom table widget with enhanced functionality"""
    
    def __init__(self):
        super().__init__()
        self.setup_table()
        
    def setup_table(self):
        # Set up columns
        self.setColumnCount(7)
        headers = ['Image', 'Title', 'Sold', 'Featured', 'Price', 'Hashtags', 'Actions']
        self.setHorizontalHeaderLabels(headers)
        
        # Configure table appearance
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSortingEnabled(True)
        
        # Set column widths
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # Image
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Title
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)   # Sold
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)   # Featured
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)   # Price
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch) # Hashtags
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)   # Actions
        
        self.setColumnWidth(0, 80)   # Image thumbnail
        self.setColumnWidth(2, 60)   # Sold checkbox
        self.setColumnWidth(3, 80)   # Featured checkbox
        self.setColumnWidth(4, 80)   # Price
        self.setColumnWidth(6, 120)  # Actions
        
        # Set row height
        self.verticalHeader().setDefaultSectionSize(60)

class ImageThumbnailWidget(QLabel):
    """Widget for displaying image thumbnails"""
    
    def __init__(self, image_url=None):
        super().__init__()
        self.image_url = image_url
        self.setFixedSize(60, 60)
        self.setScaledContents(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: #f8f9fa;
            }
        """)
        
        if image_url:
            self.load_image()
        else:
            self.setText("No Image")
            
    def load_image(self):
        """Load image from URL"""
        try:
            # For now, just show placeholder
            self.setText("🖼️")
        except Exception:
            self.setText("❌")

class TwinfolksWreathManager(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.wreaths_data = []
        self.changes_made = False
        self.settings = {}
        
        # Set up project folder
        self.project_folder = self.get_project_folder()
        self.ensure_project_structure()
        
        # Load data
        self.load_settings()
        self.load_wreaths()
        
        self.init_ui()
        self.populate_table()
        
    def get_project_folder(self):
        """Get the project folder path"""
        home = Path.home()
        return home / "Documents" / "Twinfolks_Wreaths"
    
    def ensure_project_structure(self):
        """Create project folder structure"""
        folders = [
            self.project_folder,
            self.project_folder / "backups",
            self.project_folder / "imports",
            self.project_folder / "exports"
        ]
        
        for folder in folders:
            folder.mkdir(parents=True, exist_ok=True)
        
        # Create welcome file if this is first time
        welcome_file = self.project_folder / "WELCOME.txt"
        if not welcome_file.exists():
            welcome_content = """
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
            """.strip()
            
            with open(welcome_file, 'w') as f:
                f.write(welcome_content)
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Twinfolks Wreath Manager")
        self.setGeometry(100, 100, 1200, 800)
        
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
        
        deploy_action = QAction('Deploy to Netlify', self)
        deploy_action.setShortcut('Ctrl+D')
        deploy_action.triggered.connect(self.deploy_to_netlify)
        deploy_menu.addAction(deploy_action)
        
    def create_toolbar(self, layout):
        """Create the toolbar with common actions"""
        toolbar_layout = QHBoxLayout()
        
        # Add New Wreath button
        self.add_btn = QPushButton("Add New Wreath")
        self.add_btn.setStyleSheet("QPushButton { background-color: #10b981; color: white; padding: 8px 16px; border-radius: 4px; }")
        self.add_btn.clicked.connect(self.add_new_wreath)
        toolbar_layout.addWidget(self.add_btn)
        
        # Import JSON button
        self.import_btn = QPushButton("Import JSON Files")
        self.import_btn.setStyleSheet("QPushButton { background-color: #3b82f6; color: white; padding: 8px 16px; border-radius: 4px; }")
        self.import_btn.clicked.connect(self.import_json_files)
        toolbar_layout.addWidget(self.import_btn)
        
        # Save button
        self.save_btn = QPushButton("Save Changes")
        self.save_btn.setStyleSheet("QPushButton { background-color: #f59e0b; color: white; padding: 8px 16px; border-radius: 4px; }")
        self.save_btn.clicked.connect(self.save_wreaths)
        self.save_btn.setEnabled(False)
        toolbar_layout.addWidget(self.save_btn)
        
        # Deploy button
        self.deploy_btn = QPushButton("Deploy to Website")
        self.deploy_btn.setStyleSheet("QPushButton { background-color: #8b5cf6; color: white; padding: 8px 16px; border-radius: 4px; }")
        self.deploy_btn.clicked.connect(self.deploy_to_netlify)
        toolbar_layout.addWidget(self.deploy_btn)
        
        # Spacer
        toolbar_layout.addStretch()
        
        # Search box
        search_label = QLabel("Search:")
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search wreaths...")
        self.search_box.textChanged.connect(self.filter_wreaths)
        toolbar_layout.addWidget(search_label)
        toolbar_layout.addWidget(self.search_box)
        
        # Filter by sold status
        self.sold_filter = QComboBox()
        self.sold_filter.addItems(["All Wreaths", "Available Only", "Sold Only"])
        self.sold_filter.currentTextChanged.connect(self.filter_wreaths)
        toolbar_layout.addWidget(self.sold_filter)
        
        # Filter by featured status
        self.featured_filter = QComboBox()
        self.featured_filter.addItems(["All", "Featured Only", "Not Featured"])
        self.featured_filter.currentTextChanged.connect(self.filter_wreaths)
        toolbar_layout.addWidget(self.featured_filter)
        
        layout.addLayout(toolbar_layout)
        
    def create_main_table(self, layout):
        """Create the main wreaths table"""
        self.table = WreathTableWidget()
        self.table.cellChanged.connect(self.on_cell_changed)
        layout.addWidget(self.table)
        
    def create_status_bar(self):
        """Create the status bar"""
        self.status_bar = self.statusBar()
        self.wreath_count_label = QLabel()
        self.changes_label = QLabel()
        
        self.status_bar.addWidget(self.wreath_count_label)
        self.status_bar.addPermanentWidget(self.changes_label)
        
    def load_settings(self):
        """Load application settings"""
        settings_file = self.project_folder / "settings.json"
        try:
            if settings_file.exists():
                with open(settings_file, 'r') as f:
                    self.settings = json.load(f)
            else:
                self.settings = {
                    'netlify_site_id': '',
                    'netlify_access_token': '',
                    'auto_backup': True,
                    'backup_count': 10
                }
        except Exception as e:
            print(f"Error loading settings: {e}")
            self.settings = {}
            
    def save_settings(self):
        """Save application settings"""
        settings_file = self.project_folder / "settings.json"
        try:
            with open(settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            QMessageBox.critical(self, "Settings Error", f"Could not save settings: {e}")
            
    def load_wreaths(self):
        """Load wreaths from JSON file"""
        wreaths_file = self.project_folder / "wreaths.json"
        try:
            if wreaths_file.exists():
                with open(wreaths_file, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.wreaths_data = data
                    else:
                        self.wreaths_data = []
                        
                # Ensure all wreaths have required fields
                for wreath in self.wreaths_data:
                    if 'featured' not in wreath:
                        wreath['featured'] = False
                    if 'id' not in wreath:
                        wreath['id'] = str(uuid.uuid4())
                        
            else:
                self.wreaths_data = []
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Could not load wreaths: {e}")
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
        backup_folder = self.project_folder / "backups"
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = backup_folder / f"wreaths_backup_{timestamp}.json"
        
        try:
            shutil.copy2(wreaths_file, backup_file)
            
            # Clean up old backups
            backup_count = self.settings.get('backup_count', 10)
            backup_files = sorted(backup_folder.glob("wreaths_backup_*.json"))
            
            if len(backup_files) > backup_count:
                for old_backup in backup_files[:-backup_count]:
                    old_backup.unlink()
                    
        except Exception as e:
            print(f"Backup error: {e}")
            
    def populate_table(self):
        """Populate the table with wreath data"""
        self.table.setSortingEnabled(False)  # Disable during population
        
        self.table.setRowCount(len(self.wreaths_data))
        
        for row, wreath in enumerate(self.wreaths_data):
            # Image thumbnail
            image_widget = ImageThumbnailWidget(
                wreath.get('images', [None])[0] if wreath.get('images') else None
            )
            self.table.setCellWidget(row, 0, image_widget)
            
            # Title
            title_item = QTableWidgetItem(wreath.get('title', ''))
            self.table.setItem(row, 1, title_item)
            
            # Sold checkbox
            sold_widget = QCheckBox()
            sold_widget.setChecked(wreath.get('sold', False))
            sold_widget.stateChanged.connect(lambda state, r=row: self.on_sold_changed(r, state))
            sold_widget.setStyleSheet("QCheckBox { margin: auto; }")
            self.table.setCellWidget(row, 2, sold_widget)
            
            # Featured checkbox
            featured_widget = QCheckBox()
            featured_widget.setChecked(wreath.get('featured', False))
            featured_widget.stateChanged.connect(lambda state, r=row: self.on_featured_changed(r, state))
            featured_widget.setStyleSheet("QCheckBox { margin: auto; }")
            self.table.setCellWidget(row, 3, featured_widget)
            
            # Price
            price = wreath.get('localPrice', 0)
            price_item = QTableWidgetItem(f"${price:.2f}")
            self.table.setItem(row, 4, price_item)
            
            # Hashtags
            hashtags = wreath.get('hashtags', [])
            hashtags_text = ' '.join([f"#{tag}" for tag in hashtags[:5]])  # Show first 5
            if len(hashtags) > 5:
                hashtags_text += f" (+{len(hashtags) - 5} more)"
            hashtags_item = QTableWidgetItem(hashtags_text)
            self.table.setItem(row, 5, hashtags_item)
            
            # Actions
            actions_widget = self.create_actions_widget(row)
            self.table.setCellWidget(row, 6, actions_widget)
            
        self.table.setSortingEnabled(True)  # Re-enable sorting
        self.update_status()
        
    def create_actions_widget(self, row):
        """Create action buttons for a row"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        
        # Edit button
        edit_btn = QPushButton("Edit")
        edit_btn.setMaximumWidth(40)
        edit_btn.clicked.connect(lambda: self.edit_wreath(row))
        layout.addWidget(edit_btn)
        
        # View Images button
        images_btn = QPushButton("📷")
        images_btn.setMaximumWidth(30)
        images_btn.clicked.connect(lambda: self.view_images(row))
        layout.addWidget(images_btn)
        
        # Delete button
        delete_btn = QPushButton("🗑️")
        delete_btn.setMaximumWidth(30)
        delete_btn.setStyleSheet("QPushButton { color: #dc2626; }")
        delete_btn.clicked.connect(lambda: self.delete_wreath(row))
        layout.addWidget(delete_btn)
        
        return widget
        
    def on_sold_changed(self, row, state):
        """Handle sold checkbox change"""
        if row < len(self.wreaths_data):
            self.wreaths_data[row]['sold'] = (state == Qt.CheckState.Checked.value)
            self.mark_changes_made()
            
    def on_featured_changed(self, row, state):
        """Handle featured checkbox change"""
        if row < len(self.wreaths_data):
            self.wreaths_data[row]['featured'] = (state == Qt.CheckState.Checked.value)
            self.mark_changes_made()
            
    def on_cell_changed(self, row, column):
        """Handle cell value changes"""
        if row >= len(self.wreaths_data):
            return
            
        item = self.table.item(row, column)
        if not item:
            return
            
        # Handle title changes
        if column == 1:  # Title column
            self.wreaths_data[row]['title'] = item.text()
            self.mark_changes_made()
            
        # Handle price changes
        elif column == 4:  # Price column
            try:
                price_text = item.text().replace('$', '').replace(',', '')
                price = float(price_text)
                self.wreaths_data[row]['localPrice'] = price
                item.setText(f"${price:.2f}")
                self.mark_changes_made()
            except ValueError:
                # Revert to original value
                original_price = self.wreaths_data[row].get('localPrice', 0)
                item.setText(f"${original_price:.2f}")
                
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
        if dialog.exec() == QDialog.DialogCode.Accepted:
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
        if dialog.exec() == QDialog.DialogCode.Accepted:
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
        
        dialog = ImageViewerDialog(images, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_images = dialog.get_images()
            self.wreaths_data[row]['images'] = updated_images
            self.populate_table()
            self.mark_changes_made()
            
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
            self.wreaths_data.pop(row)
            self.populate_table()
            self.mark_changes_made()
            
    def filter_wreaths(self):
        """Filter wreaths based on search and filters"""
        search_text = self.search_box.text().lower()
        sold_filter = self.sold_filter.currentText()
        featured_filter = self.featured_filter.currentText()
        
        for row in range(self.table.rowCount()):
            show_row = True
            
            # Search filter
            if search_text:
                if row < len(self.wreaths_data):
                    wreath = self.wreaths_data[row]
                    title = wreath.get('title', '').lower()
                    description = wreath.get('description', '').lower()
                    hashtags = ' '.join(wreath.get('hashtags', [])).lower()
                    
                    if not (search_text in title or search_text in description or search_text in hashtags):
                        show_row = False
                        
            # Sold filter
            if show_row and sold_filter != "All Wreaths":
                if row < len(self.wreaths_data):
                    wreath = self.wreaths_data[row]
                    is_sold = wreath.get('sold', False)
                    
                    if sold_filter == "Available Only" and is_sold:
                        show_row = False
                    elif sold_filter == "Sold Only" and not is_sold:
                        show_row = False
                        
            # Featured filter
            if show_row and featured_filter != "All":
                if row < len(self.wreaths_data):
                    wreath = self.wreaths_data[row]
                    is_featured = wreath.get('featured', False)
                    
                    if featured_filter == "Featured Only" and not is_featured:
                        show_row = False
                    elif featured_filter == "Not Featured" and is_featured:
                        show_row = False
                        
            self.table.setRowHidden(row, not show_row)
            
    def update_status(self):
        """Update status bar"""
        total_wreaths = len(self.wreaths_data)
        available_wreaths = len([w for w in self.wreaths_data if not w.get('sold', False)])
        featured_wreaths = len([w for w in self.wreaths_data if w.get('featured', False)])
        
        status_text = f"Total: {total_wreaths} | Available: {available_wreaths} | Featured: {featured_wreaths}"
        self.wreath_count_label.setText(status_text)
        
    def import_json_files(self):
        """Import JSON files from imports folder or file dialog"""
        imports_folder = self.project_folder / "imports"
        json_files = list(imports_folder.glob("*.json"))
        
        if json_files:
            # Show files found in imports folder
            file_list = '\n'.join([f.name for f in json_files])
            reply = QMessageBox.question(
                self, 'Import JSON Files',
                f'Found {len(json_files)} JSON files in imports folder:\n\n{file_list}\n\nImport these files?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.process_import_files(json_files)
        else:
            # No files in imports folder, open file dialog
            files, _ = QFileDialog.getOpenFileNames(
                self, 'Import JSON Files',
                str(self.project_folder),
                'JSON Files (*.json)'
            )
            
            if files:
                file_paths = [Path(f) for f in files]
                self.process_import_files(file_paths)
                
    def process_import_files(self, file_paths):
        """Process imported JSON files"""
        imported_count = 0
        
        for file_path in file_paths:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    
                if isinstance(data, list):
                    # List of wreaths
                    for wreath in data:
                        if self.validate_wreath_data(wreath):
                            # Ensure required fields
                            if 'id' not in wreath:
                                wreath['id'] = str(uuid.uuid4())
                            if 'featured' not in wreath:
                                wreath['featured'] = False
                                
                            self.wreaths_data.append(wreath)
                            imported_count += 1
                            
                elif isinstance(data, dict):
                    # Single wreath
                    if self.validate_wreath_data(data):
                        if 'id' not in data:
                            data['id'] = str(uuid.uuid4())
                        if 'featured' not in data:
                            data['featured'] = False
                            
                        self.wreaths_data.append(data)
                        imported_count += 1
                        
            except Exception as e:
                QMessageBox.warning(self, "Import Error", f"Could not import {file_path.name}: {e}")
                
        if imported_count > 0:
            self.populate_table()
            self.mark_changes_made()
            QMessageBox.information(self, "Import Complete", f"Imported {imported_count} wreaths!")
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
        """Open settings dialog"""
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.settings = dialog.get_settings()
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