# OCR PDF Processing Pipeline

![CI/CD Pipeline](https://github.com/YOUR_USERNAME/ocr_parse/workflows/CI/CD%20Pipeline/badge.svg)

A Python application for extracting text from PDF files using Google's Gemini AI.

## Features

- PDF to image conversion
- AI-powered text extraction using Gemini
- Batch processing capabilities
- Markdown output format

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your Gemini API key:
```bash
export GEMINI_API_KEY="your_api_key_here"
```

3. Run the application:
```bash
python call.py
```

## CI/CD Pipeline

This project includes GitHub Actions workflows that:

- **Test**: Runs linting and import tests
- **Security Scan**: Checks for vulnerabilities with Bandit and Safety
- **Build**: Packages the application
- **Deploy**: Creates deployment artifacts

### Viewing Pipeline Results

1. Push your code to GitHub
2. Go to the "Actions" tab in your repository
3. Click on any workflow run to see detailed logs
4. Each step shows real-time output of your code execution

### Setting up Secrets

Add these secrets in your GitHub repository settings:

- `GEMINI_API_KEY`: Your Google Gemini API key

## File Structure

```
ocr_parse/
├── .github/workflows/    # CI/CD pipeline definitions
├── Data/                 # Input PDF files
├── Output/              # Generated markdown files
├── pdf_ocr.py          # Main OCR processing class
├── call.py             # Application entry point
├── config.py           # Configuration settings
├── utils.py            # Utility functions
└── requirements.txt    # Python dependencies
```