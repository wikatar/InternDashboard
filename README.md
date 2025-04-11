# The Balthazar Project Dashboard

A Seaborn-based dashboard for visualizing data from The Balthazar Project Google Sheet. This dashboard is designed to be a daily check-in tool to help identify pain points by comparing goals ("Mål") against outcomes ("Utfall").

## Features

- Direct connection to your Google Sheet
- Visualization of goals vs. outcomes
- Categorized metrics:
  - Financial Metrics (Sales, Expenses)
  - Productivity Metrics (Meetings, Git Commits, etc.)
  - Content Metrics (YouTube Videos)
  - Additional Statistics (YouTube, Website, Email, Customers)
- Daily tracking with the possibility to expand to monthly views
- Interactive Streamlit interface

## Setup

### Prerequisites

- Python 3.7 or higher
- A Google Sheet with The Balthazar Project data
- Google Sheets API credentials (service account)

### Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/balthazar-dashboard.git
   cd balthazar-dashboard
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Set up Google Sheets API:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable the Google Sheets API
   - Create a service account and download the JSON credentials file
   - Share your Google Sheet with the service account email address (with Editor permissions)

## Usage

1. Run the Streamlit app:
   ```
   streamlit run app.py
   ```

2. In the app:
   - Upload your Google API credentials JSON file
   - Enter your Google Sheet name (e.g., "The Balthazar Project Dashboard")
   - Click "Fetch Data"
   - Explore your data through the dashboard

## Data Structure

The dashboard expects your Google Sheet to have the following structure:

- Days (15-27) as columns
- Categories with "Mål" (goals) and "Utfall" (outcomes) as rows
- Additional statistics in a section labeled "Övrig relevant statistik"

Example:
```
                | 15 | 16 | 17 | ... | 27 |
--------------------------------------------|
Mål: Sales      | 0  | 5000 | 5000 | ... |
Utfall: Sales   | 0  | 0    | 3000 | ... |
Mål: Expenses   | 0  | 1000 | 1000 | ... |
Utfall: Expenses| 0  | 500  | 700  | ... |
...
```

## Future Enhancements

- Monthly aggregation views
- Export capabilities
- Automated insights
- Trend analysis
- Customizable thresholds for identifying pain points

## License

MIT

## Acknowledgments

- Seaborn for visualization
- Streamlit for the interactive interface
- Pandas for data manipulation 