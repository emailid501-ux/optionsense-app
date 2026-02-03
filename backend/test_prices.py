"""Test price accuracy vs Google Finance"""
import requests

API_BASE = "http://localhost:8000"

stocks_to_test = ["TATASTEEL", "RELIANCE", "TCS", "ONGC", "HDFCBANK"]

print("=" * 60)
print("PRICE ACCURACY TEST")
print("=" * 60)

for symbol in stocks_to_test:
    try:
        # 1. Get from our API
        api_response = requests.get(f"{API_BASE}/stock/{symbol}", timeout=15)
        
        if api_response.status_code == 200:
            api_data = api_response.json()
            api_price = api_data.get('price', 'N/A')
            
            # 2. Get directly from Google Finance
            from live_data import fetch_google_finance_data
            gf_data = fetch_google_finance_data(symbol)
            gf_price = gf_data.get('price', 'N/A') if gf_data else 'N/A'
            
            match = "✅ MATCH" if api_price == gf_price else "⚠️ DIFFERENT"
            print(f"{symbol:12} | API: ₹{api_price:>10} | Google: ₹{gf_price:>10} | {match}")
        else:
            print(f"{symbol:12} | API Error: {api_response.status_code}")
            
    except Exception as e:
        print(f"{symbol:12} | Error: {e}")

print("=" * 60)
