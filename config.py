import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for GCP Cost Optimization Dashboard"""
    
    # BigQuery settings
    BIGQUERY_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
    BIGQUERY_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    # AI settings
    AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Public datasets for SQL optimization
    PUBLIC_DATASETS = [
        {
            "name": "Google Analytics E-commerce",
            "dataset": "bigquery-public-data.google_analytics_sample",
            "table": "ga_sessions_20170801",
            "description": "Google Analytics 360 e-commerce data with transactions, products, and user behavior"
        },
        {
            "name": "TheLook E-commerce",
            "dataset": "bigquery-public-data.thelook_ecommerce",
            "table": "orders",
            "description": "Synthetic e-commerce dataset with orders, products, users, and inventory"
        },
        {
            "name": "TheLook E-commerce Products",
            "dataset": "bigquery-public-data.thelook_ecommerce",
            "table": "products",
            "description": "Product catalog with categories, brands, pricing, and inventory levels"
        },
        {
            "name": "TheLook E-commerce Users",
            "dataset": "bigquery-public-data.thelook_ecommerce",
            "table": "users",
            "description": "Customer demographics and registration data"
        }
    ]
    
    # Simulation settings
    DEFAULT_QUERY_COUNT = 10
    DEFAULT_BUCKET_COUNT = 10
    DEFAULT_SCHEDULE_COUNT = 10
    DEFAULT_ML_JOB_COUNT = 10
    
    # Cost constants (USD)
    BIGQUERY_COST_PER_TB = 50.0  # $50 per TB of data processed (increased for better visualization)
    
    # GCS Storage costs per GB per month
    GCS_STANDARD_COST_PER_GB = 0.020
    GCS_NEARLINE_COST_PER_GB = 0.010
    GCS_COLDLINE_COST_PER_GB = 0.004
    GCS_ARCHIVE_COST_PER_GB = 0.0012
    
    # ML/Compute costs (approximate hourly rates in USD)
    GPU_COSTS = {
        "T4": 0.35,      # NVIDIA T4
        "V100": 2.48,    # NVIDIA V100
        "A100": 3.67,    # NVIDIA A100
        "TPU_V2": 4.50,  # TPU v2
        "TPU_V3": 8.00   # TPU v3
    }
    
    # Spot VM discount percentage
    SPOT_VM_DISCOUNT = 0.70  # 70% discount on average
    
    @classmethod
    def validate(cls):
        """Validate that required configuration is present"""
        errors = []
        
        if not cls.BIGQUERY_PROJECT_ID:
            errors.append("GCP_PROJECT_ID is not set")
        
        if cls.AI_PROVIDER == "gemini" and not cls.GEMINI_API_KEY:
            errors.append("GEMINI_API_KEY is required when using Gemini provider")
        
        if cls.AI_PROVIDER == "openai" and not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is required when using OpenAI provider")
        
        if cls.AI_PROVIDER not in ["gemini", "openai"]:
            errors.append("AI_PROVIDER must be either 'gemini' or 'openai'")
        
        return errors
