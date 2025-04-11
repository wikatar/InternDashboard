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
        
        # Define color palette for consistent visualization
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
        """Prepare data for visualization by adding Month column and sorting."""
        if self.df.empty:
            return
            
        # Ensure Date is an integer
        self.df["Date"] = pd.to_numeric(self.df["Date"], errors="coerce")
        
        # Sort by Date
        self.df = self.df.sort_values("Date")
        
    def create_metric_comparison(self, category, figsize=(10, 6)):
        """
        Create a comparison plot of goals vs. outcomes for a specific category.
        
        Args:
            category: Category name to plot
            figsize: Figure size tuple (width, height)
            
        Returns:
            matplotlib Figure object
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        # Filter data for the given category
        cat_df = self.df[self.df["Category"] == category]
        
        if cat_df.empty:
            ax.text(0.5, 0.5, f"No data for {category}", ha="center", va="center", color="#FAFAFA")
            return fig
            
        # Create line plot
        sns.lineplot(
            data=cat_df,
            x="Date",
            y="Value",
            hue="Type",
            palette=self.colors,
            markers=True,
            ax=ax
        )
        
        # Set plot title and labels
        ax.set_title(f"{category}: Mål vs. Utfall", color="#FFFFFF", fontsize=14)
        ax.set_xlabel("Day of Month", color="#FAFAFA")
        ax.set_ylabel("Value", color="#FAFAFA")
        
        # Format x-axis ticks
        ax.set_xticks(cat_df["Date"].unique())
        
        # Add legend
        ax.legend(title="", frameon=True, facecolor="#262730", edgecolor="#666666")
        
        # Add grid
        ax.grid(True, linestyle="--", alpha=0.7, color="#444444")
        
        # Tight layout
        fig.tight_layout()
        
        return fig
        
    def create_category_group_plots(self, categories, group_name, figsize=(15, 10)):
        """
        Create a multi-plot figure with comparisons for a group of categories.
        
        Args:
            categories: List of category names to include
            group_name: Name of the category group
            figsize: Figure size tuple (width, height)
            
        Returns:
            matplotlib Figure object
        """
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
                cat_df = self.df[self.df["Category"] == category]
                
                if cat_df.empty:
                    axes[i].text(0.5, 0.5, f"No data for {category}", ha="center", va="center", color="#FAFAFA")
                    continue
                
                # Create line plot
                sns.lineplot(
                    data=cat_df,
                    x="Date",
                    y="Value",
                    hue="Type",
                    palette=self.colors,
                    markers=True,
                    ax=axes[i]
                )
                
                # Set plot title and labels
                axes[i].set_title(category, color="#FFFFFF")
                axes[i].set_xlabel("Day of Month", color="#FAFAFA")
                axes[i].set_ylabel("Value", color="#FAFAFA")
                
                # Format x-axis ticks
                axes[i].set_xticks(cat_df["Date"].unique())
                
                # Add grid
                axes[i].grid(True, linestyle="--", alpha=0.7, color="#444444")
                
                # Set legend
                axes[i].legend(frameon=True, facecolor="#262730", edgecolor="#666666")
        
        # Hide unused subplots
        for j in range(i + 1, len(axes)):
            fig.delaxes(axes[j])
            
        # Adjust layout
        fig.tight_layout(rect=[0, 0, 1, 0.95])  # Leave space for suptitle
        
        return fig
        
    def create_summary_dashboard(self):
        """
        Create a full dashboard with all metrics grouped by category.
        
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
                "Financial Metrics"
            )
            
        if any(cat in all_categories for cat in productivity):
            figures["Productivity Metrics"] = self.create_category_group_plots(
                [cat for cat in productivity if cat in all_categories],
                "Productivity Metrics"
            )
            
        if any(cat in all_categories for cat in content):
            figures["Content Metrics"] = self.create_category_group_plots(
                [cat for cat in content if cat in all_categories],
                "Content Metrics"
            )
            
        if yt_stats:
            figures["YouTube Statistics"] = self.create_category_group_plots(
                yt_stats, "YouTube Statistics"
            )
            
        if website_stats:
            figures["Website Statistics"] = self.create_category_group_plots(
                website_stats, "Website Statistics"
            )
            
        if email_stats:
            figures["Email Statistics"] = self.create_category_group_plots(
                email_stats, "Email Statistics"
            )
            
        if customer_stats:
            figures["Customer Statistics"] = self.create_category_group_plots(
                customer_stats, "Customer Statistics"
            )
            
        if other_stats:
            figures["Other Statistics"] = self.create_category_group_plots(
                other_stats, "Other Statistics"
            )
            
        return figures 