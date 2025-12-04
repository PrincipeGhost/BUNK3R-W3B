"""
End-to-end encryption module for media content using AES-256-GCM
All content is encrypted BEFORE uploading to Cloudinary
"""

import os
import base64
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
import logging

logger = logging.getLogger(__name__)

class EncryptionManager:
    """Manages AES-256-GCM encryption for media content"""
    
    NONCE_SIZE = 12
    KEY_SIZE = 32
    SALT_SIZE = 16
    ITERATIONS = 480000
    
    def __init__(self, master_key: str = None):
        """Initialize encryption manager with optional master key"""
        self.master_key = master_key or os.getenv('ENCRYPTION_MASTER_KEY')
        if not self.master_key:
            self.master_key = self._generate_master_key()
            logger.warning("No ENCRYPTION_MASTER_KEY found, generated temporary key")
    
    def _generate_master_key(self) -> str:
        """Generate a random master key"""
        return base64.b64encode(os.urandom(32)).decode()
    
    def generate_key(self) -> bytes:
        """Generate a random 256-bit encryption key"""
        return AESGCM.generate_key(bit_length=256)
    
    def generate_nonce(self) -> bytes:
        """Generate a random 96-bit nonce"""
        return os.urandom(self.NONCE_SIZE)
    
    def derive_key_from_password(self, password: str, salt: bytes = None) -> tuple:
        """Derive a 256-bit key from password using PBKDF2"""
        if salt is None:
            salt = os.urandom(self.SALT_SIZE)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.KEY_SIZE,
            salt=salt,
            iterations=self.ITERATIONS,
        )
        key = kdf.derive(password.encode())
        return key, salt
    
    def encrypt_data(self, data: bytes, key: bytes = None) -> dict:
        """
        Encrypt binary data using AES-256-GCM
        Returns dict with encrypted_data, key, and nonce (all base64 encoded)
        """
        try:
            if key is None:
                key = self.generate_key()
            
            nonce = self.generate_nonce()
            aesgcm = AESGCM(key)
            ciphertext = aesgcm.encrypt(nonce, data, None)
            
            return {
                'encrypted_data': base64.b64encode(ciphertext).decode(),
                'key': base64.b64encode(key).decode(),
                'nonce': base64.b64encode(nonce).decode(),
                'success': True
            }
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            return {'success': False, 'error': str(e)}
    
    def decrypt_data(self, encrypted_data: str, key: str, nonce: str) -> dict:
        """
        Decrypt data using AES-256-GCM
        All parameters should be base64 encoded strings
        """
        try:
            ciphertext = base64.b64decode(encrypted_data)
            key_bytes = base64.b64decode(key)
            nonce_bytes = base64.b64decode(nonce)
            
            aesgcm = AESGCM(key_bytes)
            plaintext = aesgcm.decrypt(nonce_bytes, ciphertext, None)
            
            return {
                'data': plaintext,
                'success': True
            }
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            return {'success': False, 'error': str(e)}
    
    def encrypt_file(self, file_data: bytes) -> dict:
        """
        Encrypt a file (image/video) for upload
        Returns encrypted binary data and encryption metadata
        """
        try:
            key = self.generate_key()
            nonce = self.generate_nonce()
            aesgcm = AESGCM(key)
            
            ciphertext = aesgcm.encrypt(nonce, file_data, None)
            
            return {
                'encrypted_data': ciphertext,
                'key': base64.b64encode(key).decode(),
                'iv': base64.b64encode(nonce).decode(),
                'original_size': len(file_data),
                'encrypted_size': len(ciphertext),
                'success': True
            }
        except Exception as e:
            logger.error(f"File encryption error: {e}")
            return {'success': False, 'error': str(e)}
    
    def decrypt_file(self, encrypted_data: bytes, key: str, iv: str) -> dict:
        """
        Decrypt a file from Cloudinary
        """
        try:
            key_bytes = base64.b64decode(key)
            nonce_bytes = base64.b64decode(iv)
            
            aesgcm = AESGCM(key_bytes)
            plaintext = aesgcm.decrypt(nonce_bytes, encrypted_data, None)
            
            return {
                'data': plaintext,
                'success': True
            }
        except Exception as e:
            logger.error(f"File decryption error: {e}")
            return {'success': False, 'error': str(e)}
    
    def encrypt_text(self, text: str, key: bytes = None) -> dict:
        """Encrypt text content (captions, comments, etc)"""
        return self.encrypt_data(text.encode('utf-8'), key)
    
    def decrypt_text(self, encrypted_data: str, key: str, nonce: str) -> dict:
        """Decrypt text content"""
        result = self.decrypt_data(encrypted_data, key, nonce)
        if result['success']:
            result['text'] = result['data'].decode('utf-8')
            del result['data']
        return result
    
    def encrypt_for_user(self, data: bytes, user_id: str) -> dict:
        """
        Encrypt data with a user-specific derived key
        Uses master key + user_id to derive unique key per user
        """
        try:
            user_salt = hashlib.sha256(f"{self.master_key}:{user_id}".encode()).digest()[:16]
            user_key, _ = self.derive_key_from_password(self.master_key, user_salt)
            
            return self.encrypt_data(data, user_key)
        except Exception as e:
            logger.error(f"User encryption error: {e}")
            return {'success': False, 'error': str(e)}
    
    def generate_content_key(self) -> dict:
        """
        Generate a new encryption key for a piece of content
        Returns key and IV in base64 format for storage
        """
        key = self.generate_key()
        iv = self.generate_nonce()
        
        return {
            'key': base64.b64encode(key).decode(),
            'iv': base64.b64encode(iv).decode()
        }
    
    def get_encryption_metadata(self, encrypted_result: dict) -> dict:
        """Extract only metadata needed for database storage"""
        return {
            'key': encrypted_result.get('key'),
            'iv': encrypted_result.get('iv') or encrypted_result.get('nonce'),
        }


encryption_manager = EncryptionManager()
