# File: python-admin/build_exe.py
# Script to build standalone executable for Twinfolks Wreath Manager

import os
import sys
import subprocess
import shutil
from pathlib import Path

def build_executable():
    """Build standalone executable using PyInstaller"""
    
    print("🔨 Building Twinfolks Wreath Manager executable...")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("main.py").exists():
        print("❌ Error: main.py not found!")
        print("Please run this script from the python-admin directory.")
        return False
        
    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print("✅ PyInstaller found")
    except ImportError:
        print("❌ PyInstaller not found!")
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "PyInstaller"])
        
    # Clean previous builds
    for folder in ["build", "dist", "__pycache__"]:
        if Path(folder).exists():
            print(f"🧹 Cleaning {folder}...")
            shutil.rmtree(folder)
            
    # Remove old spec file
    spec_file = Path("main.spec")
    if spec_file.exists():
        spec_file.unlink()
        
    print("\n📦 Building executable...")
    
    # PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",                    # Single executable file
        "--windowed",                   # No console window
        "--name", "TwinfolksWreathManager",
        "--icon", "assets/icon.ico",    # App icon (optional)
        "--add-data", "assets;assets",  # Include assets folder (optional)
        "--clean",                      # Clean before building
        "main.py"
    ]
    
    try:
        # Run PyInstaller
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Build completed successfully!")
            
            # Check if executable was created
            exe_path = Path("dist/TwinfolksWreathManager.exe")
            if exe_path.exists():
                exe_size = exe_path.stat().st_size / (1024 * 1024)  # MB
                print(f"\n🎉 Executable created: {exe_path}")
                print(f"📏 Size: {exe_size:.1f} MB")
                
                # Create a release folder
                release_folder = Path("../TwinfolksWreathManager_Release")
                release_folder.mkdir(exist_ok=True)
                
                # Copy executable to release folder
                release_exe = release_folder / "TwinfolksWreathManager.exe"
                shutil.copy2(exe_path, release_exe)
                
                # Create README for users
                readme_content = """
Twinfolks Wreath Manager
========================

A complete wreath management system for Twinfolks Door Decor.

🚀 Getting Started:
1. Double-click TwinfolksWreathManager.exe to launch
2. The app will create a project folder at: Documents/Twinfolks_Wreaths
3. Configure your Netlify settings in Edit → Settings
4. Import your Poshmark JSON files or start adding wreaths manually

📁 Project Folder:
- All your wreaths are saved in Documents/Twinfolks_Wreaths/wreaths.json
- Backups are automatically created in the backups/ folder
- Import new JSON files into the imports/ folder

🌐 Netlify Deployment:
- Configure your Site ID and Access Token in settings
- Click "Deploy to Website" to update your live site
- The app will upload your wreaths.json file automatically

💡 Tips:
- Use the "Featured" checkbox to highlight special wreaths
- Drag and drop images in the image manager to reorder them
- The search box works on titles, descriptions, and hashtags
- Always save your changes before deploying

🆘 Need Help?
- All data is stored locally in Documents/Twinfolks_Wreaths
- Your wreaths.json file can be manually edited if needed
- Backups are created automatically before each save

Built with ❤️ for beautiful handcrafted wreaths!
                """.strip()
                
                readme_path = release_folder / "README.txt"
                with open(readme_path, 'w') as f:
                    f.write(readme_content)
                    
                print(f"\n📁 Release package created: {release_folder}")
                print(f"   - TwinfolksWreathManager.exe")
                print(f"   - README.txt")
                
                print(f"\n🎯 Next Steps:")
                print(f"   1. Test the executable: {release_exe}")
                print(f"   2. Share the entire folder: {release_folder}")
                print(f"   3. Your wife can run it without installing Python!")
                
                return True
            else:
                print("❌ Executable not found after build!")
                return False
                
        else:
            print("❌ Build failed!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Build error: {e}")
        return False

def create_assets_folder():
    """Create assets folder with default icon"""
    assets_folder = Path("assets")
    assets_folder.mkdir(exist_ok=True)
    
    # Create a simple text-based icon file as placeholder
    icon_info = assets_folder / "icon_info.txt"
    with open(icon_info, 'w') as f:
        f.write("""
Icon Information
================

For a professional look, add these files to the assets/ folder:

1. icon.ico - Windows icon file (32x32 or 48x48 pixels)
2. icon.png - PNG icon for the application

You can create these from any wreath image using online converters:
- PNG to ICO: convertio.co/png-ico/
- Resize images: resizeimage.net

Recommended icon: A simple wreath silhouette on transparent background.

If no icon files are provided, the application will use the default system icon.
        """)

if __name__ == "__main__":
    print("🎀 Twinfolks Wreath Manager - Build Script")
    print("=========================================\n")
    
    # Create assets folder
    create_assets_folder()
    
    # Build executable
    success = build_executable()
    
    if success:
        print("\n🎉 Build completed successfully!")
        print("\nYour standalone executable is ready to use!")
    else:
        print("\n❌ Build failed. Please check the error messages above.")
        
    input("\nPress Enter to exit...")