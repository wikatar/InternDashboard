import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

class BalthazarGSheetConnector:
    def __init__(self, credentials_path, sheet_name, worksheet_name=None):
        """
        Initialize the connector with Google Sheets credentials and sheet name.
        
        Args:
            credentials_path: Path to Google API credentials JSON file
            sheet_name: Name of the Google Sheet to connect to
            worksheet_name: Name of the specific worksheet/tab to use (optional)
        """
        self.credentials_path = credentials_path
        self.sheet_name = sheet_name
        self.worksheet_name = worksheet_name
        self.scope = ['https://spreadsheets.google.com/feeds',
                      'https://www.googleapis.com/auth/drive']
        
    def connect(self):
        """Establish connection to the Google Sheet."""
        try:
            credentials = ServiceAccountCredentials.from_json_keyfile_name(
                self.credentials_path, self.scope)
            self.client = gspread.authorize(credentials)
            
            # Check if we can access any sheets first
            available_sheets = []
            try:
                available_sheets = [sheet.title for sheet in self.client.openall()]
                print(f"Service account can access these sheets: {available_sheets}")
            except Exception as e:
                print(f"Error listing available sheets: {e}")
            
            # Try to open by title
            try:
                self.spreadsheet = self.client.open(self.sheet_name)
                print(f"Successfully opened Google Sheet: {self.sheet_name}")
                
                # Get all worksheet names in this spreadsheet
                worksheet_names = [ws.title for ws in self.spreadsheet.worksheets()]
                print(f"Available worksheets in '{self.sheet_name}': {worksheet_names}")
                
                # Select the specified worksheet if provided, otherwise use the first one
                if self.worksheet_name and self.worksheet_name in worksheet_names:
                    self.sheet = self.spreadsheet.worksheet(self.worksheet_name)
                    print(f"Using worksheet: {self.worksheet_name}")
                else:
                    self.sheet = self.spreadsheet.sheet1
                    print(f"Using first worksheet: {self.sheet.title}")
                
                return True
                
            except gspread.exceptions.SpreadsheetNotFound:
                print(f"Sheet '{self.sheet_name}' not found.")
                print("Please make sure:")
                print(f"1. Your Google Sheet is exactly named '{self.sheet_name}'")
                print(f"2. You've shared it with the service account email in your credentials file")
                print(f"3. You've given Editor permissions to that email")
                
                if not available_sheets:
                    print("\nThe service account cannot access ANY sheets. Please check sharing permissions.")
                else:
                    print(f"\nThe service account can access these sheets: {available_sheets}")
                    print("Consider using one of these names instead.")
                
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