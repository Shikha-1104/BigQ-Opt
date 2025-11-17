"""SQL Query Simulator for generating unoptimized queries."""

import random
from typing import List


class SQLQuerySimulator:
    """Generates unoptimized SQL queries with common anti-patterns."""
    
    def generate_unoptimized_queries(
        self, 
        dataset: str, 
        table: str, 
        count: int = 10
    ) -> List[str]:
        """
        Generates unoptimized SQL queries with common anti-patterns.
        
        Args:
            dataset: BigQuery public dataset name
            table: Table name within the dataset
            count: Number of queries to generate (5-10)
            
        Returns:
            List of unoptimized SQL query strings
        """
        queries = []
        full_table = f"`{dataset}.{table}`"
        
        # Anti-pattern templates
        templates = [
            # SELECT * without column specification
            f"SELECT * FROM {full_table}",
            
            # Missing WHERE clause - full table scan
            f"SELECT * FROM {full_table} ORDER BY RAND() LIMIT 100",
            
            # No partition filter
            f"SELECT * FROM {full_table} LIMIT 1000",
            
            # CROSS JOIN creating cartesian product
            f"SELECT * FROM {full_table} t1 CROSS JOIN {full_table} t2 LIMIT 10",
            
            # Unnecessary subquery
            f"SELECT * FROM (SELECT * FROM {full_table}) AS subquery",
            
            # SELECT * with unnecessary JOIN
            f"SELECT * FROM {full_table} t1 JOIN {full_table} t2 ON t1.id = t2.id",
            
            # Large aggregation without filters
            f"SELECT COUNT(*), AVG(*) FROM {full_table}",
            
            # SELECT * with DISTINCT (processes all columns)
            f"SELECT DISTINCT * FROM {full_table}",
            
            # Multiple unnecessary subqueries
            f"SELECT * FROM (SELECT * FROM (SELECT * FROM {full_table}) t1) t2 LIMIT 50",
            
            # Full table scan with complex expression
            f"SELECT * FROM {full_table} WHERE 1=1 ORDER BY RAND()",
        ]
        
        # Select random queries up to count
        selected_queries = random.sample(templates, min(count, len(templates)))
        
        return selected_queries
