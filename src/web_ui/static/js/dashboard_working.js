// WORKING Professional Trading Dashboard JavaScript
// Fixed to actually make API calls and show live data

console.log('🚀 Loading WORKING dashboard...');

// Global variables
let userWatchlist = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'ADA/USDT', 'MATIC/USDT'];
let updateIntervals = [];

// Initialize when DOM loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('📊 DOM loaded, initializing dashboard...');
    initializeDashboard();
});

async function initializeDashboard() {
    console.log('🔄 Starting dashboard initialization...');
    
    // Load initial data immediately
    await loadInitialData();
    
    // Start auto-refresh intervals
    startAutoRefresh();
    
    // Set up event listeners
    setupEventListeners();
    
    console.log('✅ Dashboard initialization complete!');
}

async function loadInitialData() {
    console.log('📈 Loading all initial data...');
    
    // Load all sections in parallel
    await Promise.all([
        updateWatchlistDisplay(),
        updateMarketHeatmap(),
        updateTopMetrics(),
        updateFearGreedIndex(),
        updatePortfolioMetrics()
    ]);
    
    console.log('✅ Initial data loaded successfully');
}

// Update watchlist with live prices
async function updateWatchlistDisplay() {
    console.log('💰 Updating watchlist...');
    const watchlistContainer = document.getElementById('watchlist');
    if (!watchlistContainer) {
        console.log('⚠️ Watchlist container not found');
        return;
    }
    
    try {
        watchlistContainer.innerHTML = '<div class="text-xs text-gray-400 p-2">⟳ Loading prices...</div>';
        
        const pricePromises = userWatchlist.map(async (symbol) => {
            try {
                const response = await fetch(`/api/price/${symbol}?t=${Date.now()}`);
                const data = await response.json();
                
                return {
                    symbol: symbol,
                    price: data.price || 0,
                    change_24h_percent: data.change_24h_percent || data.change_24h || 0,
                    loaded: response.ok && data.price
                };
            } catch (error) {
                console.log(`❌ Failed to load ${symbol}:`, error);
                return { symbol: symbol, price: 0, change_24h_percent: 0, loaded: false };
            }
        });
        
        const prices = await Promise.all(pricePromises);
        console.log('💎 Loaded watchlist prices:', prices);
        
        watchlistContainer.innerHTML = prices.map(item => {
            const change = item.change_24h_percent || 0;
            const changeClass = change >= 0 ? 'text-green-400' : 'text-red-400';
            const changeSign = change >= 0 ? '+' : '';
            const priceDisplay = item.loaded ? `$${item.price.toLocaleString()}` : 'Error';
            const changeDisplay = item.loaded ? `${changeSign}${change.toFixed(2)}%` : '--';
            
            return `
                <div class="flex justify-between items-center p-3 bg-slate-800 rounded-lg hover:bg-slate-700 transition-colors">
                    <div>
                        <div class="font-medium text-slate-200">${item.symbol.replace('/USDT', '')}</div>
                        <div class="text-xs text-slate-400">${item.symbol}</div>
                    </div>
                    <div class="text-right">
                        <div class="font-bold text-slate-100">${priceDisplay}</div>
                        <div class="text-xs ${changeClass}">${changeDisplay}</div>
                    </div>
                    <button onclick="removeFromWatchlist('${item.symbol}')" 
                            class="ml-2 text-slate-400 hover:text-red-400 text-xs">×</button>
                </div>
            `;
        }).join('');
        
    } catch (error) {
        console.error('❌ Error updating watchlist:', error);
        watchlistContainer.innerHTML = '<div class="text-xs text-red-400 p-2">Failed to load watchlist</div>';
    }
}

// Update market heatmap
async function updateMarketHeatmap() {
    console.log('🔥 Updating market heatmap...');
    const heatmapContainer = document.getElementById('marketHeatMap');
    if (!heatmapContainer) {
        console.log('⚠️ Heatmap container not found');
        return;
    }
    
    try {
        const response = await fetch(`/api/market/heatmap?t=${Date.now()}`);
        const data = await response.json();
        
        if (data.heatmap && data.heatmap.length > 0) {
            console.log('🔥 Heat map updated with', data.heatmap.length, 'real prices');
            
            heatmapContainer.innerHTML = data.heatmap.slice(0, 6).map(item => {
                const changeClass = item.change >= 0 ? 'text-green-400' : 'text-red-400';
                const changeSign = item.change >= 0 ? '+' : '';
                
                return `
                    <div class="bg-slate-800 p-4 rounded-lg">
                        <div class="font-semibold text-slate-200">${item.symbol}</div>
                        <div class="text-lg font-bold text-slate-100">$${item.price.toLocaleString()}</div>
                        <div class="text-sm ${changeClass}">${changeSign}${item.change.toFixed(2)}%</div>
                    </div>
                `;
            }).join('');
        } else {
            heatmapContainer.innerHTML = '<div class="text-slate-400">No heatmap data</div>';
        }
    } catch (error) {
        console.error('❌ Error updating heatmap:', error);
        heatmapContainer.innerHTML = '<div class="text-red-400">Failed to load heatmap</div>';
    }
}

// Update top metrics
async function updateTopMetrics() {
    console.log('📊 Updating top metrics...');
    
    try {
        const response = await fetch(`/api/top/metrics?t=${Date.now()}`);
        const data = await response.json();
        
        console.log('💱 Price data updated');
        
        // Update various metric displays
        const elements = {
            'btcPrice': data.btc_price,
            'activeTraders': data.active_traders,
            'totalVolume': data.total_volume_24h
        };
        
        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element && value) {
                if (id === 'btcPrice') {
                    element.textContent = `$${value.toLocaleString()}`;
                } else if (id === 'totalVolume') {
                    element.textContent = `$${(value / 1e9).toFixed(1)}B`;
                } else {
                    element.textContent = value.toLocaleString();
                }
            }
        });
        
    } catch (error) {
        console.error('❌ Error updating top metrics:', error);
    }
}

// Update Fear & Greed Index
async function updateFearGreedIndex() {
    console.log('😱 Updating Fear & Greed...');
    const fearGreedContainer = document.getElementById('fearGreedValue');
    
    try {
        const response = await fetch(`/api/fear-greed?t=${Date.now()}`);
        const data = await response.json();
        
        if (fearGreedContainer) {
            fearGreedContainer.innerHTML = `
                <div class="text-center">
                    <div class="text-3xl font-bold mb-2">${data.value}</div>
                    <div class="text-lg text-slate-300">${data.classification}</div>
                </div>
            `;
        }
        
        console.log('😱 Fear & Greed updated:', data.value, data.classification);
    } catch (error) {
        console.error('❌ Error updating Fear & Greed:', error);
        if (fearGreedContainer) {
            fearGreedContainer.innerHTML = '<div class="text-red-400">Failed to load</div>';
        }
    }
}

// Update portfolio metrics  
async function updatePortfolioMetrics() {
    console.log('💼 Updating portfolio...');
    
    try {
        const response = await fetch(`/api/portfolio/summary?t=${Date.now()}`);
        const data = await response.json();
        
        console.log('📊 Portfolio metrics updated');
        
        // Update portfolio display elements
        const elements = {
            'portfolioValue': data.total_value,
            'portfolioDayChange': data.day_change,
            'portfolioPositions': data.positions
        };
        
        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                if (id === 'portfolioValue') {
                    element.textContent = typeof value === 'number' ? `$${value.toLocaleString()}` : value;
                } else if (id === 'portfolioDayChange') {
                    element.textContent = typeof value === 'number' ? `$${value.toFixed(2)}` : value;
                    if (typeof value === 'number') {
                        element.className = value >= 0 ? 'text-green-400' : 'text-red-400';
                    }
                } else {
                    element.textContent = value;
                }
            }
        });
        
    } catch (error) {
        console.error('❌ Error updating portfolio:', error);
    }
}

// Start auto-refresh intervals
function startAutoRefresh() {
    console.log('⏰ Starting auto-refresh...');
    
    // Clear existing intervals
    updateIntervals.forEach(interval => clearInterval(interval));
    updateIntervals = [];
    
    // Watchlist every 15 seconds
    updateIntervals.push(setInterval(updateWatchlistDisplay, 15000));
    
    // Heatmap every 30 seconds  
    updateIntervals.push(setInterval(updateMarketHeatmap, 30000));
    
    // Top metrics every 30 seconds
    updateIntervals.push(setInterval(updateTopMetrics, 30000));
    
    // Fear & Greed every 60 seconds
    updateIntervals.push(setInterval(updateFearGreedIndex, 60000));
    
    // Portfolio every 30 seconds
    updateIntervals.push(setInterval(updatePortfolioMetrics, 30000));
    
    console.log('✅ Auto-refresh started');
}

// Setup event listeners
function setupEventListeners() {
    // Add refresh button if it exists
    const refreshBtn = document.getElementById('refreshAll');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', loadInitialData);
    }
}

// Watchlist management
function removeFromWatchlist(symbol) {
    userWatchlist = userWatchlist.filter(s => s !== symbol);
    localStorage.setItem('userWatchlist', JSON.stringify(userWatchlist));
    updateWatchlistDisplay();
    console.log(`🗑️ Removed ${symbol} from watchlist`);
}

function addToWatchlist() {
    // This can be called from the UI
    console.log('➕ Adding to watchlist functionality available');
}

// Show notifications (if notification container exists)
function showNotification(message, type = 'info') {
    console.log(`📢 ${type.toUpperCase()}: ${message}`);
}

console.log('✅ Dashboard script loaded and ready!');