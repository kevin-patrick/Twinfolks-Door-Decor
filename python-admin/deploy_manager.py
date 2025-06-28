# File: python-admin/deploy_manager.py
# Netlify deployment manager for uploading wreaths.json

import json
import requests
import base64
from datetime import datetime
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QDialogButtonBox, QProgressBar,
                            QTextEdit, QMessageBox, QCheckBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

class DeployThread(QThread):
    """Thread for handling Netlify deployment"""
    
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    log = pyqtSignal(str)
    finished = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, site_id, access_token, wreaths_data):
        super().__init__()
        self.site_id = site_id
        self.access_token = access_token
        self.wreaths_data = wreaths_data
        
    def run(self):
        """Run the deployment process"""
        try:
            self.progress.emit(10)
            self.status.emit("Preparing wreaths.json...")
            self.log.emit("🚀 Starting deployment to Netlify...")
            
            # Prepare wreaths.json content
            wreaths_json = json.dumps(self.wreaths_data, indent=2)
            self.log.emit(f"📊 Prepared {len(self.wreaths_data)} wreaths for upload")
            
            self.progress.emit(25)
            self.status.emit("Connecting to Netlify...")
            
            # Set up headers
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            # Get current site information
            self.log.emit("🔍 Getting site information...")
            site_response = requests.get(
                f'https://api.netlify.com/api/v1/sites/{self.site_id}',
                headers=headers,
                timeout=30
            )
            
            if site_response.status_code != 200:
                raise Exception(f"Failed to get site info: {site_response.status_code} - {site_response.text}")
                
            site_data = site_response.json()
            site_name = site_data.get('name', self.site_id)
            site_url = site_data.get('url', 'Unknown')
            
            self.log.emit(f"✅ Connected to site: {site_name}")
            self.log.emit(f"🌐 Site URL: {site_url}")
            
            self.progress.emit(40)
            self.status.emit("Getting current files...")
            
            # Get current deploy to find the wreaths.json file
            deploys_response = requests.get(
                f'https://api.netlify.com/api/v1/sites/{self.site_id}/deploys',
                headers=headers,
                params={'per_page': 1},
                timeout=30
            )
            
            if deploys_response.status_code != 200:
                raise Exception(f"Failed to get deploys: {deploys_response.status_code}")
                
            deploys = deploys_response.json()
            if not deploys:
                raise Exception("No deploys found for this site")
                
            latest_deploy_id = deploys[0]['id']
            self.log.emit(f"📋 Found latest deploy: {latest_deploy_id}")
            
            self.progress.emit(55)
            self.status.emit("Getting current site files...")
            
            # Get files from latest deploy
            files_response = requests.get(
                f'https://api.netlify.com/api/v1/deploys/{latest_deploy_id}/files',
                headers=headers,
                timeout=30
            )
            
            if files_response.status_code != 200:
                raise Exception(f"Failed to get deploy files: {files_response.status_code}")
                
            current_files = files_response.json()
            self.log.emit(f"📁 Found {len(current_files)} existing files")
            
            self.progress.emit(70)
            self.status.emit("Uploading wreaths.json...")
            
            # Prepare the files for the new deploy
            files_to_upload = {}
            
            # Encode wreaths.json content
            wreaths_content_b64 = base64.b64encode(wreaths_json.encode('utf-8')).decode('utf-8')
            files_to_upload['wreaths.json'] = wreaths_content_b64
            
            self.log.emit("📤 Uploading wreaths.json...")
            
            # Create new deploy
            deploy_data = {
                'files': files_to_upload
            }
            
            deploy_response = requests.post(
                f'https://api.netlify.com/api/v1/sites/{self.site_id}/deploys',
                headers=headers,
                json=deploy_data,
                timeout=60
            )
            
            if deploy_response.status_code not in [200, 201]:
                raise Exception(f"Failed to create deploy: {deploy_response.status_code} - {deploy_response.text}")
                
            deploy_result = deploy_response.json()
            deploy_id = deploy_result['id']
            deploy_url = deploy_result.get('deploy_ssl_url', deploy_result.get('deploy_url', 'Unknown'))
            
            self.log.emit(f"🚀 Created deploy: {deploy_id}")
            self.log.emit(f"🔗 Deploy URL: {deploy_url}")
            
            self.progress.emit(85)
            self.status.emit("Waiting for deploy to complete...")
            
            # Wait for deploy to complete
            max_wait = 300  # 5 minutes
            wait_time = 0
            check_interval = 5  # seconds
            
            while wait_time < max_wait:
                deploy_status_response = requests.get(
                    f'https://api.netlify.com/api/v1/deploys/{deploy_id}',
                    headers=headers,
                    timeout=30
                )
                
                if deploy_status_response.status_code == 200:
                    deploy_status = deploy_status_response.json()
                    state = deploy_status.get('state', 'unknown')
                    
                    self.log.emit(f"📊 Deploy status: {state}")
                    
                    if state == 'ready':
                        self.log.emit("✅ Deploy completed successfully!")
                        break
                    elif state in ['error', 'failed']:
                        error_msg = deploy_status.get('error_message', 'Unknown error')
                        raise Exception(f"Deploy failed: {error_msg}")
                        
                self.msleep(check_interval * 1000)  # Convert to milliseconds
                wait_time += check_interval
                
            if wait_time >= max_wait:
                self.log.emit("⚠️ Deploy is taking longer than expected, but may still succeed")
                
            self.progress.emit(100)
            self.status.emit("Deploy completed!")
            
            # Final success message
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            success_msg = f"""
🎉 Deployment Successful!

✅ wreaths.json updated on {site_name}
🌐 Live site: {site_url}
🚀 Deploy ID: {deploy_id}
⏰ Deployed at: {timestamp}

Your wreaths are now live on the website!
            """.strip()
            
            self.log.emit(success_msg)
            self.finished.emit(True, success_msg)
            
        except Exception as e:
            error_msg = f"❌ Deployment failed: {str(e)}"
            self.log.emit(error_msg)
            self.finished.emit(False, error_msg)

class DeployDialog(QDialog):
    """Dialog showing deployment progress"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Deploying to Netlify")
        self.setModal(True)
        self.resize(600, 500)
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("🚀 Deploying to Netlify")
        header.setFont(QFont("", 14, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("padding: 10px; color: #1e40af;")
        layout.addWidget(header)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Preparing...")
        self.status_label.setStyleSheet("padding: 5px; color: #374151;")
        layout.addWidget(self.status_label)
        
        # Log area
        log_label = QLabel("📄 Deployment Log:")
        log_label.setFont(QFont("", 10, QFont.Weight.Bold))
        layout.addWidget(log_label)
        
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setFont(QFont("Consolas", 9))
        self.log_area.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        layout.addWidget(self.log_area)
        
        # Auto-close option
        self.auto_close_cb = QCheckBox("Automatically close when deployment completes")
        self.auto_close_cb.setChecked(True)
        layout.addWidget(self.auto_close_cb)
        
        # Buttons
        self.button_box = QDialogButtonBox()
        self.close_btn = self.button_box.addButton("Close", QDialogButtonBox.ButtonRole.RejectRole)
        self.close_btn.setEnabled(False)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
        
    def update_progress(self, value):
        """Update progress bar"""
        self.progress_bar.setValue(value)
        
    def update_status(self, status):
        """Update status label"""
        self.status_label.setText(status)
        
    def add_log(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_area.append(f"[{timestamp}] {message}")
        
        # Auto-scroll to bottom
        scrollbar = self.log_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def deployment_finished(self, success, message):
        """Handle deployment completion"""
        self.close_btn.setEnabled(True)
        
        if success:
            self.status_label.setText("✅ Deployment completed successfully!")
            self.status_label.setStyleSheet("padding: 5px; color: #059669; font-weight: bold;")
            
            if self.auto_close_cb.isChecked():
                # Auto-close after 3 seconds
                QTimer.singleShot(3000, self.accept)
        else:
            self.status_label.setText("❌ Deployment failed")
            self.status_label.setStyleSheet("padding: 5px; color: #dc2626; font-weight: bold;")

class DeployManager:
    """Manager for handling Netlify deployments"""
    
    def __init__(self, settings, wreaths_data, parent=None):
        self.settings = settings
        self.wreaths_data = wreaths_data
        self.parent = parent
        
    def deploy(self):
        """Start deployment process"""
        # Validate settings
        site_id = self.settings.get('netlify_site_id', '').strip()
        access_token = self.settings.get('netlify_access_token', '').strip()
        
        if not site_id or not access_token:
            QMessageBox.warning(
                self.parent, "Missing Configuration",
                "Netlify Site ID and Access Token are required for deployment.\n\n"
                "Please configure them in Settings first."
            )
            return False
            
        # Show confirmation
        reply = QMessageBox.question(
            self.parent, 'Deploy to Netlify',
            f'Deploy {len(self.wreaths_data)} wreaths to your live website?\n\n'
            f'This will update the wreaths.json file on your Netlify site.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return False
            
        # Create and show deploy dialog
        dialog = DeployDialog(self.parent)
        
        # Create deploy thread
        deploy_thread = DeployThread(site_id, access_token, self.wreaths_data)
        
        # Connect signals
        deploy_thread.progress.connect(dialog.update_progress)
        deploy_thread.status.connect(dialog.update_status)
        deploy_thread.log.connect(dialog.add_log)
        deploy_thread.finished.connect(dialog.deployment_finished)
        
        # Start deployment
        deploy_thread.start()
        
        # Show dialog
        result = dialog.exec()
        
        # Clean up thread
        if deploy_thread.isRunning():
            deploy_thread.wait(5000)  # Wait up to 5 seconds
            
        return result == QDialog.DialogCode.Accepted