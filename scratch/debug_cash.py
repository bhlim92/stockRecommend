import sys
sys.path.insert(0, '.')
from app.gspread_fetcher import fetch_portfolio_holdings

holdings = fetch_portfolio_holdings()
cash_items = [h for h in holdings if h.get('asset_class') == 'cash' or h.get('ticker') == 'CASH']

print("=== CASH items ===")
for h in cash_items:
    print(h)

print()
print("=== ALL items summary ===")
for h in holdings:
    ticker = h['ticker']
    ac = h.get('asset_class', '?')
    qty = h['quantity']
    ev = h['total_evaluation']
    tp = h['total_purchase']
    print(f"{ticker:20} {ac:12} qty={qty:15,.0f} eval={ev:15,.0f} purchase={tp:15,.0f}")
