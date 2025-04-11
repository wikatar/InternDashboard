import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt
from gsheet_connector import BalthazarGSheetConnector
from dashboard_visualizer import BalthazarVisualizer
from datetime import datetime, timedelta

# Set page config
st.set_page_config(
    page_title="Balthazar Project - Daily Dashboard",
    page_icon="📊",
    layout="wide"
)

# Initialize session state for persistent settings
if 'settings' not in st.session_state:
    st.session_state.settings = {
        'sheet_name': '2025',
        'worksheet_name': 'Veckomål',
        'data_range': 'A1:AE100',
        'graph_settings': {
            'figsize': (10, 6),
            'show_grid': True,
            'show_markers': True,
            'goal_color': '#00BFFF',
            'outcome_color': '#FF4B4B'
        }
    }

# Initialize visualizer for storage access
if 'visualizer' not in st.session_state:
    st.session_state.visualizer = BalthazarVisualizer(None)
    
# Load saved configuration if exists
if st.session_state.visualizer.has_config():
    saved_config = st.session_state.visualizer.load_config()
    if saved_config:
        # Update settings from saved config
        if 'sheet_name' in saved_config:
            st.session_state.settings['sheet_name'] = saved_config['sheet_name']
        if 'worksheet_name' in saved_config:
            st.session_state.settings['worksheet_name'] = saved_config['worksheet_name']
        if 'data_range' in saved_config:
            st.session_state.settings['data_range'] = saved_config['data_range']
        if 'credentials_json' in saved_config:
            st.session_state.credentials_json = saved_config['credentials_json']
            # Save credentials to file for use
            with open("temp_credentials.json", "w") as f:
                f.write(saved_config['credentials_json'])

# Try to load saved data if exists
if 'data' not in st.session_state and st.session_state.visualizer.has_browser_data():
    data, date_range = st.session_state.visualizer.load_from_browser()
    if data is not None:
        st.session_state.data = data
        st.session_state.date_range = date_range

# Custom CSS for dark mode enhancements
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 4px 4px 0px 0px;
        padding: 10px 20px;
        background-color: #262730;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FF4B4B !important;
        color: white !important;
    }
    div.block-container {
        padding-top: 2rem;
    }
    .main .block-container {
        padding-bottom: 5rem;
    }
    h1 {
        margin-bottom: 0.5rem;
    }
    footer {
        visibility: hidden;
    }
    .stExpander {
        border: none;
        border-radius: 8px;
    }
    .stStatus {
        width: 100%;
    }
    .metric-container {
        background-color: #262730;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# App title with logo
st.title("🔥 The Balthazar Project - Daily Dashboard")
st.markdown("---")

# Sidebar for configuration
with st.sidebar:
    st.header("Configuration")
    
    # File uploader for credentials
    uploaded_creds = st.file_uploader(
        "Upload Google credentials JSON file", 
        type=["json"], 
        help="Service account credentials for Google Sheets API"
    )
    
    # Credentials text area as an alternative
    if 'credentials_json' in st.session_state:
        credentials_json = st.text_area(
            "Or paste credentials JSON here",
            value=st.session_state.credentials_json,
            height=100,
            help="Paste your Google Service Account credentials JSON"
        )
    else:
        credentials_json = st.text_area(
            "Or paste credentials JSON here",
            height=100,
            help="Paste your Google Service Account credentials JSON"
        )
    
    # Sheet name input with persistent value
    sheet_name = st.text_input(
        "Google Sheet name", 
        value=st.session_state.settings['sheet_name'],
        help="The name of your Google Sheet"
    )
    
    # Worksheet name input with persistent value
    worksheet_name = st.text_input(
        "Worksheet/Tab name", 
        value=st.session_state.settings['worksheet_name'],
        help="The name of the specific tab within your Google Sheet"
    )
    
    # Data range input with persistent value
    data_range = st.text_input(
        "Data range", 
        value=st.session_state.settings['data_range'],
        help="Range of cells to fetch (e.g., A1:Z100)"
    )
    
    # Save configuration button
    if st.button("Save Configuration"):
        config = {
            'sheet_name': sheet_name,
            'worksheet_name': worksheet_name,
            'data_range': data_range,
        }
        
        if credentials_json:
            config['credentials_json'] = credentials_json
            
        success = st.session_state.visualizer.save_config(config)
        if success:
            st.success("Configuration saved!")
            # Update session state
            st.session_state.settings['sheet_name'] = sheet_name
            st.session_state.settings['worksheet_name'] = worksheet_name
            st.session_state.settings['data_range'] = data_range
            if credentials_json:
                st.session_state.credentials_json = credentials_json
        else:
            st.error("Failed to save configuration.")
    
    # Fetch data button
    fetch_button = st.button("Fetch Data", type="primary")
    
    # Clear saved data button
    if st.session_state.visualizer.has_browser_data():
        if st.button("Clear Saved Data"):
            success = st.session_state.visualizer.clear_browser_data()
            if success and 'data' in st.session_state:
                del st.session_state.data
                st.success("Saved data cleared!")
            else:
                st.error("Failed to clear saved data.")
    
    st.markdown("---")
    st.markdown("### Week Range Selection")
    
    # Week range selector - always visible
    col1, col2 = st.columns(2)
    with col1:
        start_week = st.number_input(
            "Start Week",
            value=1,  # Default to week 1
            key="start_week",
            help="Enter the starting week number"
        )
    with col2:
        end_week = st.number_input(
            "End Week",
            value=4,  # Default to week 4
            key="end_week",
            help="Enter the ending week number"
        )
    
    # Store week range in session state
    st.session_state.week_range = (start_week, end_week)
    
    st.markdown("---")
    st.markdown("### Graph Settings")
    
    # Graph customization options
    with st.expander("Customize Graphs", expanded=False):
        # Figure size
        fig_width = st.slider("Figure Width", 8, 20, int(st.session_state.settings['graph_settings']['figsize'][0]))
        fig_height = st.slider("Figure Height", 4, 12, int(st.session_state.settings['graph_settings']['figsize'][1]))
        
        # Grid and markers
        show_grid = st.checkbox("Show Grid", value=st.session_state.settings['graph_settings']['show_grid'])
        show_markers = st.checkbox("Show Markers", value=st.session_state.settings['graph_settings']['show_markers'])
        
        # Colors
        goal_color = st.color_picker("Goal Color", value=st.session_state.settings['graph_settings']['goal_color'])
        outcome_color = st.color_picker("Outcome Color", value=st.session_state.settings['graph_settings']['outcome_color'])
        
        # Save settings button
        if st.button("Save Graph Settings"):
            st.session_state.settings['graph_settings'].update({
                'figsize': (fig_width, fig_height),
                'show_grid': show_grid,
                'show_markers': show_markers,
                'goal_color': goal_color,
                'outcome_color': outcome_color
            })
            st.success("Graph settings saved!")
    
    st.markdown("---")
    st.markdown("### Visualization Options")
    
    # Category selections
    if 'data' in st.session_state:
        df = st.session_state.data
        all_categories = sorted(df["Category"].unique())
        selected_category = st.selectbox(
            "View specific category",
            ["All Categories"] + all_categories
        )

# Main content
if (uploaded_creds is not None or credentials_json) and fetch_button:
    # Save the credentials temporarily
    temp_cred_path = "temp_credentials.json"
    
    if uploaded_creds is not None:
        with open(temp_cred_path, "wb") as f:
            f.write(uploaded_creds.getvalue())
    elif credentials_json:
        with open(temp_cred_path, "w") as f:
            f.write(credentials_json)
            # Update session state
            st.session_state.credentials_json = credentials_json
    
    try:
        # Status message
        status = st.status("Connecting to Google Sheet...")
        
        # Connect to Google Sheet
        connector = BalthazarGSheetConnector(temp_cred_path, sheet_name, worksheet_name)
        
        if connector.connect():
            status.update(label="Fetching data...")
            
            # Fetch and process data
            raw_data = connector.get_data(data_range)
            processed_data = connector.process_data(raw_data)
            
            if not processed_data.empty:
                # Store data in session state
                st.session_state.data = processed_data
                st.session_state.raw_data = raw_data
                
                # Save the configuration
                config = {
                    'sheet_name': sheet_name,
                    'worksheet_name': worksheet_name,
                    'data_range': data_range,
                }
                if credentials_json:
                    config['credentials_json'] = credentials_json
                
                st.session_state.visualizer = BalthazarVisualizer(processed_data)
                
                # Save data to persistent storage
                date_range = (
                    datetime.now().strftime("%Y-%m-%d"), 
                    (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")
                )
                save_success = st.session_state.visualizer.save_to_browser(date_range)
                config_success = st.session_state.visualizer.save_config(config)
                
                if save_success and config_success:
                    status.update(label="✅ Data fetched and saved successfully!", state="complete")
                else:
                    status.update(label="⚠️ Data fetched but couldn't be saved completely", state="error")
            else:
                status.update(label="❌ No data found or processing error", state="error")
        else:
            status.update(label="❌ Failed to connect to Google Sheet", state="error")
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
    
    finally:
        # Clean up temporary credentials file
        if os.path.exists(temp_cred_path) and temp_cred_path != "temp_credentials.json":
            os.remove(temp_cred_path)

# Display dashboard if data is available
if 'data' in st.session_state:
    df = st.session_state.data
    
    # Summary metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric("Total Categories", len(df["Category"].unique()))
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        total_goals = len(df[df["Type"] == "Mål"])
        st.metric("Total Goals", total_goals)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        total_outcomes = len(df[df["Type"] == "Utfall"])
        st.metric("Total Outcomes", total_outcomes)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        days = df["Date"].nunique()
        st.metric("Days Tracked", days)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["Category Groups 📊", "Individual Metrics 📈", "Raw Data 📋"])
    
    with tab1:
        # Create visualizer with custom settings
        visualizer = BalthazarVisualizer(df)
        visualizer.colors = {
            "Mål": st.session_state.settings['graph_settings']['goal_color'],
            "Utfall": st.session_state.settings['graph_settings']['outcome_color']
        }
        visualizer.show_markers = st.session_state.settings['graph_settings']['show_markers']
        visualizer.show_grid = st.session_state.settings['graph_settings']['show_grid']
        visualizer.default_figsize = st.session_state.settings['graph_settings']['figsize']
        
        # Create dashboard visualizations
        week_range = getattr(st.session_state, 'week_range', None)
        figures = visualizer.create_summary_dashboard(x_range=week_range)  # Use selected week range
        
        # Ensure static directory exists
        os.makedirs("static", exist_ok=True)
        
        # Save figures to files
        for group_name, fig in figures.items():
            try:
                # Create filename from group name
                filename = f"static/{group_name.lower().replace(' ', '_')}.png"
                fig.savefig(filename, dpi=300, bbox_inches="tight")
            except Exception as e:
                st.warning(f"Failed to save {group_name} plot: {str(e)}")
            finally:
                plt.close(fig)
        
        # Display each group in an expander
        for group_name, fig in figures.items():
            with st.expander(group_name, expanded=True):
                st.pyplot(fig)
    
    with tab2:
        if 'selected_category' in locals() and selected_category != "All Categories":
            # Create individual category visualization with custom settings
            visualizer = BalthazarVisualizer(df)
            visualizer.colors = {
                "Mål": st.session_state.settings['graph_settings']['goal_color'],
                "Utfall": st.session_state.settings['graph_settings']['outcome_color']
            }
            visualizer.show_markers = st.session_state.settings['graph_settings']['show_markers']
            visualizer.show_grid = st.session_state.settings['graph_settings']['show_grid']
            visualizer.default_figsize = st.session_state.settings['graph_settings']['figsize']
            
            # Use selected week range for individual metrics
            week_range = getattr(st.session_state, 'week_range', None)
            fig = visualizer.create_metric_comparison(selected_category, x_range=week_range)
            st.pyplot(fig)
        else:
            st.info("Select a specific category from the sidebar to see detailed metrics.")
    
    with tab3:
        # Display raw data
        st.subheader("Raw Data")
        st.dataframe(df, use_container_width=True)
        
        # Download option
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download data as CSV",
            data=csv,
            file_name="balthazar_dashboard_data.csv",
            mime="text/csv"
        )
else:
    # Instructions when no data is loaded
    st.info("Upload your Google API credentials and click 'Fetch Data' to start.")
    
    # Sample image placeholder
    st.markdown("### Sample Dashboard Preview")
    
    # Placeholder with instructions
    st.markdown("""
    This dashboard will display:
    1. 💰 **Financial Metrics** (Sales, Expenses)
    2. 📋 **Productivity Metrics** (Meetings, Git Commits, etc.)
    3. 🎬 **Content Metrics** (YouTube Videos)
    4. 📊 **Additional Statistics** (YouTube, Website, Email, Customers)
    
    Each category will show Goals ("Mål") vs. Outcomes ("Utfall") to help identify pain points.
    """)

# Footer
st.markdown("---")
st.caption("The Balthazar Project Dashboard © 2023") 