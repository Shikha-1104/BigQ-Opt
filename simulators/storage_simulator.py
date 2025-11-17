"""Storage Simulator for generating synthetic GCS bucket metadata."""

import random
from datetime import datetime, timedelta
from typing import List, Dict


class StorageSimulator:
    """Generates synthetic GCS bucket metadata."""
    
    # Storage class options
    STORAGE_CLASSES = ["STANDARD", "NEARLINE", "COLDLINE", "ARCHIVE"]
    
    # GCP regions
    REGIONS = [
        "us-central1", "us-east1", "us-west1", "us-west2",
        "europe-west1", "europe-west2", "asia-east1", "asia-southeast1"
    ]
    
    # Bucket name prefixes for realistic names
    BUCKET_PREFIXES = [
        "prod-data", "dev-logs", "analytics", "backups", "ml-datasets",
        "user-uploads", "archive", "temp-storage", "reports", "media-assets"
    ]
    
    def generate_bucket_metadata(self, count: int = 10) -> List[Dict]:
        """
        Generates synthetic GCS bucket metadata.
        
        Args:
            count: Number of buckets to generate
            
        Returns:
            List of bucket metadata dictionaries with keys:
            - name: str
            - size_gb: float
            - last_accessed: datetime
            - region: str
            - storage_class: str (STANDARD, NEARLINE, COLDLINE, ARCHIVE)
        """
        buckets = []
        
        for i in range(count):
            # Generate realistic bucket name
            prefix = random.choice(self.BUCKET_PREFIXES)
            suffix = random.randint(1000, 9999)
            bucket_name = f"{prefix}-{suffix}"
            
            # Generate size with realistic distribution
            # Most buckets are small, some are large
            size_distribution = random.random()
            if size_distribution < 0.5:  # 50% small buckets (< 100 GB)
                size_gb = round(random.uniform(1, 100), 2)
            elif size_distribution < 0.8:  # 30% medium buckets (100-1000 GB)
                size_gb = round(random.uniform(100, 1000), 2)
            else:  # 20% large buckets (1-10 TB)
                size_gb = round(random.uniform(1000, 10000), 2)
            
            # Generate last accessed date
            # Some buckets are recently accessed, others are old
            days_ago = random.randint(1, 365)
            last_accessed = datetime.now() - timedelta(days=days_ago)
            
            # Assign storage class based on access pattern
            # Old data more likely to be in cold storage
            if days_ago < 30:
                storage_class = random.choice(["STANDARD", "NEARLINE"])
            elif days_ago < 90:
                storage_class = random.choice(["STANDARD", "NEARLINE", "COLDLINE"])
            else:
                storage_class = random.choice(["NEARLINE", "COLDLINE", "ARCHIVE"])
            
            # Select region
            region = random.choice(self.REGIONS)
            
            buckets.append({
                "name": bucket_name,
                "size_gb": size_gb,
                "last_accessed": last_accessed,
                "region": region,
                "storage_class": storage_class
            })
        
        return buckets
