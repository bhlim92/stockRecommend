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
            creds.refresh(Request())
            
        spreadsheet_id = "19Gtw2QutX6xChSDanqd79edD3WFYVqooeRiHsK8pGdI"
        url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=xlsx"
        
        headers = {"Authorization": f"Bearer {creds.token}"}
        resp = requests.get(url, headers=headers, timeout=20)
        
        if resp.status_code != 200:
            print("Failed to download. Status:", resp.status_code)
            return
            
        xlsx_file = io.BytesIO(resp.content)
        xl = pd.ExcelFile(xlsx_file)
        
        output_path = "scratch/sheets_info.txt"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"Sheet names: {xl.sheet_names}\n\n")
            for sheet in xl.sheet_names:
                f.write(f"\n==================== Sheet: {sheet} ====================\n")
                df = xl.parse(sheet)
                f.write(f"Shape: {df.shape}\n")
                f.write(f"Columns: {df.columns.tolist()}\n")
                f.write(f"First 30 rows:\n{df.head(30).to_string()}\n")
                
        print("Done. File written to", output_path)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
