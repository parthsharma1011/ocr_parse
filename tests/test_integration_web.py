#!/usr/bin/env python3
"""
Web Interface Integration Tests

Tests integration between Gradio frontend and OCR backend:
- End-to-end file upload to processing pipeline
- Temporary file management across components
- Error propagation through web interface
- Resource cleanup in web context
"""

import unittest
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock external dependencies before imports
sys.modules['google.generativeai'] = MagicMock()
sys.modules['pymupdf'] = MagicMock()
sys.modules['PIL.Image'] = MagicMock()
sys.modules['gradio'] = MagicMock()

# Import gradio_app after mocking
try:
    import gradio_app
except ImportError:
    # Create mock gradio_app if import fails
    gradio_app = MagicMock()
    gradio_app._temp_dirs = []
    gradio_app.cleanup_temp_dirs = MagicMock()
    gradio_app.process_pdf_file = MagicMock()
    gradio_app.find_free_port = MagicMock(return_value=7861)

import pdf_ocr


class TestEndToEndWebWorkflow(unittest.TestCase):
    """Test complete web interface workflow"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.test_pdf = os.path.join(self.test_dir, "test.pdf")
        
        # Create valid test PDF
        with open(self.test_pdf, 'wb') as f:
            f.write(b'%PDF-1.4\n%Test PDF for web integration')
        
        # Mock file object for Gradio
        self.mock_file = MagicMock()
        self.mock_file.name = self.test_pdf
        
        # Clear temp dirs before test
        gradio_app._temp_dirs.clear()
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
        gradio_app.cleanup_temp_dirs()
    
    @patch('gradio_app.GEMINI_API_KEY', 'test_key')
    @patch('gradio_app.validate_config')
    @patch('gradio_app.validate_pdf_file')
    def test_complete_upload_to_download_workflow(self, mock_validate_pdf, mock_validate_config):
        """Test complete workflow from upload to download"""
        # Setup mocks
        mock_validate_config.return_value = True
        mock_validate_pdf.return_value = (True, "Valid PDF file")
        
        # Mock OCR processing
        mock_ocr = MagicMock()
        mock_ocr.process_pdf.return_value = ["# Page 1\nExtracted content"]
        
        # Mock temporary directories
        temp_input = os.path.join(self.test_dir, "temp_input")
        temp_output = os.path.join(self.test_dir, "temp_output")
        os.makedirs(temp_input)
        os.makedirs(temp_output)
        
        # Create expected output file
        output_file = os.path.join(temp_output, "test.md")
        with open(output_file, 'w') as f:
            f.write("# Page 1\nExtracted content")
        
        with patch('tempfile.mkdtemp', side_effect=[temp_input, temp_output]):
            with patch('shutil.copy2'):
                with patch('gradio_app.GeminiPDFOCR', return_value=mock_ocr):
                    with patch('pathlib.Path.exists', return_value=True):
                        with patch('builtins.open', mock_open(read_data="# Page 1\nExtracted content")):
                            with patch('shutil.copy2'):
                                status, content, download = gradio_app.process_pdf_file(
                                    self.mock_file, "Extract all text"
                                )
        
        # Verify successful processing
        self.assertIn("Successfully processed 1 pages", status)
        self.assertEqual(content, "# Page 1\nExtracted content")
        self.assertIsNotNone(download)
    
    def test_workflow_interruption_cleanup(self):
        """Test cleanup when workflow is interrupted"""
        # Mock validation success
        with patch('gradio_app.validate_pdf_file', return_value=(True, "Valid")):
            with patch('gradio_app.validate_config', return_value=True):
                with patch('gradio_app.GEMINI_API_KEY', 'test_key'):
                    
                    # Mock tempfile creation to track directories
                    created_dirs = []
                    def mock_mkdtemp(*args, **kwargs):
                        temp_dir = tempfile.mkdtemp()
                        created_dirs.append(temp_dir)
                        gradio_app._temp_dirs.append(temp_dir)
                        return temp_dir
                    
                    # Mock OCR to fail after temp dirs are created
                    mock_ocr = MagicMock()
                    mock_ocr.process_pdf.side_effect = Exception("Processing failed")
                    
                    with patch('tempfile.mkdtemp', side_effect=mock_mkdtemp):
                        with patch('shutil.copy2'):
                            with patch('gradio_app.GeminiPDFOCR', return_value=mock_ocr):
                                
                                status, content, download = gradio_app.process_pdf_file(self.mock_file)
                    
                    # Verify error handling
                    self.assertIn("Processing error", status)
                    self.assertEqual(content, "")
                    self.assertIsNone(download)
                    
                    # Verify temp directories were tracked
                    self.assertGreater(len(created_dirs), 0)
                    
                    # Cleanup should remove all temp directories
                    gradio_app.cleanup_temp_dirs()
                    for temp_dir in created_dirs:
                        self.assertFalse(os.path.exists(temp_dir))
    
    def test_concurrent_web_requests(self):
        """Test handling of concurrent web requests"""
        import threading
        import time
        
        results = []
        errors = []
        
        def process_request(request_id):
            try:
                mock_file = MagicMock()
                mock_file.name = self.test_pdf
                
                with patch('gradio_app.validate_pdf_file', return_value=(True, "Valid")):
                    with patch('gradio_app.GEMINI_API_KEY', 'test_key'):
                        with patch('gradio_app.validate_config', return_value=True):
                            
                            # Mock OCR with delay to simulate processing
                            mock_ocr = MagicMock()
                            def mock_process(*args, **kwargs):
                                time.sleep(0.1)  # Simulate processing time
                                return [f"Content from request {request_id}"]
                            mock_ocr.process_pdf.side_effect = mock_process
                            
                            with patch('tempfile.mkdtemp', return_value=self.test_dir):
                                with patch('shutil.copy2'):
                                    with patch('gradio_app.GeminiPDFOCR', return_value=mock_ocr):
                                        with patch('pathlib.Path.exists', return_value=True):
                                            with patch('builtins.open', mock_open(read_data=f"Result {request_id}")):
                                                
                                                status, content, download = gradio_app.process_pdf_file(mock_file)
                                                results.append((request_id, status, content))
                            
            except Exception as e:
                errors.append((request_id, str(e)))
        
        # Start multiple concurrent requests
        threads = []
        for i in range(3):
            thread = threading.Thread(target=process_request, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=5)
        
        # Verify results
        self.assertEqual(len(results), 3)
        self.assertEqual(len(errors), 0)
        
        # Verify each request was processed
        for request_id, status, content in results:
            self.assertIn("Successfully processed", status)


class TestResourceManagementIntegration(unittest.TestCase):
    """Test resource management across components"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        gradio_app._temp_dirs.clear()
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
        gradio_app.cleanup_temp_dirs()
    
    def test_temp_directory_lifecycle(self):
        """Test temporary directory creation and cleanup lifecycle"""
        # Track temp directory creation
        created_dirs = []
        
        def track_mkdtemp(*args, **kwargs):
            temp_dir = tempfile.mkdtemp()
            created_dirs.append(temp_dir)
            gradio_app._temp_dirs.append(temp_dir)
            return temp_dir
        
        # Create some temp directories
        with patch('tempfile.mkdtemp', side_effect=track_mkdtemp):
            # Simulate multiple operations creating temp dirs
            for i in range(3):
                temp_dir = tempfile.mkdtemp()
                # Create some files in temp directory
                test_file = os.path.join(temp_dir, f"test_{i}.txt")
                with open(test_file, 'w') as f:
                    f.write(f"Test content {i}")
        
        # Verify directories were created and tracked
        self.assertEqual(len(created_dirs), 3)
        for temp_dir in created_dirs:
            self.assertTrue(os.path.exists(temp_dir))
        
        # Cleanup should remove all directories
        gradio_app.cleanup_temp_dirs()
        
        for temp_dir in created_dirs:
            self.assertFalse(os.path.exists(temp_dir))
        
        # Verify tracking list is cleared
        self.assertEqual(len(gradio_app._temp_dirs), 0)
    
    def test_memory_pressure_handling(self):
        """Test handling of memory pressure during processing"""
        # Mock scenario with limited memory
        mock_file = MagicMock()
        mock_file.name = os.path.join(self.test_dir, "large.pdf")
        
        # Create large fake PDF
        with open(mock_file.name, 'wb') as f:
            f.write(b'%PDF-1.4\n')
            f.write(b'x' * (10 * 1024 * 1024))  # 10MB file
        
        # Mock memory error during processing
        with patch('gradio_app.validate_pdf_file', return_value=(True, "Valid")):
            with patch('gradio_app.GEMINI_API_KEY', 'test_key'):
                with patch('gradio_app.validate_config', return_value=True):
                    
                    mock_ocr = MagicMock()
                    mock_ocr.process_pdf.side_effect = MemoryError("Out of memory")
                    
                    with patch('tempfile.mkdtemp', return_value=self.test_dir):
                        with patch('shutil.copy2'):
                            with patch('gradio_app.GeminiPDFOCR', return_value=mock_ocr):
                                
                                status, content, download = gradio_app.process_pdf_file(mock_file)
        
        # Should handle memory error gracefully
        self.assertIn("Processing error", status)
        self.assertEqual(content, "")
        self.assertIsNone(download)
    
    def test_disk_space_exhaustion(self):
        """Test handling when disk space is exhausted"""
        mock_file = MagicMock()
        mock_file.name = os.path.join(self.test_dir, "test.pdf")
        
        with open(mock_file.name, 'wb') as f:
            f.write(b'%PDF-1.4\n%Test content')
        
        # Mock disk full error during temp file operations
        def mock_copy_with_disk_full(*args, **kwargs):
            raise OSError("No space left on device")
        
        with patch('gradio_app.validate_pdf_file', return_value=(True, "Valid")):
            with patch('gradio_app.GEMINI_API_KEY', 'test_key'):
                with patch('gradio_app.validate_config', return_value=True):
                    with patch('tempfile.mkdtemp', return_value=self.test_dir):
                        with patch('shutil.copy2', side_effect=mock_copy_with_disk_full):
                            
                            status, content, download = gradio_app.process_pdf_file(mock_file)
        
        # Should handle disk full error gracefully
        self.assertIn("Processing error", status)
        self.assertEqual(content, "")
        self.assertIsNone(download)


class TestErrorPropagationIntegration(unittest.TestCase):
    """Test error propagation through the system"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.test_pdf = os.path.join(self.test_dir, "test.pdf")
        
        with open(self.test_pdf, 'wb') as f:
            f.write(b'%PDF-1.4\n%Test content')
        
        self.mock_file = MagicMock()
        self.mock_file.name = self.test_pdf
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
        gradio_app.cleanup_temp_dirs()
    
    def test_api_error_propagation(self):
        """Test how API errors propagate through the web interface"""
        with patch('gradio_app.validate_pdf_file', return_value=(True, "Valid")):
            with patch('gradio_app.GEMINI_API_KEY', 'test_key'):
                with patch('gradio_app.validate_config', return_value=True):
                    
                    # Mock API error
                    mock_ocr = MagicMock()
                    mock_ocr.process_pdf.side_effect = Exception("API rate limit exceeded")
                    
                    with patch('tempfile.mkdtemp', return_value=self.test_dir):
                        with patch('shutil.copy2'):
                            with patch('gradio_app.GeminiPDFOCR', return_value=mock_ocr):
                                
                                status, content, download = gradio_app.process_pdf_file(self.mock_file)
        
        # Should propagate API error with user-friendly message
        self.assertIn("Processing error", status)
        self.assertIn("API rate limit exceeded", status)
        self.assertEqual(content, "")
        self.assertIsNone(download)
    
    def test_file_system_error_propagation(self):
        """Test how file system errors propagate"""
        with patch('gradio_app.validate_pdf_file', return_value=(True, "Valid")):
            with patch('gradio_app.GEMINI_API_KEY', 'test_key'):
                with patch('gradio_app.validate_config', return_value=True):
                    
                    # Mock file system error
                    with patch('tempfile.mkdtemp', side_effect=OSError("Permission denied")):
                        
                        status, content, download = gradio_app.process_pdf_file(self.mock_file)
        
        # Should handle file system error gracefully
        self.assertIn("Processing error", status)
        self.assertEqual(content, "")
        self.assertIsNone(download)
    
    def test_network_error_propagation(self):
        """Test how network errors propagate"""
        with patch('gradio_app.validate_pdf_file', return_value=(True, "Valid")):
            with patch('gradio_app.GEMINI_API_KEY', 'test_key'):
                with patch('gradio_app.validate_config', side_effect=Exception("Network timeout")):
                    
                    status, content, download = gradio_app.process_pdf_file(self.mock_file)
        
        # Should handle network error gracefully
        self.assertIn("Processing error", status)
        self.assertEqual(content, "")
        self.assertIsNone(download)


class TestPortAllocationIntegration(unittest.TestCase):
    """Test port allocation and web server integration"""
    
    def test_port_allocation_under_load(self):
        """Test port allocation when many ports are in use"""
        # Mock socket to simulate many ports in use
        used_ports = set(range(7860, 7870))  # First 10 ports in use
        
        def mock_bind(address):
            host, port = address
            if port in used_ports:
                raise OSError("Address already in use")
        
        with patch('socket.socket') as mock_socket:
            mock_socket.return_value.__enter__.return_value.bind.side_effect = mock_bind
            
            # Should find available port outside used range
            port = gradio_app.find_free_port(start_port=7860, max_attempts=20)
            self.assertNotIn(port, used_ports)
            self.assertGreaterEqual(port, 7870)
    
    def test_port_exhaustion_handling(self):
        """Test handling when all ports in range are exhausted"""
        # Mock all ports as in use
        with patch('socket.socket') as mock_socket:
            mock_socket.return_value.__enter__.return_value.bind.side_effect = OSError("Address already in use")
            
            with self.assertRaises(RuntimeError) as context:
                gradio_app.find_free_port(start_port=7860, max_attempts=5)
            
            self.assertIn("No free port found", str(context.exception))


if __name__ == '__main__':
    unittest.main(verbosity=2)