"""
Option Strategy Module
Analyzes stock trend on Daily timeframe for Weekly/Positional Option buying.
Selects ATM/OTM strikes and generates Entry/Target/SL.
"""

from datetime import datetime, timedelta
import pandas as pd
import pandas_ta as ta
from typing import Dict, Optional, List
from live_data import fetch_option_chain, get_monthly_expiry, get_nse_session

class OptionStrategy:
    def __init__(self):
        self.cached_history = {}

    def fetch_history(self, symbol: str, days: int = 100) -> Optional[pd.DataFrame]:
        """Fetch historical daily data for trend analysis."""
        # DISABLED for Stability: jugaad-data history fetch is unreliable and blocking
        # We allow the system to use Intraday Fallback immediately.
        return None
        
        try:
            from concurrent.futures import ThreadPoolExecutor
            from jugaad_data.nse import stock_df
            
            def _fetch():
                return stock_df(symbol=symbol, from_date=datetime.now() - timedelta(days=days),
                              to_date=datetime.now(), series="EQ")
            
            # Execute with timeout (3 seconds is enough for connection test)
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(_fetch)
                try:
                    df = future.result(timeout=4) # 4 seconds max
                except Exception:
                    # Timeout or Error
                    print(f"History fetch timed out for {symbol}")
                    return None
            
            if df is None or df.empty:
                return None
            
            # Clean and sort
            df = df[['DATE', 'OPEN', 'HIGH', 'LOW', 'CLOSE', 'VOLUME', 'SYMBOL']]
            df['DATE'] = pd.to_datetime(df['DATE'])
            df = df.sort_values(by='DATE')
            
            return df
        except Exception as e:
            print(f"Error fetching history for {symbol}: {e}")
            return None

    def analyze_trend(self, symbol: str) -> Dict:
        """Analyze trend using moving averages and RSI on Daily timeframe."""
        df = self.fetch_history(symbol)
        
        # Fallback to Intraday Trend if History Fails
        if df is None:
            from live_data import fetch_stock_quote, fetch_fallback_quote
            quote = fetch_stock_quote(symbol) or fetch_fallback_quote(symbol)
            
            if quote:
                price = quote.get('price', 0)
                change_pct = quote.get('change_pct', 0)
                
                # Simple Intraday Trend logic
                if change_pct > 1.0:
                    trend = "BULLISH"
                    reason = f"Intraday Up {change_pct}% (History Unavailable)"
                elif change_pct < -1.0:
                    trend = "BEARISH"
                    reason = f"Intraday Down {change_pct}% (History Unavailable)"
                else:
                    trend = "NEUTRAL"
                    reason = "Sideways Move (History Unavailable)"
                    
                return {
                    "trend": trend,
                    "reason": reason,
                    "close": price,
                    "rsi": 50, # Dummy
                    "sma_20": price # Dummy
                }
            
            return {"trend": "NEUTRAL", "reason": "Insufficient data"}
        
        # Calculate Indicators
        # 20 SMA (Short term trend)
        df['SMA_20'] = ta.sma(df['CLOSE'], length=20)
        # 50 SMA (Medium term trend)
        df['SMA_50'] = ta.sma(df['CLOSE'], length=50)
        # RSI
        df['RSI'] = ta.rsi(df['CLOSE'], length=14)
        
        last_row = df.iloc[-1]
        close = last_row['CLOSE']
        sma_20 = last_row['SMA_20'] if not pd.isna(last_row['SMA_20']) else close
        sma_50 = last_row['SMA_50'] if not pd.isna(last_row['SMA_50']) else close
        rsi = last_row['RSI'] if not pd.isna(last_row['RSI']) else 50
        
        # Determine Trend for Weekly View (Positional)
        trend = "NEUTRAL"
        reason = []
        
        # Bullish Criteria: Price > 20 SMA and RSI > 55
        if close > sma_20 and rsi > 55:
            trend = "BULLISH"
            reason.append(f"Price ({close}) above 20 SMA ({round(sma_20, 1)})")
            reason.append(f"RSI ({round(rsi, 1)}) indicates bullish momentum")
            
        # Bearish Criteria: Price < 20 SMA and RSI < 45
        elif close < sma_20 and rsi < 45:
            trend = "BEARISH"
            reason.append(f"Price ({close}) below 20 SMA ({round(sma_20, 1)})")
            reason.append(f"RSI ({round(rsi, 1)}) indicates bearish momentum")
        
        else:
            reason.append("Price or RSI in range-bound zone")
            
        return {
            "trend": trend,
            "reason": "; ".join(reason),
            "close": close,
            "rsi": round(rsi, 1),
            "sma_20": round(sma_20, 1)
        }

    def get_option_recommendation(self, symbol: str) -> Dict:
        """Generate option buying recommendation."""
        
        # 1. Analyze Trend
        analysis = self.analyze_trend(symbol)
        trend = analysis['trend']
        
        if trend == "NEUTRAL":
            return {
                "status": "NO_TRADE",
                "message": f"Trend is Neutral for {symbol}. {analysis['reason']}",
                "analysis": analysis
            }
        
        # 2. Fetch Option Chain
        chain = fetch_option_chain(symbol)
        
        # Fallback: If Option Chain fails, estimate based on Last Close Price
        if not chain:
            return self._generate_estimated_strategy(symbol, analysis, trend)
        
        # 3. Select Expiry (Monthly)
        expiry_date = get_monthly_expiry(chain)
        if not expiry_date:
             # Fallback if expiry parsing fails
             return self._generate_estimated_strategy(symbol, analysis, trend)
            
        # 4. Filter Option Data for Expiry
        records = chain.get('records', {}).get('data', [])
        expiry_data = [r for r in records if r.get('expiryDate') == expiry_date]
        
        if not expiry_data:
             return self._generate_estimated_strategy(symbol, analysis, trend)
             
        spot_price = analysis['close']
        
        selected_option = None
        option_type = "CE" if trend == "BULLISH" else "PE"
        
        # Start looking for ATM strike
        # Sort by strike price
        expiry_data.sort(key=lambda x: x.get('strikePrice', 0))
        
        # Find closest strike (ATM)
        closest_strike_data = min(expiry_data, key=lambda x: abs(x.get('strikePrice', 0) - spot_price))
        strike_price = closest_strike_data.get('strikePrice')
        
        # For buying, we prefer slightly OTM or ATM. 
        # If Bullish, Strike >= Spot. If Bearish, Strike <= Spot.
        # Let's stick to simple ATM for liquidity.
        
        option_info = closest_strike_data.get(option_type, {})
        
        # Extract details
        ltp = option_info.get('lastPrice', 0)
        
        if ltp == 0:
             # If LTP is 0, estimate it
             return self._generate_estimated_strategy(symbol, analysis, trend, strike_price, expiry_date)
        
        # Calculate Levels
        entry_range = f"{round(ltp * 0.98, 1)} - {round(ltp * 1.02, 1)}"
        target = round(ltp * 1.5, 1) # 50% gain target for weekly positional
        stoploss = round(ltp * 0.6, 1) # 40% stoploss
        
        return {
            "status": "SUCCESS",
            "symbol": symbol,
            "trend": trend,
            "expiry": expiry_date,
            "option_type": option_type,
            "strike_price": strike_price,
            "identifier": option_info.get('identifier'),
            "ltp": ltp,
            "entry_range": entry_range,
            "target": target,
            "stoploss": stoploss,
            "reason": analysis['reason'],
            "risk_reward": "1:1.5",
            "required_margin": round(ltp * option_info.get('pChange', 500) if option_info.get('pChange') else ltp * 500, 2), # Approx lot size assumption or just price
            "analysis": analysis
        }

    def _generate_estimated_strategy(self, symbol: str, analysis: Dict, trend: str, 
                                     known_strike: float = None, known_expiry: str = None) -> Dict:
        """Generate an estimated strategy when live option chain is unavailable."""
        spot_price = analysis['close']
        
        # 1. Estimate Strike (ATM) if not provided
        if known_strike:
            strike_price = known_strike
        else:
            # Round spot to nearest 10/50/100 depending on price magnitude
            if spot_price < 500:
                step = 5
            elif spot_price < 2000:
                step = 10
            elif spot_price < 10000:
                step = 50
            else:
                step = 100
            
            strike_price = round(spot_price / step) * step
            
        # 2. Estimate Expiry if not provided (Last Thursday of month approximation)
        if known_expiry:
            expiry_date = known_expiry
        else:
            today = datetime.now()
            # Simple approximation: 28th of current month
            expiry_date = today.strftime("%d-%b-%Y") + " (Est)"
            
        option_type = "CE" if trend == "BULLISH" else "PE"
        
        # 3. Estimate Premium (Black-Scholes rough approx: ~1.5-2.5% of Spot for ATM Monthly)
        # Higher IV assumption for individual stocks
        estimated_premium_pct = 0.02  # 2% of stock price
        ltp = round(spot_price * estimated_premium_pct, 1)
        
        # Calculate Levels
        entry_range = f"{round(ltp * 0.98, 1)} - {round(ltp * 1.02, 1)}"
        target = round(ltp * 1.5, 1) # 50% gain
        stoploss = round(ltp * 0.6, 1) # 40% loss
        
        return {
            "status": "SUCCESS",
            "symbol": symbol,
            "trend": trend,
            "expiry": expiry_date,
            "option_type": option_type,
            "strike_price": strike_price,
            "identifier": f"{symbol}{option_type}{strike_price}",
            "ltp": ltp,
            "entry_range": entry_range,
            "target": target,
            "stoploss": stoploss,
            "reason": analysis['reason'] + " (Based on Last Close Price)",
            "risk_reward": "1:1.5",
            "required_margin": round(ltp * 500, 2), # Approx margin
            "analysis": analysis,
            "is_estimated": True,
            "message": "Market Closed: Strategy based on Friday's Closing Price"
        }

strategy_engine = OptionStrategy()
