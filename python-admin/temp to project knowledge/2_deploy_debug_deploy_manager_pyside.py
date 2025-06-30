# File: python-admin/deploy_manager_pyside.py
# Enhanced deploy manager for Netlify deployment

import json
import requests
import base64
from pathlib import Path
from PySide6.QtWidgets import QMessageBox, QProgressDialog, QApplication
from PySide6.QtCore import QThread, Signal, Qt

class NetlifyDeployThread(QThread):
    """Thread for handling Netlify deployment"""
    progress = Signal(str)  # Progress message
    finished = Signal(bool, str)  # Success, message
    
    def __init__(self, site_id, access_token, wreaths_data):
        super().__init__()
        self.site_id = site_id
        self.access_token = access_token
        self.wreaths_data = wreaths_data
        
    def run(self):
        """Run the deployment process"""
        try:
            print("🚀 DEPLOY THREAD STARTED")
            # Step 1: Prepare JSON data
            self.progress.emit("Preparing wreaths.json data...")
            json_content = json.dumps(self.wreaths_data, indent=2)
            print(f"📄 JSON prepared: {len(json_content)} characters")
            
            # Step 2: Get current site info
            self.progress.emit("Connecting to Netlify...")
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            # Check if site exists and we have access
            site_url = f"https://api.netlify.com/api/v1/sites/{self.site_id}"
            try:
                site_response = requests.get(site_url, headers=headers, timeout=10)
            except Exception as e:
                self.finished.emit(False, f"❌ Connection failed: {str(e)}")
                return
            
            if site_response.status_code == 401:
                self.finished.emit(False, "❌ Invalid access token. Please check your Netlify settings.")
                return
            elif site_response.status_code == 404:
                self.finished.emit(False, "❌ Site not found. Please check your Site ID in settings.")
                return
            elif site_response.status_code != 200:
                self.finished.emit(False, f"❌ Error accessing site: {site_response.status_code}")
                return
                
            site_info = site_response.json()
            site_name = site_info.get('name', 'Unknown')
            site_url_public = site_info.get('url', 'Unknown')
            
            self.progress.emit(f"Connected to site: {site_name}")
            
            # Step 3: Get current files to preserve other files
            self.progress.emit("Getting current site files...")
            files_url = f"https://api.netlify.com/api/v1/sites/{self.site_id}/files"
            files_response = requests.get(files_url, headers=headers, timeout=30)
            
            if files_response.status_code != 200:
                self.finished.emit(False, f"❌ Could not get current files: {files_response.status_code}")
                return
            
            # Step 4: Create new deployment with updated wreaths.json
            self.progress.emit("Creating new deployment...")
            
            # Prepare files for deployment - just update wreaths.json
            files_to_deploy = {
                "wreaths.json": json_content
            }
            
            # Create deployment
            deploy_data = {
                "files": files_to_deploy
            }
            
            deploy_url = f"https://api.netlify.com/api/v1/sites/{self.site_id}/deploys"
            deploy_response = requests.post(deploy_url, headers=headers, json=deploy_data, timeout=60)
            
            if deploy_response.status_code not in [200, 201]:
                self.finished.emit(False, f"❌ Deployment failed: {deploy_response.status_code}\n{deploy_response.text}")
                return
                
            deploy_info = deploy_response.json()
            deploy_id = deploy_info.get('id')
            
            self.progress.emit("Deployment created, waiting for completion...")
            
            # Step 5: Wait for deployment to complete
            import time
            max_wait = 120  # 2 minutes max
            wait_time = 0
            
            while wait_time < max_wait:
                time.sleep(3)
                wait_time += 3
                
                status_url = f"https://api.netlify.com/api/v1/deploys/{deploy_id}"
                status_response = requests.get(status_url, headers=headers, timeout=30)
                
                if status_response.status_code == 200:
                    status_info = status_response.json()
                    state = status_info.get('state', 'unknown')
                    
                    if state == 'ready':
                        deploy_url_public = status_info.get('deploy_ssl_url', site_url_public)
                        self.finished.emit(True, f"✅ Deployment successful!\n\n📍 Your website: {deploy_url_public}\n📄 Updated wreaths.json with {len(self.wreaths_data)} wreaths")
                        return
                    elif state == 'error':
                        error_msg = status_info.get('error_message', 'Unknown error')
                        self.finished.emit(False, f"❌ Deployment failed: {error_msg}")
                        return
                    else:
                        self.progress.emit(f"Deploying... ({state})")
                else:
                    self.progress.emit("Checking deployment status...")
            
            # Timeout
            self.finished.emit(False, "⏰ Deployment timed out. Please check Netlify dashboard.")
            
        except requests.exceptions.Timeout:
            self.finished.emit(False, "⏰ Connection timed out. Please check your internet connection.")
        except requests.exceptions.ConnectionError:
            self.finished.emit(False, "🌐 Connection error. Please check your internet connection.")
        except Exception as e:
            self.finished.emit(False, f"❌ Unexpected error: {str(e)}")

class DeployManager:
    def __init__(self, settings, wreaths_data, parent=None):
        self.settings = settings
        self.wreaths_data = wreaths_data
        self.parent = parent
        
    def deploy(self):
        """Deploy wreaths.json to Netlify"""
        # Check if Netlify settings are configured
        site_id = self.settings.get('netlify_site_id', '').strip()
        access_token = self.settings.get('netlify_access_token', '').strip()
        
        print(f"INITIAL CHECK: site_id='{site_id}', access_token='{access_token[:8] if access_token else ''}'...")
        
        if not site_id or not access_token:
            reply = QMessageBox.question(
                self.parent, "Netlify Settings Missing",
                "Netlify Site ID and Access Token are required for deployment.\n\n"
                "Would you like to open Settings to configure them?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Open settings dialog
                from settings_dialog_pyside import SettingsDialog
                dialog = SettingsDialog(self.settings, self.parent)
                if dialog.exec() == 1:  # 1 means Accepted
                    new_settings = dialog.get_settings()
                    print(f"NEW SETTINGS FROM DIALOG: {new_settings}")
                    
                    # Update local settings
                    self.settings.update(new_settings)
                    print(f"DEPLOY MANAGER SETTINGS AFTER UPDATE: {self.settings}")
                    
                    # Update main app settings
                    self.parent.settings.update(new_settings)
                    
                    # Save the settings to the main app
                    if hasattr(self.parent, 'save_settings'):
                        self.parent.save_settings()
                        print("CALLED PARENT save_settings()")
                    
                    # Check if we now have credentials
                    new_site_id = new_settings.get('netlify_site_id', '').strip()
                    new_access_token = new_settings.get('netlify_access_token', '').strip()
                    
                    if new_site_id and new_access_token:
                        print(f"GOT CREDENTIALS: site_id={new_site_id[:8]}..., token={new_access_token[:8]}...")
                        # Continue with deployment using NEW credentials
                        site_id = new_site_id
                        access_token = new_access_token
                    else:
                        print("STILL NO CREDENTIALS - stopping deployment")
                        QMessageBox.warning(
                            self.parent, "Still Missing Credentials",
                            "Site ID and Access Token are still required. Please check your entries."
                        )
                        return
            return
        
        # Confirm deployment
        reply = QMessageBox.question(
            self.parent, "Deploy to Netlify",
            f"Deploy {len(self.wreaths_data)} wreaths to your website?\n\n"
            f"Site ID: {site_id[:10]}...\n"
            "This will update wreaths.json on your live website.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Create progress dialog
        self.progress_dialog = QProgressDialog(
            "Preparing deployment...", "Cancel", 0, 0, self.parent
        )
        self.progress_dialog.setWindowTitle("Deploying to Netlify")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.show()
        
        # Start deployment thread
        self.deploy_thread = NetlifyDeployThread(site_id, access_token, self.wreaths_data)
        self.deploy_thread.progress.connect(self.update_progress)
        self.deploy_thread.finished.connect(self.deployment_finished)
        self.progress_dialog.canceled.connect(self.cancel_deployment)
        
        self.deploy_thread.start()
        
    def update_progress(self, message):
        """Update progress dialog with status message"""
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.setLabelText(message)
            QApplication.processEvents()
            
    def cancel_deployment(self):
        """Cancel the deployment"""
        if hasattr(self, 'deploy_thread') and self.deploy_thread.isRunning():
            self.deploy_thread.quit()
            if not self.deploy_thread.wait(3000):  # Wait 3 seconds
                self.deploy_thread.terminate()  # Force terminate if needed
                self.deploy_thread.wait(1000)
        
    def deployment_finished(self, success, message):
        """Handle deployment completion"""
        # Clean up progress dialog
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()
            
        # Clean up thread
        if hasattr(self, 'deploy_thread'):
            self.deploy_thread.quit()
            self.deploy_thread.wait(5000)  # Wait up to 5 seconds
            
        if success:
            QMessageBox.information(self.parent, "Deployment Complete", message)
        else:
            QMessageBox.critical(self.parent, "Deployment Failed", message)