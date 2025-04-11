import json
import pandas as pd
from datetime import datetime

class BrowserStorage:
    def __init__(self):
        """Initialize browser storage handler."""
        self.storage_key = "balthazar_dashboard_data"
        self.config_key = "balthazar_dashboard_config"
        
    def save_data(self, data_df, date_range):
        """
        Save data and date range to browser storage.
        
        Args:
            data_df: Pandas DataFrame with the data
            date_range: Tuple of (start_date, end_date) as datetime objects
        """
        # Convert DataFrame to JSON
        data_json = data_df.to_json(orient="records")
        
        # Convert date range to strings
        date_range_str = (
            date_range[0].strftime("%Y-%m-%d"),
            date_range[1].strftime("%Y-%m-%d")
        )
        
        # Create storage object
        storage_data = {
            "data": data_json,
            "date_range": date_range_str,
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Save to localStorage
        import js
        js.localStorage.setItem(self.storage_key, json.dumps(storage_data))
        
    def load_data(self):
        """
        Load data and date range from browser storage.
        
        Returns:
            Tuple of (data_df, date_range) or (None, None) if no data exists
        """
        # Load from localStorage
        import js
        stored_data = js.localStorage.getItem(self.storage_key)
        
        if not stored_data:
            return None, None
            
        # Parse stored data
        storage_data = json.loads(stored_data)
        
        # Convert JSON back to DataFrame
        data_df = pd.read_json(storage_data["data"], orient="records")
        
        # Convert date range strings back to datetime objects
        date_range = (
            datetime.strptime(storage_data["date_range"][0], "%Y-%m-%d"),
            datetime.strptime(storage_data["date_range"][1], "%Y-%m-%d")
        )
        
        return data_df, date_range
        
    def save_config(self, config):
        """
        Save configuration to browser storage.
        
        Args:
            config: Dictionary containing configuration settings
        """
        import js
        js.localStorage.setItem(self.config_key, json.dumps(config))
        
    def load_config(self):
        """
        Load configuration from browser storage.
        
        Returns:
            Dictionary containing configuration settings or None if no config exists
        """
        import js
        stored_config = js.localStorage.getItem(self.config_key)
        return json.loads(stored_config) if stored_config else None
        
    def clear_data(self):
        """Clear data from browser storage."""
        import js
        js.localStorage.removeItem(self.storage_key)
        
    def clear_config(self):
        """Clear configuration from browser storage."""
        import js
        js.localStorage.removeItem(self.config_key)
        
    def clear_all(self):
        """Clear all data and configuration from browser storage."""
        self.clear_data()
        self.clear_config()
        
    def has_data(self):
        """Check if data exists in browser storage."""
        import js
        return js.localStorage.getItem(self.storage_key) is not None
        
    def has_config(self):
        """Check if configuration exists in browser storage."""
        import js
        return js.localStorage.getItem(self.config_key) is not None 