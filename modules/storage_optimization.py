"""
Storage Optimization Module for GCP Cost Optimization Dashboard.

This module provides the UI and workflow for simulating and optimizing
GCS storage buckets with AI-powered recommendations.
"""

import streamlit as st
from datetime import datetime
from typing import List, Dict
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from services.ai_optimizer_service import AIOptimizerService
from services.visualization_manager import VisualizationManager
from simulators.storage_simulator import StorageSimulator
from models.data_models import StorageOptimizationResult


def render_storage_optimization_module():
    """
    Renders the storage optimization module UI with simulation workflow
    and results visualization.
    
    Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 6.1, 6.2, 6.3
    """
    st.header("💾 Storage Optimization")
    st.markdown("""
    Simulate GCS bucket scenarios and get AI-powered optimization recommendations
    to reduce storage costs through storage class changes, lifecycle policies, and more.
    """)
    
    # Initialize session state for results
    if 'storage_optimization_results' not in st.session_state:
        st.session_state.storage_optimization_results = None
    if 'storage_bucket_metadata' not in st.session_state:
        st.session_state.storage_bucket_metadata = None
    
    # Configuration options
    st.subheader("Simulation Settings")
    
    col1, col2 = st.columns(2)
    with col1:
        bucket_count = st.slider(
            "Number of buckets to simulate:",
            min_value=5,
            max_value=20,
            value=10,
            help="Number of synthetic GCS buckets to generate and analyze"
        )
    
    with col2:
        st.write("")  # Spacing
    
    # Information about storage classes
    with st.expander("ℹ️ GCS Storage Classes & Pricing"):
        st.markdown("""
        **Storage Class Costs (per GB/month):**
        - **STANDARD**: $0.020 - Frequently accessed data
        - **NEARLINE**: $0.010 - Data accessed less than once per month
        - **COLDLINE**: $0.004 - Data accessed less than once per quarter
        - **ARCHIVE**: $0.0012 - Data accessed less than once per year
        
        **Optimization Opportunities:**
        - Move infrequently accessed data to cheaper storage classes
        - Delete old, unused data
        - Compress uncompressed files
        - Set up lifecycle rules for automatic transitions
        """)
    
    # Simulate button (Requirement 6.3)
    if st.button("🚀 Simulate Storage Optimization", type="primary", use_container_width=True):
        with st.spinner("Starting storage optimization workflow..."):
            _run_storage_optimization_workflow(bucket_count)
    
    # Display results if available (Requirement 3.4, 3.5)
    if st.session_state.storage_optimization_results:
        _display_storage_optimization_results(
            st.session_state.storage_optimization_results,
            st.session_state.storage_bucket_metadata
        )


def _run_storage_optimization_workflow(bucket_count: int):
    """
    Executes the storage optimization workflow:
    1. Generate synthetic bucket metadata
    2. Get AI optimization suggestions
    3. Store results in session state
    
    Requirements: 3.1, 3.2, 3.3
    
    Args:
        bucket_count: Number of buckets to generate
    """
    try:
        # Validate configuration
        config_errors = Config.validate()
        if config_errors:
            st.error("⚠️ Configuration Error - Unable to start optimization")
            for error in config_errors:
                st.error(f"• {error}")
            st.info("💡 Tip: Check your .env file and ensure all required variables (GEMINI_API_KEY or OPENAI_API_KEY) are set correctly.")
            return
        
        # Initialize services
        with st.spinner("🔧 Initializing AI optimizer and storage simulator..."):
            try:
                ai_optimizer = AIOptimizerService(
                    api_key=Config.GEMINI_API_KEY if Config.AI_PROVIDER == "gemini" else Config.OPENAI_API_KEY,
                    provider=Config.AI_PROVIDER
                )
                
                storage_simulator = StorageSimulator()
                st.info("✓ Services initialized successfully")
            except Exception as e:
                st.error(f"❌ Critical Error: Failed to initialize services")
                st.error(f"Details: {str(e)}")
                st.info("💡 Tip: Verify your AI API key is valid and the provider is correctly configured.")
                return
        
        # Step 1: Generate bucket metadata (Requirement 3.1)
        with st.spinner(f"💾 Generating {bucket_count} synthetic storage buckets..."):
            try:
                bucket_metadata = storage_simulator.generate_bucket_metadata(count=bucket_count)
                st.success(f"✓ Generated {len(bucket_metadata)} storage buckets")
                
                # Store bucket metadata in session state
                st.session_state.storage_bucket_metadata = bucket_metadata
            except Exception as e:
                st.error(f"❌ Failed to generate bucket metadata: {str(e)}")
                st.info("💡 Tip: This is usually a temporary issue. Try again or reduce the bucket count.")
                return
        
        # Step 2: Get AI optimization suggestions (Requirement 3.2, 3.3)
        with st.spinner("🤖 Analyzing buckets with AI for optimization opportunities..."):
            try:
                optimization_suggestions = ai_optimizer.analyze_storage(bucket_metadata)
                st.success(f"✓ Generated {len(optimization_suggestions)} optimization suggestions")
            except Exception as e:
                st.error(f"❌ Failed to analyze storage with AI")
                st.error(f"Details: {str(e)}")
                st.info("💡 Tip: This could be due to AI API rate limits or network issues. Wait a moment and try again.")
                return
        
        # Process suggestions into result objects
        results = []
        for suggestion in optimization_suggestions:
            # Find the corresponding bucket metadata
            bucket_name = suggestion['bucket_name']
            bucket_info = next(
                (b for b in bucket_metadata if b['name'] == bucket_name),
                None
            )
            
            if bucket_info:
                # Calculate estimated savings in USD
                size_gb = bucket_info['size_gb']
                current_storage_class = bucket_info['storage_class']
                savings_percent = suggestion['estimated_savings_percent']
                
                # Get current storage cost per GB/month
                storage_costs = {
                    'STANDARD': Config.GCS_STANDARD_COST_PER_GB,
                    'NEARLINE': Config.GCS_NEARLINE_COST_PER_GB,
                    'COLDLINE': Config.GCS_COLDLINE_COST_PER_GB,
                    'ARCHIVE': Config.GCS_ARCHIVE_COST_PER_GB
                }
                
                current_cost_per_gb = storage_costs.get(current_storage_class, Config.GCS_STANDARD_COST_PER_GB)
                current_monthly_cost = size_gb * current_cost_per_gb
                estimated_savings_usd = current_monthly_cost * (savings_percent / 100)
                
                # Determine action type from suggestion text
                suggestion_lower = suggestion['suggestion'].lower()
                if 'delete' in suggestion_lower or 'remove' in suggestion_lower:
                    action_type = 'delete'
                elif 'compress' in suggestion_lower:
                    action_type = 'compress'
                elif 'lifecycle' in suggestion_lower:
                    action_type = 'lifecycle'
                else:
                    action_type = 'move'
                
                result = StorageOptimizationResult(
                    bucket_name=bucket_name,
                    current_size_gb=size_gb,
                    current_storage_class=current_storage_class,
                    last_accessed=bucket_info['last_accessed'],
                    issue=suggestion['issue'],
                    suggestion=suggestion['suggestion'],
                    estimated_savings_percent=savings_percent,
                    estimated_savings_usd=estimated_savings_usd,
                    action_type=action_type
                )
                
                results.append(result)
        
        if not results:
            st.warning("⚠️ No optimization suggestions were generated")
            st.info("💡 The AI may not have found significant optimization opportunities for the simulated buckets. Try generating more buckets or running the simulation again.")
            return
        
        # Step 3: Store results in session state
        st.session_state.storage_optimization_results = results
        
        # Show summary
        total_savings = sum(r.estimated_savings_usd for r in results)
        avg_savings_percent = sum(r.estimated_savings_percent for r in results) / len(results)
        
        st.success(f"""
        ✅ **Analysis Complete!**
        - Buckets Analyzed: {len(bucket_metadata)}
        - Optimization Suggestions: {len(results)}
        - Average Savings: {avg_savings_percent:.1f}%
        - Estimated Monthly Savings: ${total_savings:.2f}
        """)
        
    except Exception as e:
        st.error(f"❌ Critical Error: An unexpected error occurred during storage optimization")
        st.error(f"Details: {str(e)}")
        st.info("💡 Tip: Try refreshing the page and starting over. If the issue persists, check your configuration.")
        # Only show exception in development
        if Config.DEBUG if hasattr(Config, 'DEBUG') else False:
            st.exception(e)


def _display_storage_optimization_results(
    results: List[StorageOptimizationResult],
    bucket_metadata: List[Dict]
):
    """
    Displays storage optimization results with table and charts.
    
    Requirements: 3.4, 3.5
    
    Args:
        results: List of StorageOptimizationResult objects
        bucket_metadata: List of bucket metadata dictionaries
    """
    st.divider()
    st.subheader("📊 Optimization Results")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    total_buckets = len(bucket_metadata)
    total_size = sum(b['size_gb'] for b in bucket_metadata)
    
    # Calculate current monthly cost
    storage_costs = {
        'STANDARD': Config.GCS_STANDARD_COST_PER_GB,
        'NEARLINE': Config.GCS_NEARLINE_COST_PER_GB,
        'COLDLINE': Config.GCS_COLDLINE_COST_PER_GB,
        'ARCHIVE': Config.GCS_ARCHIVE_COST_PER_GB
    }
    total_current_cost = sum(
        b['size_gb'] * storage_costs.get(b['storage_class'], Config.GCS_STANDARD_COST_PER_GB)
        for b in bucket_metadata
    )
    
    total_savings = sum(r.estimated_savings_usd for r in results)
    total_optimized_cost = total_current_cost - total_savings
    avg_savings_percent = sum(r.estimated_savings_percent for r in results) / len(results)
    
    with col1:
        st.metric(
            "Current Daily Cost",
            f"${total_current_cost:.2f}"
        )
    
    with col2:
        st.metric(
            "Avg Savings",
            f"{avg_savings_percent:.1f}%"
        )
    
    with col3:
        st.metric(
            "Optimized Cost",
            f"${total_optimized_cost:.2f}"
        )
    
    with col4:
        st.metric(
            "Current Savings",
            f"${total_savings:.2f}"
        )
    
    # Optimization suggestions table (Requirement 3.4)
    st.subheader("📋 Optimization Suggestions")
    
    table_data = []
    for r in results:
        table_data.append({
            'Bucket Name': r.bucket_name,
            'Issue': r.issue,
            'Suggestion': r.suggestion,
            'Estimated Savings': f"${r.estimated_savings_usd:.2f}/mo ({r.estimated_savings_percent:.1f}%)"
        })
    
    formatted_df = VisualizationManager.format_results_table(
        table_data,
        ['Bucket Name', 'Issue', 'Suggestion', 'Estimated Savings']
    )
    
    st.dataframe(formatted_df, use_container_width=True, height=400)
    
    # Visualizations (Requirement 3.5)
    col1, col2 = st.columns(2)
    
    with col1:
        # Pie chart of bucket size distribution
        st.subheader("💾 Storage Distribution")
        
        distribution_data = [
            {
                'bucket_name': b['name'],
                'current_size_gb': b['size_gb']
            }
            for b in bucket_metadata
        ]
        
        distribution_chart = VisualizationManager.create_storage_distribution_chart(distribution_data)
        st.plotly_chart(distribution_chart, use_container_width=True)
    
    with col2:
        # Bar chart of savings per bucket
        st.subheader("💰 Savings by Bucket")
        
        # Create bar chart using plotly
        import plotly.graph_objects as go
        
        bucket_names = [r.bucket_name for r in results]
        savings_values = [r.estimated_savings_usd for r in results]
        
        fig = go.Figure(data=[
            go.Bar(
                x=bucket_names,
                y=savings_values,
                marker_color='#4ECDC4',
                text=[f'${s:.2f}' for s in savings_values],
                textposition='auto'
            )
        ])
        
        fig.update_layout(
            title='Estimated Monthly Savings per Bucket',
            xaxis_title='Bucket Name',
            yaxis_title='Savings (USD/month)',
            template='plotly_white',
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Detailed bucket information
    st.subheader("🗂️ Bucket Details")
    
    for r in results:
        with st.expander(f"{r.bucket_name} - ${r.estimated_savings_usd:.2f}/mo savings"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Current Configuration:**")
                st.write(f"• Size: {r.current_size_gb:.2f} GB")
                st.write(f"• Storage Class: {r.current_storage_class}")
                st.write(f"• Last Accessed: {r.last_accessed.strftime('%Y-%m-%d')}")
                st.write(f"• Action Type: {r.action_type.title()}")
            
            with col2:
                st.markdown("**Optimization:**")
                st.info(f"**Issue:** {r.issue}")
                st.success(f"**Suggestion:** {r.suggestion}")
                st.metric(
                    "Estimated Savings",
                    f"${r.estimated_savings_usd:.2f}/mo",
                    delta=f"-{r.estimated_savings_percent:.1f}%"
                )
