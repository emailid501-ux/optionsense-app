"""
Pro Trader 8-Point Analysis System
Implements all 8 professional trading indicators with NSE (primary) and Moneycontrol (fallback)
"""

from typing import Dict, Optional, List
from datetime import datetime
import requests
import re
import math

# Try importing required modules
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

# Session for web requests
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})

# Helper to sanitize NaN/Inf values for JSON
def sanitize_value(value, default=0):
    """Convert NaN/Inf to default value for JSON serialization."""
    if value is None:
        return default
    try:
        if math.isnan(value) or math.isinf(value):
            return default
        return value
    except (TypeError, ValueError):
        return default

# Cache for OI Shift tracking
_oi_cache = {
    "NIFTY": {"timestamp": None, "max_put_strike": None, "max_call_strike": None},
    "BANKNIFTY": {"timestamp": None, "max_put_strike": None, "max_call_strike": None}
}


# ================================================================
# 1. PCR ANALYSIS (Enhanced)
# ================================================================

def get_pcr_analysis(symbol: str = "NIFTY") -> Dict:
    """
    Enhanced PCR Analysis with interpretation.
    PCR > 1.0 = Bullish (Put writers dominating = support strong)
    PCR < 0.7 = Bearish (Call writers dominating = resistance strong)
    PCR falling from 1.5+ = Reversal warning
    """
    try:
        from live_data import fetch_option_chain
        
        oi_data = fetch_option_chain(symbol)
        if not oi_data:
            return _get_mock_pcr()
        
        total_put_oi = oi_data.get("total_put_oi", 0)
        total_call_oi = oi_data.get("total_call_oi", 0)
        
        pcr = round(total_put_oi / total_call_oi, 2) if total_call_oi > 0 else 1.0
        
        # Interpretation
        if pcr >= 1.5:
            signal = "VERY_BULLISH"
            interpretation = "PCR बहुत High है - Strong Support, Buy on Dips"
            color = "#00E676"
        elif pcr >= 1.0:
            signal = "BULLISH"
            interpretation = "PCR 1.0+ है - Support Strong, Buying Zone"
            color = "#69F0AE"
        elif pcr >= 0.7:
            signal = "NEUTRAL"
            interpretation = "PCR Neutral Zone में है - Wait & Watch"
            color = "#FFD600"
        elif pcr >= 0.5:
            signal = "BEARISH"
            interpretation = "PCR Low है - Call Writers Active, Sell on Rise"
            color = "#FF8A80"
        else:
            signal = "VERY_BEARISH"
            interpretation = "PCR बहुत Low है - Strong Resistance, Avoid Buying"
            color = "#FF5252"
        
        return {
            "pcr": pcr,
            "total_put_oi": total_put_oi,
            "total_call_oi": total_call_oi,
            "signal": signal,
            "interpretation": interpretation,
            "interpretation_hi": interpretation,
            "color": color,
            "strategy": "Buy on Dips" if pcr >= 1.0 else "Sell on Rise"
        }
        
    except Exception as e:
        print(f"PCR Analysis Error: {e}")
        return _get_mock_pcr()


def _get_mock_pcr() -> Dict:
    return {
        "pcr": 1.15,
        "total_put_oi": 12500000,
        "total_call_oi": 10870000,
        "signal": "BULLISH",
        "interpretation": "PCR 1.0+ है - Support Strong",
        "interpretation_hi": "PCR 1.0+ है - Support Strong",
        "color": "#69F0AE",
        "strategy": "Buy on Dips"
    }


# ================================================================
# 2. OI SHIFT ANALYSIS
# ================================================================

def get_oi_shift_analysis(symbol: str = "NIFTY") -> Dict:
    """
    Track OI Shift - Support/Resistance level changes.
    Support Shift Up = Bullish
    Resistance Shift Down = Bearish
    """
    global _oi_cache
    
    try:
        from live_data import fetch_option_chain
        
        oi_data = fetch_option_chain(symbol)
        if not oi_data:
            return _get_mock_oi_shift()
        
        # Find max OI strikes
        chain = oi_data.get("data", [])
        if not chain:
            return _get_mock_oi_shift()
        
        max_put_oi = 0
        max_call_oi = 0
        max_put_strike = 0
        max_call_strike = 0
        
        for row in chain:
            put_oi = row.get("put_oi", 0) or 0
            call_oi = row.get("call_oi", 0) or 0
            strike = row.get("strike", 0)
            
            if put_oi > max_put_oi:
                max_put_oi = put_oi
                max_put_strike = strike
            if call_oi > max_call_oi:
                max_call_oi = call_oi
                max_call_strike = strike
        
        # Check shift from cache
        prev_data = _oi_cache.get(symbol, {})
        prev_put_strike = prev_data.get("max_put_strike")
        prev_call_strike = prev_data.get("max_call_strike")
        
        support_shift = None
        resistance_shift = None
        
        if prev_put_strike and max_put_strike != prev_put_strike:
            if max_put_strike > prev_put_strike:
                support_shift = "UP"
            else:
                support_shift = "DOWN"
        
        if prev_call_strike and max_call_strike != prev_call_strike:
            if max_call_strike < prev_call_strike:
                resistance_shift = "DOWN"
            else:
                resistance_shift = "UP"
        
        # Update cache
        _oi_cache[symbol] = {
            "timestamp": datetime.now().isoformat(),
            "max_put_strike": max_put_strike,
            "max_call_strike": max_call_strike
        }
        
        # Interpretation
        if support_shift == "UP":
            signal = "BULLISH"
            interpretation = f"Support ऊपर shift हुआ - {prev_put_strike} → {max_put_strike}"
        elif resistance_shift == "DOWN":
            signal = "BEARISH"
            interpretation = f"Resistance नीचे shift हुआ - {prev_call_strike} → {max_call_strike}"
        else:
            signal = "NEUTRAL"
            interpretation = "No significant OI shift detected"
        
        return {
            "max_put_strike": max_put_strike,
            "max_put_oi": max_put_oi,
            "max_call_strike": max_call_strike,
            "max_call_oi": max_call_oi,
            "support_shift": support_shift,
            "resistance_shift": resistance_shift,
            "signal": signal,
            "interpretation": interpretation,
            "prev_put_strike": prev_put_strike,
            "prev_call_strike": prev_call_strike
        }
        
    except Exception as e:
        print(f"OI Shift Error: {e}")
        return _get_mock_oi_shift()


def _get_mock_oi_shift() -> Dict:
    return {
        "max_put_strike": 23500,
        "max_put_oi": 8500000,
        "max_call_strike": 24000,
        "max_call_oi": 7200000,
        "support_shift": None,
        "resistance_shift": None,
        "signal": "NEUTRAL",
        "interpretation": "Analyzing OI shifts...",
        "prev_put_strike": None,
        "prev_call_strike": None
    }


# ================================================================
# 3. VIX & IV SKEW ANALYSIS
# ================================================================

def get_vix_iv_analysis(symbol: str = "NIFTY") -> Dict:
    """
    VIX and IV Skew Analysis.
    High VIX = High Fear = Option Selling opportunity
    Put IV > Call IV = Bearish bias (people buying protection)
    """
    try:
        vix = 14.5  # Default
        
        # Fetch VIX from yfinance
        if YFINANCE_AVAILABLE:
            try:
                vix_ticker = yf.Ticker("^INDIAVIX")
                hist = vix_ticker.history(period="1d")
                if len(hist) > 0:
                    vix = round(float(hist['Close'].iloc[-1]), 2)
            except:
                pass
        
        # Calculate IV Skew from option chain
        from live_data import fetch_option_chain
        oi_data = fetch_option_chain(symbol)
        
        put_iv = 15.0  # Default
        call_iv = 14.0
        
        if oi_data and oi_data.get("data"):
            # Get ATM strike
            spot = oi_data.get("spot_price", 0)
            for row in oi_data.get("data", []):
                strike = row.get("strike", 0)
                if abs(strike - spot) < 100:  # Near ATM
                    put_iv = row.get("put_iv", 15) or 15
                    call_iv = row.get("call_iv", 14) or 14
                    break
        
        iv_skew = round(put_iv - call_iv, 2)
        
        # VIX Interpretation
        if vix < 12:
            vix_signal = "LOW"
            vix_strategy = "Option Buying - Market Calm"
        elif vix < 18:
            vix_signal = "NORMAL"
            vix_strategy = "Both Buying & Selling OK"
        else:
            vix_signal = "HIGH"
            vix_strategy = "Option Selling - High Premium"
        
        # IV Skew Interpretation
        if iv_skew > 2:
            iv_signal = "BEARISH"
            iv_interpretation = f"Put IV ({put_iv}) > Call IV ({call_iv}) - Market mein darr hai"
        elif iv_skew < -2:
            iv_signal = "BULLISH"
            iv_interpretation = f"Call IV ({call_iv}) > Put IV ({put_iv}) - Greed zone"
        else:
            iv_signal = "NEUTRAL"
            iv_interpretation = "IV Skew Normal - Balanced market"
        
        return {
            "vix": vix,
            "vix_signal": vix_signal,
            "vix_strategy": vix_strategy,
            "put_iv": put_iv,
            "call_iv": call_iv,
            "iv_skew": iv_skew,
            "iv_signal": iv_signal,
            "iv_interpretation": iv_interpretation,
            "overall_signal": "SELL" if vix > 18 else "BUY" if vix < 12 else "NEUTRAL"
        }
        
    except Exception as e:
        print(f"VIX/IV Error: {e}")
        return {
            "vix": 14.5,
            "vix_signal": "NORMAL",
            "vix_strategy": "Both Buying & Selling OK",
            "put_iv": 15.0,
            "call_iv": 14.0,
            "iv_skew": 1.0,
            "iv_signal": "NEUTRAL",
            "iv_interpretation": "IV Skew Normal",
            "overall_signal": "NEUTRAL"
        }


# ================================================================
# 4. VOLUME ANALYSIS (True Move vs Trap Move)
# ================================================================

def get_volume_analysis(symbol: str) -> Dict:
    """
    Volume Analysis - True Move vs Trap Move.
    Price Up + Volume Up = True Buying
    Price Up + Volume Down = Fake Breakout (Trap)
    """
    try:
        if YFINANCE_AVAILABLE:
            ticker_symbol = f"{symbol}.NS" if symbol not in ["NIFTY", "BANKNIFTY"] else "^NSEI"
            ticker = yf.Ticker(ticker_symbol)
            hist = ticker.history(period="5d")
            
            if len(hist) >= 2:
                current_volume = int(hist['Volume'].iloc[-1])
                prev_volume = int(hist['Volume'].iloc[-2])
                avg_volume = int(hist['Volume'].mean())
                
                current_close = float(hist['Close'].iloc[-1])
                prev_close = float(hist['Close'].iloc[-2])
                
                price_change = current_close - prev_close
                volume_change = current_volume - prev_volume
                
                volume_ratio = round(current_volume / avg_volume, 2) if avg_volume > 0 else 1.0
                
                # Analysis
                if price_change > 0 and volume_change > 0:
                    signal = "TRUE_BUYING"
                    interpretation = "Price ↑ + Volume ↑ = Real Buying - Trade mein bane rahein"
                    color = "#00E676"
                elif price_change > 0 and volume_change < 0:
                    signal = "TRAP_MOVE"
                    interpretation = "Price ↑ + Volume ↓ = Fake Breakout - Reversal ke liye taiyar"
                    color = "#FF8A80"
                elif price_change < 0 and volume_change > 0:
                    signal = "TRUE_SELLING"
                    interpretation = "Price ↓ + Volume ↑ = Real Selling - Avoid buying"
                    color = "#FF5252"
                else:
                    signal = "WEAK_SELLING"
                    interpretation = "Price ↓ + Volume ↓ = Weak Selling - Bounce possible"
                    color = "#FFD600"
                
                return {
                    "current_volume": current_volume,
                    "avg_volume": avg_volume,
                    "volume_ratio": volume_ratio,
                    "price_change": round(price_change, 2),
                    "volume_change": volume_change,
                    "signal": signal,
                    "interpretation": interpretation,
                    "color": color
                }
        
        return _get_mock_volume()
        
    except Exception as e:
        print(f"Volume Error: {e}")
        return _get_mock_volume()


def _get_mock_volume() -> Dict:
    return {
        "current_volume": 15000000,
        "avg_volume": 12000000,
        "volume_ratio": 1.25,
        "price_change": 45.5,
        "volume_change": 3000000,
        "signal": "TRUE_BUYING",
        "interpretation": "Price ↑ + Volume ↑ = Real Buying",
        "color": "#00E676"
    }


# ================================================================
# 5. OI LADDER (Resistance Levels)
# ================================================================

def get_oi_ladder(symbol: str = "NIFTY") -> Dict:
    """
    OI Ladder - Shows resistance/support levels with OI amounts.
    Helps identify where market will face hurdles.
    """
    try:
        from live_data import fetch_option_chain
        
        oi_data = fetch_option_chain(symbol)
        if not oi_data or not oi_data.get("data"):
            return _get_mock_oi_ladder()
        
        spot = oi_data.get("spot_price", 0)
        chain = oi_data.get("data", [])
        
        # Get top 5 Call OI (Resistance) and top 5 Put OI (Support)
        call_levels = []
        put_levels = []
        
        for row in chain:
            strike = row.get("strike", 0)
            call_oi = row.get("call_oi", 0) or 0
            put_oi = row.get("put_oi", 0) or 0
            
            if call_oi > 0 and strike > spot:  # Above spot = Resistance
                call_levels.append({"strike": strike, "oi": call_oi})
            if put_oi > 0 and strike < spot:  # Below spot = Support
                put_levels.append({"strike": strike, "oi": put_oi})
        
        # Sort and get top 5
        call_levels.sort(key=lambda x: x["oi"], reverse=True)
        put_levels.sort(key=lambda x: x["oi"], reverse=True)
        
        resistance_ladder = call_levels[:5]
        support_ladder = put_levels[:5]
        
        # Format for display
        resistance_text = " > ".join([f"₹{r['strike']} ({r['oi']//100000}L)" for r in resistance_ladder])
        support_text = " > ".join([f"₹{s['strike']} ({s['oi']//100000}L)" for s in support_ladder])
        
        return {
            "spot_price": spot,
            "resistance_ladder": resistance_ladder,
            "support_ladder": support_ladder,
            "resistance_text": resistance_text,
            "support_text": support_text,
            "interpretation": f"Resistance Ladder: {resistance_text}",
            "strategy": "Trade between support and resistance levels"
        }
        
    except Exception as e:
        print(f"OI Ladder Error: {e}")
        return _get_mock_oi_ladder()


def _get_mock_oi_ladder() -> Dict:
    return {
        "spot_price": 23650,
        "resistance_ladder": [
            {"strike": 24000, "oi": 7500000},
            {"strike": 24100, "oi": 5200000},
            {"strike": 24200, "oi": 4800000}
        ],
        "support_ladder": [
            {"strike": 23500, "oi": 8500000},
            {"strike": 23400, "oi": 6200000},
            {"strike": 23300, "oi": 5100000}
        ],
        "resistance_text": "₹24000 (75L) > ₹24100 (52L) > ₹24200 (48L)",
        "support_text": "₹23500 (85L) > ₹23400 (62L) > ₹23300 (51L)",
        "interpretation": "Strong resistance at 24000",
        "strategy": "Trade between support and resistance levels"
    }


# ================================================================
# 6. THETA DECAY ANALYSIS
# ================================================================

def get_theta_decay_analysis(symbol: str = "NIFTY") -> Dict:
    """
    Theta Decay - ATM Straddle price tracking.
    If straddle price falling fast = Sideways market = No option buying
    If straddle price stable/rising = Trending = Option buying OK
    """
    try:
        from live_data import fetch_option_chain
        
        oi_data = fetch_option_chain(symbol)
        if not oi_data or not oi_data.get("data"):
            return _get_mock_theta()
        
        spot = oi_data.get("spot_price", 0)
        chain = oi_data.get("data", [])
        
        # Find ATM strike
        atm_strike = round(spot / 100) * 100  # Round to nearest 100
        
        atm_call_premium = 0
        atm_put_premium = 0
        
        for row in chain:
            if row.get("strike") == atm_strike:
                atm_call_premium = row.get("call_ltp", 0) or 0
                atm_put_premium = row.get("put_ltp", 0) or 0
                break
        
        straddle_price = atm_call_premium + atm_put_premium
        
        # Estimate daily theta (approx 5-8% decay per day)
        estimated_theta = round(straddle_price * 0.06, 2)
        
        # Interpretation
        if straddle_price > 400:
            signal = "HIGH_PREMIUM"
            interpretation = "Straddle Price High - Volatility expected, Option Buying OK"
            strategy = "Option Buying"
        elif straddle_price > 200:
            signal = "NORMAL"
            interpretation = "Straddle Price Normal - Wait for direction"
            strategy = "Wait & Watch"
        else:
            signal = "LOW_PREMIUM"
            interpretation = "Straddle Price Low - Sideways market, Avoid Option Buying"
            strategy = "Option Selling / Iron Condor"
        
        return {
            "atm_strike": atm_strike,
            "atm_call_premium": atm_call_premium,
            "atm_put_premium": atm_put_premium,
            "straddle_price": straddle_price,
            "estimated_theta": estimated_theta,
            "signal": signal,
            "interpretation": interpretation,
            "strategy": strategy
        }
        
    except Exception as e:
        print(f"Theta Error: {e}")
        return _get_mock_theta()


def _get_mock_theta() -> Dict:
    return {
        "atm_strike": 23700,
        "atm_call_premium": 185,
        "atm_put_premium": 165,
        "straddle_price": 350,
        "estimated_theta": 21,
        "signal": "NORMAL",
        "interpretation": "Straddle Price Normal - Wait for direction",
        "strategy": "Wait & Watch"
    }


# ================================================================
# 7. MARKET BREADTH (Advance/Decline)
# ================================================================

def get_market_breadth() -> Dict:
    """
    Market Breadth - Advance/Decline ratio.
    >35 advancing = Bullish
    >35 declining = Bearish
    25-25 split = Confused/No Trade
    """
    try:
        # Try Moneycontrol scraping
        url = "https://www.moneycontrol.com/stocks/marketstats/adv_decline.php"
        response = session.get(url, timeout=10)
        
        if response.status_code == 200:
            html = response.text
            
            # Try to extract advance/decline from HTML
            adv_match = re.search(r'Advances[^0-9]*(\d+)', html)
            dec_match = re.search(r'Declines[^0-9]*(\d+)', html)
            
            if adv_match and dec_match:
                advancing = int(adv_match.group(1))
                declining = int(dec_match.group(1))
            else:
                # Fallback mock
                advancing = 28
                declining = 22
        else:
            advancing = 28
            declining = 22
        
        total = advancing + declining
        unchanged = 50 - total if total < 50 else 0
        
        # Interpretation
        if advancing >= 35:
            signal = "BULLISH"
            interpretation = f"{advancing}/50 stocks Green - Market Health Good, Buy Calls"
            color = "#00E676"
        elif declining >= 35:
            signal = "BEARISH"
            interpretation = f"{declining}/50 stocks Red - Market Weak, Buy Puts"
            color = "#FF5252"
        else:
            signal = "NEUTRAL"
            interpretation = f"{advancing} Green, {declining} Red - Mixed, No Trade Zone"
            color = "#FFD600"
        
        return {
            "advancing": advancing,
            "declining": declining,
            "unchanged": unchanged,
            "total": 50,
            "advance_decline_ratio": round(advancing / declining, 2) if declining > 0 else 0,
            "signal": signal,
            "interpretation": interpretation,
            "color": color
        }
        
    except Exception as e:
        print(f"Market Breadth Error: {e}")
        return {
            "advancing": 28,
            "declining": 22,
            "unchanged": 0,
            "total": 50,
            "advance_decline_ratio": 1.27,
            "signal": "NEUTRAL",
            "interpretation": "28 Green, 22 Red - Mixed signals",
            "color": "#FFD600"
        }


# ================================================================
# 8. VWAP ANALYSIS
# ================================================================

def get_vwap_analysis(symbol: str) -> Dict:
    """
    Enhanced VWAP Analysis with entry/exit recommendations.
    Price > VWAP = Bullish, Buy area
    Price < VWAP = Bearish, Sell area
    Too far from VWAP = Mean reversion expected
    """
    try:
        if YFINANCE_AVAILABLE:
            ticker_symbol = f"{symbol}.NS" if symbol not in ["NIFTY", "BANKNIFTY"] else "^NSEI"
            ticker = yf.Ticker(ticker_symbol)
            hist = ticker.history(period="1d", interval="5m")
            
            if len(hist) > 0:
                # Calculate VWAP = Sum(Price * Volume) / Sum(Volume)
                typical_price = (hist['High'] + hist['Low'] + hist['Close']) / 3
                vol_sum = hist['Volume'].sum()
                if vol_sum == 0:
                    return _get_mock_vwap()
                vwap = sanitize_value(float((typical_price * hist['Volume']).sum() / vol_sum), 0)
                current_price = sanitize_value(float(hist['Close'].iloc[-1]), 0)
                
                if vwap == 0:
                    return _get_mock_vwap()
                
                distance = sanitize_value(current_price - vwap, 0)
                distance_pct = sanitize_value(round((distance / vwap) * 100, 2), 0)
                
                # Analysis
                if distance_pct > 0.5:
                    signal = "ABOVE_VWAP"
                    interpretation = "Price VWAP से ऊपर - Bullish, Hold Longs"
                    entry = "Jab price VWAP touch kare tab Buy"
                    stoploss = f"VWAP के नीचे: ₹{round(vwap * 0.995, 2)}"
                elif distance_pct < -0.5:
                    signal = "BELOW_VWAP"
                    interpretation = "Price VWAP से नीचे - Bearish, Hold Shorts"
                    entry = "Jab price VWAP touch kare tab Sell"
                    stoploss = f"VWAP के ऊपर: ₹{round(vwap * 1.005, 2)}"
                else:
                    signal = "AT_VWAP"
                    interpretation = "Price VWAP पर है - Decision point"
                    entry = "Breakout wait karein"
                    stoploss = "Range ke bahar"
                
                # Mean reversion warning
                if abs(distance_pct) > 1.5:
                    interpretation += " ⚠️ Price VWAP se bahut door - Reversion expected"
                
                return {
                    "vwap": sanitize_value(round(vwap, 2), 0),
                    "current_price": sanitize_value(round(current_price, 2), 0),
                    "distance": sanitize_value(round(distance, 2), 0),
                    "distance_pct": distance_pct,
                    "signal": signal,
                    "interpretation": interpretation,
                    "entry_recommendation": entry,
                    "stoploss": stoploss
                }
        
        return _get_mock_vwap()
        
    except Exception as e:
        print(f"VWAP Error: {e}")
        return _get_mock_vwap()


def _get_mock_vwap() -> Dict:
    return {
        "vwap": 23650,
        "current_price": 23720,
        "distance": 70,
        "distance_pct": 0.3,
        "signal": "ABOVE_VWAP",
        "interpretation": "Price VWAP से ऊपर - Bullish",
        "entry_recommendation": "Jab price VWAP touch kare tab Buy",
        "stoploss": "VWAP के नीचे: ₹23532"
    }


# ================================================================
# MAIN: Get Complete 8-Point Analysis
# ================================================================

def get_complete_pro_analysis(symbol: str = "NIFTY") -> Dict:
    """
    Get all 8 pro trader analysis points in one call.
    """
    return {
        "symbol": symbol,
        "timestamp": datetime.now().isoformat(),
        "1_pcr": get_pcr_analysis(symbol),
        "2_oi_shift": get_oi_shift_analysis(symbol),
        "3_vix_iv": get_vix_iv_analysis(symbol),
        "4_volume": get_volume_analysis(symbol),
        "5_oi_ladder": get_oi_ladder(symbol),
        "6_theta_decay": get_theta_decay_analysis(symbol),
        "7_market_breadth": get_market_breadth(),
        "8_vwap": get_vwap_analysis(symbol),
        "overall_verdict": _calculate_overall_verdict(symbol)
    }


def _calculate_overall_verdict(symbol: str) -> Dict:
    """Calculate overall verdict from all signals."""
    try:
        pcr = get_pcr_analysis(symbol)
        vix = get_vix_iv_analysis(symbol)
        breadth = get_market_breadth()
        
        bullish_count = 0
        bearish_count = 0
        
        if pcr.get("signal") in ["BULLISH", "VERY_BULLISH"]:
            bullish_count += 1
        elif pcr.get("signal") in ["BEARISH", "VERY_BEARISH"]:
            bearish_count += 1
        
        if vix.get("iv_signal") == "BULLISH":
            bullish_count += 1
        elif vix.get("iv_signal") == "BEARISH":
            bearish_count += 1
        
        if breadth.get("signal") == "BULLISH":
            bullish_count += 1
        elif breadth.get("signal") == "BEARISH":
            bearish_count += 1
        
        if bullish_count >= 2:
            verdict = "BULLISH"
            message = "Multiple bullish signals - Buy on dips recommended"
        elif bearish_count >= 2:
            verdict = "BEARISH"
            message = "Multiple bearish signals - Sell on rise recommended"
        else:
            verdict = "NEUTRAL"
            message = "Mixed signals - Wait for clarity"
        
        return {
            "verdict": verdict,
            "message": message,
            "bullish_signals": bullish_count,
            "bearish_signals": bearish_count
        }
        
    except:
        return {"verdict": "NEUTRAL", "message": "Analysis in progress", "bullish_signals": 0, "bearish_signals": 0}
