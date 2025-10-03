#!/usr/bin/env python3
"""
Comprehensive Unit Tests for Call Module

Tests all critical functions in call.py including:
- Directory information gathering
- Setup validation
- Folder creation and file management
- Main orchestration logic
"""

import unittest
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, call
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock the imports that might not be available in test environment
sys.modules['pdf_ocr'] = MagicMock()

import call_module as call  # Import as call to avoid conflicts


class TestGetDirectoryInfo(unittest.TestCase):
    """Test directory information gathering functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.original_cwd = os.getcwd()
        self.test_dir = tempfile.mkdtemp()
        os.chdir(self.test_dir)
        
        # Clear cache before each test
        call._get_directory_info.cache_clear()
        
        # Create test files and directories
        self.create_test_structure()
    
    def tearDown(self):
        """Clean up test environment"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def create_test_structure(self):
        """Create test directory structure"""
        # Create test files
        test_files = ['test.py', 'config.py', 'document.pdf', 'image.jpg']
        for file_name in test_files:
            Path(file_name).touch()
        
        # Create test directories
        test_dirs = ['Data', 'Output', 'tests']
        for dir_name in test_dirs:
            Path(dir_name).mkdir()
        
        # Create PDF files in Data directory
        data_pdfs = ['doc1.pdf', 'doc2.pdf']
        for pdf_name in data_pdfs:
            (Path('Data') / pdf_name).touch()
    
    def test_get_directory_info_success(self):
        """Test successful directory information gathering"""
        info = call._get_directory_info()
        
        # Check return structure
        expected_keys = ['current_dir', 'data_folder', 'output_folder', 
                        'current_files', 'current_dirs', 'current_pdfs', 'pdf_files']
        for key in expected_keys:
            self.assertIn(key, info)
        
        # Check current directory
        self.assertEqual(info['current_dir'], Path.cwd())
        
        # Check folders
        self.assertEqual(info['data_folder'], Path.cwd() / 'Data')
        self.assertEqual(info['output_folder'], Path.cwd() / 'Output')
        
        # Check files
        self.assertIn('test.py', info['current_files'])
        self.assertIn('document.pdf', info['current_files'])
        self.assertIn('document.pdf', info['current_pdfs'])
        
        # Check directories
        self.assertIn('Data', info['current_dirs'])
        self.assertIn('Output', info['current_dirs'])
        
        # Check PDF files in Data folder
        self.assertIn('doc1.pdf', info['pdf_files'])
        self.assertIn('doc2.pdf', info['pdf_files'])
    
    def test_get_directory_info_empty_directory(self):
        """Test directory info with empty directory"""
        # Clear test directory
        for item in Path('.').iterdir():
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
        
        call._get_directory_info.cache_clear()
        info = call._get_directory_info()
        
        self.assertEqual(len(info['current_files']), 0)
        self.assertEqual(len(info['current_dirs']), 0)
        self.assertEqual(len(info['current_pdfs']), 0)
        self.assertEqual(len(info['pdf_files']), 0)
    
    def test_get_directory_info_no_data_folder(self):
        """Test directory info when Data folder doesn't exist"""
        # Remove Data folder
        shutil.rmtree('Data')
        
        call._get_directory_info.cache_clear()
        info = call._get_directory_info()
        
        self.assertFalse(info['data_folder'].exists())
        self.assertEqual(len(info['pdf_files']), 0)
    
    def test_get_directory_info_permission_error_current_dir(self):
        """Test handling of permission errors in current directory"""
        with patch('pathlib.Path.iterdir', side_effect=PermissionError("Access denied")):
            call._get_directory_info.cache_clear()
            info = call._get_directory_info()
            
            # Should handle error gracefully
            self.assertEqual(len(info['current_files']), 0)
            self.assertEqual(len(info['current_dirs']), 0)
            self.assertEqual(len(info['current_pdfs']), 0)
    
    def test_get_directory_info_permission_error_data_folder(self):
        """Test handling of permission errors in data folder"""
        with patch('pathlib.Path.glob', side_effect=PermissionError("Access denied")):
            call._get_directory_info.cache_clear()
            info = call._get_directory_info()
            
            # Should handle error gracefully
            self.assertEqual(len(info['pdf_files']), 0)
    
    def test_get_directory_info_caching(self):
        """Test that directory info is cached"""
        # First call
        info1 = call._get_directory_info()
        
        # Add a new file
        Path('new_file.txt').touch()
        
        # Second call should return cached result
        info2 = call._get_directory_info()
        
        # Should be the same (cached)
        self.assertEqual(info1['current_files'], info2['current_files'])
        self.assertNotIn('new_file.txt', info2['current_files'])
        
        # Clear cache and call again
        call._get_directory_info.cache_clear()
        info3 = call._get_directory_info()
        
        # Now should include new file
        self.assertIn('new_file.txt', info3['current_files'])
    
    def test_get_directory_info_mixed_file_types(self):
        """Test directory info with various file types"""
        # Create files with different extensions
        file_types = ['.txt', '.py', '.pdf', '.jpg', '.md', '.json']
        for i, ext in enumerate(file_types):
            Path(f'file{i}{ext}').touch()
        
        call._get_directory_info.cache_clear()
        info = call._get_directory_info()
        
        # Check that only PDF files are in current_pdfs
        pdf_files = [f for f in info['current_pdfs'] if f.endswith('.pdf')]
        self.assertEqual(len(pdf_files), len([f for f in info['current_pdfs']]))
    
    def test_get_directory_info_case_insensitive_pdf(self):
        """Test PDF detection is case insensitive"""
        # Create PDF files with different cases
        pdf_files = ['test.pdf', 'TEST.PDF', 'Test.Pdf', 'document.pDf']
        for pdf_file in pdf_files:
            Path(pdf_file).touch()
        
        call._get_directory_info.cache_clear()
        info = call._get_directory_info()
        
        # All should be detected as PDFs
        for pdf_file in pdf_files:
            self.assertIn(pdf_file, info['current_pdfs'])


class TestCheckSetup(unittest.TestCase):
    """Test setup checking functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.original_cwd = os.getcwd()
        self.test_dir = tempfile.mkdtemp()
        os.chdir(self.test_dir)
        call._get_directory_info.cache_clear()
    
    def tearDown(self):
        """Clean up test environment"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    @patch('builtins.print')
    def test_check_setup_basic_output(self, mock_print):
        """Test basic setup check output"""
        # Create basic structure
        Path('Data').mkdir()
        Path('Output').mkdir()
        Path('test.py').touch()
        
        call.check_setup()
        
        # Verify print calls
        print_calls = [str(call_obj) for call_obj in mock_print.call_args_list]
        
        # Check for expected output patterns
        setup_check_found = any("Setup Check" in call_str for call_str in print_calls)
        self.assertTrue(setup_check_found)
        
        current_dir_found = any("Current directory:" in call_str for call_str in print_calls)
        self.assertTrue(current_dir_found)
    
    @patch('builtins.print')
    def test_check_setup_with_pdfs(self, mock_print):
        """Test setup check with PDF files"""
        # Create structure with PDFs
        Path('Data').mkdir()
        (Path('Data') / 'doc1.pdf').touch()
        (Path('Data') / 'doc2.pdf').touch()
        Path('current.pdf').touch()  # PDF in current directory
        
        call.check_setup()
        
        print_calls = [str(call_obj) for call_obj in mock_print.call_args_list]
        
        # Should mention PDF files
        pdf_mention_found = any("PDF files" in call_str for call_str in print_calls)
        self.assertTrue(pdf_mention_found)
    
    @patch('builtins.print')
    def test_check_setup_no_data_folder(self, mock_print):
        """Test setup check when Data folder doesn't exist"""
        # Don't create Data folder
        call.check_setup()
        
        print_calls = [str(call_obj) for call_obj in mock_print.call_args_list]
        
        # Should mention missing folder
        missing_folder_found = any("doesn't exist" in call_str for call_str in print_calls)
        self.assertTrue(missing_folder_found)


class TestSetupFolders(unittest.TestCase):
    """Test folder setup functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.original_cwd = os.getcwd()
        self.test_dir = tempfile.mkdtemp()
        os.chdir(self.test_dir)
        call._get_directory_info.cache_clear()
    
    def tearDown(self):
        """Clean up test environment"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    @patch('builtins.print')
    def test_setup_folders_creates_directories(self, mock_print):
        """Test that setup_folders creates necessary directories"""
        # Ensure directories don't exist
        self.assertFalse(Path('Data').exists())
        self.assertFalse(Path('Output').exists())
        
        call.setup_folders()
        
        # Check directories were created
        self.assertTrue(Path('Data').exists())
        self.assertTrue(Path('Output').exists())
        self.assertTrue(Path('Data').is_dir())
        self.assertTrue(Path('Output').is_dir())
    
    @patch('builtins.print')
    def test_setup_folders_moves_pdfs(self, mock_print):
        """Test that setup_folders moves PDF files to Data directory"""
        # Create PDF files in current directory
        pdf_files = ['doc1.pdf', 'doc2.pdf', 'report.pdf']
        for pdf_file in pdf_files:
            Path(pdf_file).touch()
        
        call.setup_folders()
        
        # Check PDFs were moved to Data directory
        for pdf_file in pdf_files:
            self.assertFalse(Path(pdf_file).exists())  # No longer in current dir
            self.assertTrue((Path('Data') / pdf_file).exists())  # Now in Data dir
    
    @patch('builtins.print')
    def test_setup_folders_handles_move_errors(self, mock_print):
        """Test that setup_folders handles file move errors gracefully"""
        # Create a PDF file
        Path('test.pdf').touch()
        
        # Mock rename to raise an exception
        with patch('pathlib.Path.rename', side_effect=OSError("Permission denied")):
            call.setup_folders()
            
            # Should handle error gracefully
            print_calls = [str(call_obj) for call_obj in mock_print.call_args_list]
            error_found = any("Error moving" in call_str for call_str in print_calls)
            self.assertTrue(error_found)
    
    @patch('builtins.print')
    def test_setup_folders_clears_cache_after_move(self, mock_print):
        """Test that cache is cleared after moving files"""
        # Create PDF file
        Path('test.pdf').touch()
        
        # Get initial directory info (should cache it)
        info1 = call._get_directory_info()
        self.assertIn('test.pdf', info1['current_pdfs'])
        
        # Setup folders (should move PDF and clear cache)
        call.setup_folders()
        
        # Get directory info again (should be fresh, not cached)
        info2 = call._get_directory_info()
        self.assertNotIn('test.pdf', info2['current_pdfs'])
    
    @patch('builtins.print')
    def test_setup_folders_no_pdfs_to_move(self, mock_print):
        """Test setup_folders when no PDFs need to be moved"""
        # Create only non-PDF files
        Path('test.txt').touch()
        Path('config.py').touch()
        
        call.setup_folders()
        
        # Should still create directories
        self.assertTrue(Path('Data').exists())
        self.assertTrue(Path('Output').exists())
        
        # Should not mention moving files
        print_calls = [str(call_obj) for call_obj in mock_print.call_args_list]
        move_mention = any("Found" in call_str and "PDF file" in call_str for call_str in print_calls)
        self.assertFalse(move_mention)


class TestMainFunction(unittest.TestCase):
    """Test main orchestration function"""
    
    def setUp(self):
        """Set up test environment"""
        self.original_cwd = os.getcwd()
        self.test_dir = tempfile.mkdtemp()
        os.chdir(self.test_dir)
    
    def tearDown(self):
        """Clean up test environment"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    @patch('call_module.validate_config')
    @patch('call_module.check_setup')
    @patch('call_module.setup_folders')
    @patch('builtins.print')
    def test_main_config_validation_error(self, mock_print, mock_setup_folders, 
                                         mock_check_setup, mock_validate_config):
        """Test main function with configuration validation error"""
        mock_validate_config.side_effect = ValueError("API key missing")
        
        call.main()
        
        # Should call validate_config but not proceed further
        mock_validate_config.assert_called_once()
        mock_check_setup.assert_not_called()
        mock_setup_folders.assert_not_called()
        
        # Should print error message
        print_calls = [str(call_obj) for call_obj in mock_print.call_args_list]
        error_found = any("Configuration error" in call_str for call_str in print_calls)
        self.assertTrue(error_found)
    
    @patch('call_module.validate_config')
    @patch('call_module.check_setup')
    @patch('call_module.setup_folders')
    @patch('builtins.print')
    def test_main_import_error(self, mock_print, mock_setup_folders, 
                              mock_check_setup, mock_validate_config):
        """Test main function with import error"""
        mock_validate_config.return_value = True
        
        # Mock import error for pdf_ocr
        with patch('builtins.__import__', side_effect=ImportError("Module not found")):
            call.main()
        
        # Should call setup functions
        mock_validate_config.assert_called_once()
        mock_check_setup.assert_called_once()
        mock_setup_folders.assert_called_once()
        
        # Should print import error
        print_calls = [str(call_obj) for call_obj in mock_print.call_args_list]
        import_error_found = any("Import error" in call_str for call_str in print_calls)
        self.assertTrue(import_error_found)
    
    @patch('call_module.validate_config')
    @patch('call_module.check_setup')
    @patch('call_module.setup_folders')
    @patch('call_module.secrets.token_hex')
    @patch('builtins.print')
    def test_main_session_id_generation(self, mock_print, mock_token_hex, 
                                       mock_setup_folders, mock_check_setup, 
                                       mock_validate_config):
        """Test that main function generates session ID"""
        mock_validate_config.return_value = True
        mock_token_hex.return_value = "abcd1234"
        
        # Mock successful import but fail OCR initialization to stop early
        with patch('builtins.__import__', return_value=MagicMock()):
            with patch('call_module.GeminiPDFOCR', side_effect=Exception("Stop here")):
                call.main()
        
        # Should generate session ID
        mock_token_hex.assert_called_once_with(4)
        
        # Should print session ID
        print_calls = [str(call_obj) for call_obj in mock_print.call_args_list]
        session_found = any("Session ID: abcd1234" in call_str for call_str in print_calls)
        self.assertTrue(session_found)


if __name__ == '__main__':
    # Create a mock call module for testing
    import types
    call_module = types.ModuleType('call_module')
    
    # Copy functions from call module
    import call as original_call
    for attr_name in dir(original_call):
        if not attr_name.startswith('_') or attr_name == '_get_directory_info':
            setattr(call_module, attr_name, getattr(original_call, attr_name))
    
    sys.modules['call_module'] = call_module
    
    unittest.main(verbosity=2)