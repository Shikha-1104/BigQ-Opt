"""Schedule Simulator for generating scheduled query metadata."""

import random
from typing import List, Dict


class ScheduleSimulator:
    """Generates scheduled query metadata."""
    
    # CRON patterns for different frequencies
    CRON_PATTERNS = {
        "hourly": [
            "0 * * * *",  # Every hour
            "*/30 * * * *",  # Every 30 minutes
            "15 * * * *",  # Every hour at :15
        ],
        "daily": [
            "0 0 * * *",  # Midnight daily
            "0 6 * * *",  # 6 AM daily
            "0 12 * * *",  # Noon daily
            "0 18 * * *",  # 6 PM daily
        ],
        "weekly": [
            "0 0 * * 0",  # Sunday midnight
            "0 0 * * 1",  # Monday midnight
            "0 6 * * 1",  # Monday 6 AM
        ]
    }
    
    # Query purposes
    QUERY_PURPOSES = [
        "Daily sales aggregation",
        "User activity metrics",
        "Inventory sync",
        "Analytics dashboard refresh",
        "Data warehouse ETL",
        "Report generation",
        "Backup data export",
        "ML feature extraction",
        "Audit log processing",
        "Customer segmentation update"
    ]
    
    def generate_scheduled_queries(self, count: int = 10) -> List[Dict]:
        """
        Generates scheduled query metadata.
        
        Args:
            count: Number of scheduled queries to generate
            
        Returns:
            List of scheduled query dictionaries with keys:
            - name: str
            - cron: str (CRON expression)
            - cost_mb: float (estimated cost per run in MB processed)
            - purpose: str
            - frequency: str (hourly, daily, weekly)
        """
        scheduled_queries = []
        
        for i in range(count):
            # Select frequency
            frequency = random.choice(["hourly", "daily", "weekly"])
            
            # Select CRON pattern based on frequency
            cron = random.choice(self.CRON_PATTERNS[frequency])
            
            # Generate query name
            purpose = random.choice(self.QUERY_PURPOSES)
            name = f"scheduled_{purpose.lower().replace(' ', '_')}_{i+1}"
            
            # Generate cost based on frequency
            # Hourly queries tend to process less data
            # Weekly queries might process more accumulated data
            if frequency == "hourly":
                cost_mb = round(random.uniform(10, 500), 2)
            elif frequency == "daily":
                cost_mb = round(random.uniform(100, 2000), 2)
            else:  # weekly
                cost_mb = round(random.uniform(500, 5000), 2)
            
            scheduled_queries.append({
                "name": name,
                "cron": cron,
                "cost_mb": cost_mb,
                "purpose": purpose,
                "frequency": frequency
            })
        
        return scheduled_queries
