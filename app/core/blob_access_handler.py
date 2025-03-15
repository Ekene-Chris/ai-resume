# app/core/blob_access_handler.py
import logging
import re
from typing import Tuple, Optional
from azure.core.exceptions import ResourceNotFoundError, HttpResponseError, ClientAuthenticationError
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta
from app.config import settings

logger = logging.getLogger(__name__)

class BlobAccessHandler:
    """
    Handler for blob storage access issues that provides diagnostics 
    and generates SAS tokens when needed
    """
    
    def __init__(self):
        self.storage_account_name = settings.AZURE_STORAGE_ACCOUNT_NAME
        self.connection_string = settings.AZURE_STORAGE_CONNECTION_STRING
        self.container_name = settings.AZURE_STORAGE_CONTAINER_NAME
    
    async def diagnose_blob_access_error(self, blob_name: str, error: Exception) -> Tuple[str, bool]:
        """
        Diagnose blob access errors and provide detailed error messages
        
        Args:
            blob_name: The name of the blob that failed to access
            error: The exception that was raised
            
        Returns:
            Tuple containing (error_message, is_fixable)
        """
        error_str = str(error)
        error_type = type(error).__name__
        
        # Log detailed error information
        logger.error(f"Blob access error ({error_type}): {error_str}")
        
        # Check for common access errors
        if isinstance(error, ResourceNotFoundError) or "ResourceNotFound" in error_str:
            # Check if the container exists but the blob doesn't
            try:
                blob_service = BlobServiceClient.from_connection_string(self.connection_string)
                container_client = blob_service.get_container_client(self.container_name)
                
                if container_client.exists():
                    # Container exists, but blob might not
                    blob_exists = False
                    for blob in container_client.list_blobs(name_starts_with=blob_name):
                        if blob.name == blob_name:
                            blob_exists = True
                            break
                    
                    if not blob_exists:
                        return f"The requested file '{blob_name}' does not exist in the container.", False
                    else:
                        return f"Access to the file '{blob_name}' is restricted.", True
                else:
                    return f"The storage container '{self.container_name}' does not exist.", False
            except Exception as container_check_error:
                logger.error(f"Error checking container existence: {str(container_check_error)}")
                return f"Storage container access issue: {str(container_check_error)}", False
        
        # Check for network/public access issues
        elif "InvalidContent" in error_str and "Could not download the file from the given URL" in error_str:
            return "The file cannot be accessed. This is likely due to blob storage network restrictions or access policies.", True
            
        elif isinstance(error, HttpResponseError) or "HttpResponseError" in error_str:
            if "403" in error_str or "Forbidden" in error_str:
                return "Access to the storage is forbidden. The blob may have restricted access or require authentication.", True
            elif "404" in error_str or "Not Found" in error_str:
                return "The requested file or storage container could not be found.", False
            else:
                return f"HTTP error accessing blob storage: {error_str}", True
                
        elif isinstance(error, ClientAuthenticationError) or "authentication failed" in error_str.lower():
            return "Authentication to blob storage failed. The connection string or credentials may be invalid.", False
            
        else:
            # Generic error message for unknown errors
            return f"Error accessing file in storage: {error_str}", False
    
    async def generate_sas_url(self, blob_name: str) -> Optional[str]:
        """
        Generate a SAS token URL for a blob to enable temporary access
        
        Args:
            blob_name: The name of the blob to generate a SAS token for
            
        Returns:
            SAS URL for the blob or None if generation fails
        """
        try:
            # Parse the connection string to get account key
            conn_parts = self.connection_string.split(';')
            account_key = None
            
            for part in conn_parts:
                if part.startswith('AccountKey='):
                    account_key = part.split('=', 1)[1]
                    break
            
            if not account_key:
                logger.error("Could not extract account key from connection string")
                return None
            
            # Create a SAS token with read permissions that expires in 1 hour
            expiry = datetime.utcnow() + timedelta(hours=1)
            
            sas_token = generate_blob_sas(
                account_name=self.storage_account_name,
                container_name=self.container_name,
                blob_name=blob_name,
                account_key=account_key,
                permission=BlobSasPermissions(read=True),
                expiry=expiry
            )
            
            # Construct the full URL
            sas_url = f"https://{self.storage_account_name}.blob.core.windows.net/{self.container_name}/{blob_name}?{sas_token}"
            
            logger.info(f"Generated SAS URL for blob {blob_name} expiring at {expiry}")
            return sas_url
            
        except Exception as e:
            logger.error(f"Error generating SAS token: {str(e)}")
            return None
    
    async def get_accessible_url(self, blob_name: str, original_url: str) -> str:
        """
        Attempt to get an accessible URL for a blob, generating a SAS token if needed
        
        Args:
            blob_name: The name of the blob
            original_url: The original blob URL that failed
            
        Returns:
            Accessible URL for the blob (either original or with SAS token)
        """
        # First check if the original URL is directly accessible
        import aiohttp
        
        try:
            logger.info(f"Testing accessibility of blob URL: {original_url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.head(original_url, timeout=10) as response:
                    if response.status == 200:
                        logger.info(f"Original URL is accessible: {original_url}")
                        return original_url
                    else:
                        logger.warning(f"Original URL returned status {response.status}")
        except Exception as e:
            logger.warning(f"Error testing URL accessibility: {str(e)}")
        
        # If we're here, the original URL is not accessible - try SAS token
        logger.info(f"Generating SAS token for blob: {blob_name}")
        sas_url = await self.generate_sas_url(blob_name)
        
        if sas_url:
            return sas_url
        else:
            # If SAS generation fails, return the original URL as a fallback
            logger.warning(f"Failed to generate SAS URL, returning original URL")
            return original_url

# Create singleton instance
blob_access_handler = BlobAccessHandler()