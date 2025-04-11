import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from dashboard_visualizer import BalthazarVisualizer
from browser_storage import BrowserStorage
import plotly.graph_objects as go
import sys

def create_test_data():
    """Create test data similar to what we expect from Google Sheets."""
    data = []
    
    # Add some financial metrics
    for category in ["Försäljning SEK eller högre", "Utgifter SEK eller lägre", "Resultat SEK"]:
        for week in range(15, 23):
            # Add goals
            if week <= 16:  # Only add goals for the first two weeks
                value = np.random.randint(1000, 5000) if category == "Försäljning SEK eller högre" else np.random.randint(100, 500)
                if category == "Resultat SEK":
                    value = np.random.randint(-200, 4500)
                data.append({
                    "Date": week * 7,
                    "Category": category,
                    "Type": "Mål",
                    "Value": value
                })
            
            # Add outcomes for the first few weeks
            if week < 18:
                value = np.random.randint(0, 1000) if category == "Försäljning SEK eller högre" else np.random.randint(0, 200)
                if category == "Resultat SEK":
                    value = np.random.randint(-200, 0)
                data.append({
                    "Date": week * 7,
                    "Category": category,
                    "Type": "Utfall",
                    "Value": value
                })
    
    # Add productivity metrics with no outcomes
    for category in ["Bokade möten", "Git commits", "Artiklar Hemsida (SEO)"]:
        for week in range(15, 23):
            # Add goals for all weeks
            value = np.random.randint(1, 50)
            data.append({
                "Date": week * 7,
                "Category": category,
                "Type": "Mål",
                "Value": value
            })
    
    return pd.DataFrame(data)

def test_visualizer():
    """Test the BalthazarVisualizer with sample data."""
    print("Creating test data...")
    df = create_test_data()
    print(f"Created DataFrame with {len(df)} rows")
    
    print("\nTesting BalthazarVisualizer initialization...")
    try:
        visualizer = BalthazarVisualizer(df)
        print("Successfully initialized BalthazarVisualizer")
        
        print("\nTesting prepare_data method...")
        visualizer.prepare_data()
        print("Week column added successfully")
        print(f"Week values: {sorted(visualizer.data['Week'].unique())}")
        
        print("\nTesting create_metric_comparison method...")
        fig = visualizer.create_metric_comparison("Försäljning SEK eller högre")
        print("Successfully created metric comparison plot")
        
        print("\nTesting save_to_browser and load_from_browser...")
        date_range = ("2023-01-01", "2023-12-31")
        success = visualizer.save_to_browser(date_range)
        print(f"Save to browser {'successful' if success else 'failed'}")
        
        loaded_data, loaded_range = visualizer.load_from_browser()
        print(f"Load from browser {'successful' if loaded_data is not None else 'failed'}")
        if loaded_data is not None:
            print(f"Loaded DataFrame with {len(loaded_data)} rows")
        
        print("\nAll tests passed successfully!")
        return True
    
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print(f"Python version: {sys.version}")
    print(f"Pandas version: {pd.__version__}")
    print(f"Matplotlib version: {plt.matplotlib.__version__}")
    try:
        import plotly
        print(f"Plotly version: {plotly.__version__}")
    except ImportError:
        print("Plotly not installed")
    
    test_visualizer() 