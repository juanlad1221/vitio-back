# Vau API - Backend para aplicación similar a VideoAsk con Cloudinary

Backend FastAPI para alimentar una aplicación React similar a VideoAsk, basado en la especificación de la API original, ahora con **Cloudinary** para almacenamiento multimedia.

## 🚀 Características

- 🚀 **FastAPI** - Framework web moderno y rápido
- 🗄️ **MongoDB** - Base de datos NoSQL para almacenar datos
- 🔐 **JWT Authentication** - Autenticación segura con tokens
- ☁️ **Cloudinary Storage** - Almacenamiento en la nube para archivos multimedia
- 🎬 **Video Flow** - Sistema de nodos y aristas para crear flujos de video
- 📊 **Auto-documentación** - Documentación Swagger/OpenAPI automática

## 📦 Cambios recientes: Integración con Cloudinary

### ✅ Nuevo Sistema de Storage:
- **Cloudinary Service**: Subida automática de imágenes/videos/audio
- **Optimización**: Procesamiento automático de archivos
- **CDN**: Distribución global de contenido
- **Seguridad**: URLs seguras con firmas digitales

### 🔄 Flujo de Subida Mejorado:

```mermaid
sequenceDiagram
    participant C as Cliente React
    participant API as FastAPI Backend
    participant CL as Cloudinary
    participant DB as MongoDB
    
    C->>API: POST /api/media/upload + file
    API->>API: Validar archivo
    API->>CL: Subir archivo a Cloudinary
    CL->>API: URL segura + metadatos
    API->>DB: Guardar metadatos + URL Cloudinary
    API->>C: Respuesta con URL de Cloudinary
```

## 📁 Estructura del Proyecto

```
back-vito/
├── main.py                    # Aplicación principal FastAPI
├── config.py                  # Configuración y variables de entorno
├── database.py                # Conexión y operaciones con MongoDB
├── auth.py                    # Lógica de autenticación y JWT
├── cloudinary_service.py     # 🆕 Servicio de Cloudinary
├── schemas.py                  # Modelos Pydantic para validación
├── requirements.txt            # Dependencias (actualizado con cloudinary)
├── .env                      # Variables de entorno (incluye Cloudinary)
├── README.md                  # Documentación completa
├── uploads/                   # Directorio de respaldo (legacy)
└── routers/                   # Módulos de la API
    ├── auth.py               # Endpoints de autenticación
    ├── projects.py           # Gestión de proyectos
    ├── nodes.py              # Gestión de nodos/flujo
    └── media.py              # 🔄 Gestión de archivos con Cloudinary
```

## 🔧 Configuración de Cloudinary

### 1. Crear cuenta en Cloudinary:
1. Regístrate en [cloudinary.com](https://cloudinary.com)
2. Obtén tu **Cloud Name**, **API Key** y **API Secret**
3. Crea un **Upload Preset** con nombre `vau_media_uploads`

### 2. Configurar variables de entorno:
```bash
# Agrega a tu .env
CLOUDINARY_CLOUD_NAME="your-cloud-name"
CLOUDINARY_API_KEY="your-api-key" 
CLOUDINARY_API_SECRET="your-api-secret"
CLOUDINARY_UPLOAD_PRESET="vau_media_uploads"
```

## 📋 Endpoints Actualizados

### 🎬 Media (con Cloudinary)
- `POST /api/media/upload` - Subir archivo a Cloudinary
- `GET /api/media/{type}` - Listar archivos por tipo (VIDEO/IMAGE/AUDIO)
- `PATCH /api/media/{media_id}` - Actualizar metadatos
- `DELETE /api/media/{media_id}` - Eliminar de Cloudinary y BD
- `GET /api/media/info/{public_id}` - Obtener información detallada de Cloudinary

### 📊 Nuevo Flujo de Almacenamiento:

| Componente | Cloudinary | Base de Datos | Ejemplo |
|-------------|-------------|----------------|----------|
| **Archivo físico** | ✅ (nube) | ❌ | `cloudinary://vau_media/abc123.jpg` |
| **URL segura** | ✅ | ✅ | `https://res.cloudinary.com/...` |
| **Metadatos** | ❌ | ✅ | Título, tamaño, tipo, dueño |
| **Optimización** | ✅ | ❌ | Auto-optimización por Cloudinary |
| **CDN Global** | ✅ | ❌ | Distribución automática |

## 🚀 Instalación

### 1. Instalar dependencias actualizadas:
```bash
cd /Users/juan-c/Dev/Back/back-vito
pip install -r requirements.txt
```

### 2. Configurar Cloudinary:
```bash
# Editar .env con tus credenciales de Cloudinary
CLOUDINARY_CLOUD_NAME="tu-cloud-name"
CLOUDINARY_API_KEY="tu-api-key"
CLOUDINARY_API_SECRET="tu-api-secret"
```

### 3. Iniciar el servidor:
```bash
uvicorn main:app --reload --port 8000
```

## 🧪 Ejemplo de Uso

### Subir imagen a Cloudinary:
```bash
curl -X POST http://localhost:8000/api/media/upload \
  -H "Authorization: Bearer {token}" \
  -F "title=Mi imagen" \
  -F "type=IMAGE" \
  -F "description=Descripción de la imagen" \
  -F "file=@/ruta/imagen.jpg"
```

**Respuesta:**
```json
{
  "url": "https://res.cloudinary.com/your-cloud/vau_media/abc123.jpg",
  "media_id": 12345,
  "contentType": "image/jpeg",
  "public_id": "vau_media/abc123",
  "resource_type": "image",
  "size": 1024000
}
```

## 🎯 Ventajas de Cloudinary

### ✅ **Beneficios:**
- **Almacenamiento ilimitado** - Sin preocupaciones de espacio local
- **CDN Global** - Entrega rápida desde cualquier ubicación
- **Auto-optimización** - Reducción automática de tamaño
- **Transformaciones** - Resize, crop, filtros en tiempo real
- **Seguridad** - URLs firmadas y acceso controlado
- **Backup** - Redundancia automática

### 🔄 **Transformaciones disponibles:**
```javascript
// Ejemplo: Thumbnail automático
https://res.cloudinary.com/demo/image/upload/w_150,h_150,c_fill/vau_media/image.jpg

// Ejemplo: Optimización automática  
https://res.cloudinary.com/demo/image/upload/q_auto/vau_media/image.jpg
```

## 📋 Ejemplos de Queries

### Media con metadatos de Cloudinary:
```javascript
// Documento en MongoDB con Cloudinary
{
  "id": 12345,
  "user_id": "user-uuid",
  "title": "Video de bienvenida",
  "type": "VIDEO",
  "status": "TRANSCODED",
  "url": "https://res.cloudinary.com/...",
  "public_id": "vau_media/unique_id",
  "resource_type": "video",
  "size": 1048576,
  "contentType": "video/mp4",
  "duration": 30.5,  // Solo para videos
  "width": 1920,
  "height": 1080,
  "createdAt": "2025-01-28T13:15:00Z",
  "updatedAt": "2025-01-28T13:15:00Z"
}
```

## 🌐 Despliegue en Producción

### Configuración recomendada:
```bash
# .env de producción
DEBUG=false
SECRET_KEY="super-secret-key-production"
MONGODB_URL="mongodb://cluster:password@mongodb.net/db"
CLOUDINARY_CLOUD_NAME="production-cloud"
CLOUDINARY_API_KEY="production-key"
CLOUDINARY_API_SECRET="production-secret"
```

### Features Cloudinary para producción:
- **Dominio personalizado**: `media.tuapp.com`
- **Seguridad avanzada**: Upload presets seguros
- **Analytics**: Estadísticas de uso de media
- **Backup automático**: Políticas de retención

¡Listo! 🎉 Tu backend ahora usa **Cloudinary** para almacenamiento profesional en la nube.