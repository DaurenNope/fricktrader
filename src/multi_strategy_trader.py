"""
Multi-Strategy Trading System
Orchestrates multiple trading strategies with automatic portfolio management
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict
import requests
import subprocess

from src.core.portfolio_manager import PortfolioManager
from src.market_data.live_market_provider import LiveMarketProvider
from src.analysis.individual_coin_analyzer import IndividualCoinAnalyzer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MultiStrategyTrader:
    """
    Main orchestrator for multi-strategy trading system
    Coordinates portfolio management, market analysis, and strategy execution
    """
    
    def __init__(self, config_path: str = "config/config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        
        # Initialize components
        self.portfolio_manager = PortfolioManager(self.config.get('portfolio', {}))
        self.market_provider = LiveMarketProvider()
        self.coin_analyzer = IndividualCoinAnalyzer()
        
        # Freqtrade API settings
        self.api_base = "http://127.0.0.1:8080/api/v1"
        self.api_username = self.config.get('api_server', {}).get('username', '')
        self.api_password = self.config.get('api_server', {}).get('password', '')
        
        # Runtime state
        self.running = False
        self.strategy_processes: Dict[str, Dict] = {}
        self.last_analysis_time = None
        
        logger.info("Multi-Strategy Trader initialized")
    
    def _load_config(self) -> Dict:
        """Load configuration from file"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            # Set defaults for portfolio management
            if 'portfolio' not in config:
                config['portfolio'] = {
                    'total_capital': 10000,
                    'max_strategies': 4,
                    'rebalance_hours': 6,
                    'min_confidence': 0.6
                }
            
            return config
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}
    
    def _save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def get_market_data(self) -> Dict:
        """Get comprehensive market data for analysis"""
        try:
            market_data = {}
            
            # Get data for major pairs
            major_pairs = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'AVAX/USDT', 'ADA/USDT']
            
            for pair in major_pairs:
                try:
                    # Get OHLCV data (last 100 candles for analysis)
                    ohlcv = self.market_provider.get_kline_data(pair, '1h', limit=100)
                    
                    if ohlcv:
                        market_data[pair] = {
                            'open': [candle['open'] for candle in ohlcv],
                            'high': [candle['high'] for candle in ohlcv],
                            'low': [candle['low'] for candle in ohlcv],
                            'close': [candle['close'] for candle in ohlcv],
                            'volume': [candle['volume'] for candle in ohlcv],
                            'timestamp': [candle['timestamp'] for candle in ohlcv]
                        }
                
                except Exception as e:
                    logger.warning(f"Could not get data for {pair}: {e}")
                    continue
            
            return market_data
            
        except Exception as e:
            logger.error(f"Error getting market data: {e}")
            return {}
    
    def get_freqtrade_performance(self) -> Dict:
        """Get performance data from running Freqtrade instances"""
        try:
            performance_data = {}
            
            # Try to get data from Freqtrade API
            try:
                response = requests.get(
                    f"{self.api_base}/status",
                    auth=(self.api_username, self.api_password) if self.api_username else None,
                    timeout=10
                )
                
                if response.status_code == 200:
                    
                    # Get profit/loss data
                    profit_response = requests.get(
                        f"{self.api_base}/profit",
                        auth=(self.api_username, self.api_password) if self.api_username else None,
                        timeout=10
                    )
                    
                    if profit_response.status_code == 200:
                        profit_data = profit_response.json()
                        
                        # Extract performance metrics
                        performance_data['total_return'] = profit_data.get('profit_total_pct', 0.0)
                        performance_data['win_rate'] = profit_data.get('winrate', 0.0)
                        performance_data['trades_count'] = profit_data.get('trade_count', 0)
                        
                        # Calculate Sharpe ratio estimate
                        profit_ratio = profit_data.get('profit_total', 0.0)
                        if profit_ratio > 0:
                            performance_data['sharpe_ratio'] = min(3.0, profit_ratio * 2)  # Simple estimate
                        else:
                            performance_data['sharpe_ratio'] = max(-2.0, profit_ratio * 3)
            
            except requests.exceptions.RequestException:
                logger.warning("Could not connect to Freqtrade API, using default performance data")
            
            # Use default/estimated performance if API unavailable
            if not performance_data:
                performance_data = {
                    'total_return': 0.0,
                    'win_rate': 0.5,
                    'sharpe_ratio': 0.0,
                    'trades_count': 0
                }
            
            return performance_data
            
        except Exception as e:
            logger.error(f"Error getting performance data: {e}")
            return {}
    
    def create_strategy_config(self, strategy_name: str, allocation_pct: float) -> Dict:
        """Create Freqtrade config for a specific strategy"""
        
        # Base config from main config
        base_config = self.config.copy()
        
        # Calculate stake amount based on allocation
        total_capital = self.portfolio_manager.total_capital
        allocated_capital = total_capital * (allocation_pct / 100)
        max_open_trades = min(5, max(1, int(allocation_pct / 15)))  # 1-5 trades based on allocation
        stake_amount = allocated_capital / max_open_trades
        
        # Update strategy-specific settings
        strategy_config = base_config.copy()
        strategy_config.update({
            'max_open_trades': max_open_trades,
            'stake_amount': max(25, round(stake_amount, 2)),  # Minimum $25 per trade
            'strategy': strategy_name,
            'strategy_list': [strategy_name],
            
            # Unique identifiers for this strategy instance
            'db_url': f'sqlite:///user_data/{strategy_name.lower()}_trades.db',
            'user_data_dir': f'user_data/{strategy_name.lower()}',
            
            # API server settings (different port for each strategy)
            'api_server': {
                **base_config.get('api_server', {}),
                'listen_port': base_config.get('api_server', {}).get('listen_port', 8080) + hash(strategy_name) % 100,
                'enabled': True
            }
        })
        
        return strategy_config
    
    async def start_strategy_instance(self, strategy_name: str, config: Dict) -> bool:
        """Start a Freqtrade instance for a specific strategy"""
        try:
            import subprocess
            import tempfile
            import os
            
            # Create temporary config file for this strategy
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(config, f, indent=2)
                config_file = f.name
            
            # Create command to start Freqtrade
            cmd = [
                'freqtrade', 'trade',
                '--config', config_file,
                '--strategy', strategy_name
            ]
            
            # Start the process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            self.strategy_processes[strategy_name] = {
                'process': process,
                'config_file': config_file,
                'started_at': datetime.now(),
                'allocation_pct': config.get('allocation_pct', 0),
                'api_port': config.get('api_server', {}).get('listen_port', 8080)
            }
            
            logger.info(f"Started {strategy_name} with {config.get('allocation_pct', 0):.1f}% allocation")
            return True
            
        except Exception as e:
            logger.error(f"Error starting strategy {strategy_name}: {e}")
            return False
    
    def stop_strategy_instance(self, strategy_name: str):
        """Stop a running strategy instance"""
        try:
            if strategy_name in self.strategy_processes:
                process_info = self.strategy_processes[strategy_name]
                process = process_info['process']
                
                # Terminate the process
                process.terminate()
                
                # Wait up to 30 seconds for graceful shutdown
                try:
                    process.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    process.kill()
                
                # Clean up config file
                import os
                try:
                    os.unlink(process_info['config_file'])
                except Exception:
                    pass
                
                del self.strategy_processes[strategy_name]
                logger.info(f"Stopped strategy instance: {strategy_name}")
        
        except Exception as e:
            logger.error(f"Error stopping strategy {strategy_name}: {e}")
    
    async def rebalance_strategies(self):
        """Rebalance active strategies based on market conditions"""
        try:
            logger.info("Starting strategy rebalancing...")
            
            # Get current market data
            market_data = self.get_market_data()
            if not market_data:
                logger.warning("No market data available for rebalancing")
                return
            
            # Get performance data
            performance_data = self.get_freqtrade_performance()
            
            # Run portfolio rebalancing
            rebalance_result = self.portfolio_manager.rebalance_portfolio(market_data, performance_data)
            
            logger.info(f"Market regime: {rebalance_result.get('market_regime', 'unknown')}")
            logger.info(f"Confidence: {rebalance_result.get('confidence', 0.0):.2f}")
            
            # Get new optimal allocations
            new_allocations = rebalance_result.get('allocations', {})
            
            # Stop strategies with 0 allocation
            for strategy_name in list(self.strategy_processes.keys()):
                if new_allocations.get(strategy_name, 0) < 5.0:  # Less than 5% allocation
                    logger.info(f"Stopping {strategy_name} - low allocation ({new_allocations.get(strategy_name, 0):.1f}%)")
                    self.stop_strategy_instance(strategy_name)
            
            # Start/Update active strategies
            for strategy_name, allocation_pct in new_allocations.items():
                if allocation_pct >= 5.0:  # Only run strategies with 5%+ allocation
                    
                    # Stop existing instance if significant allocation change
                    if strategy_name in self.strategy_processes:
                        old_allocation = self.strategy_processes[strategy_name]['allocation_pct']
                        if abs(allocation_pct - old_allocation) > 10.0:  # >10% change
                            logger.info(f"Restarting {strategy_name} - allocation change: {old_allocation:.1f}% → {allocation_pct:.1f}%")
                            self.stop_strategy_instance(strategy_name)
                    
                    # Start strategy if not running
                    if strategy_name not in self.strategy_processes:
                        strategy_config = self.create_strategy_config(strategy_name, allocation_pct)
                        await self.start_strategy_instance(strategy_name, strategy_config)
            
            # Log current status
            active_strategies = list(self.strategy_processes.keys())
            logger.info(f"Active strategies: {active_strategies}")
            
            # Save results
            self._save_rebalance_results(rebalance_result)
            
        except Exception as e:
            logger.error(f"Error during strategy rebalancing: {e}")
    
    def _save_rebalance_results(self, results: Dict):
        """Save rebalancing results to file"""
        try:
            import os
            os.makedirs('user_data/portfolio', exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"user_data/portfolio/rebalance_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving rebalance results: {e}")
    
    async def monitor_strategies(self):
        """Monitor running strategies and system health"""
        try:
            # Check strategy processes
            for strategy_name, process_info in list(self.strategy_processes.items()):
                process = process_info['process']
                
                # Check if process is still running
                if process.poll() is not None:
                    logger.warning(f"Strategy {strategy_name} process stopped unexpectedly")
                    
                    # Clean up and potentially restart
                    self.stop_strategy_instance(strategy_name)
                    
                    # TODO: Implement restart logic based on allocation
            
            # Log system status
            active_count = len(self.strategy_processes)
            portfolio_summary = self.portfolio_manager.get_portfolio_summary()
            
            logger.info(f"System status: {active_count} active strategies")
            logger.info(f"Portfolio allocation: {portfolio_summary.get('allocated_capital', 0):.2f} USDT")
            
        except Exception as e:
            logger.error(f"Error monitoring strategies: {e}")
    
    async def run(self):
        """Main execution loop"""
        logger.info("Starting Multi-Strategy Trading System...")
        self.running = True
        
        try:
            # Initial rebalancing
            await self.rebalance_strategies()
            
            while self.running:
                try:
                    # Monitor running strategies
                    await self.monitor_strategies()
                    
                    # Check if rebalancing is needed
                    if self.portfolio_manager.should_rebalance():
                        await self.rebalance_strategies()
                    
                    # Wait before next cycle
                    await asyncio.sleep(300)  # Check every 5 minutes
                    
                except Exception as e:
                    logger.error(f"Error in main loop: {e}")
                    await asyncio.sleep(60)  # Wait 1 minute on error
        
        except KeyboardInterrupt:
            logger.info("Shutdown requested...")
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop all strategies and clean up"""
        logger.info("Stopping Multi-Strategy Trading System...")
        self.running = False
        
        # Stop all strategy instances
        for strategy_name in list(self.strategy_processes.keys()):
            self.stop_strategy_instance(strategy_name)
        
        logger.info("All strategies stopped")
    
    def get_status(self) -> Dict:
        """Get comprehensive system status"""
        return {
            'timestamp': datetime.now().isoformat(),
            'running': self.running,
            'active_strategies': len(self.strategy_processes),
            'strategy_processes': {
                name: {
                    'allocation_pct': info['allocation_pct'],
                    'started_at': info['started_at'].isoformat(),
                    'api_port': info['api_port'],
                    'running': info['process'].poll() is None
                }
                for name, info in self.strategy_processes.items()
            },
            'portfolio_summary': self.portfolio_manager.get_portfolio_summary(),
            'last_analysis': self.last_analysis_time.isoformat() if self.last_analysis_time else None
        }

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Multi-Strategy Trading System')
    parser.add_argument('--config', default='user_data/config.json', help='Config file path')
    parser.add_argument('--dry-run', action='store_true', help='Run in dry-run mode')
    
    args = parser.parse_args()
    
    # Create and run the trading system
    trader = MultiStrategyTrader(args.config)
    
    try:
        # Run the main loop
        asyncio.run(trader.run())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise

if __name__ == "__main__":
    main()