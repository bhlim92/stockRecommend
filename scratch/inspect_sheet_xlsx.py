import os
import sys
import json
import requests
import io
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scratch.inspect_sheet_auth import AppConfig, Credentials, Request

def main():
    token_json_str = AppConfig.GOOGLE_DRIVE_TOKEN_JSON
    if not token_json_str:
        print("GOOGLE_DRIVE_TOKEN_JSON is not configured in .env")
        return
        
    try:
        creds_info = json.loads(token_json_str)
        creds = Credentials.from_authorized_user_info(creds_info, scopes=['https://www.googleapis.com/auth/drive'])
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing token...")
            creds.refresh(Request())
            
        print("Authenticated. Fetching xlsx export...")
        spreadsheet_id = "19Gtw2QutX6xChSDanqd79edD3WFYVqooeRiHsK8pGdI"
        url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=xlsx"
        
        headers = {"Authorization": f"Bearer {creds.token}"}
        resp = requests.get(url, headers=headers, timeout=20)
        
        if resp.status_code != 200:
            print("Failed to download. Status:", resp.status_code)
            return
            
        print("Download successful. Reading sheets...")
        xlsx_file = io.BytesIO(resp.content)
        
        # Read sheet names using pandas
        xl = pd.ExcelFile(xlsx_file)
        print("Sheet names:", xl.sheet_names)
        
        # Print first few rows of each sheet
        for sheet in xl.sheet_names:
            print(f"\n=== Sheet: {sheet} ===")
            df = xl.parse(sheet)
            print("Shape:", df.shape)
            print("Columns:", df.columns.tolist()[:10])
            print("First 5 rows:")
            # Display all columns to inspect indices
            pd.set_option('display.max_columns', None)
            pd.set_option('display.width', 1000)
            print(df.head(10))
            
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
