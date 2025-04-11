import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

class BalthazarGSheetConnector:
    def __init__(self, credentials_path, sheet_name):
        """
        Initialize the connector with Google Sheets credentials and sheet name.
        
        Args:
            credentials_path: Path to Google API credentials JSON file
            sheet_name: Name of the Google Sheet to connect to
        """
        self.credentials_path = credentials_path
        self.sheet_name = sheet_name
        self.scope = ['https://spreadsheets.google.com/feeds',
                      'https://www.googleapis.com/auth/drive']
        
    def connect(self):
        """Establish connection to the Google Sheet."""
        try:
            credentials = ServiceAccountCredentials.from_json_keyfile_name(
                self.credentials_path, self.scope)
            self.client = gspread.authorize(credentials)
            
            # Try to open by title - this is the most common way
            try:
                self.sheet = self.client.open(self.sheet_name).sheet1
                return True
            except gspread.exceptions.SpreadsheetNotFound:
                # If not found by title, try listing all available sheets and log them
                available_sheets = [sheet.title for sheet in self.client.openall()]
                print(f"Available sheets: {available_sheets}")
                print(f"Sheet '{self.sheet_name}' not found. Please check the exact name.")
                return False
                
        except Exception as e:
            print(f"Connection error: {e}")
            return False
            
    def get_data(self, range_name="A1:AE100"):
        """
        Fetch data from the Google Sheet.
        
        Args:
            range_name: Cell range to fetch (e.g., "A1:Z100")
            
        Returns:
            Raw data from Google Sheet as a list of lists
        """
        try:
            return self.sheet.get(range_name)
        except Exception as e:
            print(f"Error fetching data: {e}")
            return []
    
    def process_data(self, data):
        """
        Process raw sheet data into a structured DataFrame.
        
        Args:
            data: Raw data from Google Sheet as list of lists
            
        Returns:
            Pandas DataFrame with processed data
        """
        if not data or len(data) < 2:
            return pd.DataFrame()
            
        days = data[0][1:]  # ['15', '16', ..., '27']
        records = []
        current_section = ""
        
        for row in data[1:]:
            if not row:
                continue
                
            label = row[0].strip() if row[0] else ""
            values = row[1:] if len(row) > 1 else []
            
            # Skip empty rows or rows with no values
            if not label or all(v == '' for v in values):
                # Check if this is a section header
                if label and any(section in label for section in [
                    "YT", "Balthazar", "E-post", "Antal kunder"
                ]):
                    current_section = label.split()[0]  # e.g., "YT", "Website", "E-post"
                continue
            
            # Process category and type
            if label.startswith("Mål:"):
                category = label[4:].strip()
                type_ = "Mål"
            elif label.startswith("Utfall:"):
                category = label[7:].strip()
                type_ = "Utfall"
            else:
                category = f"{current_section} {label}".strip()
                type_ = "Utfall"
            
            # Process values for each day
            # For goals, extend the last value if fewer than days
            if len(values) < len(days):
                if type_ == "Mål" and values:
                    last_value = values[-1]
                    values = values + [last_value for _ in range(len(days) - len(values))]
                else:
                    values = values + ['' for _ in range(len(days) - len(values))]
            
            # Create records for each day
            for day, value in zip(days, values):
                if day and value not in ('', None):
                    try:
                        numeric_value = float(value.replace(',', '.') if isinstance(value, str) else value)
                        records.append({
                            "Date": int(day), 
                            "Category": category, 
                            "Type": type_, 
                            "Value": numeric_value
                        })
                    except (ValueError, TypeError):
                        # Skip non-numeric values
                        pass
        
        return pd.DataFrame(records) 