import asyncpg
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
from config import settings

# PostgreSQL Database Configuration (loaded from .env via config)
DATABASE_URL = settings.database_url
DATABASE_NAME = settings.database_name

# Database connection pool
class PostgreSQLDatabase:
    pool: Optional[asyncpg.Pool] = None
    
    async def connect(self):
        """Initialize PostgreSQL connection pool"""
        if not DATABASE_URL:
            raise RuntimeError("DATABASE_URL no configurado. Define DATABASE_URL en el .env")
        self.pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10, command_timeout=60)
        print(f"✅ Connected to PostgreSQL: {DATABASE_NAME}")
        await self.create_tables()
    
    async def disconnect(self):
        """Close PostgreSQL connection pool"""
        if self.pool:
            await self.pool.close()
            print("🔌 Disconnected from PostgreSQL")
    
    async def create_tables(self):
        """Create tables if they don't exist"""
        async with self.pool.acquire() as conn:
            # Users table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Projects table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    user_id TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # Add status column if it doesn't exist (migration)
            try:
                await conn.execute("""
                    ALTER TABLE projects ADD COLUMN IF NOT EXISTS status BOOLEAN DEFAULT true
                """)
                print("✅ Added status column to projects table")
            except Exception as e:
                print(f"ℹ️ Status column already exists or error: {e}")
            
            # Nodes table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS nodes (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    position JSONB NOT NULL,
                    data JSONB,
                    project_id TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                )
            """)
            
            # Edges table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS edges (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    source TEXT NOT NULL,
                    target TEXT NOT NULL,
                    project_id TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                )
            """)
            
            # Media table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS media (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    size INTEGER DEFAULT 0,
                    type TEXT NOT NULL,
                    ext TEXT,
                    url TEXT NOT NULL,
                    status TEXT DEFAULT 'active',
                    project_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                )
            """)

            # Add project_id column to media table if it doesn't exist (migration for existing tables)
            try:
                await conn.execute("""
                    ALTER TABLE media 
                    ADD COLUMN IF NOT EXISTS project_id TEXT REFERENCES projects(id) ON DELETE CASCADE
                """)
            except Exception as e:
                pass # Column likely exists
            
            print("📋 Database tables verified/created")

# Global database instance
db_instance = PostgreSQLDatabase()

# Collection functions (compatibility layer)
async def get_users_collection():
    return db_instance

async def get_projects_collection():
    return db_instance

async def get_nodes_collection():
    return db_instance

async def get_media_collection():
    return db_instance

async def get_edges_collection():
    return db_instance

# PostgreSQL Database Operations
async def insert_user(user_data):
    async with db_instance.pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO users (id, email, password, name, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (id) DO NOTHING
        """, user_data["id"], user_data["email"], user_data["password"], 
             user_data["name"], datetime.utcnow(), datetime.utcnow())
    return {"inserted_id": user_data["id"]}

async def find_user(query):
    if not query or not query.get("email"):
        return None
    
    async with db_instance.pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT id, email, password, name, created_at, updated_at
            FROM users WHERE email = $1
        """, query["email"])
        
        if row:
            return {
                "id": row["id"],
                "email": row["email"],
                "password": row["password"],
                "name": row["name"],
                "createdAt": row["created_at"].isoformat(),
                "updatedAt": row["updated_at"].isoformat()
            }
        print(f"❌ Project NOT found...")
    return None

async def find_users():
    async with db_instance.pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, email, password, name, created_at, updated_at
            FROM users ORDER BY created_at DESC
        """)
        
        return [{
            "id": row["id"],
            "email": row["email"],
            "password": row["password"],
            "name": row["name"],
            "createdAt": row["created_at"].isoformat(),
            "updatedAt": row["updated_at"].isoformat()
        } for row in rows]

async def insert_project(project_data):
    async with db_instance.pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO projects (id, title, description, status, user_id, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """, project_data["id"], project_data["title"], project_data["description"],
             project_data.get("status", True), project_data["userId"], datetime.utcnow(), datetime.utcnow())
    return {"inserted_id": project_data["id"]}

async def find_project(project_id):
    async with db_instance.pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT id, title, description, status, user_id, created_at, updated_at
            FROM projects WHERE id = $1
        """, project_id)
    
        if row:
            return {
                "id": row["id"],
                "title": row["title"],
                "description": row["description"],
                "status": row["status"],
                "userId": row["user_id"],
                "createdAt": row["created_at"].isoformat(),
                "updatedAt": row["updated_at"].isoformat()
            }
    return None

async def find_user_projects(user_id):
    async with db_instance.pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, title, description, status, user_id, created_at, updated_at
            FROM projects WHERE user_id = $1 ORDER BY updated_at DESC
        """, user_id)
        
        return [{
            "id": row["id"],
            "title": row["title"],
            "description": row["description"],
            "status": row["status"],
            "userId": row["user_id"],
            "createdAt": row["created_at"].isoformat(),
            "updatedAt": row["updated_at"].isoformat()
        } for row in rows]

async def update_project(project_id, update_data):
    set_clauses = []
    params = []
    param_idx = 1
    
    for key, value in update_data.items():
        if key in ["title", "description", "status"]:
            set_clauses.append(f"{key} = ${param_idx}")
            params.append(value)
            param_idx += 1
    
    if not set_clauses:
        return None
    
    set_clauses.append(f"updated_at = ${param_idx}")
    params.append(datetime.utcnow())
    params.append(project_id)
    
    async with db_instance.pool.acquire() as conn:
        result = await conn.fetchrow(f"""
            UPDATE projects 
            SET {', '.join(set_clauses)}
            WHERE id = ${param_idx + 1}
            RETURNING id, title, description, status, user_id, created_at, updated_at
        """, *params)
        
        if result:
            return {
                "id": result["id"],
                "title": result["title"],
                "description": result["description"],
                "status": result["status"],
                "userId": result["user_id"],
                "createdAt": result["created_at"].isoformat(),
                "updatedAt": result["updated_at"].isoformat()
            }
    return None

async def delete_project(project_id):
    async with db_instance.pool.acquire() as conn:
        result = await conn.execute("""
            DELETE FROM projects WHERE id = $1
        """, project_id)
        return result != "DELETE 0"

async def insert_node(node_data):
    async with db_instance.pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO nodes (id, type, position, data, project_id, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """, node_data["id"], node_data["type"], json.dumps(node_data["position"]),
             json.dumps(node_data.get("data", {})), node_data["projectId"],
             datetime.utcnow(), datetime.utcnow())
    return {"inserted_id": node_data["id"]}

async def find_node(node_id):
    async with db_instance.pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT id, type, position, data, project_id, created_at, updated_at
            FROM nodes WHERE id = $1
        """, node_id)
        
        if row:
            return {
                "id": row["id"],
                "type": row["type"],
                "position": row["position"],
                "data": row["data"],
                "projectId": row["project_id"],
                "createdAt": row["created_at"].isoformat(),
                "updatedAt": row["updated_at"].isoformat()
            }
    return None

async def find_project_nodes(project_id):
    async with db_instance.pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, type, position, data, project_id, created_at, updated_at
            FROM nodes WHERE project_id = $1 ORDER BY created_at ASC
        """, project_id)
        
        return [{
            "id": row["id"],
            "type": row["type"],
            "position": row["position"],
            "data": row["data"],
            "projectId": row["project_id"],
            "createdAt": row["created_at"].isoformat(),
            "updatedAt": row["updated_at"].isoformat()
        } for row in rows]

async def insert_edge(edge_data):
    async with db_instance.pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO edges (id, type, source, target, project_id, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """, edge_data["id"], edge_data["type"], edge_data["source"],
             edge_data["target"], edge_data["projectId"],
             datetime.utcnow(), datetime.utcnow())
    return {"inserted_id": edge_data["id"]}

async def find_edges(project_id):
    async with db_instance.pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, type, source, target, project_id, created_at, updated_at
            FROM edges WHERE project_id = $1 ORDER BY created_at ASC
        """, project_id)
        
        return [{
            "id": row["id"],
            "type": row["type"],
            "source": row["source"],
            "target": row["target"],
            "projectId": row["project_id"],
            "createdAt": row["created_at"].isoformat(),
            "updatedAt": row["updated_at"].isoformat()
        } for row in rows]

async def insert_media(media_data):
    async with db_instance.pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO media (id, user_id, title, description, size, type, ext, url, created_at, updated_at, project_id)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        """, media_data["id"], media_data["user_id"], media_data["title"],
             media_data.get("description", ""), media_data.get("size", 0),
             media_data["type"], media_data.get("ext", ""), media_data["url"],
             datetime.utcnow(), datetime.utcnow(), media_data.get("project_id"))
    return {"inserted_id": media_data["id"]}

async def find_media(query=None):
    if query:
        conditions = []
        params = []
        param_idx = 1
        
        if query.get("user_id"):
            conditions.append(f"user_id = ${param_idx}")
            params.append(query["user_id"])
            param_idx += 1
            
        if query.get("project_id"):
            conditions.append(f"project_id = ${param_idx}")
            params.append(query["project_id"])
            param_idx += 1
            
        if query.get("type"):
            conditions.append(f"type = ${param_idx}")
            params.append(query["type"])
            param_idx += 1
            
        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        
        async with db_instance.pool.acquire() as conn:
            rows = await conn.fetch(f"""
                SELECT id, user_id, title, description, size, type, ext, url, status, created_at, updated_at, project_id
                FROM media {where_clause} ORDER BY created_at DESC
            """, *params)
    else:
        async with db_instance.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, user_id, title, description, size, type, ext, url, status, created_at, updated_at, project_id
                FROM media ORDER BY created_at DESC
            """)
    
    return [{
        "id": row["id"],
        "user_id": row["user_id"],
        "title": row["title"],
        "description": row["description"],
        "size": row["size"],
        "type": row["type"],
        "ext": row["ext"],
        "url": row["url"],
        "status": row["status"],
        "project_id": row["project_id"],
        "createdAt": row["created_at"].isoformat(),
        "updatedAt": row["updated_at"].isoformat()
    } for row in rows]

async def update_media(media_id, update_data):
    set_clauses = []
    params = []
    param_idx = 1
    
    for key, value in update_data.items():
        if key in ["title", "description", "type", "status"]:
            set_clauses.append(f"{key} = ${param_idx}")
            params.append(value)
            param_idx += 1
    
    if not set_clauses:
        return None
    
    set_clauses.append(f"updated_at = ${param_idx}")
    params.append(datetime.utcnow())
    params.append(media_id)
    
    async with db_instance.pool.acquire() as conn:
        result = await conn.fetchrow(f"""
            UPDATE media 
            SET {', '.join(set_clauses)}
            WHERE id = ${param_idx + 1}
            RETURNING id, user_id, title, description, size, type, ext, url, status, created_at, updated_at
        """, *params)
        
        if result:
            return {
                "id": result["id"],
                "user_id": result["user_id"],
                "title": result["title"],
                "description": result["description"],
                "size": result["size"],
                "type": result["type"],
                "ext": result["ext"],
                "url": result["url"],
                "status": result["status"],
                "createdAt": result["created_at"].isoformat(),
                "updatedAt": result["updated_at"].isoformat()
            }
    return None

async def delete_media(media_id):
    async with db_instance.pool.acquire() as conn:
        result = await conn.execute("""
            DELETE FROM media WHERE id = $1
        """, media_id)
        return result != "DELETE 0"

async def find_user_by_id(user_id):
    async with db_instance.pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT id, email, password, name, created_at, updated_at
            FROM users WHERE id = $1
        """, user_id)
        
        if row:
            return {
                "id": row["id"],
                "email": row["email"],
                "password": row["password"],
                "name": row["name"],
                "createdAt": row["created_at"].isoformat(),
                "updatedAt": row["updated_at"].isoformat()
            }
    return None

async def update_user(user_id, update_data):
    set_clauses = []
    params = []
    param_idx = 1
    
    for key, value in update_data.items():
        if key in ["name", "password"]:
            set_clauses.append(f"{key} = ${param_idx}")
            params.append(value)
            param_idx += 1
    
    if not set_clauses:
        return None
    
    set_clauses.append(f"updated_at = ${param_idx}")
    params.append(datetime.utcnow())
    params.append(user_id)
    
    async with db_instance.pool.acquire() as conn:
        result = await conn.fetchrow(f"""
            UPDATE users 
            SET {', '.join(set_clauses)}
            WHERE id = ${param_idx + 1}
            RETURNING id, email, password, name, created_at, updated_at
        """, *params)
        
        if result:
            return {
                "id": result["id"],
                "email": result["email"],
                "password": result["password"],
                "name": result["name"],
                "createdAt": result["created_at"].isoformat(),
                "updatedAt": result["updated_at"].isoformat()
            }
    return None

print(f"✅ PostgreSQL database module initialized")
