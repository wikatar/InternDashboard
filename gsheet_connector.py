import gspread
import pandas as pd
import re
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
            data = self.sheet.get(range_name)
            print(f"Successfully fetched {len(data)} rows of data")
            
            # Print a sample of the data structure
            if data and len(data) > 0:
                print(f"First row structure: {data[0]}")
                if len(data) > 1:
                    print(f"Second row structure: {data[1]}")
            else:
                print("Warning: No data rows found in the specified range")
                
            return data
        except Exception as e:
            print(f"Error fetching data: {e}")
            return []
    
    def process_data(self, data):
        """
        Process raw sheet data into a structured DataFrame based on the Veckomål structure.
        
        Args:
            data: Raw data from Google Sheet as list of lists
            
        Returns:
            Pandas DataFrame with processed data
        """
        if not data or len(data) < 1:
            print("Not enough data to process (need at least 1 row)")
            return pd.DataFrame()
            
        print(f"Processing {len(data)} rows of data")
        
        # Based on the prints, we can see that:
        # 1. Categories are in column 1 (index 1), not column 0
        # 2. Day values start from column 2 (index 2)
        
        # Get columns for days
        day_columns = list(range(2, 11))  # Columns 2-10 (indices 2-10)
        days = [str(d) for d in range(1, len(day_columns) + 1)]
        print(f"Using day columns at positions: {day_columns}")
        
        records = []
        category_pattern = re.compile(r'(Mål|Utfall)[:\s]+(.+)')
        
        for row_idx, row in enumerate(data):
            if not row or len(row) <= 1:
                continue
                
            # Get category from column 1
            category_col = row[1].strip() if len(row) > 1 and row[1] else ""
            
            # Skip rows without category information
            if not category_col:
                continue
            
            # Check if this is a category row
            match = category_pattern.match(category_col)
            
            if match:
                # This is a category row with Mål/Utfall
                row_type, category_name = match.groups()
                current_type = "Mål" if "Mål" in row_type else "Utfall"
                current_category = category_name.strip()
                print(f"Row {row_idx}: Found {current_type} for category '{current_category}'")
                
                # Process values for this category
                for day_idx, col_idx in enumerate(day_columns):
                    if col_idx < len(row):
                        value = row[col_idx]
                        if value not in ('', None):
                            try:
                                # Handle different number formats
                                if isinstance(value, str):
                                    value = value.replace(',', '.').replace(' ', '')
                                
                                numeric_value = float(value)
                                records.append({
                                    "Date": int(days[day_idx]), 
                                    "Category": current_category, 
                                    "Type": current_type, 
                                    "Value": numeric_value
                                })
                                print(f"  - Added record: Date={days[day_idx]}, Category={current_category}, Type={current_type}, Value={numeric_value}")
                            except (ValueError, TypeError, IndexError) as e:
                                print(f"  - Skipping value '{value}': {e}")
        
        if not records:
            print("Warning: No valid records found after processing")
            return pd.DataFrame()
            
        print(f"Successfully created {len(records)} records")
        df = pd.DataFrame(records)
        return df 