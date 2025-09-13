// Professional Trading Dashboard JavaScript
// Handles real-time data updates and TradingView charts

// Toast notifications
function ensureToastContainer() {
    let container = document.getElementById('toastContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'fixed top-4 right-4 z-50 space-y-2';
        document.body.appendChild(container);
    }
    return container;
}

function showToast(message, type = 'info') {
    try {
        const container = ensureToastContainer();
        const toast = document.createElement('div');
        const base = 'px-4 py-3 rounded-lg shadow-lg text-sm border';
        const colors = {
            info: 'bg-slate-800 text-slate-100 border-slate-700',
            success: 'bg-emerald-900 text-emerald-100 border-emerald-700',
            error: 'bg-red-900 text-red-100 border-red-700',
            warning: 'bg-yellow-900 text-yellow-100 border-yellow-700'
        };
        toast.className = `${base} ${colors[type] || colors.info}`;
        toast.textContent = message;
        container.appendChild(toast);
        setTimeout(() => {
            toast.style.transition = 'opacity 300ms ease';
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 320);
        }, 3000);
    } catch (_) {}
}

// Lightweight loading helpers
function setSectionLoading(sectionEl, isLoading) {
    if (!sectionEl) return;
    if (isLoading) {
        sectionEl.classList.add('opacity-70');
        sectionEl.classList.add('pointer-events-none');
    } else {
        sectionEl.classList.remove('opacity-70');
        sectionEl.classList.remove('pointer-events-none');
    }
}

class TradingDashboard {
    constructor() {
        this.currentSymbol = 'BTC/USDT';
        this.currentTimeframe = '1h';
        this.autoRefresh = true;
        this.refreshInterval = null;
        this.lastUpdate = null;
        
        this.init();
    }
    
    init() {
        console.log('🚀 Initializing Professional Trading Dashboard');
        this.setupEventListeners();
        this.startAutoRefresh();
        this.loadInitialData();
    }
    
    async loadInitialData() {
        console.log('📊 Loading initial dashboard data');
        
        // Initialize TradingView chart first
        setTimeout(() => {
            this.initializeTradingViewChart();
        }, 1000);
        
        await this.updateAllData();
    }
    
    initializeTradingViewChart() {
        try {
            console.log('🔍 DEBUG: initializeTradingViewChart called');
            
            // Check if TradingView is available
            if (typeof TradingView === 'undefined') {
                console.error('❌ TradingView library not loaded!');
                this.showChartError('TradingView library not loaded');
                return;
            }
            
            // Convert pair format for TradingView (BTC/USDT -> BTCUSDT)
            const tvSymbol = this.currentSymbol.replace('/', '');
            
            // Convert timeframe format for TradingView
            const tvInterval = this.convertTimeframeForTradingView(this.currentTimeframe);
            
            console.log(`📊 Initializing TradingView chart: ${tvSymbol} on ${tvInterval}`);
            
            // Clear existing chart
            const chartContainer = document.getElementById('tradingview_widget');
            if (!chartContainer) {
                console.error('❌ TradingView container not found!');
                return;
            }
            
            console.log('🔍 DEBUG: Container found, clearing content');
            chartContainer.innerHTML = '';
            
            console.log('🔍 DEBUG: Creating TradingView widget...');
            
            // Create TradingView widget with proper candlestick configuration
            new TradingView.widget({
                "autosize": true,
                "symbol": `BINANCE:${tvSymbol}`,
                "interval": tvInterval,
                "timezone": "Etc/UTC",
                "theme": "dark",
                "style": "1", // Candlestick style
                "locale": "en",
                "enable_publishing": false,
                "backgroundColor": "rgba(30, 41, 59, 1)",
                "gridColor": "rgba(51, 65, 85, 1)",
                "hide_top_toolbar": false,
                "hide_legend": false,
                "save_image": false,
                "container_id": "tradingview_widget",
                "studies": [
                    "Volume@tv-basicstudies",
                    "RSI@tv-basicstudies",
                    "MACD@tv-basicstudies",
                    "BB@tv-basicstudies" // Bollinger Bands
                ],
                "toolbar_bg": "#1e293b",
                "loading_screen": {
                    "backgroundColor": "#1e293b",
                    "foregroundColor": "#667eea"
                },
                "overrides": {
                    // Candlestick colors
                    "mainSeriesProperties.candleStyle.upColor": "#10b981",
                    "mainSeriesProperties.candleStyle.downColor": "#ef4444",
                    "mainSeriesProperties.candleStyle.borderUpColor": "#10b981",
                    "mainSeriesProperties.candleStyle.borderDownColor": "#ef4444",
                    "mainSeriesProperties.candleStyle.wickUpColor": "#10b981",
                    "mainSeriesProperties.candleStyle.wickDownColor": "#ef4444",
                    // Volume colors
                    "volumePaneSize": "medium",
                    "scalesProperties.backgroundColor": "#1e293b"
                }
            });
            
            console.log(`✅ TradingView candlestick chart initialized for ${tvSymbol}`);
            
        } catch (error) {
            console.error('❌ Error initializing TradingView chart:', error);
            this.showChartError(error.message);
        }
    }
    
    updateTradingViewChart() {
        try {
            // Clear existing chart
            const chartContainer = document.getElementById('tradingview_widget');
            if (chartContainer) {
                chartContainer.innerHTML = '';
                
                // Small delay to ensure container is cleared
                setTimeout(() => {
                    this.initializeTradingViewChart();
                }, 100);
            }
        } catch (error) {
            console.error('❌ Error updating TradingView chart:', error);
            this.showChartError(error.message);
        }
    }
    
    convertTimeframeForTradingView(timeframe) {
        const timeframeMap = {
            '1m': '1',
            '5m': '5',
            '15m': '15',
            '1h': '60',
            '4h': '240',
            '1d': '1D',
            '1w': '1W'
        };
        
        return timeframeMap[timeframe] || '60';
    }
    
    showChartError(errorMessage) {
        const chartContainer = document.getElementById('tradingview_widget');
        if (chartContainer) {
            chartContainer.innerHTML = `
                <div class="flex items-center justify-center h-full bg-slate-800 rounded-xl">
                    <div class="text-center text-gray-400">
                        <i class="fas fa-exclamation-triangle text-4xl mb-3"></i>
                        <div class="font-medium text-lg">Chart Error</div>
                        <div class="text-sm mt-1">${errorMessage}</div>
                        <button onclick="dashboard.updateTradingViewChart()" class="mt-4 px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg text-sm">
                            <i class="fas fa-redo mr-2"></i>Retry
                        </button>
                    </div>
                </div>
            `;
        }
    }
    
    setupEventListeners() {
        // Symbol input handling
        const symbolInput = document.getElementById('symbolInput');
        if (symbolInput) {
            symbolInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.analyzeSymbol();
                }
            });
        }
        
        // Auto-refresh toggle
        const autoRefreshBtn = document.getElementById('autoRefreshBtn');
        if (autoRefreshBtn) {
            autoRefreshBtn.addEventListener('click', () => {
                this.toggleAutoRefresh();
            });
        }
    }
    
    async loadInitialData() {
        console.log('📊 Loading initial dashboard data');
        
        // Initialize TradingView chart first
        setTimeout(() => {
            this.initializeTradingViewChart();
        }, 1000);
        
        await this.updateAllData();
    }
    
    async updateAllData() {
        const pageRoot = document.querySelector('.max-w-7xl') || document.body;
        try {
            setSectionLoading(pageRoot, true);
            console.log(`🔄 Updating data for ${this.currentSymbol}`);
            
            // Update all dashboard sections with real data
            await Promise.all([
                this.updateMarketData(),
                this.updateActiveTrades(),
                this.updateSmartMoneyAnalysis(),
                this.updatePatternAnalysis(),
                this.updateKeyMetrics(),
                this.updateRecentSignals(),
                this.updateSmartMoneyScreener(),
                this.updateTradeLogic(),
                this.updateSocialSentiment()
            ]);
            
            this.updateLastUpdateTime();
            console.log('✅ Dashboard data updated successfully');
            
        } catch (error) {
            console.error('❌ Error updating dashboard data:', error);
            showToast('Failed to update dashboard data', 'error');
        } finally {
            setSectionLoading(pageRoot, false);
        }
    }
    
    async updateSocialSentiment() {
        try {
            const response = await fetch(`/api/social-sentiment/${encodeURIComponent(this.currentSymbol)}`);
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Update sentiment bars
            const twitterSentiment = data.twitter_sentiment * 100;
            const redditSentiment = data.reddit_sentiment * 100;
            const overallSentiment = data.overall_sentiment * 100;
            
            document.getElementById('twitterSentiment').textContent = `${twitterSentiment.toFixed(1)}%`;
            document.getElementById('twitterSentimentBar').style.width = `${twitterSentiment}%`;
            
            document.getElementById('redditSentiment').textContent = `${redditSentiment.toFixed(1)}%`;
            document.getElementById('redditSentimentBar').style.width = `${redditSentiment}%`;
            
            document.getElementById('overallSentiment').textContent = `${overallSentiment.toFixed(1)}%`;
            document.getElementById('overallSentimentBar').style.width = `${overallSentiment}%`;
            
            // Update followed traders
            this.updateFollowedTraders();
            
            console.log('👥 Social sentiment updated');
            
        } catch (error) {
            console.error('Error updating social sentiment:', error);
            showToast('Failed to load social sentiment', 'warning');
        }
    }
    
    async updateFollowedTraders() {
        try {
            const response = await fetch('/api/followed-traders');
            const traders = await response.json();
            
            const container = document.getElementById('followedTraders');
            if (!container) return;
            
            if (traders.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-user-plus"></i>
                        <h3>No Traders Followed</h3>
                        <p>Add traders to follow their sentiment and signals</p>
                    </div>
                `;
                return;
            }
            
            const tradersHtml = traders.map(trader => `
                <div class="bg-slate-800 rounded-lg p-3 border border-slate-700">
                    <div class="flex items-center justify-between mb-2">
                        <div class="flex items-center gap-2">
                            <div class="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white text-sm font-bold">
                                ${trader.username.charAt(0)}
                            </div>
                            <div>
                                <p class="font-medium text-white text-sm">${trader.username}</p>
                                <p class="text-xs text-gray-400">${trader.platform} • ${(trader.followers / 1000).toFixed(0)}K followers</p>
                            </div>
                        </div>
                        ${trader.verified ? '<i class="fas fa-check-circle text-blue-400 text-sm"></i>' : ''}
                    </div>
                    
                    <div class="grid grid-cols-2 gap-2 text-xs mb-2">
                        <div>
                            <span class="text-gray-400">Win Rate:</span>
                            <span class="text-white font-medium">${(trader.win_rate * 100).toFixed(1)}%</span>
                        </div>
                        <div>
                            <span class="text-gray-400">Signals:</span>
                            <span class="text-white font-medium">${trader.total_signals}</span>
                        </div>
                    </div>
                    
                    ${trader.recent_signal ? `
                        <div class="border-t border-slate-700 pt-2">
                            <div class="flex items-center justify-between">
                                <span class="text-xs text-gray-400">Latest:</span>
                                <span class="px-2 py-1 text-xs rounded-full ${
                                    trader.recent_signal.signal === 'BUY' ? 'bg-green-900 text-green-300' : 
                                    trader.recent_signal.signal === 'SELL' ? 'bg-red-900 text-red-300' : 
                                    'bg-yellow-900 text-yellow-300'
                                }">${trader.recent_signal.signal}</span>
                            </div>
                            <p class="text-xs text-gray-300 mt-1">${trader.recent_signal.pair} - ${trader.recent_signal.reasoning}</p>
                        </div>
                    ` : ''}
                </div>
            `).join('');
            
            container.innerHTML = tradersHtml;
            console.log('⭐ Followed traders updated');
            
        } catch (error) {
            console.error('Error updating followed traders:', error);
            showToast('Failed to load followed traders', 'warning');
        }
    }
    
    async updateRecentSignals() {
        try {
            const response = await fetch('/api/recent-signals');
            const signals = await response.json();
            
            const container = document.getElementById('recentSignals');
            if (!container) return;
            
            if (signals.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-bolt"></i>
                        <h3>No Recent Signals</h3>
                        <p>Waiting for strategy signals to generate</p>
                    </div>
                `;
                return;
            }
            
            const signalsHtml = signals.slice(0, 6).map(signal => `
                <div class="bg-slate-800 rounded-lg p-3 border border-slate-700 hover:border-slate-600 transition-all">
                    <div class="flex items-center justify-between mb-2">
                        <div class="flex items-center gap-2">
                            <span class="font-medium text-white">${signal.pair}</span>
                            <span class="px-2 py-1 text-xs rounded-full ${
                                signal.signal_type === 'BUY' ? 'bg-green-900 text-green-300' : 
                                signal.signal_type === 'SELL' ? 'bg-red-900 text-red-300' : 
                                'bg-yellow-900 text-yellow-300'
                            }">${signal.signal_type}</span>
                        </div>
                        <span class="text-xs text-gray-400">${new Date(signal.timestamp).toLocaleTimeString()}</span>
                    </div>
                    <div class="flex items-center justify-between text-sm">
                        <span class="text-gray-400">Score: ${signal.composite_score.toFixed(3)}</span>
                        <span class="text-gray-400">${signal.confidence.toFixed(1)}%</span>
                    </div>
                    <p class="text-xs text-gray-300 mt-2 truncate">${signal.reasoning}</p>
                </div>
            `).join('');
            
            container.innerHTML = signalsHtml;
            console.log('📡 Recent signals updated');
            
        } catch (error) {
            console.error('Error updating recent signals:', error);
            showToast('Failed to load recent signals', 'warning');
        }
    }
    
    async updateSmartMoneyScreener() {
        try {
            const response = await fetch('/api/smart-money-screener');
            const opportunities = await response.json();
            
            const container = document.getElementById('smartMoneyScreener');
            if (!container) return;
            
            if (opportunities.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-gem"></i>
                        <h3>Smart Money Opportunities</h3>
                        <p>Click "Run Screener" to discover top trading opportunities</p>
                    </div>
                `;
                return;
            }
            
            const opportunitiesHtml = opportunities.slice(0, 5).map(opp => `
                <div class="bg-slate-800 rounded-xl p-4 border border-slate-700 hover:border-slate-600 transition-all">
                    <div class="flex items-center justify-between mb-3">
                        <div class="flex items-center gap-3">
                            <span class="font-bold text-white">${opp.pair}</span>
                            <span class="px-2 py-1 text-xs rounded-full ${
                                opp.signal === 'ACCUMULATION' ? 'bg-green-900 text-green-300' : 
                                opp.signal === 'DISTRIBUTION' ? 'bg-red-900 text-red-300' : 
                                'bg-gray-900 text-gray-300'
                            }">${opp.signal}</span>
                        </div>
                        <span class="px-2 py-1 text-xs rounded-full ${
                            opp.recommendation === 'STRONG_BUY' ? 'bg-green-900 text-green-300' : 
                            opp.recommendation === 'BUY' ? 'bg-blue-900 text-blue-300' : 
                            'bg-gray-900 text-gray-300'
                        }">${opp.recommendation}</span>
                    </div>
                    
                    <div class="grid grid-cols-2 gap-3 text-sm">
                        <div>
                            <p class="text-gray-400">Whale Activity</p>
                            <p class="font-medium text-white">${(opp.whale_activity * 100).toFixed(1)}%</p>
                        </div>
                        <div>
                            <p class="text-gray-400">Confidence</p>
                            <p class="font-medium text-white">${(opp.confidence * 100).toFixed(1)}%</p>
                        </div>
                        <div>
                            <p class="text-gray-400">Large TXs</p>
                            <p class="font-medium text-white">${opp.large_transactions}</p>
                        </div>
                        <div>
                            <p class="text-gray-400">Score</p>
                            <p class="font-medium text-white">${opp.score.toFixed(3)}</p>
                        </div>
                    </div>
                    
                    <div class="mt-3">
                        <div class="w-full bg-slate-700 rounded-full h-2">
                            <div class="bg-gradient-to-r from-blue-400 to-purple-600 h-2 rounded-full" 
                                 style="width: ${opp.score * 100}%"></div>
                        </div>
                    </div>
                </div>
            `).join('');
            
            container.innerHTML = opportunitiesHtml;
            console.log('💎 Smart money screener updated');
            
        } catch (error) {
            console.error('Error updating smart money screener:', error);
            showToast('Failed to load smart money screener', 'warning');
        }
    }
    
    async updateTradeLogic() {
        try {
            const response = await fetch(`/api/trade-logic/${encodeURIComponent(this.currentSymbol)}`);
            const logic = await response.json();
            
            const container = document.getElementById('tradeLogic');
            if (!container) return;
            
            if (logic.error) {
                container.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-brain"></i>
                        <h3>Loading Trade Logic</h3>
                        <p>Analyzing decision-making process</p>
                    </div>
                `;
                return;
            }
            
            const logicHtml = `
                <div class="space-y-4">
                    <div class="bg-slate-800 rounded-xl p-4">
                        <h4 class="font-medium text-white mb-3 flex items-center gap-2">
                            <i class="fas fa-chart-line text-blue-400"></i>
                            Technical Analysis
                        </h4>
                        <div class="space-y-2">
                            <div class="flex justify-between">
                                <span class="text-gray-400">Score:</span>
                                <span class="text-white font-medium">${logic.decision_process.technical_analysis.score.toFixed(3)}</span>
                            </div>
                            ${logic.decision_process.technical_analysis.reasoning.map(reason => `
                                <div class="flex items-start gap-2">
                                    <i class="fas fa-check-circle text-green-400 text-sm mt-0.5"></i>
                                    <span class="text-sm text-gray-300">${reason}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    
                    <div class="bg-slate-800 rounded-xl p-4">
                        <h4 class="font-medium text-white mb-3 flex items-center gap-2">
                            <i class="fas fa-shield-alt text-red-400"></i>
                            Risk Assessment
                        </h4>
                        <div class="grid grid-cols-2 gap-3 text-sm">
                            <div>
                                <p class="text-gray-400">Risk Level</p>
                                <p class="font-medium ${
                                    logic.decision_process.risk_assessment.risk_level === 'LOW' ? 'text-green-400' : 
                                    logic.decision_process.risk_assessment.risk_level === 'MEDIUM' ? 'text-yellow-400' : 
                                    'text-red-400'
                                }">${logic.decision_process.risk_assessment.risk_level}</p>
                            </div>
                            <div>
                                <p class="text-gray-400">Position Size</p>
                                <p class="font-medium text-white">${(logic.decision_process.risk_assessment.position_size * 100).toFixed(1)}%</p>
                            </div>
                        </div>
                        <div class="mt-2">
                            <p class="text-gray-400 text-sm">Stop Loss: ${logic.decision_process.risk_assessment.stop_loss}</p>
                        </div>
                    </div>
                    
                    <div class="bg-slate-800 rounded-xl p-4">
                        <h4 class="font-medium text-white mb-3 flex items-center gap-2">
                            <i class="fas fa-brain text-purple-400"></i>
                            Final Decision
                        </h4>
                        <div class="flex items-center justify-between">
                            <span class="px-3 py-2 rounded-full text-sm font-medium ${
                                logic.decision_process.final_decision === 'BUY' ? 'bg-green-900 text-green-300' : 
                                logic.decision_process.final_decision === 'SELL' ? 'bg-red-900 text-red-300' : 
                                'bg-gray-900 text-gray-300'
                            }">${logic.decision_process.final_decision}</span>
                            <div class="text-right">
                                <p class="text-sm text-gray-400">Confidence</p>
                                <p class="font-bold text-white">${logic.decision_process.confidence.toFixed(1)}%</p>
                            </div>
                        </div>
                        <div class="mt-3">
                            <div class="w-full bg-slate-700 rounded-full h-2">
                                <div class="bg-gradient-to-r from-purple-400 to-purple-600 h-2 rounded-full" 
                                     style="width: ${logic.decision_process.confidence}%"></div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            container.innerHTML = logicHtml;
            console.log('🧠 Trade logic updated');
            
        } catch (error) {
            console.error('Error updating trade logic:', error);
            showToast('Failed to load trade logic', 'warning');
        }
    }
    
    async updateMarketData() {
        try {
            const response = await fetch(`/api/market-data/${encodeURIComponent(this.currentSymbol)}`);
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Update price display
            this.updatePriceDisplay(data.price_data || {});
            
            // Update technical analysis
            this.updateTechnicalAnalysis(data.technical_analysis || {});
            
            // Update multi-signal score
            this.updateMultiSignalScore(data.multi_signal_score || {});
            
            // Update market data section
            this.updateMarketDataSection(data);
            
            // TradingView chart is already initialized - no need to render additional charts
            
            console.log('📈 Market data updated for', this.currentSymbol);
            
        } catch (error) {
            console.error('Error updating market data:', error);
            showToast('Failed to load market data', 'error');
            // TradingView chart will handle its own errors
        }
    }
    
    updateMarketDataSection(data) {
        const container = document.getElementById('marketData');
        if (!container) return;
        
        const marketDataHtml = `
            <div class="space-y-4">
                <div class="bg-slate-800 rounded-xl p-4">
                    <h4 class="font-medium text-white mb-3 flex items-center gap-2">
                        <i class="fas fa-chart-bar text-blue-400"></i>
                        Price Information
                    </h4>
                    <div class="grid grid-cols-2 gap-4 text-sm">
                        <div>
                            <p class="text-gray-400">Current Price</p>
                            <p class="font-bold text-white text-lg">$${data.price_data.current_price.toLocaleString('en-US', {
                                minimumFractionDigits: 2,
                                maximumFractionDigits: 6
                            })}</p>
                        </div>
                        <div>
                            <p class="text-gray-400">24h Change</p>
                            <p class="font-medium ${data.price_data.change_24h >= 0 ? 'text-green-400' : 'text-red-400'}">
                                ${data.price_data.change_24h >= 0 ? '+' : ''}${data.price_data.change_24h.toFixed(2)}%
                            </p>
                        </div>
                        <div>
                            <p class="text-gray-400">24h High</p>
                            <p class="font-medium text-white">$${data.price_data.high_24h.toLocaleString()}</p>
                        </div>
                        <div>
                            <p class="text-gray-400">24h Low</p>
                            <p class="font-medium text-white">$${data.price_data.low_24h.toLocaleString()}</p>
                        </div>
                    </div>
                </div>
                
                <div class="bg-slate-800 rounded-xl p-4">
                    <h4 class="font-medium text-white mb-3 flex items-center gap-2">
                        <i class="fas fa-cogs text-purple-400"></i>
                        Technical Indicators
                    </h4>
                    <div class="space-y-3">
                        <div class="flex justify-between items-center">
                            <span class="text-gray-400">RSI (14)</span>
                            <div class="flex items-center gap-2">
                                <span class="font-medium text-white">${data.technical_analysis.rsi}</span>
                                <div class="w-16 bg-slate-700 rounded-full h-2">
                                    <div class="bg-gradient-to-r from-red-400 via-yellow-400 to-green-400 h-2 rounded-full" 
                                         style="width: ${data.technical_analysis.rsi}%"></div>
                                </div>
                            </div>
                        </div>
                        <div class="flex justify-between items-center">
                            <span class="text-gray-400">MACD</span>
                            <span class="font-medium ${data.technical_analysis.macd >= 0 ? 'text-green-400' : 'text-red-400'}">
                                ${data.technical_analysis.macd.toFixed(4)}
                            </span>
                        </div>
                        <div class="flex justify-between items-center">
                            <span class="text-gray-400">Volume Ratio</span>
                            <span class="font-medium text-white">${data.technical_analysis.volume_ratio.toFixed(2)}x</span>
                        </div>
                        <div class="flex justify-between items-center">
                            <span class="text-gray-400">ATR %</span>
                            <span class="font-medium text-white">${data.technical_analysis.atr_percent.toFixed(2)}%</span>
                        </div>
                    </div>
                </div>
                
                <div class="bg-slate-800 rounded-xl p-4">
                    <h4 class="font-medium text-white mb-3 flex items-center gap-2">
                        <i class="fas fa-chart-pie text-green-400"></i>
                        Market Stats
                    </h4>
                    <div class="grid grid-cols-1 gap-3 text-sm">
                        <div class="flex justify-between">
                            <span class="text-gray-400">24h Volume</span>
                            <span class="font-medium text-white">$${(data.price_data.volume_24h / 1000000).toFixed(1)}M</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-400">Market Cap</span>
                            <span class="font-medium text-white">$${(data.price_data.market_cap / 1000000000).toFixed(1)}B</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-400">Technical Score</span>
                            <span class="font-medium ${data.technical_analysis.technical_score > 0.6 ? 'text-green-400' : data.technical_analysis.technical_score > 0.4 ? 'text-yellow-400' : 'text-red-400'}">
                                ${data.technical_analysis.technical_score.toFixed(3)}
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        container.innerHTML = marketDataHtml;
        console.log('📊 Market data section updated');
    }
    
    generateDemoChartData() {
        // Generate realistic demo chart data
        const now = new Date();
        const labels = [];
        const prices = [];
        const basePrice = this.currentSymbol.includes('BTC') ? 45000 : 
                         this.currentSymbol.includes('ETH') ? 2800 : 
                         this.currentSymbol.includes('SOL') ? 120 : 1.0;
        
        for (let i = 23; i >= 0; i--) {
            const time = new Date(now.getTime() - i * 60 * 60 * 1000);
            labels.push(time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }));
            
            // Generate realistic price movement
            const volatility = 0.02; // 2% volatility
            const randomChange = (Math.random() - 0.5) * volatility;
            const price = basePrice * (1 + randomChange + Math.sin(i * 0.1) * 0.01);
            prices.push(price);
        }
        
        return { labels, prices };
    }
    
    // TradingView chart is handled by initializeTradingViewChart() - no need for renderPriceChart   
 
    updatePriceDisplay(priceData) {
        // Update current price with proper formatting
        const currentPriceEl = document.getElementById('currentPrice');
        if (currentPriceEl && priceData.current_price) {
            currentPriceEl.textContent = `$${priceData.current_price.toLocaleString('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 4
            })}`;
        }
        
        // Update price change with color coding
        const priceChangeEl = document.getElementById('priceChange');
        if (priceChangeEl && priceData.change_24h !== undefined) {
            const change = priceData.change_24h;
            priceChangeEl.textContent = `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`;
            priceChangeEl.className = change >= 0 ? 'text-green-400' : 'text-red-400';
        }
    }
    
    updateTechnicalAnalysis(techData) {
        // Update technical indicators with precise formatting
        const indicators = [
            { id: 'rsiValue', value: techData.rsi, suffix: '', decimals: 1 },
            { id: 'macdValue', value: techData.macd, suffix: '', decimals: 4 },
            { id: 'volumeRatio', value: techData.volume_ratio, suffix: 'x', decimals: 2 },
            { id: 'atrPercent', value: techData.atr_percent, suffix: '%', decimals: 2 }
        ];
        
        indicators.forEach(indicator => {
            const element = document.getElementById(indicator.id);
            if (element && indicator.value !== undefined) {
                element.textContent = `${indicator.value.toFixed(indicator.decimals)}${indicator.suffix}`;
            }
        });
        
        // Update technical score
        const techScoreEl = document.getElementById('technicalScore');
        if (techScoreEl && techData.technical_score !== undefined) {
            techScoreEl.textContent = techData.technical_score.toFixed(3);
        }
    }
    
    updateMultiSignalScore(signalData) {
        // Update multi-signal score with precise formatting
        const scoreEl = document.getElementById('multiSignalScore');
        if (scoreEl && signalData.composite_score !== undefined) {
            scoreEl.textContent = signalData.composite_score.toFixed(3);
        }
        
        // Update signal strength bar
        const strengthBar = document.getElementById('signalStrengthBar');
        const strengthValue = document.getElementById('signalStrengthValue');
        if (strengthBar && strengthValue && signalData.signal_strength !== undefined) {
            const strength = signalData.signal_strength;
            strengthBar.style.width = `${strength}%`;
            strengthValue.textContent = `${strength.toFixed(1)}%`;
            
            // Color code based on strength
            if (strength >= 70) {
                strengthBar.className = 'bg-gradient-to-r from-green-400 to-green-600 h-2 rounded-full';
            } else if (strength >= 40) {
                strengthBar.className = 'bg-gradient-to-r from-yellow-400 to-yellow-600 h-2 rounded-full';
            } else {
                strengthBar.className = 'bg-gradient-to-r from-red-400 to-red-600 h-2 rounded-full';
            }
        }
        
        // Update signal breakdown
        const breakdownEl = document.getElementById('signalBreakdown');
        if (breakdownEl && signalData.technical_score !== undefined) {
            breakdownEl.textContent = `Tech: ${signalData.technical_score.toFixed(2)} | OnChain: ${signalData.onchain_score.toFixed(2)} | Sentiment: ${signalData.sentiment_score.toFixed(2)}`;
        }
    }
    
    async updateActiveTrades() {
        try {
            const response = await fetch('/api/trades/active');
            const data = await response.json();
            
            // Update active trades count
            const countEl = document.getElementById('activeTradesCount');
            if (countEl) {
                countEl.textContent = data.summary?.total_trades || 0;
            }
            
            // Update total P&L with precise formatting
            const profitEl = document.getElementById('tradesProfit');
            if (profitEl && data.summary?.total_profit_abs !== undefined) {
                const profit = data.summary.total_profit_abs;
                profitEl.textContent = `$${profit.toFixed(2)} P&L`;
                profitEl.className = profit >= 0 ? 'text-xs text-green-400 mt-1' : 'text-xs text-red-400 mt-1';
            }
            
            // Update profitability bar
            const profitabilityBar = document.getElementById('profitabilityBar');
            const profitabilityValue = document.getElementById('profitabilityValue');
            if (profitabilityBar && profitabilityValue && data.summary?.total_profit_pct !== undefined) {
                const profitPct = data.summary.total_profit_pct;
                const normalizedPct = Math.max(0, Math.min(100, (profitPct + 10) * 5)); // Normalize -10% to +10% range to 0-100%
                
                profitabilityBar.style.width = `${normalizedPct}%`;
                profitabilityValue.textContent = `${profitPct.toFixed(1)}%`;
                
                // Color code the bar
                if (profitPct >= 0) {
                    profitabilityBar.className = 'bg-gradient-to-r from-green-400 to-green-600 h-2 rounded-full';
                } else {
                    profitabilityBar.className = 'bg-gradient-to-r from-red-400 to-red-600 h-2 rounded-full';
                }
            }
            
            // Update detailed trades display
            this.updateActiveTradesDetail(data.trades || []);
            
            console.log('💰 Active trades updated:', data.summary?.total_trades || 0);
            
        } catch (error) {
            console.error('Error updating active trades:', error);
            showToast('Failed to load active trades', 'warning');
        }
    }  
  
    updateActiveTradesDetail(trades) {
        const container = document.getElementById('activeTradesDetail');
        if (!container) return;
        
        if (trades.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-wallet"></i>
                    <h3>No Active Trades</h3>
                    <p>Waiting for trading signals to execute</p>
                </div>
            `;
            return;
        }
        
        // Create detailed trade cards
        const tradesHtml = trades.map(trade => `
            <div class="bg-slate-800 rounded-xl p-4 border border-slate-700 hover:border-slate-600 transition-all">
                <div class="flex items-center justify-between mb-3">
                    <div class="flex items-center gap-3">
                        <span class="font-bold text-white">${trade.pair}</span>
                        <span class="px-2 py-1 text-xs rounded-full ${trade.side === 'LONG' ? 'bg-green-900 text-green-300' : 'bg-red-900 text-red-300'}">${trade.side}</span>
                        <span class="px-2 py-1 text-xs rounded-full bg-slate-700 text-slate-300">${trade.risk_level}</span>
                    </div>
                    <button onclick="dashboard.closeTradeModal(${trade.trade_id})" class="text-red-400 hover:text-red-300 text-sm">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                
                <div class="grid grid-cols-2 gap-4 mb-3">
                    <div>
                        <p class="text-xs text-gray-400">Entry Price</p>
                        <p class="font-medium text-white">$${trade.open_rate.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 4})}</p>
                    </div>
                    <div>
                        <p class="text-xs text-gray-400">Current Price</p>
                        <p class="font-medium text-white">$${trade.current_rate.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 4})}</p>
                    </div>
                    <div>
                        <p class="text-xs text-gray-400">P&L</p>
                        <p class="font-medium ${trade.profit_pct >= 0 ? 'text-green-400' : 'text-red-400'}">
                            ${trade.profit_pct >= 0 ? '+' : ''}${trade.profit_pct.toFixed(2)}% ($${trade.profit_abs.toFixed(2)})
                        </p>
                    </div>
                    <div>
                        <p class="text-xs text-gray-400">Duration</p>
                        <p class="font-medium text-white">${trade.duration}</p>
                    </div>
                </div>
                
                <div class="mb-3">
                    <p class="text-xs text-gray-400 mb-1">Entry Reasoning</p>
                    <p class="text-sm text-gray-300">${trade.entry_reasoning}</p>
                </div>
                
                ${trade.stop_loss ? `
                    <div class="flex items-center justify-between text-xs">
                        <span class="text-gray-400">Stop Loss:</span>
                        <span class="text-red-400">$${trade.stop_loss.toFixed(4)}</span>
                    </div>
                ` : ''}
            </div>
        `).join('');
        
        container.innerHTML = tradesHtml;
        
        // Update trade count badge
        const badgeEl = document.getElementById('tradeCountBadge');
        if (badgeEl) {
            badgeEl.textContent = `${trades.length} trade${trades.length !== 1 ? 's' : ''}`;
        }
    }
    
    async updatePatternAnalysis() {
        try {
            const response = await fetch(`/api/market-data/${encodeURIComponent(this.currentSymbol)}`);
            const data = await response.json();
            
            if (data.pattern_analysis) {
                const patterns = data.pattern_analysis;
                
                // Update pattern count
                const countEl = document.getElementById('patternCount');
                if (countEl) {
                    countEl.textContent = patterns.total_patterns || 0;
                }
                
                // Update pattern breakdown
                const breakdownEl = document.getElementById('patternBreakdown');
                if (breakdownEl) {
                    breakdownEl.textContent = `${patterns.bullish_patterns || 0} Bullish, ${patterns.bearish_patterns || 0} Bearish`;
                }
                
                // Update pattern bars
                const bullishBar = document.getElementById('bullishPatternBar');
                const bullishCount = document.getElementById('bullishPatternCount');
                if (bullishBar && bullishCount) {
                    const bullishPct = (patterns.bullish_patterns / Math.max(patterns.total_patterns, 1)) * 100;
                    bullishBar.style.width = `${bullishPct}%`;
                    bullishCount.textContent = patterns.bullish_patterns || 0;
                }
                
                const bearishBar = document.getElementById('bearishPatternBar');
                const bearishCount = document.getElementById('bearishPatternCount');
                if (bearishBar && bearishCount) {
                    const bearishPct = (patterns.bearish_patterns / Math.max(patterns.total_patterns, 1)) * 100;
                    bearishBar.style.width = `${bearishPct}%`;
                    bearishCount.textContent = patterns.bearish_patterns || 0;
                }
                
                // Update advanced patterns display
                this.updateAdvancedPatternsDisplay(patterns.detected_patterns || []);
            }
            
        } catch (error) {
            console.error('Error updating pattern analysis:', error);
            showToast('Failed to load pattern analysis', 'warning');
        }
    }
    
    updateAdvancedPatternsDisplay(patterns) {
        const container = document.getElementById('advancedPatterns');
        if (!container) return;
        
        if (patterns.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-search"></i>
                    <h3>No Patterns Detected</h3>
                    <p>No significant chart patterns found for current timeframe</p>
                </div>
            `;
            return;
        }
        
        const patternsHtml = patterns.map(pattern => `
            <div class="bg-slate-800 rounded-xl p-4 border border-slate-700">
                <div class="flex items-center justify-between mb-2">
                    <h4 class="font-medium text-white">${pattern.type}</h4>
                    <span class="pattern-badge pattern-${pattern.signal.toLowerCase()}">${pattern.signal}</span>
                </div>
                <div class="grid grid-cols-2 gap-4 text-sm">
                    <div>
                        <p class="text-gray-400">Timeframe</p>
                        <p class="text-white font-medium">${pattern.timeframe}</p>
                    </div>
                    <div>
                        <p class="text-gray-400">Confidence</p>
                        <p class="text-white font-medium">${(pattern.confidence * 100).toFixed(0)}%</p>
                    </div>
                    <div>
                        <p class="text-gray-400">Target</p>
                        <p class="text-white font-medium">$${pattern.target_price.toLocaleString()}</p>
                    </div>
                    <div>
                        <p class="text-gray-400">Completion</p>
                        <p class="text-white font-medium">${(pattern.completion * 100).toFixed(0)}%</p>
                    </div>
                </div>
                <div class="mt-3">
                    <div class="w-full bg-slate-700 rounded-full h-2">
                        <div class="bg-gradient-to-r ${pattern.signal === 'BULLISH' ? 'from-green-400 to-green-600' : 'from-red-400 to-red-600'} h-2 rounded-full" 
                             style="width: ${pattern.completion * 100}%"></div>
                    </div>
                </div>
            </div>
        `).join('');
        
        container.innerHTML = patternsHtml;
    }    

    async updateSmartMoneyAnalysis() {
        try {
            const response = await fetch(`/api/market-data/${encodeURIComponent(this.currentSymbol)}`);
            const data = await response.json();
            
            if (data.smart_money_signals) {
                const smartMoney = data.smart_money_signals;
                
                // Update smart money signal
                const signalEl = document.getElementById('smartMoneySignal');
                if (signalEl) {
                    signalEl.textContent = smartMoney.signal || 'NEUTRAL';
                    
                    // Color code the signal
                    if (smartMoney.signal === 'ACCUMULATION') {
                        signalEl.className = 'text-2xl font-bold mt-2 text-green-400';
                    } else if (smartMoney.signal === 'DISTRIBUTION') {
                        signalEl.className = 'text-2xl font-bold mt-2 text-red-400';
                    } else {
                        signalEl.className = 'text-2xl font-bold mt-2 text-yellow-400';
                    }
                }
                
                // Update confidence
                const confidenceEl = document.getElementById('smartMoneyConfidence');
                const confidenceValueEl = document.getElementById('smartMoneyConfidenceValue');
                const confidenceBarEl = document.getElementById('smartMoneyConfidenceBar');
                
                if (confidenceEl && smartMoney.confidence !== undefined) {
                    const confidence = smartMoney.confidence * 100;
                    confidenceEl.textContent = `${confidence.toFixed(0)}% confidence in ${smartMoney.signal.toLowerCase()} signal`;
                    
                    if (confidenceValueEl) {
                        confidenceValueEl.textContent = `${confidence.toFixed(0)}%`;
                    }
                    
                    if (confidenceBarEl) {
                        confidenceBarEl.style.width = `${confidence}%`;
                    }
                }
                
                // Update smart money analysis details
                this.updateSmartMoneyDetails(smartMoney);
            }
            
        } catch (error) {
            console.error('Error updating smart money analysis:', error);
            showToast('Failed to load smart money analysis', 'warning');
        }
    }
    
    updateSmartMoneyDetails(smartMoney) {
        const container = document.getElementById('smartMoneyAnalysis');
        if (!container) return;
        
        const analysisHtml = `
            <div class="space-y-4">
                <div class="bg-slate-800 rounded-xl p-4">
                    <h4 class="font-medium text-white mb-3">Whale Activity</h4>
                    <div class="flex items-center justify-between mb-2">
                        <span class="text-sm text-gray-400">Activity Level</span>
                        <span class="text-sm font-medium text-white">${(smartMoney.whale_activity * 100).toFixed(1)}%</span>
                    </div>
                    <div class="w-full bg-slate-700 rounded-full h-2">
                        <div class="bg-gradient-to-r from-orange-400 to-orange-600 h-2 rounded-full" 
                             style="width: ${smartMoney.whale_activity * 100}%"></div>
                    </div>
                </div>
                
                <div class="bg-slate-800 rounded-xl p-4">
                    <h4 class="font-medium text-white mb-3">Institutional Flow</h4>
                    <div class="flex items-center justify-between mb-2">
                        <span class="text-sm text-gray-400">Net Flow</span>
                        <span class="text-sm font-medium ${smartMoney.institutional_flow >= 0 ? 'text-green-400' : 'text-red-400'}">
                            ${smartMoney.institutional_flow >= 0 ? '+' : ''}${(smartMoney.institutional_flow * 100).toFixed(1)}%
                        </span>
                    </div>
                    <div class="w-full bg-slate-700 rounded-full h-2">
                        <div class="bg-gradient-to-r ${smartMoney.institutional_flow >= 0 ? 'from-green-400 to-green-600' : 'from-red-400 to-red-600'} h-2 rounded-full" 
                             style="width: ${Math.abs(smartMoney.institutional_flow) * 100}%"></div>
                    </div>
                </div>
                
                <div class="bg-slate-800 rounded-xl p-4">
                    <h4 class="font-medium text-white mb-3">Large Transactions</h4>
                    <div class="flex items-center justify-between">
                        <span class="text-sm text-gray-400">Last 24h</span>
                        <span class="text-lg font-bold text-white">${smartMoney.large_transactions || 0}</span>
                    </div>
                </div>
                
                <div class="bg-slate-800 rounded-xl p-4">
                    <h4 class="font-medium text-white mb-3">Analysis Summary</h4>
                    <div class="space-y-2">
                        ${smartMoney.reasoning?.map(reason => `
                            <div class="flex items-start gap-2">
                                <i class="fas fa-check-circle text-green-400 text-sm mt-0.5"></i>
                                <span class="text-sm text-gray-300">${reason}</span>
                            </div>
                        `).join('') || '<p class="text-sm text-gray-400">No analysis available</p>'}
                    </div>
                </div>
            </div>
        `;
        
        container.innerHTML = analysisHtml;
    }
    
    async updateKeyMetrics() {
        // This method updates the key metrics cards at the top
        // Most of the work is done in other update methods, but we can add any additional logic here
        console.log('📊 Key metrics updated');
    }
    
    updateLastUpdateTime() {
        const now = new Date();
        this.lastUpdate = now;
        
        const timeString = now.toLocaleTimeString('en-US', {
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
        
        // Update both last update displays
        const lastUpdateEl = document.getElementById('lastUpdate');
        const lastUpdateHeaderEl = document.getElementById('lastUpdateHeader');
        
        if (lastUpdateEl) {
            lastUpdateEl.textContent = `Last updated: ${timeString}`;
        }
        
        if (lastUpdateHeaderEl) {
            lastUpdateHeaderEl.textContent = `Last updated: ${timeString}`;
        }
    }
    
    // User interaction methods
    analyzeSymbol() {
        const symbolInput = document.getElementById('symbolInput');
        if (symbolInput && symbolInput.value.trim()) {
            this.currentSymbol = symbolInput.value.trim().toUpperCase();
            console.log(`🔍 Analyzing symbol: ${this.currentSymbol}`);
            
            // Update TradingView chart symbol
            this.updateTradingViewChart();
            
            // Update all data
            this.updateAllData();
        }
    }
    
    updateTradingViewChart() {
        try {
            // Convert pair format for TradingView (BTC/USDT -> BTCUSDT)
            const tvSymbol = this.currentSymbol.replace('/', '');
            
            // Update TradingView widget
            const chartContainer = document.getElementById('tradingview_widget');
            if (chartContainer) {
                // Clear existing chart
                chartContainer.innerHTML = '';
                
                // Create new TradingView widget
                new TradingView.widget({
                    "autosize": true,
                    "symbol": `BINANCE:${tvSymbol}`,
                    "interval": this.currentTimeframe === '1h' ? '60' : this.currentTimeframe,
                    "timezone": "Etc/UTC",
                    "theme": "dark",
                    "style": "1",
                    "locale": "en",
                    "enable_publishing": false,
                    "backgroundColor": "rgba(30, 41, 59, 1)",
                    "gridColor": "rgba(51, 65, 85, 1)",
                    "hide_top_toolbar": false,
                    "hide_legend": false,
                    "save_image": false,
                    "container_id": "tradingview_widget"
                });
                
                console.log(`📊 TradingView chart updated to ${tvSymbol}`);
            }
        } catch (error) {
            console.error('Error updating TradingView chart:', error);
        }
    }
    
    quickAnalyze(symbol) {
        this.currentSymbol = symbol;
        const symbolInput = document.getElementById('symbolInput');
        if (symbolInput) {
            symbolInput.value = symbol;
        }
        console.log(`⚡ Quick analyzing: ${symbol}`);
        
        // Update TradingView chart
        this.updateTradingViewChart();
        
        // Update all data
        this.updateAllData();
    }
    
    setTimeframe(timeframe) {
        this.currentTimeframe = timeframe;
        
        // Update active timeframe button
        document.querySelectorAll('.timeframe-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        
        event.target.classList.add('active');
        
        console.log(`⏰ Timeframe changed to: ${timeframe}`);
        
        // Update TradingView chart with new timeframe
        this.updateTradingViewChart();
        
        // Update all data
        this.updateAllData();
    }
    
    initializeTradingViewChart() {
        try {
            // Convert pair format for TradingView (BTC/USDT -> BTCUSDT)
            const tvSymbol = this.currentSymbol.replace('/', '');
            
            // Convert timeframe format for TradingView
            const tvInterval = this.convertTimeframeForTradingView(this.currentTimeframe);
            
            console.log(`📊 Initializing TradingView chart: ${tvSymbol} on ${tvInterval}`);
            
            // Create TradingView widget
            new TradingView.widget({
                "autosize": true,
                "symbol": `BINANCE:${tvSymbol}`,
                "interval": tvInterval,
                "timezone": "Etc/UTC",
                "theme": "dark",
                "style": "1",
                "locale": "en",
                "enable_publishing": false,
                "backgroundColor": "rgba(30, 41, 59, 1)",
                "gridColor": "rgba(51, 65, 85, 1)",
                "hide_top_toolbar": false,
                "hide_legend": false,
                "save_image": false,
                "container_id": "tradingview_widget",
                "studies": [
                    "Volume@tv-basicstudies",
                    "RSI@tv-basicstudies",
                    "MACD@tv-basicstudies"
                ],
                "toolbar_bg": "#1e293b",
                "loading_screen": {
                    "backgroundColor": "#1e293b",
                    "foregroundColor": "#667eea"
                }
            });
            
            console.log(`✅ TradingView chart initialized for ${tvSymbol}`);
            
        } catch (error) {
            console.error('❌ Error initializing TradingView chart:', error);
            this.showChartError(error.message);
        }
    }
    
    updateTradingViewChart() {
        try {
            // Clear existing chart
            const chartContainer = document.getElementById('tradingview_widget');
            if (chartContainer) {
                chartContainer.innerHTML = '';
                
                // Small delay to ensure container is cleared
                setTimeout(() => {
                    this.initializeTradingViewChart();
                }, 100);
            }
        } catch (error) {
            console.error('❌ Error updating TradingView chart:', error);
            this.showChartError(error.message);
        }
    }
    
    convertTimeframeForTradingView(timeframe) {
        const timeframeMap = {
            '1m': '1',
            '5m': '5',
            '15m': '15',
            '1h': '60',
            '4h': '240',
            '1d': '1D'
        };
        
        return timeframeMap[timeframe] || '60';
    }
    
    showChartError(errorMessage) {
        const chartContainer = document.getElementById('tradingview_widget');
        if (chartContainer) {
            chartContainer.innerHTML = `
                <div class="flex items-center justify-center h-full bg-slate-800 rounded-xl">
                    <div class="text-center text-gray-400">
                        <i class="fas fa-exclamation-triangle text-4xl mb-3"></i>
                        <div class="font-medium text-lg">Chart Error</div>
                        <div class="text-sm mt-1">${errorMessage}</div>
                        <button onclick="dashboard.updateTradingViewChart()" class="mt-4 px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg text-sm">
                            <i class="fas fa-redo mr-2"></i>Retry
                        </button>
                    </div>
                </div>
            `;
        }
    }
    
    toggleAutoRefresh() {
        this.autoRefresh = !this.autoRefresh;
        
        const btn = document.getElementById('autoRefreshBtn');
        if (btn) {
            const span = btn.querySelector('span');
            if (span) {
                span.textContent = `Auto Refresh: ${this.autoRefresh ? 'ON' : 'OFF'}`;
            }
        }
        
        if (this.autoRefresh) {
            this.startAutoRefresh();
        } else {
            this.stopAutoRefresh();
        }
        
        console.log(`🔄 Auto refresh: ${this.autoRefresh ? 'ON' : 'OFF'}`);
    }
    
    startAutoRefresh() {
        this.stopAutoRefresh(); // Clear any existing interval
        
        if (this.autoRefresh) {
            this.refreshInterval = setInterval(() => {
                this.updateAllData();
            }, 30000); // Update every 30 seconds
            
            console.log('🔄 Auto refresh started (30s interval)');
        }
    }
    
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
            console.log('⏹️ Auto refresh stopped');
        }
    }
    
    showError(message) {
        console.error('❌ Dashboard Error:', message);
        // You could add a toast notification here
    }
    
    closeTradeModal(tradeId) {
        if (confirm(`Are you sure you want to close trade ${tradeId}?`)) {
            this.closeTrade(tradeId);
        }
    }
    
    async closeTrade(tradeId) {
        try {
            const response = await fetch(`/api/trades/${tradeId}/close`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    reason: 'Manual close via dashboard'
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                console.log(`✅ Trade ${tradeId} closed successfully`);
                // Refresh trades data
                this.updateActiveTrades();
            } else {
                console.error(`❌ Failed to close trade ${tradeId}:`, result.error);
            }
            
        } catch (error) {
            console.error('Error closing trade:', error);
        }
    }
}

// Global functions for HTML onclick handlers
function analyzeSymbol() {
    if (window.dashboard) {
        window.dashboard.analyzeSymbol();
    }
}

function quickAnalyze(symbol) {
    if (window.dashboard) {
        window.dashboard.quickAnalyze(symbol);
    }
}

function setTimeframe(timeframe) {
    if (window.dashboard) {
        window.dashboard.setTimeframe(timeframe);
    }
}

function toggleAutoRefresh() {
    if (window.dashboard) {
        window.dashboard.toggleAutoRefresh();
    }
}

function filterPatterns(type) {
    console.log(`🔍 Filtering patterns: ${type}`);
    // Add pattern filtering logic here
}

function runScreener() {
    console.log('🔍 Running smart money screener');
    if (window.dashboard) {
        window.dashboard.updateSmartMoneyScreener();
    }
}

function setChartTimeframe(timeframe) {
    console.log(`📊 Setting chart timeframe to: ${timeframe}`);
    
    // Update active chart timeframe button
    document.querySelectorAll('.chart-timeframe-btn').forEach(btn => {
        btn.classList.remove('active');
        btn.classList.remove('bg-gradient-to-r', 'from-blue-500', 'to-purple-600', 'text-white');
        btn.classList.add('bg-slate-800', 'hover:bg-slate-700');
    });
    
    // Set active button
    event.target.classList.add('active');
    event.target.classList.remove('bg-slate-800', 'hover:bg-slate-700');
    event.target.classList.add('bg-gradient-to-r', 'from-blue-500', 'to-purple-600', 'text-white');
    
    // Map chart timeframes to trading timeframes
    const timeframeMap = {
        '1D': '1d',
        '1W': '1d', // Use daily for weekly view
        '1M': '1d', // Use daily for monthly view
        'All': '1h'  // Use hourly for all-time view
    };
    
    if (window.dashboard) {
        // Update dashboard timeframe
        window.dashboard.currentTimeframe = timeframeMap[timeframe] || '1h';
        
        // Update TradingView chart
        window.dashboard.updateTradingViewChart();
    }
}

// Global functions for HTML onclick handlers
function analyzeSymbol() {
    if (window.dashboard) {
        const symbolInput = document.getElementById('symbolInput');
        if (symbolInput && symbolInput.value.trim()) {
            window.dashboard.currentSymbol = symbolInput.value.trim().toUpperCase();
            console.log(`🔍 Analyzing symbol: ${window.dashboard.currentSymbol}`);
            
            // Update TradingView chart with new symbol
            updateTradingViewSymbol();
            
            window.dashboard.updateAllData();
        }
    }
}

function quickAnalyze(symbol) {
    if (window.dashboard) {
        window.dashboard.currentSymbol = symbol;
        const symbolInput = document.getElementById('symbolInput');
        if (symbolInput) {
            symbolInput.value = symbol;
        }
        console.log(`⚡ Quick analyzing: ${symbol}`);
        
        // Update TradingView chart with new symbol
        updateTradingViewSymbol();
        
        window.dashboard.updateAllData();
    }
}

function setTimeframe(timeframe) {
    if (window.dashboard) {
        window.dashboard.currentTimeframe = timeframe;
        
        // Update active timeframe button
        document.querySelectorAll('.timeframe-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        
        event.target.classList.add('active');
        
        console.log(`⏰ Timeframe changed to: ${timeframe}`);
        
        // Update TradingView chart
        updateTradingViewSymbol();
        
        window.dashboard.updateAllData();
    }
}

function updateTradingViewSymbol() {
    try {
        if (!window.dashboard) return;
        
        // Convert pair format for TradingView (BTC/USDT -> BTCUSDT)
        const tvSymbol = window.dashboard.currentSymbol.replace('/', '');
        
        console.log(`📊 Updating TradingView chart to: ${tvSymbol}`);
        
        // Find and update the TradingView widget
        const container = document.querySelector('.tradingview-widget-container__widget');
        if (container) {
            container.innerHTML = '';
            
            // Create new script with updated symbol
            const script = document.createElement('script');
            script.type = 'text/javascript';
            script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js';
            script.async = true;
            script.innerHTML = JSON.stringify({
                "width": "100%",
                "height": "100%",
                "symbol": `BINANCE:${tvSymbol}`,
                "interval": convertTimeframeForTradingView(window.dashboard.currentTimeframe),
                "timezone": "Etc/UTC",
                "theme": "dark",
                "style": "1", // Candlestick style
                "locale": "en",
                "enable_publishing": false,
                "backgroundColor": "rgba(30, 41, 59, 1)",
                "gridColor": "rgba(51, 65, 85, 1)",
                "hide_top_toolbar": false,
                "hide_legend": false,
                "save_image": false,
                "studies": [
                    "Volume@tv-basicstudies",
                    "RSI@tv-basicstudies", 
                    "MACD@tv-basicstudies",
                    "BB@tv-basicstudies"
                ],
                "show_popup_button": true,
                "popup_width": "1000",
                "popup_height": "650"
            });
            
            container.appendChild(script);
        }
        
    } catch (error) {
        console.error('❌ Error updating TradingView symbol:', error);
    }
}

function convertTimeframeForTradingView(timeframe) {
    const timeframeMap = {
        '1m': '1',
        '5m': '5', 
        '15m': '15',
        '1h': '60',
        '4h': '240',
        '1d': '1D',
        '1w': '1W'
    };
    
    return timeframeMap[timeframe] || '60';
}

function toggleAutoRefresh() {
    if (window.dashboard) {
        window.dashboard.toggleAutoRefresh();
    }
}

function filterPatterns(type) {
    console.log(`🔍 Filtering patterns: ${type}`);
    // Add pattern filtering logic here
}

function runScreener() {
    console.log('🔍 Running smart money screener');
    if (window.dashboard) {
        window.dashboard.updateSmartMoneyScreener();
    }
}

function refreshSocialSentiment() {
    console.log('🔄 Refreshing social sentiment');
    if (window.dashboard) {
        window.dashboard.updateSocialSentiment();
    }
}

// Fix timeframe functionality to actually affect data
async function fetchTimeframeData(timeframe) {
    try {
        if (!window.dashboard) return;
        
        console.log(`📊 Fetching ${timeframe} specific data for ${window.dashboard.currentSymbol}`);
        
        const response = await fetch(`/api/timeframe-data/${encodeURIComponent(window.dashboard.currentSymbol)}/${timeframe}`);
        const data = await response.json();
        
        if (data.error) {
            console.error('Error fetching timeframe data:', data.error);
            return;
        }
        
        // Update indicators with timeframe-adjusted values
        if (data.technical_analysis) {
            // Update signal strength based on timeframe
            const signalStrengthElement = document.getElementById('signalStrengthValue');
            const signalStrengthBar = document.getElementById('signalStrengthBar');
            
            if (signalStrengthElement) {
                signalStrengthElement.textContent = `${data.signal_strength || 50}%`;
            }
            
            if (signalStrengthBar) {
                const strength = data.signal_strength || 50;
                signalStrengthBar.style.width = `${strength}%`;
                
                // Color code based on strength
                if (strength >= 70) {
                    signalStrengthBar.className = 'bg-gradient-to-r from-green-400 to-green-600 h-2 rounded-full';
                } else if (strength >= 40) {
                    signalStrengthBar.className = 'bg-gradient-to-r from-yellow-400 to-yellow-600 h-2 rounded-full';
                } else {
                    signalStrengthBar.className = 'bg-gradient-to-r from-red-400 to-red-600 h-2 rounded-full';
                }
            }
        }
        
        console.log(`✅ Timeframe data updated for ${timeframe}`);
        
    } catch (error) {
        console.error('Error fetching timeframe data:', error);
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 DOM loaded, initializing dashboard');
    window.dashboard = new TradingDashboard();
});