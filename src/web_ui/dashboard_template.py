DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚀 FrickTrader Pro Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js" defer></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .gradient-bg { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .card-hover { transition: all 0.3s ease; }
        .card-hover:hover { transform: translateY(-2px); box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1); }
        .nav-tab.active { background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); }
        .metric-card { background: linear-gradient(145deg, #1f2937 0%, #111827 100%); }
        .profit { color: #10b981; }
        .loss { color: #ef4444; }
        .btn-primary { background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); }
        .btn-success { background: linear-gradient(135deg, #10b981 0%, #059669 100%); }
        .btn-danger { background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); }
        .btn-warning { background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); }
        .status-indicator { width: 12px; height: 12px; border-radius: 50%; animation: pulse 2s infinite; }
        .status-online { background-color: #10b981; }
        .status-offline { background-color: #ef4444; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
    </style>
</head>
<body class="bg-gray-900 text-white min-h-screen" x-data="dashboard()">
    <!-- Header -->
    <header class="gradient-bg p-6 shadow-2xl">
        <div class="max-w-7xl mx-auto flex justify-between items-center">
            <div>
                <h1 class="text-4xl font-bold text-white flex items-center">
                    <i class="fas fa-rocket mr-3"></i>FrickTrader Pro
                </h1>
                <p class="text-blue-100 mt-1">Professional Trading Command Center</p>
            </div>
            <div class="text-right">
                <div class="flex items-center mb-2">
                    <div class="status-indicator mr-2" :class="status.api_connected ? 'status-online' : 'status-offline'"></div>
                    <span class="text-white font-semibold" x-text="status.api_connected ? 'CONNECTED' : 'DISCONNECTED'"></span>
                </div>
                <div class="text-blue-100 text-sm" x-text="'Updated: ' + lastUpdate"></div>
            </div>
        </div>
    </header>

    <div class="max-w-7xl mx-auto p-6">
        <!-- Navigation Tabs -->
        <nav class="flex space-x-1 mb-8 bg-gray-800 p-1 rounded-lg">
            <button @click="activeTab = 'overview'" :class="activeTab === 'overview' ? 'nav-tab active' : 'nav-tab'" 
                    class="px-6 py-3 rounded-md text-white font-medium transition-all">
                <i class="fas fa-chart-line mr-2"></i>Overview
            </button>
            <button @click="activeTab = 'control'" :class="activeTab === 'control' ? 'nav-tab active' : 'nav-tab'"
                    class="px-6 py-3 rounded-md text-white font-medium transition-all">
                <i class="fas fa-cogs mr-2"></i>Bot Control
            </button>
            <button @click="activeTab = 'trading'" :class="activeTab === 'trading' ? 'nav-tab active' : 'nav-tab'"
                    class="px-6 py-3 rounded-md text-white font-medium transition-all">
                <i class="fas fa-exchange-alt mr-2"></i>Trading
            </button>
            <button @click="activeTab = 'market'" :class="activeTab === 'market' ? 'nav-tab active' : 'nav-tab'"
                    class="px-6 py-3 rounded-md text-white font-medium transition-all">
                <i class="fas fa-globe mr-2"></i>Market
            </button>
            <button @click="activeTab = 'logic'" :class="activeTab === 'logic' ? 'nav-tab active' : 'nav-tab'"
                    class="px-6 py-3 rounded-md text-white font-medium transition-all">
                <i class="fas fa-brain mr-2"></i>Trade Logic
            </button>
            <button @click="activeTab = 'analytics'" :class="activeTab === 'analytics' ? 'nav-tab active' : 'nav-tab'"
                    class="px-6 py-3 rounded-md text-white font-medium transition-all">
                <i class="fas fa-chart-bar mr-2"></i>Analytics
            </button>
            <button @click="activeTab = 'backtest'" :class="activeTab === 'backtest' ? 'nav-tab active' : 'nav-tab'"
                    class="px-6 py-3 rounded-md text-white font-medium transition-all">
                <i class="fas fa-history mr-2"></i>Backtest
            </button>
            <button @click="activeTab = 'charts'" :class="activeTab === 'charts' ? 'nav-tab active' : 'nav-tab'"
                    class="px-6 py-3 rounded-md text-white font-medium transition-all">
                <i class="fas fa-chart-line mr-2"></i>Charts
            </button>
        </nav>

        <!-- Overview Tab -->
        <div x-show="activeTab === 'overview'" class="space-y-8">
            <!-- Portfolio Metrics -->
            <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div class="metric-card p-6 rounded-xl card-hover">
                    <div class="flex items-center justify-between mb-4">
                        <h3 class="text-gray-400 text-sm font-medium">Portfolio Value</h3>
                        <i class="fas fa-wallet text-green-400"></i>
                    </div>
                    <div class="text-3xl font-bold text-white" x-text="'$' + portfolio.total_value.toFixed(2)"></div>
                    <div class="text-green-400 text-sm mt-2">Live Balance</div>
                </div>
                
                <div class="metric-card p-6 rounded-xl card-hover">
                    <div class="flex items-center justify-between mb-4">
                        <h3 class="text-gray-400 text-sm font-medium">Total P&L</h3>
                        <i class="fas fa-chart-line text-blue-400"></i>
                    </div>
                    <div class="text-3xl font-bold" :class="portfolio.total_pnl >= 0 ? 'profit' : 'loss'" 
                         x-text="(portfolio.total_pnl >= 0 ? '+' : '') + '$' + portfolio.total_pnl.toFixed(2)"></div>
                    <div class="text-gray-400 text-sm mt-2">All Time</div>
                </div>
                
                <div class="metric-card p-6 rounded-xl card-hover">
                    <div class="flex items-center justify-between mb-4">
                        <h3 class="text-gray-400 text-sm font-medium">Active Trades</h3>
                        <i class="fas fa-exchange-alt text-yellow-400"></i>
                    </div>
                    <div class="text-3xl font-bold text-white" x-text="portfolio.active_positions"></div>
                    <div class="text-yellow-400 text-sm mt-2">Open Positions</div>
                </div>
                
                <div class="metric-card p-6 rounded-xl card-hover">
                    <div class="flex items-center justify-between mb-4">
                        <h3 class="text-gray-400 text-sm font-medium">Win Rate</h3>
                        <i class="fas fa-target text-purple-400"></i>
                    </div>
                    <div class="text-3xl font-bold text-white" x-text="portfolio.win_rate.toFixed(1) + '%'"></div>
                    <div class="text-purple-400 text-sm mt-2">Success Rate</div>
                </div>
            </div>

            <!-- Bot Status & Quick Actions -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div class="bg-gray-800 p-6 rounded-xl card-hover">
                    <h2 class="text-xl font-bold text-white mb-6 flex items-center">
                        <i class="fas fa-robot mr-3 text-green-400"></i>Bot Status
                    </h2>
                    <div class="space-y-4">
                        <div class="flex justify-between items-center">
                            <span class="text-gray-400">Status</span>
                            <div class="flex items-center">
                                <div class="status-indicator mr-2" :class="status.bot_running ? 'status-online' : 'status-offline'"></div>
                                <span class="font-bold" :class="status.bot_running ? 'text-green-400' : 'text-red-400'" 
                                      x-text="status.bot_running ? 'RUNNING' : 'STOPPED'"></span>
                            </div>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-400">Strategy</span>
                            <span class="font-bold text-white" x-text="status.strategy"></span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-400">Mode</span>
                            <span class="font-bold text-white" x-text="status.dry_run ? 'DRY RUN' : 'LIVE'"></span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-400">Exchange</span>
                            <span class="font-bold text-white" x-text="status.exchange"></span>
                        </div>
                    </div>
                </div>

                <div class="bg-gray-800 p-6 rounded-xl card-hover">
                    <h2 class="text-xl font-bold text-white mb-6 flex items-center">
                        <i class="fas fa-bell mr-3 text-yellow-400"></i>System Alerts
                    </h2>
                    <div id="alerts" class="space-y-2">
                        <div class="text-center text-gray-500">No active alerts</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Bot Control Tab -->
        <div x-show="activeTab === 'control'" class="space-y-8">
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <!-- Bot Controls -->
                <div class="bg-gray-800 p-6 rounded-xl card-hover">
                    <h2 class="text-xl font-bold text-white mb-6 flex items-center">
                        <i class="fas fa-play-circle mr-3 text-green-400"></i>Bot Controls
                    </h2>
                    <div class="grid grid-cols-2 gap-4 mb-6">
                        <button @click="startBot()" :disabled="status.bot_running" 
                                class="btn-success text-white px-4 py-3 rounded-lg font-semibold disabled:opacity-50">
                            <i class="fas fa-play mr-2"></i>Start Bot
                        </button>
                        <button @click="stopBot()" :disabled="!status.bot_running"
                                class="btn-danger text-white px-4 py-3 rounded-lg font-semibold disabled:opacity-50">
                            <i class="fas fa-stop mr-2"></i>Stop Bot
                        </button>
                        <button @click="reloadConfig()" 
                                class="btn-primary text-white px-4 py-3 rounded-lg font-semibold">
                            <i class="fas fa-sync mr-2"></i>Reload Config
                        </button>
                        <button @click="emergencyStop()" 
                                class="btn-danger text-white px-4 py-3 rounded-lg font-semibold bg-red-800">
                            <i class="fas fa-exclamation-triangle mr-2"></i>Emergency Stop
                        </button>
                    </div>
                </div>

                <!-- Strategy Configuration -->
                <div class="bg-gray-800 p-6 rounded-xl card-hover">
                    <h2 class="text-xl font-bold text-white mb-6 flex items-center">
                        <i class="fas fa-brain mr-3 text-purple-400"></i>Strategy Configuration
                    </h2>
                    <div class="space-y-4">
                        <div>
                            <label class="block text-gray-400 text-sm font-medium mb-2">Current Strategy</label>
                            <select x-model="selectedStrategy" @change="updateStrategy()" 
                                    class="w-full bg-gray-700 text-white p-3 rounded-lg border border-gray-600">
                                <template x-for="strategy in availableStrategies" :key="strategy">
                                    <option :value="strategy" x-text="strategy"></option>
                                </template>
                            </select>
                        </div>
                        <div class="grid grid-cols-2 gap-4">
                            <div>
                                <label class="block text-gray-400 text-sm font-medium mb-2">Max Open Trades</label>
                                <input x-model="maxOpenTrades" type="number" min="1" max="10" 
                                       class="w-full bg-gray-700 text-white p-3 rounded-lg border border-gray-600">
                            </div>
                            <div>
                                <label class="block text-gray-400 text-sm font-medium mb-2">Stake Amount</label>
                                <input x-model="stakeAmount" type="text" placeholder="unlimited" 
                                       class="w-full bg-gray-700 text-white p-3 rounded-lg border border-gray-600">
                            </div>
                        </div>
                        <button @click="updateTradingParams()" 
                                class="w-full btn-primary text-white p-3 rounded-lg font-semibold">
                            <i class="fas fa-save mr-2"></i>Update Parameters
                        </button>
                    </div>
                </div>
            </div>
            
            <!-- Advanced Trading Controls -->
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <!-- Manual Trading -->
                <div class="bg-gray-800 p-6 rounded-xl card-hover">
                    <h2 class="text-xl font-bold text-white mb-6 flex items-center">
                        <i class="fas fa-hand-paper mr-3 text-orange-400"></i>Manual Trading
                    </h2>
                    <div class="space-y-4">
                        <div>
                            <label class="block text-gray-400 text-sm font-medium mb-2">Pair</label>
                            <select x-model="selectedPair" class="w-full bg-gray-700 text-white p-3 rounded-lg border border-gray-600">
                                <option value="">Select pair...</option>
                                <option value="BTC/USDT">BTC/USDT</option>
                                <option value="ETH/USDT">ETH/USDT</option>
                                <option value="ADA/USDT">ADA/USDT</option>
                                <option value="SOL/USDT">SOL/USDT</option>
                                <option value="DOT/USDT">DOT/USDT</option>
                                <option value="LINK/USDT">LINK/USDT</option>
                                <option value="AVAX/USDT">AVAX/USDT</option>
                                <option value="UNI/USDT">UNI/USDT</option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-gray-400 text-sm font-medium mb-2">Stake Amount (optional)</label>
                            <input x-model="manualStakeAmount" type="number" step="0.01" placeholder="Use default" 
                                   class="w-full bg-gray-700 text-white p-3 rounded-lg border border-gray-600">
                        </div>
                        <div class="grid grid-cols-2 gap-3">
                            <button @click="forceBuy()" :disabled="!selectedPair" 
                                    class="btn-success text-white px-4 py-2 rounded-lg font-semibold disabled:opacity-50">
                                <i class="fas fa-plus mr-2"></i>Force Buy
                            </button>
                            <button @click="forceSell()" :disabled="!selectedPair"
                                    class="btn-danger text-white px-4 py-2 rounded-lg font-semibold disabled:opacity-50">
                                <i class="fas fa-minus mr-2"></i>Force Sell
                            </button>
                        </div>
                        <button @click="closeAllPositions()" 
                                class="w-full btn-danger text-white p-3 rounded-lg font-semibold bg-red-800">
                            <i class="fas fa-times-circle mr-2"></i>Close All Positions
                        </button>
                    </div>
                </div>

                <!-- Whitelist Management -->
                <div class="bg-gray-800 p-6 rounded-xl card-hover">
                    <h2 class="text-xl font-bold text-white mb-6 flex items-center">
                        <i class="fas fa-list mr-3 text-blue-400"></i>Whitelist Management
                    </h2>
                    <div class="space-y-4">
                        <div class="max-h-60 overflow-y-auto">
                            <div class="text-sm text-gray-400 mb-2">Active Trading Pairs:</div>
                            <template x-for="pair in whitelist" :key="pair">
                                <div class="flex justify-between items-center bg-gray-700 p-2 rounded mb-2">
                                    <span class="text-white" x-text="pair"></span>
                                    <button @click="removePairFromWhitelist(pair)" 
                                            class="text-red-400 hover:text-red-300 text-sm">
                                        <i class="fas fa-times"></i>
                                    </button>
                                </div>
                            </template>
                        </div>
                        <div>
                            <input x-model="newPair" type="text" placeholder="Add new pair (e.g. DOGE/USDT)" 
                                   class="w-full bg-gray-700 text-white p-3 rounded-lg border border-gray-600 mb-2">
                            <button @click="addPairToWhitelist()" :disabled="!newPair" 
                                    class="w-full btn-primary text-white p-2 rounded-lg font-semibold disabled:opacity-50">
                                <i class="fas fa-plus mr-2"></i>Add Pair
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Pause/Resume Pair Management -->
                <div class="bg-gray-800 p-6 rounded-xl card-hover">
                    <h2 class="text-xl font-bold text-white mb-6 flex items-center">
                        <i class="fas fa-pause-circle mr-3 text-yellow-400"></i>Pair Control
                    </h2>
                    
                    <!-- Paused Pairs List -->
                    <div class="mb-4">
                        <div class="text-sm text-gray-400 mb-2">Currently Paused Pairs:</div>
                        <div class="max-h-40 overflow-y-auto">
                            <template x-for="pausedPair in pausedPairs" :key="pausedPair.pair">
                                <div class="flex justify-between items-center bg-red-900 bg-opacity-50 p-2 rounded mb-2">
                                    <div>
                                        <div class="text-white font-semibold" x-text="pausedPair.pair"></div>
                                        <div class="text-xs text-gray-400" x-text="pausedPair.reason"></div>
                                    </div>
                                    <button @click="resumePair(pausedPair.pair)" 
                                            class="text-green-400 hover:text-green-300 text-sm px-2 py-1 bg-green-800 bg-opacity-30 rounded">
                                        <i class="fas fa-play mr-1"></i>Resume
                                    </button>
                                </div>
                            </template>
                            <div x-show="pausedPairs.length === 0" class="text-center text-gray-500 py-4">
                                No pairs are currently paused
                            </div>
                        </div>
                    </div>
                    
                    <!-- Pause Pair Controls -->
                    <div class="border-t border-gray-700 pt-4">
                        <div class="text-sm text-gray-400 mb-2">Pause Trading on Pair:</div>
                        <select x-model="selectedPairToPause" class="w-full bg-gray-700 text-white p-3 rounded-lg border border-gray-600 mb-2">
                            <option value="">Select pair to pause...</option>
                            <template x-for="pair in whitelist" :key="pair">
                                <option :value="pair" x-text="pair"></option>
                            </template>
                        </select>
                        <button @click="pausePair()" :disabled="!selectedPairToPause" 
                                class="w-full btn-warning text-white p-2 rounded-lg font-semibold disabled:opacity-50">
                            <i class="fas fa-pause mr-2"></i>Pause Pair
                        </button>
                    </div>
                </div>

                <!-- Live Parameter Tuning -->
                <div class="bg-gray-800 p-6 rounded-xl card-hover">
                    <h2 class="text-xl font-bold text-white mb-6 flex items-center">
                        <i class="fas fa-sliders-h mr-3 text-purple-400"></i>Live Parameter Tuning
                    </h2>
                    
                    <!-- Parameter Categories -->
                    <div class="space-y-4">
                        <!-- Buy Parameters -->
                        <div class="bg-gray-700 p-4 rounded-lg">
                            <h3 class="text-white font-semibold mb-3 flex items-center">
                                <i class="fas fa-arrow-up text-green-400 mr-2"></i>Buy Parameters
                            </h3>
                            <div class="grid grid-cols-2 gap-3">
                                <div>
                                    <label class="block text-gray-400 text-xs font-medium mb-1">RSI Buy Level</label>
                                    <input x-model="strategyParams.buy_params.rsi_buy" type="number" min="10" max="50" 
                                           class="w-full bg-gray-600 text-white p-2 rounded border border-gray-500 text-sm">
                                </div>
                                <div>
                                    <label class="block text-gray-400 text-xs font-medium mb-1">Volume Factor</label>
                                    <input x-model="strategyParams.buy_params.volume_factor" type="number" step="0.1" min="1" max="3" 
                                           class="w-full bg-gray-600 text-white p-2 rounded border border-gray-500 text-sm">
                                </div>
                                <div>
                                    <label class="block text-gray-400 text-xs font-medium mb-1">MACD Threshold</label>
                                    <input x-model="strategyParams.buy_params.macd_threshold" type="number" step="0.001" 
                                           class="w-full bg-gray-600 text-white p-2 rounded border border-gray-500 text-sm">
                                </div>
                                <div>
                                    <label class="block text-gray-400 text-xs font-medium mb-1">BB Lower Factor</label>
                                    <input x-model="strategyParams.buy_params.bb_lower_factor" type="number" step="0.01" min="0.9" max="1.0" 
                                           class="w-full bg-gray-600 text-white p-2 rounded border border-gray-500 text-sm">
                                </div>
                            </div>
                        </div>
                        
                        <!-- Sell Parameters -->
                        <div class="bg-gray-700 p-4 rounded-lg">
                            <h3 class="text-white font-semibold mb-3 flex items-center">
                                <i class="fas fa-arrow-down text-red-400 mr-2"></i>Sell Parameters
                            </h3>
                            <div class="grid grid-cols-2 gap-3">
                                <div>
                                    <label class="block text-gray-400 text-xs font-medium mb-1">RSI Sell Level</label>
                                    <input x-model="strategyParams.sell_params.rsi_sell" type="number" min="50" max="90" 
                                           class="w-full bg-gray-600 text-white p-2 rounded border border-gray-500 text-sm">
                                </div>
                                <div>
                                    <label class="block text-gray-400 text-xs font-medium mb-1">Profit Target (%)</label>
                                    <input x-model="strategyParams.sell_params.profit_target" type="number" step="0.01" min="0.01" max="0.20" 
                                           class="w-full bg-gray-600 text-white p-2 rounded border border-gray-500 text-sm">
                                </div>
                                <div>
                                    <label class="block text-gray-400 text-xs font-medium mb-1">Stop Loss (%)</label>
                                    <input x-model="strategyParams.sell_params.stop_loss" type="number" step="0.01" min="-0.20" max="-0.01" 
                                           class="w-full bg-gray-600 text-white p-2 rounded border border-gray-500 text-sm">
                                </div>
                                <div>
                                    <label class="block text-gray-400 text-xs font-medium mb-1">Trailing Stop (%)</label>
                                    <input x-model="strategyParams.sell_params.trailing_stop" type="number" step="0.01" min="0.01" max="0.10" 
                                           class="w-full bg-gray-600 text-white p-2 rounded border border-gray-500 text-sm">
                                </div>
                            </div>
                        </div>
                        
                        <!-- Risk Parameters -->
                        <div class="bg-gray-700 p-4 rounded-lg">
                            <h3 class="text-white font-semibold mb-3 flex items-center">
                                <i class="fas fa-shield-alt text-yellow-400 mr-2"></i>Risk Parameters
                            </h3>
                            <div class="grid grid-cols-2 gap-3">
                                <div>
                                    <label class="block text-gray-400 text-xs font-medium mb-1">Max Open Trades</label>
                                    <input x-model="strategyParams.risk_params.max_open_trades" type="number" min="1" max="10" 
                                           class="w-full bg-gray-600 text-white p-2 rounded border border-gray-500 text-sm">
                                </div>
                                <div>
                                    <label class="block text-gray-400 text-xs font-medium mb-1">Stop Loss (%)</label>
                                    <input x-model="strategyParams.risk_params.stoploss" type="number" step="0.01" min="-0.50" max="-0.01" 
                                           class="w-full bg-gray-600 text-white p-2 rounded border border-gray-500 text-sm">
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Action Buttons -->
                    <div class="grid grid-cols-2 gap-3 mt-4">
                        <button @click="updateStrategyParameters()" 
                                class="btn-success text-white px-4 py-2 rounded-lg font-semibold">
                            <i class="fas fa-save mr-2"></i>Apply Changes
                        </button>
                        <button @click="resetStrategyParameters()" 
                                class="btn-warning text-white px-4 py-2 rounded-lg font-semibold">
                            <i class="fas fa-undo mr-2"></i>Reset to Defaults
                        </button>
                    </div>
                    
                    <!-- Parameter Status -->
                    <div x-show="parameterUpdateStatus" class="mt-3 p-2 rounded text-sm" 
                         :class="parameterUpdateSuccess ? 'bg-green-800 text-green-200' : 'bg-red-800 text-red-200'">
                        <span x-text="parameterUpdateStatus"></span>
                    </div>
                </div>

                <!-- System Health -->
                <div class="bg-gray-800 p-6 rounded-xl card-hover">
                    <h2 class="text-xl font-bold text-white mb-6 flex items-center">
                        <i class="fas fa-heartbeat mr-3 text-red-400"></i>System Health
                    </h2>
                    <div class="space-y-4">
                        <div class="grid grid-cols-2 gap-4">
                            <div class="text-center">
                                <div class="text-2xl font-bold text-white" x-text="systemHealth.cpu_percent + '%'"></div>
                                <div class="text-xs text-gray-400">CPU Usage</div>
                            </div>
                            <div class="text-center">
                                <div class="text-2xl font-bold text-white" x-text="systemHealth.memory_percent + '%'"></div>
                                <div class="text-xs text-gray-400">Memory Usage</div>
                            </div>
                        </div>
                        <div class="space-y-2 text-sm">
                            <div class="flex justify-between">
                                <span class="text-gray-400">Memory Used:</span>
                                <span class="text-white" x-text="systemHealth.memory_used_gb + ' GB'"></span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-400">Disk Free:</span>
                                <span class="text-white" x-text="systemHealth.disk_free_gb + ' GB'"></span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-400">Uptime:</span>
                                <span class="text-white" x-text="systemHealth.uptime_hours + ' hrs'"></span>
                            </div>
                        </div>
                        <button @click="refreshSystemHealth()" 
                                class="w-full btn-primary text-white p-2 rounded-lg font-semibold">
                            <i class="fas fa-sync mr-2"></i>Refresh
                        </button>
                    </div>
                </div>
            </div>

            <!-- Configuration Editor & Logs -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <!-- Live Configuration Editor -->
                <div class="bg-gray-800 p-6 rounded-xl card-hover">
                    <h2 class="text-xl font-bold text-white mb-6 flex items-center">
                        <i class="fas fa-cog mr-3 text-green-400"></i>Configuration Editor
                    </h2>
                    <div class="space-y-4">
                        <div class="grid grid-cols-2 gap-4">
                            <div>
                                <label class="block text-gray-400 text-sm font-medium mb-2">Dry Run</label>
                                <select x-model="configEditor.dry_run" class="w-full bg-gray-700 text-white p-3 rounded-lg border border-gray-600">
                                    <option value="true">Yes (Safe Mode)</option>
                                    <option value="false">No (Live Trading)</option>
                                </select>
                            </div>
                            <div>
                                <label class="block text-gray-400 text-sm font-medium mb-2">Timeframe</label>
                                <select x-model="configEditor.timeframe" class="w-full bg-gray-700 text-white p-3 rounded-lg border border-gray-600">
                                    <option value="1m">1 minute</option>
                                    <option value="5m">5 minutes</option>
                                    <option value="15m">15 minutes</option>
                                    <option value="1h">1 hour</option>
                                    <option value="4h">4 hours</option>
                                    <option value="1d">1 day</option>
                                </select>
                            </div>
                        </div>
                        <div class="grid grid-cols-2 gap-4">
                            <div>
                                <label class="block text-gray-400 text-sm font-medium mb-2">Max Open Trades</label>
                                <input x-model="configEditor.max_open_trades" type="number" min="1" max="20" 
                                       class="w-full bg-gray-700 text-white p-3 rounded-lg border border-gray-600">
                            </div>
                            <div>
                                <label class="block text-gray-400 text-sm font-medium mb-2">Stake Currency</label>
                                <select x-model="configEditor.stake_currency" class="w-full bg-gray-700 text-white p-3 rounded-lg border border-gray-600">
                                    <option value="USDT">USDT</option>
                                    <option value="BUSD">BUSD</option>
                                    <option value="BTC">BTC</option>
                                    <option value="ETH">ETH</option>
                                </select>
                            </div>
                        </div>
                        <button @click="updateConfiguration()" 
                                class="w-full btn-success text-white p-3 rounded-lg font-semibold">
                            <i class="fas fa-save mr-2"></i>Save Configuration
                        </button>
                    </div>
                </div>

                <!-- Live Log Viewer -->
                <div class="bg-gray-800 p-6 rounded-xl card-hover">
                    <h2 class="text-xl font-bold text-white mb-6 flex items-center">
                        <i class="fas fa-terminal mr-3 text-yellow-400"></i>Live Logs
                    </h2>
                    <div class="space-y-4">
                        <div class="flex gap-2">
                            <button @click="refreshLogs()" 
                                    class="btn-primary text-white px-4 py-2 rounded-lg font-semibold text-sm">
                                <i class="fas fa-sync mr-1"></i>Refresh
                            </button>
                            <select x-model="logLimit" @change="refreshLogs()" 
                                    class="bg-gray-700 text-white px-3 py-2 rounded-lg border border-gray-600 text-sm">
                                <option value="50">50 lines</option>
                                <option value="100">100 lines</option>
                                <option value="200">200 lines</option>
                            </select>
                        </div>
                        <div class="bg-black p-4 rounded-lg h-80 overflow-y-auto text-xs font-mono">
                            <template x-for="log in logs" :key="log.timestamp">
                                <div class="text-green-400 mb-1" x-text="log.message || 'Loading logs...'"></div>
                            </template>
                            <div x-show="logs.length === 0" class="text-gray-500 text-center py-8">
                                No logs available
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Trading Tab -->
        <div x-show="activeTab === 'trading'" class="space-y-8">
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <!-- Active Trades -->
                <div class="bg-gray-800 p-6 rounded-xl card-hover">
                    <h2 class="text-xl font-bold text-white mb-6 flex items-center">
                        <i class="fas fa-chart-line mr-3 text-green-400"></i>Active Trades
                    </h2>
                    <div class="space-y-3">
                        <template x-for="trade in activeTrades" :key="trade.trade_id">
                            <div class="bg-gray-700 p-4 rounded-lg flex justify-between items-center">
                                <div>
                                    <div class="font-semibold text-white" x-text="trade.pair"></div>
                                    <div class="text-sm text-gray-400" x-text="'ID: ' + trade.trade_id"></div>
                                </div>
                                <div class="text-right">
                                    <div class="font-bold" :class="trade.profit_abs >= 0 ? 'profit' : 'loss'" 
                                         x-text="'$' + trade.profit_abs.toFixed(2)"></div>
                                    <button @click="forceExitTrade(trade.trade_id)" 
                                            class="text-red-400 hover:text-red-300 text-sm mt-1">
                                        <i class="fas fa-times mr-1"></i>Close
                                    </button>
                                </div>
                            </div>
                        </template>
                        <div x-show="activeTrades.length === 0" class="text-center text-gray-500 py-8">
                            No active trades
                        </div>
                    </div>
                </div>

                <!-- Trade History -->
                <div class="bg-gray-800 p-6 rounded-xl card-hover">
                    <h2 class="text-xl font-bold text-white mb-6 flex items-center">
                        <i class="fas fa-history mr-3 text-blue-400"></i>Recent Trades
                    </h2>
                    <div class="space-y-3">
                        <template x-for="trade in tradeHistory.slice(0, 10)" :key="trade.trade_id">
                            <div class="bg-gray-700 p-3 rounded-lg flex justify-between items-center">
                                <div>
                                    <div class="font-semibold text-white" x-text="trade.pair"></div>
                                    <div class="text-xs text-gray-400" x-text="new Date(trade.close_date).toLocaleDateString()"></div>
                                </div>
                                <div class="text-right">
                                    <div class="font-bold" :class="trade.profit_abs >= 0 ? 'profit' : 'loss'" 
                                         x-text="'$' + trade.profit_abs.toFixed(2)"></div>
                                </div>
                            </div>
                        </template>
                    </div>
                </div>
            </div>

            <!-- Trade Journey Timeline -->
            <div class="bg-gray-800 p-6 rounded-xl card-hover">
                <h2 class="text-xl font-bold text-white mb-6 flex items-center">
                    <i class="fas fa-route mr-3 text-cyan-400"></i>Trade Journey Timeline
                </h2>
                
                <!-- Trade Selection -->
                <div class="mb-4">
                    <select x-model="selectedTradeId" @change="loadTradeJourney()" 
                            class="w-full bg-gray-700 text-white p-3 rounded-lg border border-gray-600">
                        <option value="">Select a completed trade...</option>
                        <template x-for="trade in recentTradeJourneys" :key="trade.trade_id">
                            <option :value="trade.trade_id" x-text="`${trade.pair} - $${trade.profit_abs.toFixed(2)} (${new Date(trade.close_date).toLocaleDateString()})`"></option>
                        </template>
                    </select>
                </div>

                <!-- Timeline Display -->
                <div x-show="currentTradeJourney" class="space-y-4">
                    <!-- Trade Summary -->
                    <div x-show="currentTradeJourney" class="bg-gray-700 p-4 rounded-lg mb-4">
                        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 text-sm">
                            <div>
                                <span class="text-gray-400">Pair:</span>
                                <span class="text-white font-semibold ml-2" x-text="currentTradeJourney?.trade_summary?.pair"></span>
                            </div>
                            <div>
                                <span class="text-gray-400">Strategy:</span>
                                <span class="text-white font-semibold ml-2" x-text="currentTradeJourney?.trade_summary?.strategy"></span>
                            </div>
                            <div>
                                <span class="text-gray-400">Duration:</span>
                                <span class="text-white font-semibold ml-2" x-text="currentTradeJourney?.trade_summary?.duration"></span>
                            </div>
                            <div>
                                <span class="text-gray-400">Final P&L:</span>
                                <span class="font-semibold ml-2" 
                                      :class="currentTradeJourney?.trade_summary?.profit_abs >= 0 ? 'profit' : 'loss'" 
                                      x-text="'$' + currentTradeJourney?.trade_summary?.profit_abs?.toFixed(2)"></span>
                            </div>
                        </div>
                    </div>

                    <!-- Timeline Events -->
                    <div class="relative">
                        <!-- Timeline Line -->
                        <div class="absolute left-6 top-0 bottom-0 w-0.5 bg-gray-600"></div>
                        
                        <template x-for="(event, index) in currentTradeJourney?.timeline" :key="index">
                            <div class="relative flex items-start mb-6">
                                <!-- Timeline Dot -->
                                <div class="flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center mr-4 text-white text-sm font-bold"
                                     :class="{
                                         'bg-green-500': event.event_type === 'entry',
                                         'bg-blue-500': event.event_type === 'peak' || event.event_type === 'trough',
                                         'bg-red-500': event.event_type === 'exit',
                                         'bg-yellow-500': event.event_type === 'signal'
                                     }">
                                    <i :class="{
                                         'fas fa-play': event.event_type === 'entry',
                                         'fas fa-arrow-up': event.event_type === 'peak',
                                         'fas fa-arrow-down': event.event_type === 'trough',
                                         'fas fa-stop': event.event_type === 'exit',
                                         'fas fa-bell': event.event_type === 'signal'
                                     }"></i>
                                </div>
                                
                                <!-- Event Content -->
                                <div class="flex-grow bg-gray-700 p-4 rounded-lg">
                                    <div class="flex justify-between items-start mb-2">
                                        <h4 class="text-white font-semibold" x-text="event.title"></h4>
                                        <span class="text-gray-400 text-sm" x-text="new Date(event.timestamp * 1000).toLocaleString()"></span>
                                    </div>
                                    
                                    <p class="text-gray-300 text-sm mb-3" x-text="event.description"></p>
                                    
                                    <!-- Price & P&L Info -->
                                    <div class="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
                                        <div>
                                            <span class="text-gray-400">Price:</span>
                                            <span class="text-white font-semibold ml-2" x-text="'$' + event.price?.toFixed(4)"></span>
                                        </div>
                                        <div x-show="event.unrealized_pnl !== undefined">
                                            <span class="text-gray-400">Unrealized P&L:</span>
                                            <span class="font-semibold ml-2" 
                                                  :class="event.unrealized_pnl >= 0 ? 'profit' : 'loss'" 
                                                  x-text="'$' + event.unrealized_pnl?.toFixed(2)"></span>
                                        </div>
                                        <div x-show="event.realized_pnl !== undefined">
                                            <span class="text-gray-400">Realized P&L:</span>
                                            <span class="font-semibold ml-2" 
                                                  :class="event.realized_pnl >= 0 ? 'profit' : 'loss'" 
                                                  x-text="'$' + event.realized_pnl?.toFixed(2)"></span>
                                        </div>
                                    </div>
                                    
                                    <!-- Decision Factors -->
                                    <div x-show="event.decision_factors" class="mt-3 pt-3 border-t border-gray-600">
                                        <h5 class="text-gray-400 text-xs font-semibold mb-2">DECISION FACTORS:</h5>
                                        <div class="grid grid-cols-2 gap-2 text-xs">
                                            <template x-for="(value, key) in event.decision_factors" :key="key">
                                                <div class="flex justify-between">
                                                    <span class="text-gray-400 capitalize" x-text="key.replace('_', ' ')"></span>
                                                    <span class="text-white font-semibold" x-text="value"></span>
                                                </div>
                                            </template>
                                        </div>
                                    </div>
                                    
                                    <!-- Technical Indicators -->
                                    <div x-show="event.technical_indicators" class="mt-3 pt-3 border-t border-gray-600">
                                        <h5 class="text-gray-400 text-xs font-semibold mb-2">TECHNICAL INDICATORS:</h5>
                                        <div class="grid grid-cols-3 gap-2 text-xs">
                                            <template x-for="(value, key) in event.technical_indicators" :key="key">
                                                <div class="text-center">
                                                    <div class="text-gray-400 uppercase" x-text="key"></div>
                                                    <div class="text-white font-bold" x-text="typeof value === 'number' ? value.toFixed(2) : value"></div>
                                                </div>
                                            </template>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </template>
                    </div>
                </div>
                
                <!-- No Trade Selected Message -->
                <div x-show="!currentTradeJourney" class="text-center py-8 text-gray-400">
                    <i class="fas fa-route text-4xl mb-4"></i>
                    <p>Select a completed trade to view its journey timeline</p>
                </div>
            </div>
        </div>

        <!-- Market Tab -->
        <div x-show="activeTab === 'market'" class="space-y-8">
            <!-- Market Sub-navigation -->
            <div class="flex space-x-1 mb-4 bg-gray-700 p-1 rounded-lg">
                <button @click="marketTab = 'overview'" :class="marketTab === 'overview' ? 'nav-tab active' : 'nav-tab'" class="px-4 py-2 rounded-md text-white font-medium transition-all text-sm">
                    <i class="fas fa-globe mr-2"></i>Market Overview
                </button>
                <button @click="marketTab = 'openbb'" :class="marketTab === 'openbb' ? 'nav-tab active' : 'nav-tab'" class="px-4 py-2 rounded-md text-white font-medium transition-all text-sm">
                    <i class="fas fa-rocket mr-2"></i>OpenBB Analysis
                </button>
            </div>

            <!-- Market Overview Content -->
            <div x-show="marketTab === 'overview'" class="space-y-8">
                <!-- Market Overview -->
                <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <div class="metric-card p-6 rounded-xl card-hover">
                        <h3 class="text-gray-400 text-sm font-medium mb-2">Fear & Greed Index</h3>
                        <div class="text-2xl font-bold text-white" x-text="marketOverview.fear_greed?.value || '--'"></div>
                        <div class="text-sm mt-1" x-text="marketOverview.fear_greed?.classification || 'Neutral'"></div>
                    </div>
                    <div class="metric-card p-6 rounded-xl card-hover">
                        <h3 class="text-gray-400 text-sm font-medium mb-2">Total Market Cap</h3>
                        <div class="text-2xl font-bold text-white" x-text="formatLargeNumber(marketOverview.total_market_cap)"></div>
                        <div class="text-sm mt-1 text-gray-400">USD</div>
                    </div>
                    <div class="metric-card p-6 rounded-xl card-hover">
                        <h3 class="text-gray-400 text-sm font-medium mb-2">24h Volume</h3>
                        <div class="text-2xl font-bold text-white" x-text="formatLargeNumber(marketOverview.total_volume)"></div>
                        <div class="text-sm mt-1 text-gray-400">USD</div>
                    </div>
                    <div class="metric-card p-6 rounded-xl card-hover">
                        <h3 class="text-gray-400 text-sm font-medium mb-2">BTC Dominance</h3>
                        <div class="text-2xl font-bold text-white" x-text="(marketOverview.bitcoin_dominance || 0).toFixed(1) + '%'"></div>
                        <div class="text-sm mt-1 text-gray-400">Market Share</div>
                    </div>
                </div>

                <!-- Live Prices -->
                <div class="bg-gray-800 p-6 rounded-xl card-hover">
                    <h2 class="text-xl font-bold text-white mb-6 flex items-center">
                        <i class="fas fa-coins mr-3 text-yellow-400"></i>Live Prices
                    </h2>
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        <template x-for="[pair, data] in Object.entries(marketPrices)" :key="pair">
                            <div class="bg-gray-700 p-4 rounded-lg">
                                <div class="flex justify-between items-center mb-2">
                                    <span class="font-semibold text-white" x-text="pair"></span>
                                    <span class="text-sm text-gray-400" x-text="data.name"></span>
                                </div>
                                <div class="text-xl font-bold text-white" x-text="'$' + data.price.toLocaleString()"></div>
                                <div class="text-sm" :class="data.change_24h >= 0 ? 'profit' : 'loss'" 
                                     x-text="(data.change_24h >= 0 ? '+' : '') + data.change_24h.toFixed(2) + '%'"></div>
                            </div>
                        </template>
                    </div>
                </div>
            </div>

            <!-- OpenBB Analysis Content -->
            <div x-show="marketTab === 'openbb'" class="space-y-8">
                <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    <!-- Whale Activity -->
                    <div class="bg-gray-800 p-6 rounded-xl card-hover">
                        <h2 class="text-xl font-bold text-white mb-6 flex items-center">
                            <i class="fas fa-fish mr-3 text-blue-400"></i>Whale Activity
                        </h2>
                        <div class="space-y-4">
                            <template x-for="(data, symbol) in openbbCryptoData.whale_activity" :key="symbol">
                                <div class="bg-gray-700 p-4 rounded-lg">
                                    <div class="flex justify-between items-center mb-2">
                                        <span class="font-semibold text-white" x-text="symbol"></span>
                                        <span class="text-sm text-gray-400" x-text="data.action_recommendation"></span>
                                    </div>
                                    <div class="text-sm">
                                        <span class="text-gray-400">Large Transactions:</span>
                                        <span class="font-semibold" x-text="data.large_transactions"></span>
                                    </div>
                                    <div class="text-sm">
                                        <span class="text-gray-400">Exchange Flow:</span>
                                        <span class="font-semibold" x-text="data.exchange_flow"></span>
                                    </div>
                                </div>
                            </template>
                        </div>
                    </div>

                    <!-- DeFi Opportunities -->
                    <div class="bg-gray-800 p-6 rounded-xl card-hover">
                        <h2 class="text-xl font-bold text-white mb-6 flex items-center">
                        <i class="fas fa-hand-holding-usd mr-3 text-green-400"></i>DeFi Opportunities
                        </h2>
                        <div class="space-y-3">
                            <template x-for="opportunity in openbbCryptoData.defi_opportunities" :key="opportunity.protocol + opportunity.asset">
                                <div class="bg-gray-700 p-3 rounded-lg">
                                    <div class="flex justify-between items-center">
                                        <div>
                                            <span class="font-semibold text-white" x-text="opportunity.protocol + ' - ' + opportunity.asset"></span>
                                            <span class="text-xs text-gray-400 ml-2" x-text="'TVL: ' + opportunity.tvl"></span>
                                        </div>
                                        <span class="font-bold text-green-400" x-text="opportunity.apy + '% APY'"></span>
                                    </div>
                                    <div class="text-sm text-gray-400 mt-1">
                                        Risk: <span x-text="opportunity.risk"></span> - Action: <span x-text="opportunity.action"></span>
                                    </div>
                                </div>
                            </template>
                        </div>
                    </div>

                    <!-- Actionable Signals -->
                    <div class="bg-gray-800 p-6 rounded-xl card-hover">
                        <h2 class="text-xl font-bold text-white mb-6 flex items-center">
                            <i class="fas fa-lightbulb mr-3 text-yellow-400"></i>Actionable Signals
                        </h2>
                        <div class="space-y-3">
                            <template x-for="signal in openbbCryptoData.actionable_signals" :key="signal.symbol + signal.timeframe">
                                <div class="bg-gray-700 p-3 rounded-lg">
                                    <div class="flex justify-between items-center">
                                        <span class="font-semibold text-white" x-text="signal.symbol + ' (' + signal.timeframe + ')'"></span>
                                        <span class="font-bold" :class="signal.signal === 'BUY' ? 'text-green-400' : 'text-red-400'" x-text="signal.signal"></span>
                                    </div>
                                    <div class="text-sm text-gray-400 mt-1">
                                        <span x-text="signal.reason"></span>
                                        <span class="text-xs text-gray-500 ml-2" x-text="'Confidence: ' + signal.confidence"></span>
                                    </div>
                                </div>
                            </template>
                        </div>
                    </div>
                </div>
                <div class="bg-gray-800 p-6 rounded-xl card-hover">
                    <h2 class="text-xl font-bold text-white mb-6 flex items-center">
                        <i class="fas fa-chart-bar mr-3 text-purple-400"></i>Technical Indicators
                    </h2>
                    <div class="space-y-4">
                        <template x-for="(values, indicator) in openbbTechnicalsData" :key="indicator">
                            <div class="bg-gray-700 p-4 rounded-lg">
                                <h3 class="font-semibold text-white mb-2" x-text="indicator.toUpperCase()"></h3>
                                <div class="text-sm text-gray-400">
                                    <pre x-text="JSON.stringify(values, null, 2)"></pre>
                                </div>
                            </div>
                        </template>
                    </div>
                </div>
                 <div class="bg-gray-800 p-6 rounded-xl card-hover">
                    <h2 class="text-xl font-bold text-white mb-6 flex items-center">
                        <i class="fas fa-chart-pie mr-3 text-indigo-400"></i>Sector Rotation
                    </h2>
                    <div class="space-y-4">
                        <template x-for="(value, sector) in openbbSectorRotationData" :key="sector">
                            <div class="bg-gray-700 p-4 rounded-lg">
                                <div class="flex justify-between items-center">
                                    <span class="font-semibold text-white" x-text="sector"></span>
                                    <span class="font-bold" :class="value > 0 ? 'text-green-400' : 'text-red-400'" x-text="(value * 100).toFixed(2) + '%'"></span>
                                </div>
                            </div>
                        </template>
                    </div>
                </div>
            </div>
        </div>

        <!-- Trade Logic Tab -->
        <div x-show="activeTab === 'logic'" class="space-y-8">
            <!-- Live Trade Reasoning Panel -->
            <div class="bg-gray-800 p-6 rounded-xl card-hover">
                <h2 class="text-xl font-bold text-white mb-6 flex items-center">
                    <i class="fas fa-brain mr-3 text-purple-400"></i>Live Trade Reasoning
                </h2>
                <div id="trade-reasoning" class="space-y-4">
                    <div class="bg-gray-700 p-4 rounded-lg">
                        <div class="flex items-center justify-between mb-2">
                            <span class="text-green-400 font-semibold">📈 MEAN REVERSION ANALYSIS</span>
                            <span class="text-gray-400 text-sm" x-text="new Date().toLocaleTimeString()"></span>
                        </div>
                        <div class="text-gray-300 text-sm">
                            Strategy detecting BB Upper Touch signals - prices hitting resistance levels
                        </div>
                    </div>
                </div>
            </div>

            <!-- Technical Indicators Dashboard -->
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div class="bg-gray-800 p-6 rounded-xl card-hover">
                    <h3 class="text-lg font-bold text-white mb-4 flex items-center">
                        <i class="fas fa-chart-line mr-2 text-blue-400"></i>RSI Levels
                    </h3>
                    <div id="rsi-indicators" class="space-y-3">
                        <template x-for="(data, pair) in tradeLogic.indicators" :key="pair">
                            <div class="flex justify-between items-center">
                                <span class="text-gray-400" x-text="pair"></span>
                                <div class="flex items-center">
                                    <span class="text-white font-mono" x-text="data.rsi"></span>
                                    <div class="ml-2 w-2 h-2 rounded-full" 
                                         :class="data.rsi < 30 ? 'bg-green-400' : data.rsi > 70 ? 'bg-red-400' : 'bg-yellow-400'"></div>
                                </div>
                            </div>
                        </template>
                    </div>
                    <div class="mt-4 pt-4 border-t border-gray-700">
                        <div class="text-xs text-gray-500">Entry: &lt;30 | Exit: &gt;70</div>
                    </div>
                </div>

                <div class="bg-gray-800 p-6 rounded-xl card-hover">
                    <h3 class="text-lg font-bold text-white mb-4 flex items-center">
                        <i class="fas fa-wave-square mr-2 text-green-400"></i>MACD Signals
                    </h3>
                    <div id="macd-indicators" class="space-y-3">
                        <template x-for="(data, pair) in tradeLogic.indicators" :key="pair">
                            <div class="flex justify-between items-center">
                                <span class="text-gray-400" x-text="pair"></span>
                                <div class="flex items-center">
                                    <span class="text-white font-mono" x-text="data.macd"></span>
                                    <div class="ml-2 w-2 h-2 rounded-full" 
                                         :class="data.macd > data.macd_signal ? 'bg-green-400' : 'bg-red-400'"></div>
                                </div>
                            </div>
                        </template>
                    </div>
                    <div class="mt-4 pt-4 border-t border-gray-700">
                        <div class="text-xs text-gray-500">Bullish: MACD > Signal</div>
                    </div>
                </div>

                <div class="bg-gray-800 p-6 rounded-xl card-hover">
                    <h3 class="text-lg font-bold text-white mb-4 flex items-center">
                        <i class="fas fa-expand-arrows-alt mr-2 text-purple-400"></i>Bollinger Bands
                    </h3>
                    <div id="bb-indicators" class="space-y-3">
                        <template x-for="(data, pair) in tradeLogic.indicators" :key="pair">
                            <div class="flex justify-between items-center">
                                <span class="text-gray-400" x-text="pair"></span>
                                <div class="flex items-center">
                                    <span class="text-white font-mono" x-text="data.bb_position + '%'"></span>
                                    <div class="ml-2 w-2 h-2 rounded-full" 
                                         :class="data.bb_position < 20 ? 'bg-green-400' : data.bb_position > 80 ? 'bg-red-400' : 'bg-blue-400'"></div>
                                </div>
                            </div>
                        </template>
                    </div>
                    <div class="mt-4 pt-4 border-t border-gray-700">
                        <div class="text-xs text-gray-500">Entry: Near Lower | Exit: Upper Touch</div>
                    </div>
                </div>
            </div>

            <!-- Strategy Decision Tree -->
            <div class="bg-gray-800 p-6 rounded-xl card-hover">
                <h2 class="text-xl font-bold text-white mb-6 flex items-center">
                    <i class="fas fa-sitemap mr-3 text-green-400"></i>Active Strategy Decision Tree
                </h2>
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div class="bg-gray-700 p-4 rounded-lg">
                        <h4 class="text-white font-semibold mb-3">Market Condition Analysis</h4>
                        <div class="space-y-2">
                            <div class="flex justify-between">
                                <span class="text-gray-400">Volatility</span>
                                <span class="text-yellow-400 font-semibold" x-text="tradeLogic.strategyState.market_analysis?.volatility || 'MODERATE'"></span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-400">Trend Direction</span>
                                <span class="text-blue-400 font-semibold" x-text="tradeLogic.strategyState.market_analysis?.trend_direction || 'SIDEWAYS'"></span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-400">Volume</span>
                                <span class="text-green-400 font-semibold" x-text="tradeLogic.strategyState.market_analysis?.volume || 'NORMAL'"></span>
                            </div>
                        </div>
                    </div>
                    <div class="bg-gray-700 p-4 rounded-lg">
                        <h4 class="text-white font-semibold mb-3">Selected Strategy</h4>
                        <div class="text-center">
                            <div class="text-2xl text-purple-400 mb-2">📈</div>
                            <div class="text-white font-bold" x-text="tradeLogic.strategyState.market_analysis?.selected_strategy || 'MEAN REVERSION'"></div>
                            <div class="text-gray-400 text-sm mt-2" x-text="tradeLogic.strategyState.market_analysis?.reasoning || 'Loading strategy analysis...'">
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Recent Trade Decisions -->
            <div class="bg-gray-800 p-6 rounded-xl card-hover">
                <h2 class="text-xl font-bold text-white mb-6 flex items-center">
                    <i class="fas fa-history mr-3 text-blue-400"></i>Recent Trade Decisions
                </h2>
                <div class="space-y-4">
                    <template x-for="decision in tradeLogic.decisions" :key="decision.timestamp + decision.pair">
                        <div class="bg-gray-700 p-4 rounded-lg border-l-4" 
                             :class="decision.type === 'EXIT' ? 'border-red-400' : 'border-green-400'">
                            <div class="flex justify-between items-start mb-2">
                                <div class="flex items-center">
                                    <span class="font-semibold" 
                                          :class="decision.type === 'EXIT' ? 'text-red-400' : 'text-green-400'"
                                          x-text="(decision.type === 'EXIT' ? '📉 EXIT' : '📈 ENTRY')"></span>
                                    <span class="text-white font-bold ml-2" x-text="decision.pair"></span>
                                </div>
                                <span class="text-gray-400 text-sm" x-text="decision.timestamp"></span>
                            </div>
                            <div class="text-gray-300 text-sm mb-1">
                                <strong>Reason:</strong> <span x-text="decision.reason"></span>
                            </div>
                            <div class="text-gray-400 text-xs">
                                Strategy: <span x-text="decision.strategy"></span> | 
                                RSI: <span x-text="decision.details?.rsi"></span> | 
                                BB Position: <span x-text="decision.details?.bb_position + '%'"></span>
                            </div>
                        </div>
                    </template>
                    
                    <div x-show="tradeLogic.decisions.length === 0" class="text-center text-gray-500 py-8">
                        No recent trade decisions
                    </div>
                </div>
            </div>

            <!-- Trade Journey Timeline -->
            <div class="bg-gray-800 p-6 rounded-xl card-hover">
                <div class="flex items-center justify-between mb-6">
                    <h2 class="text-xl font-bold text-white flex items-center">
                        <i class="fas fa-route mr-3 text-orange-400"></i>Trade Journey Timeline
                    </h2>
                    <div class="flex space-x-2">
                        <select x-model="selectedTradeForTimeline" class="bg-gray-700 text-white px-3 py-1 rounded border border-gray-600">
                            <option value="">Select trade to track...</option>
                            <template x-for="trade in activeTrades" :key="trade.trade_id">
                                <option :value="trade.trade_id" x-text="trade.pair + ' (#' + trade.trade_id + ')'"></option>
                            </template>
                        </select>
                        <button @click="loadTradeJourney()" class="bg-blue-600 hover:bg-blue-700 px-4 py-1 rounded text-white text-sm">
                            <i class="fas fa-refresh mr-1"></i>Refresh
                        </button>
                    </div>
                </div>
                
                <!-- Timeline Container -->
                <div x-show="tradeJourney.events.length > 0" class="relative">
                    <!-- Timeline Line -->
                    <div class="absolute left-8 top-0 bottom-0 w-0.5 bg-gradient-to-b from-blue-500 via-purple-500 to-green-500"></div>
                    
                    <!-- Timeline Events -->
                    <div class="space-y-6">
                        <template x-for="(event, index) in tradeJourney.events" :key="index">
                            <div class="relative flex items-start">
                                <!-- Timeline Dot -->
                                <div class="absolute left-6 w-4 h-4 rounded-full border-2 border-gray-800 z-10"
                                     :class="{
                                         'bg-green-500': event.type === 'entry',
                                         'bg-blue-500': event.type === 'analysis',
                                         'bg-yellow-500': event.type === 'signal',
                                         'bg-red-500': event.type === 'exit',
                                         'bg-purple-500': event.type === 'decision'
                                     }"></div>
                                
                                <!-- Event Content -->
                                <div class="ml-16 bg-gray-700 p-4 rounded-lg w-full">
                                    <div class="flex items-center justify-between mb-2">
                                        <div class="flex items-center">
                                            <i class="fas" 
                                               :class="{
                                                   'fa-play text-green-400': event.type === 'entry',
                                                   'fa-chart-line text-blue-400': event.type === 'analysis',
                                                   'fa-bell text-yellow-400': event.type === 'signal',
                                                   'fa-stop text-red-400': event.type === 'exit',
                                                   'fa-brain text-purple-400': event.type === 'decision'
                                               }"></i>
                                            <span class="ml-2 font-semibold text-white" x-text="event.title"></span>
                                            <span class="ml-2 text-xs px-2 py-1 rounded-full" 
                                                  :class="{
                                                      'bg-green-900 text-green-300': event.type === 'entry',
                                                      'bg-blue-900 text-blue-300': event.type === 'analysis',
                                                      'bg-yellow-900 text-yellow-300': event.type === 'signal',
                                                      'bg-red-900 text-red-300': event.type === 'exit',
                                                      'bg-purple-900 text-purple-300': event.type === 'decision'
                                                  }" 
                                                  x-text="event.type.toUpperCase()"></span>
                                        </div>
                                        <span class="text-gray-400 text-sm" x-text="new Date(event.timestamp).toLocaleString()"></span>
                                    </div>
                                    
                                    <!-- Event Details -->
                                    <div class="text-gray-300 text-sm mb-3" x-text="event.description"></div>
                                    
                                    <!-- Technical Data -->
                                    <div x-show="event.technicals" class="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                                        <div x-show="event.technicals?.price" class="bg-gray-600 p-2 rounded">
                                            <div class="text-gray-400">Price</div>
                                            <div class="text-white font-mono" x-text="'$' + event.technicals.price"></div>
                                        </div>
                                        <div x-show="event.technicals?.rsi" class="bg-gray-600 p-2 rounded">
                                            <div class="text-gray-400">RSI</div>
                                            <div class="text-white font-mono" x-text="event.technicals.rsi"></div>
                                        </div>
                                        <div x-show="event.technicals?.macd" class="bg-gray-600 p-2 rounded">
                                            <div class="text-gray-400">MACD</div>
                                            <div class="text-white font-mono" x-text="event.technicals.macd"></div>
                                        </div>
                                        <div x-show="event.technicals?.volume" class="bg-gray-600 p-2 rounded">
                                            <div class="text-gray-400">Volume</div>
                                            <div class="text-white font-mono" x-text="event.technicals.volume + 'x'"></div>
                                        </div>
                                    </div>
                                    
                                    <!-- Decision Reasoning -->
                                    <div x-show="event.reasoning" class="mt-3 p-3 bg-gray-600 rounded border-l-4 border-purple-500">
                                        <div class="text-purple-300 text-xs font-semibold mb-1">STRATEGY REASONING</div>
                                        <div class="text-gray-300 text-sm" x-text="event.reasoning"></div>
                                    </div>
                                    
                                    <!-- Profit/Loss Impact -->
                                    <div x-show="event.pnl !== undefined" class="mt-3 flex items-center">
                                        <span class="text-gray-400 text-sm mr-2">P&L Impact:</span>
                                        <span :class="event.pnl >= 0 ? 'text-green-400' : 'text-red-400'" 
                                              class="font-mono text-sm font-bold" 
                                              x-text="(event.pnl >= 0 ? '+' : '') + event.pnl.toFixed(4) + ' USDT'"></span>
                                    </div>
                                </div>
                            </div>
                        </template>
                    </div>
                </div>
                
                <!-- Empty State -->
                <div x-show="tradeJourney.events.length === 0" class="text-center py-12">
                    <i class="fas fa-route text-gray-500 text-4xl mb-4"></i>
                    <h3 class="text-gray-400 text-lg font-semibold mb-2">No Trade Journey Selected</h3>
                    <p class="text-gray-500 text-sm">Select an active trade above to view its complete journey timeline</p>
                </div>
            </div>
        </div>

        <!-- Analytics Tab -->
        <div x-show="activeTab === 'analytics'" class="space-y-8">
            <!-- Performance Metrics -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div class="metric-card p-6 rounded-xl card-hover">
                    <h3 class="text-gray-400 text-sm font-medium mb-4">Trading Performance</h3>
                    <div class="space-y-3">
                        <div class="flex justify-between">
                            <span class="text-gray-400">Total Trades</span>
                            <span class="font-bold text-white" x-text="portfolio.total_trades"></span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-400">Winning Trades</span>
                            <span class="font-bold text-green-400" x-text="portfolio.winning_trades"></span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-400">Win Rate</span>
                            <span class="font-bold text-white" x-text="portfolio.win_rate.toFixed(1) + '%'"></span>
                        </div>
                    </div>
                </div>

                <div class="metric-card p-6 rounded-xl card-hover">
                    <h3 class="text-gray-400 text-sm font-medium mb-4">Risk Metrics</h3>
                    <div class="space-y-3">
                        <div class="flex justify-between">
                            <span class="text-gray-400">Best Trade</span>
                            <span class="font-bold text-green-400" x-text="'$' + (portfolio.best_trade || 0).toFixed(2)"></span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-400">Worst Trade</span>
                            <span class="font-bold text-red-400" x-text="'$' + (portfolio.worst_trade || 0).toFixed(2)"></span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-400">Max Drawdown</span>
                            <span class="font-bold text-red-400" x-text="(portfolio.max_drawdown || 0).toFixed(2) + '%'"></span>
                        </div>
                    </div>
                </div>

                <div class="metric-card p-6 rounded-xl card-hover">
                    <h3 class="text-gray-400 text-sm font-medium mb-4">Advanced Metrics</h3>
                    <div class="space-y-3">
                        <div class="flex justify-between">
                            <span class="text-gray-400">Profit Factor</span>
                            <span class="font-bold text-white" x-text="(portfolio.profit_factor || 0).toFixed(2)"></span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-400">Expectancy</span>
                            <span class="font-bold text-white" x-text="'$' + (portfolio.expectancy || 0).toFixed(2)"></span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-400">Avg Duration</span>
                            <span class="font-bold text-white" x-text="portfolio.avg_trade_duration || '--'"></span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Strategy Performance Comparison -->
            <div class="bg-gray-800 p-6 rounded-xl card-hover">
                <div class="flex items-center justify-between mb-6">
                    <h2 class="text-xl font-bold text-white flex items-center">
                        <i class="fas fa-chart-bar mr-3 text-indigo-400"></i>Strategy Performance Comparison
                    </h2>
                    <div class="flex space-x-2">
                        <select x-model="strategyComparison.timeframe" @change="loadStrategyComparison()" class="bg-gray-700 text-white px-3 py-1 rounded border border-gray-600">
                            <option value="7d">Last 7 Days</option>
                            <option value="30d">Last 30 Days</option>
                            <option value="90d">Last 90 Days</option>
                        </select>
                        <button @click="loadStrategyComparison()" class="bg-indigo-600 hover:bg-indigo-700 px-4 py-2 rounded text-white text-sm">
                            <i class="fas fa-refresh mr-1"></i>Refresh
                        </button>
                    </div>
                </div>

                <!-- Strategy Performance Table -->
                <div class="overflow-x-auto">
                    <table class="w-full text-sm">
                        <thead class="text-gray-400 border-b border-gray-700">
                            <tr>
                                <th class="text-left py-3 px-2">Strategy</th>
                                <th class="text-right py-3 px-2">Total Return</th>
                                <th class="text-right py-3 px-2">Win Rate</th>
                                <th class="text-right py-3 px-2">Trades</th>
                                <th class="text-right py-3 px-2">Avg Duration</th>
                                <th class="text-right py-3 px-2">Max DD</th>
                                <th class="text-right py-3 px-2">Sharpe</th>
                                <th class="text-right py-3 px-2">Status</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-700">
                            <template x-for="(strategy, index) in strategyComparison.strategies" :key="index">
                                <tr class="hover:bg-gray-700/50 transition-colors">
                                    <td class="py-3 px-2">
                                        <div class="flex items-center">
                                            <div class="w-3 h-3 rounded-full mr-2" :class="strategy.status === 'active' ? 'bg-green-400' : 'bg-gray-400'"></div>
                                            <span class="text-white font-medium" x-text="strategy.name"></span>
                                        </div>
                                    </td>
                                    <td class="py-3 px-2 text-right">
                                        <span class="font-bold" :class="strategy.total_return >= 0 ? 'text-green-400' : 'text-red-400'" 
                                              x-text="(strategy.total_return * 100).toFixed(2) + '%'"></span>
                                    </td>
                                    <td class="py-3 px-2 text-right text-white" x-text="(strategy.win_rate * 100).toFixed(1) + '%'"></td>
                                    <td class="py-3 px-2 text-right text-white" x-text="strategy.total_trades"></td>
                                    <td class="py-3 px-2 text-right text-gray-300" x-text="strategy.avg_duration"></td>
                                    <td class="py-3 px-2 text-right text-red-400" x-text="(strategy.max_drawdown * 100).toFixed(2) + '%'"></td>
                                    <td class="py-3 px-2 text-right text-white" x-text="strategy.sharpe_ratio.toFixed(2)"></td>
                                    <td class="py-3 px-2 text-right">
                                        <span class="px-2 py-1 rounded-full text-xs" 
                                              :class="strategy.status === 'active' ? 'bg-green-900 text-green-300' : 'bg-gray-700 text-gray-400'" 
                                              x-text="strategy.status"></span>
                                    </td>
                                </tr>
                            </template>
                        </tbody>
                    </table>
                </div>

                <!-- Strategy Performance Charts -->
                <div class="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <!-- Performance Chart -->
                    <div class="bg-gray-700 p-4 rounded-lg">
                        <h3 class="text-white font-semibold mb-4 flex items-center">
                            <i class="fas fa-chart-line mr-2 text-blue-400"></i>Cumulative Returns
                        </h3>
                        <div class="h-64 flex items-center justify-center text-gray-400">
                            <div class="text-center">
                                <i class="fas fa-chart-line text-4xl mb-2"></i>
                                <p>Performance chart visualization</p>
                                <p class="text-sm text-gray-500">Real-time strategy comparison</p>
                            </div>
                        </div>
                    </div>

                    <!-- Risk-Return Scatter -->
                    <div class="bg-gray-700 p-4 rounded-lg">
                        <h3 class="text-white font-semibold mb-4 flex items-center">
                            <i class="fas fa-chart-scatter mr-2 text-purple-400"></i>Risk vs Return
                        </h3>
                        <div class="h-64 flex items-center justify-center text-gray-400">
                            <div class="text-center">
                                <i class="fas fa-chart-scatter text-4xl mb-2"></i>
                                <p>Risk-return analysis</p>
                                <p class="text-sm text-gray-500">Quadrant analysis view</p>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Strategy Comparison Insights -->
                <div class="mt-6 bg-gradient-to-r from-indigo-900/20 to-purple-900/20 border border-indigo-800/30 rounded-lg p-4">
                    <h3 class="text-white font-semibold mb-3 flex items-center">
                        <i class="fas fa-lightbulb mr-2 text-yellow-400"></i>Performance Insights
                    </h3>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div class="space-y-2">
                            <div class="text-sm">
                                <span class="text-gray-400">Best Performer:</span>
                                <span class="text-green-400 font-semibold ml-1" x-text="strategyComparison.insights.best_performer"></span>
                            </div>
                            <div class="text-sm">
                                <span class="text-gray-400">Most Consistent:</span>
                                <span class="text-blue-400 font-semibold ml-1" x-text="strategyComparison.insights.most_consistent"></span>
                            </div>
                        </div>
                        <div class="space-y-2">
                            <div class="text-sm">
                                <span class="text-gray-400">Highest Sharpe:</span>
                                <span class="text-purple-400 font-semibold ml-1" x-text="strategyComparison.insights.highest_sharpe"></span>
                            </div>
                            <div class="text-sm">
                                <span class="text-gray-400">Recommended:</span>
                                <span class="text-orange-400 font-semibold ml-1" x-text="strategyComparison.insights.recommended"></span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Backtest Tab -->
        <div x-show="activeTab === 'backtest'" class="space-y-8">
            <!-- Strategy Selection & Backtest Configuration -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <!-- Strategy Management -->
                <div class="bg-gray-800 p-6 rounded-xl card-hover">
                    <div class="flex items-center justify-between mb-6">
                        <h3 class="text-xl font-bold text-white flex items-center">
                            <i class="fas fa-code mr-2 text-blue-400"></i>Strategy Management
                        </h3>
                        <button @click="loadStrategies()" class="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg text-white text-sm">
                            <i class="fas fa-refresh mr-1"></i>Refresh
                        </button>
                    </div>
                    
                    <!-- Available Strategies -->
                    <div class="space-y-4">
                        <div>
                            <label class="block text-gray-300 text-sm font-medium mb-2">Available Strategies</label>
                            <select x-model="backtest.selectedStrategy" class="w-full bg-gray-700 text-white p-3 rounded-lg border border-gray-600 focus:border-blue-500">
                                <option value="">Select a strategy...</option>
                                <template x-for="strategy in backtest.strategies" :key="strategy.name">
                                    <option :value="strategy.name" x-text="strategy.name"></option>
                                </template>
                            </select>
                        </div>
                        
                        <!-- Strategy Info -->
                        <div x-show="backtest.selectedStrategy" class="bg-gray-700 p-4 rounded-lg">
                            <template x-for="strategy in backtest.strategies" :key="strategy.name">
                                <div x-show="strategy.name === backtest.selectedStrategy">
                                    <div class="text-sm text-gray-300">
                                        <div><span class="font-medium">File:</span> <span x-text="strategy.file"></span></div>
                                        <div><span class="font-medium">Modified:</span> <span x-text="new Date(strategy.modified).toLocaleString()"></span></div>
                                    </div>
                                </div>
                            </template>
                        </div>
                        
                        <!-- Create New Strategy -->
                        <div class="border-t border-gray-600 pt-4">
                            <button @click="showStrategyCreator = true" class="w-full bg-green-600 hover:bg-green-700 px-4 py-2 rounded-lg text-white">
                                <i class="fas fa-plus mr-2"></i>Create New Strategy
                            </button>
                        </div>
                    </div>
                </div>
                
                <!-- Backtest Configuration -->
                <div class="bg-gray-800 p-6 rounded-xl card-hover">
                    <h3 class="text-xl font-bold text-white mb-6 flex items-center">
                        <i class="fas fa-cog mr-2 text-green-400"></i>Backtest Configuration
                    </h3>
                    
                    <div class="space-y-4">
                        <div>
                            <label class="block text-gray-300 text-sm font-medium mb-2">Time Range</label>
                            <input x-model="backtest.timerange" type="text" placeholder="20241101-20241201" 
                                   class="w-full bg-gray-700 text-white p-3 rounded-lg border border-gray-600 focus:border-blue-500">
                            <div class="text-xs text-gray-400 mt-1">Format: YYYYMMDD-YYYYMMDD</div>
                        </div>
                        
                        <div>
                            <label class="block text-gray-300 text-sm font-medium mb-2">Trading Pairs</label>
                            <div class="space-y-2">
                                <template x-for="(pair, index) in backtest.pairs" :key="index">
                                    <div class="flex items-center space-x-2">
                                        <input x-model="backtest.pairs[index]" type="text" 
                                               class="flex-1 bg-gray-700 text-white p-2 rounded border border-gray-600 focus:border-blue-500">
                                        <button @click="backtest.pairs.splice(index, 1)" class="bg-red-600 hover:bg-red-700 px-3 py-2 rounded text-white">
                                            <i class="fas fa-times"></i>
                                        </button>
                                    </div>
                                </template>
                                <button @click="backtest.pairs.push('')" class="w-full bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded text-white text-sm">
                                    <i class="fas fa-plus mr-1"></i>Add Pair
                                </button>
                            </div>
                        </div>
                        
                        <button @click="runBacktest()" :disabled="!backtest.selectedStrategy || backtest.isRunning" 
                                class="w-full bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 px-6 py-3 rounded-lg text-white font-medium">
                            <i class="fas fa-play mr-2" x-show="!backtest.isRunning"></i>
                            <i class="fas fa-spinner fa-spin mr-2" x-show="backtest.isRunning"></i>
                            <span x-text="backtest.isRunning ? 'Running Backtest...' : 'Run Backtest'"></span>
                        </button>
                    </div>
                </div>
            </div>
            
            <!-- Backtest Results -->
            <div x-show="backtest.results" class="bg-gray-800 p-6 rounded-xl card-hover">
                <h3 class="text-xl font-bold text-white mb-6 flex items-center">
                    <i class="fas fa-chart-line mr-2 text-yellow-400"></i>Backtest Results
                </h3>
                
                <div x-show="backtest.results?.success" class="space-y-6">
                    <!-- Summary Stats -->
                    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <div class="bg-gray-700 p-4 rounded-lg text-center">
                            <div class="text-2xl font-bold text-green-400" x-text="backtest.results?.results?.strategy_summary?.total_trades || 0"></div>
                            <div class="text-gray-300 text-sm">Total Trades</div>
                        </div>
                        <div class="bg-gray-700 p-4 rounded-lg text-center">
                            <div class="text-2xl font-bold text-blue-400" x-text="(backtest.results?.results?.strategy_summary?.wins || 0) + '%'"></div>
                            <div class="text-gray-300 text-sm">Win Rate</div>
                        </div>
                        <div class="bg-gray-700 p-4 rounded-lg text-center">
                            <div class="text-2xl font-bold text-purple-400" x-text="(backtest.results?.results?.strategy_summary?.profit_total || 0).toFixed(4)"></div>
                            <div class="text-gray-300 text-sm">Total Profit</div>
                        </div>
                        <div class="bg-gray-700 p-4 rounded-lg text-center">
                            <div class="text-2xl font-bold text-orange-400" x-text="(backtest.results?.results?.strategy_summary?.max_drawdown || 0).toFixed(2) + '%'"></div>
                            <div class="text-gray-300 text-sm">Max Drawdown</div>
                        </div>
                    </div>
                    
                    <!-- Raw Output -->
                    <div class="bg-gray-900 p-4 rounded-lg max-h-96 overflow-y-auto">
                        <h4 class="text-white font-bold mb-2">Backtest Output:</h4>
                        <pre class="text-green-400 text-xs whitespace-pre-wrap" x-text="backtest.results?.output || 'No output available'"></pre>
                    </div>
                </div>
                
                <div x-show="backtest.results && !backtest.results.success" class="bg-red-900 border border-red-600 p-4 rounded-lg">
                    <h4 class="text-red-300 font-bold mb-2">Backtest Error:</h4>
                    <pre class="text-red-200 text-sm whitespace-pre-wrap" x-text="backtest.results?.error || 'Unknown error'"></pre>
                </div>
            </div>
            
            <!-- Strategy Creator Modal -->
            <div x-show="showStrategyCreator" x-transition class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                <div class="bg-gray-800 rounded-xl p-6 max-w-4xl w-full max-h-[90vh] overflow-y-auto">
                    <div class="flex justify-between items-center mb-4">
                        <h3 class="text-xl font-bold text-white">Create New Strategy</h3>
                        <button @click="showStrategyCreator = false" class="text-gray-400 hover:text-white">
                            <i class="fas fa-times text-xl"></i>
                        </button>
                    </div>
                    
                    <div class="space-y-4">
                        <div>
                            <label class="block text-gray-300 text-sm font-medium mb-2">Strategy Name</label>
                            <input x-model="newStrategy.name" type="text" placeholder="my_custom_strategy" 
                                   class="w-full bg-gray-700 text-white p-3 rounded-lg border border-gray-600 focus:border-blue-500">
                        </div>
                        
                        <div>
                            <label class="block text-gray-300 text-sm font-medium mb-2">Strategy Code</label>
                            <textarea x-model="newStrategy.code" rows="20" placeholder="# Your strategy code here..." 
                                      class="w-full bg-gray-900 text-green-400 p-4 rounded-lg border border-gray-600 focus:border-blue-500 font-mono text-sm"></textarea>
                        </div>
                        
                        <div class="flex space-x-4">
                            <button @click="createStrategy()" class="bg-green-600 hover:bg-green-700 px-6 py-2 rounded-lg text-white">
                                <i class="fas fa-save mr-2"></i>Create Strategy
                            </button>
                            <button @click="showStrategyCreator = false" class="bg-gray-600 hover:bg-gray-700 px-6 py-2 rounded-lg text-white">
                                Cancel
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Charts Tab -->
        <div x-show="activeTab === 'charts'" class="space-y-8">
            <!-- Chart Controls -->
            <div class="bg-gray-800 p-6 rounded-xl card-hover">
                <h2 class="text-xl font-bold text-white mb-6 flex items-center">
                    <i class="fas fa-chart-line mr-3 text-blue-400"></i>Trading Charts & Analysis
                </h2>
                
                <!-- Chart Selection -->
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                    <div>
                        <label class="block text-gray-400 text-sm font-medium mb-2">Trading Pair</label>
                        <select x-model="selectedChartPair" @change="loadChartData()" 
                                class="w-full bg-gray-700 text-white p-3 rounded-lg border border-gray-600">
                            <option value="">Select pair...</option>
                            <template x-for="pair in whitelist" :key="pair">
                                <option :value="pair" x-text="pair"></option>
                            </template>
                        </select>
                    </div>
                    <div>
                        <label class="block text-gray-400 text-sm font-medium mb-2">Timeframe</label>
                        <select x-model="selectedTimeframe" @change="loadChartData()" 
                                class="w-full bg-gray-700 text-white p-3 rounded-lg border border-gray-600">
                            <option value="5m">5 Minutes</option>
                            <option value="15m">15 Minutes</option>
                            <option value="1h" selected>1 Hour</option>
                            <option value="4h">4 Hours</option>
                            <option value="1d">1 Day</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-gray-400 text-sm font-medium mb-2">Chart Type</label>
                        <select x-model="selectedChartType" 
                                class="w-full bg-gray-700 text-white p-3 rounded-lg border border-gray-600">
                            <option value="candles">Candlesticks</option>
                            <option value="line">Line Chart</option>
                            <option value="area">Area Chart</option>
                        </select>
                    </div>
                </div>

                <!-- Technical Indicators Toggle -->
                <div class="mb-4">
                    <label class="block text-gray-400 text-sm font-medium mb-3">Technical Indicators</label>
                    <div class="flex flex-wrap gap-3">
                        <label class="flex items-center">
                            <input type="checkbox" x-model="indicators.sma" class="mr-2">
                            <span class="text-white text-sm">SMA (20,50)</span>
                        </label>
                        <label class="flex items-center">
                            <input type="checkbox" x-model="indicators.ema" class="mr-2">
                            <span class="text-white text-sm">EMA (12,26)</span>
                        </label>
                        <label class="flex items-center">
                            <input type="checkbox" x-model="indicators.rsi" class="mr-2">
                            <span class="text-white text-sm">RSI (14)</span>
                        </label>
                        <label class="flex items-center">
                            <input type="checkbox" x-model="indicators.macd" class="mr-2">
                            <span class="text-white text-sm">MACD</span>
                        </label>
                        <label class="flex items-center">
                            <input type="checkbox" x-model="indicators.bb" class="mr-2">
                            <span class="text-white text-sm">Bollinger Bands</span>
                        </label>
                    </div>
                </div>
            </div>

            <!-- Main Chart Display -->
            <div class="bg-gray-800 p-6 rounded-xl card-hover">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-xl font-semibold text-white" x-text="selectedChartPair + ' - ' + selectedTimeframe.toUpperCase()"></h3>
                    <div class="text-sm text-gray-400" x-text="'Last Updated: ' + new Date().toLocaleString()"></div>
                </div>
                
                <!-- Chart Container -->
                <div class="bg-gray-900 p-4 rounded-lg mb-4">
                    <div x-show="!selectedChartPair" class="text-center py-16 text-gray-400">
                        <i class="fas fa-chart-area text-6xl mb-4"></i>
                        <p class="text-lg">Select a trading pair to view charts</p>
                        <p class="text-sm mt-2">Charts will show real OHLCV data from Freqtrade</p>
                    </div>
                    
                    <div x-show="selectedChartPair" class="h-96">
                        <!-- TradingView Lightweight Charts Integration -->
                        <div id="trading-chart" class="w-full h-full bg-gray-900 rounded"></div>
                        
                        <!-- Fallback Chart Display -->
                        <div x-show="!chartData" class="text-center py-16 text-gray-400">
                            <i class="fas fa-spinner fa-spin text-4xl mb-4"></i>
                            <p>Loading chart data...</p>
                        </div>
                    </div>
                </div>

                <!-- Trade Signals Overlay -->
                <div x-show="selectedChartPair" class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <!-- Current Signals -->
                    <div class="bg-gray-700 p-4 rounded-lg">
                        <h4 class="text-white font-semibold mb-3 flex items-center">
                            <i class="fas fa-bullhorn mr-2 text-yellow-400"></i>Current Signals
                        </h4>
                        <div class="space-y-2 text-sm">
                            <div class="flex justify-between">
                                <span class="text-gray-400">RSI Signal:</span>
                                <span class="text-green-400">NEUTRAL</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-400">MACD:</span>
                                <span class="text-red-400">BEARISH</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-400">Volume:</span>
                                <span class="text-blue-400">INCREASING</span>
                            </div>
                        </div>
                    </div>

                    <!-- Support/Resistance -->
                    <div class="bg-gray-700 p-4 rounded-lg">
                        <h4 class="text-white font-semibold mb-3 flex items-center">
                            <i class="fas fa-arrows-alt-v mr-2 text-purple-400"></i>Key Levels
                        </h4>
                        <div class="space-y-2 text-sm">
                            <div class="flex justify-between">
                                <span class="text-gray-400">Resistance:</span>
                                <span class="text-red-400">$42,150</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-400">Current:</span>
                                <span class="text-white font-semibold">$41,240</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-400">Support:</span>
                                <span class="text-green-400">$40,800</span>
                            </div>
                        </div>
                    </div>

                    <!-- Trade History -->
                    <div class="bg-gray-700 p-4 rounded-lg">
                        <h4 class="text-white font-semibold mb-3 flex items-center">
                            <i class="fas fa-history mr-2 text-cyan-400"></i>Recent Trades
                        </h4>
                        <div class="space-y-2 text-sm">
                            <template x-for="trade in activeTrades.filter(t => t.pair === selectedChartPair).slice(0, 3)" :key="trade.trade_id">
                                <div class="flex justify-between">
                                    <span class="text-gray-400" x-text="trade.side"></span>
                                    <span :class="trade.profit_abs >= 0 ? 'text-green-400' : 'text-red-400'" 
                                          x-text="'$' + trade.profit_abs.toFixed(2)"></span>
                                </div>
                            </template>
                            <div x-show="activeTrades.filter(t => t.pair === selectedChartPair).length === 0" 
                                 class="text-center text-gray-500">No recent trades</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Chart Analysis Tools -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <!-- Volume Analysis -->
                <div class="bg-gray-800 p-6 rounded-xl card-hover">
                    <h3 class="text-xl font-bold text-white mb-4 flex items-center">
                        <i class="fas fa-chart-bar mr-3 text-green-400"></i>Volume Analysis
                    </h3>
                    <div class="h-32 bg-gray-900 rounded p-4 flex items-center justify-center">
                        <span class="text-gray-400">Volume chart will display here</span>
                    </div>
                </div>

                <!-- Pattern Recognition -->
                <div class="bg-gray-800 p-6 rounded-xl card-hover">
                    <h3 class="text-xl font-bold text-white mb-4 flex items-center">
                        <i class="fas fa-search mr-3 text-orange-400"></i>Pattern Recognition
                    </h3>
                    <div class="space-y-3 text-sm">
                        <div class="flex justify-between items-center">
                            <span class="text-gray-400">Detected Pattern:</span>
                            <span class="text-yellow-400 font-semibold">Ascending Triangle</span>
                        </div>
                        <div class="flex justify-between items-center">
                            <span class="text-gray-400">Confidence:</span>
                            <span class="text-green-400">78%</span>
                        </div>
                        <div class="flex justify-between items-center">
                            <span class="text-gray-400">Target:</span>
                            <span class="text-blue-400">$43,500</span>
                        </div>
                        <div class="text-gray-400 text-xs mt-3">
                            Bullish continuation pattern forming. Wait for breakout above resistance.
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        function dashboard() {
            return {
                activeTab: 'overview',
                marketTab: 'overview',
                status: {
                    api_connected: false,
                    bot_running: false,
                    strategy: 'Unknown',
                    dry_run: true,
                    exchange: 'Unknown'
                },
                portfolio: {
                    total_value: 0,
                    total_pnl: 0,
                    today_pnl: 0,
                    active_positions: 0,
                    total_trades: 0,
                    win_rate: 0
                },
                activeTrades: [],
                tradeHistory: [],
                marketPrices: {},
                marketOverview: {},
                openbbCryptoData: {},
                openbbTechnicalsData: {},
                openbbSectorRotationData: {},
                availableStrategies: ['SampleStrategy'],
                selectedStrategy: 'SampleStrategy',
                maxOpenTrades: 3,
                stakeAmount: 'unlimited',
                lastUpdate: '',
                
                // Trade Logic Data
                tradeLogic: {
                    indicators: {},
                    decisions: [],
                    strategyState: {
                        current_strategy: 'MultiStrategy',
                        market_analysis: {
                            volatility: 'MODERATE',
                            trend_direction: 'SIDEWAYS',
                            volume: 'NORMAL',
                            selected_strategy: 'MEAN REVERSION',
                            reasoning: 'Loading...'
                        }
                    }
                },
                
                // Trade Journey Timeline Data
                selectedTradeId: '',
                recentTradeJourneys: [],
                currentTradeJourney: null,
                
                // Strategy Comparison Data
                strategyComparison: {
                    timeframe: '30d',
                    strategies: [],
                    insights: {
                        best_performer: 'Loading...',
                        most_consistent: 'Loading...',
                        highest_sharpe: 'Loading...',
                        recommended: 'Loading...'
                    }
                },
                
                // Advanced Control Data
                selectedPair: '',
                manualStakeAmount: '',
                whitelist: [],
                newPair: '',
                pausedPairs: [],
                selectedPairToPause: '',
                strategyParams: {
                    buy_params: {
                        rsi_buy: 30,
                        macd_threshold: 0.0,
                        volume_factor: 1.5,
                        bb_lower_factor: 0.98
                    },
                    sell_params: {
                        rsi_sell: 70,
                        profit_target: 0.04,
                        stop_loss: -0.05,
                        trailing_stop: 0.02
                    },
                    risk_params: {
                        max_open_trades: 3,
                        stoploss: -0.10
                    }
                },
                parameterUpdateStatus: '',
                parameterUpdateSuccess: false,
                systemHealth: {
                    cpu_percent: 0,
                    memory_percent: 0,
                    memory_used_gb: 0,
                    memory_total_gb: 0,
                    disk_percent: 0,
                    disk_free_gb: 0,
                    uptime_hours: 0
                },
                configEditor: {
                    dry_run: 'true',
                    timeframe: '15m',
                    max_open_trades: 6,
                    stake_currency: 'USDT'
                },
                logs: [],
                logLimit: 100,
                
                // Backtest Data
                backtest: {
                    strategies: [],
                    selectedStrategy: '',
                    timerange: '20241101-20241201',
                    pairs: ['BTC/USDT', 'ETH/USDT', 'BNB/USDT'],
                    isRunning: false,
                    results: null
                },
                showStrategyCreator: false,
                newStrategy: {
                    name: '',
                    code: ''
                },

                async init() {
                    await this.loadAllData();
                    await this.loadRecentTradeJourneys();
                    await this.loadPausedPairs();
                    await this.loadStrategyParameters();
                    setInterval(() => this.loadAllData(), 30000);
                },

                async loadAllData() {
                    try {
                        // Load bot status
                        const statusResponse = await fetch('/api/status');
                        if (statusResponse.ok) {
                            this.status = await statusResponse.json();
                            this.selectedStrategy = this.status.strategy || 'SampleStrategy';
                            this.maxOpenTrades = this.status.max_open_trades || 3;
                            this.stakeAmount = this.status.stake_amount || 'unlimited';
                            this.availableStrategies = this.status.available_strategies || ['SampleStrategy'];
                        }

                        // Load portfolio data
                        const portfolioResponse = await fetch('/api/portfolio');
                        if (portfolioResponse.ok) {
                            this.portfolio = await portfolioResponse.json();
                        }

                        // Load active trades
                        const tradesResponse = await fetch('/api/trades/active');
                        if (tradesResponse.ok) {
                            this.activeTrades = await tradesResponse.json();
                        }

                        // Load trade history
                        const historyResponse = await fetch('/api/trades/history');
                        if (historyResponse.ok) {
                            this.tradeHistory = await historyResponse.json();
                        }

                        // Load market data
                        const marketResponse = await fetch('/api/market/prices');
                        if (marketResponse.ok) {
                            this.marketPrices = await marketResponse.json();
                        }

                        // Load market overview
                        const overviewResponse = await fetch('/api/market/overview');
                        if (overviewResponse.ok) {
                            this.marketOverview = await overviewResponse.json();
                        }

                        // Load OpenBB crypto data
                        const openbbResponse = await fetch('/api/market/openbb_crypto?symbol=BTC');
                        if (openbbResponse.ok) {
                            this.openbbCryptoData = await openbbResponse.json();
                        }

                        // Load OpenBB technicals data
                        const openbbTechnicalsResponse = await fetch('/api/market/openbb_technicals?symbol=BTC-USD');
                        if (openbbTechnicalsResponse.ok) {
                            this.openbbTechnicalsData = await openbbTechnicalsResponse.json();
                        }

                        // Load OpenBB sector rotation data
                        const openbbSectorRotationResponse = await fetch('/api/market/openbb_sector_rotation');
                        if (openbbSectorRotationResponse.ok) {
                            this.openbbSectorRotationData = await openbbSectorRotationResponse.json();
                        }

                        // Load trade logic data
                        const indicatorsResponse = await fetch('/api/trade-logic/indicators');
                        if (indicatorsResponse.ok) {
                            const data = await indicatorsResponse.json();
                            this.tradeLogic.indicators = data.indicators;
                        }

                        const decisionsResponse = await fetch('/api/trade-logic/decisions');
                        if (decisionsResponse.ok) {
                            const data = await decisionsResponse.json();
                            this.tradeLogic.decisions = data.decisions;
                        }

                        const strategyResponse = await fetch('/api/trade-logic/strategy-state');
                        if (strategyResponse.ok) {
                            const data = await strategyResponse.json();
                            this.tradeLogic.strategyState = data;
                        }

                        // Load advanced control data
                        await this.loadWhitelist();
                        await this.loadConfiguration();
                        await this.loadStrategies();
                        await this.refreshSystemHealth();
                        
                        // Load strategy comparison data
                        await this.loadStrategyComparison();

                        this.lastUpdate = new Date().toLocaleTimeString();
                    } catch (error) {
                        console.error('Error loading data:', error);
                        this.addAlert('Error loading data: ' + error.message, 'error');
                    }
                },

                async startBot() {
                    try {
                        const response = await fetch('/api/bot/start', { method: 'POST' });
                        const result = await response.json();
                        this.addAlert(result.message, result.success ? 'success' : 'error');
                        if (result.success) {
                            setTimeout(() => this.loadAllData(), 1000);
                        }
                    } catch (error) {
                        this.addAlert('Failed to start bot: ' + error.message, 'error');
                    }
                },

                async stopBot() {
                    if (!confirm('Are you sure you want to stop the trading bot?')) return;
                    try {
                        const response = await fetch('/api/bot/stop', { method: 'POST' });
                        const result = await response.json();
                        this.addAlert(result.message, result.success ? 'success' : 'error');
                        if (result.success) {
                            setTimeout(() => this.loadAllData(), 1000);
                        }
                    } catch (error) {
                        this.addAlert('Failed to stop bot: ' + error.message, 'error');
                    }
                },

                async reloadConfig() {
                    try {
                        const response = await fetch('/api/bot/reload', { method: 'POST' });
                        const result = await response.json();
                        this.addAlert(result.message, result.success ? 'success' : 'error');
                        if (result.success) {
                            setTimeout(() => this.loadAllData(), 1000);
                        }
                    } catch (error) {
                        this.addAlert('Failed to reload config: ' + error.message, 'error');
                    }
                },

                async emergencyStop() {
                    if (!confirm('⚠️ EMERGENCY STOP: This will halt all trading immediately. Are you sure?')) return;
                    try {
                        const response = await fetch('/api/bot/stop', { method: 'POST' });
                        const result = await response.json();
                        this.addAlert('Emergency stop executed: ' + result.message, result.success ? 'success' : 'error');
                        if (result.success) {
                            setTimeout(() => this.loadAllData(), 1000);
                        }
                    } catch (error) {
                        this.addAlert('Emergency stop failed: ' + error.message, 'error');
                    }
                },

                async updateStrategy() {
                    try {
                        const response = await fetch('/api/bot/strategy', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ strategy: this.selectedStrategy })
                        });
                        const result = await response.json();
                        this.addAlert(result.message, result.success ? 'success' : 'error');
                    } catch (error) {
                        this.addAlert('Failed to update strategy: ' + error.message, 'error');
                    }
                },

                async updateTradingParams() {
                    try {
                        const response = await fetch('/api/bot/params', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ 
                                max_open_trades: parseInt(this.maxOpenTrades),
                                stake_amount: this.stakeAmount 
                            })
                        });
                        const result = await response.json();
                        this.addAlert(result.message, result.success ? 'success' : 'error');
                    } catch (error) {
                        this.addAlert('Failed to update parameters: ' + error.message, 'error');
                    }
                },

                async forceExitTrade(tradeId) {
                    if (!confirm(`Force exit trade ${tradeId}? This action cannot be undone.`)) return;
                    try {
                        const response = await fetch(`/api/trades/${tradeId}/exit`, { method: 'POST' });
                        const result = await response.json();
                        this.addAlert(result.message, result.success ? 'success' : 'error');
                        if (result.success) {
                            setTimeout(() => this.loadAllData(), 1000);
                        }
                    } catch (error) {
                        this.addAlert('Failed to exit trade: ' + error.message, 'error');
                    }
                },

                addAlert(message, type) {
                    const alertsDiv = document.getElementById('alerts');
                    const alertElement = document.createElement('div');
                    
                    let bgColor;
                    switch(type) {
                        case 'success': bgColor = 'bg-green-600'; break;
                        case 'error': bgColor = 'bg-red-600'; break;
                        case 'info': bgColor = 'bg-blue-600'; break;
                        default: bgColor = 'bg-gray-600';
                    }
                    
                    alertElement.className = `${bgColor} p-3 rounded-lg text-sm text-white`;
                    alertElement.textContent = message;
                    
                    if (alertsDiv.children.length === 1 && alertsDiv.children[0].textContent === 'No active alerts') {
                        alertsDiv.innerHTML = '';
                    }
                    
                    alertsDiv.insertBefore(alertElement, alertsDiv.firstChild);
                    
                    setTimeout(() => {
                        alertElement.remove();
                        if (alertsDiv.children.length === 0) {
                            alertsDiv.innerHTML = '<div class="text-center text-gray-500">No active alerts</div>';
                        }
                    }, 10000);
                },

                // Advanced Trading Controls
                async forceBuy() {
                    if (!this.selectedPair) {
                        this.addAlert('Please select a trading pair', 'error');
                        return;
                    }
                    if (!confirm(`Force buy ${this.selectedPair}?`)) return;
                    try {
                        const payload = { pair: this.selectedPair };
                        if (this.manualStakeAmount) {
                            payload.stake_amount = parseFloat(this.manualStakeAmount);
                        }
                        const response = await fetch('/api/bot/force-buy', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(payload)
                        });
                        const result = await response.json();
                        this.addAlert(result.message, result.success ? 'success' : 'error');
                        if (result.success) {
                            setTimeout(() => this.loadAllData(), 1000);
                        }
                    } catch (error) {
                        this.addAlert('Failed to force buy: ' + error.message, 'error');
                    }
                },

                async forceSell() {
                    if (!this.selectedPair) {
                        this.addAlert('Please select a trading pair', 'error');
                        return;
                    }
                    if (!confirm(`Force sell ${this.selectedPair}?`)) return;
                    try {
                        const response = await fetch('/api/bot/force-sell', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ pair: this.selectedPair })
                        });
                        const result = await response.json();
                        this.addAlert(result.message, result.success ? 'success' : 'error');
                        if (result.success) {
                            setTimeout(() => this.loadAllData(), 1000);
                        }
                    } catch (error) {
                        this.addAlert('Failed to force sell: ' + error.message, 'error');
                    }
                },

                async closeAllPositions() {
                    if (!confirm('⚠️ CLOSE ALL POSITIONS: This will exit all open trades immediately. Are you sure?')) return;
                    try {
                        const response = await fetch('/api/bot/close-all', { method: 'POST' });
                        const result = await response.json();
                        this.addAlert(result.message, result.success ? 'success' : 'error');
                        if (result.success) {
                            setTimeout(() => this.loadAllData(), 1000);
                        }
                    } catch (error) {
                        this.addAlert('Failed to close all positions: ' + error.message, 'error');
                    }
                },

                // Whitelist Management
                async loadWhitelist() {
                    try {
                        const response = await fetch('/api/whitelist');
                        const result = await response.json();
                        if (result.success) {
                            this.whitelist = result.whitelist;
                        }
                    } catch (error) {
                        console.error('Failed to load whitelist:', error);
                    }
                },

                async addPairToWhitelist() {
                    if (!this.newPair) return;
                    try {
                        const updatedList = [...this.whitelist, this.newPair];
                        const response = await fetch('/api/whitelist', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ pairs: updatedList })
                        });
                        const result = await response.json();
                        this.addAlert(result.message, result.success ? 'success' : 'error');
                        if (result.success) {
                            this.whitelist = updatedList;
                            this.newPair = '';
                        }
                    } catch (error) {
                        this.addAlert('Failed to add pair: ' + error.message, 'error');
                    }
                },

                async removePairFromWhitelist(pair) {
                    if (!confirm(`Remove ${pair} from whitelist?`)) return;
                    try {
                        const updatedList = this.whitelist.filter(p => p !== pair);
                        const response = await fetch('/api/whitelist', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ pairs: updatedList })
                        });
                        const result = await response.json();
                        this.addAlert(result.message, result.success ? 'success' : 'error');
                        if (result.success) {
                            this.whitelist = updatedList;
                        }
                    } catch (error) {
                        this.addAlert('Failed to remove pair: ' + error.message, 'error');
                    }
                },

                // Pause/Resume Pair Functions
                async pausePair() {
                    if (!this.selectedPairToPause) {
                        this.addAlert('Please select a pair to pause', 'error');
                        return;
                    }
                    if (!confirm(`Pause trading on ${this.selectedPairToPause}? This will prevent new entries on this pair.`)) return;
                    
                    try {
                        const response = await fetch('/api/pairs/pause', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ pair: this.selectedPairToPause })
                        });
                        const result = await response.json();
                        this.addAlert(result.message || result.error, result.success ? 'success' : 'error');
                        if (result.success) {
                            this.selectedPairToPause = '';
                            await this.loadPausedPairs();
                        }
                    } catch (error) {
                        this.addAlert('Failed to pause pair: ' + error.message, 'error');
                    }
                },

                async resumePair(pair) {
                    if (!confirm(`Resume trading on ${pair}? This will allow new entries on this pair.`)) return;
                    
                    try {
                        const response = await fetch('/api/pairs/resume', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ pair: pair })
                        });
                        const result = await response.json();
                        this.addAlert(result.message || result.error, result.success ? 'success' : 'error');
                        if (result.success) {
                            await this.loadPausedPairs();
                        }
                    } catch (error) {
                        this.addAlert('Failed to resume pair: ' + error.message, 'error');
                    }
                },

                async loadPausedPairs() {
                    try {
                        const response = await fetch('/api/pairs/paused');
                        const result = await response.json();
                        if (result.success) {
                            this.pausedPairs = result.paused_pairs || [];
                        }
                    } catch (error) {
                        console.error('Failed to load paused pairs:', error);
                    }
                },

                // Parameter Tuning Functions
                async loadStrategyParameters() {
                    try {
                        const response = await fetch('/api/strategy/parameters');
                        const result = await response.json();
                        if (result.success) {
                            this.strategyParams = result.parameters;
                        }
                    } catch (error) {
                        console.error('Failed to load strategy parameters:', error);
                    }
                },

                async updateStrategyParameters() {
                    if (!confirm('Update strategy parameters? Changes will take effect on next trade entry.')) return;
                    
                    try {
                        const response = await fetch('/api/strategy/parameters', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ parameters: this.strategyParams })
                        });
                        const result = await response.json();
                        
                        this.parameterUpdateSuccess = result.success;
                        this.parameterUpdateStatus = result.message || result.error;
                        
                        if (result.success) {
                            this.addAlert(result.message, 'success');
                        } else {
                            this.addAlert(result.error, 'error');
                        }
                        
                        // Clear status after 5 seconds
                        setTimeout(() => {
                            this.parameterUpdateStatus = '';
                        }, 5000);
                        
                    } catch (error) {
                        this.parameterUpdateSuccess = false;
                        this.parameterUpdateStatus = 'Failed to update parameters: ' + error.message;
                        this.addAlert('Failed to update parameters: ' + error.message, 'error');
                        
                        setTimeout(() => {
                            this.parameterUpdateStatus = '';
                        }, 5000);
                    }
                },

                async resetStrategyParameters() {
                    if (!confirm('Reset all strategy parameters to defaults? This will overwrite current settings.')) return;
                    
                    try {
                        const response = await fetch('/api/strategy/parameters/reset', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' }
                        });
                        const result = await response.json();
                        
                        this.parameterUpdateSuccess = result.success;
                        this.parameterUpdateStatus = result.message || result.error;
                        
                        if (result.success) {
                            this.strategyParams = result.default_parameters;
                            this.addAlert(result.message, 'success');
                        } else {
                            this.addAlert(result.error, 'error');
                        }
                        
                        // Clear status after 5 seconds
                        setTimeout(() => {
                            this.parameterUpdateStatus = '';
                        }, 5000);
                        
                    } catch (error) {
                        this.parameterUpdateSuccess = false;
                        this.parameterUpdateStatus = 'Failed to reset parameters: ' + error.message;
                        this.addAlert('Failed to reset parameters: ' + error.message, 'error');
                        
                        setTimeout(() => {
                            this.parameterUpdateStatus = '';
                        }, 5000);
                    }
                },

                // System Health
                async refreshSystemHealth() {
                    try {
                        const response = await fetch('/api/system/health');
                        const result = await response.json();
                        if (result.success) {
                            this.systemHealth = result.health;
                        } else {
                            this.addAlert('Failed to get system health: ' + result.message, 'error');
                        }
                    } catch (error) {
                        this.addAlert('Failed to refresh system health: ' + error.message, 'error');
                    }
                },

                // Configuration Management
                async loadConfiguration() {
                    try {
                        const response = await fetch('/api/config');
                        const result = await response.json();
                        if (result.success) {
                            this.configEditor = {
                                dry_run: result.config.dry_run,
                                timeframe: result.config.timeframe,
                                max_open_trades: result.config.max_open_trades,
                                stake_currency: result.config.stake_currency
                            };
                        }
                    } catch (error) {
                        console.error('Failed to load configuration:', error);
                    }
                },

                async updateConfiguration() {
                    if (!confirm('Update configuration? This will require a bot restart to take effect.')) return;
                    try {
                        const response = await fetch('/api/config', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ 
                                updates: {
                                    dry_run: this.configEditor.dry_run === 'true',
                                    timeframe: this.configEditor.timeframe,
                                    max_open_trades: parseInt(this.configEditor.max_open_trades),
                                    stake_currency: this.configEditor.stake_currency
                                }
                            })
                        });
                        const result = await response.json();
                        this.addAlert(result.message, result.success ? 'success' : 'error');
                    } catch (error) {
                        this.addAlert('Failed to update configuration: ' + error.message, 'error');
                    }
                },

                // Log Management
                async refreshLogs() {
                    try {
                        const response = await fetch(`/api/logs?limit=${this.logLimit}`);
                        const result = await response.json();
                        if (result.success) {
                            this.logs = result.logs.map(log => ({
                                timestamp: log.timestamp || new Date().toISOString(),
                                message: log.message || log
                            }));
                        } else {
                            this.logs = [{ message: 'Failed to load logs: ' + result.message }];
                        }
                    } catch (error) {
                        this.logs = [{ message: 'Error loading logs: ' + error.message }];
                    }
                },

                // === BACKTEST & STRATEGY MANAGEMENT METHODS ===

                async loadStrategies() {
                    try {
                        const response = await fetch('/api/strategies');
                        const result = await response.json();
                        if (result.success) {
                            this.backtest.strategies = result.strategies;
                            this.addAlert(`Loaded ${result.count} strategies`, 'success');
                        } else {
                            this.addAlert('Failed to load strategies: ' + result.error, 'error');
                        }
                    } catch (error) {
                        this.addAlert('Failed to load strategies: ' + error.message, 'error');
                    }
                },

                async runBacktest() {
                    if (!this.backtest.selectedStrategy) {
                        this.addAlert('Please select a strategy', 'error');
                        return;
                    }
                    
                    try {
                        this.backtest.isRunning = true;
                        this.addAlert(`Starting backtest for ${this.backtest.selectedStrategy}...`, 'info');
                        
                        const response = await fetch('/api/backtest/run', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                strategy: this.backtest.selectedStrategy,
                                timerange: this.backtest.timerange,
                                pairs: this.backtest.pairs.filter(p => p.trim() !== '')
                            })
                        });
                        
                        const result = await response.json();
                        this.backtest.results = result;
                        
                        if (result.success) {
                            this.addAlert('Backtest completed successfully!', 'success');
                        } else {
                            this.addAlert('Backtest failed: ' + result.error, 'error');
                        }
                    } catch (error) {
                        this.addAlert('Backtest failed: ' + error.message, 'error');
                        this.backtest.results = { success: false, error: error.message };
                    } finally {
                        this.backtest.isRunning = false;
                    }
                },

                async createStrategy() {
                    if (!this.newStrategy.name || !this.newStrategy.code) {
                        this.addAlert('Please provide strategy name and code', 'error');
                        return;
                    }
                    
                    try {
                        const response = await fetch('/api/strategies/create', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                strategy_name: this.newStrategy.name,
                                strategy_code: this.newStrategy.code
                            })
                        });
                        
                        const result = await response.json();
                        
                        if (result.success) {
                            this.addAlert(`Strategy ${this.newStrategy.name} created successfully!`, 'success');
                            this.showStrategyCreator = false;
                            this.newStrategy.name = '';
                            this.newStrategy.code = '';
                            await this.loadStrategies(); // Refresh strategy list
                        } else {
                            this.addAlert('Failed to create strategy: ' + result.error, 'error');
                        }
                    } catch (error) {
                        this.addAlert('Failed to create strategy: ' + error.message, 'error');
                    }
                },

                async loadBacktestResults() {
                    try {
                        const response = await fetch('/api/backtest/results');
                        const result = await response.json();
                        if (result.success) {
                            this.backtest.results = result;
                        }
                    } catch (error) {
                        console.error('Failed to load backtest results:', error);
                    }
                },

                // === TRADE JOURNEY TIMELINE METHODS ===

                async loadTradeJourney() {
                    if (!this.selectedTradeId) {
                        this.currentTradeJourney = null;
                        return;
                    }
                    
                    try {
                        // Fetch REAL trade journey data from the API
                        const response = await fetch(`/api/trade-journey/${this.selectedTradeId}`);
                        if (!response.ok) {
                            throw new Error('Failed to fetch trade journey');
                        }
                        
                        const result = await response.json();
                        if (result.success) {
                            this.currentTradeJourney = result;
                        } else {
                            console.error('Trade journey API error:', result.error);
                            this.currentTradeJourney = null;
                        }
                        
                    } catch (error) {
                        console.error('Failed to load trade journey:', error);
                        this.currentTradeJourney = null;
                        this.addAlert('Failed to load trade journey', 'error');
                    }
                },

                async loadRecentTradeJourneys() {
                    try {
                        // Load list of recent completed trades for selection
                        const response = await fetch('/api/trade-journey/recent?limit=20');
                        if (!response.ok) {
                            throw new Error('Failed to fetch recent trade journeys');
                        }
                        
                        const result = await response.json();
                        if (result.success) {
                            this.recentTradeJourneys = result.journeys || [];
                        }
                        
                    } catch (error) {
                        console.error('Failed to load recent trade journeys:', error);
                    }
                },

                async loadStrategyComparison() {
                    try {
                        // Fetch REAL strategy performance data from Freqtrade API
                        const response = await fetch(`/api/strategies/performance?timeframe=${this.strategyComparison.timeframe}`);
                        
                        if (!response.ok) {
                            throw new Error(`HTTP error! status: ${response.status}`);
                        }
                        
                        const result = await response.json();
                        
                        if (result.success) {
                            this.strategyComparison.strategies = result.strategies || [];
                            this.strategyComparison.insights = result.insights || {
                                best_performer: 'No data available',
                                most_consistent: 'No data available',
                                highest_sharpe: 'No data available',
                                recommended: 'No data available'
                            };
                        } else {
                            throw new Error(result.error || 'Unknown error occurred');
                        }

                    } catch (error) {
                        console.error('Failed to load strategy comparison:', error);
                        this.strategyComparison.strategies = [];
                        this.strategyComparison.insights = {
                            best_performer: 'Error loading',
                            most_consistent: 'Error loading',
                            highest_sharpe: 'Error loading',
                            recommended: 'Error loading'
                        };
                        this.addAlert('Failed to load strategy performance: ' + error.message, 'error');
                    }
                },

                formatLargeNumber(num) {
                    if (!num) return '--';
                    if (num >= 1e12) return (num / 1e12).toFixed(1) + 'T';
                    if (num >= 1e9) return (num / 1e9).toFixed(1) + 'B';
                    if (num >= 1e6) return (num / 1e6).toFixed(1) + 'M';
                    if (num >= 1e3) return (num / 1e3).toFixed(1) + 'K';
                    return num.toFixed(0);
                }
            }
        }
    </script>
</body>
</html>
"""
