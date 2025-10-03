#!/usr/bin/env python3
"""
Comprehensive Unit Tests for Configuration Module

Tests all critical functions in config.py including:
- Environment loading
- Configuration validation
- Security checks
- Edge cases and boundary conditions
"""

import unittest
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, mock_open
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import config


class TestLoadEnvFile(unittest.TestCase):
    """Test environment file loading functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.original_cwd = os.getcwd()
        self.test_dir = tempfile.mkdtemp()
        os.chdir(self.test_dir)
        # Clear cache before each test
        config.load_env_file.cache_clear()
    
    def tearDown(self):
        """Clean up test environment"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_load_env_file_success(self):
        """Test successful .env file loading"""
        env_content = """
# Test comment
GEMINI_API_KEY=test_key_123
DEBUG=True
VERBOSE_LOGGING=false
"""
        with open('.env', 'w') as f:
            f.write(env_content)
        
        result = config.load_env_file()
        self.assertTrue(result)
        self.assertEqual(os.getenv('GEMINI_API_KEY'), 'test_key_123')
        self.assertEqual(os.getenv('DEBUG'), 'True')
        self.assertEqual(os.getenv('VERBOSE_LOGGING'), 'false')
    
    def test_load_env_file_no_file(self):
        """Test behavior when .env file doesn't exist"""
        result = config.load_env_file()
        self.assertTrue(result)  # Should return True even if file doesn't exist
    
    def test_load_env_file_empty_file(self):
        """Test loading empty .env file"""
        with open('.env', 'w') as f:
            f.write('')
        
        result = config.load_env_file()
        self.assertTrue(result)
    
    def test_load_env_file_comments_only(self):
        """Test file with only comments"""
        env_content = """
# This is a comment
# Another comment
"""
        with open('.env', 'w') as f:
            f.write(env_content)
        
        result = config.load_env_file()
        self.assertTrue(result)
    
    def test_load_env_file_malformed_lines(self):
        """Test handling of malformed lines"""
        env_content = """
VALID_KEY=valid_value
INVALID_LINE_NO_EQUALS
=EMPTY_KEY
KEY_WITH_MULTIPLE=EQUALS=SIGNS
"""
        with open('.env', 'w') as f:
            f.write(env_content)
        
        result = config.load_env_file()
        self.assertTrue(result)
        self.assertEqual(os.getenv('VALID_KEY'), 'valid_value')
        self.assertEqual(os.getenv('KEY_WITH_MULTIPLE'), 'EQUALS=SIGNS')
    
    def test_load_env_file_special_characters(self):
        """Test handling of special characters in values"""
        env_content = """
SPECIAL_CHARS=!@#$%^&*()
SPACES_VALUE=value with spaces
QUOTES_VALUE="quoted value"
UNICODE_VALUE=café
"""
        with open('.env', 'w') as f:
            f.write(env_content)
        
        result = config.load_env_file()
        self.assertTrue(result)
        self.assertEqual(os.getenv('SPECIAL_CHARS'), '!@#$%^&*()')
        self.assertEqual(os.getenv('SPACES_VALUE'), 'value with spaces')
        self.assertEqual(os.getenv('QUOTES_VALUE'), '"quoted value"')
        self.assertEqual(os.getenv('UNICODE_VALUE'), 'café')
    
    def test_load_env_file_whitespace_handling(self):
        """Test whitespace handling in keys and values"""
        env_content = """
  LEADING_SPACES=value
TRAILING_SPACES  =value
  BOTH_SPACES  =  value with spaces  
"""
        with open('.env', 'w') as f:
            f.write(env_content)
        
        result = config.load_env_file()
        self.assertTrue(result)
        self.assertEqual(os.getenv('LEADING_SPACES'), 'value')
        self.assertEqual(os.getenv('TRAILING_SPACES'), 'value')
        self.assertEqual(os.getenv('BOTH_SPACES'), 'value with spaces')
    
    def test_load_env_file_permission_error(self):
        """Test handling of permission errors"""
        with patch('builtins.open', side_effect=PermissionError("Access denied")):
            with patch('pathlib.Path.exists', return_value=True):
                result = config.load_env_file()
                self.assertTrue(result)  # Should handle error gracefully
    
    def test_load_env_file_caching(self):
        """Test that function results are cached"""
        env_content = "TEST_KEY=test_value"
        with open('.env', 'w') as f:
            f.write(env_content)
        
        # First call
        result1 = config.load_env_file()
        
        # Modify file
        with open('.env', 'w') as f:
            f.write("TEST_KEY=modified_value")
        
        # Second call should return cached result
        result2 = config.load_env_file()
        
        self.assertTrue(result1)
        self.assertTrue(result2)
        # Value should still be original due to caching
        self.assertEqual(os.getenv('TEST_KEY'), 'test_value')


class TestValidateConfig(unittest.TestCase):
    """Test configuration validation functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.original_env = os.environ.copy()
    
    def tearDown(self):
        """Restore original environment"""
        os.environ.clear()
        os.environ.update(self.original_env)
    
    def test_validate_config_success(self):
        """Test successful configuration validation"""
        os.environ['GEMINI_API_KEY'] = 'AIzaSyBxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
        os.environ['INPUT_FOLDER'] = 'Data'
        os.environ['OUTPUT_FOLDER'] = 'Output'
        
        # Reload config module to pick up new env vars
        import importlib
        importlib.reload(config)
        
        result = config.validate_config()
        self.assertTrue(result)
    
    def test_validate_config_missing_api_key(self):
        """Test validation with missing API key"""
        if 'GEMINI_API_KEY' in os.environ:
            del os.environ['GEMINI_API_KEY']
        
        import importlib
        importlib.reload(config)
        
        with self.assertRaises(ValueError) as context:
            config.validate_config()
        
        self.assertIn("GEMINI_API_KEY environment variable is required", str(context.exception))
    
    def test_validate_config_empty_api_key(self):
        """Test validation with empty API key"""
        os.environ['GEMINI_API_KEY'] = ''
        
        import importlib
        importlib.reload(config)
        
        with self.assertRaises(ValueError) as context:
            config.validate_config()
        
        self.assertIn("GEMINI_API_KEY environment variable is required", str(context.exception))
    
    def test_validate_config_short_api_key(self):
        """Test validation with too short API key"""
        os.environ['GEMINI_API_KEY'] = 'short_key'
        
        import importlib
        importlib.reload(config)
        
        with self.assertRaises(ValueError) as context:
            config.validate_config()
        
        self.assertIn("GEMINI_API_KEY appears to be invalid", str(context.exception))
    
    def test_validate_config_invalid_folder_names(self):
        """Test validation with invalid folder names"""
        os.environ['GEMINI_API_KEY'] = 'AIzaSyBxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
        
        # Test path traversal in folder names
        test_cases = [
            ('INPUT_FOLDER', '../malicious'),
            ('OUTPUT_FOLDER', '/absolute/path'),
            ('INPUT_FOLDER', ''),
            ('OUTPUT_FOLDER', 'folder/with/slash')
        ]
        
        for folder_var, folder_value in test_cases:
            with self.subTest(folder=folder_var, value=folder_value):
                os.environ[folder_var] = folder_value
                
                import importlib
                importlib.reload(config)
                
                with self.assertRaises(ValueError) as context:
                    config.validate_config()
                
                self.assertIn("contains invalid characters", str(context.exception))
    
    def test_validate_config_whitespace_api_key(self):
        """Test validation with whitespace in API key"""
        os.environ['GEMINI_API_KEY'] = '  AIzaSyBxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx  '
        
        import importlib
        importlib.reload(config)
        
        result = config.validate_config()
        self.assertTrue(result)


class TestConfigurationVariables(unittest.TestCase):
    """Test configuration variable loading and defaults"""
    
    def setUp(self):
        """Set up test environment"""
        self.original_env = os.environ.copy()
    
    def tearDown(self):
        """Restore original environment"""
        os.environ.clear()
        os.environ.update(self.original_env)
    
    def test_default_values(self):
        """Test default configuration values"""
        # Clear relevant env vars
        for key in ['GEMINI_MODEL', 'INPUT_FOLDER', 'OUTPUT_FOLDER', 'DEBUG', 'VERBOSE_LOGGING']:
            if key in os.environ:
                del os.environ[key]
        
        import importlib
        importlib.reload(config)
        
        self.assertEqual(config.GEMINI_MODEL, 'gemini-2.0-flash-exp')
        self.assertEqual(config.INPUT_FOLDER, 'Data')
        self.assertEqual(config.OUTPUT_FOLDER, 'Output')
        self.assertFalse(config.DEBUG)
        self.assertFalse(config.VERBOSE_LOGGING)
    
    def test_custom_values(self):
        """Test custom configuration values"""
        os.environ['GEMINI_MODEL'] = 'gemini-1.5-pro'
        os.environ['INPUT_FOLDER'] = 'CustomInput'
        os.environ['OUTPUT_FOLDER'] = 'CustomOutput'
        os.environ['DEBUG'] = 'true'
        os.environ['VERBOSE_LOGGING'] = 'TRUE'
        
        import importlib
        importlib.reload(config)
        
        self.assertEqual(config.GEMINI_MODEL, 'gemini-1.5-pro')
        self.assertEqual(config.INPUT_FOLDER, 'CustomInput')
        self.assertEqual(config.OUTPUT_FOLDER, 'CustomOutput')
        self.assertTrue(config.DEBUG)
        self.assertTrue(config.VERBOSE_LOGGING)
    
    def test_boolean_parsing(self):
        """Test boolean value parsing"""
        test_cases = [
            ('true', True),
            ('True', True),
            ('TRUE', True),
            ('false', False),
            ('False', False),
            ('FALSE', False),
            ('yes', False),  # Only 'true' should be True
            ('1', False),
            ('', False)
        ]
        
        for value, expected in test_cases:
            with self.subTest(value=value, expected=expected):
                os.environ['DEBUG'] = value
                
                import importlib
                importlib.reload(config)
                
                self.assertEqual(config.DEBUG, expected)


if __name__ == '__main__':
    unittest.main(verbosity=2)