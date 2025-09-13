// Charts-specific JavaScript functionality for FrickTrader Dashboard

class ChartsManager {
    constructor() {
        this.selectedChartPair = '';
        this.selectedTimeframe = '1h';
        this.selectedChartType = 'candlesticks';
        this.chartLoading = false;
        this.chartData = null;
        this.chart = null;
        
        // Technical indicators state
        this.indicators = {
            sma: false,
            ema: false,
            rsi: false,
            macd: false,
            bollinger: false
        };
        
        // Chart analysis data
        this.currentSignals = [];
        this.supportResistanceLevels = [];
        this.recentChartTrades = [];
        this.volumeAnalysis = {
            current: '0',
            average: '0',
            trend: 'neutral',
            analysis: 'Loading volume data...'
        };
        this.detectedPatterns = [];
        
        this.init();
    }
    
    init() {
        console.log('📈 Initializing Charts Manager');
        this.loadInitialData();
        this.initializeChart();
    }
    
    async loadInitialData() {
        try {
            // Load default chart data for BTC/USDT
            if (!this.selectedChartPair) {
                this.selectedChartPair = 'BTC/USDT';
            }
            
            await this.loadChartData();
            
        } catch (error) {
            console.error('Error loading initial chart data:', error);
        }
    }
    
    async loadChartData() {
        if (!this.selectedChartPair) {
            console.warn('No chart pair selected');
            return;
        }
        
        this.chartLoading = true;
        
        try {
            const response = await fetch(`/api/chart-data/${encodeURIComponent(this.selectedChartPair)}/${this.selectedTimeframe}`);
            const data = await response.json();
            
            if (data.success) {
                this.chartData = data.data;
                await this.updateChartDisplay();
                await this.updateChartAnalysis();
            } else {
                console.error('Error loading chart data:', data.error);
                this.showChartError(data.error);
            }
            
        } catch (error) {
            console.error('Error loading chart data:', error);
            this.showChartError('Failed to load chart data');
        } finally {
            this.chartLoading = false;
        }
    }
    
    initializeChart() {
        const chartContainer = document.getElementById('tradingview-chart');
        if (!chartContainer) {
            console.warn('Chart container not found');
            return;
        }
        
        // Initialize lightweight-charts if available
        if (typeof LightweightCharts !== 'undefined') {
            this.chart = LightweightCharts.createChart(chartContainer, {
                width: chartContainer.clientWidth,
                height: 400,
                layout: {
                    backgroundColor: '#1f2937',
                    textColor: '#d1d5db'
                },
                grid: {
                    vertLines: { color: '#374151' },
                    horzLines: { color: '#374151' }
                },
                crosshair: {
                    mode: LightweightCharts.CrosshairMode.Normal,
                },
                rightPriceScale: {
                    borderColor: '#6b7280',
                },
                timeScale: {
                    borderColor: '#6b7280',
                    timeVisible: true,
                    secondsVisible: false,
                }
            });
            
            // Add candlestick series
            this.candlestickSeries = this.chart.addCandlestickSeries({
                upColor: '#10b981',
                downColor: '#ef4444',
                borderDownColor: '#ef4444',
                borderUpColor: '#10b981',
                wickDownColor: '#ef4444',
                wickUpColor: '#10b981'
            });
            
            // Add volume series
            this.volumeSeries = this.chart.addHistogramSeries({
                color: '#6b7280',
                priceFormat: {
                    type: 'volume',
                },
                priceScaleId: '',
                scaleMargins: {
                    top: 0.8,
                    bottom: 0,
                },
            });
            
            console.log('✅ Lightweight Charts initialized');
        } else {
            console.warn('LightweightCharts library not available, using fallback');
            this.initializeFallbackChart();
        }
    }
    
    initializeFallbackChart() {
        const chartContainer = document.getElementById('tradingview-chart');
        if (!chartContainer) return;
        
        chartContainer.innerHTML = `
            <div class="flex items-center justify-center h-full bg-gray-900 rounded-lg">
                <div class="text-center text-gray-400">
                    <i class="fas fa-chart-area text-4xl mb-3"></i>
                    <h3 class="text-lg font-medium mb-2">Chart Placeholder</h3>
                    <p class="text-sm">Loading chart library...</p>
                </div>
            </div>
        `;
    }
    
    async updateChartDisplay() {
        if (!this.chartData || !this.chart) return;
        
        try {
            // Update candlestick data
            if (this.candlestickSeries && this.chartData.ohlcv) {
                const candlestickData = this.chartData.ohlcv.map(item => ({
                    time: item.time,
                    open: item.open,
                    high: item.high,
                    low: item.low,
                    close: item.close
                }));
                
                this.candlestickSeries.setData(candlestickData);
            }
            
            // Update volume data
            if (this.volumeSeries && this.chartData.ohlcv) {
                const volumeData = this.chartData.ohlcv.map(item => ({
                    time: item.time,
                    value: item.volume,
                    color: item.close >= item.open ? '#10b981' : '#ef4444'
                }));
                
                this.volumeSeries.setData(volumeData);
            }
            
            // Update current price info
            this.updateCurrentPriceInfo();
            
            console.log('📊 Chart display updated');
            
        } catch (error) {
            console.error('Error updating chart display:', error);
        }
    }
    
    updateCurrentPriceInfo() {
        if (!this.chartData || !this.chartData.current) return;
        
        const current = this.chartData.current;
        
        // Update price info elements if they exist
        const elements = {
            open: document.querySelector('[x-text="chartData?.current?.open || \'-\'"]'),
            high: document.querySelector('[x-text="chartData?.current?.high || \'-\'"]'),
            low: document.querySelector('[x-text="chartData?.current?.low || \'-\'"]'),
            close: document.querySelector('[x-text="chartData?.current?.close || \'-\'"]'),
            volume: document.querySelector('[x-text="chartData?.current?.volume || \'-\'"]'),
            change: document.querySelector('[x-text="(chartData?.current?.change || \'0\') + \'%\'"]')
        };
        
        if (elements.open) elements.open.textContent = current.open?.toFixed(4) || '-';
        if (elements.high) elements.high.textContent = current.high?.toFixed(4) || '-';
        if (elements.low) elements.low.textContent = current.low?.toFixed(4) || '-';
        if (elements.close) elements.close.textContent = current.close?.toFixed(4) || '-';
        if (elements.volume) elements.volume.textContent = this.formatVolume(current.volume) || '-';
        if (elements.change) {
            const change = current.change || 0;
            elements.change.textContent = `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`;
            elements.change.className = change >= 0 ? 'text-green-400' : 'text-red-400';
        }
    }
    
    formatVolume(volume) {
        if (!volume) return '0';
        
        if (volume >= 1e9) return `${(volume / 1e9).toFixed(2)}B`;
        if (volume >= 1e6) return `${(volume / 1e6).toFixed(2)}M`;
        if (volume >= 1e3) return `${(volume / 1e3).toFixed(2)}K`;
        
        return volume.toFixed(0);
    }
    
    async updateChartAnalysis() {
        try {
            await Promise.all([
                this.updateCurrentSignals(),
                this.updateSupportResistance(),
                this.updateRecentTrades(),
                this.updateVolumeAnalysis(),
                this.updatePatternDetection()
            ]);
        } catch (error) {
            console.error('Error updating chart analysis:', error);
        }
    }
    
    async updateCurrentSignals() {
        try {
            const response = await fetch(`/api/chart-signals/${encodeURIComponent(this.selectedChartPair)}`);
            const data = await response.json();
            
            if (data.success) {
                this.currentSignals = data.signals || [];
                this.renderCurrentSignals();
            }
        } catch (error) {
            console.error('Error updating current signals:', error);
        }
    }
    
    renderCurrentSignals() {
        // This would be handled by Alpine.js in the actual implementation
        // For now, just log the signals
        console.log('Current signals updated:', this.currentSignals);
    }
    
    async updateSupportResistance() {
        try {
            const response = await fetch(`/api/support-resistance/${encodeURIComponent(this.selectedChartPair)}`);
            const data = await response.json();
            
            if (data.success) {
                this.supportResistanceLevels = data.levels || [];
                this.renderSupportResistance();
            }
        } catch (error) {
            console.error('Error updating support/resistance:', error);
            // Use fallback data
            this.supportResistanceLevels = this.generateFallbackSupportResistance();
        }
    }
    
    generateFallbackSupportResistance() {
        if (!this.chartData || !this.chartData.current) return [];
        
        const currentPrice = this.chartData.current.close || 50000;
        
        return [
            {
                type: 'resistance',
                price: (currentPrice * 1.05).toFixed(2),
                strength: 'Strong',
                distance: '+5.0%'
            },
            {
                type: 'support',
                price: (currentPrice * 0.95).toFixed(2),
                strength: 'Moderate',
                distance: '-5.0%'
            },
            {
                type: 'resistance',
                price: (currentPrice * 1.08).toFixed(2),
                strength: 'Weak',
                distance: '+8.0%'
            }
        ];
    }
    
    renderSupportResistance() {
        console.log('Support/resistance levels updated:', this.supportResistanceLevels);
    }
    
    async updateRecentTrades() {
        try {
            const response = await fetch(`/api/recent-trades/${encodeURIComponent(this.selectedChartPair)}`);
            const data = await response.json();
            
            if (data.success) {
                this.recentChartTrades = data.trades || [];
            } else {
                // Generate sample trade data
                this.recentChartTrades = this.generateSampleTrades();
            }
        } catch (error) {
            console.error('Error updating recent trades:', error);
            this.recentChartTrades = this.generateSampleTrades();
        }
    }
    
    generateSampleTrades() {
        const trades = [];
        const now = new Date();
        
        for (let i = 0; i < 5; i++) {
            const time = new Date(now.getTime() - i * 60 * 60 * 1000);
            trades.push({
                id: i + 1,
                pair: this.selectedChartPair,
                side: Math.random() > 0.5 ? 'buy' : 'sell',
                price: (Math.random() * 1000 + 45000).toFixed(2),
                amount: (Math.random() * 0.1 + 0.01).toFixed(4),
                pnl: (Math.random() * 200 - 100).toFixed(2),
                date: time.toLocaleTimeString()
            });
        }
        
        return trades;
    }
    
    async updateVolumeAnalysis() {
        try {
            if (this.chartData && this.chartData.volume_analysis) {
                this.volumeAnalysis = this.chartData.volume_analysis;
            } else {
                // Generate sample volume analysis
                this.volumeAnalysis = {
                    current: this.formatVolume(Math.random() * 1000000000),
                    average: this.formatVolume(Math.random() * 800000000),
                    trend: Math.random() > 0.5 ? 'increasing' : 'decreasing',
                    analysis: 'Volume is above average, indicating strong market interest'
                };
            }
        } catch (error) {
            console.error('Error updating volume analysis:', error);
        }
    }
    
    async updatePatternDetection() {
        try {
            const response = await fetch(`/api/pattern-detection/${encodeURIComponent(this.selectedChartPair)}`);
            const data = await response.json();
            
            if (data.success) {
                this.detectedPatterns = data.patterns || [];
            } else {
                this.detectedPatterns = this.generateSamplePatterns();
            }
        } catch (error) {
            console.error('Error updating pattern detection:', error);
            this.detectedPatterns = this.generateSamplePatterns();
        }
    }
    
    generateSamplePatterns() {
        const patterns = [
            {
                id: 1,
                name: 'Ascending Triangle',
                description: 'Bullish continuation pattern forming',
                reliability: 75,
                target: '52,000',
                stopLoss: '48,000'
            },
            {
                id: 2,
                name: 'Support Test',
                description: 'Price testing key support level',
                reliability: 65,
                target: '51,500',
                stopLoss: '47,500'
            }
        ];
        
        return patterns;
    }
    
    updateChartType() {
        console.log('Chart type changed to:', this.selectedChartType);
        // Implement chart type switching logic here
        this.loadChartData();
    }
    
    toggleIndicator(indicator) {
        this.indicators[indicator] = !this.indicators[indicator];
        console.log(`Indicator ${indicator} ${this.indicators[indicator] ? 'enabled' : 'disabled'}`);
        
        // Implement indicator toggle logic
        this.updateIndicators();
    }
    
    updateIndicators() {
        // Add/remove indicators based on state
        if (this.chart) {
            // Implementation would go here for adding/removing technical indicators
            console.log('Updating indicators:', this.indicators);
        }
    }
    
    showChartError(message) {
        const chartContainer = document.getElementById('tradingview-chart');
        if (chartContainer) {
            chartContainer.innerHTML = `
                <div class="flex items-center justify-center h-full bg-gray-900 rounded-lg border border-gray-700">
                    <div class="text-center text-gray-500">
                        <i class="fas fa-exclamation-triangle text-4xl mb-3"></i>
                        <p class="text-lg font-medium mb-1">Chart Error</p>
                        <p class="text-sm">${message}</p>
                        <button onclick="chartsManager.loadChartData()" 
                                class="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm">
                            <i class="fas fa-sync-alt mr-2"></i>Retry
                        </button>
                    </div>
                </div>
            `;
        }
    }
    
    // Resize handler for responsive charts
    handleResize() {
        if (this.chart) {
            const chartContainer = document.getElementById('tradingview-chart');
            if (chartContainer) {
                this.chart.applyOptions({
                    width: chartContainer.clientWidth,
                });
            }
        }
    }
}

// Global functions for charts
window.loadChartData = function() {
    if (window.chartsManager) {
        window.chartsManager.loadChartData();
    }
};

window.updateChartType = function() {
    if (window.chartsManager) {
        window.chartsManager.updateChartType();
    }
};

window.toggleIndicator = function(indicator) {
    if (window.chartsManager) {
        window.chartsManager.toggleIndicator(indicator);
    }
};

// Initialize charts manager when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Wait a bit for the main dashboard to initialize
    setTimeout(() => {
        console.log('📈 Initializing Charts Manager');
        window.chartsManager = new ChartsManager();
        
        // Handle window resize
        window.addEventListener('resize', () => {
            if (window.chartsManager) {
                window.chartsManager.handleResize();
            }
        });
    }, 1000);
});

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ChartsManager;
}