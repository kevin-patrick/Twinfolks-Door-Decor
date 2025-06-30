# File: python-admin/settings_dialog_pyside.py
# Updated settings dialog with project folder location browse button

from pathlib import Path
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, 
                            QLineEdit, QDialogButtonBox, QGroupBox,
                            QGridLayout, QCheckBox, QSpinBox, QPushButton,
                            QHBoxLayout, QFileDialog, QMessageBox)
from PySide6.QtCore import Qt

class SettingsDialog(QDialog):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings.copy()
        self.parent_app = parent
        
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.resize(500, 400)
        
        self.init_ui()
        self.populate_settings()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Project folder settings
        folder_group = QGroupBox("Project Folder Location")
        folder_layout = QGridLayout(folder_group)
        
        folder_layout.addWidget(QLabel("Project Folder:"), 0, 0)
        
        # Folder path display and browse button
        folder_row = QHBoxLayout()
        self.folder_path_edit = QLineEdit()
        self.folder_path_edit.setReadOnly(True)
        self.folder_path_edit.setToolTip("Current project folder location")
        folder_row.addWidget(self.folder_path_edit)
        
        self.browse_folder_btn = QPushButton("Browse...")
        self.browse_folder_btn.clicked.connect(self.browse_project_folder)
        self.browse_folder_btn.setToolTip("Choose a different project folder location")
        folder_row.addWidget(self.browse_folder_btn)
        
        folder_layout.addLayout(folder_row, 0, 1)
        
        # Info label
        info_label = QLabel("This folder contains your wreaths.json, settings, and backups.\n"
                           "Choose a location that's easy for you to access and backup.")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; font-size: 10px;")
        folder_layout.addWidget(info_label, 1, 0, 1, 2)
        
        layout.addWidget(folder_group)
        
        # Netlify settings
        netlify_group = QGroupBox("Netlify Configuration")
        netlify_layout = QGridLayout(netlify_group)
        
        netlify_layout.addWidget(QLabel("Site ID:"), 0, 0)
        self.site_id_edit = QLineEdit()
        self.site_id_edit.setToolTip("Your Netlify site ID")
        netlify_layout.addWidget(self.site_id_edit, 0, 1)
        
        netlify_layout.addWidget(QLabel("Access Token:"), 1, 0)
        self.access_token_edit = QLineEdit()
        self.access_token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.access_token_edit.setToolTip("Your Netlify access token")
        netlify_layout.addWidget(self.access_token_edit, 1, 1)
        
        layout.addWidget(netlify_group)
        
        # General settings
        general_group = QGroupBox("General Settings")
        general_layout = QGridLayout(general_group)
        
        self.auto_backup_cb = QCheckBox("Auto backup before saving")
        self.auto_backup_cb.setToolTip("Automatically create backups when saving changes")
        general_layout.addWidget(self.auto_backup_cb, 0, 0, 1, 2)
        
        general_layout.addWidget(QLabel("Backup count:"), 1, 0)
        self.backup_count_spin = QSpinBox()
        self.backup_count_spin.setRange(1, 50)
        self.backup_count_spin.setToolTip("Maximum number of backup files to keep")
        general_layout.addWidget(self.backup_count_spin, 1, 1)
        
        layout.addWidget(general_group)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept_settings)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def populate_settings(self):
        """Populate settings fields with current values"""
        # Project folder
        current_folder = self.settings.get('project_folder', '')
        if not current_folder:
            # Default to Documents/Twinfolks_Wreaths if not set
            home = Path.home()
            current_folder = str(home / "Documents" / "Twinfolks_Wreaths")
        
        self.folder_path_edit.setText(current_folder)
        
        # Netlify settings
        self.site_id_edit.setText(self.settings.get('netlify_site_id', ''))
        self.access_token_edit.setText(self.settings.get('netlify_access_token', ''))
        
        # General settings
        self.auto_backup_cb.setChecked(self.settings.get('auto_backup', True))
        self.backup_count_spin.setValue(self.settings.get('backup_count', 10))
        
    def browse_project_folder(self):
        """Open folder browser to choose project folder location"""
        current_folder = self.folder_path_edit.text()
        
        # Default to current folder or Documents
        start_path = current_folder if current_folder and Path(current_folder).exists() else str(Path.home() / "Documents")
        
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Choose Project Folder Location",
            start_path,
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks
        )
        
        if folder_path:
            # Suggest a subfolder name if they didn't choose one that looks like a project folder
            chosen_path = Path(folder_path)
            
            # If they chose a folder that doesn't end with our project name, suggest adding it
            if chosen_path.name != "Twinfolks_Wreaths":
                reply = QMessageBox.question(
                    self,
                    "Folder Structure",
                    f"Would you like to create a 'Twinfolks_Wreaths' folder inside:\n{folder_path}\n\n"
                    "This keeps your wreath files organized in their own folder.",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    folder_path = str(chosen_path / "Twinfolks_Wreaths")
            
            self.folder_path_edit.setText(folder_path)
            
    def accept_settings(self):
        """Save settings and handle folder changes"""
        new_folder = self.folder_path_edit.text().strip()
        old_folder = self.settings.get('project_folder', '')
        
        # Validate new folder path
        if not new_folder:
            QMessageBox.warning(self, "Invalid Folder", "Please choose a valid project folder location.")
            return
            
        # Check if folder location changed
        folder_changed = (old_folder != new_folder)
        
        if folder_changed and old_folder and Path(old_folder).exists():
            # Ask user if they want to move their data
            reply = QMessageBox.question(
                self,
                "Move Project Data?",
                f"You're changing the project folder from:\n{old_folder}\n\nto:\n{new_folder}\n\n"
                "Would you like to move your existing wreaths and data to the new location?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Yes
            )
            
            if reply == QMessageBox.StandardButton.Cancel:
                return
            elif reply == QMessageBox.StandardButton.Yes:
                # User wants to move data
                try:
                    self.move_project_data(old_folder, new_folder)
                except Exception as e:
                    QMessageBox.critical(
                        self, "Move Error", 
                        f"Failed to move project data:\n{e}\n\nPlease move the files manually."
                    )
                    return
        
        # Update settings
        self.settings['project_folder'] = new_folder
        self.settings['netlify_site_id'] = self.site_id_edit.text().strip()
        self.settings['netlify_access_token'] = self.access_token_edit.text().strip()
        self.settings['auto_backup'] = self.auto_backup_cb.isChecked()
        self.settings['backup_count'] = self.backup_count_spin.value()
        
        # If folder changed, inform parent app about the change
        if folder_changed:
            self.settings['folder_changed'] = True
            self.settings['old_folder'] = old_folder
            self.settings['new_folder'] = new_folder
        
        self.accept()
        
    def move_project_data(self, old_folder, new_folder):
        """Move project data from old folder to new folder"""
        old_path = Path(old_folder)
        new_path = Path(new_folder)
        
        if not old_path.exists():
            raise Exception(f"Source folder does not exist: {old_folder}")
            
        # Create new folder
        new_path.mkdir(parents=True, exist_ok=True)
        
        # Files to move
        files_to_move = [
            "wreaths.json",
            "settings.json", 
            "WELCOME.txt"
        ]
        
        # Folders to move
        folders_to_move = [
            "backups",
            "imports", 
            "exports",
            "encoding_backups"  # From encoding fix feature
        ]
        
        # Move files
        for file_name in files_to_move:
            old_file = old_path / file_name
            new_file = new_path / file_name
            
            if old_file.exists():
                import shutil
                shutil.copy2(old_file, new_file)
        
        # Move folders
        for folder_name in folders_to_move:
            old_subfolder = old_path / folder_name
            new_subfolder = new_path / folder_name
            
            if old_subfolder.exists():
                import shutil
                shutil.copytree(old_subfolder, new_subfolder, dirs_exist_ok=True)
        
        # Create info file about the move
        move_info = new_path / "MOVED_FROM.txt"
        with open(move_info, 'w') as f:
            from datetime import datetime
            f.write(f"Project data moved from: {old_folder}\n")
            f.write(f"Move completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Original files are still in the old location for safety.\n")
        
    def get_settings(self):
        """Return the updated settings"""
        return self.settings