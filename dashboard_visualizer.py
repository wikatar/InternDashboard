import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure
import numpy as np
from browser_storage import BrowserStorage

class BalthazarVisualizer:
    def __init__(self, data):
        """Initialize visualizer with data."""
        self.data = data
        self.storage = BrowserStorage()
        self.metrics = self._get_metrics() if data is not None else []
        self.categories = self._get_categories() if data is not None else []
        
        # Set Seaborn style for dark theme
        sns.set_theme(style="darkgrid")
        
        # Default settings
        self.default_figsize = (10, 6)
        self.show_markers = True
        self.show_grid = True
        self.colors = {
            "Mål": "#00BFFF",  # Deep Sky Blue for goals
            "Utfall": "#FF4B4B"  # Red for outcomes
        }
        
        # Set darker figure style
        plt.rcParams.update({
            'figure.facecolor': '#0E1117',
            'axes.facecolor': '#262730',
            'axes.edgecolor': '#666666',
            'axes.labelcolor': '#FAFAFA',
            'axes.titlecolor': '#FFFFFF',
            'xtick.color': '#FAFAFA',
            'ytick.color': '#FAFAFA',
            'grid.color': '#444444',
            'text.color': '#FAFAFA',
            'legend.frameon': True,
            'legend.facecolor': '#262730',
            'legend.edgecolor': '#666666',
            'legend.fontsize': 10,
            'legend.title_fontsize': 12
        })
        
    def _get_metrics(self):
        """
        Extract unique metrics from data.
        
        Returns:
            List of unique metric names
        """
        if self.data is None or len(self.data) == 0:
            return []
        return sorted(self.data["Category"].unique().tolist())
        
    def _get_categories(self):
        """
        Extract unique categories from data.
        
        Returns:
            List of unique category names
        """
        if self.data is None or len(self.data) == 0:
            return []
        
        # Group categories
        financial = ["Försäljning SEK eller högre", "Utgifter SEK eller lägre", "Resultat SEK"]
        
        productivity = [
            "Bokade möten", "Git commits", "Artiklar Hemsida (SEO)",
            "Gratis verktyg hemsida (SEO)", "Skickade E-post", 
            "Färdiga moment produktion"
        ]
        
        content = ["Långa YT videos", "Korta YT videos"]
        
        all_categories = []
        
        # Only include categories that exist in the data
        data_categories = set(self.data["Category"].unique())
        
        for category in financial + productivity + content:
            if category in data_categories:
                all_categories.append(category)
                
        # Add any categories not in predefined groups
        for category in data_categories:
            if category not in all_categories:
                all_categories.append(category)
                
        return all_categories
        
    def prepare_data(self):
        """Prepare data for visualization by adding Week column and sorting."""
        if self.data is None or self.data.empty:
            print("Data is None or empty, skipping preparation.")
            return
            
        try:
            # Ensure Date is an integer
            if "Date" not in self.data.columns:
                print("Warning: 'Date' column not found in data.")
                return
                
            self.data["Date"] = pd.to_numeric(self.data["Date"], errors="coerce")
            
            # Date from the Google Sheet should already be the week number (between 1-53)
            # Just ensure it's called "Week" for consistency in the rest of the code
            self.data["Week"] = self.data["Date"]
            
            # Sort by Week and Type to ensure consistent plotting
            if "Type" in self.data.columns:
                self.data = self.data.sort_values(["Week", "Type"])
            else:
                print("Warning: 'Type' column not found, sorting only by Week.")
                self.data = self.data.sort_values(["Week"])
            
            # Drop any rows with NaN week values
            self.data = self.data.dropna(subset=["Week"])
            
            # Print data summary for debugging
            print(f"Prepared data with {len(self.data)} rows")
            print(f"Week values: {sorted(self.data['Week'].unique())}")
            if "Category" in self.data.columns:
                print(f"Categories: {sorted(self.data['Category'].unique())}")
            if "Type" in self.data.columns:
                print(f"Types: {sorted(self.data['Type'].unique())}")
        except Exception as e:
            print(f"Error preparing data: {str(e)}")
        
    def create_metric_comparison(self, category, figsize=None, x_range=None):
        """
        Create a comparison plot of goals vs. outcomes for a specific category.
        
        Args:
            category: Category name to plot
            figsize: Figure size tuple (width, height)
            x_range: Tuple of (start_week, end_week) for x-axis range
            
        Returns:
            matplotlib Figure object
        """
        self.prepare_data()
        
        if figsize is None:
            figsize = self.default_figsize
            
        fig, ax = plt.subplots(figsize=figsize)
        
        # Filter data for the given category
        cat_df = self.data[self.data["Category"] == category].copy()
        
        if cat_df.empty:
            ax.text(0.5, 0.5, f"No data for {category}", ha="center", va="center", color="#FAFAFA")
            return fig
            
        # Get all weeks in the data
        all_weeks = sorted(cat_df["Week"].unique())
        
        # Set x-axis range if specified
        if x_range and len(x_range) == 2:
            start_week, end_week = x_range
            # Generate a complete list of weeks in the range
            weeks = list(range(start_week, end_week + 1))
            # Filter data to only include weeks in the range
            cat_df = cat_df[(cat_df["Week"] >= start_week) & (cat_df["Week"] <= end_week)]
        else:
            # Use all available weeks
            min_week = int(cat_df["Week"].min())
            max_week = int(cat_df["Week"].max())
            weeks = list(range(min_week, max_week + 1))
        
        # Check if this is a "lower is better" metric
        is_lower_better = any(pattern in category.lower() for pattern in ["lägre", "mindre", "lower", "utgifter"])
        
        # Filter non-NA values for goals
        goal_df = cat_df[cat_df["Type"] == "Mål"].dropna(subset=["Value"])
        # Filter non-NA values for outcomes
        outcome_df = cat_df[cat_df["Type"] == "Utfall"].dropna(subset=["Value"])
        
        # Plot goals (dotted line)
        if not goal_df.empty:
            ax.plot(
                goal_df["Week"],
                goal_df["Value"],
                color=self.colors["Mål"],
                linestyle=":",
                marker="o" if self.show_markers else None,
                label="Mål",
                drawstyle='steps-post'  # Use steps-post to avoid ghosting
            )
            
        # Plot outcomes (solid line)
        if not outcome_df.empty:
            ax.plot(
                outcome_df["Week"],
                outcome_df["Value"],
                color=self.colors["Utfall"],
                linestyle="-",
                marker="o" if self.show_markers else None,
                label="Utfall",
                drawstyle='steps-post'  # Use steps-post to avoid ghosting
            )
        
        # Set plot title and labels
        ax.set_title(f"{category}: Mål vs. Utfall", color="#FFFFFF", fontsize=14)
        ax.set_xlabel("Week", color="#FAFAFA")
        
        # If it's a "lower is better" metric, invert the y-axis
        if is_lower_better:
            ax.invert_yaxis()
            # Set y-axis label to indicate inversion
            ax.set_ylabel("Value (lower is better)", color="#FAFAFA")
        else:
            ax.set_ylabel("Value", color="#FAFAFA")
            
        # Format x-axis to only show the weeks that are available
        if weeks:
            ax.set_xticks(weeks)
            ax.set_xticklabels([f"Week {w}" for w in weeks])
            
            # Set x-axis limits to ensure all weeks are shown
            ax.set_xlim(min(weeks) - 0.5, max(weeks) + 0.5)
            
        # Add data point annotations
        for df, label in [(goal_df, "Mål"), (outcome_df, "Utfall")]:
            if not df.empty:
                for x, y in zip(df["Week"], df["Value"]):
                    ax.annotate(
                        f"{y:.0f}",
                        (x, y),
                        textcoords="offset points",
                        xytext=(0, 10),
                        ha='center',
                        color=self.colors[label],
                        fontweight='bold'
                    )
            
        # Add legend
        ax.legend(title="", frameon=True, facecolor="#262730", edgecolor="#666666")
        
        # Add grid if enabled
        if self.show_grid:
            ax.grid(True, linestyle="--", alpha=0.7, color="#444444")
        
        # Tight layout
        fig.tight_layout()
        
        return fig
        
    def create_category_group_plots(self, categories, group_name, figsize=None, x_range=None):
        """
        Create a multi-plot figure with comparisons for a group of categories.
        
        Args:
            categories: List of category names to include
            group_name: Name of the category group
            figsize: Figure size tuple (width, height)
            x_range: Tuple of (start_week, end_week) for x-axis range
            
        Returns:
            matplotlib Figure object
        """
        self.prepare_data()
        
        if figsize is None:
            figsize = self.default_figsize
            
        # Calculate grid size based on number of categories
        n_cats = len(categories)
        if n_cats == 0:
            # Return empty figure if no categories
            fig, ax = plt.subplots(figsize=figsize)
            ax.text(0.5, 0.5, f"No data for {group_name}", ha="center", va="center", color="#FAFAFA")
            fig.suptitle(f"{group_name}", fontsize=16, color="#FFFFFF")
            return fig
            
        n_cols = min(2, n_cats)
        n_rows = (n_cats + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize)
        fig.suptitle(f"{group_name}", fontsize=16, color="#FFFFFF")
        
        # Flatten axes array for easier indexing
        if n_cats > 1:
            axes = axes.flatten()
        else:
            axes = [axes]
        
        for i, category in enumerate(categories):
            if i < len(axes):
                # Filter data for the given category
                cat_df = self.data[self.data["Category"] == category].copy()
                
                if cat_df.empty:
                    axes[i].text(0.5, 0.5, f"No data for {category}", ha="center", va="center", color="#FAFAFA")
                    axes[i].set_title(category, color="#FFFFFF")
                    continue
                
                # Check if x_range is specified
                if x_range and len(x_range) == 2:
                    start_week, end_week = x_range
                    # Generate a complete list of weeks in the range
                    weeks = list(range(start_week, end_week + 1))
                    # Filter data to only include weeks in the range
                    filtered_df = cat_df[(cat_df["Week"] >= start_week) & (cat_df["Week"] <= end_week)]
                    if not filtered_df.empty:
                        cat_df = filtered_df
                    else:
                        # If no data in range, notify user but still plot all data
                        axes[i].text(0.5, 0.9, f"No data in selected week range", 
                                    ha="center", va="center", color="yellow", fontsize=8)
                else:
                    # Use all available weeks
                    min_week = int(cat_df["Week"].min())
                    max_week = int(cat_df["Week"].max())
                    weeks = list(range(min_week, max_week + 1))
                
                # Check if this is a "lower is better" metric
                is_lower_better = any(pattern in category.lower() for pattern in ["lägre", "mindre", "lower", "utgifter"])
                
                # Filter non-NA values for goals and outcomes
                goals = cat_df[cat_df["Type"] == "Mål"].dropna(subset=["Value"])
                outcomes = cat_df[cat_df["Type"] == "Utfall"].dropna(subset=["Value"])
                
                # Plot goals (dotted line)
                if not goals.empty:
                    axes[i].plot(goals["Week"], goals["Value"], 
                               color=self.colors["Mål"], 
                               linestyle=":", 
                               marker="o" if self.show_markers else None,
                               label="Mål",
                               drawstyle='steps-post')  # Use steps-post to avoid ghosting
                
                # Plot outcomes (solid line)
                if not outcomes.empty:
                    axes[i].plot(outcomes["Week"], outcomes["Value"], 
                               color=self.colors["Utfall"], 
                               linestyle="-", 
                               marker="o" if self.show_markers else None,
                               label="Utfall",
                               drawstyle='steps-post')  # Use steps-post to avoid ghosting
                
                # Basic plot settings
                axes[i].set_title(category, color="#FFFFFF")
                axes[i].set_xlabel("Week", color="#FAFAFA")
                
                # If it's a "lower is better" metric, invert the y-axis
                if is_lower_better:
                    axes[i].invert_yaxis()
                    axes[i].set_ylabel("Value (lower is better)", color="#FAFAFA")
                else:
                    axes[i].set_ylabel("Value", color="#FAFAFA")
                
                # Format x-axis to only show the weeks that are available
                if weeks:
                    axes[i].set_xticks(weeks)
                    axes[i].set_xticklabels([f"{w}" for w in weeks], rotation=45, fontsize=8)
                    
                    # Set x-axis limits to ensure all weeks are shown
                    axes[i].set_xlim(min(weeks) - 0.5, max(weeks) + 0.5)
                
                # Add data point annotations
                for df, label in [(goals, "Mål"), (outcomes, "Utfall")]:
                    if not df.empty:
                        for x, y in zip(df["Week"], df["Value"]):
                            axes[i].annotate(
                                f"{y:.0f}",
                                (x, y),
                                textcoords="offset points",
                                xytext=(0, 10),
                                ha='center',
                                color=self.colors[label],
                                fontweight='bold',
                                fontsize=8
                            )
                
                # Add legend and grid
                axes[i].legend(title="", frameon=True, facecolor="#262730", edgecolor="#666666", fontsize=8)
                axes[i].grid(True, linestyle="--", alpha=0.7, color="#444444")
        
        # Hide unused subplots
        for j in range(i + 1, len(axes)):
            fig.delaxes(axes[j])
            
        # Adjust layout
        fig.tight_layout(rect=[0, 0, 1, 0.95])
        
        return fig
        
    def create_summary_dashboard(self, x_range=None):
        """
        Create a full dashboard with all metrics grouped by category.
        
        Args:
            x_range: Tuple of (start_week, end_week) for x-axis range. If None, uses all available weeks.
            
        Returns:
            Dict of matplotlib Figure objects keyed by group name
        """
        self.prepare_data()
        
        # Group categories
        financial = ["Försäljning SEK eller högre", "Utgifter SEK eller lägre", "Resultat SEK"]
        
        productivity = [
            "Bokade möten", "Git commits", "Artiklar Hemsida (SEO)",
            "Gratis verktyg hemsida (SEO)", "Skickade E-post", 
            "Färdiga moment produktion"
        ]
        
        content = ["Långa YT videos", "Korta YT videos"]
        
        # Filter categories that exist in the data
        data_categories = set()
        if self.data is not None and not self.data.empty:
            data_categories = set(self.data["Category"].unique())
        
        # Define additional statistics groups based on prefix
        yt_stats = [cat for cat in data_categories if cat.startswith("YT")]
        website_stats = [cat for cat in data_categories if cat.startswith("Balthazar")]
        email_stats = [cat for cat in data_categories if cat.startswith("E-post")]
        customer_stats = [cat for cat in data_categories if cat.startswith("Antal kunder")]
        
        # Filter out categories that are already in other groups
        already_included = set(financial + productivity + content + yt_stats + website_stats + email_stats + customer_stats)
        other_stats = list(data_categories - already_included)
        
        # Filter out categories that don't exist in the data
        financial = [cat for cat in financial if cat in data_categories]
        productivity = [cat for cat in productivity if cat in data_categories]
        content = [cat for cat in content if cat in data_categories]
        
        # Create figures for each group
        figures = {}
        
        if financial:
            figures["Financial Metrics"] = self.create_category_group_plots(
                financial,
                "Financial Metrics",
                x_range=x_range
            )
            
        if productivity:
            figures["Productivity Metrics"] = self.create_category_group_plots(
                productivity,
                "Productivity Metrics",
                x_range=x_range
            )
            
        if content:
            figures["Content Metrics"] = self.create_category_group_plots(
                content,
                "Content Metrics",
                x_range=x_range
            )
            
        if yt_stats:
            figures["YouTube Statistics"] = self.create_category_group_plots(
                yt_stats, "YouTube Statistics",
                x_range=x_range
            )
            
        if website_stats:
            figures["Website Statistics"] = self.create_category_group_plots(
                website_stats, "Website Statistics",
                x_range=x_range
            )
            
        if email_stats:
            figures["Email Statistics"] = self.create_category_group_plots(
                email_stats, "Email Statistics",
                x_range=x_range
            )
            
        if customer_stats:
            figures["Customer Statistics"] = self.create_category_group_plots(
                customer_stats, "Customer Statistics",
                x_range=x_range
            )
            
        if other_stats:
            figures["Other Statistics"] = self.create_category_group_plots(
                other_stats, "Other Statistics",
                x_range=x_range
            )
            
        return figures
        
    def create_metrics_display(self):
        """
        Create a metrics display for visualization.
        
        Returns:
            Plotly Figure with metrics summary
        """
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        
        if self.data is None or self.data.empty:
            # Return empty figure
            fig = go.Figure()
            fig.add_annotation(
                text="No data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color="white")
            )
            fig.update_layout(
                paper_bgcolor="#262730",
                plot_bgcolor="#262730",
                font=dict(color="white")
            )
            return fig
            
        try:
            # Prepare data
            self.prepare_data()
            
            # Check if required columns exist
            required_columns = ["Week", "Category", "Type", "Value"]
            for col in required_columns:
                if col not in self.data.columns:
                    print(f"Missing required column: {col}")
                    fig = go.Figure()
                    fig.add_annotation(
                        text=f"Missing required column: {col}",
                        xref="paper", yref="paper",
                        x=0.5, y=0.5, showarrow=False,
                        font=dict(size=16, color="white")
                    )
                    fig.update_layout(
                        paper_bgcolor="#262730",
                        plot_bgcolor="#262730",
                        font=dict(color="white")
                    )
                    return fig
            
            # Get latest week data
            latest_week = self.data["Week"].max()
            latest_data = self.data[self.data["Week"] == latest_week]
            
            # Get goal and outcome pairs
            metrics = []
            for category in latest_data["Category"].unique():
                cat_data = latest_data[latest_data["Category"] == category]
                goal = cat_data[cat_data["Type"] == "Mål"]["Value"].values
                outcome = cat_data[cat_data["Type"] == "Utfall"]["Value"].values
                
                goal_val = None if len(goal) == 0 else goal[0]
                outcome_val = None if len(outcome) == 0 else outcome[0]
                
                if goal_val is not None or outcome_val is not None:
                    metrics.append({
                        "Category": category,
                        "Goal": goal_val,
                        "Outcome": outcome_val
                    })
                    
            if not metrics:
                # Return empty figure
                fig = go.Figure()
                fig.add_annotation(
                    text="No metrics data available for the latest week",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=16, color="white")
                )
                fig.update_layout(
                    paper_bgcolor="#262730",
                    plot_bgcolor="#262730",
                    font=dict(color="white")
                )
                return fig
            
            # Create figure with subplots
            n_metrics = len(metrics)
            n_cols = min(3, n_metrics)
            n_rows = (n_metrics + n_cols - 1) // n_cols
            
            fig = make_subplots(
                rows=n_rows, cols=n_cols,
                subplot_titles=[m["Category"] for m in metrics],
                specs=[[{"type": "indicator"} for _ in range(n_cols)] for _ in range(n_rows)]
            )
            
            # Add indicators
            for i, metric in enumerate(metrics):
                row = i // n_cols + 1
                col = i % n_cols + 1
                
                goal = metric["Goal"]
                outcome = metric["Outcome"]
                
                # Check if this is a "lower is better" metric
                is_lower_better = any(pattern in metric["Category"].lower() for pattern in ["lägre", "mindre", "lower", "utgifter"])
                
                if goal is not None and outcome is not None:
                    # Calculate progress
                    if is_lower_better:
                        # For "lower is better" metrics, progress is reverse
                        progress = (goal / outcome) * 100 if outcome != 0 else 0
                        reference = 100
                    else:
                        # For normal metrics, progress is (outcome/goal)*100
                        progress = (outcome / goal) * 100 if goal != 0 else 0
                        reference = 100
                    
                    fig.add_trace(
                        go.Indicator(
                            mode="gauge+number",
                            value=progress,
                            title={"text": f"{metric['Category']}<br><span style='font-size:0.8em;'>Week {latest_week}</span>"},
                            gauge={
                                "axis": {"range": [0, 200], "ticksuffix": "%", "tickwidth": 1, "tickcolor": "white"},
                                "bar": {"color": "#FF4B4B"},
                                "bgcolor": "white",
                                "borderwidth": 2,
                                "bordercolor": "gray",
                                "steps": [
                                    {"range": [0, 50], "color": "#FF0000"},
                                    {"range": [50, 100], "color": "#FFFF00"},
                                    {"range": [100, 200], "color": "#00FF00"}
                                ],
                                "threshold": {
                                    "line": {"color": "black", "width": 4},
                                    "thickness": 0.75,
                                    "value": reference
                                }
                            },
                            number={"suffix": "%", "font": {"size": 20}},
                            domain={"row": row - 1, "column": col - 1}
                        )
                    )
                elif goal is not None:
                    fig.add_trace(
                        go.Indicator(
                            mode="number",
                            value=goal,
                            title={"text": f"{metric['Category']}<br><span style='font-size:0.8em;'>Goal: {goal}</span>"},
                            number={"font": {"size": 20, "color": "#00BFFF"}},
                            domain={"row": row - 1, "column": col - 1}
                        )
                    )
                elif outcome is not None:
                    fig.add_trace(
                        go.Indicator(
                            mode="number",
                            value=outcome,
                            title={"text": f"{metric['Category']}<br><span style='font-size:0.8em;'>Outcome: {outcome}</span>"},
                            number={"font": {"size": 20, "color": "#FF4B4B"}},
                            domain={"row": row - 1, "column": col - 1}
                        )
                    )
            
            # Update layout
            fig.update_layout(
                height=300 * n_rows,
                paper_bgcolor="#262730",
                plot_bgcolor="#262730",
                font=dict(color="white"),
                margin=dict(t=50, b=20),
                title="Latest Week Metrics"
            )
            
            return fig
        except Exception as e:
            print(f"Error creating metrics display: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Return error figure
            fig = go.Figure()
            fig.add_annotation(
                text=f"Error creating metrics display: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color="white")
            )
            fig.update_layout(
                paper_bgcolor="#262730",
                plot_bgcolor="#262730",
                font=dict(color="white")
            )
            return fig
        
    def create_category_plots(self):
        """
        Create category plots for visualization.
        
        Returns:
            List of Plotly Figures
        """
        import plotly.graph_objects as go
        import plotly.express as px
        
        if self.data is None or self.data.empty:
            # Return empty figure
            fig = go.Figure()
            fig.add_annotation(
                text="No data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color="white")
            )
            fig.update_layout(
                paper_bgcolor="#262730",
                plot_bgcolor="#262730",
                font=dict(color="white")
            )
            return [fig]
            
        try:
            # Prepare data
            self.prepare_data()
            
            # Check if required columns exist
            required_columns = ["Week", "Category", "Type", "Value"]
            for col in required_columns:
                if col not in self.data.columns:
                    print(f"Missing required column: {col}")
                    fig = go.Figure()
                    fig.add_annotation(
                        text=f"Missing required column: {col}",
                        xref="paper", yref="paper",
                        x=0.5, y=0.5, showarrow=False,
                        font=dict(size=16, color="white")
                    )
                    fig.update_layout(
                        paper_bgcolor="#262730",
                        plot_bgcolor="#262730",
                        font=dict(color="white")
                    )
                    return [fig]
            
            # Group categories
            financial = ["Försäljning SEK eller högre", "Utgifter SEK eller lägre", "Resultat SEK"]
            productivity = [
                "Bokade möten", "Git commits", "Artiklar Hemsida (SEO)",
                "Gratis verktyg hemsida (SEO)", "Skickade E-post", 
                "Färdiga moment produktion"
            ]
            content = ["Långa YT videos", "Korta YT videos"]
            
            # Filter categories that exist in the data
            data_categories = set(self.data["Category"].unique())
            financial = [cat for cat in financial if cat in data_categories]
            productivity = [cat for cat in productivity if cat in data_categories]
            content = [cat for cat in content if cat in data_categories]
            
            # Create figures
            figures = []
            
            if financial:
                fig = go.Figure()
                for category in financial:
                    cat_data = self.data[self.data["Category"] == category]
                    
                    # Plot goals
                    goals = cat_data[cat_data["Type"] == "Mål"].dropna(subset=["Value"])
                    if not goals.empty:
                        fig.add_trace(
                            go.Scatter(
                                x=goals["Week"],
                                y=goals["Value"],
                                mode="lines+markers",
                                name=f"{category} - Mål",
                                line=dict(dash="dot", color=self.colors["Mål"]),
                                legendgroup=category
                            )
                        )
                    
                    # Plot outcomes
                    outcomes = cat_data[cat_data["Type"] == "Utfall"].dropna(subset=["Value"])
                    if not outcomes.empty:
                        fig.add_trace(
                            go.Scatter(
                                x=outcomes["Week"],
                                y=outcomes["Value"],
                                mode="lines+markers",
                                name=f"{category} - Utfall",
                                line=dict(color=self.colors["Utfall"]),
                                legendgroup=category
                            )
                        )
                
                # Update layout
                fig.update_layout(
                    title="Financial Metrics",
                    xaxis_title="Week",
                    yaxis_title="Value",
                    paper_bgcolor="#262730",
                    plot_bgcolor="#262730",
                    font=dict(color="white"),
                    legend=dict(
                        font=dict(color="white"),
                        bgcolor="#262730",
                        bordercolor="white",
                        borderwidth=1
                    ),
                    xaxis=dict(gridcolor="#444"),
                    yaxis=dict(gridcolor="#444")
                )
                
                figures.append(fig)
                
            if productivity:
                fig = go.Figure()
                for category in productivity:
                    cat_data = self.data[self.data["Category"] == category]
                    
                    # Plot goals
                    goals = cat_data[cat_data["Type"] == "Mål"].dropna(subset=["Value"])
                    if not goals.empty:
                        fig.add_trace(
                            go.Scatter(
                                x=goals["Week"],
                                y=goals["Value"],
                                mode="lines+markers",
                                name=f"{category} - Mål",
                                line=dict(dash="dot", color=self.colors["Mål"]),
                                legendgroup=category
                            )
                        )
                    
                    # Plot outcomes
                    outcomes = cat_data[cat_data["Type"] == "Utfall"].dropna(subset=["Value"])
                    if not outcomes.empty:
                        fig.add_trace(
                            go.Scatter(
                                x=outcomes["Week"],
                                y=outcomes["Value"],
                                mode="lines+markers",
                                name=f"{category} - Utfall",
                                line=dict(color=self.colors["Utfall"]),
                                legendgroup=category
                            )
                        )
                
                # Update layout
                fig.update_layout(
                    title="Productivity Metrics",
                    xaxis_title="Week",
                    yaxis_title="Value",
                    paper_bgcolor="#262730",
                    plot_bgcolor="#262730",
                    font=dict(color="white"),
                    legend=dict(
                        font=dict(color="white"),
                        bgcolor="#262730",
                        bordercolor="white",
                        borderwidth=1
                    ),
                    xaxis=dict(gridcolor="#444"),
                    yaxis=dict(gridcolor="#444")
                )
                
                figures.append(fig)
                
            if content:
                fig = go.Figure()
                for category in content:
                    cat_data = self.data[self.data["Category"] == category]
                    
                    # Plot goals
                    goals = cat_data[cat_data["Type"] == "Mål"].dropna(subset=["Value"])
                    if not goals.empty:
                        fig.add_trace(
                            go.Scatter(
                                x=goals["Week"],
                                y=goals["Value"],
                                mode="lines+markers",
                                name=f"{category} - Mål",
                                line=dict(dash="dot", color=self.colors["Mål"]),
                                legendgroup=category
                            )
                        )
                    
                    # Plot outcomes
                    outcomes = cat_data[cat_data["Type"] == "Utfall"].dropna(subset=["Value"])
                    if not outcomes.empty:
                        fig.add_trace(
                            go.Scatter(
                                x=outcomes["Week"],
                                y=outcomes["Value"],
                                mode="lines+markers",
                                name=f"{category} - Utfall",
                                line=dict(color=self.colors["Utfall"]),
                                legendgroup=category
                            )
                        )
                
                # Update layout
                fig.update_layout(
                    title="Content Metrics",
                    xaxis_title="Week",
                    yaxis_title="Value",
                    paper_bgcolor="#262730",
                    plot_bgcolor="#262730",
                    font=dict(color="white"),
                    legend=dict(
                        font=dict(color="white"),
                        bgcolor="#262730",
                        bordercolor="white",
                        borderwidth=1
                    ),
                    xaxis=dict(gridcolor="#444"),
                    yaxis=dict(gridcolor="#444")
                )
                
                figures.append(fig)
                
            return figures
            
        except Exception as e:
            print(f"Error creating category plots: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Return error figure
            fig = go.Figure()
            fig.add_annotation(
                text=f"Error creating category plots: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color="white")
            )
            fig.update_layout(
                paper_bgcolor="#262730",
                plot_bgcolor="#262730",
                font=dict(color="white")
            )
            return [fig]
        
    def create_comparison_plots(self):
        """
        Create comparison plots for visualization.
        
        Returns:
            List of Plotly Figures
        """
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        
        if self.data is None or self.data.empty:
            # Return empty figure
            fig = go.Figure()
            fig.add_annotation(
                text="No data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color="white")
            )
            fig.update_layout(
                paper_bgcolor="#262730",
                plot_bgcolor="#262730",
                font=dict(color="white")
            )
            return [fig]
            
        try:
            # Prepare data
            self.prepare_data()
            
            # Check if required columns exist
            required_columns = ["Week", "Category", "Type", "Value"]
            for col in required_columns:
                if col not in self.data.columns:
                    print(f"Missing required column: {col}")
                    fig = go.Figure()
                    fig.add_annotation(
                        text=f"Missing required column: {col}",
                        xref="paper", yref="paper",
                        x=0.5, y=0.5, showarrow=False,
                        font=dict(size=16, color="white")
                    )
                    fig.update_layout(
                        paper_bgcolor="#262730",
                        plot_bgcolor="#262730",
                        font=dict(color="white")
                    )
                    return [fig]
            
            # Get all categories
            all_categories = sorted(self.data["Category"].unique())
            
            # Create figures
            figures = []
            for category in all_categories:
                cat_data = self.data[self.data["Category"] == category]
                
                # Create subplots with 2 y-axes
                fig = make_subplots(specs=[[{"secondary_y": True}]])
                
                # Check if this is a "lower is better" metric
                is_lower_better = any(pattern in category.lower() for pattern in ["lägre", "mindre", "lower", "utgifter"])
                
                # Plot goals
                goals = cat_data[cat_data["Type"] == "Mål"].dropna(subset=["Value"])
                if not goals.empty:
                    fig.add_trace(
                        go.Scatter(
                            x=goals["Week"],
                            y=goals["Value"],
                            mode="lines+markers",
                            name="Mål",
                            line=dict(dash="dot", color=self.colors["Mål"])
                        ),
                        secondary_y=False
                    )
                
                # Plot outcomes
                outcomes = cat_data[cat_data["Type"] == "Utfall"].dropna(subset=["Value"])
                if not outcomes.empty:
                    fig.add_trace(
                        go.Scatter(
                            x=outcomes["Week"],
                            y=outcomes["Value"],
                            mode="lines+markers",
                            name="Utfall",
                            line=dict(color=self.colors["Utfall"])
                        ),
                        secondary_y=False
                    )
                    
                # Plot bar chart of achievement percentage
                if not goals.empty and not outcomes.empty:
                    # Merge goals and outcomes on Week
                    merged = pd.merge(
                        goals[["Week", "Value"]].rename(columns={"Value": "Goal"}),
                        outcomes[["Week", "Value"]].rename(columns={"Value": "Outcome"}),
                        on="Week",
                        how="inner"
                    )
                    
                    if not merged.empty:
                        # Calculate achievement percentage
                        if is_lower_better:
                            # For "lower is better" metrics, achievement is (goal/outcome)*100
                            merged["Achievement"] = (merged["Goal"] / merged["Outcome"]) * 100
                        else:
                            # For normal metrics, achievement is (outcome/goal)*100
                            merged["Achievement"] = (merged["Outcome"] / merged["Goal"]) * 100
                        
                        fig.add_trace(
                            go.Bar(
                                x=merged["Week"],
                                y=merged["Achievement"],
                                name="Achievement %",
                                marker=dict(color="rgba(50, 171, 96, 0.6)"),
                                opacity=0.7
                            ),
                            secondary_y=True
                        )
                
                # Update layout
                fig.update_layout(
                    title=f"{category}: Goals vs. Outcomes",
                    xaxis_title="Week",
                    paper_bgcolor="#262730",
                    plot_bgcolor="#262730",
                    font=dict(color="white"),
                    legend=dict(
                        font=dict(color="white"),
                        bgcolor="#262730",
                        bordercolor="white",
                        borderwidth=1
                    ),
                    xaxis=dict(gridcolor="#444"),
                    yaxis=dict(gridcolor="#444"),
                    yaxis2=dict(gridcolor="#444", range=[0, 200])
                )
                
                # Update y-axis labels
                fig.update_yaxes(title_text="Value", secondary_y=False, color="white")
                fig.update_yaxes(title_text="Achievement %", secondary_y=True, color="rgba(50, 171, 96, 1)")
                
                # If it's a "lower is better" metric, add a note
                if is_lower_better:
                    fig.add_annotation(
                        text="(lower is better)",
                        xref="paper", yref="paper",
                        x=0.5, y=1.05,
                        showarrow=False,
                        font=dict(size=12, color="white")
                    )
                
                figures.append(fig)
                
            return figures
            
        except Exception as e:
            print(f"Error creating comparison plots: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Return error figure
            fig = go.Figure()
            fig.add_annotation(
                text=f"Error creating comparison plots: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color="white")
            )
            fig.update_layout(
                paper_bgcolor="#262730",
                plot_bgcolor="#262730",
                font=dict(color="white")
            )
            return [fig]
        
    def save_to_browser(self, date_range):
        """
        Save data and configuration to browser storage.
        
        Args:
            date_range: Tuple of (start_date, end_date)
        """
        if self.data is not None:
            self.storage.save_data(self.data, date_range)
    
    def load_from_browser(self):
        """
        Load data from browser storage.
        
        Returns:
            Tuple of (data_df, date_range) or (None, None) if no data exists
        """
        return self.storage.load_data()
    
    def save_config(self, config):
        """
        Save configuration to browser storage.
        
        Args:
            config: Dictionary containing configuration settings
        """
        self.storage.save_config(config)
    
    def load_config(self):
        """
        Load configuration from browser storage.
        
        Returns:
            Dictionary containing configuration settings
        """
        return self.storage.load_config()
    
    def clear_browser_data(self):
        """Clear data from browser storage."""
        self.storage.clear_data()
    
    def clear_config(self):
        """Clear configuration from browser storage."""
        self.storage.clear_config()
    
    def has_browser_data(self):
        """Check if data exists in browser storage."""
        return self.storage.has_data()
    
    def has_config(self):
        """Check if configuration exists in browser storage."""
        return self.storage.has_config() 