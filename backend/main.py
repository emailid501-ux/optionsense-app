"""OptionSense Backend - FastAPI Application."""
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Literal

from models import DashboardSnapshot, OIDetails
from data_provider import data_provider


app = FastAPI(
    title="OptionSense API",
    description="Real-time Intraday Sentiment Analysis API for Nifty & Bank Nifty",
    version="1.0.0"
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


@app.get("/dashboard-snapshot", response_model=DashboardSnapshot)
async def get_dashboard_snapshot(
    symbol: Literal["NIFTY", "BANKNIFTY"] = Query(
        default="NIFTY",
        description="Index symbol (NIFTY or BANKNIFTY)"
    )
):
    """
    Get dashboard snapshot with sentiment analysis.
    
    Returns:
    - Current price with change
    - VWAP signal (bullish/bearish)
    - PCR value and trend
    - Sentiment score (0-10) with label
    - OI Alert message with color coding
    """
    try:
        data = data_provider.get_dashboard_data(symbol)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/oi-details", response_model=OIDetails)
async def get_oi_details(
    symbol: Literal["NIFTY", "BANKNIFTY"] = Query(
        default="NIFTY",
        description="Index symbol (NIFTY or BANKNIFTY)"
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

