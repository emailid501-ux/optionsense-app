/**
 * OptionSense - Frontend Application
 * Real-time sentiment analysis for intraday option traders
 */

// Configuration
// Detect environment
const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
const CONFIG = {
    // If local, point to Python backend port 8000. If prod, use relative path (Vercel rewrites handles it)
    API_BASE_URL: isLocal ? 'http://localhost:8000' : '',
    REFRESH_INTERVAL: 2000,
    RETRY_DELAY: 5000,
    MAX_RETRIES: 3
};

// State
let state = {
    currentSymbol: 'NIFTY',
    currentTab: 'dashboard',
    currentStockFilter: 'buy',
    isLoading: false,
    lastData: null,
    stockData: null,
    refreshTimer: null,
    retryCount: 0
};

// DOM Elements
const elements = {
    // Header
    marketStatus: document.getElementById('marketStatus'),
    lastUpdated: document.getElementById('lastUpdated'),

    // Gauge
    gaugeNeedle: document.getElementById('gaugeNeedle'),
    sentimentScore: document.getElementById('sentimentScore'),
    sentimentLabel: document.getElementById('sentimentLabel'),

    // Alert
    alertBox: document.getElementById('alertBox'),
    alertText: document.getElementById('alertText'),

    // Metrics
    spotPrice: document.getElementById('spotPrice'),
    priceChange: document.getElementById('priceChange'),
    vwapValue: document.getElementById('vwapValue'),
    vwapStatus: document.getElementById('vwapStatus'),
    pcrValue: document.getElementById('pcrValue'),
    pcrTrend: document.getElementById('pcrTrend'),

    // OI Table
    oiTableBody: document.getElementById('oiTableBody'),

    // Overlays
    loadingOverlay: document.getElementById('loadingOverlay'),
    errorToast: document.getElementById('errorToast'),
    toastMessage: document.getElementById('toastMessage'),

    // Symbol Banners
    currentSymbol: document.getElementById('currentSymbol'),
    oiCurrentSymbol: document.getElementById('oiCurrentSymbol'),

    // Stock Screener
    stockList: document.getElementById('stockList'),
    buyCount: document.getElementById('buyCount'),
    sellCount: document.getElementById('sellCount'),
    holdCount: document.getElementById('holdCount'),

    // Stock Search
    stockSearch: document.getElementById('stockSearch'),
    searchBtn: document.getElementById('searchBtn')
};

// ===== API Functions =====

async function fetchDashboardData(symbol) {
    const response = await fetch(`${CONFIG.API_BASE_URL}/dashboard-snapshot?symbol=${symbol}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
}

async function fetchOIDetails(symbol) {
    const response = await fetch(`${CONFIG.API_BASE_URL}/oi-details?symbol=${symbol}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
}

async function fetchStockScreener(filter = 'all') {
    const response = await fetch(`${CONFIG.API_BASE_URL}/stock-screener?filter=${filter}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
}

async function fetchOptionStrategy(symbol) {
    const response = await fetch(`${CONFIG.API_BASE_URL}/stock/${symbol}/option-strategy`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
}

// Phase 15: Advanced Indicators API
async function fetchMarketOverview(symbol = 'NIFTY') {
    const response = await fetch(`${CONFIG.API_BASE_URL}/dashboard-snapshot?symbol=${symbol}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
}

// Phase 19: Pro Trader 8-Point Analysis API
async function fetchProAnalysis(symbol = 'NIFTY') {
    const response = await fetch(`${CONFIG.API_BASE_URL}/pro-analysis/${symbol}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
}

// ===== UI Update Functions =====

function showLoading(show) {
    state.isLoading = show;
    elements.loadingOverlay.classList.toggle('visible', show);
}

function showError(message) {
    elements.toastMessage.textContent = message;
    elements.errorToast.classList.add('visible');
    setTimeout(() => {
        elements.errorToast.classList.remove('visible');
    }, 4000);
}

function updateMarketStatus(status) {
    const isOpen = status === 'OPEN';
    elements.marketStatus.className = `market-status ${isOpen ? 'open' : 'closed'}`;
    elements.marketStatus.querySelector('.status-text').textContent = isOpen ? 'Market Open' : 'Market Closed';
}

function updateLastUpdated(timestamp) {
    const time = timestamp ? new Date(timestamp).toLocaleTimeString('en-IN') : '--:--:--';
    elements.lastUpdated.textContent = `Updated: ${time}`;
}

function updateSymbolDisplay(symbol) {
    // Update both symbol banners
    if (elements.currentSymbol) {
        elements.currentSymbol.textContent = symbol;
    }
    if (elements.oiCurrentSymbol) {
        elements.oiCurrentSymbol.textContent = symbol;
    }
}

function updateGauge(score, label, color) {
    // Score is 0-10, needle angle is -90 (left/sell) to +90 (right/buy)
    // Map: 0 -> -90deg, 5 -> 0deg, 10 -> +90deg
    const angle = (score - 5) * 18; // Each point = 18 degrees
    elements.gaugeNeedle.style.transform = `rotate(${angle}deg)`;

    // Update score display
    elements.sentimentScore.textContent = score;
    elements.sentimentLabel.textContent = label;

    // Update label styling
    elements.sentimentLabel.className = 'score-label';
    if (label === 'STRONG BUY') {
        elements.sentimentLabel.classList.add('bullish');
    } else if (label === 'STRONG SELL') {
        elements.sentimentLabel.classList.add('bearish');
    } else {
        elements.sentimentLabel.classList.add('neutral');
    }
}

function updateAlertBox(message, bgColor) {
    elements.alertText.textContent = message;

    // Determine alert type based on color
    elements.alertBox.className = 'alert-box';
    if (bgColor.includes('00E676') || bgColor.includes('69F0AE')) {
        elements.alertBox.classList.add('bullish');
    } else if (bgColor.includes('FF5252') || bgColor.includes('FF8A80')) {
        elements.alertBox.classList.add('bearish');
    } else {
        elements.alertBox.classList.add('neutral');
    }
}

function updateMetrics(data) {
    // Price
    elements.spotPrice.textContent = formatNumber(data.price);

    const changeEl = elements.priceChange;
    const isPositive = data.price_change >= 0;
    changeEl.className = `metric-change ${isPositive ? 'positive' : 'negative'}`;
    changeEl.querySelector('.change-value').textContent = `${isPositive ? '+' : ''}${formatNumber(data.price_change)}`;
    changeEl.querySelector('.change-pct').textContent = `(${isPositive ? '+' : ''}${data.price_change_pct.toFixed(2)}%)`;

    // VWAP
    elements.vwapValue.textContent = formatNumber(data.vwap_signal.value);
    elements.vwapStatus.textContent = data.vwap_signal.message;
    elements.vwapStatus.className = `metric-status ${data.vwap_signal.is_bullish ? 'bullish' : 'bearish'}`;

    // PCR
    elements.pcrValue.textContent = data.pcr.value.toFixed(2);
    const trendIcon = data.pcr.trend === 'RISING' ? '↑' : data.pcr.trend === 'FALLING' ? '↓' : '→';
    elements.pcrTrend.querySelector('.trend-icon').textContent = trendIcon;
    elements.pcrTrend.querySelector('.trend-text').textContent = data.pcr.trend;
}

function updateOITable(data) {
    const tbody = elements.oiTableBody;
    tbody.innerHTML = '';

    // Find max OI change for bar scaling
    const maxChange = Math.max(
        ...data.strikes.map(s => Math.max(Math.abs(s.ce_change), Math.abs(s.pe_change)))
    );

    data.strikes.forEach(strike => {
        const row = document.createElement('tr');
        if (strike.is_atm) row.classList.add('atm-row');

        // Call OI Change
        const ceCell = document.createElement('td');
        ceCell.className = 'td-call';
        ceCell.innerHTML = createOICell(strike.ce_change, strike.ce_bar_color, maxChange, true);
        row.appendChild(ceCell);

        // Strike Price
        const strikeCell = document.createElement('td');
        strikeCell.className = 'td-strike';
        strikeCell.textContent = strike.strike.toLocaleString();
        row.appendChild(strikeCell);

        // Put OI Change
        const peCell = document.createElement('td');
        peCell.className = 'td-put';
        peCell.innerHTML = createOICell(strike.pe_change, strike.pe_bar_color, maxChange, false);
        row.appendChild(peCell);

        tbody.appendChild(row);
    });
}

function createOICell(value, color, maxChange, isCall) {
    const barWidth = Math.min(80, (Math.abs(value) / maxChange) * 80);
    const valueClass = value >= 0 ? 'positive' : 'negative';
    const displayValue = formatOIValue(value);

    return `
        <div class="oi-cell">
            <div class="oi-bar ${color.toLowerCase()}" style="width: ${barWidth}px"></div>
            <span class="oi-value ${valueClass}">${displayValue}</span>
        </div>
    `;
}

// ===== Utility Functions =====

function formatNumber(num) {
    return num.toLocaleString('en-IN', { maximumFractionDigits: 2 });
}

function formatOIValue(value) {
    const absValue = Math.abs(value);
    const sign = value >= 0 ? '+' : '-';

    if (absValue >= 100000) {
        return `${sign}${(absValue / 100000).toFixed(1)}L`;
    } else if (absValue >= 1000) {
        return `${sign}${(absValue / 1000).toFixed(1)}K`;
    }
    return `${sign}${absValue}`;
}

// ===== Data Fetching =====

async function loadData(showOverlay = false) {
    if (state.isLoading) return;

    try {
        // Only show loading overlay on first load or manual refresh
        const isFirstLoad = !state.lastData;
        if (isFirstLoad || showOverlay) {
            showLoading(true);
        }
        state.isLoading = true;

        // Fetch both endpoints with timeout
        const fetchPromise = Promise.all([
            fetchDashboardData(state.currentSymbol),
            fetchOIDetails(state.currentSymbol)
        ]);

        const timeoutPromise = new Promise((_, reject) =>
            setTimeout(() => reject(new Error('Request timed out')), 25000)
        );

        const [dashboardData, oiData] = await Promise.race([fetchPromise, timeoutPromise]);

        // Update state
        state.lastData = { dashboard: dashboardData, oi: oiData };
        state.retryCount = 0;

        // Update UI
        updateSymbolDisplay(state.currentSymbol);
        updateMarketStatus(dashboardData.market_status);
        updateLastUpdated(dashboardData.last_updated);
        updateGauge(
            dashboardData.data.sentiment.score,
            dashboardData.data.sentiment.label,
            dashboardData.data.sentiment.color
        );
        updateAlertBox(
            dashboardData.data.oi_alert.message,
            dashboardData.data.oi_alert.bg_color
        );
        updateMetrics(dashboardData.data);
        updateOITable(oiData);

        // Phase 15: Load Advanced Indicators
        loadMarketOverview(state.currentSymbol, dashboardData.data);


    } catch (error) {
        console.error('Error fetching data:', error);
        state.retryCount++;

        if (state.retryCount <= CONFIG.MAX_RETRIES) {
            showError(`Connection error. Retrying... (${state.retryCount}/${CONFIG.MAX_RETRIES})`);
            setTimeout(loadData, CONFIG.RETRY_DELAY);
        } else {
            showError('Unable to connect to server. Please check if the backend is running.');
        }
    } finally {
        showLoading(false);
        state.isLoading = false;
    }
}

function startAutoRefresh() {
    stopAutoRefresh();
    state.refreshTimer = setInterval(loadData, CONFIG.REFRESH_INTERVAL);
}

function stopAutoRefresh() {
    if (state.refreshTimer) {
        clearInterval(state.refreshTimer);
        state.refreshTimer = null;
    }
}

// ===== Event Handlers =====

function setupEventListeners() {
    // Symbol toggle
    document.querySelectorAll('.toggle-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const symbol = btn.dataset.symbol;
            if (symbol === state.currentSymbol) return;

            // Update UI
            document.querySelector('.toggle-btn.active').classList.remove('active');
            btn.classList.add('active');

            // Update state and reload
            state.currentSymbol = symbol;
            loadData();
        });
    });

    // Tab navigation
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const tabId = tab.dataset.tab;
            if (tabId === state.currentTab) return;

            // Update tab buttons
            document.querySelector('.nav-tab.active').classList.remove('active');
            tab.classList.add('active');

            // Update tab content
            document.querySelector('.tab-pane.active').classList.remove('active');
            document.getElementById(tabId).classList.add('active');

            state.currentTab = tabId;
        });
    });

    // Refresh on visibility change
    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'visible') {
            loadData();
        }
    });

    // Stock filter buttons
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const filter = btn.dataset.filter;
            if (filter === state.currentStockFilter) return;

            // Update UI
            document.querySelector('.filter-btn.active').classList.remove('active');
            btn.classList.add('active');

            // Clear search box
            if (elements.stockSearch) elements.stockSearch.value = '';

            // Update state and reload
            state.currentStockFilter = filter;
            loadStockData();
        });
    });

    // Stock search
    console.log('🔍 Search Elements:', {
        searchBtn: elements.searchBtn,
        stockSearch: elements.stockSearch
    });
    if (elements.searchBtn) {
        elements.searchBtn.addEventListener('click', () => {
            console.log('🔍 Search button clicked!');
            searchStock();
        });
        console.log('✅ Search button listener attached');
    } else {
        console.log('❌ Search button NOT FOUND');
    }
    if (elements.stockSearch) {
        elements.stockSearch.addEventListener('keyup', (e) => {
            if (e.key === 'Enter') {
                console.log('🔍 Enter pressed!');
                searchStock();
            }
        });
        // Real-time search as you type (with debounce)
        let searchTimeout;
        elements.stockSearch.addEventListener('input', () => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(searchStock, 300);
        });
    }
}

// ===== Initialization =====

function init() {
    setupEventListeners();
    loadData();
    loadStockData();
    startAutoRefresh();

    console.log('🚀 OptionSense initialized');
    console.log(`📊 API: ${CONFIG.API_BASE_URL}`);
    console.log(`🔄 Refresh: Every ${CONFIG.REFRESH_INTERVAL / 1000}s`);
}

// Load stock screener data
async function loadStockData() {
    try {
        // Add timeout protection (60 seconds for 100 stocks)
        const fetchPromise = fetchStockScreener(state.currentStockFilter);
        const timeoutPromise = new Promise((_, reject) =>
            setTimeout(() => reject(new Error('Stock data request timed out')), 60000)
        );

        const data = await Promise.race([fetchPromise, timeoutPromise]);
        state.stockData = data;
        updateStockSummary(data.summary);
        updateStockList(data.stocks);
    } catch (error) {
        console.error('Error fetching stock data:', error);
        // Show error message in UI
        const container = elements.stockList;
        if (container) {
            container.innerHTML = `
                <div class="search-no-result">
                    <div class="emoji">⚠️</div>
                    <p>Failed to load stocks: ${error.message}</p>
                    <button onclick="loadStockData()" class="retry-btn">Retry</button>
                </div>
            `;
        }
    }
}

// Add helper to fetch specific stock
async function fetchStockDetail(symbol) {
    const response = await fetch(`${CONFIG.API_BASE_URL}/stock/${symbol}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
}

// Search for specific stock
async function searchStock() {
    const searchTerm = elements.stockSearch ? elements.stockSearch.value.trim().toUpperCase() : '';

    if (!searchTerm) {
        // If empty, reload all stocks
        loadStockData();
        return;
    }

    // If stockData is not loaded, try to fetch directly from server
    if (!state.stockData || !state.stockData.stocks) {
        // Show loading indicator
        const container = elements.stockList;
        if (container) {
            container.innerHTML = `
                <div class="search-no-result">
                    <div class="loading-spinner small"></div>
                    <p>Searching for "${searchTerm}"...</p>
                </div>
            `;

            try {
                // Fetch directly from server
                const stockDetail = await fetchStockDetail(searchTerm);
                if (stockDetail) {
                    container.innerHTML = createStockCard(stockDetail);
                    return;
                }
            } catch (e) {
                console.log("Error fetching stock:", e);
            }

            // Not found
            container.innerHTML = `
                <div class="search-no-result">
                    <div class="emoji">🔍</div>
                    <p>"${searchTerm}" not found</p>
                    <p style="font-size: 0.8rem; color: var(--text-muted); margin-top: 8px;">
                        Try loading stocks first, or try: RELIANCE, TCS, SBIN
                    </p>
                </div>
            `;
        }
        return;
    }

    // Filter stocks by symbol or name
    const filteredStocks = state.stockData.stocks.filter(stock =>
        stock.symbol.toUpperCase().includes(searchTerm) ||
        stock.name.toUpperCase().includes(searchTerm)
    );

    if (filteredStocks.length === 0) {
        // If searching a specific symbol (3+ chars), try the server on-demand
        const container = elements.stockList;
        if (container) {
            container.innerHTML = `
                <div class="search-no-result">
                    <div class="loading-spinner small"></div>
                    <p>Searching NSE for "${searchTerm}"...</p>
                </div>
            `;

            try {
                // Try fetching directly from server
                const stockDetail = await fetchStockDetail(searchTerm);
                if (stockDetail) {
                    // Update Summary counts (hacky but needed for UI consistency)
                    // Just show the single card
                    container.innerHTML = createStockCard(stockDetail);
                    return;
                }
            } catch (e) {
                console.log("Not found on server either", e);
            }

            // Still not found
            container.innerHTML = `
                <div class="search-no-result">
                    <div class="emoji">🔍</div>
                    <p>"${searchTerm}" not found in local list or NSE active list</p>
                    <p style="font-size: 0.8rem; color: var(--text-muted); margin-top: 8px;">
                        Try major stocks like: RELIANCE, TCS, CDSL, BSE
                    </p>
                </div>
            `;
        }
    } else {
        // Show filtered results
        updateStockList(filteredStocks);

        // Highlight the searched stock
        setTimeout(() => {
            const firstCard = document.querySelector('.stock-card-wrapper');
            if (firstCard) {
                firstCard.classList.add('highlight');
                firstCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }, 100);
    }
}

function updateStockSummary(summary) {
    if (elements.buyCount) elements.buyCount.textContent = summary.buy_signals;
    if (elements.sellCount) elements.sellCount.textContent = summary.sell_signals;
    if (elements.holdCount) elements.holdCount.textContent = summary.hold_signals;
}

function updateStockList(stocks) {
    const container = elements.stockList;
    if (!container) return;

    if (!stocks || stocks.length === 0) {
        container.innerHTML = `
            <div class="no-stocks">
                <div class="no-stocks-icon">📭</div>
                <p>No stocks found with this filter</p>
            </div>
        `;
        return;
    }

    // Store stocks for Best Pick analysis
    state.stockData = stocks;

    container.innerHTML = stocks.map(stock => createStockCard(stock)).join('');

    // Trigger Best Pick analysis (only once)
    if (!bestPickShown && stocks.length > 10) {
        triggerBestPickAnalysis();
    }
}

function createStockCard(stock) {
    const isPositive = stock.change >= 0;
    const recClass = stock.recommendation.toLowerCase().replace(' ', '-');

    // RSI indicator class
    const rsiClass = stock.indicators.rsi_signal === 'OVERSOLD' ? 'bullish' :
        stock.indicators.rsi_signal === 'OVERBOUGHT' ? 'bearish' : 'neutral';

    // MACD indicator class
    const macdClass = stock.indicators.macd === 'BULLISH' ? 'bullish' :
        stock.indicators.macd === 'BEARISH' ? 'bearish' : 'neutral';

    // Trading levels HTML
    const tradingLevelsHtml = stock.trading_levels && stock.trading_levels.entry ? `
        <div class="trading-levels">
            <div class="level-item">
                <span class="level-label">Entry</span>
                <span class="level-value entry">₹${formatNumber(stock.trading_levels.entry)}</span>
            </div>
            <div class="level-item">
                <span class="level-label">Target</span>
                <span class="level-value target">₹${formatNumber(stock.trading_levels.target)}</span>
            </div>
            <div class="level-item">
                <span class="level-label">Stoploss</span>
                <span class="level-value stoploss">₹${formatNumber(stock.trading_levels.stoploss)}</span>
            </div>
        </div>
    ` : '';

    // Reasons HTML (Hindi)
    const reasonsHtml = stock.reasons_hi && stock.reasons_hi.length > 0 ? `
        <div class="stock-reasons">
            <div class="reasons-title">📋 क्यों? (Reasons)</div>
            ${stock.reasons_hi.map(reason => `<div class="reason-item">${reason}</div>`).join('')}
        </div>
    ` : '';

    // Stock Analysis Checklist - Quick summary of all indicators
    let bullishChecks = 0;
    let bearishChecks = 0;

    // RSI check
    const rsiCheck = stock.indicators.rsi_signal === 'OVERSOLD' ? 'bullish' :
        stock.indicators.rsi_signal === 'OVERBOUGHT' ? 'bearish' : 'neutral';
    if (rsiCheck === 'bullish') bullishChecks++;
    else if (rsiCheck === 'bearish') bearishChecks++;

    // MACD check
    const macdCheck = stock.indicators.macd === 'BULLISH' ? 'bullish' :
        stock.indicators.macd === 'BEARISH' ? 'bearish' : 'neutral';
    if (macdCheck === 'bullish') bullishChecks++;
    else if (macdCheck === 'bearish') bearishChecks++;

    // Fib check
    const fibCheck = stock.indicators && stock.indicators.fib_signal === 'BULLISH' ? 'bullish' :
        stock.indicators && stock.indicators.fib_signal === 'BEARISH' ? 'bearish' : 'neutral';
    if (fibCheck === 'bullish') bullishChecks++;
    else if (fibCheck === 'bearish') bearishChecks++;

    // Price trend check (based on change)
    const trendCheck = stock.change > 0.5 ? 'bullish' : stock.change < -0.5 ? 'bearish' : 'neutral';
    if (trendCheck === 'bullish') bullishChecks++;
    else if (trendCheck === 'bearish') bearishChecks++;

    // Score check
    const scoreCheck = stock.score >= 7 ? 'bullish' : stock.score <= 3 ? 'bearish' : 'neutral';
    if (scoreCheck === 'bullish') bullishChecks++;
    else if (scoreCheck === 'bearish') bearishChecks++;

    // Final verdict
    const totalChecks = 5;
    let stockVerdict, verdictIcon, verdictClass;
    if (bullishChecks >= 3) {
        stockVerdict = `🚀 BULLISH (${bullishChecks}/${totalChecks} positive)`;
        verdictIcon = '🟢';
        verdictClass = 'bullish';
    } else if (bearishChecks >= 3) {
        stockVerdict = `🔻 BEARISH (${bearishChecks}/${totalChecks} negative)`;
        verdictIcon = '🔴';
        verdictClass = 'bearish';
    } else {
        stockVerdict = `⚖️ NEUTRAL - Wait for clarity`;
        verdictIcon = '🟡';
        verdictClass = 'neutral';
    }

    const stockChecklistHtml = `
        <div class="stock-checklist">
            <div class="checklist-header">📊 Quick Analysis</div>
            <div class="checklist-items-compact">
                <div class="check-item ${rsiCheck}">
                    <span class="check-label">RSI</span>
                    <span class="check-result">${stock.indicators.rsi} (${stock.indicators.rsi_signal})</span>
                </div>
                <div class="check-item ${macdCheck}">
                    <span class="check-label">MACD</span>
                    <span class="check-result">${stock.indicators.macd}</span>
                </div>
                <div class="check-item ${fibCheck}">
                    <span class="check-label">Fibonacci</span>
                    <span class="check-result">${stock.fib_levels ? stock.fib_levels.zone : 'N/A'}</span>
                </div>
                <div class="check-item ${trendCheck}">
                    <span class="check-label">Trend</span>
                    <span class="check-result">${stock.change > 0 ? '↑' : '↓'} ${stock.change_pct.toFixed(2)}%</span>
                </div>
                <div class="check-item ${scoreCheck}">
                    <span class="check-label">Score</span>
                    <span class="check-result">${stock.score}/10</span>
                </div>
            </div>
            <div class="stock-verdict ${verdictClass}">
                ${verdictIcon} ${stockVerdict}
            </div>
        </div>
    `;

    // Option Strategy Section
    const optionStrategyHtml = `
        <div class="option-strategy-container" id="option-strategy-${stock.symbol}">
            <button class="option-btn" onclick="toggleOptionStrategy('${stock.symbol}')">
                📈 Get 1-Week Option Strategy
            </button>
            <div class="option-content" style="display: none;">
                <div class="loading-spinner small"></div>
            </div>
        </div>
    `;

    // Phase 19: Pro Trader 8-Point Analysis Button
    const proAnalysisHtml = `
        <div class="pro-analysis-container" id="pro-analysis-${stock.symbol}">
            <button class="pro-analysis-btn" onclick="toggleProAnalysis('${stock.symbol}')">
                📊 Show Pro Analysis (8-Point)
            </button>
            <div class="pro-analysis-content" style="display: none;">
                <div class="loading-spinner small"></div>
            </div>
        </div>
    `;

    // Fib signal class
    const fibClass = stock.indicators && stock.indicators.fib_signal === 'BULLISH' ? 'bullish' :
        stock.indicators && stock.indicators.fib_signal === 'BEARISH' ? 'bearish' : 'neutral';

    // Fibonacci levels HTML
    const fibLevelsHtml = stock.fib_levels ? `
        <div class="fib-levels">
            <div class="fib-title">
                📐 Fibonacci Levels
                <span class="fib-signal ${fibClass}">${stock.fib_levels.signal}</span>
            </div>
            <div class="fib-level support">
                <span class="fib-level-name">Support</span>
                <span class="fib-level-value">₹${formatNumber(stock.fib_levels.nearest_support)}</span>
            </div>
            <div class="fib-level golden">
                <span class="fib-level-name">61.8%</span>
                <span class="fib-level-value">₹${formatNumber(stock.fib_levels.fib_618)}</span>
            </div>
            <div class="fib-level">
                <span class="fib-level-name">50%</span>
                <span class="fib-level-value">₹${formatNumber(stock.fib_levels.fib_500)}</span>
            </div>
            <div class="fib-level">
                <span class="fib-level-name">38.2%</span>
                <span class="fib-level-value">₹${formatNumber(stock.fib_levels.fib_382)}</span>
            </div>
            <div class="fib-level resistance">
                <span class="fib-level-name">Resistance</span>
                <span class="fib-level-value">₹${formatNumber(stock.fib_levels.nearest_resistance)}</span>
            </div>
        </div>
    ` : '';

    return `
        <div class="stock-card-wrapper" data-symbol="${stock.symbol}">
             <!-- ... existing card content ... -->
            <div class="stock-card" onclick="toggleStockDetails(this)">
                <!-- ... header ... -->
                <div class="stock-info">
                    <span class="stock-symbol">${stock.symbol}</span>
                    <span class="stock-name">${stock.name}</span>
                    <span class="stock-sector">${stock.sector}</span>
                    <div class="stock-indicators">
                        <span class="indicator-badge ${rsiClass}">RSI ${stock.indicators.rsi}</span>
                        <span class="indicator-badge ${macdClass}">${stock.indicators.macd}</span>
                        <span class="indicator-badge ${fibClass}">FIB</span>
                    </div>
                </div>
                <div class="stock-price-section">
                    <span class="stock-price" id="price-${stock.symbol}">₹${formatNumber(stock.price)}</span>
                    <span class="stock-change ${isPositive ? 'positive' : 'negative'}" id="change-${stock.symbol}">
                        ${isPositive ? '+' : ''}${stock.change_pct.toFixed(2)}%
                    </span>
                </div>
                <div class="stock-recommendation">
                    <span class="rec-badge ${recClass}">${stock.recommendation}</span>
                    <span class="rec-score">Score: ${stock.score}</span>
                    ${stock.trading_levels && stock.trading_levels.risk_reward !== 'N/A' ?
            `<span class="risk-reward">R:R ${stock.trading_levels.risk_reward}</span>` : ''}
                </div>
            </div>
            ${tradingLevelsHtml}
            ${stockChecklistHtml}
            ${optionStrategyHtml}
            ${proAnalysisHtml}
            ${fibLevelsHtml}
            ${reasonsHtml}
        </div>
    `;
}

// Function to handle option strategy toggle
async function toggleOptionStrategy(symbol) {
    const container = document.getElementById(`option-strategy-${symbol}`);
    if (!container) return;

    const content = container.querySelector('.option-content');
    const button = container.querySelector('.option-btn');

    // Toggle visibility
    if (content.style.display !== 'none' && content.dataset.loaded === 'true') {
        content.style.display = 'none';
        button.textContent = '📈 Get 1-Week Option Strategy';
        return;
    }

    content.style.display = 'block';
    button.textContent = '🔄 Loading...';
    button.disabled = true;

    try {
        // Add timeout protection (15 seconds)
        const fetchPromise = fetchOptionStrategy(symbol);
        const timeoutPromise = new Promise((_, reject) =>
            setTimeout(() => reject(new Error('Request timed out (Backend busy)')), 30000)
        );

        const strategy = await Promise.race([fetchPromise, timeoutPromise]);
        renderOptionStrategy(container, strategy);
    } catch (error) {
        content.innerHTML = `<div class="error-msg">Failed to load strategy: ${error.message}</div>`;
        button.textContent = '⚠ Retry Strategy';
        button.disabled = false;
    }
}

function renderOptionStrategy(container, strategy) {
    const content = container.querySelector('.option-content');
    const button = container.querySelector('.option-btn');

    if (strategy.status === 'NO_TRADE' || strategy.status === 'ERROR') {
        content.innerHTML = `
            <div class="strategy-card neutral">
                <div class="strategy-header">
                    <span class="strategy-type">${strategy.status === 'NO_TRADE' ? '🚫 NO TRADE' : '⚠ ERROR'}</span>
                </div>
                <p class="strategy-reason">${strategy.message}</p>
            </div>
        `;
    } else {
        const isCall = strategy.option_type === 'CE';
        const typeClass = isCall ? 'bullish' : 'bearish';

        content.innerHTML = `
            <div class="strategy-card ${typeClass}">
                <div class="strategy-header">
                    <span class="strategy-type">
                        ${isCall ? '🟢 BUY CALL (Bullish)' : '🔴 BUY PUT (Bearish)'}
                        ${strategy.is_estimated ? '<span class="est-badge" title="Market Closed - Data Estimated">🚧 EST</span>' : ''}
                    </span>
                    <span class="strategy-expiry">Exp: ${strategy.expiry}</span>
                </div>
                
                ${strategy.is_estimated ? `<div class="est-warning">⚠️ ${strategy.message || 'Market Closed: Prices are estimated'}</div>` : ''}
                
                <div class="strategy-main">
                    <div class="strategy-strike">
                        <span class="strike-price">${strategy.symbol} ${strategy.strike_price} ${strategy.option_type}</span>
                        <span class="strike-ltp">@ ₹${strategy.ltp}</span>
                    </div>
                    
                    <div class="strategy-levels">
                        <div class="level-box">
                            <span class="lbl">Entry</span>
                            <span class="val">₹${strategy.entry_range}</span>
                        </div>
                        <div class="level-box">
                            <span class="lbl">Target</span>
                            <span class="val">₹${strategy.target}</span>
                        </div>
                        <div class="level-box">
                            <span class="lbl">SL</span>
                            <span class="val">₹${strategy.stoploss}</span>
                        </div>
                    </div>
                </div>
                
                <div class="strategy-footer">
                   <div class="strategy-chips">
                        <span class="chip">Risk/Reward: ${strategy.risk_reward}</span>
                        <span class="chip">Margin: ~₹${strategy.required_margin}</span>
                   </div>
                   <p class="strategy-reason">💡 ${strategy.reason}</p>
                </div>
            </div>
        `;
    }

    content.dataset.loaded = 'true';
    button.style.display = 'none'; // Hide button after loading or keep it to toggle? Let's hide it or change text
    // actually better to keep it to toggle close, but simplifying UI
}

// ===== Phase 19: Pro Trader 8-Point Analysis =====
async function toggleProAnalysis(symbol) {
    const container = document.getElementById(`pro-analysis-${symbol}`);
    if (!container) return;

    const content = container.querySelector('.pro-analysis-content');
    const button = container.querySelector('.pro-analysis-btn');

    // Toggle visibility
    if (content.style.display === 'block') {
        content.style.display = 'none';
        button.textContent = '📊 Show Pro Analysis (8-Point)';
        return;
    }

    content.style.display = 'block';
    button.textContent = '⏳ Loading...';

    try {
        const analysis = await fetchProAnalysis(symbol);
        renderProAnalysis(content, analysis);
        button.textContent = '📊 Hide Pro Analysis';
    } catch (error) {
        content.innerHTML = `<div class="pro-error">❌ Failed to load Pro Analysis: ${error.message}</div>`;
        button.textContent = '📊 Retry Pro Analysis';
    }
}

function renderProAnalysis(container, data) {
    const pcr = data['1_pcr'] || {};
    const oiShift = data['2_oi_shift'] || {};
    const vixIv = data['3_vix_iv'] || {};
    const volume = data['4_volume'] || {};
    const oiLadder = data['5_oi_ladder'] || {};
    const theta = data['6_theta_decay'] || {};
    const breadth = data['7_market_breadth'] || {};
    const vwap = data['8_vwap'] || {};
    const verdict = data['overall_verdict'] || {};

    container.innerHTML = `
        <div class="pro-analysis-grid">
            <!-- Overall Verdict -->
            <div class="pro-verdict ${verdict.verdict?.toLowerCase() || 'neutral'}">
                <h4>🎯 Overall Verdict</h4>
                <span class="verdict-badge">${verdict.verdict || 'ANALYZING'}</span>
                <p>${verdict.message || 'Analyzing...'}</p>
                <div class="signal-count">
                    <span class="bullish">🟢 ${verdict.bullish_signals || 0}</span>
                    <span class="bearish">🔴 ${verdict.bearish_signals || 0}</span>
                </div>
            </div>

            <!-- 1. PCR -->
            <div class="pro-card" style="border-left: 4px solid ${pcr.color || '#888'}">
                <div class="pro-header">
                    <span class="pro-num">1</span>
                    <span class="pro-title">PCR Analysis</span>
                    <span class="pro-badge" style="background: ${pcr.color || '#888'}">${pcr.signal || 'N/A'}</span>
                </div>
                <div class="pro-value">${pcr.pcr || 'N/A'}</div>
                <div class="pro-interpret">${pcr.interpretation || 'Loading...'}</div>
                <div class="pro-strategy">📌 ${pcr.strategy || ''}</div>
            </div>

            <!-- 2. OI Shift -->
            <div class="pro-card" style="border-left: 4px solid ${oiShift.signal === 'BULLISH' ? '#00E676' : oiShift.signal === 'BEARISH' ? '#FF5252' : '#FFD600'}">
                <div class="pro-header">
                    <span class="pro-num">2</span>
                    <span class="pro-title">OI Shift</span>
                    <span class="pro-badge ${oiShift.signal?.toLowerCase()}">${oiShift.signal || 'NEUTRAL'}</span>
                </div>
                <div class="pro-levels">
                    <span class="support">📉 Max Put: ₹${oiShift.max_put_strike || 'N/A'}</span>
                    <span class="resistance">📈 Max Call: ₹${oiShift.max_call_strike || 'N/A'}</span>
                </div>
                <div class="pro-interpret">${oiShift.interpretation || 'No shift detected'}</div>
            </div>

            <!-- 3. VIX & IV -->
            <div class="pro-card">
                <div class="pro-header">
                    <span class="pro-num">3</span>
                    <span class="pro-title">VIX & IV Skew</span>
                    <span class="pro-badge ${vixIv.overall_signal?.toLowerCase()}">${vixIv.overall_signal || 'N/A'}</span>
                </div>
                <div class="pro-metrics">
                    <div class="metric"><span>VIX</span><strong>${vixIv.vix || 'N/A'}</strong></div>
                    <div class="metric"><span>Put IV</span><strong>${vixIv.put_iv || 'N/A'}</strong></div>
                    <div class="metric"><span>Call IV</span><strong>${vixIv.call_iv || 'N/A'}</strong></div>
                </div>
                <div class="pro-interpret">${vixIv.iv_interpretation || ''}</div>
                <div class="pro-strategy">📌 ${vixIv.vix_strategy || ''}</div>
            </div>

            <!-- 4. Volume -->
            <div class="pro-card" style="border-left: 4px solid ${volume.color || '#888'}">
                <div class="pro-header">
                    <span class="pro-num">4</span>
                    <span class="pro-title">Volume Analysis</span>
                    <span class="pro-badge" style="background: ${volume.color || '#888'}">${volume.signal?.replace('_', ' ') || 'N/A'}</span>
                </div>
                <div class="pro-metrics">
                    <div class="metric"><span>Volume Ratio</span><strong>${volume.volume_ratio || 'N/A'}x</strong></div>
                    <div class="metric"><span>Price Δ</span><strong>₹${volume.price_change || 0}</strong></div>
                </div>
                <div class="pro-interpret">${volume.interpretation || ''}</div>
            </div>

            <!-- 5. OI Ladder -->
            <div class="pro-card pro-wide">
                <div class="pro-header">
                    <span class="pro-num">5</span>
                    <span class="pro-title">OI Ladder</span>
                </div>
                <div class="ladder-grid">
                    <div class="ladder-col resistance">
                        <h5>🔴 Resistance</h5>
                        <p>${oiLadder.resistance_text || 'Loading...'}</p>
                    </div>
                    <div class="ladder-col support">
                        <h5>🟢 Support</h5>
                        <p>${oiLadder.support_text || 'Loading...'}</p>
                    </div>
                </div>
            </div>

            <!-- 6. Theta Decay -->
            <div class="pro-card">
                <div class="pro-header">
                    <span class="pro-num">6</span>
                    <span class="pro-title">Theta Decay</span>
                    <span class="pro-badge ${theta.signal?.toLowerCase()}">${theta.signal || 'N/A'}</span>
                </div>
                <div class="pro-metrics">
                    <div class="metric"><span>ATM Straddle</span><strong>₹${theta.straddle_price || 'N/A'}</strong></div>
                    <div class="metric"><span>Daily Theta</span><strong>~₹${theta.estimated_theta || 'N/A'}</strong></div>
                </div>
                <div class="pro-interpret">${theta.interpretation || ''}</div>
                <div class="pro-strategy">📌 ${theta.strategy || ''}</div>
            </div>

            <!-- 7. Market Breadth -->
            <div class="pro-card" style="border-left: 4px solid ${breadth.color || '#888'}">
                <div class="pro-header">
                    <span class="pro-num">7</span>
                    <span class="pro-title">Market Breadth</span>
                    <span class="pro-badge" style="background: ${breadth.color || '#888'}">${breadth.signal || 'N/A'}</span>
                </div>
                <div class="breadth-bar">
                    <div class="breadth-green" style="width: ${(breadth.advancing || 0) * 2}%">${breadth.advancing || 0}</div>
                    <div class="breadth-red" style="width: ${(breadth.declining || 0) * 2}%">${breadth.declining || 0}</div>
                </div>
                <div class="pro-interpret">${breadth.interpretation || ''}</div>
            </div>

            <!-- 8. VWAP -->
            <div class="pro-card">
                <div class="pro-header">
                    <span class="pro-num">8</span>
                    <span class="pro-title">VWAP Analysis</span>
                    <span class="pro-badge ${vwap.signal?.toLowerCase()}">${vwap.signal?.replace('_', ' ') || 'N/A'}</span>
                </div>
                <div class="pro-metrics">
                    <div class="metric"><span>VWAP</span><strong>₹${vwap.vwap || 'N/A'}</strong></div>
                    <div class="metric"><span>Distance</span><strong>${vwap.distance_pct || 0}%</strong></div>
                </div>
                <div class="pro-interpret">${vwap.interpretation || ''}</div>
                <div class="pro-strategy">📌 Entry: ${vwap.entry_recommendation || ''}</div>
            </div>
        </div>
    `;
}

// Start the app
document.addEventListener('DOMContentLoaded', init);

// ===== PWA Service Worker Registration =====
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then((registration) => {
                console.log('📱 PWA: Service Worker registered successfully');
                console.log('   Scope:', registration.scope);
            })
            .catch((error) => {
                console.log('📱 PWA: Service Worker registration failed:', error);
            });
    });
}

// Install prompt handling
let deferredPrompt;
window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    console.log('📱 PWA: Install prompt available');

    // Show install button or notification (optional)
    showInstallPrompt();
});

function showInstallPrompt() {
    // Create install button if it doesn't exist
    if (!document.getElementById('installBtn')) {
        const installBtn = document.createElement('button');
        installBtn.id = 'installBtn';
        installBtn.className = 'install-btn';
        installBtn.innerHTML = '📲 Install App';
        installBtn.onclick = installApp;

        // Add to header
        const header = document.querySelector('.header-right');
        if (header) {
            header.insertBefore(installBtn, header.firstChild);
        }
    }
}

async function installApp() {
    if (!deferredPrompt) return;

    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    console.log(`📱 PWA: User response to install: ${outcome}`);

    if (outcome === 'accepted') {
        // Hide install button
        const installBtn = document.getElementById('installBtn');
        if (installBtn) installBtn.remove();
    }
    deferredPrompt = null;
}

window.addEventListener('appinstalled', () => {
    console.log('📱 PWA: App installed successfully!');
    deferredPrompt = null;
});

// Failsafe: Force remove loading overlay after 5 seconds
setTimeout(() => {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay && overlay.classList.contains('visible')) {
        console.warn('⚠️ Force removing loading overlay due to timeout');
        overlay.classList.remove('visible');
    }
}, 5000);


// ===== Phase 15: Pro Trader Panel Functions =====

async function loadMarketOverview(symbol, dashboardData) {
    try {
        const overview = await fetchMarketOverview(symbol);
        updateProTraderPanel(overview, dashboardData);
    } catch (error) {
        console.error('Error loading market overview:', error);
        // Show fallback values on error
        showProTraderFallback(dashboardData);
    }
}

function showProTraderFallback(dashboardData) {
    // VIX fallback
    const vixValue = document.getElementById('vixValue');
    const vixStatus = document.getElementById('vixStatus');
    const vixAction = document.getElementById('vixAction');
    if (vixValue) {
        vixValue.textContent = '--';
        vixStatus.textContent = 'Connecting...';
        vixStatus.className = 'indicator-status YELLOW';
        vixAction.textContent = 'Data loading from server';
    }

    // Market Breadth fallback
    const breadthValue = document.getElementById('breadthValue');
    const breadthStatus = document.getElementById('breadthStatus');
    const breadthAction = document.getElementById('breadthAction');
    if (breadthValue) {
        breadthValue.innerHTML = '<span class="adv">--</span> ↑ | <span class="dec">--</span> ↓';
        breadthStatus.textContent = 'Loading...';
        breadthStatus.className = 'indicator-status YELLOW';
        breadthAction.textContent = 'Fetching market data';
    }

    // Straddle fallback
    const straddleValue = document.getElementById('straddleValue');
    const straddleStatus = document.getElementById('straddleStatus');
    if (straddleValue) {
        straddleValue.textContent = '₹--';
        straddleStatus.textContent = 'Loading option chain...';
    }

    // Still update checklist with available dashboard data
    if (dashboardData) {
        updatePartialChecklist(dashboardData);
    }
}

function updatePartialChecklist(dashboardData) {
    // PCR Check
    const checkPCR = document.getElementById('checkPCR');
    const checkPCRResult = document.getElementById('checkPCRResult');
    if (checkPCR && dashboardData && dashboardData.pcr) {
        const icon = checkPCR.querySelector('.check-icon');
        icon.textContent = '✅';
        const pcrValue = dashboardData.pcr.value;
        const pcrStatus = pcrValue > 1 ? 'BULLISH' : pcrValue < 0.7 ? 'BEARISH' : 'NEUTRAL';
        checkPCRResult.textContent = `${pcrValue.toFixed(2)} - ${pcrStatus}`;
        checkPCRResult.className = `check-result ${pcrStatus.toLowerCase()}`;
    }

    // VWAP Check
    const checkVWAP = document.getElementById('checkVWAP');
    const checkVWAPResult = document.getElementById('checkVWAPResult');
    if (checkVWAP && dashboardData && dashboardData.vwap_signal) {
        const icon = checkVWAP.querySelector('.check-icon');
        icon.textContent = '✅';
        const vwapStatus = dashboardData.vwap_signal.is_bullish ? 'Above VWAP ↑' : 'Below VWAP ↓';
        checkVWAPResult.textContent = vwapStatus;
        checkVWAPResult.className = `check-result ${dashboardData.vwap_signal.is_bullish ? 'bullish' : 'bearish'}`;
    }
}

function updateProTraderPanel(overview, dashboardData) {
    // Update VIX Card
    const vixValue = document.getElementById('vixValue');
    const vixStatus = document.getElementById('vixStatus');
    const vixAction = document.getElementById('vixAction');

    if (vixValue && overview.vix) {
        vixValue.textContent = overview.vix.value;
        vixStatus.textContent = overview.vix.status;
        vixStatus.className = `indicator-status ${overview.vix.color}`;
        vixAction.textContent = overview.vix.action;
    }

    // Update Market Breadth Card
    const breadthValue = document.getElementById('breadthValue');
    const breadthStatus = document.getElementById('breadthStatus');
    const breadthAction = document.getElementById('breadthAction');

    if (breadthValue && overview.breadth) {
        breadthValue.innerHTML = `<span class="adv">${overview.breadth.advancing}</span> ↑ | <span class="dec">${overview.breadth.declining}</span> ↓`;
        breadthStatus.textContent = overview.breadth.status;
        breadthStatus.className = `indicator-status ${overview.breadth.color}`;
        breadthAction.textContent = overview.breadth.action;
    }

    // Update Straddle/Theta Card
    const straddleValue = document.getElementById('straddleValue');
    const straddleStatus = document.getElementById('straddleStatus');
    const straddleAction = document.getElementById('straddleAction');

    if (straddleValue && overview.straddle) {
        straddleValue.textContent = `₹${overview.straddle.straddle_price || '--'}`;
        straddleStatus.textContent = `ATM Strike: ${overview.straddle.atm_strike || '--'}`;
        straddleAction.textContent = overview.straddle.action || '--';
    }

    // Update OI Ladder
    updateOILadder(overview.oi_ladder);

    // Update Checklist
    updateTraderChecklist(overview, dashboardData);
}

function updateOILadder(ladderData) {
    const resistanceLevels = document.getElementById('resistanceLevels');
    const supportLevels = document.getElementById('supportLevels');

    if (!resistanceLevels || !supportLevels || !ladderData) return;

    // Find max OI for scaling
    const allOI = [...(ladderData.resistances || []), ...(ladderData.supports || [])];
    const maxOI = Math.max(...allOI.map(l => l.oi)) || 1;

    // Render Resistances
    if (ladderData.resistances && ladderData.resistances.length > 0) {
        resistanceLevels.innerHTML = ladderData.resistances.map(level => {
            const barWidth = Math.min(100, (level.oi / maxOI) * 100);
            const oiFormatted = (level.oi / 100000).toFixed(1) + 'L';
            return `
                <div class="ladder-item">
                    <span class="ladder-strike">${level.strike}</span>
                    <div class="ladder-bar" style="width: ${barWidth}%"></div>
                    <span class="ladder-oi">${oiFormatted}</span>
                </div>
            `;
        }).join('');
    } else {
        resistanceLevels.innerHTML = '<div class="ladder-item">No data</div>';
    }

    // Render Supports
    if (ladderData.supports && ladderData.supports.length > 0) {
        supportLevels.innerHTML = ladderData.supports.map(level => {
            const barWidth = Math.min(100, (level.oi / maxOI) * 100);
            const oiFormatted = (level.oi / 100000).toFixed(1) + 'L';
            return `
                <div class="ladder-item">
                    <span class="ladder-strike">${level.strike}</span>
                    <div class="ladder-bar" style="width: ${barWidth}%"></div>
                    <span class="ladder-oi">${oiFormatted}</span>
                </div>
            `;
        }).join('');
    } else {
        supportLevels.innerHTML = '<div class="ladder-item">No data</div>';
    }
}

function updateTraderChecklist(overview, dashboardData) {
    let bullishCount = 0;
    let bearishCount = 0;

    // Check 1: Market Breadth
    const checkBreadth = document.getElementById('checkBreadth');
    const checkBreadthResult = document.getElementById('checkBreadthResult');
    if (checkBreadth && overview.breadth) {
        const icon = checkBreadth.querySelector('.check-icon');
        icon.textContent = '✅';
        icon.classList.add('checked');
        checkBreadthResult.textContent = overview.breadth.status;
        checkBreadthResult.className = `check-result ${overview.breadth.status === 'BULLISH' ? 'bullish' : overview.breadth.status === 'BEARISH' ? 'bearish' : 'neutral'}`;
        if (overview.breadth.status === 'BULLISH') bullishCount++;
        else if (overview.breadth.status === 'BEARISH') bearishCount++;
    }

    // Check 2: PCR
    const checkPCR = document.getElementById('checkPCR');
    const checkPCRResult = document.getElementById('checkPCRResult');
    if (checkPCR && dashboardData && dashboardData.pcr) {
        const icon = checkPCR.querySelector('.check-icon');
        icon.textContent = '✅';
        icon.classList.add('checked');
        const pcrValue = dashboardData.pcr.value;
        const pcrStatus = pcrValue > 1 ? 'BULLISH' : pcrValue < 0.7 ? 'BEARISH' : 'NEUTRAL';
        checkPCRResult.textContent = `${pcrValue.toFixed(2)} - ${pcrStatus}`;
        checkPCRResult.className = `check-result ${pcrStatus.toLowerCase()}`;
        if (pcrStatus === 'BULLISH') bullishCount++;
        else if (pcrStatus === 'BEARISH') bearishCount++;
    }

    // Check 3: VWAP
    const checkVWAP = document.getElementById('checkVWAP');
    const checkVWAPResult = document.getElementById('checkVWAPResult');
    if (checkVWAP && dashboardData && dashboardData.vwap_signal) {
        const icon = checkVWAP.querySelector('.check-icon');
        icon.textContent = '✅';
        icon.classList.add('checked');
        const vwapStatus = dashboardData.vwap_signal.is_bullish ? 'Above VWAP ↑' : 'Below VWAP ↓';
        checkVWAPResult.textContent = vwapStatus;
        checkVWAPResult.className = `check-result ${dashboardData.vwap_signal.is_bullish ? 'bullish' : 'bearish'}`;
        if (dashboardData.vwap_signal.is_bullish) bullishCount++;
        else bearishCount++;
    }

    // Check 4: VIX
    const checkVIX = document.getElementById('checkVIX');
    const checkVIXResult = document.getElementById('checkVIXResult');
    if (checkVIX && overview.vix) {
        const icon = checkVIX.querySelector('.check-icon');
        icon.textContent = '✅';
        icon.classList.add('checked');
        checkVIXResult.textContent = `${overview.vix.value} - ${overview.vix.status}`;
        const vixClass = overview.vix.color === 'GREEN' ? 'bullish' : overview.vix.color === 'RED' ? 'bearish' : 'neutral';
        checkVIXResult.className = `check-result ${vixClass}`;
        if (overview.vix.color === 'GREEN') bullishCount++;
        else if (overview.vix.color === 'RED') bearishCount++;
    }

    // Check 5: OI Levels
    const checkOI = document.getElementById('checkOI');
    const checkOIResult = document.getElementById('checkOIResult');
    if (checkOI && overview.oi_ladder) {
        const icon = checkOI.querySelector('.check-icon');
        icon.textContent = '✅';
        icon.classList.add('checked');
        const support = overview.oi_ladder.max_support || '--';
        const resistance = overview.oi_ladder.max_resistance || '--';
        checkOIResult.textContent = `S:${support} R:${resistance}`;
        checkOIResult.className = 'check-result neutral';
    }

    // Final Verdict
    const verdict = document.getElementById('checklistVerdict');
    if (verdict) {
        const verdictText = verdict.querySelector('.verdict-text');
        const verdictIcon = verdict.querySelector('.verdict-icon');

        if (bullishCount >= 3) {
            verdictIcon.textContent = '🚀';
            verdictText.textContent = `BULLISH Signal (${bullishCount}/5 indicators positive) - Look for BUY/CALL`;
            verdictText.className = 'verdict-text bullish';
        } else if (bearishCount >= 3) {
            verdictIcon.textContent = '🔻';
            verdictText.textContent = `BEARISH Signal (${bearishCount}/5 indicators negative) - Look for SELL/PUT`;
            verdictText.className = 'verdict-text bearish';
        } else {
            verdictIcon.textContent = '⚖️';
            verdictText.textContent = `NEUTRAL Signal - Mixed indicators. Wait for clarity.`;
            verdictText.className = 'verdict-text';
        }
    }
}

// ===== Today's Best Pick Feature =====

let bestPickShown = false;

function findBestPick(stocks) {
    if (!stocks || stocks.length === 0) return null;

    // Filter stocks with BUY recommendation and score >= 7
    let bestStocks = stocks.filter(s =>
        s.recommendation === 'Buy' && s.score >= 7
    );

    if (bestStocks.length === 0) {
        // Fallback: get highest scoring stock
        bestStocks = [...stocks].sort((a, b) => b.score - a.score);
    }

    // Calculate composite score for each stock
    bestStocks.forEach(stock => {
        let compositeScore = stock.score * 10; // Base score (0-100)

        // RSI bonus
        if (stock.indicators.rsi_signal === 'OVERSOLD') compositeScore += 20;
        else if (stock.indicators.rsi_signal === 'OVERBOUGHT') compositeScore -= 20;

        // MACD bonus
        if (stock.indicators.macd === 'BULLISH') compositeScore += 15;
        else if (stock.indicators.macd === 'BEARISH') compositeScore -= 15;

        // Fibonacci bonus
        if (stock.indicators.fib_signal === 'BULLISH') compositeScore += 10;
        else if (stock.indicators.fib_signal === 'BEARISH') compositeScore -= 10;

        // Price trend bonus
        if (stock.change_pct > 1) compositeScore += 10;
        else if (stock.change_pct < -1) compositeScore -= 10;

        // Risk-Reward bonus
        if (stock.trading_levels && stock.trading_levels.risk_reward !== 'N/A') {
            const rr = parseFloat(stock.trading_levels.risk_reward);
            if (rr >= 2) compositeScore += 15;
            else if (rr >= 1.5) compositeScore += 10;
        }

        stock.compositeScore = compositeScore;
    });

    // Sort by composite score and return best
    bestStocks.sort((a, b) => b.compositeScore - a.compositeScore);
    return bestStocks[0];
}

function showBestPickPopup(stock) {
    if (!stock || bestPickShown) return;

    const overlay = document.getElementById('bestPickOverlay');
    if (!overlay) return;

    // Populate stock info
    document.getElementById('bestPickSymbol').textContent = stock.symbol;
    document.getElementById('bestPickName').textContent = stock.name;
    document.getElementById('bestPickScore').textContent = `Score: ${stock.score}/10`;

    // Verdict
    const verdictEl = document.getElementById('bestPickVerdict');
    if (stock.recommendation === 'Buy' && stock.score >= 8) {
        verdictEl.innerHTML = '🚀 <strong>STRONG BUY</strong> - High Confidence';
        verdictEl.className = 'best-pick-verdict bullish';
    } else if (stock.recommendation === 'Buy') {
        verdictEl.innerHTML = '📈 <strong>BUY</strong> - Good Opportunity';
        verdictEl.className = 'best-pick-verdict bullish';
    } else {
        verdictEl.innerHTML = '👀 <strong>WATCH</strong> - Monitor for Entry';
        verdictEl.className = 'best-pick-verdict neutral';
    }

    // Trading levels
    if (stock.trading_levels) {
        document.getElementById('bestPickEntry').textContent =
            `₹${formatNumber(stock.trading_levels.entry)}`;
        document.getElementById('bestPickTarget').textContent =
            `₹${formatNumber(stock.trading_levels.target)}`;
        document.getElementById('bestPickStoploss').textContent =
            `₹${formatNumber(stock.trading_levels.stoploss)}`;
    }

    // Indicators
    const indicatorsEl = document.getElementById('bestPickIndicators');
    indicatorsEl.innerHTML = `
        <div class="indicator-item ${stock.indicators.rsi_signal === 'OVERSOLD' ? 'bullish' : stock.indicators.rsi_signal === 'OVERBOUGHT' ? 'bearish' : ''}">
            <span>RSI</span>
            <span>${stock.indicators.rsi} (${stock.indicators.rsi_signal})</span>
        </div>
        <div class="indicator-item ${stock.indicators.macd === 'BULLISH' ? 'bullish' : stock.indicators.macd === 'BEARISH' ? 'bearish' : ''}">
            <span>MACD</span>
            <span>${stock.indicators.macd}</span>
        </div>
        <div class="indicator-item ${stock.indicators.fib_signal === 'BULLISH' ? 'bullish' : stock.indicators.fib_signal === 'BEARISH' ? 'bearish' : ''}">
            <span>Fibonacci</span>
            <span>${stock.fib_levels ? stock.fib_levels.zone : 'N/A'}</span>
        </div>
        <div class="indicator-item ${stock.change_pct > 0 ? 'bullish' : 'bearish'}">
            <span>Trend</span>
            <span>${stock.change_pct > 0 ? '↑' : '↓'} ${stock.change_pct.toFixed(2)}%</span>
        </div>
    `;

    // Reasons
    const reasonEl = document.getElementById('bestPickReason');
    if (stock.reasons_hi && stock.reasons_hi.length > 0) {
        reasonEl.innerHTML = stock.reasons_hi.slice(0, 2).map(r => `<div>• ${r}</div>`).join('');
    } else {
        reasonEl.innerHTML = `<div>• Strong technical indicators</div><div>• Good risk-reward ratio</div>`;
    }

    // Show popup with animation
    overlay.style.display = 'flex';
    setTimeout(() => overlay.classList.add('show'), 10);
    bestPickShown = true;
}

function closeBestPick() {
    const overlay = document.getElementById('bestPickOverlay');
    if (overlay) {
        overlay.classList.remove('show');
        setTimeout(() => overlay.style.display = 'none', 300);
    }
}

// Trigger best pick analysis after stocks load
function triggerBestPickAnalysis() {
    // Wait 3 seconds after data loads to show popup
    setTimeout(() => {
        const stocks = state.stockData;
        if (stocks && stocks.length > 0) {
            const bestStock = findBestPick(stocks);
            if (bestStock) {
                showBestPickPopup(bestStock);
            }
        }
    }, 3000);
}

// ===== Pre-Market Analysis Functions =====

let preMarketDataLoaded = false;

async function loadPreMarketAnalysis() {
    try {
        const moodEl = document.getElementById('overallMood');
        if (moodEl) {
            moodEl.innerHTML = '<span class="mood-icon">⏳</span><span class="mood-text">Analyzing 200+ Stocks & Global Markets... (takes ~60s)</span>';
            moodEl.className = 'mood-banner loading';
        }

        const response = await fetch(`${CONFIG.API_BASE_URL}/pre-market-analysis`, {
            signal: AbortSignal.timeout(120000) // 2 minutes timeout for 200 stocks
        });

        if (!response.ok) throw new Error('Failed to fetch pre-market data');

        const data = await response.json();

        // Render all sections
        renderOverallMood(data.overall_mood);
        renderGlobalMarkets(data.global_markets);
        renderNewsSentiment(data.news);
        renderTopPicks(data.top_picks);

        preMarketDataLoaded = true;
    } catch (error) {
        console.error('Pre-market analysis error:', error);
        // Show error state
        const moodEl = document.getElementById('overallMood');
        if (moodEl) {
            moodEl.innerHTML = '<span class="mood-icon">⚠️</span><span class="mood-text">Could not fetch data. Click refresh to try again.</span>';
            moodEl.className = 'mood-banner error';
        }
    }
}

function renderOverallMood(mood) {
    const moodEl = document.getElementById('overallMood');
    if (!moodEl || !mood) return;

    const moodClass = mood.mood.toLowerCase();
    moodEl.innerHTML = `
        <span class="mood-icon">${mood.icon}</span>
        <span class="mood-text"><strong>${mood.mood}</strong> - ${mood.message}</span>
    `;
    moodEl.className = `mood-banner ${moodClass}`;
}

function renderGlobalMarkets(globalData) {
    const container = document.getElementById('globalMarketsGrid');
    if (!container || !globalData) return;

    const markets = globalData.data || [];

    container.innerHTML = markets.map(market => `
        <div class="market-card ${market.is_positive ? 'positive' : 'negative'}">
            <div class="market-name">${market.name}</div>
            <div class="market-price">${market.price.toLocaleString()}</div>
            <div class="market-change ${market.is_positive ? 'up' : 'down'}">
                ${market.is_positive ? '▲' : '▼'} ${Math.abs(market.change_pct).toFixed(2)}%
            </div>
        </div>
    `).join('');
}

function renderNewsSentiment(newsData) {
    const summaryEl = document.getElementById('newsSentimentSummary');
    const listEl = document.getElementById('newsList');

    if (!newsData) return;

    // Render summary
    if (summaryEl && newsData.sentiment) {
        const s = newsData.sentiment;
        const icon = s.mood === 'BULLISH' ? '🟢' : s.mood === 'BEARISH' ? '🔴' : '🟡';
        summaryEl.innerHTML = `
            <span class="sentiment-icon">${icon}</span>
            <span class="sentiment-text">
                <strong>${s.mood}</strong> - 
                ${s.bullish_count} positive, ${s.bearish_count} negative, ${s.neutral_count} neutral
                (Score: ${s.score}/10)
            </span>
        `;
        summaryEl.className = `news-sentiment-summary ${s.mood.toLowerCase()}`;
    }

    // Render news list
    if (listEl && newsData.headlines) {
        listEl.innerHTML = newsData.headlines.slice(0, 6).map(news => `
            <div class="news-card ${news.is_bullish === true ? 'bullish' : news.is_bullish === false ? 'bearish' : 'neutral'}">
                <span class="news-sentiment-tag">${news.is_bullish === true ? '🟢' : news.is_bullish === false ? '🔴' : '🟡'}</span>
                <span class="news-title">${news.title}</span>
                <span class="news-source">${news.source}</span>
            </div>
        `).join('');
    }
}

function renderTopPicks(picks) {
    const container = document.getElementById('topPicksList');
    if (!container || !picks) return;

    container.innerHTML = picks.map((pick, index) => `
        <div class="pick-card">
            <div class="pick-rank">#${index + 1}</div>
            <div class="pick-info">
                <div class="pick-header">
                    <span class="pick-symbol">${pick.symbol}</span>
                    <span class="pick-rec ${pick.recommendation.toLowerCase()}">${pick.recommendation}</span>
                </div>
                <div class="pick-name">${pick.name}</div>
                <div class="pick-levels">
                    <span class="entry">Entry: ₹${formatNumber(pick.entry)}</span>
                    <span class="target">Target: ₹${formatNumber(pick.target)}</span>
                    <span class="stoploss">SL: ₹${formatNumber(pick.stoploss)}</span>
                </div>
                <div class="pick-reasons">
                    ${pick.reasons.map(r => `<span class="reason-tag">✓ ${r}</span>`).join('')}
                </div>
            </div>
            <div class="pick-score">${pick.score}/10</div>
        </div>
    `).join('');
}

// Load pre-market data when tab is clicked
document.addEventListener('DOMContentLoaded', () => {
    // Add listener for pre-market tab
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            if (tab.dataset.tab === 'pre-market' && !preMarketDataLoaded) {
                loadPreMarketAnalysis();
            }
        });
    });
});

// ===== LIVE STOCK PRICE TIMER (2-second refresh) =====
let livePriceTimer = null;
let activeStockSymbols = new Set();

function startLivePriceUpdates() {
    // Only run on Stocks tab
    if (state.currentTab !== 'stocks') {
        stopLivePriceUpdates();
        return;
    }

    // Find all visible stock cards
    const stockCards = document.querySelectorAll('.stock-card-wrapper[data-symbol]');
    activeStockSymbols.clear();
    stockCards.forEach(card => {
        const symbol = card.dataset.symbol;
        if (symbol) activeStockSymbols.add(symbol);
    });

    // Start the 2-second timer
    if (!livePriceTimer && activeStockSymbols.size > 0) {
        livePriceTimer = setInterval(updateLivePrices, 2000);
        console.log(`🔴 LIVE: Started 2s price updates for ${activeStockSymbols.size} stocks`);
    }
}

function stopLivePriceUpdates() {
    if (livePriceTimer) {
        clearInterval(livePriceTimer);
        livePriceTimer = null;
        console.log('⚪ LIVE: Stopped price updates');
    }
}

async function updateLivePrices() {
    // Only update first 5 visible stocks (to avoid API overload)
    const symbolsToUpdate = Array.from(activeStockSymbols).slice(0, 5);

    for (const symbol of symbolsToUpdate) {
        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/stock-price/${symbol}`);
            if (response.ok) {
                const data = await response.json();

                // Update price element
                const priceEl = document.getElementById(`price-${symbol}`);
                if (priceEl) {
                    priceEl.textContent = `₹${formatNumber(data.price)}`;
                    priceEl.classList.add('price-flash');
                    setTimeout(() => priceEl.classList.remove('price-flash'), 300);
                }

                // Update change element
                const changeEl = document.getElementById(`change-${symbol}`);
                if (changeEl) {
                    const isPositive = data.change >= 0;
                    changeEl.textContent = `${isPositive ? '+' : ''}${data.change_pct.toFixed(2)}%`;
                    changeEl.className = `stock-change ${isPositive ? 'positive' : 'negative'}`;
                }
            }
        } catch (e) {
            // Silent fail - don't break the loop
        }
    }
}

// Hook into tab changes to start/stop timer
const originalSwitchTab = switchTab;
switchTab = function (tabId) {
    originalSwitchTab(tabId);
    if (tabId === 'stocks') {
        setTimeout(startLivePriceUpdates, 500); // Wait for cards to render
    } else {
        stopLivePriceUpdates();
    }
};

// Also start when stocks load
const originalUpdateStockList = updateStockList;
updateStockList = function (stocks) {
    originalUpdateStockList(stocks);
    setTimeout(startLivePriceUpdates, 500);
};
