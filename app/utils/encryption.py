"""Encryption utilities for sensitive data."""
from cryptography.fernet import Fernet
from app.config import settings


class EncryptionService:
    """Service for encrypting and decrypting sensitive data."""
    
    def __init__(self):
        """Initialize encryption service with key from settings."""
        self.cipher = Fernet(settings.encryption_key.encode())
    
    def encrypt(self, data: str) -> str:
        """
        Encrypt string data.
        
        Args:
            data: Plain text string to encrypt
            
        Returns:
            Encrypted string (base64 encoded)
        """
        if not data:
            return ""
        
        encrypted = self.cipher.encrypt(data.encode())
        return encrypted.decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt encrypted string data.
        
        Args:
            encrypted_data: Encrypted string (base64 encoded)
            
        Returns:
            Decrypted plain text string
        """
        if not encrypted_data:
            return ""
        
        decrypted = self.cipher.decrypt(encrypted_data.encode())
        return decrypted.decode()
    
    def encrypt_dict(self, data: dict) -> dict:
        """
        Encrypt all string values in a dictionary.
        
        Args:
            data: Dictionary with string values
            
        Returns:
            Dictionary with encrypted values
        """
        return {
            key: self.encrypt(value) if isinstance(value, str) else value
            for key, value in data.items()
        }
    
    def decrypt_dict(self, encrypted_data: dict) -> dict:
        """
        Decrypt all string values in a dictionary.
        
        Args:
            encrypted_data: Dictionary with encrypted values
            
        Returns:
            Dictionary with decrypted values
        """
        return {
            key: self.decrypt(value) if isinstance(value, str) else value
            for key, value in encrypted_data.items()
        }


# Global encryption service instance
encryption_service = EncryptionService()
