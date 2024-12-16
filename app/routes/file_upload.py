from fastapi import APIRouter, UploadFile, HTTPException, Form
from minio import Minio
from app.config import Settings
import os
from pydantic import BaseModel
import io
from typing import List
from app.models import DeleteFilesRequest, CreateBucketRequest, CreateFolderRequest

settings = Settings()
router = APIRouter()

# Initialize MinIO client
minio_client = Minio(
    settings.MINIO_URL.replace("http://", "").replace("https://", ""),
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=settings.MINIO_URL.startswith("https")
)

# Ensure the bucket exists
if not minio_client.bucket_exists(settings.BUCKET_NAME):
    minio_client.make_bucket(settings.BUCKET_NAME)


@router.post("/create-bucket/")
async def create_bucket(request: CreateBucketRequest):
    bucket_name = request.bucket_name

    # Check if the bucket already exists
    if minio_client.bucket_exists(bucket_name):
        raise HTTPException(status_code=400, detail=f"Bucket '{bucket_name}' already exists.")

    try:
        # Create the bucket if it doesn't exist
        minio_client.make_bucket(bucket_name)
        return {"message": f"Bucket '{bucket_name}' created successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating bucket: {str(e)}")

# Create folder endpoint
@router.post("/create-folder/")
async def create_folder(request: CreateFolderRequest):
    bucket_name = request.bucket_name
    folder_name = request.folder_name

    if not folder_name.endswith('/'):
        folder_name += '/'  # Ensure the folder name ends with a slash ('/')

    # Check if the bucket exists
    if not minio_client.bucket_exists(bucket_name):
        raise HTTPException(status_code=404, detail=f"Bucket '{bucket_name}' does not exist")

    try:
        # Use io.BytesIO to create an in-memory file-like object with no content
        empty_data = io.BytesIO()

        # Create an empty object to represent the folder in the bucket
        minio_client.put_object(
            bucket_name=bucket_name,
            object_name=folder_name,  # This creates a "folder" in MinIO
            data=empty_data,  # Pass the in-memory file-like object
            length=0,  # Zero length since it's an empty folder
            content_type="application/x-directory"  # Optionally set the content type for folder-like objects
        )
        return {"message": f"Folder '{folder_name}' created successfully in bucket '{bucket_name}'!"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating folder: {str(e)}")
    
# File upload endpoint that accepts bucket_name and folder_name
# Ensure the bucket exists
if not minio_client.bucket_exists(settings.BUCKET_NAME):
    minio_client.make_bucket(settings.BUCKET_NAME)

# Request body model for file upload (bucket_name, folder_name, and file)
@router.post("/fileupload/")
async def upload_file(
    bucket_name: str = Form(...),  # Bucket name as form data
    folder_name: str = Form(...),  # Folder name as form data
    file: UploadFile = Form(...)    # The actual file to upload
):
    # Validate that the file is a PDF
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only .pdf files are allowed")

    # Calculate the file size
    file_size = len(await file.read())  # Read the file and calculate its size

    # Rewind the file after reading to make sure it can be uploaded
    file.file.seek(0)

    # Ensure the folder name ends with a slash ('/')
    if not folder_name.endswith('/'):
        folder_name += '/'

    # Construct the full object name with folder and file name
    object_name = folder_name + file.filename

    # Check if the bucket exists
    if not minio_client.bucket_exists(bucket_name):
        raise HTTPException(status_code=404, detail=f"Bucket '{bucket_name}' does not exist")

    try:
        # Upload file to MinIO with the correct length and bucket
        result = minio_client.put_object(
            bucket_name=bucket_name,
            object_name=object_name,
            data=file.file,
            length=file_size,  # Use the actual file size here
            content_type=file.content_type
        )
        return {"message": f"File '{file.filename}' uploaded successfully to folder '{folder_name}' in bucket '{bucket_name}'!", "etag": result.etag}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")
    
@router.post("/fileuploads/")
async def upload_files(
    bucket_name: str = Form(...),  # Bucket name as form data
    folder_name: str = Form(...),   # Folder name as form data
    files: List[UploadFile] = Form(...)  # List of files to upload
):
    uploaded_files_info = []  # Store information about uploaded files

    # Ensure the folder name ends with a slash ('/')
    if not folder_name.endswith('/'):
        folder_name += '/'

    # Check if the bucket exists
    if not minio_client.bucket_exists(bucket_name):
        raise HTTPException(status_code=404, detail=f"Bucket '{bucket_name}' does not exist")

    for file in files:
        # Validate that the file is a PDF
        if not file.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only .pdf files are allowed")

        # Calculate the file size
        file_size = len(await file.read())  # Read the file and calculate its size

        # Rewind the file after reading to make sure it can be uploaded
        file.file.seek(0)

        # Construct the full object name with folder and file name
        object_name = folder_name + file.filename

        try:
            # Upload file to MinIO with the correct length and bucket
            result = minio_client.put_object(
                bucket_name=bucket_name,
                object_name=object_name,
                data=file.file,
                length=file_size,  # Use the actual file size here
                content_type=file.content_type
            )
            uploaded_files_info.append({"filename": file.filename, "etag": result.etag})
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error uploading file '{file.filename}': {str(e)}")

    return {
        "message": f"{len(files)} files uploaded successfully to folder '{folder_name}' in bucket '{bucket_name}'!",
        "uploaded_files": uploaded_files_info
    }

@router.get("/filereview/")
async def review_files(bucket_name: str, folder_name: str):
    # Ensure the folder name ends with a slash ('/')
    if not folder_name.endswith('/'):
        folder_name += '/'

    # Check if the bucket exists
    if not minio_client.bucket_exists(bucket_name):
        raise HTTPException(status_code=404, detail=f"Bucket '{bucket_name}' does not exist")

    try:
        # List objects in the specified folder within the bucket
        objects = minio_client.list_objects(bucket_name, prefix=folder_name, recursive=True)
        
        # Prepare a list to hold file details
        files_info = []
        for obj in objects:
            files_info.append({
                "filename": obj.object_name.replace(folder_name, ""),  # Strip the folder name from object name
                "etag": obj.etag,
                "size": obj.size,
                "last_modified": obj.last_modified.isoformat()  # Convert to ISO format for better readability
            })

        if not files_info:
            return {"message": f"No files found in folder '{folder_name}' of bucket '{bucket_name}'."}

        return {
            "message": f"Files retrieved successfully from folder '{folder_name}' in bucket '{bucket_name}'.",
            "files": files_info
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving files: {str(e)}")


@router.delete("/filedelete/")
async def delete_file(bucket_name: str, folder_name: str, filename: str):
    # Ensure the folder name ends with a slash ('/')
    if not folder_name.endswith('/'):
        folder_name += '/'

    # Construct the full object name
    object_name = folder_name + filename

    # Check if the bucket exists
    if not minio_client.bucket_exists(bucket_name):
        raise HTTPException(status_code=404, detail=f"Bucket '{bucket_name}' does not exist")

    try:
        # Remove the object from MinIO
        minio_client.remove_object(bucket_name, object_name)
        return {"message": f"File '{filename}' deleted successfully from folder '{folder_name}' in bucket '{bucket_name}'!"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")
    
@router.delete("/filesdelete/")
async def delete_files(request: DeleteFilesRequest):
    bucket_name = request.bucket_name
    folder_name = request.folder_name
    filenames = request.filenames

    # Ensure the folder name ends with a slash ('/')
    if not folder_name.endswith('/'):
        folder_name += '/'

    # Check if the bucket exists
    if not minio_client.bucket_exists(bucket_name):
        raise HTTPException(status_code=404, detail=f"Bucket '{bucket_name}' does not exist")

    deleted_files_info = []

    for filename in filenames:
        # Construct the full object name
        object_name = folder_name + filename
        
        try:
            # Remove the object from MinIO
            minio_client.remove_object(bucket_name, object_name)
            deleted_files_info.append(filename)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting file '{filename}': {str(e)}")

    return {
        "message": f"{len(deleted_files_info)} files deleted successfully from folder '{folder_name}' in bucket '{bucket_name}'.",
        "deleted_files": deleted_files_info
    }

@router.delete("/folderdelete/")
async def delete_folder(bucket_name: str, folder_name: str):
    # Ensure the folder name ends with a slash ('/')
    if not folder_name.endswith('/'):
        folder_name += '/'

    # Check if the bucket exists
    if not minio_client.bucket_exists(bucket_name):
        raise HTTPException(status_code=404, detail=f"Bucket '{bucket_name}' does not exist")

    try:
        # List objects in the specified folder
        objects = minio_client.list_objects(bucket_name, prefix=folder_name, recursive=True)
        
        # Delete each object found in the folder
        for obj in objects:
            minio_client.remove_object(bucket_name, obj.object_name)

        return {"message": f"Folder '{folder_name}' and its contents deleted successfully from bucket '{bucket_name}'!"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting folder: {str(e)}")
    
@router.delete("/bucketdelete/")
async def delete_bucket(bucket_name: str):
    # Check if the bucket exists
    if not minio_client.bucket_exists(bucket_name):
        raise HTTPException(status_code=404, detail=f"Bucket '{bucket_name}' does not exist")

    try:
        # List objects in the bucket
        objects = minio_client.list_objects(bucket_name, recursive=True)
        
        # Delete each object found in the bucket
        for obj in objects:
            minio_client.remove_object(bucket_name, obj.object_name)

        # Now remove the bucket itself
        minio_client.remove_bucket(bucket_name)
        
        return {"message": f"Bucket '{bucket_name}' and all its contents deleted successfully!"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting bucket: {str(e)}")