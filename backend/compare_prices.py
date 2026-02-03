"""Simple API vs Google Finance comparison"""
import requests
from live_data import fetch_google_finance_data

symbol = "TATASTEEL"

print(f"Testing {symbol}...")

# 1. Google Finance (direct)
gf = fetch_google_finance_data(symbol)
gf_price = gf.get('price', 'N/A') if gf else 'N/A'
print(f"Google Finance Price: Rs.{gf_price}")

# 2. API endpoint
try:
    r = requests.get(f"http://localhost:8000/stock/{symbol}", timeout=15)
    if r.status_code == 200:
        api_data = r.json()
        api_price = api_data.get('price', 'N/A')
        print(f"API Price: Rs.{api_price}")
        
        if gf_price == api_price:
            print("RESULT: MATCH!")
        else:
            print(f"RESULT: DIFFERENT (API={api_price}, GF={gf_price})")
    else:
        print(f"API Error: {r.status_code}")
except Exception as e:
    print(f"API Error: {e}")
