from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from datetime import datetime
import uuid
import json

from auth import get_current_user
from database import (
    insert_node, find_node, find_project_nodes, 
    insert_edge, find_edges, find_project, 
    db_instance
)
from cloudinary_service import CloudinaryService

router = APIRouter(prefix="/api/node", tags=["Nodo"])

@router.post(
    "/",
    response_model=dict,
    summary="Crear un nuevo nodo",
    description="Crea un nuevo nodo en un proyecto existente. Opcionalmente conecta el nuevo nodo a un nodo fuente mediante una arista.",
    responses={
        404: {"description": "Proyecto o nodo fuente no encontrado"},
        401: {"description": "No autorizado"},
        400: {"description": "Tipo de archivo no válido"}
    }
)
async def create_node(
    projectId: str = Form(
        ..., 
        description="ID del proyecto al que pertenece el nodo",
        example="550e8400-e29b-41d4-a716-446655440000"
    ),
    sourceNodeId: str = Form(
        None, 
        description="ID del nodo fuente al que se conectará el nuevo nodo (opcional)",
        example="550e8400-e29b-41d4-a716-446655440001"
    ),
    attributes: str = Form(
        default="{}", 
        description="JSON string con los atributos del nodo: type (tipo de nodo), position (coordenadas x,y), data (datos adicionales del nodo)",
        example='{"type": "video", "position": {"x": 100, "y": 200}, "data": {"title": "Mi nodo", "description": "Descripción del nodo"}}'
    ),
    typeEdge: str = Form(
        default="default", 
        description="Tipo de arista que conecta el nodo fuente con el nuevo nodo",
        example="default"
    ),
    file: UploadFile = File(
        None, 
        description="Archivo de imagen o video opcional para el nodo (solo formatos image/* o video/*)"
    ),
    current_user: dict = Depends(get_current_user)
):
    import json
    try:
        attributes = json.loads(attributes) if isinstance(attributes, str) else attributes
    except json.JSONDecodeError:
        attributes = {}
    
    project = await find_project(projectId)
    
    if not project or project["userId"] != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    async with db_instance.pool.acquire() as conn:
        last_order_row = await conn.fetchrow("""
            SELECT MAX(node_order) as max_order FROM nodes WHERE project_id = $1
        """, projectId)
        next_order = (last_order_row["max_order"] or 0) + 1
    
    current_time = datetime.utcnow()
    node_id = str(uuid.uuid4())
    
    file_data = None
    if file and file.filename:
        content_type = file.content_type or ""
        if not content_type.startswith("image/") and not content_type.startswith("video/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Solo se permiten archivos de imagen o video"
            )
        
        upload_result = await CloudinaryService.upload_file(
            file=file,
            title=attributes.get("type", "node_media"),
            media_type="VIDEO" if content_type.startswith("video/") else "IMAGE"
        )
        file_data = {
            "url": upload_result["url"],
            "public_id": upload_result["public_id"],
            "resource_type": upload_result["resource_type"],
            "format": upload_result["format"],
            "size": upload_result["size"],
            "contentType": upload_result["contentType"],
            "width": upload_result.get("width"),
            "height": upload_result.get("height"),
            "duration": upload_result.get("duration")
        }
    
    node_data = attributes.get("data", {})
    if file_data:
        node_data["media"] = file_data
    
    new_node = {
        "id": node_id,
        "type": attributes.get("type", "default"),
        "position": attributes.get("position", {"x": 0, "y": 0}),
        "data": node_data,
        "nodeOrder": next_order,
        "projectId": projectId,
        "createdAt": current_time,
        "updatedAt": current_time
    }
    
    await insert_node(new_node)
    
    if sourceNodeId:
        edge_id = str(uuid.uuid4())
        new_edge = {
            "id": edge_id,
            "type": typeEdge,
            "source": sourceNodeId,
            "target": node_id,
            "projectId": projectId,
            "createdAt": current_time,
            "updatedAt": current_time
        }
        await insert_edge(new_edge)
    
    return {
        "message": "Se ha creado el nodo exitosamente",
        "data": new_node
    }

@router.get(
    "/details",
    response_model=dict,
    summary="Obtener detalles de un nodo",
    description="Retorna los detalles de un nodo especifico por su ID.",
    responses={
        404: {"description": "Nodo no encontrado"},
        403: {"description": "Acceso denegado"},
        401: {"description": "No autorizado"}
    }
)
async def get_node_details(id: str = Query(...), current_user: dict = Depends(get_current_user)):
    node = await find_node(id)
    
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found"
        )
    
    project = await find_project(node["projectId"])
    
    if not project or project["userId"] != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return node

@router.patch(
    "/{id}",
    response_model=dict,
    summary="Actualizar un nodo",
    description="Actualiza los atributos de un nodo existente (type, position, data).",
    responses={
        404: {"description": "Nodo no encontrado"},
        403: {"description": "Acceso denegado"},
        400: {"description": "Solicitud invalida - debe proporcionar al menos un campo"},
        401: {"description": "No autorizado"}
    }
)
async def update_node(
    id: str,
    node_data: dict,
    current_user: dict = Depends(get_current_user)
):
    node = await find_node(id)
    
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found"
        )
    
    project = await find_project(node["projectId"])
    
    if not project or project["userId"] != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    update_data = {}
    attributes = node_data.get("attributes", {})
    
    if "type" in attributes:
        update_data["type"] = attributes["type"]
    if "position" in attributes:
        update_data["position"] = attributes["position"]
    if "data" in attributes:
        update_data["data"] = attributes["data"]
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Al menos uno de los campos \"type\", \"position\" o \"data\" debe estar presente."
        )
    
    async with db_instance.pool.acquire() as conn:
        await conn.execute("""
            UPDATE nodes 
            SET type = COALESCE($1, type),
                position = COALESCE($2, position),
                data = COALESCE($3, data),
                updated_at = $4
            WHERE id = $5
        """, 
            update_data.get("type"),
            json.dumps(update_data.get("position")) if "position" in update_data else None,
            json.dumps(update_data.get("data")) if "data" in update_data else None,
            datetime.utcnow(),
            id
        )
    
    return {"message": "Nodo actualizado exitosamente"}

@router.delete(
    "/{id}",
    response_model=dict,
    summary="Eliminar un nodo",
    description="Elimina un nodo y todas sus aristas asociadas (entrantes y salientes).",
    responses={
        404: {"description": "Nodo no encontrado"},
        403: {"description": "Acceso denegado"},
        401: {"description": "No autorizado"}
    }
)
async def delete_node(id: str, current_user: dict = Depends(get_current_user)):
    node = await find_node(id)
    
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found"
        )
    
    project = await find_project(node["projectId"])
    
    if not project or project["userId"] != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    async with db_instance.pool.acquire() as conn:
        await conn.execute("DELETE FROM nodes WHERE id = $1", id)
        await conn.execute("DELETE FROM edges WHERE source = $1 OR target = $1", id)
    
    return {"message": "Nodo eliminado exitosamente"}

@router.patch(
    "/reset/position/{id}",
    response_model=dict,
    summary="Resetear posicion de un nodo",
    description="Resetea la posicion de un nodo a las coordenadas (0, 0).",
    responses={
        404: {"description": "Nodo no encontrado"},
        403: {"description": "Acceso denegado"},
        401: {"description": "No autorizado"}
    }
)
async def reset_node_position(id: str, current_user: dict = Depends(get_current_user)):
    node = await find_node(id)
    
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found"
        )
    
    project = await find_project(node["projectId"])
    
    if not project or project["userId"] != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    async with db_instance.pool.acquire() as conn:
        await conn.execute("""
            UPDATE nodes 
            SET position = $1, updated_at = $2
            WHERE id = $3
        """, json.dumps({"x": 0, "y": 0}), datetime.utcnow(), id)
    
    return {"message": "Posicion del nodo reseteada exitosamente"}
