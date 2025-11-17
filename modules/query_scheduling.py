"""
Query Scheduling Optimization Module for GCP Cost Optimization Dashboard.

This module provides the UI and workflow for simulating and optimizing
BigQuery scheduled queries with AI-powered recommendations.
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
from simulators.schedule_simulator import ScheduleSimulator
from models.data_models import ScheduleOptimizationResult


def render_query_scheduling_module():
    """
    Renders the query scheduling optimization module UI with simulation workflow
    and results visualization.
    
    Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 6.1, 6.2, 6.3
    """
    st.header("📅 Query Scheduling Optimization")
    st.markdown("""
    Simulate BigQuery scheduled query patterns and get AI-powered optimization recommendations
    to reduce redundant executions, adjust frequencies, and identify merge opportunities.
    """)
    
    # Initialize session state for results
    if 'schedule_optimization_results' not in st.session_state:
        st.session_state.schedule_optimization_results = None
    if 'schedule_metadata' not in st.session_state:
        st.session_state.schedule_metadata = None
    if 'schedule_ai_analysis' not in st.session_state:
        st.session_state.schedule_ai_analysis = None
    
    # Configuration options
    st.subheader("Simulation Settings")
    
    col1, col2 = st.columns(2)
    with col1:
        schedule_count = st.slider(
            "Number of scheduled queries to simulate:",
            min_value=5,
            max_value=20,
            value=10,
            help="Number of synthetic scheduled queries to generate and analyze"
        )
    
    with col2:
        st.write("")  # Spacing
    
    # Information about scheduling optimization
    with st.expander("ℹ️ Scheduling Optimization Strategies"):
        st.markdown("""
        **Common Optimization Opportunities:**
        - **Redundant Queries**: Identify queries producing duplicate or overlapping results
        - **Over-Frequent Execution**: Reduce frequency for queries that don't need real-time updates
        - **Merge Opportunities**: Combine multiple queries into a single efficient query
        - **Materialized Views**: Convert frequently-run queries to materialized views
        
        **Cost Impact:**
        - Reducing hourly queries to daily can save up to 95% in query costs
        - Merging 3 queries into 1 can reduce costs by 66%
        - Materialized views eliminate repeated computation costs
        """)
    
    # Simulate button (Requirement 6.3)
    if st.button("🚀 Simulate Schedule Optimization", type="primary", use_container_width=True):
        with st.spinner("Starting schedule optimization workflow..."):
            _run_schedule_optimization_workflow(schedule_count)
    
    # Display results if available (Requirement 4.4, 4.5)
    if st.session_state.schedule_optimization_results:
        _display_schedule_optimization_results(
            st.session_state.schedule_optimization_results,
            st.session_state.schedule_metadata,
            st.session_state.schedule_ai_analysis
        )


def _run_schedule_optimization_workflow(schedule_count: int):
    """
    Executes the schedule optimization workflow:
    1. Generate synthetic scheduled query metadata
    2. Get AI optimization recommendations
    3. Store results in session state
    
    Requirements: 4.1, 4.2, 4.3
    
    Args:
        schedule_count: Number of scheduled queries to generate
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
        with st.spinner("🔧 Initializing AI optimizer and schedule simulator..."):
            try:
                ai_optimizer = AIOptimizerService(
                    api_key=Config.GEMINI_API_KEY if Config.AI_PROVIDER == "gemini" else Config.OPENAI_API_KEY,
                    provider=Config.AI_PROVIDER
                )
                
                schedule_simulator = ScheduleSimulator()
                st.info("✓ Services initialized successfully")
            except Exception as e:
                st.error(f"❌ Critical Error: Failed to initialize services")
                st.error(f"Details: {str(e)}")
                st.info("💡 Tip: Verify your AI API key is valid and the provider is correctly configured.")
                return
        
        # Step 1: Generate scheduled query metadata (Requirement 4.1)
        with st.spinner(f"📅 Generating {schedule_count} synthetic scheduled queries..."):
            try:
                schedule_metadata = schedule_simulator.generate_scheduled_queries(count=schedule_count)
                st.success(f"✓ Generated {len(schedule_metadata)} scheduled queries")
                
                # Store schedule metadata in session state
                st.session_state.schedule_metadata = schedule_metadata
            except Exception as e:
                st.error(f"❌ Failed to generate schedule metadata: {str(e)}")
                st.info("💡 Tip: This is usually a temporary issue. Try again or reduce the schedule count.")
                return
        
        # Step 2: Get AI optimization recommendations (Requirement 4.2, 4.3)
        with st.spinner("🤖 Analyzing schedules with AI for optimization opportunities..."):
            try:
                ai_analysis = ai_optimizer.optimize_schedule(schedule_metadata)
                st.success(f"✓ Generated optimization recommendations")
                
                # Store AI analysis in session state
                st.session_state.schedule_ai_analysis = ai_analysis
            except Exception as e:
                st.error(f"❌ Failed to analyze schedules with AI")
                st.error(f"Details: {str(e)}")
                st.info("💡 Tip: This could be due to AI API rate limits or network issues. Wait a moment and try again.")
                return
        
        # Process AI analysis into result objects
        results = []
        
        # Process frequency adjustments
        for adjustment in ai_analysis.get('frequency_adjustments', []):
            query_name = adjustment['query_name']
            
            # Find the corresponding schedule metadata
            schedule_info = next(
                (s for s in schedule_metadata if s['name'] == query_name),
                None
            )
            
            if schedule_info:
                # Calculate current daily cost
                cost_mb = schedule_info['cost_mb']
                frequency = schedule_info['frequency']
                
                # Estimate runs per day based on frequency
                runs_per_day = {
                    'hourly': 24,
                    'daily': 1,
                    'weekly': 1/7
                }.get(frequency, 1)
                
                current_daily_cost = (cost_mb / 1024) * Config.BIGQUERY_COST_PER_TB * runs_per_day
                
                # Estimate suggested runs per day
                suggested_frequency = adjustment['suggested_frequency']
                suggested_runs_per_day = {
                    'hourly': 24,
                    'daily': 1,
                    'weekly': 1/7,
                    'twice_daily': 2,
                    'every_6_hours': 4
                }.get(suggested_frequency, 1)
                
                suggested_daily_cost = (cost_mb / 1024) * Config.BIGQUERY_COST_PER_TB * suggested_runs_per_day
                
                # Calculate savings
                savings_percent = ((current_daily_cost - suggested_daily_cost) / current_daily_cost * 100) if current_daily_cost > 0 else 0
                
                # Generate suggested CRON
                suggested_cron_map = {
                    'hourly': '0 * * * *',
                    'daily': '0 0 * * *',
                    'weekly': '0 0 * * 0',
                    'twice_daily': '0 0,12 * * *',
                    'every_6_hours': '0 */6 * * *'
                }
                suggested_cron = suggested_cron_map.get(suggested_frequency, '0 0 * * *')
                
                result = ScheduleOptimizationResult(
                    query_name=query_name,
                    current_cron=schedule_info['cron'],
                    suggested_cron=suggested_cron,
                    current_daily_cost=current_daily_cost,
                    suggested_daily_cost=suggested_daily_cost,
                    optimization_type='reduce_frequency',
                    reasoning=adjustment['reasoning'],
                    estimated_savings_percent=savings_percent
                )
                
                results.append(result)
        
        # Process merge opportunities
        for merge in ai_analysis.get('merge_opportunities', []):
            queries = merge.get('queries', [])
            if len(queries) >= 2:
                # Use first query as representative
                query_name = f"Merge: {', '.join(queries[:2])}"
                
                # Calculate combined cost
                combined_cost = 0
                for q_name in queries:
                    schedule_info = next(
                        (s for s in schedule_metadata if s['name'] == q_name),
                        None
                    )
                    if schedule_info:
                        cost_mb = schedule_info['cost_mb']
                        frequency = schedule_info['frequency']
                        runs_per_day = {
                            'hourly': 24,
                            'daily': 1,
                            'weekly': 1/7
                        }.get(frequency, 1)
                        combined_cost += (cost_mb / 1024) * Config.BIGQUERY_COST_PER_TB * runs_per_day
                
                # Assume merged query costs 60% of combined (some overlap)
                suggested_cost = combined_cost * 0.6
                savings_percent = ((combined_cost - suggested_cost) / combined_cost * 100) if combined_cost > 0 else 0
                
                result = ScheduleOptimizationResult(
                    query_name=query_name,
                    current_cron="Multiple schedules",
                    suggested_cron="Merged schedule",
                    current_daily_cost=combined_cost,
                    suggested_daily_cost=suggested_cost,
                    optimization_type='merge',
                    reasoning=merge['reasoning'],
                    estimated_savings_percent=savings_percent
                )
                
                results.append(result)
        
        # Process materialized view candidates
        for mv_candidate in ai_analysis.get('materialized_view_candidates', []):
            schedule_info = next(
                (s for s in schedule_metadata if s['name'] == mv_candidate),
                None
            )
            
            if schedule_info:
                cost_mb = schedule_info['cost_mb']
                frequency = schedule_info['frequency']
                runs_per_day = {
                    'hourly': 24,
                    'daily': 1,
                    'weekly': 1/7
                }.get(frequency, 1)
                
                current_daily_cost = (cost_mb / 1024) * Config.BIGQUERY_COST_PER_TB * runs_per_day
                
                # Materialized views have refresh cost but eliminate query cost
                # Assume 80% savings
                suggested_daily_cost = current_daily_cost * 0.2
                savings_percent = 80.0
                
                result = ScheduleOptimizationResult(
                    query_name=mv_candidate,
                    current_cron=schedule_info['cron'],
                    suggested_cron="Materialized View (auto-refresh)",
                    current_daily_cost=current_daily_cost,
                    suggested_daily_cost=suggested_daily_cost,
                    optimization_type='materialized_view',
                    reasoning="Convert to materialized view to eliminate repeated computation",
                    estimated_savings_percent=savings_percent
                )
                
                results.append(result)
        
        if not results:
            st.warning("⚠️ No optimization recommendations were generated")
            st.info("💡 The AI may not have found significant optimization opportunities for the simulated schedules. Try generating more schedules or running the simulation again.")
            return
        
        # Step 3: Store results in session state
        st.session_state.schedule_optimization_results = results
        
        # Show summary
        total_current_cost = sum(r.current_daily_cost for r in results)
        total_suggested_cost = sum(r.suggested_daily_cost for r in results)
        total_savings = total_current_cost - total_suggested_cost
        avg_savings_percent = sum(r.estimated_savings_percent for r in results) / len(results)
        
        st.success(f"""
        ✅ **Analysis Complete!**
        - Scheduled Queries Analyzed: {len(schedule_metadata)}
        - Optimization Recommendations: {len(results)}
        - Average Savings: {avg_savings_percent:.1f}%
        - Estimated Daily Savings: ${total_savings:.4f}
        - Estimated Monthly Savings: ${total_savings * 30:.2f}
        """)
        
    except Exception as e:
        st.error(f"❌ Critical Error: An unexpected error occurred during schedule optimization")
        st.error(f"Details: {str(e)}")
        st.info("💡 Tip: Try refreshing the page and starting over. If the issue persists, check your configuration.")
        # Only show exception in development
        if Config.DEBUG if hasattr(Config, 'DEBUG') else False:
            st.exception(e)


def _display_schedule_optimization_results(
    results: List[ScheduleOptimizationResult],
    schedule_metadata: List[Dict],
    ai_analysis: Dict
):
    """
    Displays schedule optimization results with timeline/heatmap and comparison table.
    
    Requirements: 4.4, 4.5
    
    Args:
        results: List of ScheduleOptimizationResult objects
        schedule_metadata: List of schedule metadata dictionaries
        ai_analysis: AI analysis results dictionary
    """
    st.divider()
    st.subheader("📊 Optimization Results")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    total_schedules = len(schedule_metadata)
    total_current_cost = sum(r.current_daily_cost for r in results)
    total_suggested_cost = sum(r.suggested_daily_cost for r in results)
    total_savings = total_current_cost - total_suggested_cost
    avg_savings_percent = sum(r.estimated_savings_percent for r in results) / len(results)
    
    with col1:
        st.metric(
            "Current Daily Cost",
            f"${total_current_cost:.4f}"
        )
    
    with col2:
        st.metric(
            "Avg Savings",
            f"{avg_savings_percent:.1f}%"
        )
    
    with col3:
        st.metric(
            "Optimized Cost",
            f"${total_suggested_cost:.4f}"
        )
    
    with col4:
        st.metric(
            "Current Savings",
            f"${total_savings:.4f}",
            delta=f"-${total_savings:.4f}"
        )
    
    # Timeline/Heatmap visualization (Requirement 4.4)
    st.subheader("🕐 Cost Distribution Timeline")
    
    # Prepare data for timeline chart
    timeline_data = []
    for schedule in schedule_metadata:
        cost_mb = schedule['cost_mb']
        frequency = schedule['frequency']
        runs_per_day = {
            'hourly': 24,
            'daily': 1,
            'weekly': 1/7
        }.get(frequency, 1)
        
        daily_cost = (cost_mb / 1024) * Config.BIGQUERY_COST_PER_TB * runs_per_day
        
        timeline_data.append({
            'query_name': schedule['name'],
            'current_cron': schedule['cron'],
            'current_daily_cost': daily_cost
        })
    
    timeline_chart = VisualizationManager.create_schedule_timeline(timeline_data)
    st.plotly_chart(timeline_chart, use_container_width=True)
    
    # Comparison table (Requirement 4.5)
    st.subheader("📋 Before/After Schedule Comparison")
    
    table_data = []
    for r in results:
        table_data.append({
            'Query Name': r.query_name,
            'Current Schedule': r.current_cron,
            'Suggested Schedule': r.suggested_cron,
            'Current Daily Cost': f"${r.current_daily_cost:.4f}",
            'Suggested Daily Cost': f"${r.suggested_daily_cost:.4f}",
            'Optimization Type': r.optimization_type.replace('_', ' ').title(),
            'Estimated Savings': f"${r.current_daily_cost - r.suggested_daily_cost:.4f}/day ({r.estimated_savings_percent:.1f}%)"
        })
    
    formatted_df = VisualizationManager.format_results_table(
        table_data,
        ['Query Name', 'Current Schedule', 'Suggested Schedule', 'Current Daily Cost', 
         'Suggested Daily Cost', 'Optimization Type', 'Estimated Savings']
    )
    
    st.dataframe(formatted_df, use_container_width=True, height=400)
    
    # AI Analysis Summary
    st.subheader("🤖 AI Analysis Summary")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Redundant Queries:**")
        redundant = ai_analysis.get('redundant_queries', [])
        if redundant:
            for query in redundant:
                st.write(f"• {query}")
        else:
            st.info("No redundant queries identified")
        
        st.markdown("**Merge Opportunities:**")
        merges = ai_analysis.get('merge_opportunities', [])
        if merges:
            for merge in merges:
                queries = merge.get('queries', [])
                st.write(f"• Merge: {', '.join(queries)}")
                st.caption(f"  Reason: {merge.get('reasoning', 'N/A')}")
        else:
            st.info("No merge opportunities identified")
    
    with col2:
        st.markdown("**Materialized View Candidates:**")
        mv_candidates = ai_analysis.get('materialized_view_candidates', [])
        if mv_candidates:
            for candidate in mv_candidates:
                st.write(f"• {candidate}")
        else:
            st.info("No materialized view candidates identified")
        
        st.markdown("**Overall Estimated Savings:**")
        overall_savings = ai_analysis.get('estimated_savings', 0)
        st.metric("Total Potential Savings", f"{overall_savings:.1f}%")
    
    # Detailed recommendations
    st.subheader("📝 Detailed Recommendations")
    
    for r in results:
        with st.expander(f"{r.query_name} - {r.optimization_type.replace('_', ' ').title()}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Current Configuration:**")
                st.write(f"• Schedule: {r.current_cron}")
                st.write(f"• Daily Cost: ${r.current_daily_cost:.4f}")
                st.write(f"• Monthly Cost: ${r.current_daily_cost * 30:.2f}")
            
            with col2:
                st.markdown("**Suggested Configuration:**")
                st.write(f"• Schedule: {r.suggested_cron}")
                st.write(f"• Daily Cost: ${r.suggested_daily_cost:.4f}")
                st.write(f"• Monthly Cost: ${r.suggested_daily_cost * 30:.2f}")
            
            st.info(f"**Reasoning:** {r.reasoning}")
            
            daily_savings = r.current_daily_cost - r.suggested_daily_cost
            monthly_savings = daily_savings * 30
            
            st.success(f"""
            **Estimated Savings:**
            - Daily: ${daily_savings:.4f} ({r.estimated_savings_percent:.1f}%)
            - Monthly: ${monthly_savings:.2f}
            - Annual: ${monthly_savings * 12:.2f}
            """)
