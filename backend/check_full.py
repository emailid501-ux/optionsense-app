"""Full ICICIBANK response"""
import requests
import json

r = requests.get("http://localhost:8000/stock/ICICIBANK", timeout=15)
if r.status_code == 200:
    data = r.json()
    print("ICICIBANK Full Data:")
    print(f"Price: {data.get('price')}")
    print(f"Change: {data.get('change_pct')}%")
    print(f"Entry: {data.get('trading_levels', {}).get('entry')}")
    print(f"Target: {data.get('trading_levels', {}).get('target')}")
    print(f"Stoploss: {data.get('trading_levels', {}).get('stoploss')}")
else:
    print(f"Error: {r.status_code}")
