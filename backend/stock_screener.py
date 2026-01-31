"""Stock screener data provider with mock data for popular Indian stocks."""
import random
from datetime import datetime
from typing import List, Dict, Literal


# Popular Indian stocks for the screener
STOCK_LIST = [
    {"symbol": "RELIANCE", "name": "Reliance Industries", "sector": "Oil & Gas"},
    {"symbol": "TCS", "name": "Tata Consultancy Services", "sector": "IT"},
    {"symbol": "HDFCBANK", "name": "HDFC Bank", "sector": "Banking"},
    {"symbol": "INFY", "name": "Infosys", "sector": "IT"},
    {"symbol": "ICICIBANK", "name": "ICICI Bank", "sector": "Banking"},
    {"symbol": "HINDUNILVR", "name": "Hindustan Unilever", "sector": "FMCG"},
    {"symbol": "SBIN", "name": "State Bank of India", "sector": "Banking"},
    {"symbol": "BHARTIARTL", "name": "Bharti Airtel", "sector": "Telecom"},
    {"symbol": "ITC", "name": "ITC Limited", "sector": "FMCG"},
    {"symbol": "KOTAKBANK", "name": "Kotak Mahindra Bank", "sector": "Banking"},
    {"symbol": "LT", "name": "Larsen & Toubro", "sector": "Infrastructure"},
    {"symbol": "AXISBANK", "name": "Axis Bank", "sector": "Banking"},
    {"symbol": "ASIANPAINT", "name": "Asian Paints", "sector": "Paints"},
    {"symbol": "MARUTI", "name": "Maruti Suzuki", "sector": "Auto"},
    {"symbol": "SUNPHARMA", "name": "Sun Pharma", "sector": "Pharma"},
    {"symbol": "TITAN", "name": "Titan Company", "sector": "Consumer"},
    {"symbol": "BAJFINANCE", "name": "Bajaj Finance", "sector": "NBFC"},
    {"symbol": "WIPRO", "name": "Wipro", "sector": "IT"},
    {"symbol": "ULTRACEMCO", "name": "UltraTech Cement", "sector": "Cement"},
    {"symbol": "TATAMOTORS", "name": "Tata Motors", "sector": "Auto"},
    {"symbol": "POWERGRID", "name": "Power Grid Corp", "sector": "Power"},
    {"symbol": "NTPC", "name": "NTPC Limited", "sector": "Power"},
    {"symbol": "ONGC", "name": "Oil & Natural Gas Corp", "sector": "Oil & Gas"},
    {"symbol": "TATASTEEL", "name": "Tata Steel", "sector": "Metals"},
    {"symbol": "JSWSTEEL", "name": "JSW Steel", "sector": "Metals"},
    {"symbol": "TECHM", "name": "Tech Mahindra", "sector": "IT"},
    {"symbol": "HCLTECH", "name": "HCL Technologies", "sector": "IT"},
    {"symbol": "ADANIENT", "name": "Adani Enterprises", "sector": "Diversified"},
    {"symbol": "ADANIPORTS", "name": "Adani Ports", "sector": "Infrastructure"},
    {"symbol": "COALINDIA", "name": "Coal India", "sector": "Mining"},
]

# Base prices for stocks (approximate)
BASE_PRICES = {
    "RELIANCE": 2450, "TCS": 3800, "HDFCBANK": 1650, "INFY": 1550,
    "ICICIBANK": 1050, "HINDUNILVR": 2400, "SBIN": 780, "BHARTIARTL": 1150,
    "ITC": 430, "KOTAKBANK": 1750, "LT": 3400, "AXISBANK": 1100,
    "ASIANPAINT": 2800, "MARUTI": 11500, "SUNPHARMA": 1650, "TITAN": 3200,
    "BAJFINANCE": 6800, "WIPRO": 480, "ULTRACEMCO": 10500, "TATAMOTORS": 780,
    "POWERGRID": 290, "NTPC": 350, "ONGC": 260, "TATASTEEL": 145,
    "JSWSTEEL": 920, "TECHM": 1450, "HCLTECH": 1650, "ADANIENT": 2900,
    "ADANIPORTS": 1250, "COALINDIA": 480
}


class StockScreener:
    """Stock screener with technical analysis signals."""
    
    def __init__(self):
        self._cache = {}
        self._last_refresh = None
    
    def _generate_stock_data(self, stock_info: Dict) -> Dict:
        """Generate mock stock data with technical signals."""
        symbol = stock_info["symbol"]
        base_price = BASE_PRICES.get(symbol, 1000)
        
        # Generate price with random fluctuation
        change_pct = random.uniform(-5, 5)
        current_price = base_price * (1 + change_pct / 100)
        price_change = current_price - base_price
        
        # Generate technical indicators
        rsi = random.uniform(20, 80)
        macd_signal = random.choice(["BULLISH", "BEARISH", "NEUTRAL"])
        volume_surge = random.uniform(0.5, 3.0)  # Volume vs average
        
        # Moving average signals
        above_20dma = random.choice([True, False])
        above_50dma = random.choice([True, False])
        above_200dma = random.choice([True, False])
        
        # Fibonacci Retracement Analysis
        # Simulate swing high and swing low for Fib calculation
        swing_range = base_price * random.uniform(0.08, 0.15)  # 8-15% swing range
        swing_high = base_price + swing_range / 2
        swing_low = base_price - swing_range / 2
        
        # Calculate Fibonacci levels
        fib_range = swing_high - swing_low
        fib_levels = {
            "swing_high": round(swing_high, 2),
            "swing_low": round(swing_low, 2),
            "fib_236": round(swing_high - fib_range * 0.236, 2),  # 23.6%
            "fib_382": round(swing_high - fib_range * 0.382, 2),  # 38.2%
            "fib_500": round(swing_high - fib_range * 0.500, 2),  # 50%
            "fib_618": round(swing_high - fib_range * 0.618, 2),  # 61.8% (Golden ratio)
            "fib_786": round(swing_high - fib_range * 0.786, 2),  # 78.6%
        }
        
        # Determine where current price is relative to Fib levels
        if current_price >= fib_levels["fib_236"]:
            fib_zone = "ABOVE_236"
            fib_signal = "BULLISH"
            nearest_support = fib_levels["fib_236"]
            nearest_resistance = fib_levels["swing_high"]
        elif current_price >= fib_levels["fib_382"]:
            fib_zone = "236_TO_382"
            fib_signal = "BULLISH"
            nearest_support = fib_levels["fib_382"]
            nearest_resistance = fib_levels["fib_236"]
        elif current_price >= fib_levels["fib_500"]:
            fib_zone = "382_TO_500"
            fib_signal = "NEUTRAL"
            nearest_support = fib_levels["fib_500"]
            nearest_resistance = fib_levels["fib_382"]
        elif current_price >= fib_levels["fib_618"]:
            fib_zone = "500_TO_618"
            fib_signal = "NEUTRAL"
            nearest_support = fib_levels["fib_618"]
            nearest_resistance = fib_levels["fib_500"]
        elif current_price >= fib_levels["fib_786"]:
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
        
        # Calculate composite score
        score = 50  # Base neutral score
        
        # RSI contribution
        if rsi < 30:
            score += 15  # Oversold - potential buy
            rsi_signal = "OVERSOLD"
        elif rsi > 70:
            score -= 15  # Overbought - potential sell
            rsi_signal = "OVERBOUGHT"
        else:
            rsi_signal = "NEUTRAL"
        
        # MACD contribution
        if macd_signal == "BULLISH":
            score += 20
        elif macd_signal == "BEARISH":
            score -= 20
        
        # Moving average contribution
        if above_20dma:
            score += 5
        if above_50dma:
            score += 5
        if above_200dma:
            score += 5
        
        # Volume surge contribution
        if volume_surge > 2:
            score += 10 if change_pct > 0 else -10
        
        # Fibonacci contribution
        if fib_signal == "BULLISH":
            score += 10
        elif fib_signal == "BEARISH":
            score -= 10
        
        # Clamp score to 0-100
        score = max(0, min(100, score))
        
        # Determine recommendation
        if score >= 70:
            recommendation = "STRONG BUY"
            rec_color = "#00E676"
        elif score >= 55:
            recommendation = "BUY"
            rec_color = "#69F0AE"
        elif score <= 30:
            recommendation = "STRONG SELL"
            rec_color = "#FF5252"
        elif score <= 45:
            recommendation = "SELL"
            rec_color = "#FF8A80"
        else:
            recommendation = "HOLD"
            rec_color = "#9E9E9E"
        
        # Calculate trading levels based on recommendation
        if recommendation in ["STRONG BUY", "BUY"]:
            # For BUY: Entry near current, Target above, Stoploss below
            entry_price = round(current_price * 0.998, 2)  # Slightly below current
            target_price = round(current_price * 1.03, 2)  # 3% profit target
            stoploss_price = round(current_price * 0.985, 2)  # 1.5% stoploss
            risk_reward = "1:2"
        elif recommendation in ["STRONG SELL", "SELL"]:
            # For SELL: Short entry near current, Target below, Stoploss above
            entry_price = round(current_price * 1.002, 2)  # Slightly above current
            target_price = round(current_price * 0.97, 2)  # 3% profit target
            stoploss_price = round(current_price * 1.015, 2)  # 1.5% stoploss
            risk_reward = "1:2"
        else:
            # For HOLD: No clear levels
            entry_price = None
            target_price = None
            stoploss_price = None
            risk_reward = "N/A"
        
        # Generate reasons for the recommendation
        reasons = []
        reasons_hi = []  # Hindi reasons
        
        # RSI reasons
        if rsi < 30:
            reasons.append(f"RSI at {round(rsi, 1)} indicates OVERSOLD - bounce expected")
            reasons_hi.append(f"RSI {round(rsi, 1)} पर है - OVERSOLD, वापसी की उम्मीद")
        elif rsi > 70:
            reasons.append(f"RSI at {round(rsi, 1)} indicates OVERBOUGHT - correction expected")
            reasons_hi.append(f"RSI {round(rsi, 1)} पर है - OVERBOUGHT, गिरावट की उम्मीद")
        else:
            reasons.append(f"RSI at {round(rsi, 1)} - neutral zone")
            reasons_hi.append(f"RSI {round(rsi, 1)} पर है - neutral zone")
        
        # MACD reasons
        if macd_signal == "BULLISH":
            reasons.append("MACD shows bullish crossover - uptrend signal")
            reasons_hi.append("MACD bullish crossover दिखा रहा है - uptrend")
        elif macd_signal == "BEARISH":
            reasons.append("MACD shows bearish crossover - downtrend signal")
            reasons_hi.append("MACD bearish crossover दिखा रहा है - downtrend")
        
        # Moving average reasons
        ma_bullish = sum([above_20dma, above_50dma, above_200dma])
        if ma_bullish >= 2:
            reasons.append(f"Price above {ma_bullish}/3 moving averages - bullish structure")
            reasons_hi.append(f"Price {ma_bullish}/3 moving averages के ऊपर है - bullish")
        elif ma_bullish <= 1:
            reasons.append(f"Price below most moving averages - bearish structure")
            reasons_hi.append(f"Price ज्यादातर moving averages के नीचे है - bearish")
        
        # Volume reasons
        if volume_surge > 2:
            if change_pct > 0:
                reasons.append(f"Volume surge {round(volume_surge, 1)}x with positive price - strong buying")
                reasons_hi.append(f"Volume {round(volume_surge, 1)}x बढ़ा है positive price के साथ - strong buying")
            else:
                reasons.append(f"Volume surge {round(volume_surge, 1)}x with negative price - strong selling")
                reasons_hi.append(f"Volume {round(volume_surge, 1)}x बढ़ा है negative price के साथ - strong selling")
        
        # Fibonacci reasons
        if fib_signal == "BULLISH":
            reasons.append(f"📐 Fib: Price above 38.2% level - bullish zone, support at ₹{nearest_support}")
            reasons_hi.append(f"📐 Fib: Price 38.2% level के ऊपर - bullish zone, support ₹{nearest_support}")
        elif fib_signal == "BEARISH":
            reasons.append(f"📐 Fib: Price below 61.8% level - bearish zone, resistance at ₹{nearest_resistance}")
            reasons_hi.append(f"📐 Fib: Price 61.8% level के नीचे - bearish zone, resistance ₹{nearest_resistance}")
        else:
            reasons.append(f"📐 Fib: Price in consolidation zone (38.2%-61.8%), watch for breakout")
            reasons_hi.append(f"📐 Fib: Price consolidation zone में है (38.2%-61.8%), breakout का इंतज़ार करें")
        
        return {
            "symbol": symbol,
            "name": stock_info["name"],
            "sector": stock_info["sector"],
            "price": round(current_price, 2),
            "change": round(price_change, 2),
            "change_pct": round(change_pct, 2),
            "volume_surge": round(volume_surge, 1),
            "indicators": {
                "rsi": round(rsi, 1),
                "rsi_signal": rsi_signal,
                "macd": macd_signal,
                "above_20dma": above_20dma,
                "above_50dma": above_50dma,
                "above_200dma": above_200dma,
                "fib_signal": fib_signal
            },
            "fib_levels": fib_levels,
            "score": score,
            "recommendation": recommendation,
            "rec_color": rec_color,
            "trading_levels": {
                "entry": entry_price,
                "target": target_price,
                "stoploss": stoploss_price,
                "risk_reward": risk_reward
            },
            "reasons": reasons,
            "reasons_hi": reasons_hi
        }
    
    def get_screener_data(self, filter_type: str = "all") -> Dict:
        """Get stock screener data with optional filtering."""
        all_stocks = [self._generate_stock_data(s) for s in STOCK_LIST]
        
        # Sort by score descending
        all_stocks.sort(key=lambda x: x["score"], reverse=True)
        
        # Filter based on type
        if filter_type == "buy":
            stocks = [s for s in all_stocks if s["recommendation"] in ["STRONG BUY", "BUY"]]
        elif filter_type == "sell":
            stocks = [s for s in all_stocks if s["recommendation"] in ["STRONG SELL", "SELL"]]
        elif filter_type == "top_gainers":
            stocks = sorted(all_stocks, key=lambda x: x["change_pct"], reverse=True)[:10]
        elif filter_type == "top_losers":
            stocks = sorted(all_stocks, key=lambda x: x["change_pct"])[:10]
        else:
            stocks = all_stocks
        
        # Get summary counts
        buy_count = len([s for s in all_stocks if s["recommendation"] in ["STRONG BUY", "BUY"]])
        sell_count = len([s for s in all_stocks if s["recommendation"] in ["STRONG SELL", "SELL"]])
        hold_count = len([s for s in all_stocks if s["recommendation"] == "HOLD"])
        
        return {
            "status": "success",
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {
                "total_stocks": len(all_stocks),
                "buy_signals": buy_count,
                "sell_signals": sell_count,
                "hold_signals": hold_count
            },
            "stocks": stocks
        }
    
    def get_stock_detail(self, symbol: str) -> Dict:
        """Get detailed data for a specific stock."""
        stock_info = next((s for s in STOCK_LIST if s["symbol"] == symbol.upper()), None)
        if not stock_info:
            return {"status": "error", "message": f"Stock {symbol} not found"}
        
        data = self._generate_stock_data(stock_info)
        data["status"] = "success"
        return data


# Global instance
stock_screener = StockScreener()
