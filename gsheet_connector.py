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
        
        # Find the header row with week numbers
        week_row_idx = -1
        week_cols = []
        week_numbers = []
        
        # Debug: Print first few rows
        for i, row in enumerate(data[:5]):
            print(f"Row {i}: {row}")
        
        # Search for the row with week numbers (usually the first or second row)
        for i, row in enumerate(data[:10]):  # Check first 10 rows
            if len(row) > 2:
                # Try to convert items to integers (week numbers)
                potential_weeks = []
                start_col = -1
                
                for j, cell in enumerate(row):
                    if cell and isinstance(cell, (str, int)):
                        try:
                            cell_str = str(cell).strip()
                            # Try to convert to integer
                            week_num = int(cell_str)
                            if 1 <= week_num <= 53:  # Valid week number
                                if start_col == -1:
                                    start_col = j
                                potential_weeks.append((j, week_num))
                        except ValueError:
                            # If not an integer, check if it's a date format
                            pass
                
                if len(potential_weeks) >= 2:  # Found at least 2 week numbers
                    week_row_idx = i
                    week_cols = [col for col, _ in potential_weeks]
                    week_numbers = [week for _, week in potential_weeks]
                    print(f"Found week numbers in row {i+1}: {week_numbers} at columns {week_cols}")
                    break
        
        if week_row_idx == -1:
            # If we can't find a week row, use a fallback approach assuming columns 2+ are weeks
            print("Could not find week numbers row, using columns 2+ as default weeks")
            if len(data[0]) > 2:
                week_cols = list(range(2, len(data[0])))
                week_numbers = list(range(1, len(week_cols) + 1))
            else:
                print("Error: Data doesn't have enough columns")
                return pd.DataFrame()
        
        # Process the data rows
        records = []
        skip_rows = week_row_idx + 1  # Skip header rows
        
        # Process each row in the data
        row_idx = 0
        while row_idx < len(data):
            row = data[row_idx]
            row_idx += 1
            
            if row_idx <= skip_rows or not row or len(row) < 2:
                continue
            
            # Check if this is a category header or a data row
            category_name = row[0].strip() if row[0] else ""
            
            # Check if it's a valid row with data
            row_label = row[1].strip() if len(row) > 1 and row[1] else ""
            
            if not row_label:
                continue
                
            if row_label.startswith("Mål:"):
                # This is a goal (Mål) row
                metric_category = row_label.replace("Mål:", "").strip()
                row_type = "Mål"
                print(f"Found Goal row for: {metric_category}")
                
                # Process values for each week
                for col_idx, week_num in zip(week_cols, week_numbers):
                    if col_idx < len(row) and row[col_idx] and row[col_idx] != '':
                        value = row[col_idx]
                        try:
                            # Handle different number formats
                            if isinstance(value, str):
                                value = value.replace(',', '.').replace(' ', '')
                                
                            # Convert to float, skip empty cells or explicit '0' values
                            if value != 0 and value != '0':
                                numeric_value = float(value)
                                records.append({
                                    "Date": int(week_num), 
                                    "Category": metric_category, 
                                    "Type": row_type, 
                                    "Value": numeric_value
                                })
                                print(f"  - Added record: Date={week_num}, Category={metric_category}, Type={row_type}, Value={numeric_value}")
                        except (ValueError, TypeError) as e:
                            print(f"  - Skipping value '{value}': {e}")
                
            elif row_label.startswith("Utfall:"):
                # This is an outcome (Utfall) row
                metric_category = row_label.replace("Utfall:", "").strip()
                row_type = "Utfall"
                print(f"Found Outcome row for: {metric_category}")
                
                # Process values for each week
                for col_idx, week_num in zip(week_cols, week_numbers):
                    if col_idx < len(row) and row[col_idx] and row[col_idx] != '':
                        value = row[col_idx]
                        try:
                            # Handle different number formats
                            if isinstance(value, str):
                                value = value.replace(',', '.').replace(' ', '')
                                
                            # Convert to float, skip empty cells or explicit '0' values
                            if value != 0 and value != '0':
                                numeric_value = float(value)
                                records.append({
                                    "Date": int(week_num), 
                                    "Category": metric_category, 
                                    "Type": row_type, 
                                    "Value": numeric_value
                                })
                                print(f"  - Added record: Date={week_num}, Category={metric_category}, Type={row_type}, Value={numeric_value}")
                        except (ValueError, TypeError) as e:
                            print(f"  - Skipping value '{value}': {e}")
            
            # Also check for rows without the prefix but matching known metrics
            else:
                # Known metrics that might not have prefixes
                known_metrics = [
                    "Försäljning SEK", "Utgifter SEK", "Resultat SEK",
                    "Bokade möten", "Git commits", "Artiklar Hemsida (SEO)",
                    "Gratis verktyg hemsida (SEO)", "Skickade E-post",
                    "Färdiga moment produktion", "Långa YT videos", "Korta YT videos"
                ]
                
                if any(metric in row_label for metric in known_metrics):
                    # Try to determine if it's a goal or outcome based on position
                    # Typically goals are first, outcomes second
                    is_goal = True  # Default to goal if we can't tell
                    
                    # Check next row if possible
                    if row_idx + 1 < len(data) and data[row_idx + 1] and len(data[row_idx + 1]) > 1:
                        next_label = data[row_idx + 1][1].strip() if data[row_idx + 1][1] else ""
                        if next_label and row_label == next_label:
                            # This is likely the first of a pair (goal)
                            is_goal = True
                        elif row_idx > 0 and data[row_idx - 1] and len(data[row_idx - 1]) > 1:
                            prev_label = data[row_idx - 1][1].strip() if data[row_idx - 1][1] else ""
                            if prev_label and row_label == prev_label:
                                # This is likely the second of a pair (outcome)
                                is_goal = False
                    
                    row_type = "Mål" if is_goal else "Utfall"
                    metric_category = row_label
                    print(f"Found {row_type} row for: {metric_category} (inferred)")
                    
                    # Process values for each week
                    for col_idx, week_num in zip(week_cols, week_numbers):
                        if col_idx < len(row) and row[col_idx] and row[col_idx] != '':
                            value = row[col_idx]
                            try:
                                # Handle different number formats
                                if isinstance(value, str):
                                    value = value.replace(',', '.').replace(' ', '')
                                    
                                # Convert to float, skip empty cells or explicit '0' values
                                if value != 0 and value != '0':
                                    numeric_value = float(value)
                                    records.append({
                                        "Date": int(week_num), 
                                        "Category": metric_category, 
                                        "Type": row_type, 
                                        "Value": numeric_value
                                    })
                                    print(f"  - Added record: Date={week_num}, Category={metric_category}, Type={row_type}, Value={numeric_value}")
                            except (ValueError, TypeError) as e:
                                print(f"  - Skipping value '{value}': {e}")
        
        if not records:
            print("Warning: No valid records found after processing")
            return pd.DataFrame()
            
        print(f"Successfully created {len(records)} records")
        df = pd.DataFrame(records)
        
        # Debug: Print a sample of the DataFrame
        print("\nSample of processed data:")
        print(df.head(10))
        
        return df 