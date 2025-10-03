#!/usr/bin/env python3
"""
Comprehensive Unit Tests for Gradio App Module

Tests all critical functions in gradio_app.py including:
- Port allocation
- File validation
- PDF processing
- Interface creation
- Security features
"""

import unittest
import os
import tempfile
import shutil
import socket
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock gradio before importing
sys.modules['gradio'] = MagicMock()

import gradio_app


class TestFindFreePort(unittest.TestCase):
    """Test port allocation functionality"""
    
    def test_find_free_port_default(self):
        """Test finding free port with default parameters"""
        port = gradio_app.find_free_port()
        self.assertIsInstance(port, int)
        self.assertGreaterEqual(port, 7860)
        self.assertLess(port, 7960)  # Within reasonable range
    
    def test_find_free_port_custom_start(self):
        """Test finding free port with custom start port"""
        port = gradio_app.find_free_port(start_port=8000)
        self.assertIsInstance(port, int)
        self.assertGreaterEqual(port, 8000)
    
    def test_find_free_port_custom_max_attempts(self):
        """Test finding free port with custom max attempts"""
        port = gradio_app.find_free_port(max_attempts=5)
        self.assertIsInstance(port, int)
    
    def test_find_free_port_no_available_ports(self):
        """Test behavior when no ports are available"""
        # Mock socket to always raise OSError (port in use)
        with patch('socket.socket') as mock_socket:
            mock_socket.return_value.__enter__.return_value.bind.side_effect = OSError("Port in use")
            
            with self.assertRaises(RuntimeError) as context:
                gradio_app.find_free_port(max_attempts=3)
            
            self.assertIn("No free port found", str(context.exception))
    
    def test_find_free_port_boundary_conditions(self):
        """Test port finding with boundary conditions"""
        # Test with max_attempts = 1
        port = gradio_app.find_free_port(max_attempts=1)
        self.assertIsInstance(port, int)
        
        # Test with start_port at edge of range
        port = gradio_app.find_free_port(start_port=65530, max_attempts=5)
        self.assertIsInstance(port, int)
    
    def test_find_free_port_socket_error_handling(self):
        """Test handling of various socket errors"""
        error_count = 0
        
        def mock_bind(address):
            nonlocal error_count
            error_count += 1
            if error_count <= 2:  # Fail first 2 attempts
                raise OSError("Port in use")
            # Succeed on 3rd attempt
        
        with patch('socket.socket') as mock_socket:
            mock_socket.return_value.__enter__.return_value.bind.side_effect = mock_bind
            
            port = gradio_app.find_free_port(start_port=7860, max_attempts=5)
            self.assertEqual(port, 7862)  # Should succeed on 3rd port (7860+2)


class TestValidatePdfFile(unittest.TestCase):
    """Test PDF file validation functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.test_pdf = os.path.join(self.test_dir, "test.pdf")
        
        # Create a valid PDF file
        with open(self.test_pdf, 'wb') as f:
            f.write(b'%PDF-1.4\n%Test PDF content')
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_validate_pdf_file_success(self):
        """Test successful PDF validation"""
        is_valid, message = gradio_app.validate_pdf_file(self.test_pdf)
        self.assertTrue(is_valid)
        self.assertEqual(message, "Valid PDF file")
    
    def test_validate_pdf_file_not_found(self):
        """Test validation with non-existent file"""
        nonexistent_file = os.path.join(self.test_dir, "nonexistent.pdf")
        is_valid, message = gradio_app.validate_pdf_file(nonexistent_file)
        self.assertFalse(is_valid)
        self.assertEqual(message, "File not found")
    
    def test_validate_pdf_file_none_path(self):
        """Test validation with None file path"""
        is_valid, message = gradio_app.validate_pdf_file(None)
        self.assertFalse(is_valid)
        self.assertEqual(message, "File not found")
    
    def test_validate_pdf_file_empty_path(self):
        """Test validation with empty file path"""
        is_valid, message = gradio_app.validate_pdf_file("")
        self.assertFalse(is_valid)
        self.assertEqual(message, "File not found")
    
    def test_validate_pdf_file_too_large(self):
        """Test validation with file too large"""
        large_pdf = os.path.join(self.test_dir, "large.pdf")
        
        # Create file larger than 50MB
        with open(large_pdf, 'wb') as f:
            f.write(b'%PDF-1.4\n')
            f.write(b'x' * (51 * 1024 * 1024))  # 51MB
        
        is_valid, message = gradio_app.validate_pdf_file(large_pdf)
        self.assertFalse(is_valid)
        self.assertEqual(message, "File too large (max 50MB)")
    
    def test_validate_pdf_file_wrong_extension(self):
        """Test validation with wrong file extension"""
        txt_file = os.path.join(self.test_dir, "test.txt")
        with open(txt_file, 'w') as f:
            f.write("Not a PDF")
        
        is_valid, message = gradio_app.validate_pdf_file(txt_file)
        self.assertFalse(is_valid)
        self.assertEqual(message, "Invalid file type (PDF required)")
    
    def test_validate_pdf_file_invalid_header(self):
        """Test validation with invalid PDF header"""
        fake_pdf = os.path.join(self.test_dir, "fake.pdf")
        with open(fake_pdf, 'wb') as f:
            f.write(b'Not a PDF file')
        
        is_valid, message = gradio_app.validate_pdf_file(fake_pdf)
        self.assertFalse(is_valid)
        self.assertEqual(message, "Invalid PDF file format")
    
    def test_validate_pdf_file_case_insensitive_extension(self):
        """Test validation with different case extensions"""
        extensions = ['.PDF', '.Pdf', '.pDf']
        
        for ext in extensions:
            with self.subTest(extension=ext):
                pdf_file = os.path.join(self.test_dir, f"test{ext}")
                with open(pdf_file, 'wb') as f:
                    f.write(b'%PDF-1.4\n%Test content')
                
                is_valid, message = gradio_app.validate_pdf_file(pdf_file)
                self.assertTrue(is_valid)
                self.assertEqual(message, "Valid PDF file")
    
    def test_validate_pdf_file_boundary_size(self):
        """Test validation with boundary file sizes"""
        # Test exactly 50MB
        boundary_pdf = os.path.join(self.test_dir, "boundary.pdf")
        with open(boundary_pdf, 'wb') as f:
            f.write(b'%PDF-1.4\n')
            f.write(b'x' * (50 * 1024 * 1024 - 9))  # Exactly 50MB including header
        
        is_valid, message = gradio_app.validate_pdf_file(boundary_pdf)
        self.assertTrue(is_valid)
        self.assertEqual(message, "Valid PDF file")
    
    def test_validate_pdf_file_permission_error(self):
        """Test validation with permission error"""
        with patch('os.path.getsize', side_effect=PermissionError("Access denied")):
            is_valid, message = gradio_app.validate_pdf_file(self.test_pdf)
            self.assertFalse(is_valid)
            self.assertIn("Validation error", message)
    
    def test_validate_pdf_file_io_error(self):
        """Test validation with IO error during header check"""
        with patch('builtins.open', side_effect=IOError("Read error")):
            is_valid, message = gradio_app.validate_pdf_file(self.test_pdf)
            self.assertFalse(is_valid)
            self.assertIn("Validation error", message)


class TestProcessPdfFile(unittest.TestCase):
    """Test PDF processing functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.test_pdf = os.path.join(self.test_dir, "test.pdf")
        
        # Create a valid PDF file
        with open(self.test_pdf, 'wb') as f:
            f.write(b'%PDF-1.4\n%Test PDF content')
        
        # Mock file object
        self.mock_file = MagicMock()
        self.mock_file.name = self.test_pdf
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
        # Clear temp dirs
        gradio_app._temp_dirs.clear()
    
    def test_process_pdf_file_no_file(self):
        """Test processing with no file provided"""
        status, content, download = gradio_app.process_pdf_file(None)
        
        self.assertIn("Please upload a PDF file", status)
        self.assertEqual(content, "")
        self.assertIsNone(download)
    
    @patch('gradio_app.DEPENDENCIES_AVAILABLE', False)
    def test_process_pdf_file_no_dependencies(self):
        """Test processing without dependencies"""
        status, content, download = gradio_app.process_pdf_file(self.mock_file)
        
        self.assertIn("Core dependencies not available", status)
        self.assertEqual(content, "")
        self.assertIsNone(download)
    
    @patch('gradio_app.GEMINI_API_KEY', None)
    def test_process_pdf_file_no_api_key(self):
        """Test processing without API key"""
        status, content, download = gradio_app.process_pdf_file(self.mock_file)
        
        self.assertIn("API key not configured", status)
        self.assertEqual(content, "")
        self.assertIsNone(download)
    
    @patch('gradio_app.validate_pdf_file')
    def test_process_pdf_file_invalid_pdf(self, mock_validate):
        """Test processing with invalid PDF"""
        mock_validate.return_value = (False, "Invalid PDF format")
        
        status, content, download = gradio_app.process_pdf_file(self.mock_file)
        
        self.assertIn("Invalid PDF format", status)
        self.assertEqual(content, "")
        self.assertIsNone(download)
    
    @patch('gradio_app.GEMINI_API_KEY', 'test_key')
    @patch('gradio_app.validate_config')
    @patch('gradio_app.validate_pdf_file')
    @patch('gradio_app.GeminiPDFOCR')
    def test_process_pdf_file_success(self, mock_ocr_class, mock_validate_pdf, mock_validate_config):
        """Test successful PDF processing"""
        # Setup mocks
        mock_validate_config.return_value = True
        mock_validate_pdf.return_value = (True, "Valid PDF file")
        
        mock_ocr = MagicMock()
        mock_ocr.process_pdf.return_value = ["Page 1 content", "Page 2 content"]
        mock_ocr_class.return_value = mock_ocr
        
        # Mock file operations
        with patch('tempfile.mkdtemp', side_effect=['/tmp/input', '/tmp/output']):
            with patch('shutil.copy2'):
                with patch('pathlib.Path.exists', return_value=True):
                    with patch('builtins.open', mock_open(read_data="# Processed content")):
                        with patch('shutil.copy2'):
                            status, content, download = gradio_app.process_pdf_file(self.mock_file, "custom prompt")
        
        self.assertIn("Successfully processed 2 pages", status)
        self.assertEqual(content, "# Processed content")
        self.assertIsNotNone(download)
    
    @patch('gradio_app.GEMINI_API_KEY', 'test_key')
    @patch('gradio_app.validate_config')
    @patch('gradio_app.validate_pdf_file')
    def test_process_pdf_file_config_error(self, mock_validate_pdf, mock_validate_config):
        """Test processing with configuration error"""
        mock_validate_pdf.return_value = (True, "Valid PDF file")
        mock_validate_config.side_effect = ValueError("Invalid config")
        
        status, content, download = gradio_app.process_pdf_file(self.mock_file)
        
        self.assertIn("Processing error", status)
        self.assertEqual(content, "")
        self.assertIsNone(download)
    
    def test_process_pdf_file_custom_prompt_handling(self):
        """Test custom prompt handling"""
        # Test empty prompt
        with patch('gradio_app.validate_pdf_file', return_value=(False, "Stop early")):
            gradio_app.process_pdf_file(self.mock_file, "")
        
        # Test whitespace-only prompt
        with patch('gradio_app.validate_pdf_file', return_value=(False, "Stop early")):
            gradio_app.process_pdf_file(self.mock_file, "   ")
        
        # Test valid prompt
        with patch('gradio_app.validate_pdf_file', return_value=(False, "Stop early")):
            gradio_app.process_pdf_file(self.mock_file, "Extract names and dates")


class TestCleanupTempDirs(unittest.TestCase):
    """Test temporary directory cleanup functionality"""
    
    def setUp(self):
        """Set up test environment"""
        gradio_app._temp_dirs.clear()
    
    def tearDown(self):
        """Clean up test environment"""
        gradio_app._temp_dirs.clear()
    
    def test_cleanup_temp_dirs_success(self):
        """Test successful cleanup of temporary directories"""
        # Create test directories
        temp_dirs = [tempfile.mkdtemp(), tempfile.mkdtemp()]
        gradio_app._temp_dirs.extend(temp_dirs)
        
        # Verify directories exist
        for temp_dir in temp_dirs:
            self.assertTrue(os.path.exists(temp_dir))
        
        # Cleanup
        gradio_app.cleanup_temp_dirs()
        
        # Verify directories are removed
        for temp_dir in temp_dirs:
            self.assertFalse(os.path.exists(temp_dir))
        
        # Verify list is cleared
        self.assertEqual(len(gradio_app._temp_dirs), 0)
    
    def test_cleanup_temp_dirs_nonexistent(self):
        """Test cleanup with non-existent directories"""
        # Add non-existent directories to list
        gradio_app._temp_dirs.extend(['/nonexistent/dir1', '/nonexistent/dir2'])
        
        # Should handle gracefully
        gradio_app.cleanup_temp_dirs()
        
        # List should be cleared
        self.assertEqual(len(gradio_app._temp_dirs), 0)
    
    def test_cleanup_temp_dirs_permission_error(self):
        """Test cleanup with permission errors"""
        temp_dir = tempfile.mkdtemp()
        gradio_app._temp_dirs.append(temp_dir)
        
        # Mock shutil.rmtree to raise permission error
        with patch('shutil.rmtree', side_effect=PermissionError("Access denied")):
            # Should handle error gracefully
            gradio_app.cleanup_temp_dirs()
        
        # List should still be cleared
        self.assertEqual(len(gradio_app._temp_dirs), 0)
        
        # Clean up manually
        try:
            shutil.rmtree(temp_dir)
        except:
            pass


class TestCreateInterface(unittest.TestCase):
    """Test Gradio interface creation"""
    
    @patch('gradio_app.gr')
    def test_create_interface_success(self, mock_gr):
        """Test successful interface creation"""
        # Mock Gradio components
        mock_blocks = MagicMock()
        mock_gr.Blocks.return_value.__enter__.return_value = mock_blocks
        
        interface = gradio_app.create_interface()
        
        # Should return the interface
        self.assertEqual(interface, mock_blocks)
        
        # Should call Gradio components
        mock_gr.Blocks.assert_called_once()
        mock_gr.Markdown.assert_called()
        mock_gr.File.assert_called()
        mock_gr.Textbox.assert_called()
        mock_gr.Button.assert_called()
    
    @patch('gradio_app.gr')
    def test_create_interface_component_configuration(self, mock_gr):
        """Test that interface components are configured correctly"""
        mock_blocks = MagicMock()
        mock_gr.Blocks.return_value.__enter__.return_value = mock_blocks
        
        gradio_app.create_interface()
        
        # Check that File component is configured for PDFs
        file_calls = [call for call in mock_gr.File.call_args_list]
        self.assertTrue(any('.pdf' in str(call) for call in file_calls))


class TestMainFunction(unittest.TestCase):
    """Test main function orchestration"""
    
    @patch('gradio_app.DEPENDENCIES_AVAILABLE', False)
    @patch('builtins.print')
    def test_main_missing_dependencies(self, mock_print):
        """Test main function with missing dependencies"""
        with self.assertRaises(SystemExit):
            gradio_app.main()
        
        # Should print error message
        print_calls = [str(call) for call in mock_print.call_args_list]
        error_found = any("Critical dependencies missing" in call_str for call_str in print_calls)
        self.assertTrue(error_found)
    
    @patch('gradio_app.GEMINI_API_KEY', None)
    @patch('gradio_app.find_free_port')
    @patch('gradio_app.create_interface')
    @patch('builtins.print')
    def test_main_missing_api_key_warning(self, mock_print, mock_create_interface, mock_find_port):
        """Test main function with missing API key shows warning"""
        mock_find_port.return_value = 7861
        mock_interface = MagicMock()
        mock_create_interface.return_value = mock_interface
        
        # Mock launch to avoid actually starting server
        mock_interface.launch.side_effect = KeyboardInterrupt("Stop test")
        
        with self.assertRaises(KeyboardInterrupt):
            gradio_app.main()
        
        # Should print warning about API key
        print_calls = [str(call) for call in mock_print.call_args_list]
        warning_found = any("GEMINI_API_KEY not configured" in call_str for call_str in print_calls)
        self.assertTrue(warning_found)
    
    @patch('gradio_app.find_free_port')
    def test_main_port_allocation_failure(self, mock_find_port):
        """Test main function with port allocation failure"""
        mock_find_port.side_effect = RuntimeError("No free port")
        
        with self.assertRaises(SystemExit):
            gradio_app.main()
    
    @patch('gradio_app.find_free_port')
    @patch('gradio_app.create_interface')
    def test_main_interface_creation_failure(self, mock_create_interface, mock_find_port):
        """Test main function with interface creation failure"""
        mock_find_port.return_value = 7861
        mock_create_interface.side_effect = Exception("Interface creation failed")
        
        with self.assertRaises(SystemExit):
            gradio_app.main()


if __name__ == '__main__':
    unittest.main(verbosity=2)