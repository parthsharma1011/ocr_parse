#!/usr/bin/env python3
"""
Quick test script for Gradio app functionality
"""

import sys
sys.path.insert(0, '.')

def test_gradio_app():
    """Test all Gradio app components"""
    print("🧪 Testing Gradio App Components...")
    
    try:
        # Test imports
        import gradio_app
        print("✅ Import successful")
        
        # Test port finding
        port = gradio_app.find_free_port()
        print(f"✅ Port allocation: {port}")
        
        # Test interface creation
        interface = gradio_app.create_interface()
        print("✅ Interface creation successful")
        
        # Test file validation
        is_valid, msg = gradio_app.validate_pdf_file("nonexistent.pdf")
        print(f"✅ File validation: {msg}")
        
        # Test cleanup
        gradio_app.cleanup_temp_dirs()
        print("✅ Cleanup function works")
        
        print("\n🎉 ALL TESTS PASSED!")
        print("🚀 Ready to launch: python start_web.py")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_gradio_app()
    sys.exit(0 if success else 1)