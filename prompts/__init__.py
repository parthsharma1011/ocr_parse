"""
Prompt Management System

Centralized prompt templates with Pydantic models for structured document extraction.
"""

from .prompt_manager import PromptManager
from .document_schemas import *
from .prompt_templates import *

__all__ = ['PromptManager']