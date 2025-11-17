"""
Visualization Manager for GCP Cost Optimization Dashboard.

This module provides static methods for creating charts and formatting data
for display in the Streamlit dashboard.
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import List, Dict
from datetime import datetime


class VisualizationManager:
    """
    Manages all visualization and data formatting for the dashboard.
    All methods are static to allow easy usage across modules.
    """
    
    @staticmethod
    def create_sql_comparison_chart(results: List[Dict]) -> go.Figure:
        """
        Creates a bar chart comparing before and after bytes processed for SQL queries.
        
        Args:
            results: List of dictionaries containing query optimization results
                    Expected keys: query_id, bytes_before, bytes_after
        
        Returns:
            Plotly Figure object with grouped bar chart
        """
        if not results:
            # Return empty figure with message
            fig = go.Figure()
            fig.add_annotation(
                text="No data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16)
            )
            return fig
        
        query_ids = [r.get('query_id', f"Query {i+1}") for i, r in enumerate(results)]
        bytes_before = [r.get('bytes_before', 0) / (1024**3) for r in results]  # Convert to GB
        bytes_after = [r.get('bytes_after', 0) / (1024**3) for r in results]  # Convert to GB
        
        fig = go.Figure(data=[
            go.Bar(
                name='Before Optimization',
                x=query_ids,
                y=bytes_before,
                marker_color='#FF6B6B',
                text=[f'{b:.2f} GB' for b in bytes_before],
                textposition='auto'
            ),
            go.Bar(
                name='After Optimization',
                x=query_ids,
                y=bytes_after,
                marker_color='#4ECDC4',
                text=[f'{a:.2f} GB' for a in bytes_after],
                textposition='auto'
            )
        ])
        
        fig.update_layout(
            title='SQL Query Optimization: Bytes Processed Comparison',
            xaxis_title='Query',
            yaxis_title='Bytes Processed (GB)',
            barmode='group',
            hovermode='x unified',
            template='plotly_white',
            height=500,
            xaxis={'categoryorder': 'array', 'categoryarray': query_ids}  # Maintain original order
        )
        
        return fig
    
    @staticmethod
    def create_savings_pie_chart(results: List[Dict]) -> go.Figure:
        """
        Creates a pie chart showing total savings distribution across queries.
        
        Args:
            results: List of dictionaries containing query optimization results
                    Expected keys: query_id, cost_before_usd, cost_after_usd
        
        Returns:
            Plotly Figure object with pie chart
        """
        if not results:
            fig = go.Figure()
            fig.add_annotation(
                text="No data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16)
            )
            return fig
        
        query_ids = [r.get('query_id', f"Query {i+1}") for i, r in enumerate(results)]
        savings = [
            r.get('cost_before_usd', 0) - r.get('cost_after_usd', 0) 
            for r in results
        ]
        
        # Filter out queries with no savings
        data = [(qid, sav) for qid, sav in zip(query_ids, savings) if sav > 0]
        
        if not data:
            fig = go.Figure()
            fig.add_annotation(
                text="No savings detected",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16)
            )
            return fig
        
        query_ids, savings = zip(*data)
        
        fig = go.Figure(data=[go.Pie(
            labels=query_ids,
            values=savings,
            hole=0.3,
            marker=dict(colors=px.colors.qualitative.Set3),
            textinfo='label+percent',
            hovertemplate='<b>%{label}</b><br>Savings: $%{value:.4f}<br>Percentage: %{percent}<extra></extra>'
        )])
        
        total_savings = sum(savings)
        fig.update_layout(
            title=f'Cost Savings Distribution (Total: ${total_savings:.4f})',
            template='plotly_white',
            height=500
        )
        
        return fig
    
    @staticmethod
    def create_storage_distribution_chart(buckets: List[Dict]) -> go.Figure:
        """
        Creates a pie chart showing bucket size distribution.
        
        Args:
            buckets: List of dictionaries containing bucket metadata
                    Expected keys: bucket_name, current_size_gb
        
        Returns:
            Plotly Figure object with pie chart
        """
        if not buckets:
            fig = go.Figure()
            fig.add_annotation(
                text="No data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16)
            )
            return fig
        
        bucket_names = [b.get('bucket_name', f"Bucket {i+1}") for i, b in enumerate(buckets)]
        sizes = [b.get('current_size_gb', 0) for b in buckets]
        
        fig = go.Figure(data=[go.Pie(
            labels=bucket_names,
            values=sizes,
            marker=dict(colors=px.colors.qualitative.Pastel),
            textinfo='label+percent',
            hovertemplate='<b>%{label}</b><br>Size: %{value:.2f} GB<br>Percentage: %{percent}<extra></extra>'
        )])
        
        total_size = sum(sizes)
        fig.update_layout(
            title=f'Storage Distribution by Bucket (Total: {total_size:.2f} GB)',
            template='plotly_white',
            height=500
        )
        
        return fig
    
    @staticmethod
    def create_schedule_timeline(schedules: List[Dict]) -> go.Figure:
        """
        Creates a heatmap showing cost distribution by time for scheduled queries.
        
        Args:
            schedules: List of dictionaries containing schedule metadata
                      Expected keys: query_name, current_cron, current_daily_cost
        
        Returns:
            Plotly Figure object with heatmap
        """
        if not schedules:
            fig = go.Figure()
            fig.add_annotation(
                text="No data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16)
            )
            return fig
        
        # Parse CRON expressions to estimate hourly costs
        # Simplified approach: distribute daily cost across hours based on frequency
        hours = list(range(24))
        query_names = [s.get('query_name', f"Query {i+1}") for i, s in enumerate(schedules)]
        
        # Create cost matrix (queries x hours)
        cost_matrix = []
        for schedule in schedules:
            daily_cost = schedule.get('current_daily_cost', 0)
            cron = schedule.get('current_cron', '0 0 * * *')
            
            # Simple heuristic: parse CRON to estimate execution hours
            hourly_costs = [0] * 24
            
            # Parse basic CRON patterns
            parts = cron.split()
            if len(parts) >= 2:
                minute, hour = parts[0], parts[1]
                
                if hour == '*':
                    # Runs every hour
                    cost_per_run = daily_cost / 24
                    hourly_costs = [cost_per_run] * 24
                elif '/' in hour:
                    # Runs every N hours
                    interval = int(hour.split('/')[1])
                    runs_per_day = 24 // interval
                    cost_per_run = daily_cost / runs_per_day if runs_per_day > 0 else 0
                    for h in range(0, 24, interval):
                        hourly_costs[h] = cost_per_run
                elif ',' in hour:
                    # Runs at specific hours
                    hours_list = [int(h) for h in hour.split(',')]
                    cost_per_run = daily_cost / len(hours_list) if hours_list else 0
                    for h in hours_list:
                        if 0 <= h < 24:
                            hourly_costs[h] = cost_per_run
                else:
                    # Runs at specific hour
                    try:
                        h = int(hour)
                        if 0 <= h < 24:
                            hourly_costs[h] = daily_cost
                    except ValueError:
                        # Default to spreading across day
                        hourly_costs = [daily_cost / 24] * 24
            else:
                # Default to spreading across day
                hourly_costs = [daily_cost / 24] * 24
            
            cost_matrix.append(hourly_costs)
        
        fig = go.Figure(data=go.Heatmap(
            z=cost_matrix,
            x=[f'{h:02d}:00' for h in hours],
            y=query_names,
            colorscale='YlOrRd',
            hovertemplate='Query: %{y}<br>Time: %{x}<br>Cost: $%{z:.4f}<extra></extra>',
            colorbar=dict(title='Cost (USD)')
        ))
        
        fig.update_layout(
            title='Scheduled Query Cost Heatmap by Hour',
            xaxis_title='Hour of Day',
            yaxis_title='Query Name',
            template='plotly_white',
            height=max(400, len(query_names) * 40)
        )
        
        return fig
    
    @staticmethod
    def create_ml_cost_breakdown(jobs: List[Dict]) -> go.Figure:
        """
        Creates a donut chart showing ML job cost breakdown.
        
        Args:
            jobs: List of dictionaries containing ML job metadata
                 Expected keys: job_name, current_cost
        
        Returns:
            Plotly Figure object with donut chart
        """
        if not jobs:
            fig = go.Figure()
            fig.add_annotation(
                text="No data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16)
            )
            return fig
        
        job_names = [j.get('job_name', f"Job {i+1}") for i, j in enumerate(jobs)]
        costs = [j.get('current_cost', 0) for j in jobs]
        
        fig = go.Figure(data=[go.Pie(
            labels=job_names,
            values=costs,
            hole=0.4,
            marker=dict(colors=px.colors.qualitative.Bold),
            textinfo='label+percent',
            hovertemplate='<b>%{label}</b><br>Cost: $%{value:.2f}<br>Percentage: %{percent}<extra></extra>'
        )])
        
        total_cost = sum(costs)
        fig.update_layout(
            title=f'ML Training Job Cost Breakdown (Total: ${total_cost:.2f})',
            template='plotly_white',
            height=500,
            annotations=[dict(
                text=f'${total_cost:.2f}',
                x=0.5, y=0.5,
                font_size=20,
                showarrow=False
            )]
        )
        
        return fig
    
    @staticmethod
    def format_results_table(data: List[Dict], columns: List[str]) -> pd.DataFrame:
        """
        Formats data as a pandas DataFrame for Streamlit display.
        
        Args:
            data: List of dictionaries containing result data
            columns: List of column names to include in the DataFrame
        
        Returns:
            Pandas DataFrame formatted for display
        """
        if not data:
            return pd.DataFrame()
        
        # Extract specified columns from data
        formatted_data = []
        for item in data:
            row = {}
            for col in columns:
                value = item.get(col, '')
                
                # Format specific data types
                if isinstance(value, float):
                    # Format floats to 2 decimal places for costs, 4 for percentages
                    if 'percent' in col.lower() or 'savings' in col.lower():
                        row[col] = f'{value:.2f}%' if 'percent' in col.lower() else f'{value:.4f}'
                    elif 'cost' in col.lower() or 'usd' in col.lower():
                        row[col] = f'${value:.4f}'
                    elif 'gb' in col.lower() or 'size' in col.lower():
                        row[col] = f'{value:.2f} GB'
                    else:
                        row[col] = f'{value:.2f}'
                elif isinstance(value, int):
                    # Format large integers with commas
                    if 'bytes' in col.lower():
                        # Convert bytes to GB for readability
                        row[col] = f'{value / (1024**3):.2f} GB'
                    else:
                        row[col] = f'{value:,}'
                elif isinstance(value, datetime):
                    row[col] = value.strftime('%Y-%m-%d %H:%M:%S')
                elif isinstance(value, list):
                    row[col] = ', '.join(str(v) for v in value)
                else:
                    row[col] = str(value)
            
            formatted_data.append(row)
        
        df = pd.DataFrame(formatted_data)
        
        # Reorder columns to match the specified order
        df = df[columns] if all(col in df.columns for col in columns) else df
        
        return df
