"""
GCP Cost Optimization Dashboard - Main Application Entry Point

This Streamlit application provides a comprehensive dashboard for simulating
and optimizing Google Cloud Platform costs across multiple domains:
- SQL Query Optimization
- Storage Optimization
- Query Scheduling Optimization
- ML Autoscaling Optimization

Requirements: 6.1, 6.2, 6.4
"""

import streamlit as st
from modules.sql_optimization import render_sql_optimization_module
from modules.storage_optimization import render_storage_optimization_module
from modules.query_scheduling import render_query_scheduling_module
from modules.ml_autoscaling import render_ml_autoscaling_module


def main():
    """
    Main application entry point.
    Sets up Streamlit page configuration, sidebar navigation,
    and renders the selected module.
    """
    try:
        # Set up Streamlit page configuration (Requirement 6.1)
        st.set_page_config(
            page_title="GCP Cost Optimization Dashboard",
            page_icon="💰",
            layout="wide",
            initial_sidebar_state="expanded",
            menu_items={
                'Get Help': None,
                'Report a bug': None,
                'About': "GCP Cost Optimization Dashboard - Simulate and optimize cloud costs with AI"
            }
        )
    except Exception as e:
        # Page config can only be set once, so this is expected on reruns
        pass
    
    # Application header and description (Requirement 6.1)
    st.title("💰 GCP Cost Optimization Dashboard")
    st.markdown("""
    **Simulate Google Cloud Platform workloads and get AI-powered optimization recommendations**
    
    This dashboard helps you identify cost savings opportunities across BigQuery, Cloud Storage, 
    Scheduled Queries, and ML Training Jobs using synthetic data and AI analysis.
    """)
    
    # Initialize session state for module selection (Requirement 6.4)
    if 'selected_module' not in st.session_state:
        st.session_state.selected_module = "SQL Optimization"
    
    # Create sidebar with navigation tabs (Requirement 6.2)
    with st.sidebar:
        st.header("📊 Navigation")
        st.markdown("Select an optimization module:")
        
        # Module selection buttons
        modules = {
            "🔍 SQL Optimization": "SQL Optimization",
            "💾 Storage Optimization": "Storage Optimization",
            "📅 Query Scheduling": "Query Scheduling",
            "🤖 ML Autoscaling": "ML Autoscaling"
        }
        
        # Create radio buttons for module selection
        selected_display = st.radio(
            "Optimization Modules",
            options=list(modules.keys()),
            index=list(modules.values()).index(st.session_state.selected_module),
            label_visibility="collapsed"
        )
        
        # Update session state with selected module
        st.session_state.selected_module = modules[selected_display]
        
        st.divider()
        
        # Configuration status
        st.subheader("⚙️ Configuration")
        
        try:
            from config import Config
            
            config_errors = Config.validate()
            
            if not config_errors:
                st.success("✓ Configuration valid")
                st.info("All required environment variables are set")
            else:
                st.warning("⚠️ Configuration issues detected")
                st.info("Some features may not work correctly")
                with st.expander("View Issues"):
                    for error in config_errors:
                        st.error(f"• {error}")
                    st.info("💡 Tip: Check your .env file and ensure all required variables are set.")
        except Exception as e:
            st.error("❌ Failed to load configuration")
            st.error(f"Details: {str(e)}")
    
    # Render the selected module based on session state (Requirement 6.2, 6.4)
    try:
        if st.session_state.selected_module == "SQL Optimization":
            render_sql_optimization_module()
        elif st.session_state.selected_module == "Storage Optimization":
            render_storage_optimization_module()
        elif st.session_state.selected_module == "Query Scheduling":
            render_query_scheduling_module()
        elif st.session_state.selected_module == "ML Autoscaling":
            render_ml_autoscaling_module()
    except Exception as e:
        st.error(f"❌ Critical Error: Failed to render module")
        st.error(f"Details: {str(e)}")
        st.info("💡 Tip: Try refreshing the page or selecting a different module.")
        # Show exception details in development mode
        from config import Config
        if hasattr(Config, 'DEBUG') and Config.DEBUG:
            st.exception(e)
    
    # Footer
    st.divider()
    st.caption("GCP Cost Optimization Dashboard | Powered by AI | Built with Streamlit")


if __name__ == "__main__":
    main()
