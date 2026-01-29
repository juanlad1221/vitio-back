from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import List, Optional
from datetime import datetime
import uuid

from auth import get_current_user
from database import insert_media as db_insert_media, find_media as db_find_media, update_media as db_update_media, delete_media as db_delete_media
from cloudinary_service import CloudinaryService
from config import settings

router = APIRouter(prefix="/api/media", tags=["Media"])

@router.post("/upload", include_in_schema=False)
async def upload_media(
    title: str = Form(...),
    type: str = Form(...),
    description: Optional[str] = Form(None),
    projectId: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload file to Cloudinary and save metadata to PostgreSQL
    """
    # Validate file
    if not file or not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file: no filename provided"
        )
    
    # Upload to Cloudinary
    try:
        cloudinary_result = await CloudinaryService.upload_file(
            file=file,
            title=title,
            description=description or "",
            media_type=type
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload to Cloudinary: {str(e)}"
        )
    
    # Save metadata to PostgreSQL
    media_record = {
        "id": str(uuid.uuid4()),
        "user_id": current_user["user_id"],
        "title": title,
        "description": description or "",
        "size": cloudinary_result.get("size", 0),
        "ext": cloudinary_result.get("format", ""),
        "type": type,
        "url": cloudinary_result["url"],
        "project_id": projectId
    }
    
    await db_insert_media(media_record)
    
    return {
        "url": cloudinary_result["url"],
        "media_id": media_record["id"],
        "contentType": cloudinary_result.get("contentType", "application/octet-stream"),
        "public_id": cloudinary_result.get("public_id"),
        "resource_type": cloudinary_result.get("resource_type"),
        "size": cloudinary_result.get("size", 0),
        "project_id": projectId
    }

@router.get("/", include_in_schema=False)
async def get_media_files(
    type: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Get user's media files from PostgreSQL
    """
    if type:
        media_files = await db_find_media({"user_id": current_user["user_id"], "type": type})
    else:
        media_files = await db_find_media({"user_id": current_user["user_id"]})
    return media_files

@router.get("/{media_id}", include_in_schema=False)
async def get_media_info(
    media_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get specific media file information
    """
    # Get all user's media and find the specific one
    media_files = await db_find_media({"user_id": current_user["user_id"]})
    
    for media in media_files:
        if media["id"] == media_id:
            return media
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Media file not found"
    )

@router.patch("/{media_id}", include_in_schema=False)
async def update_media_endpoint(
    media_id: str,
    media_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Update media metadata in PostgreSQL
    """
    # Build update data
    update_data = {}
    
    if "title" in media_data:
        update_data["title"] = media_data["title"]
    if "description" in media_data:
        update_data["description"] = media_data["description"]
    if "type" in media_data:
        update_data["type"] = media_data["type"]
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field must be provided for update"
        )
    
    updated_media = await db_update_media(media_id, update_data)
    
    if not updated_media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media file not found"
        )
    
    return {"message": "Media updated successfully", "data": updated_media}

@router.delete("/{media_id}", include_in_schema=False)
async def delete_media_endpoint(
    media_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete media file from Cloudinary and PostgreSQL
    """
    # First get the media info to get public_id
    media_files = await db_find_media({"user_id": current_user["user_id"]})
    target_media = None
    
    for media in media_files:
        if media["id"] == media_id:
            target_media = media
            break
    
    if not target_media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media file not found"
        )
    
    # Delete from Cloudinary
    try:
        # Extract public_id from URL if needed
        public_id = target_media.get("public_id")
        if public_id:
            await CloudinaryService.delete_file(public_id)
    except Exception as e:
        print(f"Warning: Failed to delete from Cloudinary: {e}")
    
    # Delete from PostgreSQL
    deleted = await db_delete_media(media_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete media file"
        )
    
    return {"message": "Media deleted successfully"}
