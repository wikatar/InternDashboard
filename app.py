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
                        status.update(label="✅ Data fetched but config couldn't be saved", state="warning")
                    elif config_success:
                        status.update(label="✅ Data fetched but couldn't be saved to browser", state="warning")
                    else:
                        status.update(label="✅ Data fetched but nothing could be saved", state="warning")
                except Exception as e:
                    status.update(label=f"✅ Data fetched but error saving: {str(e)}", state="warning")
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
                    
                for group_name, categories in all_groups:
                    if not categories:
                        continue
                        
                    with st.expander(group_name, expanded=True):
                        for i, category in enumerate(categories):
                            # Create a direct custom plot for each category - IMPROVED CODE
                            cat_df = df[df["Category"] == category].copy()
                            
                            # Skip if no data
                            if cat_df.empty:
                                st.warning(f"No data found for category: {category}")
                                continue
                                
                            # Ensure this subset has Week column
                            if "Week" not in cat_df.columns and "Date" in cat_df.columns:
                                cat_df["Week"] = cat_df["Date"]
                            
                            # Convert to numeric if needed
                            cat_df["Value"] = pd.to_numeric(cat_df["Value"], errors="coerce")
                            cat_df["Week"] = pd.to_numeric(cat_df["Week"], errors="coerce")
                            
                            # Filter relevant data - include all rows with valid data including zeros
                            goals = cat_df[cat_df["Type"] == "Mål"].copy()
                            goals = goals[(goals["Value"].notna()) & (goals["Week"].notna())]
                            
                            outcomes = cat_df[cat_df["Type"] == "Utfall"].copy()
                            outcomes = outcomes[(outcomes["Value"].notna()) & (outcomes["Week"].notna())]
                            
                            # Show debug info directly (not in an expander to avoid nesting)
                            st.caption(f"**Debug info:** Mål: {len(goals)} points, Utfall: {len(outcomes)} points")
                            
                            # Convert to native Python types to avoid PyArrow conversion issues
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
                            
                            # Get the weeks
                            goal_weeks = goals_x
                            outcome_weeks = outcomes_x
                            all_weeks = sorted(set(goal_weeks + outcome_weeks))
                            
                            if all_weeks:
                                # Filter for selected week range
                                if week_range:
                                    min_week, max_week = week_range
                                else:
                                    # Default to the weeks available in the data
                                    min_week = min(all_weeks)
                                    max_week = max(all_weeks)
                                
                                # Create figure
                                fig = go.Figure()
                                
                                # Add goal trace (if we have data)
                                if goals_x:
                                    fig.add_trace(go.Scatter(
                                        x=goals_x, 
                                        y=goals_y,
                                        mode='lines+markers',
                                        name='Mål',
                                        line=dict(color="#00BFFF", dash='dash', width=3),
                                        marker=dict(size=10, symbol="circle")
                                    ))
                                    
                                # Add outcome trace (if we have data)
                                if outcomes_x:
                                    fig.add_trace(go.Scatter(
                                        x=outcomes_x, 
                                        y=outcomes_y,
                                        mode='lines+markers',
                                        name='Utfall',
                                        line=dict(color="#FF4B4B", width=3),
                                        marker=dict(size=10, symbol="circle")
                                    ))
                                    
                                    # Add values on points if requested
                                    if show_values:
                                        if goals_x:
                                            for x, y in zip(goals_x, goals_y):
                                                fig.add_annotation(
                                                    x=x, y=y,
                                                    text=f"{int(y) if y == int(y) else y:.1f}",
                                                    showarrow=False,
                                                    yshift=15,
                                                    font=dict(color="#00BFFF", size=14),
                                                    bgcolor="rgba(0,0,0,0.5)",
                                                    bordercolor="#00BFFF",
                                                    borderwidth=1,
                                                    borderpad=3
                                                )
                                            
                                            if outcomes_x:
                                                for x, y in zip(outcomes_x, outcomes_y):
                                                    fig.add_annotation(
                                                        x=x, y=y,
                                                        text=f"{int(y) if y == int(y) else y:.1f}",
                                                        showarrow=False,
                                                        yshift=15,
                                                        font=dict(color="#FF4B4B", size=14),
                                                        bgcolor="rgba(0,0,0,0.5)",
                                                        bordercolor="#FF4B4B",
                                                        borderwidth=1,
                                                        borderpad=3
                                                    )
                                
                                # Check if this is a "lower is better" metric
                                is_lower_better = any(pattern in category.lower() for pattern in ["lägre", "mindre", "lower", "utgifter"])
                                
                                # Update layout
                                fig.update_layout(
                                    title=f"{category}",
                                    xaxis_title="Week",
                                    yaxis_title="Value" if not is_lower_better else "Value (lower is better)",
                                    paper_bgcolor="#262730",
                                    plot_bgcolor="#262730",
                                    font=dict(color="white", size=14),
                                    height=400,
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
                                        title_font=dict(size=14)
                                    )
                                )
                                
                                # Display the chart
                                st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.warning(f"No numeric data for {category}")
            
            elif plot_style == "Advanced Line Charts":
                # Create single multi-line chart with all categories
                fig = go.Figure()
                
                all_categories = sorted(df["Category"].unique())
                colors = px.colors.qualitative.Plotly
                
                for i, category in enumerate(all_categories):
                    cat_df = df[df["Category"] == category].copy()
                    
                    # Get color index with wraparound
                    color_idx = i % len(colors)
                    
                    # Plot goals for this category
                    goals = cat_df[cat_df["Type"] == "Mål"].dropna(subset=["Value"])
                    if not goals.empty:
                        # Convert to native types
                        goals_x = [int(x) for x in goals["Week"].tolist()]
                        goals_y = [float(y) for y in goals["Value"].tolist()]
                        
                        fig.add_trace(go.Scatter(
                            x=goals_x,
                            y=goals_y,
                            mode='markers+lines',
                            name=f"{category} (Mål)",
                            line=dict(color=colors[color_idx], dash='dot'),
                            marker=dict(symbol='circle')
                        ))
                    
                    # Plot outcomes for this category
                    outcomes = cat_df[cat_df["Type"] == "Utfall"].dropna(subset=["Value"])
                    if not outcomes.empty:
                        # Convert to native types
                        outcomes_x = [int(x) for x in outcomes["Week"].tolist()]
                        outcomes_y = [float(y) for y in outcomes["Value"].tolist()]
                        
                        fig.add_trace(go.Scatter(
                            x=outcomes_x,
                            y=outcomes_y,
                            mode='markers+lines',
                            name=f"{category} (Utfall)",
                            line=dict(color=colors[color_idx]),
                            marker=dict(symbol='square')
                        ))
                
                # Update layout
                fig.update_layout(
                    title="All Metrics Overview",
                    xaxis_title="Week",
                    yaxis_title="Value",
                    paper_bgcolor="#262730",
                    plot_bgcolor="#262730",
                    font=dict(color="white"),
                    legend=dict(
                        font=dict(color="white"),
                        bgcolor="#262730"
                    )
                )
                
                # Display the chart
                st.plotly_chart(fig, use_container_width=True)
            
            elif plot_style == "Category Groups":
                # Display categories using the visualizer's group plots function
                if financial_filtered:
                    st.write("### Financial Metrics")
                    fig = visualizer.create_category_group_plots(financial_filtered, "Financial Metrics", 
                                                           figsize=st.session_state.settings['graph_settings']['figsize'],
                                                           x_range=week_range)
                    st.pyplot(fig)
                
                if productivity_filtered:
                    st.write("### Productivity Metrics")
                    fig = visualizer.create_category_group_plots(productivity_filtered, "Productivity Metrics", 
                                                           figsize=st.session_state.settings['graph_settings']['figsize'],
                                                           x_range=week_range)
                    st.pyplot(fig)
                
                if content_filtered:
                    st.write("### Content Metrics")
                    fig = visualizer.create_category_group_plots(content_filtered, "Content Metrics", 
                                                           figsize=st.session_state.settings['graph_settings']['figsize'],
                                                           x_range=week_range)
                    st.pyplot(fig)
                    
                if other_categories:
                    st.write("### Other Metrics")
                    fig = visualizer.create_category_group_plots(other_categories, "Other Metrics", 
                                                           figsize=st.session_state.settings['graph_settings']['figsize'],
                                                           x_range=week_range)
                    st.pyplot(fig)
            
            elif plot_style == "Individual Metrics":
                # Display each category individually
                for category in sorted(df["Category"].unique()):
                    st.write(f"### {category}")
                    fig = visualizer.create_metric_comparison(category, 
                                                       figsize=st.session_state.settings['graph_settings']['figsize'],
                                                       x_range=week_range)
                    st.pyplot(fig)
            
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
                # Update layout
                min_week = min(all_weeks)
                max_week = max(all_weeks)
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
                        title_font=dict(size=14)
                    )
                )
                
                st.plotly_chart(detail_fig, use_container_width=True)
            else:
                st.warning(f"No data available for {selected_category}")

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