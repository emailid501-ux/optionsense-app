# 📊 OptionSense User Manual
## Stock Analysis & Option Strategy Tool

---

# 🇮🇳 हिंदी में पढ़ें (Hindi Version Below)

---

# English Version

## What is OptionSense?

OptionSense is a **real-time stock analysis tool** that helps you:
- See **Top 100 NSE stocks** with Buy/Sell recommendations
- Get **technical analysis** (RSI, MACD, Fibonacci levels)
- Search **any NSE listed stock** for analysis
- Get **Option buying strategies** for weekly trades

---

## System Requirements

| Component | Minimum |
|-----------|---------|
| OS | Windows 10/11 |
| RAM | 4 GB |
| Python | 3.9 or higher |
| Internet | Required (for live data) |

---

## Installation (One-Time Setup)

### Step 1: Install Python
1. Go to [python.org/downloads](https://python.org/downloads)
2. Download Python 3.11 (or latest)
3. **IMPORTANT**: Check ✅ "Add Python to PATH" during installation
4. Click "Install Now"

### Step 2: Download OptionSense
1. Extract `optionsense.zip` to a folder (e.g., `C:\OptionSense`)
2. You should see two folders: `backend` and `frontend`

### Step 3: Install Dependencies
1. Open **Command Prompt** (Press `Win + R`, type `cmd`, press Enter)
2. Navigate to backend folder:
   ```
   cd C:\OptionSense\backend
   ```
3. Install required libraries:
   ```
   pip install -r requirements.txt
   ```
4. Wait for installation to complete (2-5 minutes)

---

## How to Start the App

### Step 1: Start the Server
1. Open **Command Prompt**
2. Go to backend folder:
   ```
   cd C:\OptionSense\backend
   ```
3. Start the server:
   ```
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```
4. Wait until you see: `Uvicorn running on http://0.0.0.0:8000`

### Step 2: Open the App
1. Open **Google Chrome** browser
2. Type this URL: `http://localhost:8000/frontend/index.html`
3. Press Enter

🎉 **Your app is now running!**

---

## How to Use

### Dashboard Tab
- Shows **NIFTY/BANKNIFTY sentiment** (Bullish/Bearish/Neutral)
- **PCR (Put-Call Ratio)** indicates market direction
- **VWAP Signal** shows intraday trend

### Stocks Tab
- **Buy (Green)**: Recommended to buy
- **Sell (Red)**: Recommended to sell/avoid
- **Watch (Yellow)**: No clear signal, monitor

### Search Any Stock
1. Type stock symbol in search box (e.g., `CDSL`, `IRCTC`, `TITAN`)
2. Press Enter or click Search
3. Analysis will appear within 10-30 seconds

### Option Strategy
- Click **"Get 1-Week Option Strategy"** on any stock card
- Shows recommended **Call/Put** option to buy
- Displays **Strike Price**, **Trend**, and **Risk Level**

---

## Access from Phone (Same WiFi)

If your laptop and phone are on the **same WiFi network**:

### Step 1: Find Your Laptop's IP
1. Open Command Prompt
2. Type: `ipconfig`
3. Look for **IPv4 Address** (e.g., `192.168.29.129`)

### Step 2: Open on Phone
1. Open Chrome on your phone
2. Type: `http://192.168.29.129:8000/frontend/index.html`
   (Replace with your actual IP)
3. Bookmark this page for easy access

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "pip not found" | Reinstall Python with "Add to PATH" checked |
| "Module not found" | Run `pip install -r requirements.txt` again |
| "Connection refused" | Make sure server is running (Step 1) |
| Page not loading | Check URL spelling, try `localhost` instead of IP |
| Data not loading | Check internet connection |
| Slow loading | Normal for first load (100 stocks), wait 30-60 sec |

---

## Stop the App

1. Go to the Command Prompt window where server is running
2. Press `Ctrl + C`
3. Server will stop

---

## Daily Usage

Every day when you want to use:
1. Open Command Prompt
2. Run: `cd C:\OptionSense\backend && uvicorn main:app --host 0.0.0.0 --port 8000`
3. Open browser: `http://localhost:8000/frontend/index.html`

---

---

# 🇮🇳 हिंदी वर्शन

## OptionSense क्या है?

OptionSense एक **रियल-टाइम स्टॉक एनालिसिस टूल** है जो आपको:
- **टॉप 100 NSE स्टॉक्स** Buy/Sell रिकमेंडेशन के साथ दिखाता है
- **टेक्निकल एनालिसिस** (RSI, MACD, Fibonacci) देता है
- **कोई भी NSE स्टॉक** सर्च और एनालाइज कर सकते हो
- **ऑप्शन स्ट्रेटेजी** वीकली ट्रेड के लिए देता है

---

## इंस्टॉलेशन (सिर्फ एक बार करना है)

### स्टेप 1: Python इंस्टॉल करें
1. [python.org/downloads](https://python.org/downloads) पर जाएं
2. Python 3.11 डाउनलोड करें
3. **जरूरी**: इंस्टॉल करते वक्त ✅ "Add Python to PATH" पर टिक करें
4. "Install Now" पर क्लिक करें

### स्टेप 2: OptionSense डाउनलोड करें
1. `optionsense.zip` को किसी फोल्डर में Extract करें (जैसे `C:\OptionSense`)
2. दो फोल्डर दिखेंगे: `backend` और `frontend`

### स्टेप 3: Dependencies इंस्टॉल करें
1. **Command Prompt** खोलें (`Win + R` दबाएं, `cmd` लिखें, Enter दबाएं)
2. Backend फोल्डर में जाएं:
   ```
   cd C:\OptionSense\backend
   ```
3. Libraries इंस्टॉल करें:
   ```
   pip install -r requirements.txt
   ```
4. 2-5 मिनट रुकें

---

## ऐप कैसे चलाएं

### स्टेप 1: सर्वर स्टार्ट करें
1. **Command Prompt** खोलें
2. Backend फोल्डर में जाएं:
   ```
   cd C:\OptionSense\backend
   ```
3. सर्वर चालू करें:
   ```
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```
4. जब तक `Uvicorn running on http://0.0.0.0:8000` न दिखे, रुकें

### स्टेप 2: ऐप खोलें
1. **Google Chrome** खोलें
2. यह URL टाइप करें: `http://localhost:8000/frontend/index.html`
3. Enter दबाएं

🎉 **बधाई हो! ऐप चल रहा है!**

---

## कैसे इस्तेमाल करें

### Dashboard टैब
- **NIFTY/BANKNIFTY सेंटीमेंट** दिखाता है (Bullish/Bearish/Neutral)
- **PCR** मार्केट डायरेक्शन बताता है
- **VWAP Signal** इंट्राडे ट्रेंड दिखाता है

### Stocks टैब
- **Buy (हरा)**: खरीदने की सिफारिश
- **Sell (लाल)**: बेचने/टालने की सिफारिश
- **Watch (पीला)**: कोई clear सिग्नल नहीं

### कोई भी Stock सर्च करें
1. सर्च बॉक्स में stock symbol लिखें (जैसे `CDSL`, `IRCTC`, `TITAN`)
2. Enter दबाएं या Search पर क्लिक करें
3. 10-30 सेकंड में एनालिसिस आ जाएगी

### Option Strategy
- किसी भी stock card पर **"Get 1-Week Option Strategy"** पर क्लिक करें
- रिकमेंडेड **Call/Put** ऑप्शन दिखेगा
- **Strike Price**, **Trend**, और **Risk Level** दिखेगा

---

## फोन से कैसे देखें (Same WiFi पर)

अगर आपका laptop और phone **एक ही WiFi** पर हैं:

### स्टेप 1: Laptop का IP पता करें
1. Command Prompt खोलें
2. टाइप करें: `ipconfig`
3. **IPv4 Address** देखें (जैसे `192.168.29.129`)

### स्टेप 2: Phone पर खोलें
1. Phone पर Chrome खोलें
2. टाइप करें: `http://192.168.29.129:8000/frontend/index.html`
   (अपना actual IP डालें)
3. इस page को Bookmark कर लें

---

## समस्या और समाधान

| समस्या | समाधान |
|--------|--------|
| "pip not found" | Python फिर से इंस्टॉल करें, "Add to PATH" टिक करें |
| "Module not found" | `pip install -r requirements.txt` फिर चलाएं |
| "Connection refused" | सर्वर चल रहा है या नहीं देखें |
| Page नहीं खुल रहा | URL की spelling चेक करें |
| Data नहीं आ रहा | Internet चेक करें |
| धीरे load हो रहा | Normal है (100 stocks), 30-60 सेकंड रुकें |

---

## ऐप बंद कैसे करें

1. जिस Command Prompt में सर्वर चल रहा है, वहां जाएं
2. `Ctrl + C` दबाएं
3. सर्वर बंद हो जाएगा

---

## रोज़ाना इस्तेमाल

हर दिन जब इस्तेमाल करना हो:
1. Command Prompt खोलें
2. चलाएं: `cd C:\OptionSense\backend && uvicorn main:app --host 0.0.0.0 --port 8000`
3. Browser में खोलें: `http://localhost:8000/frontend/index.html`

---

## Disclaimer (चेतावनी)

⚠️ **यह टूल सिर्फ Educational Purpose के लिए है।**
- यह Financial Advice नहीं है
- Invest करने से पहले अपनी Research करें
- Loss का जिम्मेदार User खुद है

---

Made with ❤️ for Indian Traders
