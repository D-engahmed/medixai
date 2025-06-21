"""
Encryption utilities for sensitive data
"""
from typing import Union, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
import json

from app.config.settings import settings

class Encryptor:
    """
    Encryption utility class using AES-GCM
    """
    
    def __init__(self, key: Optional[str] = None):
        """Initialize encryptor with key or generate new one"""
        if key:
            self.key = base64.urlsafe_b64decode(key)
        else:
            self.key = AESGCM.generate_key(bit_length=256)
    
    def get_key(self) -> str:
        """Get base64 encoded key"""
        return base64.urlsafe_b64encode(self.key).decode()
    
    def encrypt(self, data: Union[str, dict, list]) -> dict:
        """
        Encrypt data using AES-GCM
        Returns: {"encrypted": encrypted_data, "nonce": nonce}
        """
        if isinstance(data, (dict, list)):
            data = json.dumps(data)
        
        data = data.encode()
        aesgcm = AESGCM(self.key)
        nonce = os.urandom(12)
        encrypted = aesgcm.encrypt(nonce, data, None)
        
        return {
            "encrypted": base64.urlsafe_b64encode(encrypted).decode(),
            "nonce": base64.urlsafe_b64encode(nonce).decode()
        }
    
    def decrypt(self, encrypted_data: str, nonce: str) -> Union[str, dict, list]:
        """
        Decrypt data using AES-GCM
        """
        try:
            encrypted = base64.urlsafe_b64decode(encrypted_data)
            nonce = base64.urlsafe_b64decode(nonce)
            aesgcm = AESGCM(self.key)
            decrypted = aesgcm.decrypt(nonce, encrypted, None)
            
            try:
                # Try to parse as JSON
                return json.loads(decrypted)
            except json.JSONDecodeError:
                # Return as string if not JSON
                return decrypted.decode()
        except Exception as e:
            raise ValueError(f"فشل فك التشفير: {str(e)}")

class FieldEncryptor:
    """
    Utility for encrypting individual database fields
    """
    
    def __init__(self):
        """Initialize with application encryption key"""
        self.fernet = Fernet(settings.ENCRYPTION_KEY)
    
    def encrypt_field(self, value: str) -> str:
        """Encrypt a single field value"""
        if not value:
            return value
        return self.fernet.encrypt(value.encode()).decode()
    
    def decrypt_field(self, encrypted_value: str) -> str:
        """Decrypt a single field value"""
        if not encrypted_value:
            return encrypted_value
        return self.fernet.decrypt(encrypted_value.encode()).decode()

def derive_key(password: str, salt: Optional[bytes] = None) -> tuple:
    """
    Derive encryption key from password using PBKDF2
    Returns: (key, salt)
    """
    if not salt:
        salt = os.urandom(16)
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key.decode(), base64.urlsafe_b64encode(salt).decode()

def hash_file(file_path: str) -> str:
    """
    Calculate SHA-256 hash of file
    """
    sha256 = hashes.Hash(hashes.SHA256())
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256.update(chunk)
    return base64.urlsafe_b64encode(sha256.finalize()).decode()
