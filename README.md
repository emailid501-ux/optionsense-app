# 📊 OptionSense - Real-Time Trading Analysis Platform

> **Live Market Data | Technical Analysis | Option Strategies | Pro Trader Insights**

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js (optional, for development)

### Installation & Running

```bash
# 1. Start Backend (Port 8000)
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000

# 2. Start Frontend (Port 3000)
cd frontend
python -m http.server 3000
```

### Access
- **Frontend:** http://localhost:3000
- **API Docs:** http://localhost:8000/docs

---

## 📱 Features Overview

### 1. Dashboard (Home Tab)
Real-time index analysis with live price updates.

| Feature | Description |
|---------|-------------|
| **Live Price** | NIFTY/BANKNIFTY current price from Moneycontrol (primary) or Google Finance (fallback) |
| **VWAP Signal** | Shows if price is above/below VWAP (Volume Weighted Average Price) |
| **PCR Value** | Put-Call Ratio with trend indicator (RISING/FALLING) |
| **Sentiment Score** | 0-10 score with BULLISH/BEARISH/NEUTRAL label |
| **OI Alert** | Open Interest based trading recommendation |

**Symbol Selection:** NIFTY | BANKNIFTY | FINNIFTY | MIDCPNIFTY

---

### 2. Stock Screener (Stocks Tab)
Live stock recommendations with technical analysis.

| Feature | Description |
|---------|-------------|
| **Stock Cards** | All stocks with live prices (Moneycontrol + Google Finance) |
| **Recommendation** | STRONG BUY / BUY / HOLD / SELL / STRONG SELL |
| **Score** | Technical score (0-100) based on multiple indicators |
| **Trading Levels** | Entry, Target, Stoploss with Risk:Reward ratio |

**Filters:**
- 📈 All Stocks
- 🟢 Buy Signals
- 🔴 Sell Signals
- ⬆️ Top Gainers
- ⬇️ Top Losers

**Stock Detail View:**
- Quick Analysis: RSI, MACD, Fibonacci
- Fibonacci Levels with Support/Resistance
- Reasons in English & Hindi (Hinglish)
- 1-Week Option Strategy recommendation

---

### 3. Pro Trader Analysis (8-Point System)
Advanced institutional-grade analysis.

| Point | Indicator | What It Shows |
|-------|-----------|---------------|
| 1 | **PCR Analysis** | Put-Call Ratio sentiment |
| 2 | **OI Shift** | Open Interest movement between strikes |
| 3 | **VIX/IV** | India VIX and Implied Volatility analysis |
| 4 | **Volume Analysis** | True move vs Trap move detection |
| 5 | **OI Ladder** | Support/Resistance from OI data |
| 6 | **Theta Decay** | ATM Straddle time decay impact |
| 7 | **Market Breadth** | Advance/Decline ratio |
| 8 | **VWAP** | Institutional buying/selling zones |

---

### 4. Pre-Market Analysis
Analysis before market opens (before 9:15 AM IST).

| Feature | Description |
|---------|-------------|
| **Global Markets** | SGX Nifty, S&P 500, NASDAQ, Dow Jones |
| **News Sentiment** | Latest market news with AI sentiment |
| **Top 3 Picks** | AI-recommended stocks for the day |

---

## 🔄 Data Sources & Priority

### Index Data (NIFTY, BANKNIFTY, etc.)
```
Priority: Moneycontrol → Google Finance → Yahoo Finance → NSE
```

### Stock Data (RELIANCE, TCS, etc.)
```
Priority: Moneycontrol (if mapped) → Google Finance → NSE
```

### Supported Moneycontrol Stocks (117+)
All NIFTY 50, NIFTY Next 50, and popular stocks including:
- RELIANCE, TCS, HDFCBANK, INFY, ICICIBANK
- SBIN, BHARTIARTL, KOTAKBANK, ITC, LT
- TATAMOTORS, TATASTEEL, WIPRO, AXISBANK
- ADANIENT, ADANIPORTS, ZOMATO, PAYTM, DMART
- And many more...

---

## 🛠️ API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/dashboard-snapshot` | GET | Main dashboard data |
| `/oi-details` | GET | Option chain OI data |
| `/stock-screener` | GET | Stock list with analysis |
| `/stock/{symbol}` | GET | Individual stock detail |
| `/pro-analysis/{symbol}` | GET | 8-point pro analysis |
| `/pre-market-analysis` | GET | Pre-market overview |
| `/market-overview` | GET | VIX, Breadth, Straddle |
| `/vix` | GET | India VIX |
| `/oi-ladder/{symbol}` | GET | Support/Resistance |

**Query Parameters:**
- `symbol`: NIFTY, BANKNIFTY, FINNIFTY, MIDCPNIFTY
- `filter`: all, buy, sell, top_gainers, top_losers

---

## 📊 Technical Indicators Used

### RSI (Relative Strength Index)
- **< 30:** OVERSOLD - Potential bounce
- **30-70:** NEUTRAL zone
- **> 70:** OVERBOUGHT - Potential correction

### MACD
- **BULLISH:** Line crosses above signal
- **BEARISH:** Line crosses below signal

### Moving Averages
- 20 DMA, 50 DMA, 200 DMA
- Price position relative to MAs determines trend

### Fibonacci Levels
- 23.6%, 38.2%, 50%, 61.8%, 78.6%
- Key support and resistance levels

### PCR (Put-Call Ratio)
- **> 1.2:** Bullish sentiment
- **< 0.8:** Bearish sentiment
- **0.8-1.2:** Neutral

---

## ⚡ Performance Notes

1. **Stock Screener Loading Time:** 5-15 seconds (fetches live prices for each stock)
2. **Data Refresh:** Prices update on each API call (no auto-refresh)
3. **Market Hours:** Best used during 9:15 AM - 3:30 PM IST
4. **Cache Duration:** 60 seconds for bulk stock data

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| Blank page | Check if backend is running on port 8000 |
| Stale prices | Refresh the page to fetch latest data |
| Stock not found | Not all stocks have Moneycontrol mapping, Google Finance is fallback |
| Slow loading | Normal - fetching live prices from multiple sources |
| API 500 error | Check backend console for error details |

---

## 🚀 Deployment (Vercel) -> Best Free Option

We have configured the project for **Vercel** (Lifetime Free, High Speed).

### Steps to Deploy:
1. **Install Vercel CLI** (if not installed):
   ```bash
   npm install -g vercel
   ```
2. **Login to Vercel**:
   ```bash
   vercel login
   ```
3. **Deploy**:
   Run this command in the project root folder:
   ```bash
   vercel
   ```
   - Accept all defaults (just press Enter 4-5 times).
4. **Done!** You will get a production URL (e.g., `https://optionsense.vercel.app`).

**Note:** The `vercel.json` file handles all routing between Python Backend and Frontend automatically.

---

## 📁 Project Structure

```
spatial-gemini/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── live_data.py         # Moneycontrol, Google Finance, NSE integrations
│   ├── live_stock_screener.py  # Stock analysis engine
│   ├── pro_trader_analysis.py  # 8-point system
│   ├── pre_market_analysis.py  # Pre-market module
│   └── option_strategy.py   # Option recommendations
└── frontend/
    ├── index.html           # Main HTML
    ├── app.js               # JavaScript logic
    └── styles.css           # Styling
```

---

## 📜 Changelog

### Version 2.0 (February 2026)
- ✅ Moneycontrol integration as primary data source
- ✅ Google Finance as fallback for all stocks
- ✅ 117+ stock symbol mappings
- ✅ Real-time price updates in stock screener
- ✅ Pro Trader 8-Point Analysis system
- ✅ Pre-Market Analysis with global markets

### Version 1.0
- Initial release with NSE data
- Basic dashboard and stock screener

---

## 📞 Support

For issues or feature requests, check the browser console (F12) and backend terminal for error messages.

---

**Made with ❤️ for Indian Traders**
