"""Direct price check for ICICIBANK"""
import requests

# Get from API
try:
    r = requests.get("http://localhost:8000/stock/ICICIBANK", timeout=15)
    if r.status_code == 200:
        data = r.json()
        print(f"Our API Price:     ₹{data.get('price')}")
        print(f"Our API Change%:   {data.get('change_pct')}%")
    else:
        print(f"API Error: {r.status_code}")
except Exception as e:
    print(f"API Error: {e}")

# Also check TATASTEEL for comparison
try:
    r2 = requests.get("http://localhost:8000/stock/TATASTEEL", timeout=15)
    if r2.status_code == 200:
        d2 = r2.json()
        print(f"\nTATASTEEL API:     ₹{d2.get('price')}")
        print(f"TATASTEEL Change%: {d2.get('change_pct')}%")
except:
    pass
