"""
NSE Live Data Module
Fetches real-time stock data from NSE India
"""

import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta, time as dt_time
import random
from functools import lru_cache
import time
import re
import concurrent.futures
import pytz
import numpy as np
import json

# Configure local timezone
IST = pytz.timezone('Asia/Kolkata')

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

def _init_session():
    """Initialize session by visiting homepage to get cookies."""
    try:
        session.get("https://www.nseindia.com", timeout=10)
        print("NSE Session initialized with cookies")
    except Exception as e:
        print(f"Error initializing NSE session: {e}")

# Initialize session immediately
_init_session()

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
    # NIFTY 200 & Popular Stocks
    "ADANIPOWER", "ATGL", "CANBK", "CONCOR", "FEDERALBNK", "GMRINFRA",
    "IDBI", "IEX", "IRFC", "JIOFIN", "KALYANKJIL", "LODHA", "MAXHEALTH",
    "MCX", "MFSL", "NHPC", "OIL", "PATANJALI", "PEL", "PERSISTENT",
    "PETRONET", "PIIND", "PFC", "POLYCAB", "RECLTD", "SBICARD", "SONACOMS",
    "TATAELXSI", "TIINDIA", "TVSMOTOR", "UNIONBANK", "UBL", "VBL", "VOLTAS",
    "ZYDUSLIFE", "ABB", "ACC", "ABCAPITAL", "AJANTPHARM", "ALKEM",
    "ANGELONE", "ASHOKLEY", "ASTRAL", "ATUL", "AUBANK",
    "BALKRISIND", "BANDHANBNK", "BDL", "CAMS", "CANFINHOME", "CENTRALBK",
    "CGPOWER", "CROMPTON", "CUMMINSIND", "CYIENT", "DELHIVERY", "DIXON",
    "ESCORTS", "EXIDEIND", "FACT", "FORTIS", "FSL", "GLENMARK", "GNFC",
    "GODREJPROP", "GSPL", "GUJGASLTD", "HDFCAMC", "HEG", "HINDPETRO",
    "CDSL", "BSE", "KFINTECH", "SURYODAY",
    "HONAUT", "HUDCO", "IBREALEST", "INDHOTEL", "INDIAMART", "IGL",
    "INDUSTOWER", "INTELLECT", "IPCALAB", "IRB", "ISEC", "JBCHEPHARM",
    "JKCEMENT", "JSL", "JUBLFOOD", "KAJARIACER", "KEI", "KPITTECH",
    "LAURUSLABS", "LICHSGFIN", "LTTS", "MANAPPURAM",
    "MASTEK", "METROPOLIS", "MGL", "MRF", "NATIONALUM",
    "NAVINFLUOR", "NLCINDIA", "NUVAMA",
    # Additional NIFTY 500 Stocks
    "AIAENG", "AFFLE", "AARTIIND", "ABSLAMC", "AEGISLOG", "AHLUCONT",
    "AMARAJABAT", "AMBER", "ANURAS", "APTUS", "ARE&M", "ASAHIINDIA",
    "ATGL", "AVADHSUGAR", "AVANTIFEED", "BAJAJELEC", "BAJAJHLDNG", "BALRAMCHIN",
    "BASF", "BATAINDIA", "BCG", "BEML", "BHARATFORG", "BIRLACORPN",
    "BLUEDART", "BLUESTARCO", "BRIGADE", "BSOFT", "CARBORUNIV", "CASTROLIND",
    "CCL", "CESC", "CHALET", "CHAMBLEFERT", "CHENNPETRO", "CIE", "CLEAN",
    "COFORGE", "COROMANDEL", "CREDITACC", "CRISIL", "CSBBANK", "DATAPATTNS",
    "DCMSHRIRAM", "DEEPAKFERT", "DEEPAKNTR", "DEVYANI", "DHANI", "DHANUKA",
    "DISHTV", "DOMS", "ECLERX", "EDELWEISS", "ELECON", "ELGIEQUIP",
    "EMAMILTD", "EMCURE", "ENGINERSIN", "EPIGRAL", "EQUITASBNK", "ERIS",
    "FINEORG", "FIRSTSOUR", "FIVESTAR", "FLUOROCHEM", "GATEWAY", "GDL",
    "GENESYS", "GILLETTE", "GLAXO", "GLOBALBEES", "GMDCLTD", "GODFRYPHLP",
    "GOLDIAM", "GOODYEAR", "GRANULES", "GRAPHITE", "GRINDWELL", "GSFC",
    "GRSE", "HAPPSTMNDS", "HBLPOWER", "HDFCAMC", "HERITGFOOD", "HFCL",
    "HINDCOPPER", "HINDOILEXP", "HINDZINC", "HLEGLAS", "HOMEFIRST", "IBULHSGFIN",
    "IDFC", "IIFL", "IIFLSEC", "INDIGOPNTS", "INDOSTAR", "INFIBEAM",
    "INOXWIND", "IONEXCHANG", "JAMNAAUTO", "JBMA", "JINDALSAW", "JKLAKSHMI",
    "JKPAPER", "JKTYRE", "JMFINANCIL", "JOVEES", "JUSTDIAL", "JYOTHYLAB",
    "KALYANI", "KARURVYSYA", "KAYNES", "KIMS", "KIRLOSENG", "KIRLPNU",
    "KNRCON", "KOLTEPATIL", "KPRMILL", "KRBL", "KTKBANK", "LATENTVIEW",
    "LAXMIMACH", "LEMONTREE", "LXCHEM", "MAHABANK", "MAHLIFE", "MAHLOG",
    "MAHSEAMLES", "MAPMYINDIA", "MASFIN", "MAXHEALTH", "MAZAGON", "MEDPLUS",
    "MIDHANI", "MMTC", "MOIL", "MPHASIS", "MSTCLTD", "MTARTECH",
    "NAM-INDIA", "NATCOPHARM", "NESCO", "NEWGEN", "NFL", "OLECTRA",
    "ORIENTELEC", "ORIENTPPR", "PGHH", "PHOENIXLTD", "PNBHOUSING", "PRINCEPIPE",
    "PRSMJOHNSN", "PSB", "PSPPROJECT", "QUESS", "RADICO", "RAJRATAN",
    "RALLIS", "RAMCOCEM", "RKFORGE", "ROSSARI", "ROUTE", "RVNL",
    "SAFARI", "SAGCEM", "SANDUMA", "SANOFI", "SAPPHIRE", "SARDAEN",
    "SCHNEIDER", "SEQUENT", "SHARDACROP", "SHILPAMED", "SHOPERSTOP", "SIS",
    "SJVN", "SKFINDIA", "SOBHA", "SOLARINDS", "SOLARA", "SONATSOFTW",
    "SPARC", "SPIC", "STARCEMENT", "STAR", "SUNTV", "SUPRAJIT", "SUPREMEIND"
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
            # Use first 200 stocks from NIFTY_STOCKS for comprehensive coverage
            top_stocks = NIFTY_STOCKS[:200]
            print(f"Fetching data for {len(top_stocks)} stocks in parallel...")
            
            import concurrent.futures
            
            def fetch_stock_data(symbol):
                try:
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
                    # print(f"Error fetching {symbol}: {e}")
                    pass
                return None

            # Use ThreadPoolExecutor for parallel fetching
            with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
                future_to_symbol = {executor.submit(fetch_stock_data, sym): sym for sym in top_stocks}
                for i, future in enumerate(concurrent.futures.as_completed(future_to_symbol)):
                    result = future.result()
                    if result:
                        stocks_data.append(result)
                    
                    # Optional: Print progress every 50 stocks
                    if (i + 1) % 50 == 0:
                        print(f"Fetched {i + 1}/{len(top_stocks)} stocks...")
                        
            print(f"Completed fetching {len(stocks_data)} stocks.")
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
        if symbol in ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"]:
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


# ===== PHASE 15: Advanced Trading Indicators =====

def fetch_india_vix() -> Dict:
    """
    Fetch India VIX (Volatility Index).
    VIX < 15: Low volatility - Good for option buying
    VIX 15-18: Moderate volatility
    VIX > 18: High volatility - Good for option selling
    """
    try:
        from jugaad_data.nse import NSELive
        nse = NSELive()
        
        # Try to get VIX from indices
        try:
            vix_data = nse.index_quote("INDIA VIX")
            if vix_data and 'lastPrice' in vix_data:
                vix_value = float(vix_data['lastPrice'])
            else:
                vix_value = 14.5  # Default fallback
        except:
            vix_value = 14.5  # Default fallback
        
        # Determine status
        if vix_value < 13:
            status = "VERY_LOW"
            action = "Strong Option Buying Zone"
            color = "GREEN"
        elif vix_value < 15:
            status = "LOW"
            action = "Option Buying OK"
            color = "GREEN"
        elif vix_value < 18:
            status = "MODERATE"
            action = "Be Cautious"
            color = "YELLOW"
        elif vix_value < 22:
            status = "HIGH"
            action = "Option Selling Preferred"
            color = "ORANGE"
        else:
            status = "VERY_HIGH"
            action = "Extreme Caution - Avoid Trading"
            color = "RED"
        
        return {
            "value": round(vix_value, 2),
            "status": status,
            "action": action,
            "color": color
        }


    except Exception as e:
        print(f"VIX fetch error: {e}")
        return {"value": 14.5, "status": "UNKNOWN", "action": "Data Unavailable", "color": "GREY"}


def fetch_technical_signals(symbol: str) -> Dict:
    """
    Fetch/Calculate technical signals for the dashboard.
    Returns VWAP, PCR, Sentiment, Verdict.
    """
    try:
        # Calculate PCR from option chain
        pcr_value = 1.0 # Default
        
        # Try to calculate real PCR if possible, or use simplified trend
        option_chain = fetch_option_chain(symbol)
        if option_chain:
            total_ce_oi = option_chain.get('filtered', {}).get('CE', {}).get('totOI', 0)
            total_pe_oi = option_chain.get('filtered', {}).get('PE', {}).get('totOI', 0)
            
            if total_ce_oi > 0:
                pcr_value = round(total_pe_oi / total_ce_oi, 2)
        
        # Determine sentiment based on PCR
        sentiment_score = 5
        verdict = "NEUTRAL"
        recommendation = "Wait for clear direction"
        
        if pcr_value > 1.2:
            sentiment_score = 8
            verdict = "STRONG BUY"
            recommendation = "Look for Buying Opportunities"
        elif pcr_value < 0.8:
            sentiment_score = 3
            verdict = "STRONG SELL"
            recommendation = "Look for Selling Opportunities"
        
        # Mock VWAP (since we don't have intraday candles easily)
        # In a real app, this would come from a candle API
        # We'll make VWAP slightly below price if Bullish, above if Bearish
        current_price = 0
        if option_chain:
             current_price = option_chain.get('records', {}).get('underlyingValue', 0)
        
        if current_price == 0:
             # Try fallback price
             pass

        vwap_value = current_price * 0.998 if pcr_value > 1 else current_price * 1.002
        
        return {
            "vwap": round(vwap_value, 2),
            "pcr": pcr_value,
            "sentiment_score": sentiment_score,
            "verdict": verdict,
            "recommendation": recommendation
        }

    except Exception as e:
        print(f"Error fetching signals: {e}")
        return {
            "vwap": 0,
            "pcr": 1.0,
            "sentiment_score": 5,
            "verdict": "NEUTRAL",
            "recommendation": "Data Unavailable"
        }

# ===== MONEYCONTROL LIVE DATA (PRIMARY SOURCE) =====

# Moneycontrol Index IDs
MC_INDEX_IDS = {
    "NIFTY": "in;NSX",
    "NIFTY50": "in;NSX",
    "NIFTY 50": "in;NSX",
    # Bank NIFTY, FINNIFTY not available in Moneycontrol priceapi
}

# Moneycontrol Stock Symbol Mapping (NSE Symbol -> MC ID)
MC_STOCK_IDS = {
    # NIFTY 50 Top Stocks
    "RELIANCE": "RI", "TCS": "TCS", "HDFCBANK": "HDF01", "INFY": "IT",
    "ICICIBANK": "ICI02", "HINDUNILVR": "HU", "SBIN": "SBI", "BHARTIARTL": "BA08",
    "KOTAKBANK": "KMB", "ITC": "ITC", "LT": "LT", "AXISBANK": "AB16",
    "ASIANPAINT": "APLH", "MARUTI": "MS24", "TITAN": "TIT", "ULTRACEMCO": "UCM",
    "BAJFINANCE": "BAF", "WIPRO": "W", "SUNPHARMA": "SPLO6", "HCLTECH": "HCL02",
    "ONGC": "ONG", "NTPC": "NTP", "POWERGRID": "PGC", "TATAMOTORS": "TM04",
    "M&M": "MM", "ADANIENT": "AE06", "ADANIPORTS": "APSE", "COALINDIA": "CI",
    "JSWSTEEL": "JSW01", "TATASTEEL": "TSC", "TECHM": "TM4", "NESTLEIND": "NES",
    "BAJAJFINSV": "BF04", "INDUSINDBK": "IIB", "GRASIM": "GI02", "DIVISLAB": "DLA",
    "BRITANNIA": "BRI03", "HINDALCO": "HAL", "CIPLA": "C", "DRREDDY": "DRR",
    "EICHERMOT": "EIM3", "APOLLOHOSP": "AHE1", "SBILIFE": "SLICS", "TATACONSUM": "TC",
    "BPCL": "BPC", "HEROMOTOCO": "HHM", "BAJAJ-AUTO": "BJP", "UPL": "UPL04",
    "SHREECEM": "SXC", "HDFCLIFE": "HLIC",
    # NIFTY Next 50
    "ADANIGREEN": "AGEL", "AMBUJACEM": "ACBP5", "AUROPHARMA": "AP32", "BANKBARODA": "BB",
    "BERGEPAINT": "BPL07", "BIOCON": "BIOC", "BOSCHLTD": "MI", "CHOLAFIN": "CIFC",
    "COLPAL": "CCI", "DABUR": "DII2", "DLF": "DLF", "GAIL": "G12", "GODREJCP": "GCPL",
    "HAVELLS": "HVEL", "ICICIGI": "ICIG", "ICICIPRULI": "IPL04", "INDIGO": "IGO",
    "IOC": "IOC", "JINDALSTEL": "JSPL", "LICI": "LICI", "LUPIN": "L", "MARICO": "M13",
    "MCDOWELL-N": "MCD", "MOTHERSON": "SSP02", "MUTHOOTFIN": "MFI02", "NAUKRI": "INF2",
    "NMDC": "NMDC", "PIDILITIND": "PID5", "PNB": "PNB", "SAIL": "S04", "SIEMENS": "SIE",
    "SRF": "SRF", "TATAPOWER": "TPL", "TORNTPHARM": "TFS", "TRENT": "TT03", "VEDL": "STLC",
    "YESBANK": "YB", "ZOMATO": "ZOMATO", "PAYTM": "OCL05", "DMART": "DMART",
    "IRCTC": "IRCTC", "HAL": "HAL02", "BEL": "BEL", "IDEA": "IDEA",
    # Popular Stocks
    "TATAELXSI": "TE13", "POLYCAB": "PCAB", "PFC": "PFC", "RECLTD": "REC",
    "SBICARD": "SBIC", "NHPC": "NHPC", "IRFC": "IRFC", "JIOFIN": "JIL02",
    "ADANIPOWER": "APL62", "ABB": "ABB", "ACC": "ACI", "CANBK": "CB06",
    "FEDERALBNK": "FB", "GMRINFRA": "GI41", "IEX": "IEX", "MCX": "MCX",
    "PETRONET": "PLNG", "VBL": "VBL", "VOLTAS": "V03", "ZYDUSLIFE": "CDH",
    "BSE": "BSE05", "CDSL": "CDSL", "KFINTECH": "KPITC05",
}


def fetch_moneycontrol_index(symbol: str) -> Optional[Dict]:
    """
    Fetch live index price from Moneycontrol priceapi.
    Primary source for NIFTY 50 data.
    Returns: {'price': float, 'change': float, 'change_pct': float}
    """
    try:
        mc_id = MC_INDEX_IDS.get(symbol.upper())
        if not mc_id:
            return None
        
        # URL encode the mc_id (in;NSX -> in%3BNSX)
        from urllib.parse import quote
        mc_id_encoded = quote(mc_id, safe='')
            
        url = f"https://priceapi.moneycontrol.com/pricefeed/notapplicable/inidicesindia/{mc_id_encoded}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
        }
        
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code != 200:
            return None
            
        data = response.json()
        if data.get('code') != '200' or not data.get('data'):
            return None
            
        price_data = data['data']
        return {
            'price': float(price_data.get('pricecurrent', 0)),
            'change': float(price_data.get('pricechange', 0)),
            'change_pct': float(price_data.get('pricepercentchange', 0)),
            'high': float(price_data.get('HIGH', 0)),
            'low': float(price_data.get('LOW', 0)),
            'prev_close': float(price_data.get('priceprevclose', 0)),
            'market_state': price_data.get('market_state', 'UNKNOWN'),
            'source': 'moneycontrol'
        }
        
    except Exception as e:
        print(f"Moneycontrol Index Error ({symbol}): {e}")
        return None


def fetch_moneycontrol_stock(symbol: str) -> Optional[Dict]:
    """
    Fetch live stock price from Moneycontrol priceapi.
    Primary source for individual NSE stocks.
    Returns: {'price': float, 'change': float, 'change_pct': float, ...}
    """
    try:
        mc_id = MC_STOCK_IDS.get(symbol.upper())
        if not mc_id:
            return None
            
        url = f"https://priceapi.moneycontrol.com/pricefeed/nse/equitycash/{mc_id}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
        }
        
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code != 200:
            return None
            
        data = response.json()
        if data.get('code') != '200' or not data.get('data'):
            return None
            
        price_data = data['data']
        return {
            'price': float(price_data.get('pricecurrent', 0)),
            'change': float(price_data.get('pricechange', 0)),
            'change_pct': float(price_data.get('pricepercentchange', 0)),
            'high': float(price_data.get('HP', 0)),
            'low': float(price_data.get('LP', 0)),
            'prev_close': float(price_data.get('priceprevclose', 0)),
            'open': float(price_data.get('OPN', 0)),
            'volume': int(price_data.get('VOL', 0)),
            'high_52': float(price_data.get('52H', 0)),
            'low_52': float(price_data.get('52L', 0)),
            'market_state': price_data.get('market_state', 'UNKNOWN'),
            'company': price_data.get('company', symbol),
            'source': 'moneycontrol'
        }
        
    except Exception as e:
        print(f"Moneycontrol Stock Error ({symbol}): {e}")
        return None

def fetch_google_finance_data(symbol: str) -> Optional[Dict]:
    """
    Fetch live price from Google Finance via scraping.
    Returns dict: {'price': float, 'change': float, 'change_pct': float}
    Supports: NIFTY, BANKNIFTY, and ANY individual NSE stock
    """
    try:
        # Map symbol to Google Finance format
        if symbol == "NIFTY":
            google_symbol = "NIFTY_50:INDEXNSE"
        elif symbol == "BANKNIFTY":
            google_symbol = "NIFTY_BANK:INDEXNSE"
        elif symbol == "FINNIFTY":
            google_symbol = "NIFTY_FIN_SERVICE:INDEXNSE"
        elif symbol == "MIDCPNIFTY":
            google_symbol = "NIFTY_MIDCAP_SELECT:INDEXNSE"
        else:
            # For individual stocks: TATASTEEL -> TATASTEEL:NSE
            google_symbol = f"{symbol.upper()}:NSE"
            
        url = f"https://www.google.com/finance/quote/{google_symbol}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = session.get(url, headers=headers, timeout=5)
        if response.status_code != 200:
            return None
            
        html = response.text
        
        data = {}
        
        # 1. Extract Price - Try multiple methods
        # Method 1: Class YMlKec fxKbKc (works for indexes)
        price_match = re.search(r'class="YMlKec fxKbKc">([0-9,.]+)<', html)
        if price_match:
            data['price'] = float(price_match.group(1).replace(',', ''))
        else:
            # Method 2: data-last-price attribute (works for individual stocks)
            alt_match = re.search(r'data-last-price="([0-9.]+)"', html)
            if alt_match:
                data['price'] = float(alt_match.group(1))
            else:
                return None  # Price is mandatory
            
        # 2. Extract Change (Class: P2Luy Ez2Ioe OR JwB6zf) - Harder to rely on class
        # Alternative: Calculate change if we can find previous close, or just default to 0
        # For now, let's try to find the change element which usually has +/- sign
        # <div class="JwB6zf" ...>+123.45</div>
        # Regex for signed number with 2 decimals
        
        # Try to find valid change pattern near price? Too risky.
        # Fallback: Use Yahoo for change/pct if possible, or Mock based on trend.
        # But wait, we can just extract the next number after price in DOM?
        
        # Let's try to regex for the change percentage usually in brackets () or with %
        # <div class="JwB6zf ...">0.50%</div>
        
        pct_match = re.search(r'class="JwB6zf[^"]*">([0-9,.\-+]+)%<', html)
        if pct_match:
            pct_str = pct_match.group(1).replace('+', '').replace(',', '')
            data['change_pct'] = float(pct_str)
            # Calculate absolute change
            data['change'] = data['price'] * (data['change_pct'] / 100)
        else:
            data['change'] = 0.0
            data['change_pct'] = 0.0
            
        return data
        
    except Exception as e:
        print(f"Google Finance Scrape Error: {e}")
        return None

def get_live_dashboard_data(symbol: str) -> Dict:
    """
    Get live dashboard data snapshot including:
    - Current price and change (Moneycontrol Primary)
    - VWAP signal
    - PCR value
    - Sentiment Score
    - Alert message
    """
    current_price = 0.0
    price_change = 0.0
    price_change_pct = 0.0
    data_source = None
    
    # 1. Primary: Moneycontrol (User Request - Feb 2026)
    mc_data = fetch_moneycontrol_index(symbol)
    if mc_data:
        current_price = mc_data['price']
        price_change = mc_data['change']
        price_change_pct = mc_data['change_pct']
        data_source = 'moneycontrol'
        print(f"✅ Using Moneycontrol Data: {symbol} = ₹{current_price}")

    # 2. Secondary: Google Finance (for Bank NIFTY, FINNIFTY, etc.)
    if current_price == 0:
        print(f"Moneycontrol failed for {symbol}, falling back to Google Finance...")
        gf_data = fetch_google_finance_data(symbol)
        if gf_data:
            current_price = gf_data['price']
            price_change = gf_data['change']
            price_change_pct = gf_data['change_pct']
            data_source = 'google_finance'
            print(f"✅ Using Google Finance Data: {symbol} = ₹{current_price}")

    # 3. Tertiary: Yahoo Finance
    if current_price == 0:
        print(f"Google Finance failed for {symbol}, falling back to Yahoo...")
        try:
            import yfinance as yf
            yf_symbol = "^NSEI" if symbol == "NIFTY" else "^NSEBANK"
            if symbol == "FINNIFTY": yf_symbol = "NIFTY_FIN_SERVICE.NS"
            if symbol == "MIDCPNIFTY": yf_symbol = "^NSEMDCP50" 
            
            ticker = yf.Ticker(yf_symbol)
            hist = ticker.history(period="1d")
            if not hist.empty:
                current_price = float(hist['Close'].iloc[-1])
                # Calculate change
                prev_close = ticker.info.get('previousClose', current_price)
                if prev_close and prev_close != current_price:
                    price_change = current_price - prev_close
                    price_change_pct = (price_change / prev_close) * 100
                else:
                    open_price = float(hist['Open'].iloc[-1])
                    price_change = current_price - open_price
                    price_change_pct = (price_change / open_price) * 100
                data_source = 'yahoo_finance'
                print(f"✅ Using Yahoo Finance Data: {symbol} = ₹{current_price}")
        except Exception as e:
            print(f"yfinance fetch failed: {e}")

    # 3. Tertiary: NSE (If Yahoo failed)
    if current_price == 0:
        try:
            from jugaad_data.nse import NSELive
            nse = NSELive()
            index_name = symbol.replace("NIFTY", "NIFTY 50" if symbol == "NIFTY" else symbol)
            quote = nse.index_quote(index_name)
            if quote:
                current_price = quote.get('lastPrice', 0)
                price_change = quote.get('change', 0)
                price_change_pct = quote.get('pChange', 0)
        except:
            pass
            
    # 3. Fetch Technical Signals (PCR, VWAP) from Option Chain
    signals = {"vwap": 0, "pcr": 1.0, "sentiment_score": 5, "verdict": "NEUTRAL", "recommendation": "Data Unavailable"}
    try:
        signals = fetch_technical_signals(symbol)
    except Exception as e:
        print(f"Signal fetch failed: {e}")
        
    # 4. Fallback Signal Calculation (If signals failed but we have price)
    if current_price > 0 and signals['vwap'] == 0:
        # Create synthetic VWAP signal based on price trend
        is_bullish = price_change >= 0
        signals['vwap'] = current_price * (0.998 if is_bullish else 1.002)
        signals['sentiment_score'] = 7 if is_bullish else 3
        signals['verdict'] = "STRONG BUY" if is_bullish else "STRONG SELL"
        signals['recommendation'] = "Trend Following"
        
    # 5. Construct Response
    
    # Get current IST time
    now = datetime.now(IST)
    
    # Simple market status check (Mon-Fri, 9:15-15:30) + Budget Day exception
    is_weekend = now.weekday() >= 5
    is_budget_day = now.day == 1 and now.month == 2 # Budget Day exception
    is_open_time = dt_time(9, 15) <= now.time() <= dt_time(15, 30)
    
    market_active = (not is_weekend or is_budget_day) and is_open_time
    market_status = "OPEN" if market_active else "CLOSED"

    return {
        "status": "success",
        "symbol": symbol,
        "last_updated": now.isoformat(),
        "market_status": market_status,
        "data": {
            "price": float(current_price),
            "price_change": float(price_change),
            "price_change_pct": float(price_change_pct),
            "vwap_signal": {
                "value": float(signals.get('vwap', current_price)),
                "is_bullish": signals.get('vwap', current_price) < current_price,
                "message": "Bullish - Price above VWAP" if (signals.get('vwap', current_price) < current_price) else "Bearish - Price below VWAP"
            },
            "pcr": {
                "value": float(signals.get('pcr', 1.0)),
                "trend": "RISING" if signals.get('pcr', 1.0) > 0.8 else "FALLING"
            },
            "sentiment": {
                "score": int(signals.get('sentiment_score', 5)),
                "label": signals.get('verdict', 'NEUTRAL'),
                "color": "GREEN" if signals.get('verdict') == "STRONG BUY" else "RED" if signals.get('verdict') == "STRONG SELL" else "YELLOW"
            },
            "oi_alert": { 
                "message": signals.get('recommendation', 'Wait for clear direction'),
                "bg_color": "GREEN" if "BUY" in signals.get('recommendation', '') else "RED" if "SELL" in signals.get('recommendation', '') else "GREY" 
            }
        }
    }


def fetch_market_breadth() -> Dict:
    """
    Fetch Market Breadth - Advance/Decline ratio for NIFTY 50.
    Optimized: Uses index data instead of 50 individual stock calls.
    """
    try:
        from jugaad_data.nse import NSELive
        nse = NSELive()
        
        # Try to get NIFTY 50 index data which has advance/decline info
        try:
            # Get market status from index
            nifty_data = nse.index_quote("NIFTY 50")
            if nifty_data:
                # If we have the advancers/decliners data
                advances = nifty_data.get('advances', 0)
                declines = nifty_data.get('declines', 0)
                unchanged = nifty_data.get('unchanged', 0)
                
                if advances > 0 or declines > 0:
                    total = advances + declines + unchanged
                    if total == 0:
                        total = 1
                    adv_ratio = advances / total
                    
                    if adv_ratio > 0.6:
                        status = "BULLISH"
                        action = "Look for Call/Buy opportunities"
                        color = "GREEN"
                    elif adv_ratio < 0.4:
                        status = "BEARISH"
                        action = "Look for Put/Sell opportunities"
                        color = "RED"
                    else:
                        status = "NEUTRAL"
                        action = "No clear direction - Avoid trading"
                        color = "YELLOW"
                    
                    return {
                        "advancing": advances,
                        "declining": declines,
                        "unchanged": unchanged,
                        "ratio": round(adv_ratio, 2),
                        "status": status,
                        "action": action,
                        "color": color
                    }
        except:
            pass
        
        # Fallback: Quick estimation from NIFTY percentage change
        try:
            nifty_data = nse.index_quote("NIFTY 50")
            if nifty_data and 'percentChange' in nifty_data:
                pct_change = float(nifty_data['percentChange'])
                
                # Estimate based on index movement
                if pct_change > 0.5:
                    return {
                        "advancing": 35, "declining": 12, "unchanged": 3,
                        "ratio": 0.70, "status": "BULLISH", 
                        "action": "Look for Call/Buy opportunities", "color": "GREEN"
                    }
                elif pct_change < -0.5:
                    return {
                        "advancing": 12, "declining": 35, "unchanged": 3,
                        "ratio": 0.24, "status": "BEARISH", 
                        "action": "Look for Put/Sell opportunities", "color": "RED"
                    }
                else:
                    return {
                        "advancing": 25, "declining": 22, "unchanged": 3,
                        "ratio": 0.50, "status": "NEUTRAL", 
                        "action": "No clear direction - Wait for clarity", "color": "YELLOW"
                    }
        except:
            pass
        
        # Default fallback
        return {
            "advancing": 25, "declining": 20, "unchanged": 5,
            "ratio": 0.50, "status": "NEUTRAL", 
            "action": "Data loading...", "color": "YELLOW"
        }
    except Exception as e:
        print(f"Market Breadth error: {e}")
        return {
            "advancing": 25, "declining": 20, "unchanged": 5,
            "ratio": 0.50, "status": "UNKNOWN", 
            "action": "Data Unavailable", "color": "GREY"
        }



def fetch_straddle_price(symbol: str = "NIFTY") -> Dict:
    """
    Fetch ATM Straddle price for Theta Decay tracking.
    If straddle price is falling: Market is sideways, avoid option buying.
    If straddle price is stable/rising: Market is trending, OK to buy options.
    """
    try:
        option_chain = fetch_option_chain(symbol)
        if not option_chain or 'records' not in option_chain:
            return {"price": 0, "atm_strike": 0, "trend": "UNKNOWN", "action": "Data Unavailable"}
        
        # Find ATM strike
        spot_price = option_chain.get('records', {}).get('underlyingValue', 0)
        if spot_price == 0:
            return {"price": 0, "atm_strike": 0, "trend": "UNKNOWN", "action": "Data Unavailable"}
        
        # Use correct step size for each symbol
        step_sizes = {
            "NIFTY": 50,
            "BANKNIFTY": 100,
            "FINNIFTY": 50,
            "MIDCPNIFTY": 25
        }
        step = step_sizes.get(symbol, 50)
        atm_strike = round(spot_price / step) * step
        
        # Find ATM Call and Put prices
        atm_call_price = 0
        atm_put_price = 0
        
        for item in option_chain.get('records', {}).get('data', []):
            if item.get('strikePrice') == atm_strike:
                if 'CE' in item:
                    atm_call_price = item['CE'].get('lastPrice', 0)
                if 'PE' in item:
                    atm_put_price = item['PE'].get('lastPrice', 0)
                break
        
        straddle_price = atm_call_price + atm_put_price
        
        # We can't track historical without a cache, so provide guidance
        if straddle_price > 0:
            return {
                "atm_strike": atm_strike,
                "call_price": round(atm_call_price, 2),
                "put_price": round(atm_put_price, 2),
                "straddle_price": round(straddle_price, 2),
                "trend": "MONITOR",
                "action": f"Track if ₹{round(straddle_price, 0)} falls quickly = Sideways, avoid buying"
            }
        else:
            return {"straddle_price": 0, "trend": "UNKNOWN", "action": "Data Unavailable"}
    except Exception as e:
        print(f"Straddle fetch error: {e}")
        return {"straddle_price": 0, "trend": "UNKNOWN", "action": "Data Unavailable"}


def fetch_oi_ladder(symbol: str = "NIFTY", levels: int = 5) -> Dict:
    """
    Fetch OI Ladder - Top resistance and support levels based on OI.
    """
    try:
        option_chain = fetch_option_chain(symbol)
        if not option_chain or 'records' not in option_chain:
            return {"resistances": [], "supports": []}
        
        spot_price = option_chain.get('records', {}).get('underlyingValue', 0)
        data = option_chain.get('records', {}).get('data', [])
        
        # Collect OI data
        call_oi = []
        put_oi = []
        
        for item in data:
            strike = item.get('strikePrice', 0)
            if 'CE' in item and strike > spot_price:
                call_oi.append({
                    'strike': strike,
                    'oi': item['CE'].get('openInterest', 0),
                    'oi_change': item['CE'].get('changeinOpenInterest', 0)
                })
            if 'PE' in item and strike < spot_price:
                put_oi.append({
                    'strike': strike,
                    'oi': item['PE'].get('openInterest', 0),
                    'oi_change': item['PE'].get('changeinOpenInterest', 0)
                })
        
        # Sort by OI and get top levels
        call_oi.sort(key=lambda x: x['oi'], reverse=True)
        put_oi.sort(key=lambda x: x['oi'], reverse=True)
        
        resistances = call_oi[:levels]
        supports = put_oi[:levels]
        
        # Sort by strike for display
        resistances.sort(key=lambda x: x['strike'])
        supports.sort(key=lambda x: x['strike'], reverse=True)
        
        return {
            "spot": round(spot_price, 2),
            "resistances": resistances,
            "supports": supports,
            "max_resistance": resistances[0]['strike'] if resistances else 0,
            "max_support": supports[0]['strike'] if supports else 0
        }
    except Exception as e:
        print(f"OI Ladder error: {e}")
        return {"resistances": [], "supports": []}


def get_market_overview(symbol: str = "NIFTY") -> Dict:
    """
    Combined API for all advanced indicators.
    Returns VIX, Market Breadth, Straddle, OI Ladder in one call.
    """
    return {
        "vix": fetch_india_vix(),
        "breadth": fetch_market_breadth(),
        "straddle": fetch_straddle_price(symbol),
        "oi_ladder": fetch_oi_ladder(symbol)
    }


# Session initialization is now handled lazily on first request failure
# via fetch_option_chain logic.
# get_nse_session() removed to prevent module import blocking.
