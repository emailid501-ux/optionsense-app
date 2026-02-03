"""Mock data provider simulating real market data for OptionSense."""
import random
import math
from datetime import datetime, time
from typing import Dict, List, Tuple

from algorithms import (
    get_relevant_strikes,
    get_atm_strike,
    calculate_oi_signal,
    calculate_sentiment_score,
    get_bar_color_for_oi
)


# Base prices for indices
BASE_PRICES = {
    "NIFTY": 25350.0,
    "BANKNIFTY": 53800.0,
    "FINNIFTY": 24500.0,
    "MIDCPNIFTY": 12800.0
}

# Strike step sizes
STRIKE_STEPS = {
    "NIFTY": 50,
    "BANKNIFTY": 100,
    "FINNIFTY": 50,
    "MIDCPNIFTY": 25
}


class MarketDataProvider:
    """Provides simulated market data for testing."""
    
    def __init__(self):
        self._price_offset = {}
        self._last_update = {}
        self._oi_data = {}
        self._pcr_history = {}
        self._scenario = "BULLISH"
        
        # Try to sync base prices with real market data on startup
        try:
            from live_data import fetch_option_chain
            from jugaad_data.nse import NSELive
            
            print("Syncing mock data with real market prices...")
            nse = NSELive()
            
            # Update each index base price
            for symbol in BASE_PRICES.keys():
                try:
                    # Use fetch_option_chain to get underlying price (more reliable)
                    chain_data = fetch_option_chain(symbol)
                    
                    if chain_data and 'records' in chain_data:
                        underlying_value = chain_data['records'].get('underlyingValue')
                        if underlying_value:
                            real_price = float(underlying_value)
                            BASE_PRICES[symbol] = real_price
                            print(f"Updated {symbol} base price to {real_price}")
                except Exception as e:
                    print(f"Could not sync {symbol}: {e}")
                    
        except Exception as e:
            print(f"Mock data sync failed: {e}")
        
    def _is_market_open(self) -> bool:
        """Check if Indian market is open (9:15 AM to 3:30 PM IST)."""
        now = datetime.now()
        market_open = time(9, 15)
        market_close = time(15, 30)
        
        # Check if weekday (0-4 = Mon-Fri), but allow Budget Day (Feb 1st 2026)
        is_budget_day = now.date() == datetime(2026, 2, 1).date()
        if now.weekday() > 4 and not is_budget_day:
            return False
        
        current_time = now.time()
        return market_open <= current_time <= market_close
    
    def _generate_price_movement(self, symbol: str) -> float:
        """Generate realistic price movement based on scenario."""
        base = BASE_PRICES[symbol]
        
        # Simulate different market scenarios
        if self._scenario == "BULLISH":
            trend = random.uniform(0.1, 0.5)  # Upward bias
        elif self._scenario == "BEARISH":
            trend = random.uniform(-0.5, -0.1)  # Downward bias
        elif self._scenario == "VOLATILE":
            trend = random.uniform(-1.0, 1.0)  # High volatility
        else:  # SIDEWAYS
            trend = random.uniform(-0.2, 0.2)  # Low movement
        
        # Add some randomness
        noise = random.gauss(0, 0.15)
        pct_change = (trend + noise) / 100
        
        if symbol not in self._price_offset:
            self._price_offset[symbol] = 0
        
        self._price_offset[symbol] += base * pct_change
        self._price_offset[symbol] = max(-base * 0.03, min(base * 0.03, self._price_offset[symbol]))
        
        return base + self._price_offset[symbol]
    
    def _generate_vwap(self, symbol: str, current_price: float) -> Tuple[float, bool]:
        """Generate VWAP value and bullish/bearish status."""
        # VWAP typically stays close to but slightly behind price
        offset = random.uniform(-0.3, 0.2) / 100 * current_price
        vwap = current_price + offset
        
        is_bullish = current_price > vwap
        return (round(vwap, 2), is_bullish)
    
    def _generate_pcr(self, symbol: str) -> Tuple[float, str]:
        """Generate PCR value and trend."""
        # PCR typically ranges from 0.5 to 1.5
        if self._scenario == "BULLISH":
            pcr = random.uniform(1.0, 1.4)
        elif self._scenario == "BEARISH":
            pcr = random.uniform(0.6, 0.9)
        else:
            pcr = random.uniform(0.8, 1.2)
        
        # Track trend
        if symbol not in self._pcr_history:
            self._pcr_history[symbol] = []
        
        self._pcr_history[symbol].append(pcr)
        if len(self._pcr_history[symbol]) > 5:
            self._pcr_history[symbol] = self._pcr_history[symbol][-5:]
        
        # Determine trend
        if len(self._pcr_history[symbol]) >= 2:
            avg_old = sum(self._pcr_history[symbol][:-1]) / len(self._pcr_history[symbol][:-1])
            if pcr > avg_old + 0.05:
                trend = "RISING"
            elif pcr < avg_old - 0.05:
                trend = "FALLING"
            else:
                trend = "STABLE"
        else:
            trend = "STABLE"
        
        return (round(pcr, 2), trend)
    
    def _generate_oi_changes(self, symbol: str, atm: int) -> List[Dict]:
        """Generate OI changes for each strike."""
        step = STRIKE_STEPS[symbol]
        strikes = get_relevant_strikes(atm, step)
        oi_data = []
        
        for strike in strikes:
            distance_from_atm = abs(strike - atm)
            
            # Generate OI changes based on scenario
            if self._scenario == "BULLISH":
                # Call unwinding near ATM, Put writing
                ce_change = random.randint(-80000, 20000) if distance_from_atm < step * 2 else random.randint(-30000, 40000)
                pe_change = random.randint(10000, 150000) if distance_from_atm < step * 3 else random.randint(-20000, 80000)
            elif self._scenario == "BEARISH":
                # Call writing, Put unwinding
                ce_change = random.randint(20000, 120000) if distance_from_atm < step * 2 else random.randint(-10000, 60000)
                pe_change = random.randint(-100000, 10000) if distance_from_atm < step * 3 else random.randint(-40000, 30000)
            else:  # SIDEWAYS or VOLATILE
                ce_change = random.randint(-50000, 50000)
                pe_change = random.randint(-50000, 50000)
            
            oi_data.append({
                "strike": strike,
                "ce_change": ce_change,
                "pe_change": pe_change,
                "ce_bar_color": get_bar_color_for_oi(ce_change, is_call=True),
                "pe_bar_color": get_bar_color_for_oi(pe_change, is_call=False),
                "is_atm": strike == atm
            })
        
        return oi_data
    
    def get_dashboard_data(self, symbol: str) -> Dict:
        """Get complete dashboard data for a symbol."""
        # Rotate scenario occasionally for demo purposes
        scenarios = ["BULLISH", "BEARISH", "SIDEWAYS", "VOLATILE"]
        self._scenario = random.choice(scenarios)
        
        current_price = self._generate_price_movement(symbol)
        base_price = BASE_PRICES[symbol]
        price_change = current_price - base_price
        price_change_pct = (price_change / base_price) * 100
        
        vwap, is_vwap_bullish = self._generate_vwap(symbol, current_price)
        pcr, pcr_trend = self._generate_pcr(symbol)
        
        # Get OI data for signal calculation
        step = STRIKE_STEPS[symbol]
        atm = get_atm_strike(current_price, step)
        oi_data = self._generate_oi_changes(symbol, atm)
        
        # Calculate total COI for signal
        total_ce_change = sum(d["ce_change"] for d in oi_data)
        total_pe_change = sum(d["pe_change"] for d in oi_data)
        
        oi_message, oi_status, oi_color = calculate_oi_signal(total_ce_change, total_pe_change)
        
        score, label, sentiment_color = calculate_sentiment_score(
            pcr, current_price, vwap, oi_status
        )
        
        return {
            "status": "success",
            "symbol": symbol,
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "market_status": "OPEN" if self._is_market_open() else "CLOSED",
            "data": {
                "price": round(current_price, 2),
                "price_change": round(price_change, 2),
                "price_change_pct": round(price_change_pct, 2),
                "vwap_signal": {
                    "value": vwap,
                    "is_bullish": is_vwap_bullish,
                    "message": "Price > VWAP" if is_vwap_bullish else "Price < VWAP"
                },
                "pcr": {
                    "value": pcr,
                    "trend": pcr_trend
                },
                "sentiment": {
                    "score": score,
                    "label": label,
                    "color": sentiment_color
                },
                "oi_alert": {
                    "message": oi_message,
                    "bg_color": oi_color
                }
            }
        }
    
    def get_oi_details(self, symbol: str, spot_price: float = None) -> Dict:
        """Get OI details for option chain table."""
        if spot_price is None:
            spot_price = self._generate_price_movement(symbol)
        
        step = STRIKE_STEPS[symbol]
        atm = get_atm_strike(spot_price, step)
        oi_data = self._generate_oi_changes(symbol, atm)
        
        return {
            "status": "success",
            "symbol": symbol,
            "atm_strike": atm,
            "strikes": oi_data
        }


# Global instance
data_provider = MarketDataProvider()
