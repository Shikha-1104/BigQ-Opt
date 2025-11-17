"""ML Job Simulator for generating training job metadata."""

import random
from typing import List, Dict


class MLJobSimulator:
    """Generates ML training job metadata."""
    
    # Accelerator types with typical characteristics
    ACCELERATOR_CONFIGS = {
        "T4": {
            "gpu_hours_range": (2, 20),
            "cpu_hours_range": (4, 40),
            "peak_nodes_range": (1, 4),
            "cost_per_hour": 0.35
        },
        "V100": {
            "gpu_hours_range": (5, 50),
            "cpu_hours_range": (10, 100),
            "peak_nodes_range": (2, 8),
            "cost_per_hour": 2.48
        },
        "A100": {
            "gpu_hours_range": (10, 100),
            "cpu_hours_range": (20, 200),
            "peak_nodes_range": (4, 16),
            "cost_per_hour": 3.67
        },
        "TPU": {
            "gpu_hours_range": (8, 80),
            "cpu_hours_range": (16, 160),
            "peak_nodes_range": (1, 8),
            "cost_per_hour": 4.50
        }
    }
    
    # Job name templates
    JOB_TYPES = [
        "image_classification",
        "nlp_transformer",
        "recommendation_model",
        "object_detection",
        "time_series_forecast",
        "sentiment_analysis",
        "fraud_detection",
        "customer_churn",
        "demand_prediction",
        "anomaly_detection"
    ]
    
    def generate_training_jobs(self, count: int = 10) -> List[Dict]:
        """
        Generates ML training job metadata.
        
        Args:
            count: Number of training jobs to generate
            
        Returns:
            List of training job dictionaries with keys:
            - job_name: str
            - gpu_hours: float
            - cpu_hours: float
            - peak_nodes: int
            - accelerator_type: str (T4, V100, A100, TPU)
            - training_duration_hours: float
            - estimated_cost: float
        """
        training_jobs = []
        
        for i in range(count):
            # Select accelerator type
            accelerator_type = random.choice(list(self.ACCELERATOR_CONFIGS.keys()))
            config = self.ACCELERATOR_CONFIGS[accelerator_type]
            
            # Generate job name
            job_type = random.choice(self.JOB_TYPES)
            job_name = f"{job_type}_training_{i+1}"
            
            # Generate resource usage based on accelerator type
            gpu_hours = round(random.uniform(*config["gpu_hours_range"]), 2)
            cpu_hours = round(random.uniform(*config["cpu_hours_range"]), 2)
            peak_nodes = random.randint(*config["peak_nodes_range"])
            
            # Calculate training duration (assuming parallel execution)
            training_duration_hours = round(gpu_hours / peak_nodes, 2)
            
            # Calculate estimated cost
            estimated_cost = round(gpu_hours * config["cost_per_hour"], 2)
            
            training_jobs.append({
                "job_name": job_name,
                "gpu_hours": gpu_hours,
                "cpu_hours": cpu_hours,
                "peak_nodes": peak_nodes,
                "accelerator_type": accelerator_type,
                "training_duration_hours": training_duration_hours,
                "estimated_cost": estimated_cost
            })
        
        return training_jobs
