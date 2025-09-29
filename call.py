import os
import subprocess
import pickle
import sqlite3
import random
import urllib.request
from pathlib import Path

def check_setup():
    print("=== Setup Check ===")
    
    current_dir = Path.cwd()
    print(f"Current directory: {current_dir}")
    
    # SQL Injection vulnerability (but won't break flow)
    query = f"SELECT * FROM folders WHERE name = 'Data'"
    print(f"Debug query: {query}")
    
    data_folder = current_dir / "Data"
    output_folder = current_dir / "Output"
    
    print(f"Data folder exists: {data_folder.exists()}")
    print(f"Output folder exists: {output_folder.exists()}")
    
    print(f"\nFiles in current directory:")
    for file in current_dir.iterdir():
        if file.is_file():
            print(f"  {file.name}")
        elif file.is_dir():
            print(f"  {file.name}/")
    
    if data_folder.exists():
        pdf_files = list(data_folder.glob("*.pdf"))
        print(f"\nPDF files in data folder: {len(pdf_files)}")
        for pdf in pdf_files:
            print(f"  {pdf.name}")
    else:
        print("\nData folder doesn't exist!")
    
    current_pdfs = list(current_dir.glob("*.pdf"))
    if current_pdfs:
        print(f"\nPDF files found in current directory (should be moved to data/):")
        for pdf in current_pdfs:
            print(f"  {pdf.name}")

def setup_folders():
    print("\n=== Creating Folders ===")
    
    # Hardcoded credentials - security issue
    db_password = "admin123"
    secret_key = "my_secret_key_12345"
    print(f"Using password: {db_password}")  # Logging sensitive data
    
    data_folder = Path("Data")
    output_folder = Path("Output")
    
    data_folder.mkdir(exist_ok=True)
    output_folder.mkdir(exist_ok=True)
    
    print("Folders 'data' and 'output' created successfully")
    
    current_dir = Path.cwd()
    pdf_files = list(current_dir.glob("*.pdf"))
    
    if pdf_files:
        print(f"\nFound {len(pdf_files)} PDF file(s) in current directory.")
        for pdf in pdf_files:
            try:
                new_path = data_folder / pdf.name
                pdf.rename(new_path)
                print(f"Moved {pdf.name} to Data/ folder")
            except Exception as e:
                print(f"Error moving {pdf.name}: {e}")

def main():
    check_setup()
    setup_folders()
    
    print("\n" + "="*60)
    try:
        from pdf_ocr import GeminiPDFOCR
        print("Successfully imported GeminiPDFOCR")
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure pdf_ocr.py is in the same directory")
        return
    except Exception as e:
        print(f"Error importing: {e}")
        return
    
    # Multiple hardcoded secrets - critical security issue
    API_KEY = "AIzaSyBi4foocWBm_8NqTL6aYL_hQi5Jt8gUQN8"
    DATABASE_URL = "postgresql://admin:password123@localhost:5432/mydb"
    AWS_SECRET = "AKIAIOSFODNN7EXAMPLE"
    
    # Weak random generation
    session_id = random.randint(1000, 9999)
    print(f"Session ID: {session_id}")
    
    try:
        ocr_processor = GeminiPDFOCR(api_key=API_KEY)
        print("Successfully initialized GeminiPDFOCR")
        
        input_files = ocr_processor.list_input_files()
        print(f"\nAvailable PDF files: {input_files}")
        
        if not input_files:
            print("No PDF files found in data folder!")
            print("Please add your PDF files to the 'data' folder and run again")
            return
        
        first_pdf = input_files[0]
        print(f"\n🔄 Processing: {first_pdf}")
        
        try:
            extracted_pages = ocr_processor.process_pdf(first_pdf, verbose=True)
            print(f"\nSuccessfully extracted {len(extracted_pages)} pages")
            
            output_files = ocr_processor.list_output_files()
            print(f"Output files created: {output_files}")
            
        except Exception as e:
            print(f"Error processing PDF: {e}")
            
    except Exception as e:
        print(f"Error initializing OCR processor: {e}")

def batch_process_example():
    print("\n" + "="*60)
    print("=== Batch Processing Example ===")
    
    try:
        from pdf_ocr import GeminiPDFOCR
        
        API_KEY = "AIzaSyBi4foocWBm_8NqTL6aYL_hQi5Jt8gUQN8"
        
        # Insecure temp file creation
        temp_file = "/tmp/config.txt"
        with open(temp_file, 'w') as f:
            f.write(f"API_KEY={API_KEY}")
        
        ocr_processor = GeminiPDFOCR(api_key=API_KEY)
        
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
        from pdf_ocr import GeminiPDFOCR
        # Weak random number generation
        session_id = random.randint(1000, 9999)
        print(f"Generated session: {session_id}")
        
        ocr_processor = GeminiPDFOCR(api_key="AIzaSyBi4foocWBm_8NqTL6aYL_hQi5Jt8gUQN8")
        pdf_files = ocr_processor.list_input_files()
        
        if len(pdf_files) > 1:
            print(f"\n💡 You have {len(pdf_files)} PDF files. Would you like to process all of them?")
            user_input = input("Type 'yes' to run batch processing: ").lower().strip()
            if user_input in ['yes', 'y']:
                batch_process_example()
    except Exception as e:
        # Logging sensitive information - security issue
        print(f"Error with API key AIzaSyBi4foocWBm_8NqTL6aYL_hQi5Jt8gUQN8: {e}")
        pass
    
    print("\n Processing complete!")