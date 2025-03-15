# app/core/azure_blob.py - Update with access diagnostics
from fastapi import UploadFile
from azure.storage.blob import BlobServiceClient, ContentSettings, generate_blob_sas, BlobSasPermissions
from azure.storage.blob.aio import BlobClient
from azure.core.exceptions import ResourceNotFoundError, HttpResponseError, ClientAuthenticationError
from app.config import settings
from datetime import datetime, timedelta
import uuid
import aiohttp
import asyncio
import logging

logger = logging.getLogger(__name__)

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
            logger.info(f"Creating blob container: {container_name}")
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
        
        logger.info(f"Successfully uploaded file to blob storage: {blob_name}")
        return blob_name
    
    except Exception as e:
        logger.error(f"Error uploading to blob storage: {str(e)}", exc_info=True)
        raise

async def get_blob_url(blob_name: str) -> str:
    """
    Get the URL for a blob with diagnostic checks
    
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
        
        # Check if the blob exists
        container_client = blob_service_client.get_container_client(container_name)
        blob_client = container_client.get_blob_client(blob_name)
        
        # Verify blob exists
        try:
            blob_properties = blob_client.get_blob_properties()
            logger.info(f"Blob exists: {blob_name}, size: {blob_properties.size} bytes")
        except ResourceNotFoundError:
            logger.error(f"Blob not found: {blob_name}")
            raise Exception(f"The file '{blob_name}' was not found in storage.")
        except Exception as access_error:
            logger.warning(f"Could not verify blob exists: {str(access_error)}")
            # Continue anyway - we'll handle access issues at usage time
        
        # Construct the blob URL
        blob_url = f"https://{account_name}.blob.core.windows.net/{container_name}/{blob_name}"
        
        # Check if the blob is publicly accessible
        try:
            async with aiohttp.ClientSession() as session:
                async with session.head(blob_url, timeout=5) as response:
                    if response.status == 200:
                        logger.info(f"Blob is publicly accessible: {blob_url}")
                    else:
                        logger.warning(f"Blob may not be publicly accessible (status {response.status})")
                        # We'll create a SAS token later if needed when actual access fails
        except Exception as test_error:
            logger.warning(f"Could not test blob accessibility: {str(test_error)}")
        
        return blob_url
    
    except Exception as e:
        logger.error(f"Error getting blob URL: {str(e)}", exc_info=True)
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
        logger.info(f"Deleted blob: {blob_name}")
        
        return True
    
    except ResourceNotFoundError:
        logger.warning(f"Attempted to delete non-existent blob: {blob_name}")
        return True  # Consider it successful if already gone
    except Exception as e:
        logger.error(f"Error deleting blob: {str(e)}", exc_info=True)
        return False

async def generate_sas_url(blob_name: str, expiry_hours: int = 2) -> str:
    """
    Generate a SAS URL for a blob providing temporary authenticated access
    
    Args:
        blob_name: The name of the blob
        expiry_hours: Hours until the SAS token expires
        
    Returns:
        SAS URL for the blob
    """
    try:
        connection_string = settings.AZURE_STORAGE_CONNECTION_STRING
        container_name = settings.AZURE_STORAGE_CONTAINER_NAME
        
        # Parse connection string to get account details
        account_name = None
        account_key = None
        
        for part in connection_string.split(";"):
            if part.startswith("AccountName="):
                account_name = part.split("=", 1)[1]
            elif part.startswith("AccountKey="):
                account_key = part.split("=", 1)[1]
                
        if not account_name or not account_key:
            logger.error("Could not extract account details from connection string")
            raise Exception("Invalid connection string format")
            
        # Generate SAS token
        expiry = datetime.utcnow() + timedelta(hours=expiry_hours)
        
        sas_token = generate_blob_sas(
            account_name=account_name,
            container_name=container_name,
            blob_name=blob_name,
            account_key=account_key,
            permission=BlobSasPermissions(read=True),
            expiry=expiry
        )
        
        # Construct the SAS URL
        sas_url = f"https://{account_name}.blob.core.windows.net/{container_name}/{blob_name}?{sas_token}"
        
        logger.info(f"Generated SAS URL for blob {blob_name} (expires in {expiry_hours} hours)")
        return sas_url
        
    except Exception as e:
        logger.error(f"Error generating SAS URL: {str(e)}", exc_info=True)
        raise