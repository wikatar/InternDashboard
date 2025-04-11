import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt
from gsheet_connector import BalthazarGSheetConnector
from dashboard_visualizer import BalthazarVisualizer

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
    
    # Fetch data button
    fetch_button = st.button("Fetch Data", type="primary")
    
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

# Save settings when inputs change
if sheet_name != st.session_state.settings['sheet_name']:
    st.session_state.settings['sheet_name'] = sheet_name
if worksheet_name != st.session_state.settings['worksheet_name']:
    st.session_state.settings['worksheet_name'] = worksheet_name
if data_range != st.session_state.settings['data_range']:
    st.session_state.settings['data_range'] = data_range

# Main content
if uploaded_creds is not None and fetch_button:
    # Save the credentials temporarily
    temp_cred_path = "temp_credentials.json"
    with open(temp_cred_path, "wb") as f:
        f.write(uploaded_creds.getvalue())
    
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
                
                status.update(label="✅ Data fetched successfully!", state="complete")
            else:
                status.update(label="❌ No data found or processing error", state="error")
        else:
            status.update(label="❌ Failed to connect to Google Sheet", state="error")
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
    
    finally:
        # Clean up temporary credentials file
        if os.path.exists(temp_cred_path):
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
        
        figures = visualizer.create_summary_dashboard()
        
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
            
            fig = visualizer.create_metric_comparison(selected_category)
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