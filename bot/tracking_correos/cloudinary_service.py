"""
Cloudinary service for encrypted media uploads
All content is encrypted BEFORE uploading to Cloudinary
"""

import os
import io
import base64
import cloudinary
import cloudinary.uploader
import cloudinary.api
import logging
from typing import Optional, Dict, List
from .encryption import encryption_manager

logger = logging.getLogger(__name__)

class CloudinaryService:
    """Manages encrypted media uploads to Cloudinary"""
    
    ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    ALLOWED_VIDEO_TYPES = ['video/mp4', 'video/webm', 'video/quicktime', 'video/x-msvideo']
    MAX_IMAGE_SIZE = 10 * 1024 * 1024
    MAX_VIDEO_SIZE = 100 * 1024 * 1024
    MAX_POST_VIDEO_DURATION = 60
    MAX_STORY_VIDEO_DURATION = 15
    MAX_CAROUSEL_ITEMS = 10
    
    def __init__(self):
        """Initialize Cloudinary configuration"""
        self.cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME')
        self.api_key = os.getenv('CLOUDINARY_API_KEY')
        self.api_secret = os.getenv('CLOUDINARY_API_SECRET')
        
        if all([self.cloud_name, self.api_key, self.api_secret]):
            cloudinary.config(
                cloud_name=self.cloud_name,
                api_key=self.api_key,
                api_secret=self.api_secret,
                secure=True
            )
            self.configured = True
            logger.info("Cloudinary configured successfully")
        else:
            self.configured = False
            logger.warning("Cloudinary not configured - missing credentials")
    
    def is_configured(self) -> bool:
        """Check if Cloudinary is properly configured"""
        return self.configured
    
    def validate_file(self, file_data: bytes, content_type: str, is_video: bool = False) -> Dict:
        """Validate file size and type"""
        if is_video:
            if content_type not in self.ALLOWED_VIDEO_TYPES:
                return {'valid': False, 'error': 'Invalid video type'}
            if len(file_data) > self.MAX_VIDEO_SIZE:
                return {'valid': False, 'error': 'Video too large (max 100MB)'}
        else:
            if content_type not in self.ALLOWED_IMAGE_TYPES:
                return {'valid': False, 'error': 'Invalid image type'}
            if len(file_data) > self.MAX_IMAGE_SIZE:
                return {'valid': False, 'error': 'Image too large (max 10MB)'}
        
        return {'valid': True}
    
    def upload_encrypted_media(self, file_data: bytes, content_type: str, 
                               folder: str = "encrypted_media",
                               resource_type: str = "auto") -> Dict:
        """
        Encrypt and upload media to Cloudinary
        Returns encrypted URL and encryption metadata
        """
        if not self.configured:
            return {'success': False, 'error': 'Cloudinary not configured'}
        
        try:
            is_video = content_type.startswith('video/')
            validation = self.validate_file(file_data, content_type, is_video)
            if not validation['valid']:
                return {'success': False, 'error': validation['error']}
            
            encrypted = encryption_manager.encrypt_file(file_data)
            if not encrypted['success']:
                return {'success': False, 'error': 'Encryption failed'}
            
            file_buffer = io.BytesIO(encrypted['encrypted_data'])
            
            upload_result = cloudinary.uploader.upload(
                file_buffer,
                folder=folder,
                resource_type="raw",
                unique_filename=True,
                overwrite=False,
                tags=["encrypted", "e2e"],
            )
            
            return {
                'success': True,
                'url': upload_result['secure_url'],
                'public_id': upload_result['public_id'],
                'encryption_key': encrypted['key'],
                'encryption_iv': encrypted['iv'],
                'original_size': encrypted['original_size'],
                'encrypted_size': encrypted['encrypted_size'],
                'resource_type': 'video' if is_video else 'image',
                'format': content_type.split('/')[-1]
            }
            
        except Exception as e:
            logger.error(f"Upload error: {e}")
            return {'success': False, 'error': str(e)}
    
    def upload_thumbnail(self, file_data: bytes, folder: str = "thumbnails") -> Dict:
        """
        Upload a thumbnail (unencrypted for preview purposes)
        Thumbnails are low-res blurred previews
        """
        if not self.configured:
            return {'success': False, 'error': 'Cloudinary not configured'}
        
        try:
            file_buffer = io.BytesIO(file_data)
            
            upload_result = cloudinary.uploader.upload(
                file_buffer,
                folder=folder,
                resource_type="image",
                transformation=[
                    {"width": 400, "height": 400, "crop": "fill"},
                    {"quality": "auto:low"},
                    {"effect": "blur:300"}
                ],
                unique_filename=True,
                overwrite=False,
            )
            
            return {
                'success': True,
                'url': upload_result['secure_url'],
                'public_id': upload_result['public_id']
            }
            
        except Exception as e:
            logger.error(f"Thumbnail upload error: {e}")
            return {'success': False, 'error': str(e)}
    
    def delete_media(self, public_id: str, resource_type: str = "raw") -> bool:
        """Delete media from Cloudinary"""
        if not self.configured:
            return False
        
        try:
            result = cloudinary.uploader.destroy(public_id, resource_type=resource_type)
            return result.get('result') == 'ok'
        except Exception as e:
            logger.error(f"Delete error: {e}")
            return False
    
    def get_download_url(self, public_id: str) -> Optional[str]:
        """Get a signed URL for downloading encrypted content"""
        if not self.configured:
            return None
        
        try:
            url = cloudinary.CloudinaryResource(public_id, type="upload", resource_type="raw").url
            return url
        except Exception as e:
            logger.error(f"URL generation error: {e}")
            return None
    
    def upload_carousel(self, files: List[Dict], folder: str = "encrypted_media") -> Dict:
        """
        Upload multiple files for a carousel post
        Each file should have: data, content_type
        """
        if len(files) > self.MAX_CAROUSEL_ITEMS:
            return {
                'success': False, 
                'error': f'Maximum {self.MAX_CAROUSEL_ITEMS} items allowed'
            }
        
        results = []
        for i, file in enumerate(files):
            result = self.upload_encrypted_media(
                file['data'],
                file['content_type'],
                folder=folder
            )
            if result['success']:
                result['order'] = i
                results.append(result)
            else:
                for r in results:
                    self.delete_media(r['public_id'])
                return {'success': False, 'error': f"Failed to upload file {i+1}"}
        
        return {
            'success': True,
            'media': results,
            'count': len(results)
        }
    
    def upload_story_media(self, file_data: bytes, content_type: str) -> Dict:
        """Upload media for a story (15 second limit for videos)"""
        return self.upload_encrypted_media(
            file_data, 
            content_type,
            folder="encrypted_stories"
        )
    
    def upload_avatar(self, file_data: bytes, content_type: str, user_id: str) -> Dict:
        """
        Upload a user avatar (not encrypted, public profile image)
        Applies automatic transformations for consistent sizing
        """
        if not self.configured:
            return {'success': False, 'error': 'Cloudinary not configured'}
        
        if content_type not in self.ALLOWED_IMAGE_TYPES:
            return {'success': False, 'error': 'Tipo de imagen no permitido'}
        
        if len(file_data) > 5 * 1024 * 1024:
            return {'success': False, 'error': 'Imagen muy grande (max 5MB)'}
        
        try:
            file_buffer = io.BytesIO(file_data)
            
            upload_result = cloudinary.uploader.upload(
                file_buffer,
                folder="avatars",
                public_id=f"user_{user_id}",
                overwrite=True,
                resource_type="image",
                transformation=[
                    {"width": 256, "height": 256, "crop": "fill", "gravity": "face"},
                    {"quality": "auto:good"},
                    {"fetch_format": "auto"}
                ]
            )
            
            return {
                'success': True,
                'url': upload_result['secure_url'],
                'public_id': upload_result['public_id']
            }
            
        except Exception as e:
            logger.error(f"Avatar upload error: {e}")
            return {'success': False, 'error': str(e)}
    
    def delete_avatar(self, user_id: str) -> bool:
        """Delete a user's avatar from Cloudinary"""
        if not self.configured:
            return False
        
        try:
            result = cloudinary.uploader.destroy(f"avatars/user_{user_id}", resource_type="image")
            return result.get('result') == 'ok'
        except Exception as e:
            logger.error(f"Avatar delete error: {e}")
            return False


cloudinary_service = CloudinaryService()
