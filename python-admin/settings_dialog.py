# File: python-admin/settings_dialog.py
# Settings dialog for Netlify configuration and app preferences

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QDialogButtonBox, QTabWidget,
                            QWidget, QCheckBox, QSpinBox, QTextEdit, QGroupBox,
                            QGridLayout, QMessageBox, QFrame, QComboBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap, QPainter, QIcon

class SettingsDialog(QDialog):
    """Settings dialog for application configuration"""
    
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings.copy()  # Work with a copy
        
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.resize(500, 400)
        
        self.init_ui()
        self.populate_settings()
        
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Netlify tab
        self.create_netlify_tab()
        
        # General tab  
        self.create_general_tab()
        
        # About tab
        self.create_about_tab()
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept_settings)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def create_netlify_tab(self):
        """Create Netlify configuration tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Instructions
        instructions = QLabel(
            "🌐 Configure your Netlify deployment settings to automatically upload changes to your live website."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("padding: 10px; background-color: #e0f2fe; border-radius: 4px; margin-bottom: 10px;")
        layout.addWidget(instructions)
        
        # Netlify settings group
        netlify_group = QGroupBox("Netlify Configuration")
        netlify_layout = QGridLayout(netlify_group)
        
        # Site ID
        netlify_layout.addWidget(QLabel("Site ID:"), 0, 0)
        self.site_id_edit = QLineEdit()
        self.site_id_edit.setPlaceholderText("e.g., 12345678-1234-1234-1234-123456789abc")
        netlify_layout.addWidget(self.site_id_edit, 0, 1)
        
        site_id_help = QPushButton("?")
        site_id_help.setMaximumWidth(25)
        site_id_help.clicked.connect(self.show_site_id_help)
        netlify_layout.addWidget(site_id_help, 0, 2)
        
        # Access Token
        netlify_layout.addWidget(QLabel("Access Token:"), 1, 0)
        self.access_token_edit = QLineEdit()
        self.access_token_edit.setPlaceholderText("Your Netlify personal access token")
        self.access_token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        netlify_layout.addWidget(self.access_token_edit, 1, 1)
        
        token_help = QPushButton("?")
        token_help.setMaximumWidth(25)
        token_help.clicked.connect(self.show_token_help)
        netlify_layout.addWidget(token_help, 1, 2)
        
        # Show/Hide token button
        self.toggle_token_btn = QPushButton("Show")
        self.toggle_token_btn.setMaximumWidth(60)
        self.toggle_token_btn.clicked.connect(self.toggle_token_visibility)
        netlify_layout.addWidget(self.toggle_token_btn, 1, 3)
        
        # Test connection button
        self.test_connection_btn = QPushButton("Test Connection")
        self.test_connection_btn.clicked.connect(self.test_netlify_connection)
        netlify_layout.addWidget(self.test_connection_btn, 2, 0, 1, 4)
        
        layout.addWidget(netlify_group)
        
        # Setup instructions
        setup_group = QGroupBox("Setup Instructions")
        setup_layout = QVBoxLayout(setup_group)
        
        instructions_text = QTextEdit()
        instructions_text.setMaximumHeight(150)
        instructions_text.setReadOnly(True)
        instructions_text.setHtml("""
        <div style="font-size: 12px; line-height: 1.4;">
        <b>📋 How to get your Netlify credentials:</b><br><br>
        
        <b>1. Site ID:</b><br>
        • Go to your Netlify dashboard<br>
        • Click on your site<br>
        • Go to Settings → General<br>
        • Copy the "Site ID" (under Site details)<br><br>
        
        <b>2. Access Token:</b><br>
        • Go to User Settings → Applications<br>
        • Click "New access token"<br>
        • Give it a description like "Twinfolks Wreath Manager"<br>
        • Copy the generated token<br><br>
        
        <b>🔒 Security:</b> Your credentials are stored locally and never shared.
        </div>
        """)
        setup_layout.addWidget(instructions_text)
        
        layout.addWidget(setup_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Netlify")
        
    def create_general_tab(self):
        """Create general settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Backup settings
        backup_group = QGroupBox("Backup Settings")
        backup_layout = QGridLayout(backup_group)
        
        # Auto-backup checkbox
        self.auto_backup_cb = QCheckBox("Automatically backup before saving changes")
        self.auto_backup_cb.setChecked(True)
        backup_layout.addWidget(self.auto_backup_cb, 0, 0, 1, 2)
        
        # Backup count
        backup_layout.addWidget(QLabel("Keep this many backups:"), 1, 0)
        self.backup_count_spin = QSpinBox()
        self.backup_count_spin.setRange(1, 50)
        self.backup_count_spin.setValue(10)
        backup_layout.addWidget(self.backup_count_spin, 1, 1)
        
        layout.addWidget(backup_group)
        
        # Display settings
        display_group = QGroupBox("Display Settings")
        display_layout = QGridLayout(display_group)
        
        # Table row height
        display_layout.addWidget(QLabel("Table row height:"), 0, 0)
        self.row_height_spin = QSpinBox()
        self.row_height_spin.setRange(40, 120)
        self.row_height_spin.setValue(60)
        self.row_height_spin.setSuffix(" px")
        display_layout.addWidget(self.row_height_spin, 0, 1)
        
        # Image thumbnail size
        display_layout.addWidget(QLabel("Thumbnail size:"), 1, 0)
        self.thumbnail_size_spin = QSpinBox()
        self.thumbnail_size_spin.setRange(40, 100)
        self.thumbnail_size_spin.setValue(60)
        self.thumbnail_size_spin.setSuffix(" px")
        display_layout.addWidget(self.thumbnail_size_spin, 1, 1)
        
        layout.addWidget(display_group)
        
        # Import/Export settings
        import_group = QGroupBox("Import/Export Settings")
        import_layout = QGridLayout(import_group)
        
        # Auto-scan imports folder
        self.auto_scan_imports_cb = QCheckBox("Automatically scan imports folder on startup")
        self.auto_scan_imports_cb.setChecked(True)
        import_layout.addWidget(self.auto_scan_imports_cb, 0, 0, 1, 2)
        
        # Confirm before importing
        self.confirm_import_cb = QCheckBox("Confirm before importing files")
        self.confirm_import_cb.setChecked(True)
        import_layout.addWidget(self.confirm_import_cb, 1, 0, 1, 2)
        
        layout.addWidget(import_group)
        
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "General")
        
    def create_about_tab(self):
        """Create about tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # App info
        app_info = QLabel()
        app_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        app_info.setStyleSheet("padding: 20px;")
        app_info.setHtml("""
        <div style="text-align: center; font-size: 14px;">
        <h2 style="color: #059669;">🎄 Twinfolks Wreath Manager</h2>
        <p><b>Version:</b> 1.0.0</p>
        <p><b>Built for:</b> Twinfolks Door Decor</p>
        <br>
        <p style="color: #666;">A complete wreath management system for<br>
        beautiful handcrafted wreaths.</p>
        <br>
        <p><b>Features:</b></p>
        <ul style="text-align: left; display: inline-block;">
        <li>✅ Spreadsheet-like wreath management</li>
        <li>🖼️ Drag-and-drop image organization</li>
        <li>🏷️ Smart hashtag system</li>
        <li>🚀 One-click Netlify deployment</li>
        <li>💾 Automatic backups</li>
        <li>📱 User-friendly interface</li>
        </ul>
        <br>
        <p style="color: #666; font-size: 12px;">
        Built with ❤️ using Python and PyQt6<br>
        Data stored locally in your Documents folder
        </p>
        </div>
        """)
        layout.addWidget(app_info)
        
        # Project folder info
        folder_group = QGroupBox("Project Folder")
        folder_layout = QVBoxLayout(folder_group)
        
        from pathlib import Path
        project_folder = Path.home() / "Documents" / "Twinfolks_Wreaths"
        
        folder_info = QLabel(f"📁 Project folder: {project_folder}")
        folder_info.setStyleSheet("font-family: monospace; font-size: 11px; padding: 5px;")
        folder_layout.addWidget(folder_info)
        
        folder_buttons = QHBoxLayout()
        
        open_folder_btn = QPushButton("Open Project Folder")
        open_folder_btn.clicked.connect(self.open_project_folder)
        folder_buttons.addWidget(open_folder_btn)
        
        folder_buttons.addStretch()
        folder_layout.addLayout(folder_buttons)
        
        layout.addWidget(folder_group)
        
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "About")
        
    def populate_settings(self):
        """Populate settings fields with current values"""
        # Netlify settings
        self.site_id_edit.setText(self.settings.get('netlify_site_id', ''))
        self.access_token_edit.setText(self.settings.get('netlify_access_token', ''))
        
        # General settings
        self.auto_backup_cb.setChecked(self.settings.get('auto_backup', True))
        self.backup_count_spin.setValue(self.settings.get('backup_count', 10))
        self.row_height_spin.setValue(self.settings.get('row_height', 60))
        self.thumbnail_size_spin.setValue(self.settings.get('thumbnail_size', 60))
        self.auto_scan_imports_cb.setChecked(self.settings.get('auto_scan_imports', True))
        self.confirm_import_cb.setChecked(self.settings.get('confirm_import', True))
        
    def show_site_id_help(self):
        """Show Site ID help dialog"""
        QMessageBox.information(
            self, "Site ID Help",
            "Your Netlify Site ID can be found in your site's settings:\n\n"
            "1. Go to your Netlify dashboard\n"
            "2. Click on your site\n"
            "3. Go to Settings → General\n"
            "4. Copy the 'Site ID' under 'Site details'\n\n"
            "It looks like: 12345678-1234-1234-1234-123456789abc"
        )
        
    def show_token_help(self):
        """Show Access Token help dialog"""
        QMessageBox.information(
            self, "Access Token Help",
            "To create a Netlify Access Token:\n\n"
            "1. Go to User Settings → Applications\n"
            "2. Click 'New access token'\n"
            "3. Give it a description like 'Twinfolks Wreath Manager'\n"
            "4. Copy the generated token\n\n"
            "⚠️ Important: Save this token securely - Netlify only shows it once!"
        )
        
    def toggle_token_visibility(self):
        """Toggle access token visibility"""
        if self.access_token_edit.echoMode() == QLineEdit.EchoMode.Password:
            self.access_token_edit.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_token_btn.setText("Hide")
        else:
            self.access_token_edit.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_token_btn.setText("Show")
            
    def test_netlify_connection(self):
        """Test Netlify connection"""
        site_id = self.site_id_edit.text().strip()
        access_token = self.access_token_edit.text().strip()
        
        if not site_id or not access_token:
            QMessageBox.warning(
                self, "Missing Information",
                "Please enter both Site ID and Access Token before testing."
            )
            return
            
        # Test the connection
        try:
            import requests
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f'https://api.netlify.com/api/v1/sites/{site_id}',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                site_data = response.json()
                site_name = site_data.get('name', 'Unknown')
                site_url = site_data.get('url', 'Unknown')
                
                QMessageBox.information(
                    self, "Connection Successful! ✅",
                    f"Successfully connected to Netlify!\n\n"
                    f"Site: {site_name}\n"
                    f"URL: {site_url}\n\n"
                    f"You can now deploy wreaths to your website."
                )
            else:
                QMessageBox.critical(
                    self, "Connection Failed ❌",
                    f"Failed to connect to Netlify.\n\n"
                    f"Error {response.status_code}: {response.text[:200]}\n\n"
                    f"Please check your Site ID and Access Token."
                )
                
        except requests.exceptions.Timeout:
            QMessageBox.critical(
                self, "Connection Timeout",
                "Connection to Netlify timed out.\n\n"
                "Please check your internet connection and try again."
            )
        except Exception as e:
            QMessageBox.critical(
                self, "Connection Error",
                f"Error connecting to Netlify:\n\n{str(e)}"
            )
            
    def open_project_folder(self):
        """Open the project folder in file explorer"""
        from pathlib import Path
        import os
        import sys
        
        project_folder = Path.home() / "Documents" / "Twinfolks_Wreaths"
        
        try:
            if sys.platform == "win32":
                os.startfile(project_folder)
            elif sys.platform == "darwin":  # macOS
                os.system(f"open '{project_folder}'")
            else:  # Linux
                os.system(f"xdg-open '{project_folder}'")
        except Exception as e:
            QMessageBox.warning(
                self, "Cannot Open Folder",
                f"Could not open project folder:\n{e}\n\n"
                f"Folder location: {project_folder}"
            )
            
    def accept_settings(self):
        """Accept and save settings"""
        # Update settings dictionary
        self.settings['netlify_site_id'] = self.site_id_edit.text().strip()
        self.settings['netlify_access_token'] = self.access_token_edit.text().strip()
        self.settings['auto_backup'] = self.auto_backup_cb.isChecked()
        self.settings['backup_count'] = self.backup_count_spin.value()
        self.settings['row_height'] = self.row_height_spin.value()
        self.settings['thumbnail_size'] = self.thumbnail_size_spin.value()
        self.settings['auto_scan_imports'] = self.auto_scan_imports_cb.isChecked()
        self.settings['confirm_import'] = self.confirm_import_cb.isChecked()
        
        self.accept()
        
    def get_settings(self):
        """Get the updated settings"""
        return self.settings

# For testing the dialog standalone
if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Test with sample settings
    test_settings = {
        'netlify_site_id': '',
        'netlify_access_token': '',
        'auto_backup': True,
        'backup_count': 10,
        'row_height': 60,
        'thumbnail_size': 60,
        'auto_scan_imports': True,
        'confirm_import': True
    }
    
    dialog = SettingsDialog(test_settings)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        print("Updated settings:", dialog.get_settings())
    
    sys.exit(app.exec())