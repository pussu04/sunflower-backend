#!/usr/bin/env python3
"""
Simple test script to verify the sunflower disease detection setup
"""

import sys
import os

def test_imports():
    """Test if all required imports work"""
    print("Testing imports...")
    
    try:
        from flask import Flask
        print("✅ Flask imported successfully")
    except ImportError as e:
        print(f"❌ Flask import failed: {e}")
        return False
    
    try:
        import numpy as np
        print("✅ NumPy imported successfully")
    except ImportError as e:
        print(f"❌ NumPy import failed: {e}")
        return False
    
    try:
        from PIL import Image
        print("✅ PIL imported successfully")
    except ImportError as e:
        print(f"❌ PIL import failed: {e}")
        return False
    
    try:
        import tensorflow as tf
        print(f"✅ TensorFlow imported successfully (version: {tf.__version__})")
    except ImportError:
        try:
            import keras
            print(f"✅ Keras imported successfully (version: {keras.__version__})")
        except ImportError as e:
            print(f"❌ Neither TensorFlow nor Keras could be imported: {e}")
            return False
    
    return True

def test_model_file():
    """Test if the model file exists"""
    print("\nTesting model file...")
    
    model_path = os.path.join(os.path.dirname(__file__), 'trainedmodels', 'densenet121-baseline.h5')
    
    if os.path.exists(model_path):
        file_size = os.path.getsize(model_path) / (1024 * 1024)  # Size in MB
        print(f"✅ Model file exists: {model_path}")
        print(f"✅ Model file size: {file_size:.2f} MB")
        return True
    else:
        print(f"❌ Model file not found: {model_path}")
        return False

def test_sunflower_module():
    """Test if the sunflower module can be imported"""
    print("\nTesting sunflower module...")
    
    try:
        from trainedmodels.sunflowerModel import sunflower_routes, CLASS_LABELS
        print("✅ Sunflower module imported successfully")
        print(f"✅ Classes: {CLASS_LABELS}")
        return True
    except ImportError as e:
        print(f"❌ Sunflower module import failed: {e}")
        return False

def test_templates():
    """Test if templates exist"""
    print("\nTesting templates...")
    
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'index.html')
    
    if os.path.exists(template_path):
        print(f"✅ Template file exists: {template_path}")
        return True
    else:
        print(f"❌ Template file not found: {template_path}")
        return False

def main():
    """Run all tests"""
    print("🌻 Sunflower Disease Detection - Setup Test")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_model_file,
        test_sunflower_module,
        test_templates
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! The setup is ready.")
        return True
    else:
        print("❌ Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
