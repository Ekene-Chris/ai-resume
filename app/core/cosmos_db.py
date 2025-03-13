# app/core/cosmos_db.py
from azure.cosmos import CosmosClient, PartitionKey, exceptions
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class CosmosDBService:
    def __init__(self):
        # Initialize the Cosmos client
        self.client = CosmosClient(settings.COSMOS_DB_ENDPOINT, settings.COSMOS_DB_KEY)
        
        # Get or create database
        self.database = self._get_or_create_database(settings.COSMOS_DB_DATABASE)
        
        # Get or create container for CV analyses
        self.analyses_container = self._get_or_create_container(
            self.database,
            settings.COSMOS_DB_ANALYSES_CONTAINER,
            partition_key=PartitionKey(path="/analysis_id")
        )

    def _get_or_create_database(self, database_name):
        """Get a database by name, or create it if it doesn't exist"""
        try:
            return self.client.get_database_client(database_name)
        except exceptions.CosmosResourceNotFoundError:
            logger.info(f"Creating database: {database_name}")
            return self.client.create_database(database_name)

    def _get_or_create_container(self, database, container_name, partition_key):
        """Get a container by name, or create it if it doesn't exist"""
        try:
            return database.get_container_client(container_name)
        except exceptions.CosmosResourceNotFoundError:
            logger.info(f"Creating container: {container_name}")
            return database.create_container(id=container_name, partition_key=partition_key)

    async def create_analysis_record(self, metadata):
        """Create a new analysis record in Cosmos DB"""
        try:
            return self.analyses_container.create_item(body=metadata)
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Error creating analysis record: {str(e)}")
            raise

    async def update_analysis_record(self, analysis_id, updates):
        """Update an existing analysis record"""
        try:
            # First get the current record
            current_record = self.analyses_container.read_item(
                item=analysis_id,
                partition_key=analysis_id
            )
            
            # Update the record with new data
            for key, value in updates.items():
                current_record[key] = value
            
            # Replace the item in the container
            return self.analyses_container.replace_item(
                item=current_record['id'],
                body=current_record
            )
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Error updating analysis record: {str(e)}")
            raise

    async def get_analysis_record(self, analysis_id):
        """Get an analysis record by ID"""
        try:
            return self.analyses_container.read_item(
                item=analysis_id,
                partition_key=analysis_id
            )
        except exceptions.CosmosResourceNotFoundError:
            return None
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Error getting analysis record: {str(e)}")
            raise

    async def list_analyses(self, query=None, parameters=None):
        """List analysis records with optional filtering"""
        if query is None:
            query = "SELECT * FROM c"
            
        try:
            items = list(self.analyses_container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            return items
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Error listing analyses: {str(e)}")
            raise
            
    async def delete_analysis_record(self, analysis_id):
        """Delete an analysis record by ID"""
        try:
            self.analyses_container.delete_item(
                item=analysis_id,
                partition_key=analysis_id
            )
            return True
        except exceptions.CosmosResourceNotFoundError:
            return False
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Error deleting analysis record: {str(e)}")
            raise

# Singleton instance
cosmos_service = CosmosDBService()