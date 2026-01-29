from fastapi import APIRouter, Depends, HTTPException, status, Query
from datetime import datetime
import uuid

from auth import get_current_user
from database import get_nodes_collection, get_edges_collection, get_projects_collection

router = APIRouter(prefix="/api/node", tags=["Nodo"])

@router.post("/", include_in_schema=False)
async def create_node(node_data: dict, current_user: dict = Depends(get_current_user)):
    project_id = node_data.get("projectId")
    source_node_id = node_data.get("sourceNodeId")
    target_node_id = node_data.get("targetNodeId")
    attributes = node_data.get("attributes", {})
    type_edge = node_data.get("typeEdge", "default")
    
    # Verify project belongs to user
    projects_collection = await get_projects_collection()
    project = await projects_collection.find_one({
        "id": project_id,
        "userId": current_user["user_id"]
    })
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    nodes_collection = await get_nodes_collection()
    edges_collection = await get_edges_collection()
    
    current_time = datetime.utcnow()
    node_id = str(uuid.uuid4())
    
    # Create node
    new_node = {
        "id": node_id,
        "type": attributes.get("type", "default"),
        "position": attributes.get("position", {"x": 0, "y": 0}),
        "data": attributes.get("data"),
        "projectId": project_id,
        "createdAt": current_time,
        "updatedAt": current_time
    }
    
    await nodes_collection.insert_one(new_node)
    
    # Create edge
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
    
    await edges_collection.insert_one(new_edge)
    
    return {
        "message": "Se ha creado el nodo exitosamente",
        "data": new_node
    }

@router.get("/details", include_in_schema=False)
async def get_node_details(id: str = Query(...), current_user: dict = Depends(get_current_user)):
    nodes_collection = await get_nodes_collection()
    
    node = await nodes_collection.find_one({"id": id})
    
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found"
        )
    
    # Verify node belongs to user's project
    projects_collection = await get_projects_collection()
    project = await projects_collection.find_one({
        "id": node["projectId"],
        "userId": current_user["user_id"]
    })
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    node_dict = dict(node)
    if "_id" in node_dict:
        node_dict.pop("_id")
    node_dict["projectId"] = node["projectId"]
    
    return node_dict

@router.patch("/{id}", include_in_schema=False)
async def update_node(
    id: str,
    node_data: dict,
    current_user: dict = Depends(get_current_user)
):
    nodes_collection = await get_nodes_collection()
    
    # Get node and verify ownership
    node = await nodes_collection.find_one({"id": id})
    
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found"
        )
    
    # Verify node belongs to user's project
    projects_collection = await get_projects_collection()
    project = await projects_collection.find_one({
        "id": node["projectId"],
        "userId": current_user["user_id"]
    })
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Validate at least one field is provided
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
    
    update_data["updatedAt"] = datetime.utcnow()
    
    await nodes_collection.update_one(
        {"id": id},
        {"$set": update_data}
    )
    
    return {"message": "Nodo actualizado exitosamente"}

@router.delete("/{id}", include_in_schema=False)
async def delete_node(id: str, current_user: dict = Depends(get_current_user)):
    nodes_collection = await get_nodes_collection()
    
    # Get node and verify ownership
    node = await nodes_collection.find_one({"id": id})
    
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found"
        )
    
    # Verify node belongs to user's project
    projects_collection = await get_projects_collection()
    project = await projects_collection.find_one({
        "id": node["projectId"],
        "userId": current_user["user_id"]
    })
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Delete node and associated edges
    edges_collection = await get_edges_collection()
    
    await nodes_collection.delete_one({"id": id})
    await edges_collection.delete_many({"$or": [{"source": id}, {"target": id}]})
    
    return {"message": "Nodo eliminado exitosamente"}

@router.patch("/reset/position/{id}", include_in_schema=False)
async def reset_node_position(id: str, current_user: dict = Depends(get_current_user)):
    nodes_collection = await get_nodes_collection()
    
    # Get node and verify ownership
    node = await nodes_collection.find_one({"id": id})
    
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found"
        )
    
    # Verify node belongs to user's project
    projects_collection = await get_projects_collection()
    project = await projects_collection.find_one({
        "id": node["projectId"],
        "userId": current_user["user_id"]
    })
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Reset position to origin
    await nodes_collection.update_one(
        {"id": id},
        {
            "$set": {
                "position": {"x": 0, "y": 0},
                "updatedAt": datetime.utcnow()
            }
        }
    )
    
    return {"message": "Posicion del nodo reseteada exitosamente"}
