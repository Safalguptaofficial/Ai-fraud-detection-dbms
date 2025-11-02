"""
Data Encryption at Rest
Handles encryption of sensitive data (PII, credentials, etc.)
"""
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
import base64
import os
from typing import Optional, Union
import logging

logger = logging.getLogger(__name__)


class EncryptionManager:
    """
    Manages encryption/decryption using Fernet (symmetric encryption)
    Uses AES-128 in CBC mode with PKCS7 padding
    """
    
    def __init__(self, master_key: Optional[str] = None):
        """
        Initialize encryption manager
        
        Args:
            master_key: Base64-encoded master key. If None, generates new key.
        """
        if master_key:
            self.key = master_key.encode()
        else:
            # Generate new key
            self.key = Fernet.generate_key()
        
        self.cipher = Fernet(self.key)
    
    @classmethod
    def from_password(cls, password: str, salt: bytes) -> 'EncryptionManager':
        """
        Create encryption manager from password using PBKDF2
        
        Args:
            password: Master password
            salt: Salt for key derivation (store this!)
        """
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return cls(master_key=key.decode())
    
    def encrypt(self, plaintext: Union[str, bytes]) -> str:
        """
        Encrypt plaintext data
        
        Args:
            plaintext: Data to encrypt (string or bytes)
        
        Returns:
            Base64-encoded encrypted string
        """
        if isinstance(plaintext, str):
            plaintext = plaintext.encode('utf-8')
        
        encrypted = self.cipher.encrypt(plaintext)
        return encrypted.decode('utf-8')
    
    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt ciphertext data
        
        Args:
            ciphertext: Base64-encoded encrypted string
        
        Returns:
            Decrypted plaintext string
        """
        if isinstance(ciphertext, str):
            ciphertext = ciphertext.encode('utf-8')
        
        decrypted = self.cipher.decrypt(ciphertext)
        return decrypted.decode('utf-8')
    
    def get_key(self) -> str:
        """Get the encryption key (store this securely!)"""
        return self.key.decode('utf-8')


class FieldEncryption:
    """
    Database field-level encryption
    Encrypts sensitive fields before storing in database
    """
    
    # Fields that should be encrypted
    SENSITIVE_FIELDS = [
        'ssn',              # Social Security Number
        'tax_id',           # Tax ID
        'credit_card',      # Credit card numbers
        'bank_account',     # Bank account numbers
        'password',         # Passwords (use hashing instead!)
        'api_key',          # API keys
        'oauth_token',      # OAuth tokens
        'connection_params' # Database connection strings
    ]
    
    def __init__(self, encryption_manager: EncryptionManager):
        self.encryptor = encryption_manager
    
    def encrypt_field(self, field_name: str, value: Optional[str]) -> Optional[str]:
        """
        Encrypt a field if it's sensitive
        
        Args:
            field_name: Name of the field
            value: Value to potentially encrypt
        
        Returns:
            Encrypted value if sensitive, original value otherwise
        """
        if value is None:
            return None
        
        if field_name.lower() in self.SENSITIVE_FIELDS:
            try:
                return self.encryptor.encrypt(value)
            except Exception as e:
                logger.error(f"Failed to encrypt field {field_name}: {e}")
                raise
        
        return value
    
    def decrypt_field(self, field_name: str, value: Optional[str]) -> Optional[str]:
        """
        Decrypt a field if it was encrypted
        
        Args:
            field_name: Name of the field
            value: Value to potentially decrypt
        
        Returns:
            Decrypted value if it was encrypted, original value otherwise
        """
        if value is None:
            return None
        
        if field_name.lower() in self.SENSITIVE_FIELDS:
            try:
                return self.encryptor.decrypt(value)
            except Exception as e:
                logger.error(f"Failed to decrypt field {field_name}: {e}")
                # Return None rather than exposing encrypted data
                return None
        
        return value
    
    def encrypt_dict(self, data: dict) -> dict:
        """
        Encrypt all sensitive fields in a dictionary
        
        Args:
            data: Dictionary with potentially sensitive fields
        
        Returns:
            Dictionary with sensitive fields encrypted
        """
        encrypted_data = data.copy()
        
        for field_name, value in data.items():
            if isinstance(value, str):
                encrypted_data[field_name] = self.encrypt_field(field_name, value)
        
        return encrypted_data
    
    def decrypt_dict(self, data: dict) -> dict:
        """
        Decrypt all encrypted fields in a dictionary
        
        Args:
            data: Dictionary with potentially encrypted fields
        
        Returns:
            Dictionary with encrypted fields decrypted
        """
        decrypted_data = data.copy()
        
        for field_name, value in data.items():
            if isinstance(value, str):
                decrypted_data[field_name] = self.decrypt_field(field_name, value)
        
        return decrypted_data


def generate_master_key() -> str:
    """Generate a new master encryption key"""
    return Fernet.generate_key().decode('utf-8')


def generate_salt() -> str:
    """Generate a new salt for password-based encryption"""
    return base64.b64encode(os.urandom(16)).decode('utf-8')


# Example usage:
"""
from security.encryption import EncryptionManager, FieldEncryption

# Method 1: Use a master key
encryption_manager = EncryptionManager(master_key="your-base64-key")

# Method 2: Derive from password
salt = generate_salt()  # Store this!
encryption_manager = EncryptionManager.from_password("SecurePassword123", salt.encode())

# Encrypt/decrypt directly
encrypted = encryption_manager.encrypt("sensitive data")
decrypted = encryption_manager.decrypt(encrypted)

# Field-level encryption
field_encryptor = FieldEncryption(encryption_manager)

# Encrypt sensitive fields in a dict
user_data = {
    "name": "John Doe",
    "email": "john@example.com",
    "ssn": "123-45-6789",  # Will be encrypted
    "api_key": "sk_live_abc123"  # Will be encrypted
}

encrypted_data = field_encryptor.encrypt_dict(user_data)
# encrypted_data['ssn'] and encrypted_data['api_key'] are now encrypted

decrypted_data = field_encryptor.decrypt_dict(encrypted_data)
# Original values restored
"""

