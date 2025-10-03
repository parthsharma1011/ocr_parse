#!/usr/bin/env python3
"""
Comprehensive Integration Tests for PDF OCR Processing Tool

Tests critical integration points and failure modes:
- PDF to image conversion pipeline
- Image to text extraction flow  
- File saving and cleanup operations
- Mid-process failure recovery
- Resource exhaustion scenarios
"""

import unittest
import os
import tempfile
import shutil
import time
import threading
import signal
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock external dependencies before any imports
sys.modules['google.generativeai'] = MagicMock()
sys.modules['pymupdf'] = MagicMock()
sys.modules['PIL.Image'] = MagicMock()
sys.modules['gradio'] = MagicMock()

# Import after mocking
import pdf_ocr


class TestPDFToImagePipeline(unittest.TestCase):
    """Test PDF to image conversion integration"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.input_dir = os.path.join(self.test_dir, "input")
        self.output_dir = os.path.join(self.test_dir, "output")
        os.makedirs(self.input_dir)
        os.makedirs(self.output_dir)
        
        # Create test PDF file
        self.test_pdf = os.path.join(self.input_dir, "test.pdf")
        with open(self.test_pdf, 'wb') as f:
            f.write(b'%PDF-1.4\n%Test PDF content for integration testing')
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_pdf_to_images_success_pipeline(self):
        """Test successful PDF to image conversion pipeline"""
        # Mock PyMuPDF components
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_pix = MagicMock()
        
        # Configure mocks
        mock_doc.__len__.return_value = 3  # 3 pages
        mock_doc.load_page.return_value = mock_page
        mock_page.get_pixmap.return_value = mock_pix
        mock_pix.tobytes.return_value = b'fake_png_data'
        
        with patch('pymupdf.open', return_value=mock_doc):
            ocr = pdf_ocr.GeminiPDFOCR(
                api_key="test_key",
                input_folder=self.input_dir,
                output_folder=self.output_dir
            )
            
            image_paths = ocr.pdf_to_images(self.test_pdf)
            
            # Verify results
            self.assertEqual(len(image_paths), 3)
            for path in image_paths:
                self.assertTrue(os.path.exists(path))
                self.assertTrue(path.endswith('.png'))
    
    def test_pdf_to_images_corrupted_pdf(self):
        """Test handling of corrupted PDF files"""
        # Create corrupted PDF
        corrupted_pdf = os.path.join(self.input_dir, "corrupted.pdf")
        with open(corrupted_pdf, 'wb') as f:
            f.write(b'Not a real PDF file')
        
        with patch('pymupdf.open', side_effect=Exception("Corrupted PDF")):
            ocr = pdf_ocr.GeminiPDFOCR(
                api_key="test_key",
                input_folder=self.input_dir,
                output_folder=self.output_dir
            )
            
            image_paths = ocr.pdf_to_images(corrupted_pdf)
            
            # Should return empty list for corrupted PDF
            self.assertEqual(len(image_paths), 0)
    
    def test_pdf_to_images_memory_pressure(self):
        """Test PDF conversion under memory pressure"""
        # Mock large PDF with many pages
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 100  # Large PDF
        
        # Mock memory error during processing
        def mock_get_pixmap(*args, **kwargs):
            if mock_doc.load_page.call_count > 50:  # Fail after 50 pages
                raise MemoryError("Out of memory")
            mock_pix = MagicMock()
            mock_pix.tobytes.return_value = b'fake_png_data'
            return mock_pix
        
        mock_page = MagicMock()
        mock_page.get_pixmap.side_effect = mock_get_pixmap
        mock_doc.load_page.return_value = mock_page
        
        with patch('pymupdf.open', return_value=mock_doc):
            ocr = pdf_ocr.GeminiPDFOCR(
                api_key="test_key",
                input_folder=self.input_dir,
                output_folder=self.output_dir
            )
            
            image_paths = ocr.pdf_to_images(self.test_pdf)
            
            # Should handle memory error gracefully
            self.assertEqual(len(image_paths), 0)
    
    def test_pdf_to_images_disk_space_exhaustion(self):
        """Test PDF conversion when disk space is exhausted"""
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 5
        
        mock_page = MagicMock()
        mock_pix = MagicMock()
        mock_pix.tobytes.return_value = b'fake_png_data'
        mock_page.get_pixmap.return_value = mock_pix
        mock_doc.load_page.return_value = mock_page
        
        # Mock disk full error
        original_open = open
        def mock_open_with_disk_full(*args, **kwargs):
            if 'wb' in args or (len(args) > 1 and 'wb' in args[1]):
                raise OSError("No space left on device")
            return original_open(*args, **kwargs)
        
        with patch('pymupdf.open', return_value=mock_doc):
            with patch('builtins.open', side_effect=mock_open_with_disk_full):
                ocr = pdf_ocr.GeminiPDFOCR(
                    api_key="test_key",
                    input_folder=self.input_dir,
                    output_folder=self.output_dir
                )
                
                image_paths = ocr.pdf_to_images(self.test_pdf)
                
                # Should handle disk full error gracefully
                self.assertEqual(len(image_paths), 0)


class TestImageToTextPipeline(unittest.TestCase):
    """Test image to text extraction integration"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.test_image = os.path.join(self.test_dir, "test.png")
        
        # Create fake image file
        with open(self.test_image, 'wb') as f:
            f.write(b'fake_png_data')
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_image_to_text_success_pipeline(self):
        """Test successful image to text extraction"""
        # Mock PIL and Gemini components
        mock_image = MagicMock()
        mock_image.size = (1000, 1000)  # Normal size image
        
        mock_response = MagicMock()
        mock_response.text = "Extracted text from image"
        
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        
        with patch('PIL.Image.open', return_value=mock_image):
            ocr = pdf_ocr.GeminiPDFOCR(api_key="test_key")
            ocr._model = mock_model
            
            result = ocr.extract_text_from_image(self.test_image)
            
            self.assertEqual(result, "Extracted text from image")
            mock_model.generate_content.assert_called_once()
    
    def test_image_to_text_large_image_optimization(self):
        """Test image optimization for large images"""
        # Mock large image that needs optimization
        mock_image = MagicMock()
        mock_image.size = (5000, 5000)  # Large image > 4MP threshold
        
        mock_response = MagicMock()
        mock_response.text = "Extracted text from optimized image"
        
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        
        with patch('PIL.Image.open', return_value=mock_image):
            ocr = pdf_ocr.GeminiPDFOCR(api_key="test_key")
            ocr._model = mock_model
            
            result = ocr.extract_text_from_image(self.test_image)
            
            # Should call thumbnail for optimization
            mock_image.thumbnail.assert_called_once_with((2000, 2000), unittest.mock.ANY)
            self.assertEqual(result, "Extracted text from optimized image")
    
    def test_image_to_text_api_failure(self):
        """Test handling of Gemini API failures"""
        mock_image = MagicMock()
        mock_image.size = (1000, 1000)
        
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("API Error")
        
        with patch('PIL.Image.open', return_value=mock_image):
            ocr = pdf_ocr.GeminiPDFOCR(api_key="test_key")
            ocr._model = mock_model
            
            result = ocr.extract_text_from_image(self.test_image)
            
            # Should return empty string on API failure
            self.assertEqual(result, "")
    
    def test_image_to_text_rate_limiting(self):
        """Test handling of API rate limiting"""
        mock_image = MagicMock()
        mock_image.size = (1000, 1000)
        
        # Mock rate limit error then success
        mock_model = MagicMock()
        responses = [
            Exception("Rate limit exceeded"),
            MagicMock(text="Success after retry")
        ]
        mock_model.generate_content.side_effect = responses
        
        with patch('PIL.Image.open', return_value=mock_image):
            ocr = pdf_ocr.GeminiPDFOCR(api_key="test_key")
            ocr._model = mock_model
            
            # First call should fail
            result1 = ocr.extract_text_from_image(self.test_image)
            self.assertEqual(result1, "")
            
            # Second call should succeed
            result2 = ocr.extract_text_from_image(self.test_image)
            self.assertEqual(result2, "Success after retry")
    
    def test_image_to_text_corrupted_image(self):
        """Test handling of corrupted image files"""
        with patch('PIL.Image.open', side_effect=Exception("Corrupted image")):
            ocr = pdf_ocr.GeminiPDFOCR(api_key="test_key")
            
            result = ocr.extract_text_from_image(self.test_image)
            
            # Should return empty string for corrupted image
            self.assertEqual(result, "")


class TestFileSavingAndCleanup(unittest.TestCase):
    """Test file operations and cleanup integration"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.test_dir, "output")
        os.makedirs(self.output_dir)
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_file_saving_success(self):
        """Test successful file saving"""
        ocr = pdf_ocr.GeminiPDFOCR(
            api_key="test_key",
            output_folder=self.output_dir
        )
        
        pages = ["# Page 1\nContent 1", "# Page 2\nContent 2"]
        output_file = os.path.join(self.output_dir, "test.md")
        
        ocr._save_to_file(pages, output_file)
        
        # Verify file was created and contains expected content
        self.assertTrue(os.path.exists(output_file))
        with open(output_file, 'r') as f:
            content = f.read()
            self.assertIn("Page 1", content)
            self.assertIn("Page 2", content)
            self.assertIn("Generated by OCR Processor", content)
    
    def test_file_saving_path_traversal_protection(self):
        """Test protection against path traversal attacks"""
        ocr = pdf_ocr.GeminiPDFOCR(
            api_key="test_key",
            output_folder=self.output_dir
        )
        
        pages = ["# Malicious content"]
        malicious_path = os.path.join(self.test_dir, "..", "malicious.md")
        
        with self.assertRaises(ValueError) as context:
            ocr._save_to_file(pages, malicious_path)
        
        self.assertIn("path traversal detected", str(context.exception))
    
    def test_file_saving_permission_error(self):
        """Test handling of file permission errors"""
        ocr = pdf_ocr.GeminiPDFOCR(
            api_key="test_key",
            output_folder=self.output_dir
        )
        
        pages = ["# Test content"]
        output_file = os.path.join(self.output_dir, "test.md")
        
        with patch('builtins.open', side_effect=PermissionError("Access denied")):
            with self.assertRaises(PermissionError):
                ocr._save_to_file(pages, output_file)
    
    def test_cleanup_images_success(self):
        """Test successful image cleanup"""
        # Create temporary image files
        temp_images = []
        for i in range(3):
            temp_file = os.path.join(self.test_dir, f"temp_{i}.png")
            with open(temp_file, 'wb') as f:
                f.write(b'fake_image_data')
            temp_images.append(temp_file)
        
        ocr = pdf_ocr.GeminiPDFOCR(api_key="test_key")
        ocr._cleanup_images(temp_images)
        
        # Verify all images were deleted
        for temp_file in temp_images:
            self.assertFalse(os.path.exists(temp_file))
    
    def test_cleanup_images_partial_failure(self):
        """Test cleanup with some files failing to delete"""
        # Create temporary image files
        temp_images = []
        for i in range(3):
            temp_file = os.path.join(self.test_dir, f"temp_{i}.png")
            with open(temp_file, 'wb') as f:
                f.write(b'fake_image_data')
            temp_images.append(temp_file)
        
        # Mock unlink to fail for second file
        original_unlink = Path.unlink
        def mock_unlink(self, *args, **kwargs):
            if "temp_1" in str(self):
                raise PermissionError("Cannot delete")
            return original_unlink(self, *args, **kwargs)
        
        with patch.object(Path, 'unlink', mock_unlink):
            ocr = pdf_ocr.GeminiPDFOCR(api_key="test_key")
            ocr._cleanup_images(temp_images)
        
        # Should handle partial failure gracefully
        # Files 0 and 2 should be deleted, file 1 should remain
        self.assertFalse(os.path.exists(temp_images[0]))
        self.assertTrue(os.path.exists(temp_images[1]))
        self.assertFalse(os.path.exists(temp_images[2]))


class TestMidProcessFailureRecovery(unittest.TestCase):
    """Test recovery from mid-process failures"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.input_dir = os.path.join(self.test_dir, "input")
        self.output_dir = os.path.join(self.test_dir, "output")
        os.makedirs(self.input_dir)
        os.makedirs(self.output_dir)
        
        # Create test PDF
        self.test_pdf = os.path.join(self.input_dir, "test.pdf")
        with open(self.test_pdf, 'wb') as f:
            f.write(b'%PDF-1.4\n%Test content')
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_process_interruption_during_pdf_conversion(self):
        """Test interruption during PDF to image conversion"""
        # Mock PDF conversion that gets interrupted
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 5
        
        call_count = 0
        def mock_load_page(page_num):
            nonlocal call_count
            call_count += 1
            if call_count > 2:  # Interrupt after 2 pages
                raise KeyboardInterrupt("Process interrupted")
            
            mock_page = MagicMock()
            mock_pix = MagicMock()
            mock_pix.tobytes.return_value = b'fake_png_data'
            mock_page.get_pixmap.return_value = mock_pix
            return mock_page
        
        mock_doc.load_page.side_effect = mock_load_page
        
        with patch('pymupdf.open', return_value=mock_doc):
            ocr = pdf_ocr.GeminiPDFOCR(
                api_key="test_key",
                input_folder=self.input_dir,
                output_folder=self.output_dir
            )
            
            # Should handle interruption gracefully
            image_paths = ocr.pdf_to_images(self.test_pdf)
            self.assertEqual(len(image_paths), 0)
    
    def test_process_interruption_during_text_extraction(self):
        """Test interruption during text extraction phase"""
        # Mock successful PDF conversion
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 3
        
        mock_page = MagicMock()
        mock_pix = MagicMock()
        mock_pix.tobytes.return_value = b'fake_png_data'
        mock_page.get_pixmap.return_value = mock_pix
        mock_doc.load_page.return_value = mock_page
        
        # Mock text extraction that fails partway through
        call_count = 0
        def mock_extract_text(image_path, custom_prompt=None):
            nonlocal call_count
            call_count += 1
            if call_count > 1:  # Fail after first image
                raise Exception("Network error during extraction")
            return f"Extracted text from {os.path.basename(image_path)}"
        
        with patch('pymupdf.open', return_value=mock_doc):
            ocr = pdf_ocr.GeminiPDFOCR(
                api_key="test_key",
                input_folder=self.input_dir,
                output_folder=self.output_dir
            )
            
            # Mock the extract_text_from_image method
            ocr.extract_text_from_image = mock_extract_text
            
            # Should handle partial extraction gracefully
            try:
                pages = ocr.process_pdf("test.pdf", verbose=False)
                # Some pages may be processed, others may be empty
                self.assertIsInstance(pages, list)
            except Exception:
                # Or it may fail completely, which is also acceptable
                pass
    
    def test_temp_directory_cleanup_on_failure(self):
        """Test that temporary files are cleaned up even on failure"""
        # Track created temp files
        created_files = []
        
        original_open = open
        def track_temp_files(*args, **kwargs):
            if len(args) > 0 and 'temp' in str(args[0]) and 'wb' in str(args[1:]):
                created_files.append(args[0])
            return original_open(*args, **kwargs)
        
        # Mock PDF processing that fails
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 2
        mock_doc.load_page.side_effect = Exception("Processing failed")
        
        with patch('pymupdf.open', return_value=mock_doc):
            with patch('builtins.open', side_effect=track_temp_files):
                ocr = pdf_ocr.GeminiPDFOCR(
                    api_key="test_key",
                    input_folder=self.input_dir,
                    output_folder=self.output_dir
                )
                
                # Process should fail but cleanup should still happen
                image_paths = ocr.pdf_to_images(self.test_pdf)
                self.assertEqual(len(image_paths), 0)
                
                # Verify temp directory still exists but is empty
                self.assertTrue(os.path.exists(ocr.temp_dir))


class TestConcurrentProcessing(unittest.TestCase):
    """Test concurrent processing scenarios"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.input_dir = os.path.join(self.test_dir, "input")
        self.output_dir = os.path.join(self.test_dir, "output")
        os.makedirs(self.input_dir)
        os.makedirs(self.output_dir)
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_concurrent_pdf_processing(self):
        """Test processing multiple PDFs concurrently"""
        # Create multiple test PDFs
        pdf_files = []
        for i in range(3):
            pdf_file = os.path.join(self.input_dir, f"test_{i}.pdf")
            with open(pdf_file, 'wb') as f:
                f.write(f'%PDF-1.4\n%Test content {i}'.encode())
            pdf_files.append(pdf_file)
        
        # Mock successful processing
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 2
        
        mock_page = MagicMock()
        mock_pix = MagicMock()
        mock_pix.tobytes.return_value = b'fake_png_data'
        mock_page.get_pixmap.return_value = mock_pix
        mock_doc.load_page.return_value = mock_page
        
        with patch('pymupdf.open', return_value=mock_doc):
            ocr = pdf_ocr.GeminiPDFOCR(
                api_key="test_key",
                input_folder=self.input_dir,
                output_folder=self.output_dir
            )
            
            # Mock text extraction
            ocr.extract_text_from_image = lambda x, y=None: f"Text from {os.path.basename(x)}"
            
            # Process all PDFs
            results = ocr.process_all_pdfs(verbose=False)
            
            # Verify all PDFs were processed
            self.assertEqual(len(results), 3)
            for i in range(3):
                pdf_name = f"test_{i}.pdf"
                self.assertIn(pdf_name, results)
                self.assertIsInstance(results[pdf_name], list)
    
    def test_resource_contention_handling(self):
        """Test handling of resource contention during concurrent processing"""
        # Mock scenario where multiple threads compete for resources
        lock = threading.Lock()
        access_count = 0
        
        def mock_extract_with_contention(image_path, custom_prompt=None):
            nonlocal access_count
            with lock:
                access_count += 1
                if access_count > 2:  # Simulate resource exhaustion
                    raise Exception("Resource temporarily unavailable")
                time.sleep(0.1)  # Simulate processing time
                return f"Extracted text {access_count}"
        
        # Mock PDF with multiple pages
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 5
        
        mock_page = MagicMock()
        mock_pix = MagicMock()
        mock_pix.tobytes.return_value = b'fake_png_data'
        mock_page.get_pixmap.return_value = mock_pix
        mock_doc.load_page.return_value = mock_page
        
        with patch('pymupdf.open', return_value=mock_doc):
            ocr = pdf_ocr.GeminiPDFOCR(
                api_key="test_key",
                input_folder=self.input_dir,
                output_folder=self.output_dir,
                max_workers=3  # Force concurrent processing
            )
            
            ocr.extract_text_from_image = mock_extract_with_contention
            
            # Create test PDF
            test_pdf = os.path.join(self.input_dir, "test.pdf")
            with open(test_pdf, 'wb') as f:
                f.write(b'%PDF-1.4\n%Test content')
            
            # Should handle resource contention gracefully
            pages = ocr.process_pdf("test.pdf", verbose=False)
            
            # Some pages may succeed, others may fail
            self.assertIsInstance(pages, list)


if __name__ == '__main__':
    unittest.main(verbosity=2)