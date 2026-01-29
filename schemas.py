from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import re

# Simple validation classes since pydantic is having issues
class EmailStr:
    def __init__(self, email: str):
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise ValueError("Invalid email format")
        self.email = email
    
    def __str__(self):
        return self.email

class BaseModel:
    def dict(self):
        return self.__dict__

# Auth DTOs
class RegisterDto(BaseModel):
    def __init__(self, email: str, password: str, name: str):
        self.email = EmailStr(email)
        self.password = password
        self.name = name

class LoginDto(BaseModel):
    def __init__(self, email: str, password: str):
        self.email = EmailStr(email)
        self.password = password

class UpdatePasswordDto(BaseModel):
    def __init__(self, password: str):
        self.password = password

# Auth Response Types
class RegisterTypes(BaseModel):
    def __init__(self, message: str):
        self.message = message

class LoginTypes(BaseModel):
    def __init__(self, message: str, access_token: str):
        self.message = message
        self.access_token = access_token

class UpdatePasswordTypes(BaseModel):
    def __init__(self, message: str):
        self.message = message

# Project DTOs
class UpdateProjectDto(BaseModel):
    def __init__(self, title: Optional[str] = None, description: Optional[str] = None, status: Optional[bool] = None):
        self.title = title
        self.description = description
        self.status = status

# Project Types
class ProjectTypes(BaseModel):
    def __init__(self, id: str, title: str, userId: str, description: str, createdAt: datetime, updatedAt: datetime, status: bool = True):
        self.id = id
        self.title = title
        self.userId = userId
        self.description = description
        self.status = status
        self.createdAt = createdAt
        self.updatedAt = updatedAt

class ProjectTypesResponse(BaseModel):
    def __init__(self, message: str, data: Dict[str, Any]):
        self.message = message
        self.data = data

# Node DTOs
class NodePositionDto(BaseModel):
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

class NodeAttributesDto(BaseModel):
    def __init__(self, type: str, position: NodePositionDto, data: Optional[Dict[str, Any]] = None):
        self.type = type
        self.position = position
        self.data = data

class NodeProjectDto(BaseModel):
    def __init__(self, projectId: str, sourceNodeId: str, targetNodeId: str, attributes: NodeAttributesDto, typeEdge: Optional[str] = None):
        self.projectId = projectId
        self.sourceNodeId = sourceNodeId
        self.targetNodeId = targetNodeId
        self.attributes = attributes
        self.typeEdge = typeEdge

class NodeAttributesUpdateDto(BaseModel):
    def __init__(self, type: Optional[str] = None, position: Optional[NodePositionDto] = None, data: Optional[Dict[str, Any]] = None):
        self.type = type
        self.position = position
        self.data = data

class UpdateNodeProjectDto(BaseModel):
    def __init__(self, attributes: NodeAttributesUpdateDto):
        self.attributes = attributes

# Node Types
class PositionNodeTypes(BaseModel):
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

class NodeTypes(BaseModel):
    def __init__(self, id: str, type: str, position: PositionNodeTypes, data: Optional[Dict[str, Any]] = None, createdAt: datetime = None, updatedAt: datetime = None):
        self.id = id
        self.type = type
        self.position = position
        self.data = data
        self.createdAt = createdAt or datetime.utcnow()
        self.updatedAt = updatedAt or datetime.utcnow()

class NodeTypesResponse(BaseModel):
    def __init__(self, message: str, data: Dict[str, Any]):
        self.message = message
        self.data = data

class DetailsNodeTypes(BaseModel):
    def __init__(self, id: str, type: str, position: PositionNodeTypes, data: Optional[Dict[str, Any]] = None, createdAt: datetime = None, updatedAt: datetime = None, projectId: str = None):
        self.id = id
        self.type = type
        self.position = position
        self.data = data
        self.createdAt = createdAt
        self.updatedAt = updatedAt
        self.projectId = projectId

# Project Details
class DetailsProjectTypes(BaseModel):
    def __init__(self, id: str, title: str, userId: str, description: str, createdAt: datetime, updatedAt: datetime, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]], status: bool = True):
        self.id = id
        self.title = title
        self.userId = userId
        self.description = description
        self.status = status
        self.createdAt = createdAt
        self.updatedAt = updatedAt
        self.nodes = nodes
        self.edges = edges

# Media DTOs
class MediaType(str, Enum):
    VIDEO = "VIDEO"
    IMAGE = "IMAGE"
    AUDIO = "AUDIO"

class UploadMediaDto(BaseModel):
    def __init__(self, title: str, description: Optional[str] = None, size: int = 0, type: MediaType = None, ext: str = ""):
        self.title = title
        self.description = description
        self.size = size
        self.type = type
        self.ext = ext

class UpdateMediaDto(BaseModel):
    def __init__(self, title: str, description: Optional[str] = None, type: MediaType = None):
        self.title = title
        self.description = description
        self.type = type

class DeleteMediaDto(BaseModel):
    def __init__(self, ext: str, type: MediaType):
        self.ext = ext
        self.type = type

# Media Types
class UploadMediaTypes(BaseModel):
    def __init__(self, url: str, media_id: int, contentType: str):
        self.url = url
        self.media_id = media_id
        self.contentType = contentType

class GetAllMediaTypes(BaseModel):
    def __init__(self, id: int, user_id: str, title: str, description: Optional[str] = None, size: int = 0, ext: str = "", status: str = "", createdAt: datetime = None, updatedAt: datetime = None):
        self.id = id
        self.user_id = user_id
        self.title = title
        self.description = description
        self.size = size
        self.ext = ext
        self.status = status
        self.createdAt = createdAt or datetime.utcnow()
        self.updatedAt = updatedAt or datetime.utcnow()