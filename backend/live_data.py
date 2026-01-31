"""
NSE Live Data Module
Fetches real-time stock data from NSE India
"""

import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import random
from functools import lru_cache
import time

# NSE Headers to avoid blocking
NSE_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
}

# Session for NSE
session = requests.Session()
session.headers.update(NSE_HEADERS)

# Cache for stock list (refresh every 24 hours)
_stock_list_cache = None
_stock_list_cache_time = None

# NIFTY 500 stocks list (sample of major stocks)
NIFTY_STOCKS = [
    # NIFTY 50
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "HINDUNILVR", "SBIN", 
    "BHARTIARTL", "KOTAKBANK", "ITC", "LT", "AXISBANK", "ASIANPAINT", "MARUTI",
    "TITAN", "ULTRACEMCO", "BAJFINANCE", "WIPRO", "SUNPHARMA", "HCLTECH",
    "ONGC", "NTPC", "POWERGRID", "TATAMOTORS", "M&M", "ADANIENT", "ADANIPORTS",
    "COALINDIA", "JSWSTEEL", "TATASTEEL", "TECHM", "NESTLEIND", "BAJAJFINSV",
    "INDUSINDBK", "GRASIM", "DIVISLAB", "BRITANNIA", "HINDALCO", "CIPLA",
    "DRREDDY", "EICHERMOT", "APOLLOHOSP", "SBILIFE", "TATACONSUM", "BPCL",
    "HEROMOTOCO", "BAJAJ-AUTO", "UPL", "SHREECEM", "HDFCLIFE",
    # NIFTY Next 50
    "ADANIGREEN", "AMBUJACEM", "AUROPHARMA", "BANKBARODA", "BERGEPAINT",
    "BIOCON", "BOSCHLTD", "CHOLAFIN", "COLPAL", "DABUR", "DLF", "GAIL",
    "GODREJCP", "HAVELLS", "ICICIGI", "ICICIPRULI", "INDIGO", "IOC",
    "JINDALSTEL", "LICI", "LUPIN", "MARICO", "MCDOWELL-N", "MOTHERSON",
    "MUTHOOTFIN", "NAUKRI", "NMDC", "OBEROIRLTY", "OFSS", "PAGEIND",
    "PIDILITIND", "PNB", "SAIL", "SIEMENS", "SRF", "TATAPOWER", "TORNTPHARM",
    "TRENT", "VEDL", "YESBANK", "ZOMATO", "PAYTM", "POLICYBZR", "DMART",
    "NYKAA", "IRCTC", "HAL", "BEL", "IDEA", "IDFCFIRSTB",
    # Additional Popular Stocks
    "ADANIPOWER", "ATGL", "CANBK", "CONCOR", "FEDERALBNK", "GMRINFRA",
    "IDBI", "IEX", "IRFC", "JIOFIN", "KALYANKJIL", "LODHA", "MAXHEALTH",
    "MCX", "MFSL", "NHPC", "OIL", "PATANJALI", "PEL", "PERSISTENT",
    "PETRONET", "PIIND", "PFC", "POLYCAB", "RECLTD", "SBICARD", "SONACOMS",
    "TATAELXSI", "TIINDIA", "TVSMOTOR", "UNIONBANK", "UBL", "VBL", "VOLTAS",
    "ZYDUSLIFE", "ABB", "ACC", "ABCAPITAL", "AJANTPHARM", "ALKEM",
    "ANGELONE", "ASHOKLEY", "ASTRAL", "ATUL", "AUBANK", "AUROPHARMA",
    "BALKRISIND", "BANDHANBNK", "BDL", "CAMS", "CANFINHOME", "CENTRALBK",
    "CGPOWER", "CROMPTON", "CUMMINSIND", "CYIENT", "DELHIVERY", "DIXON",
    "ESCORTS", "EXIDEIND", "FACT", "FORTIS", "FSL", "GLENMARK", "GNFC",
    "GODREJPROP", "GSPL", "GUJGASLTD", "HDFCAMC", "HEG", "HINDPETRO",
    "CDSL", "BSE", "ANGELONE", "KFINTECH", "CAMS", "SURYODAY",
    "HONAUT", "HUDCO", "IBREALEST", "INDHOTEL", "INDIAMART", "IGL",
    "INDUSTOWER", "INTELLECT", "IPCALAB", "IRB", "ISEC", "ITES", "JBCHEPHARM",
    "JKCEMENT", "JSL", "JUBLFOOD", "KAJARIACER", "KEI", "KPITTECH",
    "L&TFH", "LAURUSLABS", "LICHSGFIN", "LTI", "LTTS", "M&MFIN", "MANAPPURAM",
    "MASTEK", "METROPOLIS", "MGL", "MINDTREE", "MRF", "NAM-INDIA", "NATIONALUM",
    "NAVINFLUOR", "NETWORK18", "NLCINDIA", "NOCIL", "NUVAMA", "OBEROIRLTY"
]

# Cache for last close data (to avoid repeated API calls)
_last_close_cache = None
_last_close_cache_date = None


def fetch_last_close_data() -> List[Dict]:
    """
    Fetch last closing data for NIFTY stocks using jugaad-data.
    This is used when market is closed and real-time data is unavailable.
    """
    global _last_close_cache, _last_close_cache_date
    
    today = datetime.now().date()
    
    # Return cached data if still valid (same day)
    if _last_close_cache and _last_close_cache_date == today:
        return _last_close_cache
    
    stocks_data = []
    
    try:
        from jugaad_data.nse import bhavcopy_save, bhavcopy_fo_save
        from jugaad_data.nse import NSELive
        import pandas as pd
        
        nse = NSELive()
        
        # Try to get index data which includes constituent stocks
        try:
            # Get NIFTY 50 constituents with last close
            nifty_data = nse.trade_info()
            
            # Fall back to getting individual stock data
            # LIMIT to 12 stocks to prevent timeout on initial load
            # We select top stocks + CDSL + BSE
            top_stocks = ["CDSL", "BSE", "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "SBIN", "BHARTIARTL", "ITC", "ANGELONE", "KPITTECH"]
            
            for symbol in top_stocks:
                try:
                    quote = nse.stock_quote(symbol)
                    if quote and 'priceInfo' in quote:
                        price_info = quote['priceInfo']
                        stocks_data.append({
                            'symbol': symbol,
                            'name': quote.get('info', {}).get('companyName', symbol),
                            'price': price_info.get('close', price_info.get('lastPrice', 0)),
                            'change': price_info.get('change', 0),
                            'change_pct': price_info.get('pChange', 0),
                            'open': price_info.get('open', 0),
                            'high': price_info.get('intraDayHighLow', {}).get('max', 0),
                            'low': price_info.get('intraDayHighLow', {}).get('min', 0),
                            'prev_close': price_info.get('previousClose', 0),
                            'volume': 0,
                            'week_52_high': price_info.get('weekHighLow', {}).get('max', 0),
                            'week_52_low': price_info.get('weekHighLow', {}).get('min', 0),
                            'sector': 'Various',
                            'success': True
                        })
                except Exception:
                    continue
        except Exception as e:
            print(f"Error fetching from NSELive: {e}")
        
        if stocks_data:
            _last_close_cache = stocks_data
            _last_close_cache_date = today
            return stocks_data
            
    except ImportError:
        print("jugaad-data not properly installed")
    except Exception as e:
        print(f"Error in fetch_last_close_data: {e}")
    
    return []


def get_nse_session():
    """Initialize NSE session with cookies."""
    try:
        # First hit the main page to get cookies
        session.get("https://www.nseindia.com", timeout=10)
        return True
    except Exception as e:
        print(f"Error initializing NSE session: {e}")
        return False


def get_monthly_expiry(option_data: Dict) -> str:
    """Get the near-month expiry date from option chain data."""
    if not option_data or 'records' not in option_data:
        return ""
    
    expiry_dates = option_data.get('records', {}).get('expiryDates', [])
    if not expiry_dates:
        return ""
        
    # Standard logic: Filter out weekly expiries if stock options (usually Monthly)
    # However, NSE API returns all expiries. For stocks, we usually take the nearest month-end.
    # Simple logic: Take the first expiry that is at least 3 days away (to avoid expiry day volatility)
    # Or just take the nearest one for now.
    
    # Sort dates
    try:
        sorted_dates = sorted(expiry_dates, key=lambda x: datetime.strptime(x, "%d-%b-%Y"))
        
        # Determine current date
        today = datetime.now()
        
        for date_str in sorted_dates:
            exp_date = datetime.strptime(date_str, "%d-%b-%Y")
            if exp_date > today:
                return date_str
                
        return sorted_dates[0] if sorted_dates else ""
        
    except Exception as e:
        print(f"Error parsing expiry dates: {e}")
        return expiry_dates[0] if expiry_dates else ""


def fetch_option_chain(symbol: str) -> Optional[Dict]:
    """
    Fetch option chain for a symbol from NSE.
    """
    try:
        # Use appropriate API based on if it's index or stock
        if symbol in ["NIFTY", "BANKNIFTY", "FINNIFTY"]:
            url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
        else:
            url = f"https://www.nseindia.com/api/option-chain-equities?symbol={symbol}"
            
        response = session.get(url, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            # Try refreshing session
            get_nse_session()
            response = session.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to fetch option chain for {symbol}: {response.status_code}")
                return None
    except Exception as e:
        print(f"Error fetching option chain for {symbol}: {e}")
        return None



def fetch_fallback_quote(symbol: str) -> Optional[Dict]:
    """
    Fetch quote using jugaad-data (NSELive) as fallback.
    """
    try:
        from jugaad_data.nse import NSELive
        nse = NSELive()
        quote = nse.stock_quote(symbol)
        
        if quote and 'priceInfo' in quote:
            price_info = quote['priceInfo']
            return {
                'symbol': symbol,
                'name': quote.get('info', {}).get('companyName', symbol),
                'price': price_info.get('close', price_info.get('lastPrice', 0)),
                'change': price_info.get('change', 0),
                'change_pct': price_info.get('pChange', 0),
                'open': price_info.get('open', 0),
                'high': price_info.get('intraDayHighLow', {}).get('max', 0),
                'low': price_info.get('intraDayHighLow', {}).get('min', 0),
                'prev_close': price_info.get('previousClose', 0),
                'volume': 0,
                'week_52_high': price_info.get('weekHighLow', {}).get('max', 0),
                'week_52_low': price_info.get('weekHighLow', {}).get('min', 0),
                'sector': 'Various',
                'success': True
            }
    except Exception as e:
        print(f"Fallback fetch failed for {symbol}: {e}")
    return None


def fetch_stock_quote(symbol: str) -> Optional[Dict]:
    """
    Fetch live quote for a single stock from NSE.
    Returns stock data with price, change, volume, etc.
    """
    try:
        url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"
        response = session.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            price_info = data.get('priceInfo', {})
            
            return {
                'symbol': symbol,
                'name': data.get('info', {}).get('companyName', symbol),
                'price': price_info.get('lastPrice', 0),
                'change': price_info.get('change', 0),
                'change_pct': price_info.get('pChange', 0),
                'open': price_info.get('open', 0),
                'high': price_info.get('intraDayHighLow', {}).get('max', 0),
                'low': price_info.get('intraDayHighLow', {}).get('min', 0),
                'prev_close': price_info.get('previousClose', 0),
                'volume': data.get('preOpenMarket', {}).get('totalTradedVolume', 0),
                'week_52_high': price_info.get('weekHighLow', {}).get('max', 0),
                'week_52_low': price_info.get('weekHighLow', {}).get('min', 0),
                'sector': data.get('industryInfo', {}).get('sector', 'Unknown'),
                'pe_ratio': data.get('metadata', {}).get('pdSymbolPe', 0),
                'success': True
            }
        else:
            return None
    except Exception as e:
        print(f"Error fetching quote for {symbol}: {e}")
        return None


def fetch_nifty50_stocks() -> List[Dict]:
    """
    Fetch all NIFTY 50 stocks data.
    """
    try:
        url = "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%2050"
        response = session.get(url, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            stocks = []
            
            for item in data.get('data', [])[1:]:  # Skip index row
                stocks.append({
                    'symbol': item.get('symbol', ''),
                    'name': item.get('meta', {}).get('companyName', item.get('symbol', '')),
                    'price': item.get('lastPrice', 0),
                    'change': item.get('change', 0),
                    'change_pct': item.get('pChange', 0),
                    'open': item.get('open', 0),
                    'high': item.get('dayHigh', 0),
                    'low': item.get('dayLow', 0),
                    'prev_close': item.get('previousClose', 0),
                    'volume': item.get('totalTradedVolume', 0),
                    'week_52_high': item.get('yearHigh', 0),
                    'week_52_low': item.get('yearLow', 0),
                    'sector': 'Various',
                    'success': True
                })
            
            return stocks
        else:
            return []
    except Exception as e:
        print(f"Error fetching NIFTY 50 stocks: {e}")
        return []


def fetch_all_equity_stocks() -> List[Dict]:
    """
    Fetch all equity stocks from NSE.
    Uses the equity market data API.
    """
    try:
        # Try to get NIFTY 500 data
        url = "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%20500"
        response = session.get(url, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            stocks = []
            
            for item in data.get('data', [])[1:]:  # Skip index row
                stocks.append({
                    'symbol': item.get('symbol', ''),
                    'name': item.get('meta', {}).get('companyName', item.get('symbol', '')),
                    'price': item.get('lastPrice', 0),
                    'change': item.get('change', 0),
                    'change_pct': item.get('pChange', 0),
                    'open': item.get('open', 0),
                    'high': item.get('dayHigh', 0),
                    'low': item.get('dayLow', 0),
                    'prev_close': item.get('previousClose', 0),
                    'volume': item.get('totalTradedVolume', 0),
                    'week_52_high': item.get('yearHigh', 0),
                    'week_52_low': item.get('yearLow', 0),
                    'sector': item.get('meta', {}).get('industry', 'Various'),
                    'success': True
                })
            
            return stocks
        else:
            # Fallback to NIFTY 50
            return fetch_nifty50_stocks()
    except Exception as e:
        print(f"Error fetching all equity stocks: {e}")
        return fetch_nifty50_stocks()


def calculate_rsi(prices: List[float], period: int = 14) -> float:
    """Calculate RSI from price list."""
    if len(prices) < period + 1:
        return 50  # Default neutral
    
    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]
    
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    
    if avg_loss == 0:
        return 100
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return round(rsi, 1)


def generate_mock_indicators(price: float, change_pct: float, 
                              high_52: float, low_52: float) -> Dict:
    """
    Generate realistic technical indicators based on price data.
    In production, these would be calculated from historical data.
    """
    # Simulate RSI based on position in 52-week range
    if high_52 > low_52:
        position = (price - low_52) / (high_52 - low_52)
        rsi = 30 + (position * 40) + random.uniform(-10, 10)
        rsi = max(15, min(85, rsi))
    else:
        rsi = 50 + random.uniform(-20, 20)
    
    # RSI signal
    if rsi < 30:
        rsi_signal = "OVERSOLD"
    elif rsi > 70:
        rsi_signal = "OVERBOUGHT"
    else:
        rsi_signal = "NEUTRAL"
    
    # MACD signal based on trend
    if change_pct > 1:
        macd = "BULLISH"
    elif change_pct < -1:
        macd = "BEARISH"
    else:
        macd = "NEUTRAL"
    
    # Moving average signals (simulated based on price position)
    above_20dma = change_pct > -0.5
    above_50dma = price > (low_52 + (high_52 - low_52) * 0.3)
    above_200dma = price > (low_52 + (high_52 - low_52) * 0.2)
    
    # Volume surge (simulated)
    volume_surge = 1.0 + random.uniform(-0.5, 1.5)
    
    return {
        'rsi': round(rsi, 1),
        'rsi_signal': rsi_signal,
        'macd': macd,
        'above_20dma': above_20dma,
        'above_50dma': above_50dma,
        'above_200dma': above_200dma,
        'volume_surge': round(volume_surge, 1)
    }


def calculate_fibonacci_levels(price: float, high_52: float, low_52: float) -> Dict:
    """Calculate Fibonacci retracement levels based on 52-week range."""
    swing_high = high_52
    swing_low = low_52
    fib_range = swing_high - swing_low
    
    fib_levels = {
        "swing_high": round(swing_high, 2),
        "swing_low": round(swing_low, 2),
        "fib_236": round(swing_high - fib_range * 0.236, 2),
        "fib_382": round(swing_high - fib_range * 0.382, 2),
        "fib_500": round(swing_high - fib_range * 0.500, 2),
        "fib_618": round(swing_high - fib_range * 0.618, 2),
        "fib_786": round(swing_high - fib_range * 0.786, 2),
    }
    
    # Determine zone and signal
    if price >= fib_levels["fib_236"]:
        fib_zone = "ABOVE_236"
        fib_signal = "BULLISH"
        nearest_support = fib_levels["fib_236"]
        nearest_resistance = fib_levels["swing_high"]
    elif price >= fib_levels["fib_382"]:
        fib_zone = "236_TO_382"
        fib_signal = "BULLISH"
        nearest_support = fib_levels["fib_382"]
        nearest_resistance = fib_levels["fib_236"]
    elif price >= fib_levels["fib_500"]:
        fib_zone = "382_TO_500"
        fib_signal = "NEUTRAL"
        nearest_support = fib_levels["fib_500"]
        nearest_resistance = fib_levels["fib_382"]
    elif price >= fib_levels["fib_618"]:
        fib_zone = "500_TO_618"
        fib_signal = "NEUTRAL"
        nearest_support = fib_levels["fib_618"]
        nearest_resistance = fib_levels["fib_500"]
    elif price >= fib_levels["fib_786"]:
        fib_zone = "618_TO_786"
        fib_signal = "BEARISH"
        nearest_support = fib_levels["fib_786"]
        nearest_resistance = fib_levels["fib_618"]
    else:
        fib_zone = "BELOW_786"
        fib_signal = "BEARISH"
        nearest_support = fib_levels["swing_low"]
        nearest_resistance = fib_levels["fib_786"]
    
    fib_levels["zone"] = fib_zone
    fib_levels["signal"] = fib_signal
    fib_levels["nearest_support"] = nearest_support
    fib_levels["nearest_resistance"] = nearest_resistance
    
    return fib_levels


def get_stock_list() -> List[str]:
    """Get list of available stocks."""
    return NIFTY_STOCKS



# Session initialization is now handled lazily on first request failure
# via fetch_option_chain logic.
# get_nse_session() removed to prevent module import blocking.
