"""BigQuery Service for cost optimization dashboard."""

from google.cloud import bigquery
from typing import Dict, List, Optional
import os
import streamlit as st


class BigQueryService:
    """Service for interacting with Google BigQuery API."""
    
    def __init__(self, project_id: str, credentials_path: Optional[str] = None):
        """
        Initialize BigQuery client with proper authentication.
        
        Args:
            project_id: GCP project ID
            credentials_path: Path to service account JSON (optional)
        """
        self.project_id = project_id
        self.credentials_path = credentials_path
        
        # Set credentials environment variable if provided
        if credentials_path:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        
        # Initialize BigQuery client
        self.client = bigquery.Client(project=project_id)

    @st.cache_data(ttl=3600, show_spinner=False)
    def dry_run_query(_self, query: str) -> Dict:
        """
        Execute a dry-run to estimate query cost without running the query.
        Cached for 1 hour to improve performance.
        
        Args:
            query: SQL query to analyze
            
        Returns:
            Dictionary with:
                - total_bytes_processed: int
                - estimated_cost_usd: float
                - success: bool
                - error: str (if any)
        """
        # Configure job for dry-run
        job_config = bigquery.QueryJobConfig(
            dry_run=True,
            use_query_cache=False
        )
        
        try:
            # Execute dry-run query
            job = _self.client.query(query, job_config=job_config)
            bytes_processed = job.total_bytes_processed
            
            # Calculate estimated cost using $5 per TB formula
            cost_usd = (bytes_processed / (1024**4)) * 5.0
            
            return {
                "total_bytes_processed": bytes_processed,
                "estimated_cost_usd": cost_usd,
                "success": True,
                "error": None
            }
        except Exception as e:
            return {
                "total_bytes_processed": 0,
                "estimated_cost_usd": 0.0,
                "success": False,
                "error": str(e)
            }

    @st.cache_resource
    def get_public_datasets(_self) -> List[Dict]:
        """
        Return list of available BigQuery public datasets.
        Cached as a resource since this data is static.
        
        Returns:
            List of datasets with:
                - dataset_id: str
                - table_id: str
                - description: str
        """
        return [
            {
                "dataset_id": "bigquery-public-data.new_york_citibike",
                "table_id": "citibike_trips",
                "description": "NYC Citibike trip data with bike sharing information"
            },
            {
                "dataset_id": "bigquery-public-data.samples",
                "table_id": "natality",
                "description": "US natality data with birth statistics"
            },
            {
                "dataset_id": "bigquery-public-data.google_analytics_sample",
                "table_id": "ga_sessions_20170801",
                "description": "Google Analytics sample data for web analytics"
            }
        ]

    def get_table_schema(self, dataset: str, table: str) -> Dict:
        """
        Retrieve table schema from BigQuery API.
        
        Args:
            dataset: Full dataset ID (e.g., 'bigquery-public-data.samples')
            table: Table name
            
        Returns:
            Dictionary with:
                - columns: List[Dict] with name and type
                - partition_field: str (if any)
                - clustering_fields: List[str]
        """
        try:
            # Get table reference
            table_ref = f"{dataset}.{table}"
            table_obj = self.client.get_table(table_ref)
            
            # Extract column information
            columns = [
                {
                    "name": field.name,
                    "type": field.field_type,
                    "mode": field.mode
                }
                for field in table_obj.schema
            ]
            
            # Extract partition field if exists
            partition_field = None
            if table_obj.time_partitioning:
                partition_field = table_obj.time_partitioning.field
            
            # Extract clustering fields if exist
            clustering_fields = []
            if table_obj.clustering_fields:
                clustering_fields = list(table_obj.clustering_fields)
            
            return {
                "columns": columns,
                "partition_field": partition_field,
                "clustering_fields": clustering_fields
            }
        except Exception as e:
            return {
                "columns": [],
                "partition_field": None,
                "clustering_fields": [],
                "error": str(e)
            }



class BigQueryErrorHandler:
    """Handler for BigQuery API errors."""
    
    @staticmethod
    def handle_dry_run_error(error: Exception) -> Dict:
        """
        Handle BigQuery dry-run errors gracefully.
        
        Args:
            error: Exception from BigQuery API
            
        Returns:
            Dictionary with:
                - error_type: str
                - user_message: str
        """
        error_message = str(error)
        
        # Check for syntax errors
        if "Syntax error" in error_message or "syntax" in error_message.lower():
            return {
                "error_type": "syntax",
                "user_message": "Invalid SQL syntax. Please check your query for errors."
            }
        
        # Check for table not found
        if "Not found" in error_message or "not found" in error_message.lower():
            return {
                "error_type": "not_found",
                "user_message": "Table or dataset not found. Please verify the dataset and table names."
            }
        
        # Check for permission denied
        if "Permission denied" in error_message or "permission" in error_message.lower():
            return {
                "error_type": "permission",
                "user_message": "Insufficient permissions to access this resource. Please check your credentials."
            }
        
        # Check for quota exceeded
        if "Quota exceeded" in error_message or "quota" in error_message.lower():
            return {
                "error_type": "quota",
                "user_message": "BigQuery quota exceeded. Please try again later or increase your quota."
            }
        
        # Unknown error
        return {
            "error_type": "unknown",
            "user_message": f"An error occurred: {error_message}"
        }
