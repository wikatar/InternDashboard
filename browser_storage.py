import json
import pandas as pd
import os
import pickle
from datetime import datetime

class BrowserStorage:
    def __init__(self):
        """Initialize persistent storage handler."""
        self.data_file = "balthazar_dashboard_data.pkl"
        self.config_file = "balthazar_dashboard_config.pkl"
        
    def save_data(self, data_df, date_range):
        """
        Save data and date range to persistent storage.
        
        Args:
            data_df: Pandas DataFrame with the data
            date_range: Tuple of (start_date, end_date) as datetime objects
        """
        # Convert date range to strings if they are datetime objects
        date_range_str = date_range
        if hasattr(date_range[0], 'strftime'):
            date_range_str = (
                date_range[0].strftime("%Y-%m-%d"),
                date_range[1].strftime("%Y-%m-%d")
            )
        
        # Create storage object
        storage_data = {
            "data": data_df.copy(),  # Make a copy to avoid reference issues
            "date_range": date_range_str,
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Save to pickle file
        try:
            # Use the highest protocol for better compatibility
            with open(self.data_file, 'wb') as f:
                pickle.dump(storage_data, f, protocol=pickle.HIGHEST_PROTOCOL)
            
            # Verify the data was saved correctly
            if os.path.exists(self.data_file) and os.path.getsize(self.data_file) > 0:
                return True
            else:
                print("Warning: Data file was created but appears to be empty.")
                return False
        except Exception as e:
            print(f"Error saving data: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        
    def load_data(self):
        """
        Load data and date range from persistent storage.
        
        Returns:
            Tuple of (data_df, date_range) or (None, None) if no data exists
        """
        # Check if file exists
        if not os.path.exists(self.data_file):
            return None, None
            
        try:
            # Load from pickle file
            with open(self.data_file, 'rb') as f:
                storage_data = pickle.load(f)
                
            # Extract data and date range
            data_df = storage_data["data"]
            date_range_str = storage_data["date_range"]
            
            # Convert date range strings back to datetime objects if needed
            date_range = date_range_str
            if isinstance(date_range_str[0], str):
                try:
                    date_range = (
                        datetime.strptime(date_range_str[0], "%Y-%m-%d"),
                        datetime.strptime(date_range_str[1], "%Y-%m-%d")
                    )
                except:
                    # Keep as strings if conversion fails
                    pass
                
            return data_df, date_range
        except Exception as e:
            print(f"Error loading data: {str(e)}")
            return None, None
        
    def save_config(self, config):
        """
        Save configuration to persistent storage.
        
        Args:
            config: Dictionary containing configuration settings
        """
        try:
            # Make a copy of the config to avoid reference issues
            config_copy = {}
            for key, value in config.items():
                config_copy[key] = value
                
            # Save with the highest protocol for better compatibility
            with open(self.config_file, 'wb') as f:
                pickle.dump(config_copy, f, protocol=pickle.HIGHEST_PROTOCOL)
            
            # Verify the config was saved correctly
            if os.path.exists(self.config_file) and os.path.getsize(self.config_file) > 0:
                return True
            else:
                print("Warning: Config file was created but appears to be empty.")
                return False
        except Exception as e:
            print(f"Error saving config: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        
    def load_config(self):
        """
        Load configuration from persistent storage.
        
        Returns:
            Dictionary containing configuration settings or None if no config exists
        """
        # Check if file exists
        if not os.path.exists(self.config_file):
            return None
            
        try:
            with open(self.config_file, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            print(f"Error loading config: {str(e)}")
            return None
        
    def clear_data(self):
        """Clear data from persistent storage."""
        if os.path.exists(self.data_file):
            try:
                os.remove(self.data_file)
                return True
            except Exception as e:
                print(f"Error clearing data: {str(e)}")
                return False
        return True
        
    def clear_config(self):
        """Clear configuration from persistent storage."""
        if os.path.exists(self.config_file):
            try:
                os.remove(self.config_file)
                return True
            except Exception as e:
                print(f"Error clearing config: {str(e)}")
                return False
        return True
        
    def clear_all(self):
        """Clear all data and configuration from persistent storage."""
        data_cleared = self.clear_data()
        config_cleared = self.clear_config()
        return data_cleared and config_cleared
        
    def has_data(self):
        """Check if data exists in persistent storage."""
        return os.path.exists(self.data_file)
        
    def has_config(self):
        """Check if configuration exists in persistent storage."""
        return os.path.exists(self.config_file) 