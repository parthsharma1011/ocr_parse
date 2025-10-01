"""
Main Application Entry Point

This module provides the command-line interface and orchestration logic for the
PDF OCR processing application. It handles setup, validation, and user interaction.

Features:
- Interactive command-line interface
- Automatic folder setup and PDF file management
- Configuration validation and error handling
- Batch processing capabilities
- Performance-optimized directory operations

Security:
- Secure configuration validation
- Safe file operations with path validation
- No sensitive data exposure in output
- Proper error handling and logging

Performance:
- Cached directory operations
- Optimized file moving and setup
- Efficient batch processing
- Memory-conscious resource management

Author: OCR Processing Team
Version: 2.0.0
"""

import os
import secrets
from pathlib import Path
from typing import Dict, List, Optional
from config import validate_config, GEMINI_API_KEY, INPUT_FOLDER, OUTPUT_FOLDER
from utils import setup_logging
from functools import lru_cache

@lru_cache(maxsize=1)
def _get_directory_info() -> Dict[str, any]:
    """
    Cached directory information gathering for performance optimization.
    
    Scans the current directory and input folder to gather comprehensive
    information about files and directories. Uses LRU caching to avoid
    repeated filesystem operations.
    
    Returns:
        Dict[str, any]: Dictionary containing directory information with keys:
            - current_dir (Path): Current working directory
            - data_folder (Path): Input folder path
            - output_folder (Path): Output folder path
            - current_files (List[str]): Files in current directory
            - current_dirs (List[str]): Subdirectories in current directory
            - current_pdfs (List[str]): PDF files in current directory
            - pdf_files (List[str]): PDF files in input folder
            
    Performance:
        - LRU cache prevents repeated directory scans
        - Single-pass directory traversal for efficiency
        - Batch processing of file information
        - Optimized for repeated calls during setup
        
    Example:
        >>> info = _get_directory_info()
        >>> print(f"Found {len(info['pdf_files'])} PDFs in input folder")
        >>> print(f"Found {len(info['current_pdfs'])} PDFs to move")
        
    Note:
        This is an internal function used by setup and validation routines.
        The cache should be cleared if files are moved or directories change.
    """
    current_dir = Path.cwd()
    data_folder = current_dir / INPUT_FOLDER
    output_folder = current_dir / OUTPUT_FOLDER
    
    # Initialize lists for different file types
    current_files = []
    current_dirs = []
    current_pdfs = []
    
    # Single-pass directory traversal for efficiency
    try:
        for item in current_dir.iterdir():
            if item.is_file():
                current_files.append(item.name)
                # Check for PDF files that need to be moved
                if item.suffix.lower() == '.pdf':
                    current_pdfs.append(item.name)
            elif item.is_dir():
                current_dirs.append(item.name)
    except PermissionError:
        # Handle permission errors gracefully
        pass
    
    # Get PDF files from input folder if it exists
    pdf_files = []
    if data_folder.exists():
        try:
            pdf_files = [f.name for f in data_folder.glob("*.pdf")]
        except PermissionError:
            # Handle permission errors gracefully
            pass
    
    return {
        'current_dir': current_dir,
        'data_folder': data_folder,
        'output_folder': output_folder,
        'current_files': current_files,
        'current_dirs': current_dirs,
        'current_pdfs': current_pdfs,
        'pdf_files': pdf_files
    }

def check_setup() -> None:
    """
    Perform comprehensive setup validation and display system status.
    
    Checks the current directory structure, validates folder existence,
    and displays information about available PDF files. This function
    provides users with a clear overview of the application state.
    
    Features:
        - Directory structure validation
        - PDF file discovery and reporting
        - Clear status messages for user guidance
        - Performance-optimized with cached directory info
        
    Output:
        Prints detailed information about:
        - Current working directory
        - Input/output folder status
        - Files and directories in current location
        - PDF files ready for processing
        - PDF files that need to be moved
        
    Example Output:
        ```
        === Setup Check ===
        Current directory: /path/to/ocr_parse
        Data folder exists: True
        Output folder exists: True
        
        Files in current directory:
          call.py
          pdf_ocr.py
          Data/
          Output/
        
        PDF files in data folder: 3
          document1.pdf
          document2.pdf
          document3.pdf
        ```
        
    Performance:
        - Uses cached directory information
        - Single filesystem scan for all information
        - Efficient display formatting
    """
    print("=== Setup Check ===")
    
    # Get cached directory information for performance
    info = _get_directory_info()
    
    # Display basic directory information
    print(f"Current directory: {info['current_dir']}")
    print(f"Data folder exists: {info['data_folder'].exists()}")
    print(f"Output folder exists: {info['output_folder'].exists()}")
    
    # Display current directory contents
    print(f"\nFiles in current directory:")
    # Show files first
    for file in sorted(info['current_files']):
        print(f"  {file}")
    # Then show directories with trailing slash
    for dir_name in sorted(info['current_dirs']):
        print(f"  {dir_name}/")
    
    # Display PDF files in input folder
    if info['data_folder'].exists():
        pdf_count = len(info['pdf_files'])
        print(f"\nPDF files in {INPUT_FOLDER} folder: {pdf_count}")
        for pdf in sorted(info['pdf_files']):
            print(f"  {pdf}")
    else:
        print(f"\n{INPUT_FOLDER} folder doesn't exist!")
    
    # Display PDF files that need to be moved
    if info['current_pdfs']:
        print(f"\nPDF files found in current directory (should be moved to {INPUT_FOLDER}/):")
        for pdf in sorted(info['current_pdfs']):
            print(f"  {pdf}")

def setup_folders():
    print("\n=== Creating Folders ===")
    
    data_folder = Path(INPUT_FOLDER)
    output_folder = Path(OUTPUT_FOLDER)
    
    # Create both folders at once
    data_folder.mkdir(exist_ok=True)
    output_folder.mkdir(exist_ok=True)
    
    print("Folders created successfully")
    
    # Use cached info for better performance
    info = _get_directory_info()
    current_pdfs = [Path(info['current_dir']) / pdf for pdf in info['current_pdfs']]
    
    if current_pdfs:
        print(f"\nFound {len(current_pdfs)} PDF file(s) in current directory.")
        # Move files in batch for better performance
        moved_count = 0
        for pdf in current_pdfs:
            try:
                new_path = data_folder / pdf.name
                pdf.rename(new_path)
                moved_count += 1
                print(f"Moved {pdf.name} to {INPUT_FOLDER}/ folder")
            except Exception as e:
                print(f"Error moving {pdf.name}: {e}")
        
        if moved_count > 0:
            # Clear cache since files were moved
            _get_directory_info.cache_clear()

def main() -> None:
    """
    Main application entry point and orchestration function.
    
    Coordinates the entire OCR processing workflow from configuration validation
    through PDF processing. Handles all major error conditions gracefully and
    provides clear user feedback throughout the process.
    
    Workflow:
        1. Validate configuration and API key
        2. Check and setup directory structure
        3. Initialize OCR processor
        4. Process the first available PDF file
        5. Display results and output information
        
    Error Handling:
        - Configuration errors: Clear messages about missing API keys
        - Import errors: Guidance on missing dependencies
        - Processing errors: Detailed error information
        - Graceful degradation: Continues where possible
        
    Security:
        - Validates configuration before processing
        - Uses secure session ID generation
        - No sensitive data in error messages
        - Safe file operations throughout
        
    Performance:
        - Lazy loading of heavy dependencies
        - Efficient resource initialization
        - Optimized directory operations
        
    Example Output:
        ```
        === Setup Check ===
        Current directory: /path/to/ocr_parse
        ...
        Session ID: a1b2c3d4
        Successfully initialized GeminiPDFOCR
        Available PDF files: ['document.pdf']
        🔄 Processing: document.pdf
        Successfully extracted 5 pages
        ```
    """
    # Step 1: Validate configuration before proceeding
    try:
        validate_config()
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("\nPlease create a .env file with your GEMINI_API_KEY")
        print("See README.md for detailed setup instructions.")
        return
    
    # Step 2: Check current setup and create necessary folders
    check_setup()
    setup_folders()
    
    print("\n" + "="*60)
    
    # Step 3: Import OCR processor (lazy loading for better startup)
    try:
        from pdf_ocr import GeminiPDFOCR
        print("Successfully imported GeminiPDFOCR")
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure all dependencies are installed: pip install -r requirements.txt")
        return
    except Exception as e:
        print(f"Error importing OCR module: {e}")
        return
    
    # Step 4: Generate secure session ID for tracking
    session_id = secrets.token_hex(4)
    print(f"Session ID: {session_id}")
    
    # Step 5: Initialize OCR processor and process files
    try:
        # Initialize with validated API key
        ocr_processor = GeminiPDFOCR(api_key=GEMINI_API_KEY)
        print("Successfully initialized GeminiPDFOCR")
        
        # Get list of available PDF files
        input_files = ocr_processor.list_input_files()
        print(f"\nAvailable PDF files: {input_files}")
        
        # Check if any PDF files are available
        if not input_files:
            print(f"\n❌ No PDF files found in {INPUT_FOLDER} folder!")
            print(f"\n📋 To get started:")
            print(f"   1. Place your PDF files in the '{INPUT_FOLDER}' folder")
            print(f"   2. Run this application again")
            print(f"\n💡 Supported formats: PDF files only")
            return
        
        # Process the first PDF file as a demonstration
        first_pdf = input_files[0]
        print(f"\n🔄 Processing: {first_pdf}")
        
        try:
            # Process PDF with verbose output for user feedback
            extracted_pages = ocr_processor.process_pdf(first_pdf, verbose=True)
            print(f"\n✅ Successfully extracted {len(extracted_pages)} pages")
            
            # Show output files created
            output_files = ocr_processor.list_output_files()
            print(f"\n📄 Output files created: {output_files}")
            print(f"\n💾 Results saved to: {OUTPUT_FOLDER}/ folder")
            
        except Exception as e:
            print(f"\n❌ Error processing PDF: {e}")
            print("\n🔧 Troubleshooting tips:")
            print("   - Check if the PDF file is not corrupted")
            print("   - Ensure you have a stable internet connection")
            print("   - Verify your API key is valid and has quota remaining")
            
    except Exception as e:
        print(f"\n❌ Error initializing OCR processor: {e}")
        print("\n🔧 This might be due to:")
        print("   - Invalid API key")
        print("   - Network connectivity issues")
        print("   - API service unavailability")

def batch_process_example():
    print("\n" + "="*60)
    print("=== Batch Processing Example ===")
    
    try:
        from pdf_ocr import GeminiPDFOCR
        
        ocr_processor = GeminiPDFOCR(api_key=GEMINI_API_KEY)
        
        pdf_files = ocr_processor.list_input_files()
        
        if not pdf_files:
            print("No PDF files found for batch processing!")
            return
        
        print(f"Found {len(pdf_files)} PDF files for batch processing:")
        for i, filename in enumerate(pdf_files, 1):
            print(f"{i}. {filename}")
        
        results = ocr_processor.process_all_pdfs(verbose=False)
        
        print(f"\n📊 Batch Processing Results:")
        for filename, pages in results.items():
            if pages:
                print(f"{filename}: {len(pages)} pages extracted")
            else:
                print(f"{filename}: Failed to extract")
        
        output_files = ocr_processor.list_output_files()
        print(f"\nTotal output files created: {len(output_files)}")
        for output_file in output_files:
            print(f"  {output_file}")
            
    except Exception as e:
        print(f"Error in batch processing: {e}")

if __name__ == "__main__":
    print("PDF OCR Processing Tool")
    print("="*60)
    
    main()
    
    try:
        # Check if configuration is valid before proceeding
        if not GEMINI_API_KEY:
            print("\nPlease configure your GEMINI_API_KEY in .env file")
        else:
            from pdf_ocr import GeminiPDFOCR
            
            ocr_processor = GeminiPDFOCR(api_key=GEMINI_API_KEY)
            pdf_files = ocr_processor.list_input_files()
            
            if len(pdf_files) > 1:
                print(f"\n💡 You have {len(pdf_files)} PDF files. Would you like to process all of them?")
                user_input = input("Type 'yes' to run batch processing: ").lower().strip()
                if user_input in ['yes', 'y']:
                    batch_process_example()
    except Exception as e:
        print(f"Error during processing: {e}")
    
    print("\n Processing complete!")
    
    