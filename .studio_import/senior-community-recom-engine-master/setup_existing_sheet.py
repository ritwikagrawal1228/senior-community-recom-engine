"""
Setup existing Google Sheet with CRM structure
"""

import gspread
from google.oauth2.service_account import Credentials

def setup_existing_spreadsheet(spreadsheet_id):
    """
    Set up an existing Google Spreadsheet with CRM structure

    Args:
        spreadsheet_id: The ID from the Google Sheets URL
    """
    # Set up credentials
    service_account_file = 'gen-lang-client-0663556503-72ee52ed113f.json'
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    creds = Credentials.from_service_account_file(service_account_file, scopes=scopes)
    client = gspread.authorize(creds)

    print(f"Connecting to spreadsheet...")

    # Open the spreadsheet
    spreadsheet = client.open_by_key(spreadsheet_id)

    print(f"[OK] Connected to: {spreadsheet.title}")
    print(f"[OK] URL: {spreadsheet.url}")

    # Rename first sheet
    sheet1 = spreadsheet.sheet1
    sheet1.update_title('Client Consultations')

    # Create additional sheets
    try:
        spreadsheet.add_worksheet(title='Recommendations Detail', rows=1000, cols=20)
        spreadsheet.add_worksheet(title='Performance Analytics', rows=1000, cols=16)
        print("[OK] Created 3 sheets")
    except:
        print("[OK] Sheets already exist")

    # Set up headers for each sheet
    setup_consultations_sheet(spreadsheet)
    setup_recommendations_sheet(spreadsheet)
    setup_performance_sheet(spreadsheet)

    print("\n" + "="*80)
    print("GOOGLE SHEET SETUP COMPLETE!")
    print("="*80)
    print(f"\nSpreadsheet URL: {spreadsheet.url}")
    print(f"\nSpreadsheet ID: {spreadsheet.id}")
    print("\nAdd this to your .env file:")
    print(f"GOOGLE_SPREADSHEET_ID={spreadsheet.id}")
    print("\n" + "="*80)

    return spreadsheet


def setup_consultations_sheet(spreadsheet):
    """Set up Sheet 1: Client Consultations"""
    sheet = spreadsheet.worksheet('Client Consultations')

    headers = [
        'Consultation_ID',
        'Timestamp',
        'Client_Name',
        'Care_Level',
        'Budget',
        'Timeline',
        'Location_ZIP',
        'Special_Needs',
        'Total_Recommendations',
        'Top_Community_ID',
        'Top_Community_Name',
        'Top_Monthly_Fee',
        'Top_Distance',
        'Top_Score',
        'Top_Reason',
        'Processing_Time',
        'Total_Cost',
        'Status',
        'Assigned_To',
        'Notes'
    ]

    # Set headers
    sheet.update('A1:T1', [headers])

    # Format header row
    sheet.format('A1:T1', {
        'textFormat': {'bold': True},
        'backgroundColor': {'red': 0.2, 'green': 0.5, 'blue': 0.8}
    })

    # Freeze header row
    sheet.freeze(rows=1)

    print("  [OK] Set up 'Client Consultations' sheet")


def setup_recommendations_sheet(spreadsheet):
    """Set up Sheet 2: Recommendations Detail"""
    sheet = spreadsheet.worksheet('Recommendations Detail')

    headers = [
        'Consultation_ID',
        'Client_Name',
        'Rank',
        'Community_ID',
        'Community_Name',
        'Monthly_Fee',
        'Distance_Miles',
        'Availability',
        'Combined_Score',
        'Business_Rank',
        'Cost_Rank',
        'Distance_Rank',
        'Availability_Rank',
        'Holistic_Reason',
        'Contract_Rate',
        'Work_With_Placement',
        'Tour_Scheduled',
        'Tour_Status',
        'Client_Feedback'
    ]

    # Set headers
    sheet.update('A1:S1', [headers])

    # Format header row
    sheet.format('A1:S1', {
        'textFormat': {'bold': True},
        'backgroundColor': {'red': 0.2, 'green': 0.7, 'blue': 0.5}
    })

    # Freeze header row
    sheet.freeze(rows=1)

    print("  [OK] Set up 'Recommendations Detail' sheet")


def setup_performance_sheet(spreadsheet):
    """Set up Sheet 3: Performance Analytics"""
    sheet = spreadsheet.worksheet('Performance Analytics')

    headers = [
        'Date',
        'Consultation_ID',
        'Processing_Time_Seconds',
        'Audio_Input_Tokens',
        'Text_Input_Tokens',
        'Output_Tokens',
        'Total_Tokens',
        'API_Calls',
        'Audio_Input_Cost',
        'Text_Input_Cost',
        'Output_Cost',
        'Total_Cost',
        'Throughput_Tokens_Per_Sec',
        'Communities_Filtered',
        'Communities_Ranked'
    ]

    # Set headers
    sheet.update('A1:O1', [headers])

    # Format header row
    sheet.format('A1:O1', {
        'textFormat': {'bold': True},
        'backgroundColor': {'red': 0.8, 'green': 0.5, 'blue': 0.2}
    })

    # Freeze header row
    sheet.freeze(rows=1)

    print("  [OK] Set up 'Performance Analytics' sheet")


if __name__ == "__main__":
    # Your spreadsheet ID from the URL
    SPREADSHEET_ID = "1gNMRRR4nsxe3M4Olz7_QP7DN4f3d3HZDjUvwjKeTPng"

    print("\n" + "="*80)
    print("SETTING UP YOUR GOOGLE SHEET")
    print("="*80 + "\n")

    setup_existing_spreadsheet(SPREADSHEET_ID)

    print("\nDONE! Your Google Sheet is ready to use.")
    print("\nNext: Test the integration with:")
    print("  python -c \"from google_sheets_integration import push_to_crm; print('Ready!')\"")
