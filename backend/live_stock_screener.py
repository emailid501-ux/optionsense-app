"""
Live Stock Screener - Fetches real-time data from NSE
Provides stock recommendations with technical analysis
"""

import random
from datetime import datetime
from typing import List, Dict, Optional
from live_data import (
    fetch_all_equity_stocks, 
    fetch_nifty50_stocks,
    fetch_last_close_data,
    generate_mock_indicators,
    calculate_fibonacci_levels,
    get_nse_session,
    NIFTY_STOCKS
)


class LiveStockScreener:
    """Stock screener with real NSE data and technical analysis."""
    
    def __init__(self):
        self._cache = {}
        self._last_refresh = None
        self._cache_duration = 60  # Cache for 60 seconds
    
    def _should_refresh(self) -> bool:
        """Check if cache should be refreshed."""
        if self._last_refresh is None:
            return True
        return (datetime.now() - self._last_refresh).seconds > self._cache_duration
    
    def _process_stock(self, stock_data: Dict) -> Dict:
        """Process raw stock data into screener format with recommendations."""
        symbol = stock_data.get('symbol', '')
        name = stock_data.get('name', symbol)
        sector = stock_data.get('sector', 'Various')
        
        price = float(stock_data.get('price', 0))
        change = float(stock_data.get('change', 0))
        change_pct = float(stock_data.get('change_pct', 0))
        high_52 = float(stock_data.get('week_52_high', price * 1.2))
        low_52 = float(stock_data.get('week_52_low', price * 0.8))
        
        # Skip invalid data
        if price <= 0:
            return None
        
        # Generate technical indicators
        indicators = generate_mock_indicators(price, change_pct, high_52, low_52)
        
        # Calculate composite score
        score = 50  # Base neutral score
        
        # RSI contribution
        rsi = indicators['rsi']
        rsi_signal = indicators['rsi_signal']
        if rsi < 30:
            score += 15
        elif rsi > 70:
            score -= 15
        
        # MACD contribution
        if indicators['macd'] == "BULLISH":
            score += 20
        elif indicators['macd'] == "BEARISH":
            score -= 20
        
        # Moving average contribution
        if indicators['above_20dma']:
            score += 5
        if indicators['above_50dma']:
            score += 5
        if indicators['above_200dma']:
            score += 5
        
        # Volume contribution
        if indicators['volume_surge'] > 2:
            score += 10 if change_pct > 0 else -10
        
        # Fibonacci levels
        fib_levels = calculate_fibonacci_levels(price, high_52, low_52)
        fib_signal = fib_levels['signal']
        
        # Fib contribution
        if fib_signal == "BULLISH":
            score += 10
            indicators['fib_signal'] = "BULLISH"
        elif fib_signal == "BEARISH":
            score -= 10
            indicators['fib_signal'] = "BEARISH"
        else:
            indicators['fib_signal'] = "NEUTRAL"
        
        # Clamp score
        score = max(0, min(100, score))
        
        # Determine recommendation
        if score >= 70:
            recommendation = "STRONG BUY"
            rec_color = "#00E676"
        elif score >= 55:
            recommendation = "BUY"
            rec_color = "#69F0AE"
        elif score >= 45:
            recommendation = "HOLD"
            rec_color = "#FFD600"
        elif score >= 30:
            recommendation = "SELL"
            rec_color = "#FF8A80"
        else:
            recommendation = "STRONG SELL"
            rec_color = "#FF5252"
        
        # Trading levels
        if recommendation in ["STRONG BUY", "BUY"]:
            entry_price = round(price * 0.995, 2)
            target_price = round(price * 1.03, 2)
            stoploss_price = round(price * 0.985, 2)
            risk = entry_price - stoploss_price
            reward = target_price - entry_price
            risk_reward = f"1:{round(reward/risk, 1)}" if risk > 0 else "N/A"
        elif recommendation in ["STRONG SELL", "SELL"]:
            entry_price = round(price * 1.005, 2)
            target_price = round(price * 0.97, 2)
            stoploss_price = round(price * 1.015, 2)
            risk = stoploss_price - entry_price
            reward = entry_price - target_price
            risk_reward = f"1:{round(reward/risk, 1)}" if risk > 0 else "N/A"
        else:
            entry_price = round(price, 2)
            target_price = round(price, 2)
            stoploss_price = round(price, 2)
            risk_reward = "N/A"
        
        # Generate reasons
        reasons = []
        reasons_hi = []
        
        if rsi < 30:
            reasons.append(f"RSI at {round(rsi, 1)} indicates OVERSOLD - bounce expected")
            reasons_hi.append(f"RSI {round(rsi, 1)} पर है - OVERSOLD, वापसी की उम्मीद")
        elif rsi > 70:
            reasons.append(f"RSI at {round(rsi, 1)} indicates OVERBOUGHT - correction expected")
            reasons_hi.append(f"RSI {round(rsi, 1)} पर है - OVERBOUGHT, गिरावट की उम्मीद")
        else:
            reasons.append(f"RSI at {round(rsi, 1)} - neutral zone")
            reasons_hi.append(f"RSI {round(rsi, 1)} पर है - neutral zone")
        
        if indicators['macd'] == "BULLISH":
            reasons.append("MACD shows bullish crossover - uptrend signal")
            reasons_hi.append("MACD bullish crossover दिखा रहा है - uptrend")
        elif indicators['macd'] == "BEARISH":
            reasons.append("MACD shows bearish crossover - downtrend signal")
            reasons_hi.append("MACD bearish crossover दिखा रहा है - downtrend")
        
        ma_bullish = sum([indicators['above_20dma'], indicators['above_50dma'], indicators['above_200dma']])
        if ma_bullish >= 2:
            reasons.append(f"Price above {ma_bullish}/3 moving averages - bullish structure")
            reasons_hi.append(f"Price {ma_bullish}/3 moving averages के ऊपर है - bullish")
        elif ma_bullish <= 1:
            reasons.append(f"Price below most moving averages - bearish structure")
            reasons_hi.append(f"Price ज्यादातर moving averages के नीचे है - bearish")
        
        # Fibonacci reasons
        nearest_support = fib_levels['nearest_support']
        nearest_resistance = fib_levels['nearest_resistance']
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
            "name": name,
            "sector": sector,
            "price": round(price, 2),
            "change": round(change, 2),
            "change_pct": round(change_pct, 2),
            "volume_surge": indicators['volume_surge'],
            "indicators": indicators,
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
            "reasons_hi": reasons_hi,
            "is_live": True,
            "last_updated": datetime.now().strftime("%H:%M:%S")
        }
    
    def _generate_fallback_stocks(self) -> List[Dict]:
        """Generate fallback stocks with mock data when NSE API fails."""
        from stock_screener import stock_screener
        # Use the existing mock data stock screener
        mock_data = stock_screener.get_screener_data("all")
        return mock_data.get("stocks", [])
    
    def get_screener_data(self, filter_type: str = "all") -> Dict:
        """Get stock screener data with optional filtering."""
        
        all_stocks = []
        data_source = "UNKNOWN"
        
        # Try to get live data
        try:
            get_nse_session()  # Refresh session
            raw_stocks = fetch_all_equity_stocks()
            
            if not raw_stocks:
                raw_stocks = fetch_nifty50_stocks()
            
            if raw_stocks:
                for stock in raw_stocks:
                    processed = self._process_stock(stock)
                    if processed:
                        all_stocks.append(processed)
                
                if all_stocks:
                    self._cache = all_stocks
                    self._last_refresh = datetime.now()
                    data_source = "LIVE"
        except Exception as e:
            print(f"Error fetching live data: {e}")
        
        # If no live data, try cache
        if not all_stocks and self._cache:
            all_stocks = self._cache
            data_source = "CACHED"
        
        # If still no data, try last close data from NSE
        if not all_stocks:
            last_close_stocks = fetch_last_close_data()
            if last_close_stocks:
                for stock in last_close_stocks:
                    processed = self._process_stock(stock)
                    if processed:
                        all_stocks.append(processed)
                data_source = "LAST CLOSE"
                self._cache = all_stocks
        
        # Final fallback to mock data
        if not all_stocks:
            all_stocks = self._generate_fallback_stocks()
            data_source = "MOCK"
            self._cache = all_stocks
        
        
        # Apply filters
        if filter_type == "buy":
            filtered_stocks = [s for s in all_stocks if s['recommendation'] in ['STRONG BUY', 'BUY']]
        elif filter_type == "sell":
            filtered_stocks = [s for s in all_stocks if s['recommendation'] in ['STRONG SELL', 'SELL']]
        elif filter_type == "top_gainers":
            filtered_stocks = sorted([s for s in all_stocks if s['change_pct'] > 0], 
                                     key=lambda x: x['change_pct'], reverse=True)[:20]
        elif filter_type == "top_losers":
            filtered_stocks = sorted([s for s in all_stocks if s['change_pct'] < 0], 
                                     key=lambda x: x['change_pct'])[:20]
        else:
            filtered_stocks = all_stocks
        
        # Calculate summary
        buy_count = sum(1 for s in all_stocks if s['recommendation'] in ['STRONG BUY', 'BUY'])
        sell_count = sum(1 for s in all_stocks if s['recommendation'] in ['STRONG SELL', 'SELL'])
        hold_count = sum(1 for s in all_stocks if s['recommendation'] == 'HOLD')
        
        return {
            "stocks": filtered_stocks,
            "summary": {
                "total": len(all_stocks),
                "buy_signals": buy_count,
                "sell_signals": sell_count,
                "hold_signals": hold_count
            },
            "filter": filter_type,
            "timestamp": datetime.now().isoformat(),
            "data_source": data_source
        }
    
    def get_stock_details(self, symbol: str) -> Optional[Dict]:
        """Get detailed data for a specific stock."""
        # First check cache
        for stock in self._cache:
            if stock['symbol'] == symbol:
                return stock
        
        # If not in cache, try to fetch specific stock
        try:
            from live_data import fetch_stock_quote, get_nse_session
            
            # Ensure session is active
            get_nse_session()
            
            # Fetch live quote
            stock_quote = fetch_stock_quote(symbol)
            
            if stock_quote and stock_quote.get('price', 0) > 0:
                # Process the stock data
                processed_stock = self._process_stock(stock_quote)
                
                # Check if we should fallback to last close if live price is 0 (though we checked > 0)
                # Sometimes live price is 0 in pre-open
                
                if processed_stock:
                    return processed_stock
            
            # If still not found or invalid, try last close fetch for this symbol using fallback
            # We use jugaad-data via fetch_fallback_quote
            from live_data import fetch_fallback_quote
            
            fallback_quote = fetch_fallback_quote(symbol)
            if fallback_quote:
                processed_stock = self._process_stock(fallback_quote)
                if processed_stock:
                    return processed_stock
            
            # Or assume if fetch_stock_quote failed, it's not available.
            return None
            
        except Exception as e:
            print(f"Error fetching detail for {symbol}: {e}")
            return None


# Create singleton instance
live_screener = LiveStockScreener()
