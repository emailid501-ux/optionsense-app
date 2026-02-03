"""Test Google Finance scraping for TATASTEEL"""
import requests
import re

url = 'https://www.google.com/finance/quote/TATASTEEL:NSE'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

print(f"Fetching: {url}")
r = requests.get(url, headers=headers, timeout=10)
print(f"Status: {r.status_code}")

html = r.text

# Check for price using the regex
price_match = re.search(r'class="YMlKec fxKbKc">([0-9,.]+)<', html)
print(f"Price match result: {price_match}")

if price_match:
    price = float(price_match.group(1).replace(',', ''))
    print(f"✅ TATASTEEL Price: ₹{price}")
else:
    # Try alternative regex
    print("Trying alternative...")
    alt_match = re.search(r'data-last-price="([0-9.]+)"', html)
    if alt_match:
        print(f"Alt price: {alt_match.group(1)}")
    else:
        # Save HTML for inspection
        with open("debug_html.txt", "w", encoding="utf-8") as f:
            f.write(html[:10000])
        print("❌ No price found. Saved first 10KB of HTML to debug_html.txt")
