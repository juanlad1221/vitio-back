from fastapi import APIRouter, Depends, HTTPException, status, Query
from datetime import datetime
import uuid
import json

from auth import get_current_user
from database import (
    insert_node, find_node, find_project_nodes, 
    insert_edge, find_edges, find_project, 
    db_instance
)

router = APIRouter(prefix="/api/node", tags=["Nodo"])

@router.post("/", include_in_schema=False)
async def create_node(node_data: dict, current_user: dict = Depends(get_current_user)):
    project_id = node_data.get("projectId")
    source_node_id = node_data.get("sourceNodeId")
    attributes = node_data.get("attributes", {})
    type_edge = node_data.get("typeEdge", "default")
    
    project = await find_project(project_id)
    
    if not project or project["userId"] != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    async with db_instance.pool.acquire() as conn:
        last_order_row = await conn.fetchrow("""
            SELECT MAX(node_order) as max_order FROM nodes WHERE project_id = $1
        """, project_id)
        next_order = (last_order_row["max_order"] or 0) + 1
    
    current_time = datetime.utcnow()
    node_id = str(uuid.uuid4())
    
    new_node = {
        "id": node_id,
        "type": attributes.get("type", "default"),
        "position": attributes.get("position", {"x": 0, "y": 0}),
        "data": attributes.get("data"),
        "nodeOrder": next_order,
        "projectId": project_id,
        "createdAt": current_time,
        "updatedAt": current_time
    }
    
    await insert_node(new_node)
    
    if source_node_id:
        edge_id = str(uuid.uuid4())
        new_edge = {
            "id": edge_id,
            "type": type_edge,
            "source": source_node_id,
            "target": node_id,
            "projectId": project_id,
            "createdAt": current_time,
            "updatedAt": current_time
        }
        await insert_edge(new_edge)
    
    return {
        "message": "Se ha creado el nodo exitosamente",
        "data": new_node
    }

@router.get("/details", include_in_schema=False)
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

@router.patch("/{id}", include_in_schema=False)
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

@router.delete("/{id}", include_in_schema=False)
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

@router.patch("/reset/position/{id}", include_in_schema=False)
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
