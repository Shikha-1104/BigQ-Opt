"""
SQL Optimization Module for GCP Cost Optimization Dashboard.

This module provides the UI and workflow for simulating and optimizing
SQL queries using BigQuery public datasets.
"""

import streamlit as st
from datetime import datetime
from typing import List, Dict, Tuple
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from services.bigquery_service import BigQueryService
from services.ai_optimizer_service import AIOptimizerService
from services.visualization_manager import VisualizationManager
from simulators.sql_query_simulator import SQLQuerySimulator
from models.data_models import SQLOptimizationResult


def _process_query_pair_parallel(
    query_id: str,
    original_query: str,
    optimized_query: str,
    bigquery_service: BigQueryService
) -> Tuple[bool, Dict]:
    """
    Process a single query pair (original and optimized) with dry-runs.
    Used for parallel processing.
    
    Args:
        query_id: Identifier for the query
        original_query: Original unoptimized query
        optimized_query: AI-optimized query
        bigquery_service: BigQuery service instance
        
    Returns:
        Tuple of (success: bool, result: Dict)
    """
    try:
        # Dry-run original query
        before_result = bigquery_service.dry_run_query(original_query)
        
        if not before_result['success']:
            error_msg = before_result.get('error', 'Unknown error')
            # Check if it's an authentication error
            if '401' in error_msg or 'UNAUTHENTICATED' in error_msg or 'authentication' in error_msg.lower():
                return False, {
                    'query_id': query_id,
                    'error': f"Authentication error - check credentials"
                }
            return False, {
                'query_id': query_id,
                'error': f"Original query failed: {error_msg[:150]}"
            }
        
        # Dry-run optimized query
        after_result = bigquery_service.dry_run_query(optimized_query)
        
        if not after_result['success']:
            error_msg = after_result.get('error', 'Unknown error')
            # Check if it's an authentication error
            if '401' in error_msg or 'UNAUTHENTICATED' in error_msg or 'authentication' in error_msg.lower():
                return False, {
                    'query_id': query_id,
                    'error': f"Authentication error - check credentials"
                }
            return False, {
                'query_id': query_id,
                'error': f"Optimized query failed: {error_msg[:150]}"
            }
        
        return True, {
            'query_id': query_id,
            'before_result': before_result,
            'after_result': after_result
        }
    except Exception as e:
        error_str = str(e)
        # Check if it's an authentication error
        if '401' in error_str or 'UNAUTHENTICATED' in error_str or 'authentication' in error_str.lower():
            return False, {
                'query_id': query_id,
                'error': f"Authentication error - check credentials"
            }
        return False, {
            'query_id': query_id,
            'error': error_str[:150]
        }


def render_sql_optimization_module():
    """
    Renders the SQL optimization module UI with dataset selection,
    simulation workflow, and results visualization.
    
    Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 6.1, 6.2, 6.3
    """
    st.header("🔍 SQL Query Optimization")
    st.markdown("""
    Simulate unoptimized SQL queries on BigQuery public datasets and get AI-powered 
    optimization suggestions with cost comparisons.
    """)
    
    # Initialize session state for results
    if 'sql_optimization_results' not in st.session_state:
        st.session_state.sql_optimization_results = None
    
    # Dataset selection dropdown (Requirement 1.1, 6.1, 6.2)
    st.subheader("Select Dataset")
    
    dataset_options = {
        f"{ds['name']}": ds 
        for ds in Config.PUBLIC_DATASETS
    }
    
    selected_dataset_name = st.selectbox(
        "Choose a BigQuery public dataset:",
        options=list(dataset_options.keys()),
        help="Select a public dataset to simulate SQL optimization"
    )
    
    selected_dataset = dataset_options[selected_dataset_name]
    
    # Display dataset information
    with st.expander("ℹ️ Dataset Information"):
        st.write(f"**Dataset:** `{selected_dataset['dataset']}`")
        st.write(f"**Table:** `{selected_dataset['table']}`")
        st.write(f"**Description:** {selected_dataset['description']}")
    
    # Configuration options
    col1, col2 = st.columns(2)
    with col1:
        query_count = st.slider(
            "Number of queries to generate:",
            min_value=3,
            max_value=10,
            value=5,
            help="Number of unoptimized queries to generate and optimize"
        )
    
    with col2:
        st.write("")  # Spacing
    
    # Simulate button (Requirement 6.3)
    if st.button("🚀 Simulate SQL Optimization", type="primary", use_container_width=True):
        with st.spinner("Starting SQL optimization workflow..."):
            _run_sql_optimization_workflow(
                selected_dataset,
                query_count
            )
    
    # Display results if available (Requirement 1.5, 2.1, 2.2, 2.3)
    if st.session_state.sql_optimization_results:
        _display_sql_optimization_results(st.session_state.sql_optimization_results)


def _run_sql_optimization_workflow(dataset_info: Dict, query_count: int):
    """
    Executes the SQL optimization workflow:
    1. Generate unoptimized queries
    2. Get AI optimizations
    3. Run BigQuery dry-runs for before/after
    4. Calculate savings
    5. Store results in session state
    
    Requirements: 1.2, 1.3, 1.4
    
    Args:
        dataset_info: Dictionary with dataset, table, and description
        query_count: Number of queries to generate
    """
    try:
        # Validate configuration
        config_errors = Config.validate()
        if config_errors:
            st.error("⚠️ Configuration Error - Unable to start optimization")
            for error in config_errors:
                st.error(f"• {error}")
            st.info("💡 Tip: Check your .env file and ensure all required variables (GCP_PROJECT_ID, GEMINI_API_KEY) are set correctly.")
            return
        
        # Initialize services
        with st.spinner("🔧 Initializing BigQuery and AI services..."):
            try:
                bigquery_service = BigQueryService(
                    project_id=Config.BIGQUERY_PROJECT_ID,
                    credentials_path=Config.BIGQUERY_CREDENTIALS
                )
                
                ai_optimizer = AIOptimizerService(
                    api_key=Config.GEMINI_API_KEY if Config.AI_PROVIDER == "gemini" else Config.OPENAI_API_KEY,
                    provider=Config.AI_PROVIDER
                )
                
                sql_simulator = SQLQuerySimulator()
                st.info("✓ Services initialized successfully")
            except Exception as e:
                st.error(f"❌ Critical Error: Failed to initialize services")
                st.error(f"Details: {str(e)}")
                st.info("💡 Tip: Verify your API keys and GCP credentials are valid.")
                return
        
        # Step 1: Generate unoptimized queries (Requirement 1.2)
        with st.spinner(f"📝 Generating {query_count} unoptimized queries..."):
            try:
                unoptimized_queries = sql_simulator.generate_unoptimized_queries(
                    dataset=dataset_info['dataset'],
                    table=dataset_info['table'],
                    count=query_count
                )
                st.success(f"✓ Generated {len(unoptimized_queries)} unoptimized queries")
            except Exception as e:
                st.error(f"❌ Failed to generate queries: {str(e)}")
                st.info("💡 Tip: This is usually a temporary issue. Try again or reduce the query count.")
                return
        
        # Step 2: Get AI optimizations for all queries (Requirement 1.3)
        status_text = st.empty()
        status_text.info("🤖 Getting AI optimizations for all queries...")
        
        optimized_queries = []
        for idx, original_query in enumerate(unoptimized_queries):
            try:
                optimization_result = ai_optimizer.optimize_sql_query(
                    query=original_query,
                    dataset_info={
                        'dataset': dataset_info['dataset'],
                        'table': dataset_info['table']
                    }
                )
                optimized_queries.append({
                    'query_id': f"Query {idx + 1}",
                    'original_query': original_query,
                    'optimized_query': optimization_result['optimized_query'],
                    'optimizations_applied': optimization_result['optimizations_applied']
                })
            except Exception as e:
                st.warning(f"⚠️ Failed to optimize Query {idx + 1}: {str(e)[:100]}")
                continue
        
        if not optimized_queries:
            st.error("❌ No queries were successfully optimized by AI")
            status_text.empty()
            return
        
        st.success(f"✓ AI optimized {len(optimized_queries)} queries")
        
        # Step 3: Run BigQuery dry-runs in parallel (Requirement 1.4)
        status_text.info(f"⚡ Running parallel dry-runs for {len(optimized_queries)} query pairs...")
        
        results = []
        progress_bar = st.progress(0, text=f"Processing dry-runs: 0/{len(optimized_queries)}")
        
        # Use ThreadPoolExecutor for parallel dry-run execution (max 5 workers to avoid rate limits)
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Submit all dry-run tasks
            future_to_query = {
                executor.submit(
                    _process_query_pair_parallel,
                    q['query_id'],
                    q['original_query'],
                    q['optimized_query'],
                    bigquery_service
                ): q for q in optimized_queries
            }
            
            # Process completed tasks as they finish
            completed = 0
            for future in as_completed(future_to_query):
                query_data = future_to_query[future]
                completed += 1
                
                try:
                    success, result_data = future.result()
                    
                    if success:
                        # Step 4: Calculate savings percentage
                        before_result = result_data['before_result']
                        after_result = result_data['after_result']
                        
                        bytes_before = before_result['total_bytes_processed']
                        bytes_after = after_result['total_bytes_processed']
                        cost_before = before_result['estimated_cost_usd']
                        cost_after = after_result['estimated_cost_usd']
                        
                        if bytes_before > 0:
                            savings_percent = ((bytes_before - bytes_after) / bytes_before) * 100
                        else:
                            savings_percent = 0.0
                        
                        # Create result object
                        result = SQLOptimizationResult(
                            query_id=query_data['query_id'],
                            original_query=query_data['original_query'],
                            optimized_query=query_data['optimized_query'],
                            bytes_before=bytes_before,
                            bytes_after=bytes_after,
                            cost_before_usd=cost_before,
                            cost_after_usd=cost_after,
                            savings_percent=savings_percent,
                            optimizations_applied=query_data['optimizations_applied'],
                            timestamp=datetime.now()
                        )
                        
                        results.append(result)
                        st.success(f"✓ {query_data['query_id']} optimized: {savings_percent:.1f}% savings")
                    else:
                        st.warning(f"⚠️ {result_data['query_id']}: {result_data['error']}")
                        st.info(f"💡 Continuing with remaining queries")
                
                except Exception as e:
                    st.warning(f"⚠️ Error processing {query_data['query_id']}: {str(e)[:100]}")
                    st.info(f"💡 Continuing with remaining queries...")
                
                # Update progress
                progress_bar.progress(completed / len(optimized_queries), 
                                    text=f"Processing dry-runs: {completed}/{len(optimized_queries)}")
        
        status_text.empty()
        progress_bar.empty()
        
        if not results:
            st.error("❌ No queries were successfully optimized")
            st.info("💡 Possible causes:")
            st.info("• Invalid SQL syntax in generated queries")
            st.info("• BigQuery API authentication issues")
            st.info("• AI API rate limits or errors")
            st.info("Try reducing the query count or check your API credentials.")
            return
        
        # Step 5: Store results in session state
        st.session_state.sql_optimization_results = results
        
        # Show summary
        total_savings = sum(r.cost_before_usd - r.cost_after_usd for r in results)
        avg_savings_percent = sum(r.savings_percent for r in results) / len(results)
        
        st.success(f"""
        ✅ **Optimization Complete!**
        - Processed: {len(results)} queries
        - Average Savings: {avg_savings_percent:.1f}%
        - Total Cost Savings: ${total_savings:.4f}
        """)
        
    except Exception as e:
        st.error(f"❌ Critical Error: An unexpected error occurred during optimization")
        st.error(f"Details: {str(e)}")
        st.info("💡 Tip: Try refreshing the page and starting over. If the issue persists, check your configuration.")
        # Only show exception in development
        if Config.DEBUG if hasattr(Config, 'DEBUG') else False:
            st.exception(e)


def _display_sql_optimization_results(results: List[SQLOptimizationResult]):
    """
    Displays SQL optimization results with comparison table and charts.
    
    Requirements: 1.5, 2.1, 2.2, 2.3
    
    Args:
        results: List of SQLOptimizationResult objects
    """
    st.divider()
    st.subheader("📊 Optimization Results")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    total_bytes_before = sum(r.bytes_before for r in results)
    total_bytes_after = sum(r.bytes_after for r in results)
    total_cost_before = sum(r.cost_before_usd for r in results)
    total_cost_after = sum(r.cost_after_usd for r in results)
    total_savings = total_cost_before - total_cost_after
    avg_savings_percent = sum(r.savings_percent for r in results) / len(results)
    
    with col1:
        st.metric(
            "Current Daily Cost",
            f"${total_cost_before:.4f}"
        )
    
    with col2:
        st.metric(
            "Avg Savings",
            f"{avg_savings_percent:.1f}%"
        )
    
    with col3:
        st.metric(
            "Optimized Cost",
            f"${total_cost_after:.4f}"
        )
    
    with col4:
        st.metric(
            "Current Savings",
            f"${total_savings:.4f}",
            delta=f"-{(total_savings/total_cost_before*100):.1f}%" if total_cost_before > 0 else "0%"
        )
    
    # Comparison table (Requirement 1.5)
    st.subheader("📋 Query Comparison Table")
    
    table_data = []
    for r in results:
        table_data.append({
            'Query ID': r.query_id,
            'Bytes Before': r.bytes_before,
            'Bytes After': r.bytes_after,
            'Cost Before': r.cost_before_usd,
            'Cost After': r.cost_after_usd,
            'Savings %': r.savings_percent
        })
    
    formatted_df = VisualizationManager.format_results_table(
        table_data,
        ['Query ID', 'Bytes Before', 'Bytes After', 'Cost Before', 'Cost After', 'Savings %']
    )
    
    st.dataframe(formatted_df, use_container_width=True)
    
    # Bar chart comparing before/after bytes (Requirement 2.1)
    st.subheader("📊 Bytes Processed Comparison")
    
    chart_data = [
        {
            'query_id': r.query_id,
            'bytes_before': r.bytes_before,
            'bytes_after': r.bytes_after
        }
        for r in results
    ]
    
    comparison_chart = VisualizationManager.create_sql_comparison_chart(chart_data)
    st.plotly_chart(comparison_chart, use_container_width=True)
    
    # Pie chart showing total savings (Requirement 2.2)
    st.subheader("💰 Cost Savings Distribution")
    
    savings_data = [
        {
            'query_id': r.query_id,
            'cost_before_usd': r.cost_before_usd,
            'cost_after_usd': r.cost_after_usd
        }
        for r in results
    ]
    
    savings_chart = VisualizationManager.create_savings_pie_chart(savings_data)
    st.plotly_chart(savings_chart, use_container_width=True)
    
    # Display before and after SQL text for each query (Requirement 2.3)
    st.subheader("📝 Query Details")
    
    for r in results:
        with st.expander(f"{r.query_id} - {r.savings_percent:.1f}% savings"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Original Query:**")
                st.code(r.original_query, language="sql")
                st.caption(f"Bytes: {r.bytes_before:,} | Cost: ${r.cost_before_usd:.4f}")
            
            with col2:
                st.markdown("**Optimized Query:**")
                st.code(r.optimized_query, language="sql")
                st.caption(f"Bytes: {r.bytes_after:,} | Cost: ${r.cost_after_usd:.4f}")
            
            st.markdown("**Optimizations Applied:**")
            for opt in r.optimizations_applied:
                st.markdown(f"• {opt}")
