#!/usr/bin/env python3
"""
Quick launcher for the PDF OCR Web Interface

Simple script to start the Gradio web interface with minimal setup.
"""

if __name__ == "__main__":
    try:
        from gradio_app import main
        main()
    except ImportError as e:
        print("❌ Missing dependencies. Please install requirements:")
        print("pip install -r requirements.txt")
        print(f"Error: {e}")
    except Exception as e:
        print(f"❌ Error starting web interface: {e}")