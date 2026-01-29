#!/bin/bash

echo "🚀 Starting Vau API with MongoDB Atlas + Cloudinary..."

# Export environment variables
export CLOUDINARY_CLOUD_NAME="daako1jzi"
export CLOUDINARY_API_KEY="853528968267547"
export CLOUDINARY_API_SECRET="3_nZ5PEJV9OWnNVm8ej5QoSzucg"
export MONGODB_URL="mongodb+srv://juanlad1221:Y@nome1221@cluster-test.zakd7ag.mongodb.net/vau_db"

# Start server
echo "✅ Environment variables loaded"
echo "🔗 Starting server on http://localhost:8000"
echo "📊 Documentation: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"
uvicorn main:app --reload --port 8000