import os
import json
import csv
import requests
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from app.config import AppConfig
from app.utils.logger import setup_logger

logger = setup_logger("gspread_fetcher", "logs/app.log")

def get_google_credentials():
    """
    Retrieves and refreshes Google credentials using user token or service account.
    """
    scopes = ["https://www.googleapis.com/auth/drive"]
    token_json_str = AppConfig.GOOGLE_DRIVE_TOKEN_JSON
    
    # 1. Try OAuth2 user credentials (token.json string)
    if token_json_str:
        try:
            creds_info = json.loads(token_json_str)
            creds = Credentials.from_authorized_user_info(creds_info, scopes=scopes)
            if creds and creds.expired and creds.refresh_token:
                logger.info("User OAuth2 Token expired. Refreshing token...")
                creds.refresh(Request())
            return creds
        except Exception as e:
            logger.error(f"Failed to load/refresh User OAuth2 credentials: {str(e)}")
            if not AppConfig.GOOGLE_APPLICATION_CREDENTIALS:
                raise e

    # 2. Try service account credentials
    cred_path = AppConfig.GOOGLE_APPLICATION_CREDENTIALS
    if cred_path and os.path.exists(cred_path):
        try:
            creds = service_account.Credentials.from_service_account_file(
                cred_path, scopes=scopes
            )
            return creds
        except Exception as e:
            logger.error(f"Failed to load Service Account credentials: {str(e)}")
            raise e

    raise RuntimeError("No Google credentials configured (neither GOOGLE_DRIVE_TOKEN_JSON nor GOOGLE_APPLICATION_CREDENTIALS).")

def fetch_portfolio_holdings():
    """
    Fetches the portfolio stock list from Google Spreadsheet,
    combining ordinary stock holdings from '매매일지' and pension holdings from '연금매매일지',
    and returns combined parsed data.
    """
    spreadsheet_id = AppConfig.PORTFOLIO_SPREADSHEET_ID
    
    if not spreadsheet_id:
        logger.warning("Portfolio Spreadsheet ID is not configured.")
        return []
        
    try:
        creds = get_google_credentials()
        # Force refresh to make sure token is valid for requests
        if hasattr(creds, "valid") and not creds.valid:
            creds.refresh(Request())
            
        access_token = creds.token
        url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=xlsx"
        
        logger.info("Fetching spreadsheet from Google Drive export URL (format: xlsx)...")
        headers = {"Authorization": f"Bearer {access_token}"}
        resp = requests.get(url, headers=headers, timeout=15)
        
        if resp.status_code != 200:
            logger.error(f"Failed to export spreadsheet. HTTP Status: {resp.status_code}, Response: {resp.text[:200]}")
            raise RuntimeError(f"Failed to fetch spreadsheet. Status code: {resp.status_code}")
            
        import pandas as pd
        import io
        
        xlsx_file = io.BytesIO(resp.content)
        xl = pd.ExcelFile(xlsx_file, engine='openpyxl')
        
        holdings = []
        
        def clean_float(val):
            if pd.isna(val):
                return 0.0
            if isinstance(val, (int, float)):
                return float(val)
            try:
                return float(str(val).replace(",", "").replace("$", "").strip())
            except ValueError:
                return 0.0

        # 1. Parse '매매일지' (Ordinary Stock)
        if '매매일지' in xl.sheet_names:
            df_stock = xl.parse('매매일지', header=None)
            end_idx = min(115, len(df_stock))
            for r_idx in range(1, end_idx):
                row = df_stock.iloc[r_idx].tolist()
                if len(row) <= 3:
                    continue
                    
                qty_val = row[1]
                ticker_val = row[2]
                name_val = row[3]
                
                # Check if it is a cash asset with missing ticker
                is_cash_asset = False
                raw_type = str(row[5]).strip() if len(row) > 5 and not pd.isna(row[5]) else ""
                name_str = str(name_val).strip() if not pd.isna(name_val) else ""
                if "현금" in raw_type or "mmf" in raw_type or "mmf" in name_str.lower() or "현금" in name_str:
                    is_cash_asset = True
                
                if pd.isna(qty_val):
                    continue
                    
                if pd.isna(ticker_val):
                    if is_cash_asset:
                        ticker_val = "CASH"
                    else:
                        continue
                    
                qty_str = str(qty_val).strip()
                ticker = str(ticker_val).strip()
                name = name_str
                
                if not qty_str or not ticker:
                    continue
                    
                qty = clean_float(qty_str)
                if qty <= 0:
                    continue
                    
                raw_type = str(row[5]).strip() if len(row) > 5 and not pd.isna(row[5]) else ""
                # CASH 티커이면 항상 현금으로 분류 (금 조건보다 먼저 확인)
                if ticker == "CASH" or "현금" in raw_type or "mmf" in raw_type.lower() or "mmf" in name.lower() or "현금" in name:
                    asset_class = "cash"
                    asset_type = "현금"
                elif "주식" in raw_type:
                    asset_class = "stock"
                    asset_type = "주식"
                elif "채권" in raw_type:
                    asset_class = "bond"
                    asset_type = "채권"
                elif "금" in raw_type:
                    asset_class = "gold"
                    asset_type = "금"
                elif "원자재" in raw_type:
                    asset_class = "commodity"
                    asset_type = "원자재"
                else:
                    asset_class = "stock"
                    asset_type = "주식"
                    
                current_price = clean_float(row[8]) if len(row) > 8 else 0.0
                purchase_price = clean_float(row[18]) if len(row) > 18 else 0.0
                total_purchase = clean_float(row[19]) if len(row) > 19 else 0.0
                total_evaluation = clean_float(row[20]) if len(row) > 20 else 0.0
                profit = clean_float(row[21]) if len(row) > 21 else 0.0
                
                roi = "0.0%"
                if len(row) > 22 and not pd.isna(row[22]):
                    roi_val = row[22]
                    if isinstance(roi_val, (int, float)):
                        roi = f"{roi_val * 100:.2f}%"
                    else:
                        roi = str(roi_val).strip()
                    
                weight = "0.0%"
                if len(row) > 24 and not pd.isna(row[24]):
                    weight_val = row[24]
                    if isinstance(weight_val, (int, float)):
                        weight = f"{weight_val * 100:.2f}%"
                    else:
                        weight = str(weight_val).strip()
                
                holdings.append({
                    "account_type": "일반주식",
                    "ticker": ticker,
                    "name": name,
                    "quantity": qty,
                    "current_price": current_price,
                    "purchase_price": purchase_price,
                    "total_purchase": total_purchase,
                    "total_evaluation": total_evaluation,
                    "profit": profit,
                    "roi": roi,
                    "weight": weight,
                    "asset_class": asset_class,
                    "asset_type": asset_type
                })
                
        # 2. Parse '연금매매일지' (Pension)
        if '연금매매일지' in xl.sheet_names:
            df_pension = xl.parse('연금매매일지', header=None)
            end_idx = min(115, len(df_pension))
            for r_idx in range(1, end_idx):
                row = df_pension.iloc[r_idx].tolist()
                if len(row) <= 3:
                    continue
                    
                qty_val = row[1]
                ticker_val = row[2]
                name_val = row[3]
                
                # Check if it is a cash asset with missing ticker
                is_cash_asset = False
                raw_type = str(row[5]).strip() if len(row) > 5 and not pd.isna(row[5]) else ""
                name_str = str(name_val).strip() if not pd.isna(name_val) else ""
                if "현금" in raw_type or "mmf" in raw_type or "mmf" in name_str.lower() or "현금" in name_str:
                    is_cash_asset = True
                
                if pd.isna(qty_val):
                    continue
                    
                if pd.isna(ticker_val):
                    if is_cash_asset:
                        ticker_val = "CASH"
                    else:
                        continue
                    
                qty_str = str(qty_val).strip()
                ticker = str(ticker_val).strip()
                name = name_str
                
                if not qty_str or not ticker:
                    continue
                    
                qty = clean_float(qty_str)
                if qty <= 0:
                    continue
                    
                raw_type = str(row[5]).strip() if len(row) > 5 and not pd.isna(row[5]) else ""
                # CASH 티커이면 항상 현금으로 분류 (금 조건보다 먼저 확인)
                if ticker == "CASH" or "현금" in raw_type or "mmf" in raw_type.lower() or "mmf" in name.lower() or "현금" in name:
                    asset_class = "cash"
                    asset_type = "현금"
                elif "주식" in raw_type:
                    asset_class = "stock"
                    asset_type = "주식"
                elif "채권" in raw_type:
                    asset_class = "bond"
                    asset_type = "채권"
                elif "금" in raw_type:
                    asset_class = "gold"
                    asset_type = "금"
                elif "원자재" in raw_type:
                    asset_class = "commodity"
                    asset_type = "원자재"
                else:
                    asset_class = "stock"
                    asset_type = "주식"
                    
                current_price = clean_float(row[8]) if len(row) > 8 else 0.0
                purchase_price = clean_float(row[14]) if len(row) > 14 else 0.0
                total_purchase = clean_float(row[15]) if len(row) > 15 else 0.0
                total_evaluation = clean_float(row[16]) if len(row) > 16 else 0.0
                profit = clean_float(row[17]) if len(row) > 17 else 0.0
                
                roi = "0.0%"
                if len(row) > 18 and not pd.isna(row[18]):
                    roi_val = row[18]
                    if isinstance(roi_val, (int, float)):
                        roi = f"{roi_val * 100:.2f}%"
                    else:
                        roi = str(roi_val).strip()
                    
                weight = "0.0%"
                if len(row) > 21 and not pd.isna(row[21]):
                    weight_val = row[21]
                    if isinstance(weight_val, (int, float)):
                        weight = f"{weight_val * 100:.2f}%"
                    else:
                        weight = str(weight_val).strip()
                
                holdings.append({
                    "account_type": "개인연금",
                    "ticker": ticker,
                    "name": name,
                    "quantity": qty,
                    "current_price": current_price,
                    "purchase_price": purchase_price,
                    "total_purchase": total_purchase,
                    "total_evaluation": total_evaluation,
                    "profit": profit,
                    "roi": roi,
                    "weight": weight,
                    "asset_class": asset_class,
                    "asset_type": asset_type
                })
                
        logger.info(f"Successfully loaded {len(holdings)} holdings (ordinary & pension) from Google Spreadsheet.")
        return holdings
        
    except Exception as e:
        logger.error(f"Error fetching portfolio holdings: {str(e)}")
        raise e
