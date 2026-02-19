from database import (
    get_users_collection, get_projects_collection, 
    get_nodes_collection, get_edges_collection, get_media_collection,
    insert_project, find_project, find_user_projects, 
    update_project, delete_project, find_project_nodes, find_edges,
    insert_node, insert_edge
)
from fastapi import APIRouter, Depends, HTTPException, status, Body
from datetime import datetime
import uuid

from auth import get_current_user
from schemas import ProjectTypes, DetailsProjectTypes, ProjectTypesResponse

# Define el APIRouter requerido
router = APIRouter(prefix="/api/project", tags=["Proyectos"])

@router.post(
    "/",
    summary="Crear proyecto",
    description="Crea un nuevo proyecto para el usuario autenticado.",
    responses={
        200: {
            "description": "Proyecto creado",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Proyecto creado exitosamente",
                        "data": {
                            "id": "uuid",
                            "title": "Mi Proyecto",
                            "description": "Descripción opcional",
                            "status": True,
                            "userId": "uuid-user",
                            "createdAt": "2025-01-01T00:00:00Z",
                            "updatedAt": "2025-01-01T00:00:00Z"
                        }
                    }
                }
            },
        },
        400: {"description": "Validación inválida"},
    },
)
async def create_project(
    project_data: dict = Body(..., example={"title": "Mi Proyecto", "description": "Descripción opcional"}),
    current_user: dict = Depends(get_current_user)
):
    title = project_data.get("title")
    description = project_data.get("description", "")
    
    if not title or title.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El título es requerido"
        )
    
    current_time = datetime.utcnow()
    project_id = str(uuid.uuid4())
    
    new_project = {
        "id": project_id,
        "title": title.strip(),
        "description": description.strip(),
        "status": True,
        "userId": current_user["user_id"],
        "createdAt": current_time,
        "updatedAt": current_time
    }
    
    result = await insert_project(new_project)
    
    start_node_id = str(uuid.uuid4())
    end_node_id = str(uuid.uuid4())
    
    start_node = {
        "id": start_node_id,
        "type": "start",
        "position": {"x": 0, "y": 40},
        "data": {},
        "nodeOrder": 1,
        "projectId": project_id,
        "createdAt": current_time,
        "updatedAt": current_time
    }
    
    end_node = {
        "id": end_node_id,
        "type": "end",
        "position": {"x": 800, "y": 40},
        "data": {},
        "nodeOrder": 2,
        "projectId": project_id,
        "createdAt": current_time,
        "updatedAt": current_time
    }
    
    await insert_node(start_node)
    await insert_node(end_node)
    
    edge = {
        "id": str(uuid.uuid4()),
        "type": "default",
        "source": start_node_id,
        "target": end_node_id,
        "projectId": project_id,
        "createdAt": current_time,
        "updatedAt": current_time
    }
    
    await insert_edge(edge)
    
    return {
        "message": "Proyecto creado exitosamente",
        "data": new_project,
        "nodes": [start_node, end_node],
        "edges": [edge]
    }

@router.get(
    "/",
    summary="Listar proyectos",
    description="Obtiene todos los proyectos del usuario autenticado.",
    responses={
        200: {
            "description": "Lista de proyectos",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Proyectos obtenidos exitosamente",
                        "data": [
                            {"id": "uuid", "title": "Proyecto A", "description": "", "status": True, "userId": "uuid-user", "createdAt": "2025-01-01T00:00:00Z", "updatedAt": "2025-01-01T00:00:00Z"}
                        ]
                    }
                }
            },
        }
    },
)
async def get_projects(current_user: dict = Depends(get_current_user)):
    # Obtener todos los proyectos del usuario actual
    projects = await find_user_projects(current_user["user_id"])
    
    # Limpiar _id si existe
    cleaned_projects = []
    for project in projects:
        project_dict = dict(project)
        if "_id" in project_dict:
            project_dict.pop("_id")
        cleaned_projects.append(project_dict)
    
    return {
        "message": "Proyectos obtenidos exitosamente",
        "data": cleaned_projects
    }

@router.get(
    "/detail/{project_id}",
    summary="Detalle de proyecto",
    description="Obtiene el detalle de un proyecto del usuario, incluyendo nodos y edges.",
    responses={
        200: {
            "description": "Detalle del proyecto",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Detalles del proyecto obtenidos exitosamente",
                        "data": {
                            "id": "uuid",
                            "title": "Proyecto A",
                            "userId": "uuid-user",
                            "description": "",
                            "status": True,
                            "createdAt": "2025-01-01T00:00:00Z",
                            "updatedAt": "2025-01-01T00:00:00Z",
                            "nodes": [],
                            "edges": []
                        }
                    }
                }
            },
        },
        403: {"description": "Acceso denegado"},
        404: {"description": "Proyecto no encontrado"},
    },
)
async def get_project_details(project_id: str, current_user: dict = Depends(get_current_user)):
    # Obtener proyecto y verificar propiedad
    project = await find_project(project_id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proyecto no encontrado"
        )
    
    if project["userId"] != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado"
        )
    
    # Obtener nodos y edges asociados
    nodes = await find_project_nodes(project_id)
    edges = await find_edges(project_id)
    
    # Limpiar datos
    project_dict = dict(project)
    if "_id" in project_dict:
        project_dict.pop("_id")
    
    cleaned_nodes = []
    for node in nodes:
        node_dict = dict(node)
        if "_id" in node_dict:
            node_dict.pop("_id")
        cleaned_nodes.append(node_dict)
    
    cleaned_edges = []
    for edge in edges:
        edge_dict = dict(edge)
        if "_id" in edge_dict:
            edge_dict.pop("_id")
        cleaned_edges.append(edge_dict)
    
    # Construir respuesta detallada
    project_details = {
        "id": project_dict["id"],
        "title": project_dict["title"],
        "userId": project_dict["userId"],
        "description": project_dict["description"],
        "status": project_dict.get("status", True),
        "createdAt": project_dict["createdAt"],
        "updatedAt": project_dict["updatedAt"],
        "nodes": cleaned_nodes,
        "edges": cleaned_edges
    }
    
    return {
        "message": "Detalles del proyecto obtenidos exitosamente",
        "data": project_details
    }

@router.patch(
    "/{project_id}",
    summary="Actualizar proyecto",
    description="Actualiza título, descripción o status del proyecto.",
    responses={
        200: {
            "description": "Proyecto actualizado",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Proyecto actualizado exitosamente",
                        "data": {
                            "id": "uuid",
                            "title": "Nuevo título",
                            "description": "Nueva descripción",
                            "status": False,
                            "userId": "uuid-user",
                            "createdAt": "2025-01-01T00:00:00Z",
                            "updatedAt": "2025-01-02T00:00:00Z"
                        }
                    }
                }
            },
        },
        400: {"description": "Solicitud inválida"},
        403: {"description": "Acceso denegado"},
        404: {"description": "Proyecto no encontrado"},
    },
)
async def update_project_endpoint(
    project_id: str,
    project_data: dict = Body(..., example={"title": "Nuevo título", "description": "Nueva descripción", "status": True}),
    current_user: dict = Depends(get_current_user)
):
    # Verificar existencia y propiedad del proyecto
    project = await find_project(project_id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proyecto no encontrado"
        )
    
    if project["userId"] != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado"
        )
    
    # Validar al menos un campo para actualizar
    title = project_data.get("title")
    description = project_data.get("description")
    status_val = project_data.get("status")
    
    if title is None and description is None and status_val is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Al menos uno de los campos 'title', 'description' o 'status' debe ser proporcionado"
        )
    
    # Construir datos de actualización
    update_data = {}
    if title is not None:
        update_data["title"] = title.strip()
    if description is not None:
        update_data["description"] = description.strip()
    if status_val is not None:
        update_data["status"] = status_val
    
    update_data["updatedAt"] = datetime.utcnow()
    
    # Actualizar proyecto
    updated_project = await update_project(project_id, update_data)
    
    return {
        "message": "Proyecto actualizado exitosamente",
        "data": updated_project
    }

@router.delete(
    "/{project_id}",
    summary="Eliminar proyecto",
    description="Elimina un proyecto del usuario y sus datos asociados.",
    responses={
        200: {
            "description": "Proyecto eliminado",
            "content": {"application/json": {"example": {"message": "Proyecto eliminado exitosamente"}}},
        },
        403: {"description": "Acceso denegado"},
        404: {"description": "Proyecto no encontrado"},
        500: {"description": "Error al eliminar"},
    },
)
async def delete_project_endpoint(project_id: str, current_user: dict = Depends(get_current_user)):
    # Verificar existencia y propiedad del proyecto
    project = await find_project(project_id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proyecto no encontrado"
        )
    
    if project["userId"] != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado"
        )
    
    # Eliminar proyecto y datos asociados
    success = await delete_project(project_id)
    
    if success:
        return {
            "message": "Proyecto eliminado exitosamente"
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al eliminar el proyecto"
        )
