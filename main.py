import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Load environment variables BEFORE importing config
from dotenv import load_dotenv
load_dotenv()

from routers import auth, projects, nodes, media
from config import settings
from database import db_instance
import cloudinary

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting FastAPI with PostgreSQL + Cloudinary")
    print(f"PostgreSQL URL: {settings.database_url}")
    print(f"Cloudinary Cloud: {settings.cloudinary_cloud_name}")
    
    # Initialize Cloudinary
    try:
        cloudinary.config(
            cloud_name=settings.cloudinary_cloud_name,
            api_key=settings.cloudinary_api_key,
            api_secret=settings.cloudinary_api_secret
        )
        print("🚀 Cloudinary configured successfully")
    except Exception as e:
        print(f"❌ Cloudinary configuration failed: {e}")
    
    # Initialize PostgreSQL connection
    try:
        await db_instance.connect()
        print("🚀 Database connection established successfully")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        raise e
    
    yield
    # Shutdown
    print("Shutting down FastAPI")
    await db_instance.disconnect()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your React app URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(nodes.router)
app.include_router(media.router)

@app.get("/")
async def root():
    return {"message": "Vau API - Backend para VideoAsk-like application with MongoDB Atlas + Cloudinary"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "cloudinary": "configured" if settings.cloudinary_cloud_name else "missing",
        "database": "mongodb_atlas" if "mongodb+srv://" in settings.mongodb_url else "local"
    }
