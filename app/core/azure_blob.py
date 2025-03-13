# app/core/azure_blob.py
from fastapi import UploadFile
from azure.storage.blob import BlobServiceClient, ContentSettings
from azure.storage.blob.aio import BlobClient
from app.config import settings
import uuid
import aiohttp
import asyncio

async def upload_to_blob(file: UploadFile) -> str:
    """
    Upload a file to Azure Blob Storage
    
    Args:
        file: The file to upload
        
    Returns:
        The blob name (path) in Azure Blob Storage
    """
    try:
        # Create a unique blob name using UUID
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else ''
        blob_name = f"{uuid.uuid4()}.{file_extension}"
        
        # Get connection string from settings
        connection_string = settings.AZURE_STORAGE_CONNECTION_STRING
        container_name = settings.AZURE_STORAGE_CONTAINER_NAME
        
        # Create blob client
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service_client.get_container_client(container_name)
        
        # Ensure container exists
        if not container_client.exists():
            container_client.create_container(public_access="blob")
        
        # Get blob client
        blob_client = container_client.get_blob_client(blob_name)
        
        # Set content type based on file extension
        content_type = "application/pdf"
        if file_extension.lower() in ['doc', 'docx']:
            content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        
        # Read file content
        contents = await file.read()
        
        # Upload file
        blob_client.upload_blob(
            contents, 
            overwrite=True,
            content_settings=ContentSettings(content_type=content_type)
        )
        
        return blob_name
    
    except Exception as e:
        print(f"Error uploading to blob storage: {str(e)}")
        raise

async def get_blob_url(blob_name: str) -> str:
    """
    Get the URL for a blob
    
    Args:
        blob_name: The name of the blob
        
    Returns:
        The URL for the blob
    """
    try:
        connection_string = settings.AZURE_STORAGE_CONNECTION_STRING
        container_name = settings.AZURE_STORAGE_CONTAINER_NAME
        
        # Create blob client
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        account_name = blob_service_client.account_name
        
        # Construct the blob URL
        blob_url = f"https://{account_name}.blob.core.windows.net/{container_name}/{blob_name}"
        
        return blob_url
    
    except Exception as e:
        print(f"Error getting blob URL: {str(e)}")
        raise

async def delete_blob(blob_name: str) -> bool:
    """
    Delete a blob from Azure Blob Storage
    
    Args:
        blob_name: The name of the blob to delete
        
    Returns:
        True if deletion was successful, False otherwise
    """
    try:
        connection_string = settings.AZURE_STORAGE_CONNECTION_STRING
        container_name = settings.AZURE_STORAGE_CONTAINER_NAME
        
        # Create blob client
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service_client.get_container_client(container_name)
        blob_client = container_client.get_blob_client(blob_name)
        
        # Delete the blob
        blob_client.delete_blob()
        
        return True
    
    except Exception as e:
        print(f"Error deleting blob: {str(e)}")
        return False