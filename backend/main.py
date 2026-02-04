import os
import sys

# Add current directory (backend) and vendor directory to sys.path
# This is CRITICAL for Vercel/Lambda environments to find local modules
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
sys.path.append(os.path.join(current_dir, "vendor"))

from fastapi import FastAPI, Query, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import Literal
import asyncio

from models import DashboardSnapshot, OIDetails
from data_provider import data_provider
from websocket_manager import manager, get_live_prices

app = FastAPI(
    title="OptionSense API",
    description="Real-time Intraday Sentiment Analysis API for Nifty & Bank Nifty",
    version="2.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "OptionSense API",
        "version": "1.0.0",
        "endpoints": [
            "/dashboard-snapshot?symbol=NIFTY",
            "/oi-details?symbol=NIFTY",
            "/health"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "OptionSense API"}


# ===== Pro Trader 8-Point Analysis =====
from pro_trader_analysis import get_complete_pro_analysis

@app.get("/pro-analysis/{symbol}")
def get_pro_analysis(symbol: str):
    """
    Get all 8 pro trader analysis points:
    1. PCR Analysis
    2. OI Shift Tracking
    3. VIX & IV Skew
    4. Volume Analysis (True/Trap Move)
    5. OI Ladder
    6. Theta Decay
    7. Market Breadth
    8. VWAP Analysis
    """
    try:
        analysis = get_complete_pro_analysis(symbol.upper())
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== WebSocket for Real-time Prices =====
@app.websocket("/ws/prices")
async def websocket_prices(websocket: WebSocket):
    """
    WebSocket endpoint for real-time price streaming.
    Sends NIFTY, BANKNIFTY, and top stock prices every 2 seconds.
    """
    await manager.connect(websocket)
    try:
        while True:
            # Fetch live prices
            prices = await asyncio.get_event_loop().run_in_executor(
                None, get_live_prices_sync
            )
            
            # Send to this client
            import json
            from datetime import datetime
            await websocket.send_text(json.dumps({
                "type": "price_update",
                "data": prices,
                "timestamp": datetime.now().isoformat()
            }))
            
            await asyncio.sleep(2)  # 2 second interval
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)


def get_live_prices_sync():
    """Synchronous wrapper for getting live prices using Google Finance"""
    from live_data import fetch_google_finance_data
    
    prices = {}
    
    # Fetch ALL prices from Google Finance (accurate real-time data)
    all_symbols = ["NIFTY", "BANKNIFTY", "RELIANCE", "TCS", "HDFCBANK", "INFY", "TATASTEEL"]
    
    for symbol in all_symbols:
        data = fetch_google_finance_data(symbol)
        if data:
            prices[symbol] = {
                "price": round(data["price"], 2),
                "change": round(data["change"], 2),
                "change_pct": round(data["change_pct"], 2)
            }
    
    return prices


# Import live data module
import live_data

@app.get("/dashboard-snapshot", response_model=DashboardSnapshot)
async def get_dashboard_snapshot(
    symbol: Literal["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"] = Query(
        default="NIFTY",
        description="Index symbol"
    )
):
    """
    Get dashboard snapshot with sentiment analysis using live NSE data.
    
    Returns:
    - Current price with change
    - VWAP signal (bullish/bearish)
    - PCR value and trend
    - Sentiment score (0-10) with label
    - OI Alert message with color coding
    """
    try:
        # Switch to live data
        data = live_data.get_live_dashboard_data(symbol)
        return data
    except Exception as e:
        # Fallback to mock data if live data fails completely
        print(f"Live dashboard fetch failed, using mock: {e}")
        try:
            return data_provider.get_dashboard_data(symbol)
        except:
             raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/oi-details", response_model=OIDetails)
async def get_oi_details(
    symbol: Literal["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"] = Query(
        default="NIFTY",
        description="Index symbol"
    )
):
    """
    Get OI details for option chain visualization.
    
    Returns:
    - ATM strike price
    - 11 strikes (5 above + ATM + 5 below)
    - OI changes with color coding for each strike
    """
    try:
        data = data_provider.get_oi_details(symbol)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== Stock Screener Endpoints =====
# Using live NSE data instead of mock data
from live_stock_screener import live_screener


@app.get("/stock-screener")
def get_stock_screener(
    filter: Literal["all", "buy", "sell", "top_gainers", "top_losers"] = Query(
        default="all",
        description="Filter type for stock list"
    )
):
    """
    Get stock screener data with buy/sell recommendations.
    
    Filter options:
    - all: All stocks sorted by score
    - buy: Only stocks with BUY/STRONG BUY signals
    - sell: Only stocks with SELL/STRONG SELL signals
    - top_gainers: Top 20 gainers by % change
    - top_losers: Top 20 losers by % change
    
    Data Source: NSE India (Real-time)
    """
    try:
        data = live_screener.get_screener_data(filter)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stock/{symbol}")
def get_stock_detail(symbol: str):
    """Get detailed data for a specific stock."""
    try:
        data = live_screener.get_stock_details(symbol.upper())
        if data is None:
            raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stock-price/{symbol}")
def get_stock_price(symbol: str):
    """
    Lightweight endpoint for live stock price (2-second refresh).
    Returns ONLY price and change - no analysis.
    """
    try:
        import yfinance as yf
        ticker = yf.Ticker(f"{symbol.upper()}.NS")
        info = ticker.fast_info
        price = float(info.get('lastPrice', 0) or info.get('last_price', 0))
        prev_close = float(info.get('previousClose', 0) or info.get('previous_close', price))
        change = price - prev_close
        change_pct = (change / prev_close * 100) if prev_close else 0
        
        return {
            "symbol": symbol.upper(),
            "price": round(price, 2),
            "change": round(change, 2),
            "change_pct": round(change_pct, 2),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


from datetime import datetime



# ===== Option Strategy Endpoints =====
from option_strategy import strategy_engine


@app.get("/stock/{symbol}/option-strategy")
def get_option_strategy(symbol: str):
    """Get weekly option buying strategy for a stock."""
    try:
        strategy = strategy_engine.get_option_recommendation(symbol.upper())
        return strategy
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== Phase 15: Advanced Indicators Endpoints =====
from live_data import (
    fetch_india_vix, 
    fetch_market_breadth, 
    fetch_straddle_price, 
    fetch_oi_ladder,
    get_market_overview
)


@app.get("/market-overview")
def market_overview(symbol: str = "NIFTY"):
    """
    Get all advanced trading indicators in one call.
    Includes: VIX, Market Breadth, Straddle Price, OI Ladder
    """
    try:
        return get_market_overview(symbol)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/vix")
def get_vix():
    """Get India VIX with interpretation."""
    try:
        return fetch_india_vix()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/market-breadth")
def get_market_breadth():
    """Get Market Breadth - Advance/Decline ratio."""
    try:
        return fetch_market_breadth()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/straddle/{symbol}")
def get_straddle(symbol: str = "NIFTY"):
    """Get ATM Straddle price for Theta Decay tracking."""
    try:
        return fetch_straddle_price(symbol.upper())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/oi-ladder/{symbol}")
def get_oi_ladder(symbol: str = "NIFTY"):
    """Get OI Ladder - Support and Resistance levels."""
    try:
        return fetch_oi_ladder(symbol.upper())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===== Pre-Market Analysis Endpoints =====
from pre_market_analysis import get_complete_pre_market_analysis

@app.get("/pre-market-analysis")
def get_pre_market_analysis(gnews_key: str = None):
    """
    Get complete pre-market analysis including:
    - Global markets (S&P500, NASDAQ, SGX Nifty, etc.)
    - News headlines with sentiment analysis
    - Top 3 stock picks for next trading day
    """
    try:
        # Get current stock data for analysis
        stock_data = live_screener.get_stocks(filter_type="buy")
        
        # Get complete analysis
        analysis = get_complete_pre_market_analysis(
            stock_data=stock_data,
            gnews_api_key=gnews_key
        )
        return analysis
    except Exception as e:
        print(f"Pre-market analysis error: {e}")
        # Return mock data on error
        return get_complete_pre_market_analysis(stock_data=None, gnews_api_key=None)


# ===== Serve Frontend Static Files =====
# Get the directory where main.py is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")

# Mount frontend folder if it exists
if os.path.exists(FRONTEND_DIR):
    app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
