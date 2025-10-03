#!/usr/bin/env python3
"""
Demonstration of Prompt Management System Usage

Shows how to use the new prompt management system for different document types
and how to customize prompts for specific extraction needs.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from prompts import PromptManager
from prompts.document_schemas import DocumentType, BankStatementSchema
from prompts.prompt_templates import PromptTemplates

def demo_basic_usage():
    """Demonstrate basic prompt manager usage"""
    print("🔍 Basic Prompt Manager Usage")
    print("="*50)
    
    # Initialize prompt manager
    pm = PromptManager()
    
    # Get system instruction
    system_instruction = pm.get_system_instruction()
    print(f"System Instruction:\n{system_instruction[:100]}...\n")
    
    # Get classification prompt
    classification_prompt = pm.get_classification_prompt()
    print(f"Classification Prompt:\n{classification_prompt[:100]}...\n")
    
    # Get extraction prompts for different document types
    for doc_type in DocumentType:
        prompt = pm.get_extraction_prompt(doc_type)
        print(f"{doc_type.value} prompt length: {len(prompt)} characters")
    
    print()

def demo_document_classification():
    """Demonstrate document classification"""
    print("📋 Document Classification Demo")
    print("="*50)
    
    pm = PromptManager()
    
    # Simulate classification results
    test_classifications = [
        "bank_statement",
        "insurance form", 
        "accident claim",
        "invoice",
        "unknown document"
    ]
    
    for classification in test_classifications:
        doc_type = pm.classify_document_type(classification)
        print(f"'{classification}' → {doc_type.value}")
    
    print()

def demo_structured_extraction():
    """Demonstrate structured data extraction"""
    print("🏗️ Structured Data Extraction Demo")
    print("="*50)
    
    pm = PromptManager()
    
    # Sample bank statement JSON response
    sample_bank_response = """{
        "document_type": "bank_statement",
        "account_holder": "John Doe",
        "account_number": "1234567890",
        "bank_name": "Example Bank",
        "statement_period": "Jan 1 - Jan 31, 2024",
        "opening_balance": 1000.00,
        "closing_balance": 1250.00,
        "transactions": [
            {
                "date": "2024-01-15",
                "description": "Salary Deposit",
                "amount": 3000.00,
                "balance": 4000.00,
                "transaction_type": "credit"
            },
            {
                "date": "2024-01-20",
                "description": "Grocery Store",
                "amount": -150.00,
                "balance": 3850.00,
                "transaction_type": "debit"
            }
        ]
    }"""
    
    # Parse structured response
    structured_data = pm.parse_structured_response(sample_bank_response, DocumentType.BANK_STATEMENT)
    
    if hasattr(structured_data, 'account_holder'):
        print(f"✅ Successfully parsed bank statement for: {structured_data.account_holder}")
        print(f"   Account: {structured_data.account_number}")
        print(f"   Transactions: {len(structured_data.transactions)}")
        
        # Format as markdown
        markdown_output = pm.format_output(structured_data, "markdown")
        print(f"\nMarkdown Output (first 200 chars):\n{markdown_output[:200]}...")
        
        # Format as JSON
        json_output = pm.format_output(structured_data, "json")
        print(f"\nJSON Output (first 200 chars):\n{json_output[:200]}...")
    else:
        print("❌ Failed to parse structured data")
    
    print()

def demo_custom_prompts():
    """Demonstrate custom prompt creation"""
    print("🎯 Custom Prompt Demo")
    print("="*50)
    
    pm = PromptManager()
    
    # Custom fields for bank statement
    custom_fields = {
        "routing_number": "Bank routing number",
        "interest_earned": "Interest earned this period",
        "fees_charged": "Total fees charged"
    }
    
    custom_prompt = PromptTemplates.get_custom_prompt(
        DocumentType.BANK_STATEMENT, 
        custom_fields
    )
    
    print(f"Custom bank statement prompt length: {len(custom_prompt)} characters")
    print(f"Custom fields added: {list(custom_fields.keys())}")
    
    print()

def demo_prompt_modification():
    """Show how to modify prompts in the template file"""
    print("✏️ Prompt Modification Guide")
    print("="*50)
    
    print("To modify prompts, edit these files:")
    print("1. prompts/prompt_templates.py - Main prompt templates")
    print("2. prompts/document_schemas.py - Data schemas")
    print("3. prompts/prompt_manager.py - Processing logic")
    print()
    
    print("Example modifications:")
    print("• Add new document type in DocumentType enum")
    print("• Create new schema class for document type")
    print("• Add extraction prompt in PromptTemplates")
    print("• Update get_extraction_prompt() mapping")
    print()
    
    print("Changes take effect immediately across all code!")
    print()

def demo_integration_example():
    """Show integration with existing OCR code"""
    print("🔗 Integration Example")
    print("="*50)
    
    print("Updated OCR usage:")
    print("""
# Basic usage (auto-classification + structured extraction)
ocr = GeminiPDFOCR(api_key="your_key")
pages = ocr.process_pdf("bank_statement.pdf")

# Custom prompt (disables auto-classification)
pages = ocr.process_pdf(
    "document.pdf", 
    custom_prompt="Extract only account numbers and balances"
)

# Structured extraction with specific format
pages = ocr.process_pdf(
    "statement.pdf",
    enable_structured_extraction=True,
    output_format="json"  # or "markdown"
)
""")
    
    print("Web interface automatically uses structured extraction!")
    print()

def main():
    """Run all demonstrations"""
    print("🚀 Prompt Management System Demo")
    print("="*60)
    print()
    
    demo_basic_usage()
    demo_document_classification()
    demo_structured_extraction()
    demo_custom_prompts()
    demo_prompt_modification()
    demo_integration_example()
    
    print("✅ Demo completed! Check the prompts/ folder to modify templates.")

if __name__ == "__main__":
    main()