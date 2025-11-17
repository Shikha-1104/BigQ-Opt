"""
ML Autoscaling Optimization Module for GCP Cost Optimization Dashboard.

This module provides the UI and workflow for simulating and optimizing
ML training jobs with AI-powered compute optimization recommendations.
"""

import streamlit as st
from typing import List, Dict
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from services.ai_optimizer_service import AIOptimizerService
from services.visualization_manager import VisualizationManager
from simulators.ml_job_simulator import MLJobSimulator
from models.data_models import MLOptimizationResult


def render_ml_autoscaling_module():
    """
    Renders the ML autoscaling optimization module UI with simulation workflow
    and results visualization.
    
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 6.1, 6.2, 6.3
    """
    st.header("🤖 ML Auto Scaling Optimization")
    st.markdown("""
    Simulate ML training job workloads and get AI-powered optimization recommendations
    for compute resources, including spot VM usage, machine type adjustments, and autoscaling strategies.
    """)
    
    # Initialize session state for results
    if 'ml_optimization_results' not in st.session_state:
        st.session_state.ml_optimization_results = None
    if 'ml_job_metadata' not in st.session_state:
        st.session_state.ml_job_metadata = None
    if 'ml_ai_suggestions' not in st.session_state:
        st.session_state.ml_ai_suggestions = None
    
    # Configuration options
    st.subheader("Simulation Settings")
    
    col1, col2 = st.columns(2)
    with col1:
        job_count = st.slider(
            "Number of ML training jobs to simulate:",
            min_value=5,
            max_value=20,
            value=10,
            help="Number of synthetic ML training jobs to generate and analyze"
        )
    
    with col2:
        st.write("")  # Spacing
    
    # Information about ML optimization
    with st.expander("ℹ️ ML Compute Optimization Strategies"):
        st.markdown("""
        **Common Optimization Opportunities:**
        - **Spot VMs**: Use preemptible instances for ~70% cost savings on fault-tolerant workloads
        - **Machine Type Reduction**: Downgrade to smaller accelerators when sufficient
        - **Autoscaling**: Reduce peak nodes and enable dynamic scaling
        - **Vertex AI Caching**: Cache preprocessing steps to avoid redundant computation
        - **Accelerator Alternatives**: Switch to cheaper but sufficient accelerators
        
        **Accelerator Costs (per hour):**
        - T4 GPU: $0.35/hour
        - V100 GPU: $2.48/hour
        - A100 GPU: $3.67/hour
        - TPU v2: $4.50/hour
        - TPU v3: $8.00/hour
        
        **Typical Savings:**
        - Spot VMs: 60-70% cost reduction
        - Accelerator downgrade (A100→T4): Up to 90% savings
        - Combined optimizations: 80-90% total savings possible
        """)
    
    # Simulate button (Requirement 6.3)
    if st.button("🚀 Simulate ML Optimization", type="primary", use_container_width=True):
        with st.spinner("Starting ML optimization workflow..."):
            _run_ml_optimization_workflow(job_count)
    
    # Display results if available (Requirement 5.4, 5.5)
    if st.session_state.ml_optimization_results:
        _display_ml_optimization_results(
            st.session_state.ml_optimization_results,
            st.session_state.ml_job_metadata,
            st.session_state.ml_ai_suggestions
        )


def _run_ml_optimization_workflow(job_count: int):
    """
    Executes the ML optimization workflow:
    1. Generate synthetic ML training job metadata
    2. Get AI optimization suggestions
    3. Store results in session state
    
    Requirements: 5.1, 5.2, 5.3
    
    Args:
        job_count: Number of ML training jobs to generate
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
        with st.spinner("🔧 Initializing AI optimizer and ML job simulator..."):
            try:
                ai_optimizer = AIOptimizerService(
                    api_key=Config.GEMINI_API_KEY if Config.AI_PROVIDER == "gemini" else Config.OPENAI_API_KEY,
                    provider=Config.AI_PROVIDER
                )
                
                ml_simulator = MLJobSimulator()
                st.info("✓ Services initialized successfully")
            except Exception as e:
                st.error(f"❌ Critical Error: Failed to initialize services")
                st.error(f"Details: {str(e)}")
                st.info("💡 Tip: Verify your AI API key is valid and the provider is correctly configured.")
                return
        
        # Step 1: Generate ML training job metadata (Requirement 5.1)
        with st.spinner(f"🤖 Generating {job_count} synthetic ML training jobs..."):
            try:
                ml_job_metadata = ml_simulator.generate_training_jobs(count=job_count)
                st.success(f"✓ Generated {len(ml_job_metadata)} ML training jobs")
                
                # Store job metadata in session state
                st.session_state.ml_job_metadata = ml_job_metadata
            except Exception as e:
                st.error(f"❌ Failed to generate ML job metadata: {str(e)}")
                st.info("💡 Tip: This is usually a temporary issue. Try again or reduce the job count.")
                return
        
        # Step 2: Get AI optimization suggestions (Requirement 5.2, 5.3)
        with st.spinner("🤖 Analyzing ML jobs with AI for optimization opportunities..."):
            try:
                ai_suggestions = ai_optimizer.optimize_ml_jobs(ml_job_metadata)
                st.success(f"✓ Generated {len(ai_suggestions)} optimization suggestions")
                
                # Store AI suggestions in session state
                st.session_state.ml_ai_suggestions = ai_suggestions
            except Exception as e:
                st.error(f"❌ Failed to analyze ML jobs with AI")
                st.error(f"Details: {str(e)}")
                st.info("💡 Tip: This could be due to AI API rate limits or network issues. Wait a moment and try again.")
                return
        
        # Process AI suggestions into result objects
        results = []
        
        for suggestion in ai_suggestions:
            job_name = suggestion['job_name']
            current_config = suggestion['current_config']
            suggested_config = suggestion['suggested_config']
            optimization_type = suggestion['optimization_type']
            estimated_savings_percent = suggestion['estimated_savings_percent']
            
            # Find the corresponding job metadata
            job_info = next(
                (j for j in ml_job_metadata if j['job_name'] == job_name),
                None
            )
            
            if job_info:
                current_cost = job_info['estimated_cost']
                
                # Calculate suggested cost based on savings percentage
                suggested_cost = current_cost * (1 - estimated_savings_percent / 100)
                
                # Generate implementation notes
                implementation_notes = _generate_implementation_notes(
                    optimization_type,
                    current_config,
                    suggested_config
                )
                
                result = MLOptimizationResult(
                    job_name=job_name,
                    current_accelerator=current_config.get('accelerator_type', 'Unknown'),
                    suggested_accelerator=suggested_config.get('accelerator_type', 'Unknown'),
                    current_cost=current_cost,
                    suggested_cost=suggested_cost,
                    optimization_type=optimization_type,
                    estimated_savings_percent=estimated_savings_percent,
                    implementation_notes=implementation_notes
                )
                
                results.append(result)
        
        if not results:
            st.warning("⚠️ No optimization recommendations were generated")
            st.info("💡 The AI may not have found significant optimization opportunities for the simulated ML jobs. Try generating more jobs or running the simulation again.")
            return
        
        # Step 3: Store results in session state
        st.session_state.ml_optimization_results = results
        
        # Show summary
        total_current_cost = sum(r.current_cost for r in results)
        total_suggested_cost = sum(r.suggested_cost for r in results)
        total_savings = total_current_cost - total_suggested_cost
        avg_savings_percent = sum(r.estimated_savings_percent for r in results) / len(results)
        
        st.success(f"""
        ✅ **Analysis Complete!**
        - ML Jobs Analyzed: {len(ml_job_metadata)}
        - Optimization Recommendations: {len(results)}
        - Average Savings: {avg_savings_percent:.1f}%
        - Estimated Cost Reduction: ${total_savings:.2f}
        - Potential Monthly Savings: ${total_savings:.2f}
        """)
        
    except Exception as e:
        st.error(f"❌ Critical Error: An unexpected error occurred during ML optimization")
        st.error(f"Details: {str(e)}")
        st.info("💡 Tip: Try refreshing the page and starting over. If the issue persists, check your configuration.")
        # Only show exception in development
        if Config.DEBUG if hasattr(Config, 'DEBUG') else False:
            st.exception(e)


def _generate_implementation_notes(
    optimization_type: str,
    current_config: Dict,
    suggested_config: Dict
) -> str:
    """
    Generates implementation notes based on optimization type.
    
    Args:
        optimization_type: Type of optimization
        current_config: Current configuration
        suggested_config: Suggested configuration
        
    Returns:
        Implementation notes string
    """
    notes = []
    
    if 'spot' in optimization_type.lower():
        notes.append("Enable spot/preemptible VMs in Vertex AI training configuration")
        notes.append("Implement checkpointing to handle potential interruptions")
    
    if 'downgrade' in optimization_type.lower() or 'machine_type' in optimization_type.lower():
        current_acc = current_config.get('accelerator_type', 'Unknown')
        suggested_acc = suggested_config.get('accelerator_type', 'Unknown')
        notes.append(f"Change accelerator from {current_acc} to {suggested_acc}")
        notes.append("Test model performance with new accelerator type")
    
    if 'autoscaling' in optimization_type.lower():
        notes.append("Configure autoscaling policies in Vertex AI")
        notes.append("Set appropriate min/max node counts")
    
    if 'caching' in optimization_type.lower():
        notes.append("Enable Vertex AI caching for preprocessing steps")
        notes.append("Cache feature engineering pipelines")
    
    if not notes:
        notes.append("Review AI suggestions and implement recommended changes")
    
    return " | ".join(notes)


def _display_ml_optimization_results(
    results: List[MLOptimizationResult],
    ml_job_metadata: List[Dict],
    ai_suggestions: List[Dict]
):
    """
    Displays ML optimization results with donut chart and recommendations table.
    
    Requirements: 5.4, 5.5
    
    Args:
        results: List of MLOptimizationResult objects
        ml_job_metadata: List of ML job metadata dictionaries
        ai_suggestions: List of AI suggestion dictionaries
    """
    st.divider()
    st.subheader("📊 Optimization Results")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    total_jobs = len(ml_job_metadata)
    total_current_cost = sum(r.current_cost for r in results)
    total_suggested_cost = sum(r.suggested_cost for r in results)
    total_savings = total_current_cost - total_suggested_cost
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
            f"${total_suggested_cost:.2f}"
        )
    
    with col4:
        st.metric(
            "Current Savings",
            f"${total_savings:.2f}",
            delta=f"-${total_savings:.2f}"
        )
    
    # Donut chart visualization (Requirement 5.4)
    st.subheader("💰 ML Job Cost Breakdown")
    
    # Prepare data for donut chart
    chart_data = []
    for job in ml_job_metadata:
        chart_data.append({
            'job_name': job['job_name'],
            'current_cost': job['estimated_cost']
        })
    
    donut_chart = VisualizationManager.create_ml_cost_breakdown(chart_data)
    st.plotly_chart(donut_chart, use_container_width=True)
    
    # Recommendations table (Requirement 5.5)
    st.subheader("📋 Optimization Recommendations")
    
    table_data = []
    for r in results:
        savings_amount = r.current_cost - r.suggested_cost
        
        table_data.append({
            'Job Name': r.job_name,
            'Current Accelerator': r.current_accelerator,
            'Suggested Accelerator': r.suggested_accelerator,
            'Current Cost': f"${r.current_cost:.2f}",
            'Suggested Cost': f"${r.suggested_cost:.2f}",
            'Optimization Type': r.optimization_type.replace('_', ' ').title(),
            'Projected Savings': f"${savings_amount:.2f} ({r.estimated_savings_percent:.1f}%)"
        })
    
    formatted_df = VisualizationManager.format_results_table(
        table_data,
        ['Job Name', 'Current Accelerator', 'Suggested Accelerator', 'Current Cost',
         'Suggested Cost', 'Optimization Type', 'Projected Savings']
    )
    
    st.dataframe(formatted_df, use_container_width=True, height=400)
    
    # Optimization type breakdown
    st.subheader("🔍 Optimization Strategy Breakdown")
    
    # Count optimization types
    optimization_counts = {}
    for r in results:
        opt_type = r.optimization_type.replace('_', ' ').title()
        optimization_counts[opt_type] = optimization_counts.get(opt_type, 0) + 1
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Optimization Types:**")
        for opt_type, count in optimization_counts.items():
            st.write(f"• {opt_type}: {count} job(s)")
    
    with col2:
        st.markdown("**Cost Impact:**")
        st.metric("Total Current Cost", f"${total_current_cost:.2f}")
        st.metric("Total Optimized Cost", f"${total_suggested_cost:.2f}")
        st.metric("Total Savings", f"${total_savings:.2f}")
    
    # Detailed recommendations
    st.subheader("📝 Detailed Recommendations")
    
    for r in results:
        with st.expander(f"{r.job_name} - {r.optimization_type.replace('_', ' ').title()}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Current Configuration:**")
                st.write(f"• Accelerator: {r.current_accelerator}")
                st.write(f"• Estimated Cost: ${r.current_cost:.2f}")
                
                # Find job metadata for additional details
                job_info = next(
                    (j for j in ml_job_metadata if j['job_name'] == r.job_name),
                    None
                )
                if job_info:
                    st.write(f"• GPU Hours: {job_info['gpu_hours']:.2f}")
                    st.write(f"• Peak Nodes: {job_info['peak_nodes']}")
                    st.write(f"• Training Duration: {job_info['training_duration_hours']:.2f}h")
            
            with col2:
                st.markdown("**Suggested Configuration:**")
                st.write(f"• Accelerator: {r.suggested_accelerator}")
                st.write(f"• Estimated Cost: ${r.suggested_cost:.2f}")
                st.write(f"• Optimization: {r.optimization_type.replace('_', ' ').title()}")
            
            st.info(f"**Implementation Notes:** {r.implementation_notes}")
            
            savings_amount = r.current_cost - r.suggested_cost
            
            st.success(f"""
            **Projected Savings:**
            - Per Job: ${savings_amount:.2f} ({r.estimated_savings_percent:.1f}%)
            - Monthly (if run weekly): ${savings_amount * 4:.2f}
            - Annual (if run weekly): ${savings_amount * 52:.2f}
            """)
    
    # Additional insights
    st.subheader("💡 Key Insights")
    
    # Find highest savings opportunity
    max_savings_result = max(results, key=lambda r: r.current_cost - r.suggested_cost)
    max_savings_amount = max_savings_result.current_cost - max_savings_result.suggested_cost
    
    # Find most common optimization type
    most_common_opt = max(optimization_counts.items(), key=lambda x: x[1])
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Highest Savings Opportunity:**")
        st.write(f"{max_savings_result.job_name}")
        st.write(f"${max_savings_amount:.2f} savings")
    
    with col2:
        st.markdown("**Most Common Optimization:**")
        st.write(f"{most_common_opt[0]}")
        st.write(f"{most_common_opt[1]} job(s)")
    
    with col3:
        st.markdown("**Average Savings Per Job:**")
        avg_savings_per_job = total_savings / len(results)
        st.write(f"${avg_savings_per_job:.2f}")
        st.write(f"{avg_savings_percent:.1f}%")
