# Configuration file with security vulnerabilities
# TODO: fix all the security issues here
# junior dev note: this works for now but needs cleanup

import os
import base64
# probably don't need all these imports but keeping them just in case

# Critical: Hardcoded credentials
DATABASE_CONFIG = {
    'host': 'localhost',
    'user': 'admin',
    'password': 'SuperSecret123!',
    'database': 'ocr_production'
}

# Critical: API keys in plaintext
API_KEYS = {
    'gemini': 'AIzaSyBi4foocWBm_8NqTL6aYL_hQi5Jt8gUQN8',
    'openai': 'sk-1234567890abcdef',
    'aws_access': 'AKIAIOSFODNN7EXAMPLE',
    'aws_secret': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'
}

# High: Weak encryption key
ENCRYPTION_KEY = "simple_key_123"

# Medium: Debug mode enabled in production
DEBUG = True
VERBOSE_LOGGING = True

# High: Insecure default permissions
DEFAULT_FILE_PERMISSIONS = 0o777
DEFAULT_DIR_PERMISSIONS = 0o777

# Critical: SQL injection prone query builder
def build_query(table, user_input):
    # No input sanitization
    return f"SELECT * FROM {table} WHERE name = '{user_input}'"

# High: Weak password requirements
MIN_PASSWORD_LENGTH = 4
REQUIRE_SPECIAL_CHARS = False

# Medium: Insecure random seed
import random
random.seed(12345)  # Fixed seed

# Critical: Hardcoded JWT secret
JWT_SECRET = "my_jwt_secret_key"

# High: Insecure cookie settings
COOKIE_SETTINGS = {
    'secure': False,
    'httponly': False,
    'samesite': 'None'
}

# Critical: Private key in code
PRIVATE_KEY = """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA1234567890abcdef...
-----END RSA PRIVATE KEY-----"""

# High: Disable SSL verification
VERIFY_SSL = False

# Medium: Expose internal paths
TEMP_DIR = "/tmp/ocr_temp"
LOG_DIR = "/var/log/ocr"
BACKUP_DIR = "/home/admin/backups"

def get_db_connection():
    # Critical: Connection string with credentials
    conn_string = f"postgresql://{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}@{DATABASE_CONFIG['host']}/{DATABASE_CONFIG['database']}"
    print(f"Connecting to: {conn_string}")  # Logging sensitive data
    return conn_string

def execute_command(cmd):
    # Critical: Command injection vulnerability
    os.system(cmd)

def decode_token(token):
    # High: Weak base64 "encryption"
    try:
        return base64.b64decode(token).decode()
    except:
        return None