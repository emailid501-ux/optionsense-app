"""Check ICICIBANK price from multiple sources"""
import requests
from live_data import fetch_google_finance_data

symbol = "ICICIBANK"

print(f"Checking {symbol}...")
print("=" * 40)

# 1. Google Finance
gf = fetch_google_finance_data(symbol)
gf_price = gf.get('price', 'N/A') if gf else 'N/A'
print(f"Google Finance: ₹{gf_price}")

# 2. Our API
try:
    r = requests.get(f"http://localhost:8000/stock/{symbol}", timeout=10)
    if r.status_code == 200:
        d = r.json()
        print(f"Our API:        ₹{d.get('price')}")
        print(f"Change:         {d.get('change_pct')}%")
    else:
        print(f"API Error: {r.status_code}")
except Exception as e:
    print(f"API Error: {e}")

# 3. Moneycontrol for reference
print("\n--- Moneycontrol Reference ---")
print("Check: https://www.moneycontrol.com/india/stockpricequote/banks-private-sector/icaboratoriesbank/ICI02")
