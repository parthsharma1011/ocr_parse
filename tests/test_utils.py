#!/usr/bin/env python3
"""
Comprehensive Unit Tests for Utils Module

Tests all critical functions in utils.py including:
- Hash generation
- Input validation
- File operations
- Logging setup
- Security and performance features
"""

import unittest
import os
import tempfile
import shutil
import logging
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import utils


class TestGenerateHash(unittest.TestCase):
    """Test hash generation functionality"""
    
    def test_generate_hash_string_input(self):
        """Test hash generation with string input"""
        result = utils.generate_hash("hello world")
        expected = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
        self.assertEqual(result, expected)
        self.assertEqual(len(result), 64)  # SHA-256 produces 64 hex characters
    
    def test_generate_hash_bytes_input(self):
        """Test hash generation with bytes input"""
        result = utils.generate_hash(b"hello world")
        expected = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
        self.assertEqual(result, expected)
    
    def test_generate_hash_empty_string(self):
        """Test hash generation with empty string"""
        result = utils.generate_hash("")
        expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        self.assertEqual(result, expected)
    
    def test_generate_hash_empty_bytes(self):
        """Test hash generation with empty bytes"""
        result = utils.generate_hash(b"")
        expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        self.assertEqual(result, expected)
    
    def test_generate_hash_unicode(self):
        """Test hash generation with unicode characters"""
        result = utils.generate_hash("café 🚀")
        self.assertEqual(len(result), 64)
        self.assertIsInstance(result, str)
    
    def test_generate_hash_large_input(self):
        """Test hash generation with large input"""
        large_string = "a" * 1000000  # 1MB string
        result = utils.generate_hash(large_string)
        self.assertEqual(len(result), 64)
    
    def test_generate_hash_consistency(self):
        """Test that same input produces same hash"""
        input_data = "test consistency"
        hash1 = utils.generate_hash(input_data)
        hash2 = utils.generate_hash(input_data)
        self.assertEqual(hash1, hash2)
    
    def test_generate_hash_different_inputs(self):
        """Test that different inputs produce different hashes"""
        hash1 = utils.generate_hash("input1")
        hash2 = utils.generate_hash("input2")
        self.assertNotEqual(hash1, hash2)


class TestValidateInput(unittest.TestCase):
    """Test input validation functionality"""
    
    def test_validate_input_valid_string(self):
        """Test validation with valid string input"""
        result = utils.validate_input("Hello World!")
        self.assertEqual(result, "Hello World!")
    
    def test_validate_input_non_string(self):
        """Test validation with non-string input"""
        test_cases = [123, None, [], {}, object()]
        for input_val in test_cases:
            with self.subTest(input_val=input_val):
                result = utils.validate_input(input_val)
                self.assertIsNone(result)
    
    def test_validate_input_empty_string(self):
        """Test validation with empty string"""
        result = utils.validate_input("")
        self.assertEqual(result, "")
    
    def test_validate_input_max_length_default(self):
        """Test validation with default max length"""
        long_string = "a" * 1001  # Exceeds default max_length of 1000
        result = utils.validate_input(long_string)
        self.assertEqual(len(result), 1000)
        self.assertEqual(result, "a" * 1000)
    
    def test_validate_input_max_length_custom(self):
        """Test validation with custom max length"""
        test_string = "hello world"
        result = utils.validate_input(test_string, max_length=5)
        self.assertEqual(result, "hello")
    
    def test_validate_input_max_length_zero(self):
        """Test validation with zero max length"""
        result = utils.validate_input("test", max_length=0)
        self.assertEqual(result, "")
    
    def test_validate_input_non_printable_chars(self):
        """Test validation removes non-printable characters"""
        # Test various non-printable characters
        test_cases = [
            ("Hello\x00World", "HelloWorld"),
            ("Test\x01\x02\x03", "Test"),
            ("Normal\tTab", "NormalTab"),  # Tab is non-printable in this context
            ("Line\nBreak", "LineBreak"),  # Newline is non-printable
            ("Carriage\rReturn", "CarriageReturn"),
            ("\x1f\x7fBoundary", "Boundary"),  # Boundary non-printable chars
        ]
        
        for input_str, expected in test_cases:
            with self.subTest(input_str=repr(input_str)):
                result = utils.validate_input(input_str)
                self.assertEqual(result, expected)
    
    def test_validate_input_printable_ascii_range(self):
        """Test that printable ASCII characters (0x20-0x7E) are preserved"""
        # Test all printable ASCII characters
        printable_chars = ''.join(chr(i) for i in range(0x20, 0x7F))
        result = utils.validate_input(printable_chars)
        self.assertEqual(result, printable_chars)
    
    def test_validate_input_special_characters(self):
        """Test validation with special characters"""
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        result = utils.validate_input(special_chars)
        self.assertEqual(result, special_chars)
    
    def test_validate_input_unicode_removal(self):
        """Test that unicode characters are removed"""
        test_cases = [
            ("café", "caf"),  # é is removed
            ("🚀 rocket", " rocket"),  # emoji removed
            ("naïve", "nave"),  # ï removed
        ]
        
        for input_str, expected in test_cases:
            with self.subTest(input_str=input_str):
                result = utils.validate_input(input_str)
                self.assertEqual(result, expected)
    
    def test_validate_input_negative_max_length(self):
        """Test validation with negative max length"""
        result = utils.validate_input("test", max_length=-1)
        self.assertEqual(result, "")


class TestCreateTempFile(unittest.TestCase):
    """Test temporary file creation functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_files = []
    
    def tearDown(self):
        """Clean up created temp files"""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except:
                pass
    
    def test_create_temp_file_success(self):
        """Test successful temp file creation"""
        content = "Hello, World!"
        temp_path = utils.create_temp_file(content)
        
        self.assertIsNotNone(temp_path)
        self.assertTrue(os.path.exists(temp_path))
        self.temp_files.append(temp_path)
        
        # Verify content
        with open(temp_path, 'r') as f:
            read_content = f.read()
        self.assertEqual(read_content, content)
    
    def test_create_temp_file_custom_suffix(self):
        """Test temp file creation with custom suffix"""
        content = "# Markdown content"
        temp_path = utils.create_temp_file(content, suffix=".md")
        
        self.assertIsNotNone(temp_path)
        self.assertTrue(temp_path.endswith(".md"))
        self.temp_files.append(temp_path)
    
    def test_create_temp_file_empty_content(self):
        """Test temp file creation with empty content"""
        temp_path = utils.create_temp_file("")
        
        self.assertIsNotNone(temp_path)
        self.assertTrue(os.path.exists(temp_path))
        self.temp_files.append(temp_path)
        
        # Verify empty content
        with open(temp_path, 'r') as f:
            content = f.read()
        self.assertEqual(content, "")
    
    def test_create_temp_file_large_content(self):
        """Test temp file creation with large content"""
        large_content = "x" * 100000  # 100KB content
        temp_path = utils.create_temp_file(large_content)
        
        self.assertIsNotNone(temp_path)
        self.temp_files.append(temp_path)
        
        # Verify content size
        file_size = os.path.getsize(temp_path)
        self.assertEqual(file_size, 100000)
    
    def test_create_temp_file_unicode_content(self):
        """Test temp file creation with unicode content"""
        unicode_content = "Hello 世界 🌍 café"
        temp_path = utils.create_temp_file(unicode_content)
        
        self.assertIsNotNone(temp_path)
        self.temp_files.append(temp_path)
        
        # Verify unicode content
        with open(temp_path, 'r', encoding='utf-8') as f:
            read_content = f.read()
        self.assertEqual(read_content, unicode_content)
    
    def test_create_temp_file_permission_error(self):
        """Test temp file creation with permission error"""
        with patch('tempfile.NamedTemporaryFile', side_effect=PermissionError("Access denied")):
            temp_path = utils.create_temp_file("test content")
            self.assertIsNone(temp_path)
    
    def test_create_temp_file_io_error(self):
        """Test temp file creation with IO error"""
        with patch('tempfile.NamedTemporaryFile', side_effect=IOError("Disk full")):
            temp_path = utils.create_temp_file("test content")
            self.assertIsNone(temp_path)


class TestSafeFileRead(unittest.TestCase):
    """Test safe file reading functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.test_dir, "test.txt")
        with open(self.test_file, 'w') as f:
            f.write("Test file content")
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
        # Clear path resolution cache
        utils._resolve_path.cache_clear()
    
    def test_safe_file_read_success(self):
        """Test successful file reading"""
        content = utils.safe_file_read(self.test_file)
        self.assertEqual(content, "Test file content")
    
    def test_safe_file_read_nonexistent_file(self):
        """Test reading non-existent file"""
        nonexistent = os.path.join(self.test_dir, "nonexistent.txt")
        content = utils.safe_file_read(nonexistent)
        self.assertIsNone(content)
    
    def test_safe_file_read_directory(self):
        """Test reading a directory instead of file"""
        content = utils.safe_file_read(self.test_dir)
        self.assertIsNone(content)
    
    def test_safe_file_read_with_base_dir_valid(self):
        """Test reading file within allowed base directory"""
        content = utils.safe_file_read(self.test_file, base_dir=self.test_dir)
        self.assertEqual(content, "Test file content")
    
    def test_safe_file_read_path_traversal_attack(self):
        """Test protection against path traversal attacks"""
        # Create a file outside the base directory
        outside_dir = tempfile.mkdtemp()
        outside_file = os.path.join(outside_dir, "outside.txt")
        with open(outside_file, 'w') as f:
            f.write("Outside content")
        
        try:
            # Try to read file outside base directory
            content = utils.safe_file_read(outside_file, base_dir=self.test_dir)
            self.assertIsNone(content)
        finally:
            shutil.rmtree(outside_dir, ignore_errors=True)
    
    def test_safe_file_read_relative_path_traversal(self):
        """Test protection against relative path traversal"""
        # Create malicious path with ../
        malicious_path = os.path.join(self.test_dir, "..", "malicious.txt")
        
        # This should be blocked by path validation
        content = utils.safe_file_read(malicious_path, base_dir=self.test_dir)
        self.assertIsNone(content)
    
    def test_safe_file_read_permission_error(self):
        """Test handling of permission errors"""
        with patch('builtins.open', side_effect=PermissionError("Access denied")):
            content = utils.safe_file_read(self.test_file)
            self.assertIsNone(content)
    
    def test_safe_file_read_unicode_content(self):
        """Test reading file with unicode content"""
        unicode_file = os.path.join(self.test_dir, "unicode.txt")
        unicode_content = "Hello 世界 🌍 café"
        with open(unicode_file, 'w', encoding='utf-8') as f:
            f.write(unicode_content)
        
        content = utils.safe_file_read(unicode_file)
        self.assertEqual(content, unicode_content)
    
    def test_safe_file_read_large_file(self):
        """Test reading large file"""
        large_file = os.path.join(self.test_dir, "large.txt")
        large_content = "x" * 100000  # 100KB
        with open(large_file, 'w') as f:
            f.write(large_content)
        
        content = utils.safe_file_read(large_file)
        self.assertEqual(len(content), 100000)
        self.assertEqual(content, large_content)


class TestSetupLogging(unittest.TestCase):
    """Test logging setup functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Clear singleton logger
        utils._logger = None
        # Remove any existing handlers
        logging.getLogger().handlers.clear()
    
    def tearDown(self):
        """Clean up test environment"""
        # Clear singleton logger
        utils._logger = None
        # Remove handlers
        logging.getLogger().handlers.clear()
    
    def test_setup_logging_default(self):
        """Test logging setup with default parameters"""
        logger = utils.setup_logging()
        
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.level, logging.INFO)
    
    def test_setup_logging_custom_file(self):
        """Test logging setup with custom log file"""
        custom_log = "custom.log"
        logger = utils.setup_logging(custom_log)
        
        self.assertIsInstance(logger, logging.Logger)
        
        # Clean up
        try:
            os.unlink(custom_log)
        except:
            pass
    
    def test_setup_logging_singleton_pattern(self):
        """Test that logging setup follows singleton pattern"""
        logger1 = utils.setup_logging("test1.log")
        logger2 = utils.setup_logging("test2.log")
        
        # Should return the same logger instance
        self.assertIs(logger1, logger2)
        
        # Clean up
        for log_file in ["test1.log", "test2.log"]:
            try:
                os.unlink(log_file)
            except:
                pass
    
    def test_setup_logging_handlers(self):
        """Test that logging setup creates proper handlers"""
        logger = utils.setup_logging()
        
        # Should have both file and console handlers
        root_logger = logging.getLogger()
        self.assertGreaterEqual(len(root_logger.handlers), 2)
        
        handler_types = [type(h).__name__ for h in root_logger.handlers]
        self.assertIn('FileHandler', handler_types)
        self.assertIn('StreamHandler', handler_types)


class TestResolvePathCaching(unittest.TestCase):
    """Test path resolution caching functionality"""
    
    def setUp(self):
        """Set up test environment"""
        utils._resolve_path.cache_clear()
    
    def test_resolve_path_caching(self):
        """Test that path resolution is cached"""
        test_path = "/tmp/test/path"
        
        # First call
        result1 = utils._resolve_path(test_path)
        
        # Second call should use cache
        result2 = utils._resolve_path(test_path)
        
        self.assertEqual(result1, result2)
        self.assertIsInstance(result1, Path)
    
    def test_resolve_path_cache_info(self):
        """Test cache statistics"""
        test_paths = ["/tmp/path1", "/tmp/path2", "/tmp/path1"]  # path1 repeated
        
        for path in test_paths:
            utils._resolve_path(path)
        
        cache_info = utils._resolve_path.cache_info()
        self.assertEqual(cache_info.hits, 1)  # One cache hit for repeated path1
        self.assertEqual(cache_info.misses, 2)  # Two cache misses for unique paths


if __name__ == '__main__':
    unittest.main(verbosity=2)