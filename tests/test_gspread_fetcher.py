import pytest
from unittest.mock import patch, MagicMock
import io
import pandas as pd
from app.gspread_fetcher import fetch_portfolio_holdings

def get_mock_xlsx_content():
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Create sheet '매매일지'
        stock_data = [
            # Header
            ['투자금액비중', '보유', 'Ticker', '설명', '', '타입', '', '', '현재가격', '', '', '', '', '', '', '', '', '', '구매가', '투자금액', '평가금액', '수익', '수익률', '', '비중'],
            # Row 1: AAPL (qty = 0)
            [0.0, 0, 'AAPL', 'Apple Inc.', '', '주식', '', '', 315.2, '', '', '', '', '', '', '', '', '', 209.87, 0.0, 0.0, 0.0, 0.0, '', 0.0],
            # Row 2: JPM (qty = 5.5)
            [0.0581, 5.5, 'JPM', 'JP Morgan Chase & Co.', '', '주식', '', '', 300.96, '', '', '', '', '', '', '', '', '', 287.93, 1583.62, 1655.28, 71.67, 0.0453, '', 0.0581]
        ]
        df_stock = pd.DataFrame(stock_data)
        df_stock.to_excel(writer, sheet_name='매매일지', index=False, header=False)
        
        # Create sheet '연금매매일지'
        pension_data = [
            # Header
            ['투자금액비중', '보유', 'Ticker', '설명', '', '타입', '', '', '현재가격', '', '', '', '', '', '구매가', '투자금액', '평가금액', '수익', '수익률', '', '', '평가비중'],
            # Row 1: 448290.ks (qty = 1964)
            [0.287298, 1964, '448290.ks', 'TIGER 미국S&P500(H)', '', '주식', '', '', 17570.0, '', '', '', '', '', 15731, 30895684, 34507480.0, 3611796.0, 0.116903, '', '', 0.287298]
        ]
        df_pension = pd.DataFrame(pension_data)
        df_pension.to_excel(writer, sheet_name='연금매매일지', index=False, header=False)
        
    return output.getvalue()

@patch("app.gspread_fetcher.get_google_credentials")
@patch("app.gspread_fetcher.requests.get")
def test_fetch_portfolio_holdings(mock_get, mock_creds):
    # Set up mock credentials
    mock_credential_obj = MagicMock()
    mock_credential_obj.token = "mock-access-token"
    mock_creds.return_value = mock_credential_obj
    
    # Set up mock response
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = get_mock_xlsx_content()
    mock_get.return_value = mock_resp
    
    # Execute fetch
    holdings = fetch_portfolio_holdings()
    
    # Verify outputs
    # 1 from stock (AAPL is 0), 1 from pension
    assert len(holdings) == 2
    
    # Check JPM (ordinary stock)
    jpm = holdings[0]
    assert jpm["account_type"] == "일반주식"
    assert jpm["ticker"] == "JPM"
    assert jpm["name"] == "JP Morgan Chase & Co."
    assert jpm["quantity"] == 5.5
    assert jpm["current_price"] == 300.96
    assert jpm["purchase_price"] == 287.93
    assert jpm["total_purchase"] == 1583.62
    assert jpm["total_evaluation"] == 1655.28
    assert jpm["profit"] == 71.67
    assert jpm["roi"] == "4.53%"
    assert jpm["weight"] == "5.81%"
    
    # Check 448290.ks (pension)
    sp500 = holdings[1]
    assert sp500["account_type"] == "개인연금"
    assert sp500["ticker"] == "448290.ks"
    assert sp500["name"] == "TIGER 미국S&P500(H)"
    assert sp500["quantity"] == 1964
    assert sp500["current_price"] == 17570.0
    assert sp500["purchase_price"] == 15731.0
    assert sp500["total_purchase"] == 30895684.0
    assert sp500["total_evaluation"] == 34507480.0
    assert sp500["profit"] == 3611796.0
    assert sp500["roi"] == "11.69%"
    assert sp500["weight"] == "28.73%"
