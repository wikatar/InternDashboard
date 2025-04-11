import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure
import numpy as np

class BalthazarVisualizer:
    def __init__(self, data_df):
        """
        Initialize the visualizer with a DataFrame containing processed data.
        
        Args:
            data_df: Pandas DataFrame with columns Date, Category, Type, Value
        """
        self.df = data_df
        
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
        
    def prepare_data(self):
        """Prepare data for visualization by adding Week column and sorting."""
        if self.df.empty:
            return
            
        # Ensure Date is an integer
        self.df["Date"] = pd.to_numeric(self.df["Date"], errors="coerce")
        
        # Convert day numbers to week numbers (assuming days 1-7 are week 1, etc.)
        self.df["Week"] = ((self.df["Date"] - 1) // 7) + 1
        
        # Sort by Week and Type to ensure consistent plotting
        self.df = self.df.sort_values(["Week", "Type"])
        
        # Handle "lower is better" metrics by inverting their values
        lower_better_patterns = ["lägre", "mindre", "lower"]
        for pattern in lower_better_patterns:
            mask = self.df["Category"].str.contains(pattern, case=False, na=False)
            self.df.loc[mask, "Value"] = -self.df.loc[mask, "Value"]
            
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
        if figsize is None:
            figsize = self.default_figsize
            
        fig, ax = plt.subplots(figsize=figsize)
        
        # Filter data for the given category
        cat_df = self.df[self.df["Category"] == category].copy()
        
        if cat_df.empty:
            ax.text(0.5, 0.5, f"No data for {category}", ha="center", va="center", color="#FAFAFA")
            return fig
            
        # Ensure data is sorted by Week
        cat_df = cat_df.sort_values("Week")
        
        # Get all weeks in the data
        all_weeks = sorted(cat_df["Week"].unique())
        
        # Set x-axis range if specified
        if x_range:
            start_week, end_week = x_range
            cat_df = cat_df[(cat_df["Week"] >= start_week) & (cat_df["Week"] <= end_week)]
            weeks = list(range(start_week, end_week + 1))
        else:
            weeks = all_weeks
        
        # Plot goals first (dotted line)
        goal_df = cat_df[cat_df["Type"] == "Mål"]
        if not goal_df.empty:
            # Create a DataFrame with all weeks
            goal_data = pd.DataFrame({"Week": weeks})
            goal_data = goal_data.merge(goal_df[["Week", "Value"]], on="Week", how="left")
            
            # Forward fill missing values, but only within the actual data range
            first_valid_week = goal_df["Week"].min()
            last_valid_week = goal_df["Week"].max()
            
            # Only fill values between first and last valid weeks
            mask = (goal_data["Week"] >= first_valid_week) & (goal_data["Week"] <= last_valid_week)
            goal_data.loc[mask, "Value"] = goal_data.loc[mask, "Value"].fillna(method="ffill")
            
            # Plot only where we have actual values
            valid_goal_data = goal_data[goal_data["Value"].notna()]
            if not valid_goal_data.empty:
                sns.lineplot(
                    data=valid_goal_data,
                    x="Week",
                    y="Value",
                    color=self.colors["Mål"],
                    linestyle=":",  # Dotted line for goals
                    markers=self.show_markers,
                    label="Mål",
                    ax=ax,
                    sort=False,  # Prevent automatic sorting
                    drawstyle='steps-post'  # Use step-style plotting
                )
            
        # Plot outcomes second (solid line)
        outcome_df = cat_df[cat_df["Type"] == "Utfall"]
        if not outcome_df.empty:
            # Create a DataFrame with all weeks
            outcome_data = pd.DataFrame({"Week": weeks})
            outcome_data = outcome_data.merge(outcome_df[["Week", "Value"]], on="Week", how="left")
            
            # Plot only where we have actual values
            valid_outcome_data = outcome_data[outcome_data["Value"].notna()]
            if not valid_outcome_data.empty:
                sns.lineplot(
                    data=valid_outcome_data,
                    x="Week",
                    y="Value",
                    color=self.colors["Utfall"],
                    linestyle="-",  # Solid line for outcomes
                    markers=self.show_markers,
                    label="Utfall",
                    ax=ax,
                    sort=False,  # Prevent automatic sorting
                    drawstyle='steps-post'  # Use step-style plotting
                )
        
        # Set plot title and labels
        ax.set_title(f"{category}: Mål vs. Utfall", color="#FFFFFF", fontsize=14)
        ax.set_xlabel("Week", color="#FAFAFA")
        ax.set_ylabel("Value", color="#FAFAFA")
        
        # Format x-axis ticks
        ax.set_xticks(weeks)
        ax.set_xticklabels([f"Week {w}" for w in weeks])
        
        # Check if this is a "lower is better" metric
        is_lower_better = any(pattern in category.lower() for pattern in ["lägre", "mindre", "lower"])
        
        # If it's a "lower is better" metric, invert the y-axis
        if is_lower_better:
            ax.invert_yaxis()
            # Set y-axis label to indicate inversion
            ax.set_ylabel("Value (lower is better)", color="#FAFAFA")
            
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
        if figsize is None:
            figsize = self.default_figsize
            
        # Calculate grid size based on number of categories
        n_cats = len(categories)
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
                cat_df = self.df[self.df["Category"] == category].copy()
                
                if cat_df.empty:
                    axes[i].text(0.5, 0.5, f"No data for {category}", ha="center", va="center", color="#FAFAFA")
                    continue
                
                # Ensure data is sorted by Week
                cat_df = cat_df.sort_values("Week")
                
                # Get all weeks in the data
                all_weeks = sorted(cat_df["Week"].unique())
                
                # Set x-axis range if specified
                if x_range:
                    start_week, end_week = x_range
                    cat_df = cat_df[(cat_df["Week"] >= start_week) & (cat_df["Week"] <= end_week)]
                    weeks = list(range(start_week, end_week + 1))
                else:
                    weeks = all_weeks
                
                # Plot goals first (dotted line)
                goal_df = cat_df[cat_df["Type"] == "Mål"]
                if not goal_df.empty:
                    # Ensure we have data points for all weeks
                    goal_data = pd.DataFrame({"Week": weeks})
                    goal_data = goal_data.merge(goal_df[["Week", "Value"]], on="Week", how="left")
                    goal_data["Value"] = goal_data["Value"].fillna(method="ffill").fillna(method="bfill")
                    
                    sns.lineplot(
                        data=goal_data,
                        x="Week",
                        y="Value",
                        color=self.colors["Mål"],
                        linestyle=":",  # Dotted line for goals
                        markers=self.show_markers,
                        label="Mål",
                        ax=axes[i],
                        sort=False  # Prevent automatic sorting
                    )
                    
                # Plot outcomes second (solid line)
                outcome_df = cat_df[cat_df["Type"] == "Utfall"]
                if not outcome_df.empty:
                    # Ensure we have data points for all weeks
                    outcome_data = pd.DataFrame({"Week": weeks})
                    outcome_data = outcome_data.merge(outcome_df[["Week", "Value"]], on="Week", how="left")
                    
                    sns.lineplot(
                        data=outcome_data,
                        x="Week",
                        y="Value",
                        color=self.colors["Utfall"],
                        linestyle="-",  # Solid line for outcomes
                        markers=self.show_markers,
                        label="Utfall",
                        ax=axes[i],
                        sort=False  # Prevent automatic sorting
                    )
                
                # Set plot title and labels
                axes[i].set_title(category, color="#FFFFFF")
                axes[i].set_xlabel("Week", color="#FAFAFA")
                axes[i].set_ylabel("Value", color="#FAFAFA")
                
                # Format x-axis ticks
                axes[i].set_xticks(weeks)
                axes[i].set_xticklabels([f"Week {w}" for w in weeks])
                
                # Add legend
                axes[i].legend(title="", frameon=True, facecolor="#262730", edgecolor="#666666")
                
                # Add grid if enabled
                if self.show_grid:
                    axes[i].grid(True, linestyle="--", alpha=0.7, color="#444444")
        
        # Hide unused subplots
        for j in range(i + 1, len(axes)):
            fig.delaxes(axes[j])
            
        # Adjust layout
        fig.tight_layout(rect=[0, 0, 1, 0.95])  # Leave space for suptitle
        
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
        financial = ["Försäljning SEK eller högre", "Utgifter SEK eller lägre"]
        
        productivity = [
            "Bokade möten", "Git commits", "Artiklar Hemsida (SEO)",
            "Gratis verktyg hemsida (SEO)", "Skickade E-post", 
            "Färdiga moment produktion"
        ]
        
        content = ["Långa YT videos", "Korta YT videos"]
        
        # Define additional statistics groups based on prefix
        yt_stats = [cat for cat in self.df["Category"].unique() if cat.startswith("YT")]
        website_stats = [cat for cat in self.df["Category"].unique() if cat.startswith("Balthazar")]
        email_stats = [cat for cat in self.df["Category"].unique() if cat.startswith("E-post")]
        customer_stats = [cat for cat in self.df["Category"].unique() if cat.startswith("Antal kunder")]
        
        # Filter out categories that are already in other groups
        all_categories = set(self.df["Category"].unique())
        already_included = set(financial + productivity + content + yt_stats + website_stats + email_stats + customer_stats)
        other_stats = list(all_categories - already_included)
        
        # Create figures for each group
        figures = {}
        
        if any(cat in all_categories for cat in financial):
            figures["Financial Metrics"] = self.create_category_group_plots(
                [cat for cat in financial if cat in all_categories],
                "Financial Metrics",
                x_range=x_range
            )
            
        if any(cat in all_categories for cat in productivity):
            figures["Productivity Metrics"] = self.create_category_group_plots(
                [cat for cat in productivity if cat in all_categories],
                "Productivity Metrics",
                x_range=x_range
            )
            
        if any(cat in all_categories for cat in content):
            figures["Content Metrics"] = self.create_category_group_plots(
                [cat for cat in content if cat in all_categories],
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