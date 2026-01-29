import os
import uuid
import cloudinary
import cloudinary.uploader
import cloudinary.api
from fastapi import UploadFile, HTTPException, status
from config import settings
from typing import Dict, Any

# Configure Cloudinary
def configure_cloudinary():
    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret
    )

class CloudinaryService:
    @staticmethod
    async def upload_file(
        file: UploadFile, 
        title: str, 
        description: str = "",
        media_type: str = "IMAGE"
    ) -> Dict[str, Any]:
        """
        Upload file to Cloudinary and return metadata
        """
        configure_cloudinary()
        
        # Validate file - check if file has content and can be read
        if not file or not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file: no filename provided"
            )
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Reset file position for upload
        await file.seek(0)
        
        # Check file size
        if file_size > settings.max_file_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Maximum size: {settings.max_file_size} bytes"
            )
        
        # Generate unique filename
        unique_id = str(uuid.uuid4())
        filename = f"{unique_id}_{file.filename or 'file'}"
        
        # Determine resource type based on file extension or content type
        content_type = getattr(file, 'content_type', None) or 'application/octet-stream'
        if content_type and "image" in content_type:
            resource_type = "image"
        elif content_type and "video" in content_type:
            resource_type = "video"
        else:
            resource_type = "raw"
        
        try:
            # Upload to Cloudinary WITHOUT upload preset (simpler)
            result = cloudinary.uploader.upload(
                file_content,
                public_id=unique_id,
                resource_type=resource_type,
                folder="vau_media",
                overwrite=True,
                tags=[media_type, "user_upload"],
                quality="auto",          # Auto quality
                fetch_format="auto"     # Auto format conversion
            )
            
            return {
                "url": result.get("secure_url"),
                "public_id": result.get("public_id"),
                "resource_type": result.get("resource_type"),
                "format": result.get("format"),
                "size": result.get("bytes", file_size),
                "contentType": file.content_type,
                "width": result.get("width"),
                "height": result.get("height"),
                "duration": result.get("duration")  # For videos
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file: {str(e)}"
            )
    
    @staticmethod
    async def delete_file(public_id: str, resource_type: str = "image") -> bool:
        """
        Delete file from Cloudinary
        """
        configure_cloudinary()
        
        try:
            result = cloudinary.uploader.destroy(
                public_id,
                resource_type=resource_type,
                invalidate=True
            )
            return result.get("result") == "ok"
        except Exception as e:
            print(f"Error deleting file: {e}")
            return False
    
    @staticmethod
    async def get_file_info(public_id: str, resource_type: str = "image") -> Dict[str, Any]:
        """
        Get file information from Cloudinary
        """
        configure_cloudinary()
        
        try:
            result = cloudinary.api.resource(
                public_id,
                resource_type=resource_type
            )
            return result
        except Exception as e:
            print(f"Error getting file info: {e}")
            return {}