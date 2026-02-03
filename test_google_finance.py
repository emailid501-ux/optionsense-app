
import requests
import re

def get_google_finance_price(symbol, google_symbol):
    url = f"https://www.google.com/finance/quote/{google_symbol}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        print(f"Fetching {url}...")
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"Failed: HTTP {response.status_code}")
            return None
            
        html = response.text
        
        # Pattern to find price in "YMlKec fxKbKc" class usually used by Google Finance
        # Or look for currency symbol followed by numbers
        # The class specific to big price is often "YMlKec fxKbKc"
        
        # Regex for price inside the specific div
        # <div class="YMlKec fxKbKc">25,334.10</div>
        match = re.search(r'class="YMlKec fxKbKc">([0-9,.]+)<', html)
        
        if match:
            price_str = match.group(1).replace(',', '')
            price = float(price_str)
            print(f"SUCCESS: Found price for {symbol}: {price}")
            return price
        else:
            print("Price pattern not found in HTML")
            # debug: save html to check
            # with open("debug_gf.html", "w", encoding="utf-8") as f: f.write(html)
            return None

    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    get_google_finance_price("NIFTY", "NIFTY_50:INDEXNSE")
    get_google_finance_price("BANKNIFTY", "NIFTY_BANK:INDEXNSE")
