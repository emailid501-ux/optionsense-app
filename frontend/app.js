/**
 * OptionSense - Frontend Application
 * Real-time sentiment analysis for intraday option traders
 */

// Configuration
const CONFIG = {
    API_BASE_URL: 'http://localhost:8000',
    REFRESH_INTERVAL: 180000, // 3 minutes in milliseconds
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

async function loadData() {
    if (state.isLoading) return;

    try {
        showLoading(true);

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
    if (elements.searchBtn) {
        elements.searchBtn.addEventListener('click', searchStock);
    }
    if (elements.stockSearch) {
        elements.stockSearch.addEventListener('keyup', (e) => {
            if (e.key === 'Enter') {
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
        const data = await fetchStockScreener(state.currentStockFilter);
        state.stockData = data;
        updateStockSummary(data.summary);
        updateStockList(data.stocks);
    } catch (error) {
        console.error('Error fetching stock data:', error);
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

    if (!state.stockData || !state.stockData.stocks) {
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

    container.innerHTML = stocks.map(stock => createStockCard(stock)).join('');
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
        <div class="stock-card-wrapper">
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
                    <span class="stock-price">₹${formatNumber(stock.price)}</span>
                    <span class="stock-change ${isPositive ? 'positive' : 'negative'}">
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
            ${optionStrategyHtml}
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
