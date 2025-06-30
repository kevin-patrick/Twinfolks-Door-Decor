# File: python-admin/test_dialogs.py
# Quick test script to verify dialogs work

import sys
from PySide6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget

def test_wreath_editor():
    """Test the wreath editor dialog"""
    try:
        from wreath_editor_pyside import WreathEditorDialog
        
        # Test with new wreath
        dialog = WreathEditorDialog()
        result = dialog.exec()
        
        if result:
            print("✅ Wreath Editor: Dialog accepted")
            data = dialog.get_wreath_data()
            print(f"   Title: {data.get('title', 'No title')}")
            print(f"   Price: ${data.get('localPrice', 0)}")
        else:
            print("❌ Wreath Editor: Dialog cancelled")
            
    except Exception as e:
        print(f"❌ Wreath Editor Error: {e}")
        import traceback
        traceback.print_exc()

def test_image_viewer():
    """Test the image viewer dialog"""
    try:
        from image_viewer_pyside import ImageViewerDialog
        
        # Test with sample images
        sample_images = [
            "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=400",
            "https://images.unsplash.com/photo-1512069772995-ec65ba2d42ad?w=400"
        ]
        
        dialog = ImageViewerDialog(sample_images)
        result = dialog.exec()
        
        if result:
            print("✅ Image Viewer: Dialog accepted")
            images = dialog.get_images()
            print(f"   Number of images: {len(images)}")
        else:
            print("❌ Image Viewer: Dialog cancelled")
            
    except Exception as e:
        print(f"❌ Image Viewer Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Test both dialogs"""
    app = QApplication(sys.argv)
    
    # Create test window
    window = QWidget()
    window.setWindowTitle("Dialog Test")
    layout = QVBoxLayout(window)
    
    # Test buttons
    editor_btn = QPushButton("Test Wreath Editor")
    editor_btn.clicked.connect(test_wreath_editor)
    layout.addWidget(editor_btn)
    
    image_btn = QPushButton("Test Image Viewer")
    image_btn.clicked.connect(test_image_viewer)
    layout.addWidget(image_btn)
    
    window.show()
    app.exec()

if __name__ == '__main__':
    main()