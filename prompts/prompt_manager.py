"""
Prompt Manager - Centralized Prompt Management System

Manages all prompts used across the OCR pipeline with document classification
and structured data extraction capabilities.
"""

import json
import logging
from typing import Dict, Any, Optional, Tuple, Union
from .document_schemas import DocumentType, DocumentSchema, get_schema_for_document_type
from .prompt_templates import PromptTemplates, PROMPT_CONFIG

class PromptManager:
    """Centralized prompt management with document classification and structured extraction"""
    
    def __init__(self, enable_classification: bool = True, enable_structured_extraction: bool = True):
        """
        Initialize prompt manager
        
        Args:
            enable_classification: Enable automatic document classification
            enable_structured_extraction: Enable JSON schema-based extraction
        """
        self.enable_classification = enable_classification
        self.enable_structured_extraction = enable_structured_extraction
        self.logger = logging.getLogger(__name__)
        
    def get_system_instruction(self) -> str:
        """Get system instruction for model initialization"""
        return PromptTemplates.SYSTEM_INSTRUCTION
    
    def get_classification_prompt(self) -> str:
        """Get document classification prompt"""
        return PromptTemplates.CLASSIFICATION_PROMPT
    
    def classify_document_type(self, classification_result: str) -> DocumentType:
        """
        Parse classification result and return DocumentType
        
        Args:
            classification_result: Raw classification result from AI
            
        Returns:
            DocumentType: Classified document type
        """
        # Clean and normalize the result
        result = classification_result.strip().lower()
        
        # Map common variations to document types
        type_mapping = {
            "bank_statement": DocumentType.BANK_STATEMENT,
            "bank statement": DocumentType.BANK_STATEMENT,
            "statement": DocumentType.BANK_STATEMENT,
            "insurance_form": DocumentType.INSURANCE_FORM,
            "insurance form": DocumentType.INSURANCE_FORM,
            "insurance": DocumentType.INSURANCE_FORM,
            "accident_claim": DocumentType.ACCIDENT_CLAIM,
            "accident claim": DocumentType.ACCIDENT_CLAIM,
            "claim": DocumentType.ACCIDENT_CLAIM,
            "invoice": DocumentType.INVOICE,
            "receipt": DocumentType.INVOICE,
            "bill": DocumentType.INVOICE,
            "other": DocumentType.OTHER
        }
        
        return type_mapping.get(result, DocumentType.OTHER)
    
    def get_extraction_prompt(self, document_type: DocumentType, custom_prompt: Optional[str] = None) -> str:
        """
        Get extraction prompt for specific document type
        
        Args:
            document_type: Type of document to extract from
            custom_prompt: Optional custom prompt to override default
            
        Returns:
            str: Formatted extraction prompt
        """
        if custom_prompt:
            return custom_prompt
            
        if self.enable_structured_extraction:
            return PromptTemplates.get_extraction_prompt(document_type)
        else:
            return PromptTemplates.MARKDOWN_FALLBACK_PROMPT
    
    def get_processing_prompts(self, custom_prompt: Optional[str] = None) -> Tuple[str, Optional[str]]:
        """
        Get prompts for document processing pipeline
        
        Args:
            custom_prompt: Optional custom extraction prompt
            
        Returns:
            Tuple[str, Optional[str]]: (extraction_prompt, classification_prompt)
        """
        classification_prompt = None
        
        if self.enable_classification and not custom_prompt:
            classification_prompt = self.get_classification_prompt()
        
        # If classification is disabled or custom prompt provided, use general extraction
        if not self.enable_classification or custom_prompt:
            extraction_prompt = custom_prompt or PromptTemplates.MARKDOWN_FALLBACK_PROMPT
        else:
            # Will be determined after classification
            extraction_prompt = None
            
        return extraction_prompt, classification_prompt
    
    def parse_structured_response(self, response_text: str, document_type: DocumentType) -> Union[DocumentSchema, str]:
        """
        Parse structured JSON response into Pydantic model
        
        Args:
            response_text: Raw response from AI model
            document_type: Type of document for schema validation
            
        Returns:
            Union[DocumentSchema, str]: Parsed structured data or fallback text
        """
        if not self.enable_structured_extraction:
            return response_text
            
        try:
            # Clean response text (remove markdown formatting if present)
            cleaned_text = response_text.strip()
            if cleaned_text.startswith('```json'):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.endswith('```'):
                cleaned_text = cleaned_text[:-3]
            cleaned_text = cleaned_text.strip()
            
            # Parse JSON
            json_data = json.loads(cleaned_text)
            
            # Get appropriate schema class
            schema_class = get_schema_for_document_type(document_type)
            
            # Validate and parse with Pydantic
            structured_data = schema_class(**json_data)
            
            self.logger.info(f"Successfully parsed structured data for {document_type}")
            return structured_data
            
        except json.JSONDecodeError as e:
            self.logger.warning(f"Failed to parse JSON response: {e}")
            return response_text
        except Exception as e:
            self.logger.warning(f"Failed to validate structured data: {e}")
            return response_text
    
    def format_output(self, data: Union[DocumentSchema, str], output_format: str = "markdown") -> str:
        """
        Format extracted data for output
        
        Args:
            data: Structured data or raw text
            output_format: Output format ("markdown", "json", "text")
            
        Returns:
            str: Formatted output
        """
        if isinstance(data, str):
            return data
            
        if output_format == "json":
            return data.model_dump_json(indent=2)
        elif output_format == "markdown":
            return self._convert_to_markdown(data)
        else:
            return str(data)
    
    def _convert_to_markdown(self, data: DocumentSchema) -> str:
        """Convert structured data to markdown format"""
        if hasattr(data, 'document_type'):
            doc_type = data.document_type
            
            if doc_type == DocumentType.BANK_STATEMENT:
                return self._format_bank_statement_markdown(data)
            elif doc_type == DocumentType.INSURANCE_FORM:
                return self._format_insurance_markdown(data)
            elif doc_type == DocumentType.ACCIDENT_CLAIM:
                return self._format_accident_claim_markdown(data)
            elif doc_type == DocumentType.INVOICE:
                return self._format_invoice_markdown(data)
            else:
                return self._format_general_markdown(data)
        
        return str(data)
    
    def _format_bank_statement_markdown(self, data) -> str:
        """Format bank statement data as markdown"""
        md = f"# Bank Statement\n\n"
        md += f"**Account Holder:** {data.account_holder or 'N/A'}\n"
        md += f"**Account Number:** {data.account_number or 'N/A'}\n"
        md += f"**Bank:** {data.bank_name or 'N/A'}\n"
        md += f"**Period:** {data.statement_period or 'N/A'}\n\n"
        
        md += f"**Opening Balance:** ${data.opening_balance or 0:.2f}\n"
        md += f"**Closing Balance:** ${data.closing_balance or 0:.2f}\n\n"
        
        if data.transactions:
            md += "## Transactions\n\n"
            md += "| Date | Description | Amount | Balance |\n"
            md += "|------|-------------|--------|----------|\n"
            for txn in data.transactions:
                md += f"| {txn.date or 'N/A'} | {txn.description or 'N/A'} | ${txn.amount or 0:.2f} | ${txn.balance or 0:.2f} |\n"
        
        return md
    
    def _format_insurance_markdown(self, data) -> str:
        """Format insurance form data as markdown"""
        md = f"# Insurance Form\n\n"
        md += f"**Policy Number:** {data.policy_number or 'N/A'}\n"
        md += f"**Claim Number:** {data.claim_number or 'N/A'}\n"
        md += f"**Insured Name:** {data.insured_name or 'N/A'}\n"
        md += f"**Incident Date:** {data.incident_date or 'N/A'}\n"
        md += f"**Claim Amount:** ${data.claim_amount or 0:.2f}\n\n"
        
        if data.incident_description:
            md += f"**Incident Description:**\n{data.incident_description}\n\n"
        
        return md
    
    def _format_accident_claim_markdown(self, data) -> str:
        """Format accident claim data as markdown"""
        md = f"# Accident Claim\n\n"
        md += f"**Claim Number:** {data.claim_number or 'N/A'}\n"
        md += f"**Claimant:** {data.claimant_name or 'N/A'}\n"
        md += f"**Accident Date:** {data.accident_date or 'N/A'}\n"
        md += f"**Location:** {data.accident_location or 'N/A'}\n"
        md += f"**Damage Amount:** ${data.damage_amount or 0:.2f}\n\n"
        
        if data.accident_description:
            md += f"**Description:**\n{data.accident_description}\n\n"
        
        return md
    
    def _format_invoice_markdown(self, data) -> str:
        """Format invoice data as markdown"""
        md = f"# Invoice\n\n"
        md += f"**Invoice Number:** {data.invoice_number or 'N/A'}\n"
        md += f"**Date:** {data.invoice_date or 'N/A'}\n"
        md += f"**Vendor:** {data.vendor_name or 'N/A'}\n"
        md += f"**Customer:** {data.customer_name or 'N/A'}\n"
        md += f"**Total Amount:** ${data.total_amount or 0:.2f}\n\n"
        
        return md
    
    def _format_general_markdown(self, data) -> str:
        """Format general document data as markdown"""
        md = f"# Document\n\n"
        md += f"**Title:** {data.title or 'N/A'}\n"
        md += f"**Date:** {data.date or 'N/A'}\n\n"
        
        if data.parties:
            md += f"**Parties:** {', '.join(data.parties)}\n"
        if data.amounts:
            md += f"**Amounts:** {', '.join(f'${amt:.2f}' for amt in data.amounts)}\n"
        
        return md

# Global prompt manager instance
prompt_manager = PromptManager()