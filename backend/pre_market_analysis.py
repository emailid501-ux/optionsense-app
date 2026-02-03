"""
Pre-Market Analysis Module for OptionSense
Provides global market data, news sentiment, and next-day stock picks
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import random

# Try importing yfinance for global markets
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print("yfinance not installed. Global markets will use mock data.")


# ==========================================
# Configuration
# ==========================================

# GNews API Key (Free tier: 100 requests/day)
# Users can get their own key from: https://gnews.io/
GNEWS_API_KEY = "8bf17fa48f3fa5effe6708a9ce05f6f3"

# Global Market Symbols (Yahoo Finance)
GLOBAL_MARKETS = {
    "S&P 500": "^GSPC",
    "NASDAQ": "^IXIC",
    "DOW JONES": "^DJI",
    "SGX NIFTY": "SGX=F",
    "HANG SENG": "^HSI",
    "NIKKEI": "^N225",
    "FTSE 100": "^FTSE",
    "DAX": "^GDAXI",
}

# Sentiment Keywords
BULLISH_KEYWORDS = [
    "rally", "surge", "gain", "rise", "bullish", "positive", "growth",
    "record high", "upgrade", "beat", "strong", "boom", "optimism",
    "recovery", "profit", "outperform", "buy", "breakout", "up"
]

BEARISH_KEYWORDS = [
    "fall", "drop", "crash", "decline", "bearish", "negative", "loss",
    "record low", "downgrade", "miss", "weak", "bust", "pessimism",
    "recession", "selloff", "underperform", "sell", "breakdown", "down"
]


# ==========================================
# Global Markets Functions
# ==========================================

def fetch_global_markets() -> List[Dict]:
    """
    Fetch global market data using yfinance.
    Returns list of market data with name, symbol, price, and change.
    """
    markets_data = []
    
    if YFINANCE_AVAILABLE:
        for name, symbol in GLOBAL_MARKETS.items():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2d")
                
                if len(hist) >= 2:
                    current_price = hist['Close'].iloc[-1]
                    prev_close = hist['Close'].iloc[-2]
                    change = current_price - prev_close
                    change_pct = (change / prev_close) * 100
                    
                    markets_data.append({
                        "name": name,
                        "symbol": symbol,
                        "price": round(current_price, 2),
                        "change": round(change, 2),
                        "change_pct": round(change_pct, 2),
                        "is_positive": change >= 0,
                        "status": "UP" if change >= 0 else "DOWN"
                    })
                elif len(hist) >= 1:
                    current_price = hist['Close'].iloc[-1]
                    markets_data.append({
                        "name": name,
                        "symbol": symbol,
                        "price": round(current_price, 2),
                        "change": 0,
                        "change_pct": 0,
                        "is_positive": True,
                        "status": "FLAT"
                    })
            except Exception as e:
                print(f"Error fetching {name}: {e}")
                continue
    
    # If no data fetched, return mock data
    if not markets_data:
        markets_data = _get_mock_global_markets()
    
    return markets_data


def _get_mock_global_markets() -> List[Dict]:
    """Mock global markets data for when APIs are unavailable."""
    mock_data = [
        {"name": "S&P 500", "symbol": "^GSPC", "price": 5850.25, "change": 45.30, "change_pct": 0.78, "is_positive": True, "status": "UP"},
        {"name": "NASDAQ", "symbol": "^IXIC", "price": 18520.50, "change": 125.80, "change_pct": 0.68, "is_positive": True, "status": "UP"},
        {"name": "DOW JONES", "symbol": "^DJI", "price": 42850.00, "change": -85.50, "change_pct": -0.20, "is_positive": False, "status": "DOWN"},
        {"name": "SGX NIFTY", "symbol": "SGX=F", "price": 23580.00, "change": 65.00, "change_pct": 0.28, "is_positive": True, "status": "UP"},
        {"name": "HANG SENG", "symbol": "^HSI", "price": 19850.30, "change": -120.45, "change_pct": -0.60, "is_positive": False, "status": "DOWN"},
        {"name": "NIKKEI", "symbol": "^N225", "price": 38250.00, "change": 180.50, "change_pct": 0.47, "is_positive": True, "status": "UP"},
    ]
    # Add some randomness for demo
    for market in mock_data:
        variation = random.uniform(-0.5, 0.5)
        market["change_pct"] = round(market["change_pct"] + variation, 2)
        market["is_positive"] = market["change_pct"] >= 0
        market["status"] = "UP" if market["is_positive"] else "DOWN"
    return mock_data


# ==========================================
# News & Sentiment Functions
# ==========================================

def fetch_news_headlines(api_key: Optional[str] = None, max_articles: int = 10) -> List[Dict]:
    """
    Fetch business/stock market news headlines using GNews API.
    Falls back to mock data if API key not provided.
    """
    key = api_key or GNEWS_API_KEY
    
    if key:
        try:
            url = f"https://gnews.io/api/v4/search"
            params = {
                "q": "Indian stock market OR NSE OR Sensex OR Nifty",
                "lang": "en",
                "country": "in",
                "max": max_articles,
                "apikey": key
            }
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                articles = data.get("articles", [])
                
                headlines = []
                for article in articles:
                    headline = article.get("title", "")
                    sentiment = analyze_news_sentiment(headline)
                    headlines.append({
                        "title": headline,
                        "source": article.get("source", {}).get("name", "Unknown"),
                        "url": article.get("url", ""),
                        "published": article.get("publishedAt", ""),
                        "sentiment": sentiment["sentiment"],
                        "score": sentiment["score"],
                        "is_bullish": sentiment["is_bullish"]
                    })
                return headlines
        except Exception as e:
            print(f"GNews API error: {e}")
    
    # Return mock headlines if API fails or no key provided
    return _get_mock_news_headlines()


def _get_mock_news_headlines() -> List[Dict]:
    """Mock news headlines for demo purposes."""
    mock_headlines = [
        {"title": "RBI keeps repo rate unchanged, maintains growth-inflation balance", "source": "Economic Times", "sentiment": "NEUTRAL", "score": 0, "is_bullish": None},
        {"title": "IT sector stocks rally on strong Q3 earnings expectations", "source": "Moneycontrol", "sentiment": "BULLISH", "score": 2, "is_bullish": True},
        {"title": "FIIs continue selling streak, withdraw Rs 5000 crore in January", "source": "Mint", "sentiment": "BEARISH", "score": -2, "is_bullish": False},
        {"title": "Auto sector revival: Maruti, Tata Motors report strong sales growth", "source": "Business Standard", "sentiment": "BULLISH", "score": 2, "is_bullish": True},
        {"title": "Bank Nifty hits all-time high on strong credit growth data", "source": "CNBC", "sentiment": "BULLISH", "score": 3, "is_bullish": True},
        {"title": "Crude oil prices surge, may impact OMC stocks negatively", "source": "Reuters", "sentiment": "BEARISH", "score": -1, "is_bullish": False},
        {"title": "Pharma exports reach record high, sector outlook positive", "source": "Hindu BusinessLine", "sentiment": "BULLISH", "score": 2, "is_bullish": True},
        {"title": "Global markets mixed as investors await US Fed decision", "source": "Bloomberg", "sentiment": "NEUTRAL", "score": 0, "is_bullish": None},
    ]
    return mock_headlines


def analyze_news_sentiment(headline: str) -> Dict:
    """
    Analyze sentiment of a news headline using keyword matching.
    Returns sentiment classification and score.
    """
    headline_lower = headline.lower()
    
    bullish_count = sum(1 for word in BULLISH_KEYWORDS if word in headline_lower)
    bearish_count = sum(1 for word in BEARISH_KEYWORDS if word in headline_lower)
    
    score = bullish_count - bearish_count
    
    if score > 0:
        return {"sentiment": "BULLISH", "score": score, "is_bullish": True}
    elif score < 0:
        return {"sentiment": "BEARISH", "score": score, "is_bullish": False}
    else:
        return {"sentiment": "NEUTRAL", "score": 0, "is_bullish": None}


def calculate_overall_sentiment(headlines: List[Dict]) -> Dict:
    """
    Calculate overall market sentiment from news headlines.
    """
    if not headlines:
        return {"mood": "NEUTRAL", "score": 5, "bullish_count": 0, "bearish_count": 0, "total": 0}
    
    bullish_count = sum(1 for h in headlines if h.get("is_bullish") == True)
    bearish_count = sum(1 for h in headlines if h.get("is_bullish") == False)
    neutral_count = len(headlines) - bullish_count - bearish_count
    
    # Calculate sentiment score (0-10 scale)
    if len(headlines) > 0:
        sentiment_ratio = bullish_count / len(headlines)
        score = round(sentiment_ratio * 10)
    else:
        score = 5
    
    # Determine mood
    if bullish_count > bearish_count + 2:
        mood = "BULLISH"
    elif bearish_count > bullish_count + 2:
        mood = "BEARISH"
    else:
        mood = "NEUTRAL"
    
    return {
        "mood": mood,
        "score": score,
        "bullish_count": bullish_count,
        "bearish_count": bearish_count,
        "neutral_count": neutral_count,
        "total": len(headlines)
    }


# ==========================================
# Pre-Market Stock Picks
# ==========================================

def get_pre_market_picks(stock_data: List[Dict], global_sentiment: str = "NEUTRAL") -> List[Dict]:
    """
    Get top 3 stock picks for next trading day based on:
    1. Previous day's technical analysis
    2. Global market cues
    3. News sentiment
    """
    if not stock_data:
        return _get_mock_pre_market_picks()
    
    # Filter and score stocks
    scored_stocks = []
    
    for stock in stock_data:
        score = 0
        reasons = []
        
        # Base score from recommendation
        if stock.get("recommendation") == "Buy":
            score += 30
            reasons.append("Strong buy signal")
        elif stock.get("recommendation") == "Strong Buy":
            score += 40
            reasons.append("Very strong buy signal")
        
        # Technical indicators bonus
        indicators = stock.get("indicators", {})
        
        # RSI
        if indicators.get("rsi_signal") == "OVERSOLD":
            score += 15
            reasons.append("RSI oversold - potential bounce")
        
        # MACD
        if indicators.get("macd") == "BULLISH":
            score += 10
            reasons.append("MACD bullish crossover")
        
        # Score bonus
        stock_score = stock.get("score", 5)
        score += stock_score * 3
        
        # Global sentiment adjustment
        if global_sentiment == "BULLISH":
            score += 5
        elif global_sentiment == "BEARISH":
            score -= 5
        
        # Risk-reward bonus
        trading_levels = stock.get("trading_levels", {})
        if trading_levels.get("risk_reward", "N/A") != "N/A":
            try:
                rr = float(trading_levels["risk_reward"])
                if rr >= 2:
                    score += 10
                    reasons.append(f"Excellent R:R of {rr}")
                elif rr >= 1.5:
                    score += 5
            except:
                pass
        
        scored_stocks.append({
            "symbol": stock.get("symbol", ""),
            "name": stock.get("name", ""),
            "price": stock.get("price", 0),
            "change_pct": stock.get("change_pct", 0),
            "entry": trading_levels.get("entry", stock.get("price", 0)),
            "target": trading_levels.get("target", 0),
            "stoploss": trading_levels.get("stoploss", 0),
            "score": stock.get("score", 5),
            "pre_market_score": score,
            "reasons": reasons[:3],  # Top 3 reasons
            "recommendation": "BUY" if score >= 40 else "WATCH"
        })
    
    # Sort by pre-market score and return top 3
    scored_stocks.sort(key=lambda x: x["pre_market_score"], reverse=True)
    return scored_stocks[:3]


def _get_mock_pre_market_picks() -> List[Dict]:
    """Pre-market picks with LIVE Google Finance prices."""
    from live_data import fetch_google_finance_data
    
    # Base picks with live prices
    base_picks = [
        {"symbol": "RELIANCE", "name": "Reliance Industries Ltd", "score": 8, "reasons": ["Strong buy signal", "RSI oversold bounce", "Excellent R:R of 2.3"]},
        {"symbol": "TCS", "name": "Tata Consultancy Services", "score": 7, "reasons": ["IT sector positive cues", "MACD bullish crossover"]},
        {"symbol": "HDFCBANK", "name": "HDFC Bank Ltd", "score": 7, "reasons": ["Banking sector strength", "Strong buy signal"]},
    ]
    
    picks = []
    for pick in base_picks:
        # Fetch LIVE price from Google Finance
        gf_data = fetch_google_finance_data(pick["symbol"])
        
        if gf_data and gf_data.get("price", 0) > 0:
            price = gf_data["price"]
            change_pct = gf_data.get("change_pct", 0)
        else:
            # Fallback mock prices
            price = {"RELIANCE": 1380, "TCS": 3200, "HDFCBANK": 1750}.get(pick["symbol"], 1000)
            change_pct = 0.5
        
        # Calculate Entry/Target/SL from LIVE price
        entry = round(price * 0.995, 2)
        target = round(price * 1.03, 2)
        stoploss = round(price * 0.985, 2)
        
        picks.append({
            "symbol": pick["symbol"],
            "name": pick["name"],
            "price": round(price, 2),
            "change_pct": round(change_pct, 2),
            "entry": entry,
            "target": target,
            "stoploss": stoploss,
            "score": pick["score"],
            "pre_market_score": pick["score"] * 10,
            "reasons": pick["reasons"],
            "recommendation": "BUY"
        })
    
    return picks


# ==========================================
# Main Pre-Market Analysis Function
# ==========================================

def get_complete_pre_market_analysis(stock_data: List[Dict] = None, gnews_api_key: str = None) -> Dict:
    """
    Get complete pre-market analysis including:
    1. Global markets data
    2. News headlines with sentiment
    3. Overall market mood
    4. Top 3 stock picks for tomorrow
    """
    # Fetch global markets
    global_markets = fetch_global_markets()
    
    # Calculate global market sentiment
    positive_markets = sum(1 for m in global_markets if m.get("is_positive", False))
    global_sentiment = "BULLISH" if positive_markets >= 4 else "BEARISH" if positive_markets <= 2 else "NEUTRAL"
    
    # Fetch news
    news_headlines = fetch_news_headlines(api_key=gnews_api_key, max_articles=8)
    
    # Calculate news sentiment
    news_sentiment = calculate_overall_sentiment(news_headlines)
    
    # Get pre-market stock picks
    top_picks = get_pre_market_picks(stock_data or [], news_sentiment.get("mood", "NEUTRAL"))
    
    # Combine into final analysis
    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "market_date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
        "global_markets": {
            "data": global_markets,
            "sentiment": global_sentiment,
            "positive_count": positive_markets,
            "total_count": len(global_markets)
        },
        "news": {
            "headlines": news_headlines,
            "sentiment": news_sentiment
        },
        "top_picks": top_picks,
        "overall_mood": _calculate_overall_mood(global_sentiment, news_sentiment.get("mood", "NEUTRAL")),
        "disclaimer": "This analysis is for educational purposes only. Always do your own research before investing."
    }


def _calculate_overall_mood(global_sentiment: str, news_sentiment: str) -> Dict:
    """Calculate overall market mood from global and news sentiment."""
    sentiments = [global_sentiment, news_sentiment]
    
    bullish = sentiments.count("BULLISH")
    bearish = sentiments.count("BEARISH")
    
    if bullish > bearish:
        return {"mood": "BULLISH", "message": "Markets looking positive for tomorrow", "icon": "🟢"}
    elif bearish > bullish:
        return {"mood": "BEARISH", "message": "Markets may see selling pressure", "icon": "🔴"}
    else:
        return {"mood": "NEUTRAL", "message": "Mixed signals - trade with caution", "icon": "🟡"}
