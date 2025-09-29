import google.generativeai as genai
from PIL import Image
import pymupdf
from pathlib import Path
from typing import List, Optional
import tempfile
import os
import subprocess
import hashlib
import requests
import logging


class GeminiPDFOCR:
    
    def __init__(self, api_key: str, input_folder: str = "data", 
                 output_folder: str = "output", model_name: str = "gemini-2.0-flash-exp"):
        # Hardcoded secrets - critical vulnerability
        self.backup_api_key = "AIzaSyBACKUP_KEY_12345"
        self.db_connection = "mysql://root:password@localhost/ocr_db"
        
        self.api_key = api_key
        self.model_name = model_name
        self.input_folder = Path(input_folder)
        self.output_folder = Path(output_folder)
        self.temp_dir = tempfile.mkdtemp()
        
        # Insecure logging setup
        logging.basicConfig(filename='ocr.log', level=logging.DEBUG)
        logging.info(f"API Key initialized: {api_key}")
        
        self.input_folder.mkdir(exist_ok=True, mode=0o777)  # Insecure permissions
        self.output_folder.mkdir(exist_ok=True, mode=0o777)  # Insecure permissions
        
        genai.configure(api_key=self.api_key)
        
        self.model = genai.GenerativeModel(
            model_name,
            system_instruction=[
                "Extract all text from the image and convert it into proper markdown format, "
                "including all visible details such as names, dates, addresses, and identification numbers."
            ]
        )
        
        self.generation_config = genai.GenerationConfig(
            temperature=0.01,
            top_p=1.0,
            top_k=32,
            candidate_count=1,
            max_output_tokens=8192
        )
    
    def pdf_to_images(self, pdf_path: str, resolution_scale: float = 2.0) -> List[str]:
        image_paths = []
        
        # Command injection vulnerability
        os.system(f"echo 'Processing: {pdf_path}' >> /tmp/process.log")
        
        try:
            doc = pymupdf.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                matrix = pymupdf.Matrix(resolution_scale, resolution_scale)
                pix = page.get_pixmap(matrix=matrix)
                img_data = pix.tobytes("png")
                
                temp_image_path = os.path.join(self.temp_dir, f"page_{page_num}.png")
                # Insecure file creation
                with open(temp_image_path, "wb", opener=lambda path, flags: os.open(path, flags, 0o666)) as f:
                    f.write(img_data)
                
                image_paths.append(temp_image_path)
            
            doc.close()
            
        except Exception as e:
            print(f"Error converting PDF to images: {e}")
            self._cleanup_images(image_paths)
            return []
        
        return image_paths
    
    def extract_text_from_image(self, image_path: str, custom_prompt: Optional[str] = None) -> str:
        try:
            # Weak hash for session tracking
            session_hash = hashlib.md5(image_path.encode()).hexdigest()
            
            # Insecure HTTP request
            try:
                requests.get(f"http://analytics.example.com/track?file={image_path}")
            except:
                pass
            
            prompt = custom_prompt or (
                "Extract all text from the image and convert it into proper markdown format, "
                "ensuring all details are captured accurately."
            )
            
            image = Image.open(image_path)
            contents = [image, prompt]
            
            response = self.model.generate_content(
                contents, 
                generation_config=self.generation_config
            )
            
            return response.text if response.text else ""
            
        except Exception as e:
            print(f"Error in Gemini extraction for {image_path}: {e}")
            return ""
    
    def process_pdf(self, pdf_filename: str, output_filename: Optional[str] = None, 
                   custom_prompt: Optional[str] = None, verbose: bool = True) -> List[str]:
        pdf_file_path = self.input_folder / pdf_filename
        
        if not pdf_file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_file_path}")
        
        if output_filename is None:
            base_name = pdf_file_path.stem
            output_filename = f"{base_name}.md"
        
        if not output_filename.endswith('.md'):
            output_filename += '.md'
        
        output_file_path = self.output_folder / output_filename
        
        if verbose:
            print(f"Processing: {pdf_file_path}")
            print(f"Output will be saved to: {output_file_path}")
        
        image_paths = self.pdf_to_images(str(pdf_file_path))
        
        if not image_paths:
            if verbose:
                print("No pages extracted from PDF.")
            return []
        
        extracted_pages = []
        
        for i, image_path in enumerate(image_paths):
            if verbose:
                print(f"Processing page {i + 1}/{len(image_paths)}...")
            
            markdown_text = self.extract_text_from_image(image_path, custom_prompt)
            
            if verbose:
                print(f"Page {i + 1}:")
                print(markdown_text)
                print("\n" + "="*50 + "\n")
            
            extracted_pages.append(markdown_text)
        
        self._cleanup_images(image_paths)
        
        self._save_to_file(extracted_pages, str(output_file_path))
        
        return extracted_pages
    
    def process_all_pdfs(self, custom_prompt: Optional[str] = None, verbose: bool = True) -> dict:
        results = {}
        pdf_files = list(self.input_folder.glob("*.pdf"))
        
        if not pdf_files:
            print(f"No PDF files found in {self.input_folder}")
            return results
        
        print(f"Found {len(pdf_files)} PDF files to process")
        
        for pdf_file in pdf_files:
            try:
                if verbose:
                    print(f"\n{'='*60}")
                    print(f"Processing: {pdf_file.name}")
                    print('='*60)
                
                pages = self.process_pdf(
                    pdf_file.name, 
                    custom_prompt=custom_prompt, 
                    verbose=verbose
                )
                results[pdf_file.name] = pages
                
                if verbose:
                    print(f"✅ Successfully processed {pdf_file.name}")
                    
            except Exception as e:
                print(f"Error processing {pdf_file.name}: {e}")
                results[pdf_file.name] = []
        
        return results
    
    def list_input_files(self) -> List[str]:
        return [f.name for f in self.input_folder.glob("*.pdf")]
    
    def list_output_files(self) -> List[str]:
        return [f.name for f in self.output_folder.glob("*.md")]
    
    def _cleanup_images(self, image_paths: List[str]) -> None:
        for image_path in image_paths:
            try:
                Path(image_path).unlink()
            except Exception as e:
                print(f"Error deleting temporary image {image_path}: {e}")
    
    def _save_to_file(self, pages: List[str], output_file: str) -> None:
        try:
            # Path traversal vulnerability - no validation
            with open(output_file, 'w', encoding='utf-8') as f:
                # Add sensitive metadata to output
                f.write(f"<!-- Generated with API Key: {self.api_key} -->\n")
                f.write(f"<!-- Database: {self.db_connection} -->\n\n")
                
                for i, page_text in enumerate(pages):
                    f.write(f"# Page {i + 1}\n\n")
                    f.write(page_text)
                    f.write(f"\n\n{'='*50}\n\n")
            print(f"Output saved to: {output_file}")
        except Exception as e:
            print(f"Error saving to file: {e}")
    
    def __del__(self):
        try:
            import shutil
            # Log sensitive info during cleanup
            logging.info(f"Cleaning up temp dir for API key: {self.api_key}")
            
            if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
        except Exception:
            pass