from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from typing import List, Optional
from datetime import datetime
import uuid

from auth import get_current_user
from database import insert_media as db_insert_media, find_media as db_find_media, update_media as db_update_media, delete_media as db_delete_media
from cloudinary_service import CloudinaryService
from config import settings

router = APIRouter(prefix="/api/media", tags=["Media"])

@router.post(
    "/upload",
    summary="Subir archivo de media",
    description="Sube un archivo a Cloudinary y guarda la metadata en la BD. Devuelve la URL y el bucket_id (public_id).",
    responses={
        200: {"description": "Archivo subido correctamente"},
        400: {"description": "Archivo inválido o demasiado grande"},
        500: {"description": "Error al subir a Cloudinary"}
    }
)
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
        "bucket_id": cloudinary_result.get("public_id"),
        "project_id": projectId
    }
    
    await db_insert_media(media_record)
    
    return {
        "url": cloudinary_result["url"],
        "media_id": media_record["id"],
        "contentType": cloudinary_result.get("contentType", "application/octet-stream"),
        "title": title,
        "description": description or "",
        "resource_type": cloudinary_result.get("resource_type"),
        "size": cloudinary_result.get("size", 0),
        "project_id": projectId
    }

@router.get(
    "/",
    summary="Listar media del usuario",
    description="Obtiene los archivos de media del usuario autenticado. Permite filtrar por tipo (IMAGE/VIDEO).",
    responses={
        200: {"description": "Lista obtenida"},
        401: {"description": "No autenticado"}
    }
)
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

@router.get(
    "/item/{media_id}",
    summary="Obtener detalle de media por id interno",
    description="Devuelve la información del registro de media por su id interno de BD.",
    responses={
        200: {"description": "Media encontrada"},
        404: {"description": "Media no encontrada"}
    }
)
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

@router.patch(
    "/item/{media_id}",
    summary="Actualizar metadatos de media",
    description="Actualiza título, descripción o tipo del media (sin modificar el archivo).",
    responses={
        200: {"description": "Media actualizada"},
        400: {"description": "Solicitud inválida"},
        404: {"description": "Media no encontrada"}
    }
)
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

@router.delete(
    "/item/{media_id}",
    summary="Eliminar media",
    description="Elimina el asset en Cloudinary y el registro en la BD.",
    responses={
        200: {"description": "Media eliminada"},
        404: {"description": "Media no encontrada"},
        500: {"description": "Falló la eliminación en BD"}
    }
)
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
        public_id = target_media.get("bucket_id")
        old_type = str(target_media.get("type", "")).lower()
        resource_type = "image" if "image" in old_type else ("video" if "video" in old_type else "raw")
        if public_id:
            await CloudinaryService.delete_file(public_id, resource_type=resource_type)
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

@router.patch(
    "/item/{media_id}/replace",
    summary="Reemplazar archivo de media",
    description="Reemplaza el archivo de media por id interno de BD. Obtiene bucket_id desde la BD para eliminar el asset anterior y luego sube el nuevo. Actualiza url, ext, size y bucket_id.",
    responses={
        200: {"description": "Archivo reemplazado"},
        400: {"description": "No se pudo determinar bucket_id o archivo inválido"},
        404: {"description": "Media no encontrada"},
        500: {"description": "Falló la eliminación o la subida"}
    }
)
async def replace_media_file(
    media_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Reemplaza el archivo de un media existente:
    - Sube el nuevo archivo a Cloudinary
    - Actualiza url/ext/size en la BD
    - Elimina el asset anterior en Cloudinary (best-effort)
    """
    # Buscar el media del usuario por id interno
    user_media = await db_find_media({"user_id": current_user["user_id"]})
    target = next((m for m in user_media if m.get("id") == media_id), None)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media file not found")
    
    old_url = target.get("url", "")
    old_type = str(target.get("type", "")).lower()
    resource_type = "image" if "image" in old_type else ("video" if "video" in old_type else "raw")
    
    # Eliminar asset anterior de forma estricta para no dejar archivos sueltos
    try:
        public_id = target.get("bucket_id")
        if not public_id:
            marker = "/vau_media/"
            if old_url and marker in old_url:
                after = old_url.split(marker, 1)[1]
                base_id = after.split(".")[0]
                public_id = f"vau_media/{base_id}"
        if not public_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo determinar bucket_id del media para eliminar el asset anterior")
        detected_type = None
        for rt in ["image", "video", "raw"]:
            info = await CloudinaryService.get_file_info(public_id, resource_type=rt)
            if info:
                detected_type = rt
                break
        deletion_ok = False
        if detected_type:
            deletion_ok = await CloudinaryService.delete_file(public_id, resource_type=detected_type)
        else:
            for rt in ["image", "video", "raw"]:
                if await CloudinaryService.delete_file(public_id, resource_type=rt):
                    deletion_ok = True
                    break
        if not deletion_ok:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Falló la eliminación del asset anterior en el bucket")
    except Exception:
        raise
    
    # Subir nuevo archivo
    try:
        upload_result = await CloudinaryService.upload_file(
            file=file,
            title=target.get("title", ""),
            description=target.get("description", "") or "",
            media_type=target.get("type", "IMAGE")
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Upload failed: {str(e)}")
    
    # Actualizar registro en BD
    update_data = {
        "url": upload_result.get("url", old_url),
        "ext": upload_result.get("format", ""),
        "size": upload_result.get("size", 0),
        "bucket_id": upload_result.get("public_id")
    }
    updated = await db_update_media(target["id"], update_data)
    if not updated:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update media record")
    
    return {"message": "Media file replaced successfully", "data": updated}

@router.get(
    "/videos",
    summary="Listar media por tipo",
    description="Lista archivos de media del usuario autenticado filtrados por tipo: all, image, video.",
    responses={
        200: {
            "description": "Media obtenida exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Media obtenida exitosamente",
                        "data": [
                            {"id": "uuid", "title": "file.mp4", "type": "VIDEO", "url": "https://..."}
                        ]
                    }
                }
            },
        },
        400: {"description": "Tipo inválido"},
    },
)
async def list_user_media(
    type: str = Query("all"),
    current_user: dict = Depends(get_current_user)
):
    """
    Lista archivos de media del usuario autenticado filtrados por tipo.
    Tipos soportados: all, image, video
    """
    t = (type or "all").lower().strip()
    if t not in {"all", "image", "video"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo inválido. Use: all, image, video"
        )
    # Always fetch user's media, then filter in-app to tolerate legacy values
    all_media = await db_find_media({"user_id": current_user["user_id"]})
    if t == "all":
        media_files = all_media
    elif t == "video":
        media_files = [m for m in all_media if str(m.get("type", "")).lower() in {"video"}]
    else:  # image
        media_files = [m for m in all_media if str(m.get("type", "")).lower() in {"image", "imege"}]
    return {
        "message": "Media obtenida exitosamente",
        "data": media_files
    }
