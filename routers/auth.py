from fastapi import APIRouter, Depends, HTTPException, status, Body
from datetime import timedelta
import uuid
import re

from auth import get_password_hash, verify_password, create_access_token, get_current_user
from database import insert_user, find_user, update_user
from config import settings

router = APIRouter(prefix="/api/auth", tags=["Autenticación"])

@router.post(
    "/register",
    summary="Registro de usuario",
    description="Crea un nuevo usuario con email, contraseña y nombre.",
    responses={
        200: {
            "description": "Usuario registrado correctamente",
            "content": {
                "application/json": {
                    "example": {"message": "User registered successfully"}
                }
            },
        },
        400: {"description": "Validación inválida"},
    },
)
async def register(
    user_data: dict = Body(
        ...,
        example={"email": "user@example.com", "password": "secret123", "name": "Juan"},
    )
):
    email = user_data.get("email")
    password = user_data.get("password")
    name = user_data.get("name")
    
    # Validate email
    if not email or not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email"
        )
    
    # Validate required fields
    if not password or not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password and name are required"
        )
    
    # Check if user already exists
    existing_user = await find_user({"email": email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    user_id = str(uuid.uuid4())
    hashed_password = get_password_hash(password)
    
    new_user = {
        "id": user_id,
        "email": email,
        "password": hashed_password,
        "name": name
    }
    
    await insert_user(new_user)
    
    return {"message": "User registered successfully"}

@router.post(
    "/login",
    summary="Inicio de sesión",
    description="Autentica al usuario y devuelve un token JWT.",
    responses={
        200: {
            "description": "Login correcto",
            "content": {
                "application/json": {
                    "example": {
                        "message": "User logged in successfully",
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                    }
                }
            },
        },
        400: {"description": "Credenciales inválidas"},
    },
)
async def login(
    credentials: dict = Body(
        ...,
        example={"email": "user@example.com", "password": "secret123"},
    )
):
    email = credentials.get("email")
    password = credentials.get("password")
    
    if not email or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email and password are required"
        )
    
    # Find user by email
    user = await find_user({"email": email})
    if not user or not verify_password(password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid credentials"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user["id"]}, expires_delta=access_token_expires
    )
    
    return {
        "message": "User logged in successfully",
        "access_token": access_token
    }

@router.patch(
    "/update-password",
    summary="Actualizar contraseña",
    description="Actualiza la contraseña del usuario autenticado.",
    responses={
        200: {
            "description": "Contraseña actualizada",
            "content": {
                "application/json": {"example": {"message": "Password updated successfully"}}
            },
        },
        400: {"description": "Solicitud inválida"},
        404: {"description": "Usuario no encontrado"},
    },
)
async def update_password(
    password_data: dict = Body(..., example={"password": "newStrongPassword123"}),
    current_user: dict = Depends(get_current_user)
):
    password = password_data.get("password")
    
    if not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is required"
        )
    
    # Update user password
    hashed_password = get_password_hash(password)
    update_data = {"password": hashed_password}
    
    updated_user = await update_user(current_user["user_id"], update_data)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "Password updated successfully"}
