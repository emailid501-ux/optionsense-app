"""
WebSocket Manager for Real-time Price Streaming
Broadcasts live prices every 2 seconds to all connected clients
"""

import asyncio
from typing import List
from fastapi import WebSocket
import json

# Store active WebSocket connections
active_connections: List[WebSocket] = []


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"🔌 WebSocket connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        print(f"🔌 WebSocket disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Send message to all connected clients"""
        if not self.active_connections:
            return
            
        json_msg = json.dumps(message)
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(json_msg)
            except Exception:
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)


manager = ConnectionManager()


async def get_live_prices():
    """Fetch live prices for NIFTY, BANKNIFTY, and top stocks"""
    from live_data import fetch_google_finance_data
    
    prices = {}
    
    # Fetch index prices
    for symbol in ["NIFTY", "BANKNIFTY"]:
        data = fetch_google_finance_data(symbol)
        if data:
            prices[symbol] = {
                "price": data["price"],
                "change": data["change"],
                "change_pct": data["change_pct"]
            }
    
    # Fetch top 5 stock prices
    top_stocks = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK"]
    import yfinance as yf
    
    for symbol in top_stocks:
        try:
            ticker = yf.Ticker(f"{symbol}.NS")
            info = ticker.fast_info
            price = float(info.get('lastPrice', 0) or info.get('last_price', 0))
            prev = float(info.get('previousClose', 0) or info.get('previous_close', price))
            change = price - prev
            change_pct = (change / prev * 100) if prev else 0
            
            prices[symbol] = {
                "price": round(price, 2),
                "change": round(change, 2),
                "change_pct": round(change_pct, 2)
            }
        except:
            pass
    
    return prices


async def price_broadcaster():
    """Background task that broadcasts prices every 2 seconds"""
    while True:
        try:
            prices = await asyncio.get_event_loop().run_in_executor(
                None, lambda: asyncio.run(get_live_prices())
            )
            await manager.broadcast({
                "type": "price_update",
                "data": prices,
                "timestamp": __import__('datetime').datetime.now().isoformat()
            })
        except Exception as e:
            print(f"Broadcast error: {e}")
        
        await asyncio.sleep(2)  # 2 second interval
