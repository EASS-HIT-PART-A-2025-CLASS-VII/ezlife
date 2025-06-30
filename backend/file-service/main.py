from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import os
import shutil
from datetime import datetime
import uuid
from pymongo import MongoClient
from bson.objectid import ObjectId
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_db

app = FastAPI(title="EZLife File Service")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.pdf', '.txt'}

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "file-service"}

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    user_id: str = Form(...),
    db: MongoClient = Depends(get_db)
):
    """Upload a file and save metadata to MongoDB"""
    
    _, ext = os.path.splitext(file.filename)
    if ext.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"File type {ext} not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    unique_filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")
    
    # Save metadata to MongoDB
    file_metadata = {
        "original_filename": file.filename,
        "storage_filename": unique_filename,
        "file_path": file_path,
        "file_type": ext.lower().replace('.', ''),
        "file_size": os.path.getsize(file_path),
        "upload_time": datetime.utcnow(),
        "description": description,
        "user_id": user_id
    }
    
    # Insert into MongoDB
    try:
        result = db.files.insert_one(file_metadata)
        file_metadata["_id"] = str(result.inserted_id)
        # Remove the absolute file path from the response for security reasons
        response_data = {k: v for k, v in file_metadata.items() if k != 'file_path'}
        return response_data
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Error saving file metadata: {str(e)}")

@app.get("/files/{user_id}")
async def list_files(user_id: str, db: MongoClient = Depends(get_db)):
    """List all files for a specific user"""
    try:
        files = list(db.files.find({"user_id": user_id}))
        for file in files:
            file["_id"] = str(file["_id"])
            if "file_path" in file:
                del file["file_path"]
        return files
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving files: {str(e)}")

@app.get("/files/download/{file_id}")
async def download_file(file_id: str, db: MongoClient = Depends(get_db)):
    """Download a file by its ID"""
    try:
        file_data = db.files.find_one({"_id": ObjectId(file_id)})
        if not file_data:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_path = file_data.get("file_path")
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found on server")
        
        return FileResponse(
            path=file_path, 
            filename=file_data.get("original_filename"),
            media_type=f"application/{file_data.get('file_type')}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading file: {str(e)}")

@app.delete("/files/{file_id}")
async def delete_file(file_id: str, db: MongoClient = Depends(get_db)):
    """Delete a file by its ID"""
    try:
        # Find the file in MongoDB
        file_data = db.files.find_one({"_id": ObjectId(file_id)})
        if not file_data:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Delete the file from disk
        file_path = file_data.get("file_path")
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        
        # Delete metadata from MongoDB
        db.files.delete_one({"_id": ObjectId(file_id)})
        
        return {"message": "File deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
