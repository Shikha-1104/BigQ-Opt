"""
Data models for GCP Cost Optimization Dashboard.

This module defines dataclasses for storing optimization results
across different modules (SQL, Storage, Scheduling, ML).
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class SQLOptimizationResult:
    """
    Represents the result of SQL query optimization.
    
    Attributes:
        query_id: Unique identifier for the query
        original_query: The unoptimized SQL query
        optimized_query: The AI-optimized SQL query
        bytes_before: Bytes processed by original query
        bytes_after: Bytes processed by optimized query
        cost_before_usd: Estimated cost of original query in USD
        cost_after_usd: Estimated cost of optimized query in USD
        savings_percent: Percentage of cost savings achieved
        optimizations_applied: List of optimization techniques applied
        timestamp: When the optimization was performed
    """
    query_id: str
    original_query: str
    optimized_query: str
    bytes_before: int
    bytes_after: int
    cost_before_usd: float
    cost_after_usd: float
    savings_percent: float
    optimizations_applied: List[str]
    timestamp: datetime


@dataclass
class StorageOptimizationResult:
    """
    Represents the result of storage bucket optimization analysis.
    
    Attributes:
        bucket_name: Name of the GCS bucket
        current_size_gb: Current size of the bucket in GB
        current_storage_class: Current storage class (STANDARD, NEARLINE, etc.)
        last_accessed: Last access timestamp
        issue: Identified issue with current configuration
        suggestion: Recommended optimization action
        estimated_savings_percent: Estimated percentage of cost savings
        estimated_savings_usd: Estimated cost savings in USD
        action_type: Type of action (move, delete, compress, lifecycle)
    """
    bucket_name: str
    current_size_gb: float
    current_storage_class: str
    last_accessed: datetime
    issue: str
    suggestion: str
    estimated_savings_percent: float
    estimated_savings_usd: float
    action_type: str


@dataclass
class ScheduleOptimizationResult:
    """
    Represents the result of scheduled query optimization analysis.
    
    Attributes:
        query_name: Name of the scheduled query
        current_cron: Current CRON schedule expression
        suggested_cron: Recommended CRON schedule expression
        current_daily_cost: Current estimated daily cost in USD
        suggested_daily_cost: Suggested estimated daily cost in USD
        optimization_type: Type of optimization (reduce_frequency, merge, materialized_view)
        reasoning: Explanation for the optimization recommendation
        estimated_savings_percent: Estimated percentage of cost savings
    """
    query_name: str
    current_cron: str
    suggested_cron: str
    current_daily_cost: float
    suggested_daily_cost: float
    optimization_type: str
    reasoning: str
    estimated_savings_percent: float


@dataclass
class MLOptimizationResult:
    """
    Represents the result of ML training job optimization analysis.
    
    Attributes:
        job_name: Name of the ML training job
        current_accelerator: Current accelerator type (T4, V100, A100, TPU)
        suggested_accelerator: Recommended accelerator type
        current_cost: Current estimated cost in USD
        suggested_cost: Suggested estimated cost in USD
        optimization_type: Type of optimization (spot_vm, machine_type, autoscaling, caching)
        estimated_savings_percent: Estimated percentage of cost savings
        implementation_notes: Additional notes for implementing the optimization
    """
    job_name: str
    current_accelerator: str
    suggested_accelerator: str
    current_cost: float
    suggested_cost: float
    optimization_type: str
    estimated_savings_percent: float
    implementation_notes: str
