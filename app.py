import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt
from gsheet_connector import BalthazarGSheetConnector
from dashboard_visualizer import BalthazarVisualizer
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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
                save_success = st.session_state.visualizer.save_to_browser(date_range)
                config_success = st.session_state.visualizer.save_config(config)
                
                if save_success and config_success:
                    status.update(label="✅ Data fetched and saved successfully!", state="complete")
                else:
                    status.update(label="⚠️ Data fetched but couldn't be saved completely", state="error")
                
                # Output the structure of the processed data for debugging
                st.write("---")
                st.subheader("Data Structure")
                st.write(f"Categories: {sorted(processed_data['Category'].unique())}")
                st.write(f"Types: {sorted(processed_data['Type'].unique())}")
                st.write(f"Weeks: {sorted(processed_data['Date'].unique())}")
                st.write("---")
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
    df = st.session_state.data
    
    # Validate that data has the required format
    required_columns = ["Date", "Category", "Type", "Value"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        st.error(f"Data is missing required columns: {', '.join(missing_columns)}")
    else:
        # Convert the data to numeric where appropriate
        df["Value"] = pd.to_numeric(df["Value"], errors="coerce")
        df["Date"] = pd.to_numeric(df["Date"], errors="coerce")
        
        # Ensure we have a Week column for visualization
        if "Week" not in df.columns:
            df["Week"] = df["Date"]
        
        # Drop any rows with NaN values
        orig_len = len(df)
        df = df.dropna(subset=["Value", "Date"])
        if len(df) < orig_len:
            st.warning(f"Dropped {orig_len - len(df)} rows with invalid values.")
        
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
            st.metric("Days/Weeks Tracked", days)
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Add visualization settings
        st.subheader("Visualization Settings")
        display_cols = st.columns([2, 1, 1])
        
        with display_cols[0]:
            plot_style = st.selectbox(
                "Select Plot Style",
                ["Simple Line Charts", "Advanced Line Charts", "Gauge Charts", "Comparison Charts"],
                help="Choose how metrics are displayed"
            )
        
        with display_cols[1]:
            show_values = st.checkbox("Show Values on Points", value=True)
        
        with display_cols[2]:
            invert_metrics = st.checkbox("Auto-Invert Lower-Better Metrics", value=True)
        
        # Create tabs for different views
        tab1, tab2, tab3 = st.tabs(["Category Groups 📊", "Individual Metrics 📈", "Raw Data 📋"])
        
        with tab1:
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
            
            # Get selected week range
            week_range = getattr(st.session_state, 'week_range', None)
            if week_range:
                min_week, max_week = week_range
            else:
                min_week, max_week = 1, 52
                
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
                            # Create a direct custom plot for each category
                            cat_df = df[df["Category"] == category].copy()
                            
                            # Ensure this subset has Week column
                            if "Week" not in cat_df.columns and "Date" in cat_df.columns:
                                cat_df["Week"] = cat_df["Date"]
                            
                            # Filter relevant data
                            goals = cat_df[cat_df["Type"] == "Mål"].copy()
                            goals = goals[(goals["Value"].notna()) & (goals["Value"] != 0)]
                            
                            outcomes = cat_df[cat_df["Type"] == "Utfall"].copy()
                            outcomes = outcomes[(outcomes["Value"].notna()) & (outcomes["Value"] != 0)]
                            
                            # Get the weeks
                            all_weeks = sorted(set(goals["Week"].tolist() + outcomes["Week"].tolist()))
                            
                            if all_weeks:
                                # Filter for selected week range
                                if week_range:
                                    goals = goals[(goals["Week"] >= min_week) & (goals["Week"] <= max_week)]
                                    outcomes = outcomes[(outcomes["Week"] >= min_week) & (outcomes["Week"] <= max_week)]
                                
                                # Create figure
                                fig = go.Figure()
                                
                                # Add traces
                                if not goals.empty:
                                    fig.add_trace(go.Scatter(
                                        x=goals["Week"], y=goals["Value"],
                                        mode='lines+markers',
                                        name='Mål',
                                        line=dict(color=visualizer.colors["Mål"], dash='dash'),
                                        marker=dict(size=8)
                                    ))
                                    
                                if not outcomes.empty:
                                    fig.add_trace(go.Scatter(
                                        x=outcomes["Week"], y=outcomes["Value"],
                                        mode='lines+markers',
                                        name='Utfall',
                                        line=dict(color=visualizer.colors["Utfall"]),
                                        marker=dict(size=8)
                                    ))
                                    
                                # Add values on points if requested
                                if show_values:
                                    if not goals.empty:
                                        for x, y in zip(goals["Week"], goals["Value"]):
                                            fig.add_annotation(
                                                x=x, y=y,
                                                text=f"{y}",
                                                showarrow=False,
                                                yshift=10,
                                                font=dict(color=visualizer.colors["Mål"]),
                                                bgcolor="rgba(255,255,255,0.7)"
                                            )
                                    
                                    if not outcomes.empty:
                                        for x, y in zip(outcomes["Week"], outcomes["Value"]):
                                            fig.add_annotation(
                                                x=x, y=y,
                                                text=f"{y}",
                                                showarrow=False,
                                                yshift=10,
                                                font=dict(color=visualizer.colors["Utfall"]),
                                                bgcolor="rgba(255,255,255,0.7)"
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
                                    font=dict(color="white"),
                                    height=400,
                                    legend=dict(
                                        font=dict(color="white"),
                                        bgcolor="#262730"
                                    ),
                                    xaxis=dict(
                                        gridcolor="#444", 
                                        range=[min_week-0.5, max_week+0.5],
                                        dtick=1,
                                        tickmode="linear"
                                    ),
                                    yaxis=dict(
                                        gridcolor="#444", 
                                        autorange="reversed" if is_lower_better and invert_metrics else None,
                                        zeroline=True,
                                        zerolinecolor="#888",
                                        zerolinewidth=1
                                    )
                                )
                                
                                st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.warning(f"No data for {category}")
                                
            elif plot_style == "Advanced Line Charts":
                # Create advanced line charts using plotly
                category_plots = visualizer.create_category_plots()
                for plot in category_plots:
                    st.plotly_chart(plot, use_container_width=True)
            
            elif plot_style == "Gauge Charts":
                # Display metrics as gauge charts
                metrics_display = visualizer.create_metrics_display()
                st.plotly_chart(metrics_display, use_container_width=True)
            
            elif plot_style == "Comparison Charts":
                # Display comparison charts with achievement percentages
                comparison_plots = visualizer.create_comparison_plots()
                for plot in comparison_plots:
                    st.plotly_chart(plot, use_container_width=True)
        
        with tab2:
            if 'selected_category' in locals() and selected_category != "All Categories":
                # Add chart type selector for individual metrics
                chart_type = st.radio(
                    "Chart Type", 
                    ["Line Chart", "Bar Chart", "Area Chart", "Combo Chart"],
                    horizontal=True
                )
                
                # Create individual category visualization with custom settings
                visualizer = BalthazarVisualizer(df)
                visualizer.colors = {
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
                
                # Filter data to remove empty or zero values
                goals = cat_df[cat_df["Type"] == "Mål"].copy()
                goals = goals[(goals["Value"].notna()) & (goals["Value"] != 0)]
                
                outcomes = cat_df[cat_df["Type"] == "Utfall"].copy()
                outcomes = outcomes[(outcomes["Value"].notna()) & (outcomes["Value"] != 0)]
                
                # Get week range
                all_weeks = sorted(set(goals["Week"].tolist() + outcomes["Week"].tolist()))
                
                if not all_weeks:
                    st.warning(f"No valid data found for {selected_category}")
                else:
                    # Create plot based on selected chart type
                    fig = go.Figure()
                    
                    if chart_type == "Line Chart":
                        if not goals.empty:
                            fig.add_trace(go.Scatter(
                                x=goals["Week"], y=goals["Value"],
                                mode='lines+markers',
                                name='Mål',
                                line=dict(color=visualizer.colors["Mål"], dash='dash'),
                                marker=dict(size=10)
                            ))
                            
                        if not outcomes.empty:
                            fig.add_trace(go.Scatter(
                                x=outcomes["Week"], y=outcomes["Value"],
                                mode='lines+markers',
                                name='Utfall',
                                line=dict(color=visualizer.colors["Utfall"]),
                                marker=dict(size=10)
                            ))
                            
                    elif chart_type == "Bar Chart":
                        if not goals.empty:
                            fig.add_trace(go.Bar(
                                x=goals["Week"], y=goals["Value"],
                                name='Mål',
                                marker_color=visualizer.colors["Mål"]
                            ))
                            
                        if not outcomes.empty:
                            fig.add_trace(go.Bar(
                                x=outcomes["Week"], y=outcomes["Value"],
                                name='Utfall',
                                marker_color=visualizer.colors["Utfall"]
                            ))
                        
                    elif chart_type == "Area Chart":
                        if not goals.empty:
                            fig.add_trace(go.Scatter(
                                x=goals["Week"], y=goals["Value"],
                                mode='lines',
                                name='Mål',
                                line=dict(color=visualizer.colors["Mål"]),
                                fill='tozeroy'
                            ))
                            
                        if not outcomes.empty:
                            fig.add_trace(go.Scatter(
                                x=outcomes["Week"], y=outcomes["Value"],
                                mode='lines',
                                name='Utfall',
                                line=dict(color=visualizer.colors["Utfall"]),
                                fill='tozeroy'
                            ))
                        
                    elif chart_type == "Combo Chart":
                        if not goals.empty:
                            fig.add_trace(go.Bar(
                                x=goals["Week"], y=goals["Value"],
                                name='Mål',
                                marker_color=visualizer.colors["Mål"],
                                opacity=0.7
                            ))
                            
                        if not outcomes.empty:
                            fig.add_trace(go.Scatter(
                                x=outcomes["Week"], y=outcomes["Value"],
                                mode='lines+markers',
                                name='Utfall',
                                line=dict(color=visualizer.colors["Utfall"]),
                                marker=dict(size=10)
                            ))
                    
                    # Add data labels if requested
                    if show_values:
                        if not goals.empty:
                            for x, y in zip(goals["Week"], goals["Value"]):
                                fig.add_annotation(
                                    x=x, y=y,
                                    text=f"{y}",
                                    showarrow=False,
                                    yshift=10,
                                    font=dict(color=visualizer.colors["Mål"]),
                                    bgcolor="rgba(255,255,255,0.7)"
                                )
                        
                        if not outcomes.empty:
                            for x, y in zip(outcomes["Week"], outcomes["Value"]):
                                fig.add_annotation(
                                    x=x, y=y,
                                    text=f"{y}",
                                    showarrow=False,
                                    yshift=10,
                                    font=dict(color=visualizer.colors["Utfall"]),
                                    bgcolor="rgba(255,255,255,0.7)"
                                )
                    
                    # Find min and max for weeks to properly set the x-axis range
                    min_week = min(all_weeks) if all_weeks else 1
                    max_week = max(all_weeks) if all_weeks else 52
                    
                    # Update layout
                    fig.update_layout(
                        title=f"{selected_category}: Mål vs. Utfall",
                        xaxis_title="Week",
                        yaxis_title="Value" if not is_lower_better else "Value (lower is better)",
                        paper_bgcolor="#262730",
                        plot_bgcolor="#262730",
                        font=dict(color="white"),
                        legend=dict(
                            font=dict(color="white"),
                            bgcolor="#262730"
                        ),
                        xaxis=dict(
                            gridcolor="#444", 
                            range=[min_week-0.5, max_week+0.5],
                            dtick=1,  # Show every integer tick
                            tickmode="linear"
                        ),
                        yaxis=dict(
                            gridcolor="#444", 
                            autorange="reversed" if is_lower_better and invert_metrics else None,
                            zeroline=True,
                            zerolinecolor="#888",
                            zerolinewidth=1
                        )
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
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