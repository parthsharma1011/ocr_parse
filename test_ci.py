#!/usr/bin/env python3
"""
CI-Specific Test Runner

This module provides a simplified test runner specifically designed for CI/CD environments.
It runs only tests that don't require external dependencies or API keys.
"""

import unittest
import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, '.')

def run_ci_tests():
    """Run tests suitable for CI environment"""
    
    print("🧪 Running CI-specific tests...")
    
    # Test 1: Basic imports
    try:
        import config
        import utils
        print("✅ Core modules imported successfully")
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False
    
    # Test 2: Utility functions
    try:
        from utils import generate_hash, validate_input
        
        # Test hash generation
        hash1 = generate_hash("test")
        hash2 = generate_hash("test")
        assert hash1 == hash2, "Hash generation inconsistent"
        assert len(hash1) == 64, "Hash length incorrect"
        
        # Test input validation
        result = validate_input("test input")
        assert result == "test input", "Input validation failed"
        
        result = validate_input(123)
        assert result is None, "Invalid input type not handled"
        
        print("✅ Utility functions work correctly")
    except Exception as e:
        print(f"❌ Utility test failed: {e}")
        return False
    
    # Test 3: Configuration
    try:
        from config import INPUT_FOLDER, OUTPUT_FOLDER
        assert isinstance(INPUT_FOLDER, str), "INPUT_FOLDER not string"
        assert isinstance(OUTPUT_FOLDER, str), "OUTPUT_FOLDER not string"
        assert len(INPUT_FOLDER) > 0, "INPUT_FOLDER empty"
        assert len(OUTPUT_FOLDER) > 0, "OUTPUT_FOLDER empty"
        print("✅ Configuration validation passed")
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False
    
    # Test 4: Folder creation
    try:
        data_folder = Path(INPUT_FOLDER)
        output_folder = Path(OUTPUT_FOLDER)
        
        data_folder.mkdir(exist_ok=True)
        output_folder.mkdir(exist_ok=True)
        
        assert data_folder.exists(), "Data folder creation failed"
        assert output_folder.exists(), "Output folder creation failed"
        print("✅ Folder structure test passed")
    except Exception as e:
        print(f"❌ Folder test failed: {e}")
        return False
    
    print("🎉 All CI tests passed!")
    return True

if __name__ == "__main__":
    success = run_ci_tests()
    sys.exit(0 if success else 1)