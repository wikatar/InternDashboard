import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
from google_sheets_connector import GoogleSheetsConnector
from dashboard_visualizer import BalthazarVisualizer
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

def main():
    st.set_page_config(
        page_title="Balthazar Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    if 'data' not in st.session_state:
        st.session_state.data = None
    if 'date_range' not in st.session_state:
        st.session_state.date_range = None
    if 'visualizer' not in st.session_state:
        st.session_state.visualizer = BalthazarVisualizer(None)
    if 'config' not in st.session_state:
        st.session_state.config = None
        
    # Try to load saved configuration if exists
    if st.session_state.config is None and st.session_state.visualizer.has_config():
        st.session_state.config = st.session_state.visualizer.load_config()
        
    # Sidebar for configuration
    with st.sidebar:
        st.title("Dashboard Controls")
        
        # Configuration section
        st.subheader("Configuration")
        
        # Google Sheets credentials
        credentials_json = st.text_area(
            "Google Sheets Credentials (JSON)",
            value=st.session_state.config.get("credentials_json", "") if st.session_state.config else "",
            height=200
        )
        
        # Date range selection
        st.subheader("Date Range Selection")
        default_start = datetime.now() - timedelta(days=30)
        default_end = datetime.now()
        
        if st.session_state.config:
            try:
                if isinstance(st.session_state.config.get("date_range", ["", ""])[0], str):
                    default_start = datetime.strptime(st.session_state.config["date_range"][0], "%Y-%m-%d")
                    default_end = datetime.strptime(st.session_state.config["date_range"][1], "%Y-%m-%d")
            except:
                pass
                
        start_date = st.date_input(
            "Start Date",
            value=default_start
        )
        end_date = st.date_input(
            "End Date",
            value=default_end
        )
        
        # Auto-fetch toggle
        auto_fetch = st.checkbox(
            "Auto-fetch on load",
            value=st.session_state.config.get("auto_fetch", False) if st.session_state.config else False
        )
        
        # Save configuration button
        if st.button("Save Configuration"):
            config = {
                "credentials_json": credentials_json,
                "date_range": [
                    start_date.strftime("%Y-%m-%d"),
                    end_date.strftime("%Y-%m-%d")
                ],
                "auto_fetch": auto_fetch
            }
            success = st.session_state.visualizer.save_config(config)
            if success:
                st.session_state.config = config
                st.success("Configuration saved!")
            else:
                st.error("Failed to save configuration.")
        
        # Clear configuration button
        if st.button("Clear Configuration"):
            success = st.session_state.visualizer.clear_config()
            if success:
                st.session_state.config = None
                st.success("Configuration cleared!")
            else:
                st.error("Failed to clear configuration.")
                
        # Try to load saved data if exists
        if st.session_state.visualizer.has_browser_data() and st.session_state.data is None:
            if st.button("Load Saved Data"):
                data, date_range = st.session_state.visualizer.load_from_browser()
                if data is not None:
                    st.session_state.data = data
                    st.session_state.date_range = date_range
                    st.session_state.visualizer = BalthazarVisualizer(data)
                    st.success("Data loaded successfully!")
                else:
                    st.error("Failed to load saved data.")
                    
        # Fetch data button
        if st.button("Fetch Data"):
            with st.spinner("Fetching data from Google Sheets..."):
                try:
                    # Save credentials to file if provided
                    if credentials_json:
                        with open("google_credentials.json", "w") as f:
                            f.write(credentials_json)
                            
                    connector = GoogleSheetsConnector()
                    data = connector.fetch_data(start_date, end_date)
                    if data is not None:
                        st.session_state.data = data
                        st.session_state.date_range = (start_date, end_date)
                        st.session_state.visualizer = BalthazarVisualizer(data)
                        
                        # Save data to storage
                        success = st.session_state.visualizer.save_to_browser(st.session_state.date_range)
                        if success:
                            st.success("Data fetched and saved successfully!")
                        else:
                            st.warning("Data fetched but could not be saved.")
                    else:
                        st.error("Failed to fetch data. Please check your connection.")
                except Exception as e:
                    st.error(f"Error fetching data: {str(e)}")
                    
    # Main content area
    st.title("Balthazar Dashboard")
    
    # Auto-fetch data if configured
    if auto_fetch and st.session_state.config and st.session_state.data is None:
        with st.spinner("Auto-fetching data..."):
            try:
                start_date = datetime.strptime(st.session_state.config["date_range"][0], "%Y-%m-%d").date()
                end_date = datetime.strptime(st.session_state.config["date_range"][1], "%Y-%m-%d").date()
                
                if st.session_state.config.get("credentials_json"):
                    with open("google_credentials.json", "w") as f:
                        f.write(st.session_state.config["credentials_json"])
                        
                connector = GoogleSheetsConnector()
                data = connector.fetch_data(start_date, end_date)
                if data is not None:
                    st.session_state.data = data
                    st.session_state.date_range = (start_date, end_date)
                    st.session_state.visualizer = BalthazarVisualizer(data)
                    
                    # Save data to storage
                    success = st.session_state.visualizer.save_to_browser(st.session_state.date_range)
                    if success:
                        st.success("Data auto-fetched and saved successfully!")
                    else:
                        st.warning("Data auto-fetched but could not be saved.")
                else:
                    st.error("Failed to auto-fetch data. Please check your connection.")
            except Exception as e:
                st.error(f"Error auto-fetching data: {str(e)}")
    
    # Check if we should try loading data from disk at startup
    if st.session_state.data is None and st.session_state.visualizer.has_browser_data():
        try:
            data, date_range = st.session_state.visualizer.load_from_browser()
            if data is not None:
                st.session_state.data = data
                st.session_state.date_range = date_range
                st.session_state.visualizer = BalthazarVisualizer(data)
                st.info("Previously saved data loaded automatically.")
        except Exception as e:
            st.warning(f"Could not load saved data: {str(e)}")
    
    if st.session_state.data is not None and st.session_state.visualizer is not None:
        # Display metrics
        st.header("Key Metrics")
        metrics = st.session_state.visualizer.create_metrics_display()
        st.plotly_chart(metrics, use_container_width=True)
        
        # Display category plots
        st.header("Category Analysis")
        category_plots = st.session_state.visualizer.create_category_plots()
        for plot in category_plots:
            st.plotly_chart(plot, use_container_width=True)
            
        # Display comparison plots
        st.header("Metric Comparisons")
        comparison_plots = st.session_state.visualizer.create_comparison_plots()
        for plot in comparison_plots:
            st.plotly_chart(plot, use_container_width=True)
    else:
        st.info("Please select a date range and fetch data to view the dashboard.")

if __name__ == "__main__":
    main() 