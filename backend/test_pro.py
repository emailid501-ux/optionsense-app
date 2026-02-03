"""Quick test of Pro Analysis endpoint"""
import requests

r = requests.get("http://localhost:8000/pro-analysis/NIFTY", timeout=30)
if r.status_code == 200:
    data = r.json()
    print("✅ Pro Analysis API Working!")
    print(f"Symbol: {data.get('symbol')}")
    print(f"Verdict: {data.get('overall_verdict', {}).get('verdict')}")
    print(f"PCR: {data.get('1_pcr', {}).get('pcr')}")
    print(f"VIX: {data.get('3_vix_iv', {}).get('vix')}")
    print(f"Market Breadth: {data.get('7_market_breadth', {}).get('signal')}")
else:
    print(f"❌ Error: {r.status_code}")
