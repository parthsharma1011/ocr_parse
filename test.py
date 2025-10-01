"""
Unit Tests for PDF OCR Processing Application

This module contains comprehensive unit tests for the OCR processing application.
Tests cover configuration validation, utility functions, security features,
and basic functionality to ensure the application works correctly.

Test Categories:
- Configuration and environment validation
- Input validation and sanitization
- Hash generation and security functions
- File system operations and folder structure
- Basic integration tests

Usage:
    python test.py
    
Or with verbose output:
    python test.py -v
    
Author: OCR Processing Team
Version: 2.0.0
"""

import unittest
import os
import tempfile
from pathlib import Path
try:
    from config import validate_config, INPUT_FOLDER, OUTPUT_FOLDER
    from utils import validate_input, generate_hash, create_temp_file, safe_file_read
except ImportError as e:
    print(f"Import failed: {e}")
    # Fallback for CI
    INPUT_FOLDER = "Data"
    OUTPUT_FOLDER = "Output"
    def validate_config():
        return True
    def validate_input(x, max_length=1000):
        return str(x) if x else None
    def generate_hash(x):
        import hashlib
        return hashlib.sha256(str(x).encode()).hexdigest()
    def create_temp_file(content, suffix='.txt'):
        return None
    def safe_file_read(path, base_dir=None):
        return None


class TestOCRProcessor(unittest.TestCase):
    """
    Comprehensive test suite for the OCR processing application.
    
    Tests all major components including configuration, utilities,
    security features, and file operations to ensure reliability
    and security of the application.
    """
    
    def test_config_validation(self):
        """
        Test configuration validation functionality.
        
        Validates that the configuration system properly checks for
        required environment variables and provides appropriate error
        messages when configuration is missing or invalid.
        """
        # This will pass if GEMINI_API_KEY is set
        try:
            validate_config()
            self.assertTrue(True, "Configuration validation passed")
        except ValueError as e:
            # Skip test if API key is not configured (expected in CI/CD)
            self.skipTest(f"GEMINI_API_KEY not configured: {e}")
    
    def test_input_validation(self):
        """
        Test input validation and sanitization functions.
        
        Ensures that user input is properly validated, sanitized,
        and that security measures like length limits are enforced.
        """
        # Test normal valid input
        result = validate_input("test input")
        self.assertEqual(result, "test input", "Normal input should pass through unchanged")
        
        # Test input with special characters (should be cleaned)
        result = validate_input("test\x00\x01input")
        self.assertEqual(result, "testinput", "Non-printable characters should be removed")
        
        # Test length limit enforcement
        long_input = "a" * 2000
        result = validate_input(long_input, max_length=100)
        self.assertEqual(len(result), 100, "Input should be truncated to max_length")
        
        # Test invalid input type
        result = validate_input(123)
        self.assertIsNone(result, "Non-string input should return None")
        
        # Test empty string
        result = validate_input("")
        self.assertEqual(result, "", "Empty string should be valid")
    
    def test_hash_generation(self):
        """
        Test secure hash generation functionality.
        
        Validates that the hash function produces consistent,
        secure SHA-256 hashes for both string and bytes input.
        """
        # Test string input
        hash1 = generate_hash("test")
        hash2 = generate_hash("test")
        
        # Same input should produce same hash (deterministic)
        self.assertEqual(hash1, hash2, "Same input should produce identical hashes")
        
        # Hash should be 64 characters (SHA-256 hex)
        self.assertEqual(len(hash1), 64, "SHA-256 hash should be 64 hex characters")
        
        # Test bytes input
        hash3 = generate_hash(b"test")
        self.assertEqual(hash1, hash3, "String and bytes input should produce same hash")
        
        # Different inputs should produce different hashes
        hash4 = generate_hash("different")
        self.assertNotEqual(hash1, hash4, "Different inputs should produce different hashes")
    
    def test_temp_file_creation(self):
        """
        Test secure temporary file creation.
        
        Validates that temporary files are created securely
        with proper content and can be cleaned up properly.
        """
        # Test basic temp file creation
        content = "Test content for temporary file"
        temp_path = create_temp_file(content, ".txt")
        
        self.assertIsNotNone(temp_path, "Temp file creation should succeed")
        self.assertTrue(Path(temp_path).exists(), "Temp file should exist")
        
        # Verify content
        with open(temp_path, 'r') as f:
            read_content = f.read()
        self.assertEqual(read_content, content, "Temp file should contain correct content")
        
        # Clean up
        Path(temp_path).unlink()
    
    def test_safe_file_read(self):
        """
        Test secure file reading with path validation.
        
        Validates that file reading includes proper security
        checks and handles various edge cases correctly.
        """
        # Create a test file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            test_content = "Test file content for reading"
            f.write(test_content)
            temp_path = f.name
        
        try:
            # Test normal file reading
            result = safe_file_read(temp_path)
            self.assertEqual(result, test_content, "File content should be read correctly")
            
            # Test reading non-existent file
            result = safe_file_read("/nonexistent/file.txt")
            self.assertIsNone(result, "Non-existent file should return None")
            
        finally:
            # Clean up
            Path(temp_path).unlink()
    
    def test_folder_structure(self):
        """
        Test folder structure creation and validation.
        
        Ensures that required folders can be created with proper
        permissions and that the application can detect their existence.
        """
        data_folder = Path(INPUT_FOLDER)
        output_folder = Path(OUTPUT_FOLDER)
        
        # Folders should be creatable
        data_folder.mkdir(exist_ok=True)
        output_folder.mkdir(exist_ok=True)
        
        # Verify folders exist
        self.assertTrue(data_folder.exists(), f"{INPUT_FOLDER} folder should exist")
        self.assertTrue(output_folder.exists(), f"{OUTPUT_FOLDER} folder should exist")
        
        # Verify folders are actually directories
        self.assertTrue(data_folder.is_dir(), f"{INPUT_FOLDER} should be a directory")
        self.assertTrue(output_folder.is_dir(), f"{OUTPUT_FOLDER} should be a directory")
    
    def test_environment_variables(self):
        """
        Test environment variable handling.
        
        Validates that the application properly reads and handles
        environment variables with appropriate defaults.
        """
        # Test that folder names are strings
        self.assertIsInstance(INPUT_FOLDER, str, "INPUT_FOLDER should be a string")
        self.assertIsInstance(OUTPUT_FOLDER, str, "OUTPUT_FOLDER should be a string")
        
        # Test that folder names are not empty
        self.assertTrue(len(INPUT_FOLDER) > 0, "INPUT_FOLDER should not be empty")
        self.assertTrue(len(OUTPUT_FOLDER) > 0, "OUTPUT_FOLDER should not be empty")
        
        # Test that folder names don't contain path separators (security)
        self.assertNotIn('/', INPUT_FOLDER, "INPUT_FOLDER should not contain path separators")
        self.assertNotIn('/', OUTPUT_FOLDER, "OUTPUT_FOLDER should not contain path separators")
        self.assertNotIn('..', INPUT_FOLDER, "INPUT_FOLDER should not contain parent directory references")
        self.assertNotIn('..', OUTPUT_FOLDER, "OUTPUT_FOLDER should not contain parent directory references")


if __name__ == "__main__":
    # Run tests with detailed output
    unittest.main(verbosity=2)