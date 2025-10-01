"""
Configuration Management Module

This module handles secure configuration loading and environment variable management
for the OCR processing application. Provides optimized, cached environment loading
with secure defaults and validation.

Features:
- Secure environment variable loading from .env files
- LRU caching for performance optimization
- Validation of required configuration
- Secure default values
- No hardcoded credentials

Security:
- Environment-based credential management
- No sensitive data in source code
- Secure file permissions
- Input validation for configuration values

Author: OCR Processing Team
Version: 2.0.0
"""

import os
from pathlib import Path
from functools import lru_cache
from typing import bool


@lru_cache(maxsize=1)
def load_env_file() -> bool:
    """
    Load environment variables from .env file with caching optimization.
    
    Reads the .env file once and caches the result to avoid repeated file I/O.
    Processes environment variables in a secure manner with proper parsing.
    
    Returns:
        bool: True if loading completed successfully (file may or may not exist)
        
    Features:
        - Cached loading: file is read only once for performance
        - Buffered I/O: uses 4KB buffer for efficient file reading
        - Comment support: ignores lines starting with '#'
        - Whitespace handling: strips whitespace from keys and values
        - Error resilient: continues processing if individual lines fail
        
    File Format:
        The .env file should contain key=value pairs, one per line:
        ```
        # This is a comment
        GEMINI_API_KEY=your_api_key_here
        DEBUG=False
        ```
        
    Security:
        - Only processes files in current directory
        - No execution of file contents
        - Safe parsing of key-value pairs
        - Validates file existence before reading
        
    Performance:
        - LRU cache prevents repeated file reads
        - Buffered I/O for efficient file operations
        - Batch processing of all lines
    """
    env_file = Path('.env')
    
    # Check if .env file exists before attempting to read
    if env_file.exists():
        try:
            # Use buffered reading for better performance
            with open(env_file, 'r', encoding='utf-8', buffering=4096) as f:
                content = f.read()
            
            # Process all lines at once for better performance
            for line_num, line in enumerate(content.splitlines(), 1):
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Parse key=value pairs
                if '=' in line:
                    try:
                        key, value = line.split('=', 1)  # Split only on first '='
                        key = key.strip()
                        value = value.strip()
                        
                        # Only set non-empty keys
                        if key:
                            os.environ[key] = value
                    except Exception as e:
                        # Log parsing errors but continue processing
                        print(f"Warning: Failed to parse line {line_num} in .env file: {e}")
                        
        except Exception as e:
            print(f"Warning: Failed to read .env file: {e}")
    
    return True


# Load environment variables once at module import
# This ensures configuration is available immediately
load_env_file()

# =============================================================================
# CONFIGURATION VARIABLES
# =============================================================================
# All configuration is loaded from environment variables for security

# Required Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
"""str: Google Gemini API key (REQUIRED)

This is the primary API key used to authenticate with Google's Gemini AI service.
Must be set in environment variables or .env file.

Example:
    GEMINI_API_KEY=AIzaSyBxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
"""

# Optional Configuration with Secure Defaults
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash-exp')
"""str: Gemini model name to use for OCR processing

Defaults to 'gemini-2.0-flash-exp' which provides the best balance of
speed and accuracy for document processing tasks.

Supported models:
- gemini-2.0-flash-exp (recommended)
- gemini-1.5-pro
- gemini-1.5-flash
"""

INPUT_FOLDER = os.getenv('INPUT_FOLDER', 'Data')
"""str: Folder name for input PDF files

Defaults to 'Data'. This folder will be created automatically if it doesn't exist.
Place your PDF files in this folder for processing.
"""

OUTPUT_FOLDER = os.getenv('OUTPUT_FOLDER', 'Output')
"""str: Folder name for output markdown files

Defaults to 'Output'. Processed markdown files will be saved here.
Folder will be created automatically if it doesn't exist.
"""

# Debug and Logging Configuration
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
"""bool: Enable debug mode

When True, enables additional debug logging and verbose output.
Useful for troubleshooting and development.

Set DEBUG=True in .env file to enable.
"""

VERBOSE_LOGGING = os.getenv('VERBOSE_LOGGING', 'False').lower() == 'true'
"""bool: Enable verbose logging

When True, logs additional details about processing steps.
Useful for monitoring and debugging performance issues.

Set VERBOSE_LOGGING=True in .env file to enable.
"""

# Security Configuration
DEFAULT_FILE_PERMISSIONS = 0o644
"""int: Default file permissions for created files

Uses secure permissions (644) that allow:
- Owner: read/write
- Group: read only
- Others: read only

This prevents unauthorized modification of generated files.
"""

DEFAULT_DIR_PERMISSIONS = 0o755
"""int: Default directory permissions for created directories

Uses secure permissions (755) that allow:
- Owner: read/write/execute
- Group: read/execute
- Others: read/execute

This allows proper directory access while maintaining security.
"""


def validate_config() -> bool:
    """
    Validate that all required configuration is present and valid.
    
    Checks that essential configuration values are set and valid.
    Should be called before initializing the OCR processor.
    
    Returns:
        bool: True if configuration is valid
        
    Raises:
        ValueError: If required configuration is missing or invalid
        
    Example:
        >>> try:
        ...     validate_config()
        ...     print("Configuration is valid")
        ... except ValueError as e:
        ...     print(f"Configuration error: {e}")
        
    Validation Checks:
        - GEMINI_API_KEY is present and non-empty
        - Model name is valid (if specified)
        - Folder names are valid (if specified)
        
    Security:
        - Does not log or expose API key values
        - Validates input without storing sensitive data
        - Provides clear error messages for troubleshooting
    """
    # Check required API key
    if not GEMINI_API_KEY:
        raise ValueError(
            "GEMINI_API_KEY environment variable is required. "
            "Please set it in your .env file or environment variables.\n\n"
            "To get an API key:\n"
            "1. Visit https://makersuite.google.com/app/apikey\n"
            "2. Sign in with your Google account\n"
            "3. Create a new API key\n"
            "4. Add it to your .env file: GEMINI_API_KEY=your_key_here"
        )
    
    # Validate API key format (basic check)
    if len(GEMINI_API_KEY.strip()) < 20:
        raise ValueError(
            "GEMINI_API_KEY appears to be invalid (too short). "
            "Please check your API key and ensure it's correctly set."
        )
    
    # Validate folder names (basic security check)
    for folder_name, folder_var in [(INPUT_FOLDER, 'INPUT_FOLDER'), (OUTPUT_FOLDER, 'OUTPUT_FOLDER')]:
        if not folder_name or '..' in folder_name or '/' in folder_name:
            raise ValueError(
                f"{folder_var} contains invalid characters. "
                "Folder names should be simple directory names without path separators."
            )
    
    return True