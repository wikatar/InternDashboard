import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt
from gsheet_connector import BalthazarGSheetConnector
from dashboard_visualizer import BalthazarVisualizer
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

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
    
    # Add Debug buttons for direct data inspection
    with st.expander("Raw Data Inspection", expanded=False):
        if 'data' in st.session_state:
            if st.button("Show Sales Data Only"):
                sales_data = st.session_state.data[st.session_state.data["Category"] == "Försäljning SEK eller högre"]
                st.dataframe(sales_data)
                st.text(f"Sales data shape: {sales_data.shape}")
                
            if st.button("View All Raw Data"):
                st.dataframe(st.session_state.data)
    
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
    # Status message
    status = st.status("Connecting to Google Sheet...")
    
    try:
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
        
        # Connect to Google Sheet
        connector = BalthazarGSheetConnector(temp_cred_path, sheet_name, worksheet_name)
        
        if connector.connect():
            status.update(label="Fetching data...")
            
            # Fetch and process data
            raw_data = connector.get_data(data_range)
            processed_data = connector.process_data(raw_data)
            
            if not processed_data.empty:
                # Display info about the data being fetched
                st.info(f"Fetched {len(processed_data)} data points across {processed_data['Category'].nunique()} categories.")
                
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
                
                try:
                    # First try to save the configuration
                    config_success = st.session_state.visualizer.save_config(config)
                    
                    # Then try to save the data
                    save_success = st.session_state.visualizer.save_to_browser(date_range)
                    
                    if save_success and config_success:
                        status.update(label="✅ Data fetched and saved successfully!", state="complete")
                    elif save_success:
                        status.update(label="✅ Data fetched but config couldn't be saved", state="error")
                    elif config_success:
                        status.update(label="✅ Data fetched but couldn't be saved to browser", state="error")
                    else:
                        status.update(label="✅ Data fetched but nothing could be saved", state="error")
                except Exception as e:
                    status.update(label=f"✅ Data fetched but error saving: {str(e)}", state="error")
                    print(f"Error during save: {str(e)}")
                
                # Output the structure of the processed data for debugging
                with st.expander("Data Structure Details", expanded=False):
                    st.write("### Data Structure")
                    st.write(f"Categories: {sorted(processed_data['Category'].unique())}")
                    st.write(f"Types: {sorted(processed_data['Type'].unique())}")
                    st.write(f"Weeks: {sorted(processed_data['Date'].unique())}")
            else:
                status.update(label="❌ No data found or processing error", state="error")
                st.error("The data processing yielded an empty DataFrame. Please check the sheet structure.")
                
                # Help debugging the data structure
                if raw_data:
                    st.subheader("Raw Data Preview")
                    st.write("First few rows of raw data from Google Sheets:")
                    st.write(raw_data[:5])
        else:
            status.update(label="❌ Failed to connect to Google Sheet", state="error")
    
    except Exception as e:
        status.update(label=f"❌ Error: {str(e)}", state="error")
        st.error(f"Error details: {str(e)}")
        import traceback
        st.code(traceback.format_exc(), language="python")
    
    finally:
        # Clean up temporary credentials file
        if os.path.exists(temp_cred_path) and temp_cred_path != "temp_credentials.json":
            os.remove(temp_cred_path)

# Display dashboard if data is available
if 'data' in st.session_state and st.session_state.data is not None:
    df = st.session_state.data.copy()
    
    # Validate that data has the required format
    required_columns = ["Date", "Category", "Type", "Value"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        st.error(f"Data is missing required columns: {', '.join(missing_columns)}")
    else:
        # Debug data before conversion - hide in expander
        with st.expander("Debug Data (Click to expand)", expanded=False):
            st.write("### Debug: Data Summary Before Processing")
            st.write(f"Data shape: {df.shape}")
            st.write(f"Data types: {df.dtypes}")
            st.write(f"Sample data:\n{df.head(3)}")
            
            # Convert the data to numeric where appropriate
            df["Value"] = pd.to_numeric(df["Value"], errors="coerce")
            df["Date"] = pd.to_numeric(df["Date"], errors="coerce")
            
            # Ensure we have a Week column for visualization
            if "Week" not in df.columns:
                df["Week"] = df["Date"]
            
            # Set Week column to int type for proper display
            df["Week"] = df["Week"].astype(int)
            
            # Drop any rows with NaN values
            orig_len = len(df)
            df = df.dropna(subset=["Value", "Date"])
            if len(df) < orig_len:
                st.warning(f"Dropped {orig_len - len(df)} rows with invalid values.")
                
            # Debug data after conversion    
            st.write("### Debug: Data Summary After Processing")
            st.write(f"Data shape: {df.shape}")
            st.write(f"Columns: {df.columns.tolist()}")
            st.write(f"Week values: {sorted(df['Week'].unique())}")
            st.write(f"Categories: {sorted(df['Category'].unique())}")
            st.write(f"Types: {sorted(df['Type'].unique())}")
        
        # Explicitly update the data in session state with processed version
        st.session_state.data = df.copy()
        
        # Summary metrics in columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
            total_categories = len(df["Category"].unique())
            st.metric("Total Categories", total_categories)
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
            weeks = df["Week"].nunique()
            st.metric("Weeks Tracked", weeks)
            st.markdown('</div>', unsafe_allow_html=True)
            
        # Add debug visualization in an expander
        with st.expander("Visualization Debug (Click to expand)", expanded=False):
            st.write("Data sample:")
            st.dataframe(df.head(10))
            
            # Check data types - sometimes visualizations fail due to type issues
            st.write("Data types:")
            st.write(df.dtypes)
            
            # Check if there are any visualizations
            st.write("Creating visualizer with data...")
            debug_visualizer = BalthazarVisualizer(df)
            
            # Output category information
            st.write(f"Detected metrics: {debug_visualizer.metrics}")
            st.write(f"Detected categories: {debug_visualizer.categories}")
            
            # Try to create a test plot for the first category if available
            if debug_visualizer.categories:
                st.write(f"Attempting to create plot for {debug_visualizer.categories[0]}...")
                test_fig = debug_visualizer.create_metric_comparison(debug_visualizer.categories[0])
                st.pyplot(test_fig)
        
        st.markdown("---")
        
        # Create tabs for different visualization options
        plot_style = st.radio(
            "Select Plot Style",
            ["Simple Line Charts", "Advanced Line Charts", "Category Groups", "Individual Metrics", "Raw Data"],
            horizontal=True
        )

        # Week range filter
        week_range = st.session_state.week_range if hasattr(st.session_state, 'week_range') else None

        # Set default for controls
        if 'show_values' not in st.session_state:
            st.session_state.show_values = True
        if 'invert_metrics' not in st.session_state:
            st.session_state.invert_metrics = True

        # Controls
        with st.expander("Chart Controls", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                show_values = st.checkbox("Show Values on Points", value=st.session_state.show_values)
                st.session_state.show_values = show_values
            with col2:
                invert_metrics = st.checkbox("Invert 'Lower is Better' Metrics", value=st.session_state.invert_metrics)
                st.session_state.invert_metrics = invert_metrics

        st.markdown("---")

        # Main content container with padding
        main_container = st.container()

        # Initialize visualization engine
        if 'data' in st.session_state and st.session_state.data is not None:
            df = st.session_state.data.copy()
            
            # Create visualizer with custom settings
            visualizer = BalthazarVisualizer(df)
            visualizer.colors = {
                "Mål": st.session_state.settings['graph_settings']['goal_color'],
                "Utfall": st.session_state.settings['graph_settings']['outcome_color']
            }
            
            # Group categories
            financial = ["Försäljning SEK eller högre", "Utgifter SEK eller lägre", "Resultat SEK"]
            productivity = [
                "Bokade möten", "Git commits", "Artiklar Hemsida (SEO)",
                "Gratis verktyg hemsida (SEO)", "Skickade E-post", 
                "Färdiga moment produktion"
            ]
            content = ["Långa YT videos", "Korta YT videos"]
            
            # Filter categories that exist in the data
            data_categories = set(df["Category"].unique())
            financial_filtered = [cat for cat in financial if cat in data_categories]
            productivity_filtered = [cat for cat in productivity if cat in data_categories]
            content_filtered = [cat for cat in content if cat in data_categories]
            
            # Get any other categories
            other_categories = [cat for cat in data_categories if cat not in financial + productivity + content]
            
            # Render the selected visualization type
            if plot_style == "Simple Line Charts":
                # Create simple charts for each category group
                all_groups = [
                    ("Financial Metrics", financial_filtered),
                    ("Productivity Metrics", productivity_filtered),
                    ("Content Metrics", content_filtered)
                ]
                
                if other_categories:
                    all_groups.append(("Other Metrics", other_categories))
                    
                # COMPLETELY NEW IMPLEMENTATION - DIRECT PLOTTING
                for group_name, categories in all_groups:
                    if not categories:
                        continue
                        
                    with st.expander(group_name, expanded=True):
                        for category in categories:
                            st.write(f"### {category}")
                            
                            # Filter directly from the raw data
                            cat_data = df[df["Category"] == category].copy()
                            
                            if cat_data.empty:
                                st.warning(f"No data for {category}")
                                continue
                            
                            # Direct plotting approach
                            fig = go.Figure()
                            
                            # Get goal data
                            goal_data = cat_data[cat_data["Type"] == "Mål"]
                            if not goal_data.empty:
                                # Sort by week
                                goal_data = goal_data.sort_values("Week")
                                
                                # Plot goals
                                fig.add_trace(go.Scatter(
                                    x=goal_data["Week"].tolist(),
                                    y=goal_data["Value"].tolist(),
                                    mode="lines+markers",
                                    name="Mål",
                                    line=dict(color="#00BFFF", width=2, dash="dash"),
                                    marker=dict(size=8, symbol="circle")
                                ))
                                
                                # If this is Försäljning SEK eller högre and we only have one data point
                                # Add additional handling to make sure the sales graph looks good
                                if category == "Försäljning SEK eller högre" and len(goal_data) == 1:
                                    # Get current value
                                    current_week = goal_data["Week"].iloc[0]
                                    current_val = goal_data["Value"].iloc[0]
                                    
                                    # Create a list of new rows with the same goal value for all weeks
                                    new_rows = []
                                    for week in range(15, 27):
                                        if week != current_week:
                                            new_rows.append({
                                                "Week": week,
                                                "Value": current_val,
                                                "Type": "Mål",
                                                "Category": category
                                            })
                                    
                                    # Use concat instead of append (which is deprecated)
                                    if new_rows:
                                        new_df = pd.DataFrame(new_rows)
                                        goal_data = pd.concat([goal_data, new_df], ignore_index=True)
                                        
                                        # Sort again
                                        goal_data = goal_data.sort_values("Week")
                                        
                                        # Update the plot with extended goal data
                                        fig.data[0].x = goal_data["Week"].tolist()
                                        fig.data[0].y = goal_data["Value"].tolist()
                                
                                # Add labels to points
                                if show_values:
                                    for i, row in goal_data.iterrows():
                                        fig.add_annotation(
                                            x=row["Week"],
                                            y=row["Value"],
                                            text=str(int(row["Value"]) if row["Value"] == int(row["Value"]) else f"{row['Value']:.1f}"),
                                            showarrow=False,
                                            yshift=10,
                                            font=dict(color="#00BFFF"),
                                            bgcolor="rgba(0,0,0,0.6)",
                                            bordercolor="#00BFFF",
                                            borderwidth=1
                                        )
                            
                            # Get outcome data
                            outcome_data = cat_data[cat_data["Type"] == "Utfall"]
                            # Handle case where outcome data is empty but goals exist
                            if outcome_data.empty and not goal_data.empty:
                                # Create synthetic zeros for all weeks with goals
                                outcome_weeks = goal_data["Week"].unique()
                                
                                # Special case for Försäljning SEK eller högre - show all weeks 15-26
                                if category == "Försäljning SEK eller högre":
                                    outcome_weeks = list(range(15, 27))  # Weeks 15-26
                                
                                outcome_x = outcome_weeks.tolist() if not isinstance(outcome_weeks, list) else outcome_weeks
                                outcome_y = [0] * len(outcome_weeks)
                            elif not outcome_data.empty:
                                # Sort by week
                                outcome_data = outcome_data.sort_values("Week")
                                
                                # Plot outcomes
                                fig.add_trace(go.Scatter(
                                    x=outcome_data["Week"].tolist(),
                                    y=outcome_data["Value"].tolist(),
                                    mode="lines+markers",
                                    name="Utfall",
                                    line=dict(color="#FF4B4B", width=2),
                                    marker=dict(size=8, symbol="circle")
                                ))
                                
                                # Add labels to points
                                if show_values:
                                    for i, row in outcome_data.iterrows():
                                        fig.add_annotation(
                                            x=row["Week"],
                                            y=row["Value"],
                                            text=str(int(row["Value"]) if row["Value"] == int(row["Value"]) else f"{row['Value']:.1f}"),
                                            showarrow=False,
                                            yshift=10,
                                            font=dict(color="#FF4B4B"),
                                            bgcolor="rgba(0,0,0,0.6)",
                                            bordercolor="#FF4B4B",
                                            borderwidth=1
                                        )
                            
                            # Check if this is a "lower is better" metric
                            is_lower_better = any(pattern in category.lower() for pattern in ["lägre", "mindre", "lower", "utgifter"])
                            
                            # Set axis ranges
                            all_weeks = []
                            if not goal_data.empty:
                                all_weeks.extend(goal_data["Week"].tolist())
                            if not outcome_data.empty:
                                all_weeks.extend(outcome_data["Week"].tolist())
                            
                            # Get week range
                            if all_weeks:
                                min_week = min(all_weeks)
                                max_week = max(all_weeks)
                                
                                # For Försäljning SEK eller högre, ensure we show the full range even if data is limited
                                if category == "Försäljning SEK eller högre":
                                    if max_week - min_week < 10:  # If range is too small
                                        min_week = 15
                                        max_week = 26
                                
                                if week_range:
                                    if week_range[0] <= max_week and week_range[1] >= min_week:
                                        min_week = max(min_week, week_range[0])
                                        max_week = min(max_week, week_range[1])
                            else:
                                # Default to weeks 15-26 if no data
                                min_week = 15
                                max_week = 26
                            
                            # Get y-axis range with padding
                            all_values = []
                            if not goal_data.empty:
                                all_values.extend(goal_data["Value"].tolist())
                            if not outcome_data.empty:
                                all_values.extend(outcome_data["Value"].tolist())
                                
                            if all_values:
                                min_val = min(all_values)
                                max_val = max(all_values)
                                # Add 20% padding to top and 10% to bottom
                                y_padding_top = (max_val - min_val) * 0.2
                                y_padding_bottom = (max_val - min_val) * 0.1
                                y_min = max(0, min_val - y_padding_bottom)  # Don't go below zero unless data is negative
                                y_max = max_val + y_padding_top
                                
                                # Special case for Försäljning SEK eller högre to ensure proper scale
                                if category == "Försäljning SEK eller högre":
                                    # Ensure maximum of 7000 to show 5000 comfortably
                                    y_max = max(7000, y_max)
                            else:
                                y_min = 0
                                y_max = 100
                                
                                # Special case for Försäljning SEK eller högre
                                if category == "Försäljning SEK eller högre":
                                    y_max = 7000  # Default max for sales
                            
                            # Update layout
                            fig.update_layout(
                                title=f"{category}",
                                xaxis=dict(
                                    title="Week",
                                    tickmode="linear",
                                    dtick=1,
                                    range=[min_week-0.5, max_week+0.5],
                                    gridcolor="#444444"
                                ),
                                yaxis=dict(
                                    title="Value",
                                    autorange="reversed" if is_lower_better and invert_metrics else None,
                                    gridcolor="#444444",
                                    range=[y_min, y_max] if not (is_lower_better and invert_metrics) else [y_max, y_min]
                                ),
                                plot_bgcolor="#262730",
                                paper_bgcolor="#262730",
                                font=dict(color="white"),
                                showlegend=True,
                                legend=dict(
                                    x=0.01,
                                    y=0.99,
                                    bordercolor="white",
                                    borderwidth=1,
                                    font=dict(color="white")
                                ),
                                height=400,
                                width=None,
                                margin=dict(l=50, r=50, t=50, b=50)
                            )
                            
                            # Show goal and outcome counts
                            st.caption(f"Data points: Mål: {len(goal_data)}, Utfall: {len(outcome_data)}")
                            
                            # Display the figure
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Add detailed data points debug info
                            if category == "Försäljning SEK eller högre":
                                with st.expander("Debug Data", expanded=False):
                                    st.write("### Goal Data Points")
                                    if not goal_data.empty:
                                        st.dataframe(goal_data[["Week", "Value"]])
                                    else:
                                        st.write("No goal data")
                                        
                                    st.write("### Outcome Data Points")
                                    if not outcome_data.empty:
                                        st.dataframe(outcome_data[["Week", "Value"]])
                                    else:
                                        st.write("No outcome data")
            
            elif plot_style == "Advanced Line Charts":
                # Direct plotting implementation for all categories in one chart
                
                # Create the figure
                fig = go.Figure()
                
                # Track if we added any data
                added_traces = False
                
                # Get color palette
                colors = px.colors.qualitative.Plotly
                
                # Process each category
                for i, category in enumerate(sorted(df["Category"].unique())):
                    # Get color for this category
                    color = colors[i % len(colors)]
                    
                    # Get data for this category
                    cat_data = df[df["Category"] == category]
                    
                    # Skip if no data
                    if cat_data.empty:
                        continue
                    
                    # Process goal data
                    goal_data = cat_data[cat_data["Type"] == "Mål"]
                    if not goal_data.empty:
                        # Sort by week
                        goal_data = goal_data.sort_values("Week")
                        
                        # Add trace
                        fig.add_trace(go.Scatter(
                            x=goal_data["Week"].tolist(),
                            y=goal_data["Value"].tolist(),
                            mode="lines+markers",
                            name=f"{category} (Mål)",
                            line=dict(color=color, dash="dash"),
                            marker=dict(size=6)
                        ))
                        added_traces = True
                    
                    # Process outcome data
                    outcome_data = cat_data[cat_data["Type"] == "Utfall"]
                    if not outcome_data.empty:
                        # Sort by week
                        outcome_data = outcome_data.sort_values("Week")
                        
                        # Add trace
                        fig.add_trace(go.Scatter(
                            x=outcome_data["Week"].tolist(),
                            y=outcome_data["Value"].tolist(),
                            mode="lines+markers",
                            name=f"{category} (Utfall)",
                            line=dict(color=color),
                            marker=dict(size=6, symbol="square")
                        ))
                        added_traces = True
                
                # If no traces were added, add a dummy trace
                if not added_traces:
                    fig.add_trace(go.Scatter(
                        x=[15, 26],
                        y=[0, 0],
                        mode="lines",
                        line=dict(color="rgba(0,0,0,0)"),
                        showlegend=False
                    ))
                    st.warning("No data available for visualization")
                
                # Update layout
                fig.update_layout(
                    title="All Categories Overview",
                    xaxis=dict(
                        title="Week",
                        tickmode="linear",
                        dtick=1,
                        range=[15-0.5, 26+0.5],
                        gridcolor="#444444"
                    ),
                    yaxis=dict(
                        title="Value",
                        gridcolor="#444444"
                    ),
                    plot_bgcolor="#262730",
                    paper_bgcolor="#262730",
                    font=dict(color="white"),
                    legend=dict(
                        bordercolor="white",
                        borderwidth=1,
                        font=dict(color="white")
                    ),
                    height=600
                )
                
                # Display a caption with the data counts
                goal_count = len(df[df["Type"] == "Mål"])
                outcome_count = len(df[df["Type"] == "Utfall"])
                st.caption(f"Advanced overview with {goal_count} goal data points and {outcome_count} outcome data points across {df['Category'].nunique()} categories")
                
                # Display the figure
                st.plotly_chart(fig, use_container_width=True)
            
            elif plot_style == "Category Groups":
                # Direct implementation of category groups using plotly
                
                # Process each group
                for group_name, categories in [
                    ("Financial Metrics", financial_filtered),
                    ("Productivity Metrics", productivity_filtered),
                    ("Content Metrics", content_filtered),
                    ("Other Metrics", other_categories) if other_categories else (None, [])
                ]:
                    if not categories:
                        continue
                        
                    st.write(f"### {group_name}")
                    
                    # Calculate grid layout
                    n_cats = len(categories)
                    n_cols = min(2, n_cats)
                    n_rows = (n_cats + n_cols - 1) // n_cols
                    
                    # Create subplots
                    fig = make_subplots(
                        rows=n_rows, 
                        cols=n_cols,
                        subplot_titles=categories,
                        vertical_spacing=0.1
                    )
                    
                    # Process each category
                    for i, category in enumerate(categories):
                        row = i // n_cols + 1
                        col = i % n_cols + 1
                        
                        # Get data for this category
                        cat_data = df[df["Category"] == category]
                        
                        # Skip if no data
                        if cat_data.empty:
                            continue
                        
                        # Check if this is a "lower is better" metric
                        is_lower_better = any(pattern in category.lower() for pattern in ["lägre", "mindre", "lower", "utgifter"])
                        
                        # Process goal data
                        goal_data = cat_data[cat_data["Type"] == "Mål"]
                        if not goal_data.empty:
                            # Sort by week
                            goal_data = goal_data.sort_values("Week")
                            
                            # Add trace
                            fig.add_trace(
                                go.Scatter(
                                    x=goal_data["Week"].tolist(),
                                    y=goal_data["Value"].tolist(),
                                    mode="lines+markers",
                                    name="Mål",
                                    line=dict(color="#00BFFF", dash="dash"),
                                    marker=dict(size=6),
                                    legendgroup="Mål",
                                    showlegend=i==0  # Only show legend for first category
                                ),
                                row=row, col=col
                            )
                            
                        # Process outcome data
                        outcome_data = cat_data[cat_data["Type"] == "Utfall"]
                        # Handle case where outcome data is empty but goals exist
                        if outcome_data.empty and not goal_data.empty:
                            # Create synthetic zeros for all weeks with goals
                            outcome_weeks = goal_data["Week"].unique()
                            
                            # Special case for Försäljning SEK eller högre - show all weeks 15-26
                            if category == "Försäljning SEK eller högre":
                                outcome_weeks = list(range(15, 27))  # Weeks 15-26
                            
                            outcome_x = outcome_weeks.tolist() if not isinstance(outcome_weeks, list) else outcome_weeks
                            outcome_y = [0] * len(outcome_weeks)
                        elif not outcome_data.empty:
                            # Sort by week
                            outcome_data = outcome_data.sort_values("Week")
                            
                            # Add trace
                            fig.add_trace(
                                go.Scatter(
                                    x=outcome_data["Week"].tolist(),
                                    y=outcome_data["Value"].tolist(),
                                    mode="lines+markers",
                                    name="Utfall",
                                    line=dict(color="#FF4B4B"),
                                    marker=dict(size=6),
                                    legendgroup="Utfall",
                                    showlegend=i==0  # Only show legend for first category
                                ),
                                row=row, col=col
                            )
                        
                        # Update axes
                        fig.update_xaxes(
                            title_text="Week",
                            row=row, col=col,
                            tickmode="linear",
                            dtick=2
                        )
                        
                        if is_lower_better and invert_metrics:
                            fig.update_yaxes(
                                title_text="Value",
                                autorange="reversed",
                                row=row, col=col
                            )
                        else:
                            fig.update_yaxes(
                                title_text="Value",
                                row=row, col=col
                            )
                    
                    # Update layout
                    fig.update_layout(
                        title=f"{group_name} Overview",
                        height=300 * n_rows,
                        showlegend=True,
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1
                        ),
                        plot_bgcolor="#262730",
                        paper_bgcolor="#262730",
                        font=dict(color="white")
                    )
                    
                    # Display the figure
                    st.plotly_chart(fig, use_container_width=True)
            
            elif plot_style == "Individual Metrics":
                # Direct implementation of individual metrics using plotly
                for category in sorted(df["Category"].unique()):
                    st.write(f"### {category}")
                    
                    # Get data for this category
                    cat_data = df[df["Category"] == category]
                    
                    # Skip if no data
                    if cat_data.empty:
                        st.warning(f"No data for {category}")
                        continue
                    
                    # Create figure
                    fig = go.Figure()
                    
                    # Check if this is a "lower is better" metric
                    is_lower_better = any(pattern in category.lower() for pattern in ["lägre", "mindre", "lower", "utgifter"])
                    
                    # Process goal data
                    goal_data = cat_data[cat_data["Type"] == "Mål"]
                    if not goal_data.empty:
                        # Sort by week
                        goal_data = goal_data.sort_values("Week")
                        
                        # Add trace
                        fig.add_trace(go.Scatter(
                            x=goal_data["Week"].tolist(),
                            y=goal_data["Value"].tolist(),
                            mode="lines+markers",
                            name="Mål",
                            line=dict(color="#00BFFF", dash="dash", width=2),
                            marker=dict(size=10, symbol="circle")
                        ))
                        
                        # Add labels
                        if show_values:
                            for i, row in goal_data.iterrows():
                                fig.add_annotation(
                                    x=row["Week"],
                                    y=row["Value"],
                                    text=str(int(row["Value"]) if row["Value"] == int(row["Value"]) else f"{row['Value']:.1f}"),
                                    showarrow=False,
                                    yshift=10,
                                    font=dict(color="#00BFFF"),
                                    bgcolor="rgba(0,0,0,0.6)",
                                    bordercolor="#00BFFF",
                                    borderwidth=1
                                )
                    
                    # Process outcome data
                    outcome_data = cat_data[cat_data["Type"] == "Utfall"]
                    # Handle case where outcome data is empty but goals exist
                    if outcome_data.empty and not goal_data.empty:
                        # Create synthetic zeros for all weeks with goals
                        outcome_weeks = goal_data["Week"].unique()
                        
                        # Special case for Försäljning SEK eller högre - show all weeks 15-26
                        if category == "Försäljning SEK eller högre":
                            outcome_weeks = list(range(15, 27))  # Weeks 15-26
                        
                        outcome_x = outcome_weeks.tolist() if not isinstance(outcome_weeks, list) else outcome_weeks
                        outcome_y = [0] * len(outcome_weeks)
                    elif not outcome_data.empty:
                        # Sort by week
                        outcome_data = outcome_data.sort_values("Week")
                        
                        # Add trace
                        fig.add_trace(go.Scatter(
                            x=outcome_data["Week"].tolist(),
                            y=outcome_data["Value"].tolist(),
                            mode="lines+markers",
                            name="Utfall",
                            line=dict(color="#FF4B4B", width=2),
                            marker=dict(size=10, symbol="circle")
                        ))
                        
                        # Add labels
                        if show_values:
                            for i, row in outcome_data.iterrows():
                                fig.add_annotation(
                                    x=row["Week"],
                                    y=row["Value"],
                                    text=str(int(row["Value"]) if row["Value"] == int(row["Value"]) else f"{row['Value']:.1f}"),
                                    showarrow=False,
                                    yshift=10,
                                    font=dict(color="#FF4B4B"),
                                    bgcolor="rgba(0,0,0,0.6)",
                                    bordercolor="#FF4B4B",
                                    borderwidth=1
                                )
                    
                    # Set axis ranges
                    all_weeks = []
                    if not goal_data.empty:
                        all_weeks.extend(goal_data["Week"].tolist())
                    if not outcome_data.empty:
                        all_weeks.extend(outcome_data["Week"].tolist())
                    
                    # Get week range
                    if all_weeks:
                        min_week = min(all_weeks)
                        max_week = max(all_weeks)
                        
                        # For Försäljning SEK eller högre, ensure we show the full range even if data is limited
                        if category == "Försäljning SEK eller högre":
                            if max_week - min_week < 10:  # If range is too small
                                min_week = 15
                                max_week = 26
                        
                        if week_range:
                            if week_range[0] <= max_week and week_range[1] >= min_week:
                                min_week = max(min_week, week_range[0])
                                max_week = min(max_week, week_range[1])
                    else:
                        # Default to weeks 15-26 if no data
                        min_week = 15
                        max_week = 26
                    
                    # Get y-axis range with padding
                    all_values = []
                    if not goal_data.empty:
                        all_values.extend(goal_data["Value"].tolist())
                    if not outcome_data.empty:
                        all_values.extend(outcome_data["Value"].tolist())
                        
                    if all_values:
                        min_val = min(all_values)
                        max_val = max(all_values)
                        # Add 20% padding to top and 10% to bottom
                        y_padding_top = (max_val - min_val) * 0.2
                        y_padding_bottom = (max_val - min_val) * 0.1
                        y_min = max(0, min_val - y_padding_bottom)  # Don't go below zero unless data is negative
                        y_max = max_val + y_padding_top
                        
                        # Special case for Försäljning SEK eller högre
                        if category == "Försäljning SEK eller högre":
                            y_max = max(7000, y_max)  # Ensure we can see 5000 comfortably
                    else:
                        y_min = 0
                        y_max = 100
                        
                        # Special case for Försäljning SEK eller högre
                        if category == "Försäljning SEK eller högre":
                            y_max = 7000  # Default max for sales
                    
                    # Update layout
                    fig.update_layout(
                        title=f"{category} Detail View",
                        xaxis=dict(
                            title="Week",
                            tickmode="linear",
                            dtick=1,
                            range=[min_week-0.5, max_week+0.5],
                            gridcolor="#444444"
                        ),
                        yaxis=dict(
                            title="Value" if not is_lower_better else "Value (lower is better)",
                            autorange="reversed" if is_lower_better and invert_metrics else None,
                            gridcolor="#444444",
                            range=[y_min, y_max] if not (is_lower_better and invert_metrics) else [y_max, y_min]
                        ),
                        plot_bgcolor="#262730",
                        paper_bgcolor="#262730",
                        font=dict(color="white"),
                        showlegend=True,
                        legend=dict(
                            x=0.01,
                            y=0.99,
                            bordercolor="white",
                            borderwidth=1,
                            font=dict(color="white")
                        ),
                        height=400
                    )
                    
                    # Display data counts
                    st.caption(f"Data points: Mål: {len(goal_data)}, Utfall: {len(outcome_data)}")
                    
                    # Display the figure
                    st.plotly_chart(fig, use_container_width=True)
            
            elif plot_style == "Raw Data":
                # Display raw data
                st.dataframe(df.sort_values(["Category", "Type", "Week"]), use_container_width=True)
        
        # Add a section for single category selection at the bottom
        if 'data' in st.session_state and selected_category != "All Categories":
            st.markdown("---")
            st.subheader(f"Detailed view for: {selected_category}")
            
            # Create individual category visualization with custom settings
            cat_visualizer = BalthazarVisualizer(df)
            cat_visualizer.colors = {
                "Mål": st.session_state.settings['graph_settings']['goal_color'],
                "Utfall": st.session_state.settings['graph_settings']['outcome_color']
            }
            
            # Get data for the selected category
            cat_df = df[df["Category"] == selected_category].copy()
            
            # Ensure this subset has Week column
            if "Week" not in cat_df.columns and "Date" in cat_df.columns:
                cat_df["Week"] = cat_df["Date"]
            
            # Check if this is a "lower is better" metric
            is_lower_better = any(pattern in selected_category.lower() for pattern in ["lägre", "mindre", "lower", "utgifter"])
            
            # Filter data but include zero values
            goals = cat_df[cat_df["Type"] == "Mål"].copy()
            goals = goals[(goals["Value"].notna())]
            
            outcomes = cat_df[cat_df["Type"] == "Utfall"].copy()
            outcomes = outcomes[(outcomes["Value"].notna())]
            
            # Convert to native types
            if not goals.empty:
                goals_x = [int(x) for x in goals["Week"].tolist()]
                goals_y = [float(y) for y in goals["Value"].tolist()]
            else:
                goals_x = []
                goals_y = []
                
            if not outcomes.empty:
                outcomes_x = [int(x) for x in outcomes["Week"].tolist()]
                outcomes_y = [float(y) for y in outcomes["Value"].tolist()]
            else:
                outcomes_x = []
                outcomes_y = []
                
                # If no outcomes but goals exist, create synthetic zeros
                if goals_x:
                    # Special case for Försäljning SEK eller högre - show all weeks 15-26
                    if selected_category == "Försäljning SEK eller högre":
                        outcomes_x = list(range(15, 27))  # Weeks 15-26
                    else:
                        outcomes_x = goals_x.copy()
                    
                    outcomes_y = [0] * len(outcomes_x)
            
            # Create Plotly figure for the selected category
            detail_fig = go.Figure()
            
            # Add goal trace (if we have data)
            if goals_x:
                detail_fig.add_trace(go.Scatter(
                    x=goals_x, 
                    y=goals_y,
                    mode='lines+markers',
                    name='Mål',
                    line=dict(color="#00BFFF", dash='dash', width=3),
                    marker=dict(size=10, symbol="circle")
                ))
                
            # Add outcome trace (if we have data)
            if outcomes_x:
                detail_fig.add_trace(go.Scatter(
                    x=outcomes_x, 
                    y=outcomes_y,
                    mode='lines+markers',
                    name='Utfall',
                    line=dict(color="#FF4B4B", width=3),
                    marker=dict(size=10, symbol="circle")
                ))
                
            # Get all weeks
            all_weeks = sorted(set(goals_x + outcomes_x))
            if all_weeks:
                # For Försäljning SEK eller högre, ensure we show the full range even if data is limited
                if selected_category == "Försäljning SEK eller högre":
                    min_week = 15
                    max_week = 26
                else:
                    min_week = min(all_weeks)
                    max_week = max(all_weeks)
                
                # Calculate y-axis range with padding
                all_values = goals_y + outcomes_y
                if all_values:
                    min_val = min(all_values)
                    max_val = max(all_values)
                    # Add 20% padding to top and 10% to bottom
                    y_padding_top = (max_val - min_val) * 0.2 if max_val > min_val else max_val * 0.2
                    y_padding_bottom = (max_val - min_val) * 0.1 if max_val > min_val else max_val * 0.1
                    y_min = max(0, min_val - y_padding_bottom)  # Don't go below zero unless data is negative
                    y_max = max_val + y_padding_top
                    
                    # Special case for Försäljning SEK eller högre
                    if selected_category == "Försäljning SEK eller högre":
                        y_max = max(7000, y_max)  # Ensure we can see 5000 comfortably
                else:
                    y_min = 0
                    y_max = 100
                    
                    # Special case for Försäljning SEK eller högre
                    if selected_category == "Försäljning SEK eller högre":
                        y_max = 7000  # Default max for sales
                
                # Update layout
                detail_fig.update_layout(
                    title=f"{selected_category} Detail View",
                    xaxis_title="Week",
                    yaxis_title="Value" if not is_lower_better else "Value (lower is better)",
                    paper_bgcolor="#262730",
                    plot_bgcolor="#262730",
                    font=dict(color="white", size=14),
                    height=500,
                    legend=dict(
                        font=dict(color="white"),
                        bgcolor="#262730"
                    ),
                    xaxis=dict(
                        gridcolor="#444", 
                        range=[min_week-0.5, max_week+0.5],
                        dtick=1,
                        tickmode="linear",
                        title_font=dict(size=14)
                    ),
                    yaxis=dict(
                        gridcolor="#444", 
                        autorange="reversed" if is_lower_better and invert_metrics else None,
                        zeroline=True,
                        zerolinecolor="#888",
                        zerolinewidth=1,
                        title_font=dict(size=14),
                        range=[y_min, y_max] if not (is_lower_better and invert_metrics) else [y_max, y_min]
                    )
                )
                
                st.plotly_chart(detail_fig, use_container_width=True)
            else:
                st.warning(f"No data available for {selected_category}")

        # Debug the data processing
        with st.expander("Debug Data Processing", expanded=False):
            st.write("### Debug: Data Conversion Process")
            
            # Create a copy for debug display
            debug_df = df.copy()
            st.write(f"Original data types: {debug_df.dtypes}")
            
            # Display conversion details
            if "Date" in debug_df.columns:
                st.write("Date column before conversion:")
                st.write(debug_df["Date"].head(10))
                
                # Try to convert
                try:
                    debug_df["Date"] = pd.to_numeric(debug_df["Date"], errors="coerce")
                    st.write("Date column after conversion:")
                    st.write(debug_df["Date"].head(10))
                except Exception as e:
                    st.write(f"Error converting Date: {str(e)}")
            
            # Show Week column
            if "Week" in debug_df.columns:
                st.write("Week column:")
                st.write(debug_df["Week"].head(10))
            
            # For Försäljning SEK eller högre
            sales_data = debug_df[debug_df["Category"] == "Försäljning SEK eller högre"].copy()
            st.write(f"Försäljning SEK eller högre data points: {len(sales_data)}")
            if not sales_data.empty:
                st.dataframe(sales_data)
            else:
                st.write("No sales data found")

        # Visualize the data
        with st.container():
            # Special handling for Försäljning SEK eller högre
            if selected_category == "Försäljning SEK eller högre":
                st.markdown("""
                <div style="background-color: #262730; border-radius: 8px; padding: 15px; margin-bottom: 20px;">
                    <h3 style="color: white;">Försäljning SEK eller högre - Visualization Notes</h3>
                    <ul style="color: white;">
                        <li>This chart is configured to always show the full week range (15-26).</li>
                        <li>Y-axis maximum is set to at least 7000 to properly display the 5000 SEK goal.</li>
                        <li>If no outcome data exists, a zero line will be displayed.</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)

else:
    # Instructions when no data is loaded
    st.info("Upload your Google API credentials and click 'Fetch Data' to start.")
    
    # Only show essential instructions
    st.markdown("""
    This dashboard will display:
    1. 💰 **Financial Metrics** (Sales, Expenses)
    2. 📋 **Productivity Metrics** (Meetings, Git Commits, etc.)
    3. 🎬 **Content Metrics** (YouTube Videos)
    
    Each category will show Goals ("Mål") vs. Outcomes ("Utfall").
    """)

# Footer
st.markdown("---")
st.caption("The Balthazar Project Dashboard © 2023") 