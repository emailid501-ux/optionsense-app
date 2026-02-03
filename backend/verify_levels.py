"""Verify Entry/Target/SL are now correct"""
import requests

symbol = "TATASTEEL"
r = requests.get(f"http://localhost:8000/stock/{symbol}", timeout=15)

if r.status_code == 200:
    d = r.json()
    price = d.get('price', 0)
    levels = d.get('trading_levels', {})
    
    print(f"TATASTEEL Price: Rs.{price}")
    print(f"Entry:    Rs.{levels.get('entry', 0)}")
    print(f"Target:   Rs.{levels.get('target', 0)}")
    print(f"Stoploss: Rs.{levels.get('stoploss', 0)}")
    print(f"R:R: {levels.get('risk_reward', 'N/A')}")
    
    # Verify Entry is near current price
    entry = levels.get('entry', 0)
    if entry > 0 and abs(entry - price) / price < 0.02:  # Within 2%
        print("\n✅ Entry is near current price - CORRECT!")
    else:
        print(f"\n❌ Entry ({entry}) is NOT near price ({price}) - WRONG!")
else:
    print(f"API Error: {r.status_code}")
