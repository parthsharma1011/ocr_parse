"""
Document Schema Definitions using Pydantic

Defines structured schemas for different document types including bank statements,
insurance forms, accident claims, and general documents.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum

class DocumentType(str, Enum):
    """Document classification types"""
    BANK_STATEMENT = "bank_statement"
    INSURANCE_FORM = "insurance_form"
    ACCIDENT_CLAIM = "accident_claim"
    INVOICE = "invoice"
    RECEIPT = "receipt"
    CONTRACT = "contract"
    OTHER = "other"

class TransactionType(str, Enum):
    """Bank transaction types"""
    DEBIT = "debit"
    CREDIT = "credit"
    TRANSFER = "transfer"
    FEE = "fee"
    INTEREST = "interest"

class Transaction(BaseModel):
    """Individual bank transaction"""
    date: Optional[str] = Field(None, description="Transaction date")
    description: Optional[str] = Field(None, description="Transaction description")
    amount: Optional[float] = Field(None, description="Transaction amount")
    balance: Optional[float] = Field(None, description="Account balance after transaction")
    transaction_type: Optional[TransactionType] = Field(None, description="Type of transaction")
    reference: Optional[str] = Field(None, description="Transaction reference number")

class BankStatementSchema(BaseModel):
    """Bank statement structured data"""
    document_type: DocumentType = Field(DocumentType.BANK_STATEMENT, description="Document classification")
    account_holder: Optional[str] = Field(None, description="Account holder name")
    account_number: Optional[str] = Field(None, description="Bank account number")
    bank_name: Optional[str] = Field(None, description="Name of the bank")
    statement_period: Optional[str] = Field(None, description="Statement period (from - to)")
    opening_balance: Optional[float] = Field(None, description="Opening balance")
    closing_balance: Optional[float] = Field(None, description="Closing balance")
    total_credits: Optional[float] = Field(None, description="Total credit amount")
    total_debits: Optional[float] = Field(None, description="Total debit amount")
    transactions: List[Transaction] = Field(default_factory=list, description="List of transactions")
    address: Optional[str] = Field(None, description="Account holder address")
    phone: Optional[str] = Field(None, description="Contact phone number")
    email: Optional[str] = Field(None, description="Contact email address")

class InsuranceClaimSchema(BaseModel):
    """Insurance claim form structured data"""
    document_type: DocumentType = Field(DocumentType.INSURANCE_FORM, description="Document classification")
    policy_number: Optional[str] = Field(None, description="Insurance policy number")
    claim_number: Optional[str] = Field(None, description="Claim reference number")
    insured_name: Optional[str] = Field(None, description="Name of insured person")
    incident_date: Optional[str] = Field(None, description="Date of incident")
    incident_description: Optional[str] = Field(None, description="Description of incident")
    claim_amount: Optional[float] = Field(None, description="Claimed amount")
    policy_type: Optional[str] = Field(None, description="Type of insurance policy")
    address: Optional[str] = Field(None, description="Insured person address")
    phone: Optional[str] = Field(None, description="Contact phone number")
    email: Optional[str] = Field(None, description="Contact email address")

class AccidentClaimSchema(BaseModel):
    """Accident claim form structured data"""
    document_type: DocumentType = Field(DocumentType.ACCIDENT_CLAIM, description="Document classification")
    claim_number: Optional[str] = Field(None, description="Accident claim number")
    claimant_name: Optional[str] = Field(None, description="Name of claimant")
    accident_date: Optional[str] = Field(None, description="Date of accident")
    accident_location: Optional[str] = Field(None, description="Location of accident")
    accident_description: Optional[str] = Field(None, description="Description of accident")
    vehicle_details: Optional[str] = Field(None, description="Vehicle information")
    damage_amount: Optional[float] = Field(None, description="Estimated damage amount")
    police_report: Optional[str] = Field(None, description="Police report number")
    witnesses: Optional[List[str]] = Field(default_factory=list, description="Witness information")
    address: Optional[str] = Field(None, description="Claimant address")
    phone: Optional[str] = Field(None, description="Contact phone number")
    email: Optional[str] = Field(None, description="Contact email address")

class InvoiceSchema(BaseModel):
    """Invoice structured data"""
    document_type: DocumentType = Field(DocumentType.INVOICE, description="Document classification")
    invoice_number: Optional[str] = Field(None, description="Invoice number")
    invoice_date: Optional[str] = Field(None, description="Invoice date")
    due_date: Optional[str] = Field(None, description="Payment due date")
    vendor_name: Optional[str] = Field(None, description="Vendor/supplier name")
    customer_name: Optional[str] = Field(None, description="Customer name")
    total_amount: Optional[float] = Field(None, description="Total invoice amount")
    tax_amount: Optional[float] = Field(None, description="Tax amount")
    subtotal: Optional[float] = Field(None, description="Subtotal before tax")
    items: Optional[List[str]] = Field(default_factory=list, description="Invoice line items")
    vendor_address: Optional[str] = Field(None, description="Vendor address")
    customer_address: Optional[str] = Field(None, description="Customer address")

class GeneralDocumentSchema(BaseModel):
    """General document structured data for unknown document types"""
    document_type: DocumentType = Field(DocumentType.OTHER, description="Document classification")
    title: Optional[str] = Field(None, description="Document title or subject")
    date: Optional[str] = Field(None, description="Document date")
    parties: Optional[List[str]] = Field(default_factory=list, description="Names mentioned in document")
    addresses: Optional[List[str]] = Field(default_factory=list, description="Addresses mentioned")
    phone_numbers: Optional[List[str]] = Field(default_factory=list, description="Phone numbers found")
    email_addresses: Optional[List[str]] = Field(default_factory=list, description="Email addresses found")
    amounts: Optional[List[float]] = Field(default_factory=list, description="Monetary amounts found")
    dates: Optional[List[str]] = Field(default_factory=list, description="All dates found")
    key_information: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Other key information")

# Union type for all document schemas
DocumentSchema = Union[
    BankStatementSchema,
    InsuranceClaimSchema,
    AccidentClaimSchema,
    InvoiceSchema,
    GeneralDocumentSchema
]

def get_schema_for_document_type(doc_type: DocumentType) -> BaseModel:
    """Get appropriate schema class for document type"""
    schema_mapping = {
        DocumentType.BANK_STATEMENT: BankStatementSchema,
        DocumentType.INSURANCE_FORM: InsuranceClaimSchema,
        DocumentType.ACCIDENT_CLAIM: AccidentClaimSchema,
        DocumentType.INVOICE: InvoiceSchema,
        DocumentType.OTHER: GeneralDocumentSchema
    }
    return schema_mapping.get(doc_type, GeneralDocumentSchema)