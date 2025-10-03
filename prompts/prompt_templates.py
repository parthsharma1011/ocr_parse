"""
Prompt Templates for Document Processing

Centralized prompt templates with parameterization for different document types.
All prompts are managed here and can be easily modified.
"""

from typing import Dict, Any
from .document_schemas import DocumentType, BankStatementSchema, GeneralDocumentSchema

class PromptTemplates:
    """Centralized prompt template management"""
    
    # System instruction for model initialization
    SYSTEM_INSTRUCTION = """You are an expert document analysis AI specialized in extracting structured information from various document types including bank statements, insurance forms, invoices, and other financial documents. 

Your task is to:
1. First classify the document type
2. Extract relevant information according to the specified JSON schema
3. Return only valid JSON without any additional text or markdown formatting
4. Ensure all extracted data is accurate and properly formatted
5. Use null for missing information rather than making assumptions"""

    # Document classification prompt
    CLASSIFICATION_PROMPT = """Analyze this document image and classify it into one of these categories:
- bank_statement: Bank account statements with transactions
- insurance_form: Insurance policies or claim forms  
- accident_claim: Accident or incident claim forms
- invoice: Bills, invoices, or receipts
- other: Any other document type

Return only the classification as a single word (e.g., "bank_statement")."""

    # Bank statement extraction prompt
    BANK_STATEMENT_PROMPT = """Extract information from this bank statement and return it as JSON matching this exact schema:

{
  "document_type": "bank_statement",
  "account_holder": "string or null",
  "account_number": "string or null", 
  "bank_name": "string or null",
  "statement_period": "string or null",
  "opening_balance": number or null,
  "closing_balance": number or null,
  "total_credits": number or null,
  "total_debits": number or null,
  "transactions": [
    {
      "date": "string or null",
      "description": "string or null", 
      "amount": number or null,
      "balance": number or null,
      "transaction_type": "debit|credit|transfer|fee|interest or null",
      "reference": "string or null"
    }
  ],
  "address": "string or null",
  "phone": "string or null", 
  "email": "string or null"
}

Extract ALL transactions visible in the statement. For amounts, use positive numbers for credits and negative numbers for debits. Return only the JSON object."""

    # Insurance form extraction prompt  
    INSURANCE_FORM_PROMPT = """Extract information from this insurance document and return it as JSON matching this exact schema:

{
  "document_type": "insurance_form",
  "policy_number": "string or null",
  "claim_number": "string or null",
  "insured_name": "string or null", 
  "incident_date": "string or null",
  "incident_description": "string or null",
  "claim_amount": number or null,
  "policy_type": "string or null",
  "address": "string or null",
  "phone": "string or null",
  "email": "string or null"
}

Return only the JSON object."""

    # Accident claim extraction prompt
    ACCIDENT_CLAIM_PROMPT = """Extract information from this accident claim form and return it as JSON matching this exact schema:

{
  "document_type": "accident_claim", 
  "claim_number": "string or null",
  "claimant_name": "string or null",
  "accident_date": "string or null",
  "accident_location": "string or null", 
  "accident_description": "string or null",
  "vehicle_details": "string or null",
  "damage_amount": number or null,
  "police_report": "string or null",
  "witnesses": ["string"] or null,
  "address": "string or null",
  "phone": "string or null",
  "email": "string or null"
}

Return only the JSON object."""

    # Invoice extraction prompt
    INVOICE_PROMPT = """Extract information from this invoice/receipt and return it as JSON matching this exact schema:

{
  "document_type": "invoice",
  "invoice_number": "string or null",
  "invoice_date": "string or null", 
  "due_date": "string or null",
  "vendor_name": "string or null",
  "customer_name": "string or null",
  "total_amount": number or null,
  "tax_amount": number or null,
  "subtotal": number or null,
  "items": ["string"] or null,
  "vendor_address": "string or null",
  "customer_address": "string or null"
}

Return only the JSON object."""

    # General document extraction prompt
    GENERAL_DOCUMENT_PROMPT = """Extract key information from this document and return it as JSON matching this exact schema:

{
  "document_type": "other",
  "title": "string or null",
  "date": "string or null",
  "parties": ["string"] or null,
  "addresses": ["string"] or null, 
  "phone_numbers": ["string"] or null,
  "email_addresses": ["string"] or null,
  "amounts": [number] or null,
  "dates": ["string"] or null,
  "key_information": {} or null
}

Extract all names, addresses, phone numbers, email addresses, monetary amounts, and dates found in the document. Return only the JSON object."""

    # Fallback markdown prompt (for backward compatibility)
    MARKDOWN_FALLBACK_PROMPT = """Extract all text from the image and convert it into proper markdown format, ensuring all details are captured accurately including names, dates, addresses, and identification numbers."""

    @classmethod
    def get_extraction_prompt(cls, document_type: DocumentType) -> str:
        """Get appropriate extraction prompt for document type"""
        prompt_mapping = {
            DocumentType.BANK_STATEMENT: cls.BANK_STATEMENT_PROMPT,
            DocumentType.INSURANCE_FORM: cls.INSURANCE_FORM_PROMPT,
            DocumentType.ACCIDENT_CLAIM: cls.ACCIDENT_CLAIM_PROMPT,
            DocumentType.INVOICE: cls.INVOICE_PROMPT,
            DocumentType.OTHER: cls.GENERAL_DOCUMENT_PROMPT
        }
        return prompt_mapping.get(document_type, cls.GENERAL_DOCUMENT_PROMPT)

    @classmethod
    def get_custom_prompt(cls, document_type: DocumentType, custom_fields: Dict[str, Any] = None) -> str:
        """Generate custom prompt with additional fields"""
        base_prompt = cls.get_extraction_prompt(document_type)
        
        if custom_fields:
            # Add custom field instructions
            custom_instruction = f"\n\nAdditionally extract these specific fields: {custom_fields}"
            return base_prompt + custom_instruction
        
        return base_prompt

    @classmethod
    def get_schema_json(cls, document_type: DocumentType) -> str:
        """Get JSON schema string for document type"""
        from .document_schemas import get_schema_for_document_type
        
        schema_class = get_schema_for_document_type(document_type)
        return schema_class.model_json_schema()

# Prompt configuration for easy modification
PROMPT_CONFIG = {
    "classification_enabled": True,
    "structured_extraction": True,
    "fallback_to_markdown": True,
    "max_retries": 3,
    "temperature": 0.01,
    "max_tokens": 8192
}