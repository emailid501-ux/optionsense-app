"""Core sentiment analysis algorithms for OptionSense."""
from typing import Tuple, List, Literal


# Color constants
COLOR_STRONG_GREEN = "#00E676"
COLOR_LIGHT_GREEN = "#69F0AE"
COLOR_STRONG_RED = "#FF5252"
COLOR_LIGHT_RED = "#FF8A80"
COLOR_GREY = "#9E9E9E"


def get_relevant_strikes(current_spot_price: float, step: int = 50) -> List[int]:
    """
    Algorithm A: Smart Strike Selection
    Find ATM (At-The-Money) and select 5 Strikes Up + 5 Strikes Down.
    Returns 11 strikes total.
    """
    atm = round(current_spot_price / step) * step
    strikes = [atm + (i * step) for i in range(-5, 6)]  # -5 to +5 inclusive
    return strikes


def get_atm_strike(current_spot_price: float, step: int = 50) -> int:
    """Calculate the At-The-Money strike price."""
    return round(current_spot_price / step) * step


def calculate_oi_signal(call_coi: int, put_coi: int) -> Tuple[str, str, str]:
    """
    Algorithm B: OI Shift Logic
    Returns: (signal_message, status_label, bg_color)
    
    Conditions:
    - Call COI < 0 & Put COI > 0: SHORT COVERING (Strong Buy) - Green
    - Call COI > 0 & Put COI < 0: LONG UNWINDING (Strong Sell) - Red
    - Put COI > Call COI (Both +ve): MILD BULLISH (Support Building) - Light Green
    - Call COI > Put COI (Both +ve): MILD BEARISH (Resistance Building) - Light Red
    - Both COI Negative: UNCERTAIN (Volatile) - Grey
    """
    if call_coi < 0 and put_coi > 0:
        return (
            "Short Covering: Call Writers Exiting, Put Writers Entering",
            "SHORT COVERING",
            COLOR_STRONG_GREEN
        )
    elif call_coi > 0 and put_coi < 0:
        return (
            "Long Unwinding: Call Writers Entering, Put Writers Exiting",
            "LONG UNWINDING",
            COLOR_STRONG_RED
        )
    elif call_coi > 0 and put_coi > 0:
        if put_coi > call_coi:
            return (
                "Mild Bullish: Support Building with Put Writing",
                "MILD BULLISH",
                COLOR_LIGHT_GREEN
            )
        else:
            return (
                "Mild Bearish: Resistance Building with Call Writing",
                "MILD BEARISH",
                COLOR_LIGHT_RED
            )
    elif call_coi < 0 and put_coi < 0:
        return (
            "Uncertain: Both Sides Unwinding, Expect Volatility",
            "UNCERTAIN",
            COLOR_GREY
        )
    else:
        return (
            "Neutral: No Significant OI Change",
            "NEUTRAL",
            COLOR_GREY
        )


def calculate_sentiment_score(
    pcr: float,
    spot_price: float,
    vwap: float,
    oi_status: str
) -> Tuple[int, Literal["STRONG BUY", "STRONG SELL", "NEUTRAL"], str]:
    """
    Algorithm C: Sentiment Score Calculation (0 to 10 scale, centered at 5)
    Returns: (score, label, color)
    
    Score components:
    - PCR Logic: +2 if PCR > 1.2, -2 if PCR < 0.7
    - VWAP Logic: +3 if Price > VWAP, -3 otherwise
    - OI Shift: +5 for SHORT COVERING, -5 for LONG UNWINDING
    """
    score = 5  # Start neutral (middle of 0-10 scale)
    
    # 1. PCR Logic (Weighing Machine)
    if pcr > 1.2:
        score += 2
    elif pcr < 0.7:
        score -= 2
    
    # 2. VWAP Logic (Trend)
    if spot_price > vwap:
        score += 2
    else:
        score -= 2
    
    # 3. OI Shift Logic (High Priority)
    if oi_status == "SHORT COVERING":
        score += 3
    elif oi_status == "LONG UNWINDING":
        score -= 3
    elif oi_status == "MILD BULLISH":
        score += 1
    elif oi_status == "MILD BEARISH":
        score -= 1
    
    # Clamp score to 0-10 range
    score = max(0, min(10, score))
    
    # Determine label and color
    if score >= 7:
        return (score, "STRONG BUY", COLOR_STRONG_GREEN)
    elif score <= 3:
        return (score, "STRONG SELL", COLOR_STRONG_RED)
    else:
        return (score, "NEUTRAL", COLOR_GREY)


def get_bar_color_for_oi(oi_change: int, is_call: bool) -> Literal["GREEN", "RED", "GREY"]:
    """
    Determine bar color for OI visualization.
    
    For Calls:
    - Negative OI (unwinding) = GREEN (resistance breaking)
    - Positive OI (writing) = RED (resistance building)
    
    For Puts:
    - Positive OI (writing) = GREEN (support building)
    - Negative OI (unwinding) = RED (support breaking)
    """
    if oi_change == 0:
        return "GREY"
    
    if is_call:
        return "GREEN" if oi_change < 0 else "RED"
    else:  # Put
        return "GREEN" if oi_change > 0 else "RED"
