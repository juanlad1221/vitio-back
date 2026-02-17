import json
import os
import sys
from io import BytesIO
from unittest.mock import patch

from fastapi.testclient import TestClient

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from main import app
from auth import create_access_token
import routers.media as media_router


def run():
    client = TestClient(app)

    # Token para usuario simulado
    fake_user_id = "user-123"
    token = create_access_token({"sub": fake_user_id})

    # Datos simulados
    media_id = "media-abc"  # ID interno en BD
    bucket_id = "vau_media/oldid"  # public_id en Cloudinary
    old_url = "https://res.cloudinary.com/demo/image/upload/v1234567890/vau_media/oldid.jpg"
    fake_user_media = [
        {
            "id": media_id,
            "user_id": fake_user_id,
            "title": "Imagen antigua",
            "description": "desc",
            "size": 1000,
            "type": "IMAGE",
            "ext": "jpg",
            "url": old_url,
            "bucket_id": bucket_id,
            "status": "active",
            "project_id": None,
            "createdAt": "2025-01-01T00:00:00Z",
            "updatedAt": "2025-01-01T00:00:00Z",
        }
    ]

    upload_result = {
        "url": "https://res.cloudinary.com/demo/image/upload/v1234567891/vau_media/newid.jpg",
        "public_id": "vau_media/newid",
        "resource_type": "image",
        "format": "jpg",
        "size": 12345,
        "contentType": "image/jpeg",
        "width": 100,
        "height": 100,
    }

    updated_db_record = {
        "id": media_id,
        "user_id": fake_user_id,
        "title": "Imagen antigua",
        "description": "desc",
        "size": upload_result["size"],
        "type": "IMAGE",
        "ext": upload_result["format"],
        "url": upload_result["url"],
        "bucket_id": upload_result["public_id"],
        "status": "active",
        "createdAt": "2025-01-01T00:00:00Z",
        "updatedAt": "2025-01-02T00:00:00Z",
    }

    with patch.object(media_router, "db_find_media", return_value=fake_user_media), \
         patch.object(media_router.CloudinaryService, "upload_file", return_value=upload_result), \
         patch.object(media_router.CloudinaryService, "get_file_info", return_value={}), \
         patch.object(media_router.CloudinaryService, "delete_file", return_value=True), \
         patch.object(media_router, "db_update_media", return_value=updated_db_record):

        files = {"file": ("newfile.jpg", BytesIO(b"fakecontent"), "image/jpeg")}
        headers = {"Authorization": f"Bearer {token}"}

        # La ruta ahora usa id interno como identificador
        response = client.patch(f"/api/media/item/{media_id}/replace", files=files, headers=headers)

        print("Status:", response.status_code)
        try:
            print("Body:", json.dumps(response.json(), indent=2, ensure_ascii=False))
        except Exception:
            print("Body (raw):", response.text)


if __name__ == "__main__":
    run()
