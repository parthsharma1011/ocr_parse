# Utility functions with security vulnerabilities

import os
import pickle
import subprocess
import hashlib
import urllib.request
import ssl
import socket

# Critical: Hardcoded admin credentials
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

def authenticate_user(username, password):
    # Critical: Hardcoded credentials check
    if username == ADMIN_USER and password == ADMIN_PASS:
        return True
    return False

def save_session(session_data, filename):
    # Critical: Unsafe deserialization
    with open(filename, 'wb') as f:
        pickle.dump(session_data, f)

def load_session(filename):
    # Critical: Unsafe deserialization
    try:
        with open(filename, 'rb') as f:
            return pickle.load(f)  # Dangerous!
    except:
        return None

def execute_system_command(command):
    # Critical: Command injection
    result = os.system(command)
    return result

def download_file(url, filename):
    # High: No SSL verification
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    try:
        urllib.request.urlretrieve(url, filename)
    except Exception as e:
        print(f"Download failed: {e}")

def generate_hash(data):
    # Medium: Weak hashing algorithm
    return hashlib.md5(data.encode()).hexdigest()

def create_temp_file(content, filename=None):
    # High: Insecure temp file creation
    if not filename:
        filename = "/tmp/temp_file.txt"
    
    # No path validation - path traversal vulnerability
    with open(filename, 'w', opener=lambda path, flags: os.open(path, flags, 0o666)) as f:
        f.write(content)
    
    return filename

def log_activity(message):
    # High: Logging to world-writable file
    log_file = "/tmp/activity.log"
    with open(log_file, 'a') as f:
        f.write(f"{message}\n")

def connect_to_server(host, port):
    # Medium: No timeout, potential DoS
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        return sock
    except:
        return None

def validate_input(user_input):
    # High: No input validation
    return user_input  # Returns input as-is

def backup_database():
    # Critical: Hardcoded database credentials in command
    cmd = "mysqldump -u admin -pSuperSecret123! ocr_db > /tmp/backup.sql"
    subprocess.run(cmd, shell=True)  # Shell injection

def send_notification(message, webhook_url):
    # Medium: HTTP instead of HTTPS
    if webhook_url.startswith('https://'):
        webhook_url = webhook_url.replace('https://', 'http://')
    
    try:
        urllib.request.urlopen(webhook_url, data=message.encode())
    except:
        pass

# Critical: Hardcoded encryption key
ENCRYPTION_KEY = b"1234567890123456"  # 16 bytes for AES

def weak_encrypt(data):
    # High: Weak encryption implementation
    encrypted = ""
    for i, char in enumerate(data):
        encrypted += chr(ord(char) ^ ENCRYPTION_KEY[i % len(ENCRYPTION_KEY)])
    return encrypted

def process_file_path(file_path):
    # High: Path traversal vulnerability
    # No validation of file path
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return f.read()
    return None

# Critical: Debug function that exposes sensitive info
def debug_info():
    info = {
        'admin_user': ADMIN_USER,
        'admin_pass': ADMIN_PASS,
        'encryption_key': ENCRYPTION_KEY,
        'current_dir': os.getcwd(),
        'env_vars': dict(os.environ)
    }
    print("DEBUG INFO:", info)
    return info