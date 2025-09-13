"""
Sophisticated Multi-Bot Trading Coordinator
Manages multiple specialized trading bots with intelligent allocation
Each bot has $1000 limit and unique trading personality
"""

import asyncio
import json
import logging
import subprocess
import time
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import os
import signal
import psutil
from pathlib import Path

# Import our regime detector
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.market_analysis.regime_detector import AdvancedRegimeDetector, MarketRegime

logger = logging.getLogger(__name__)

class BotType(Enum):
    ELLIOTT_WAVE = "elliott_wave_bot"
    ORDER_BOOK_PREDATOR = "order_book_predator"
    SUPPORT_RESISTANCE = "support_resistance_bot"
    SMART_MONEY_TRACKER = "smart_money_tracker"
    VOLATILITY_SURFER = "volatility_surfer"
    MEAN_REVERSION = "mean_reversion_bot"

@dataclass
class BotConfig:
    bot_id: str
    bot_type: BotType
    strategy_name: str
    allocated_capital: float
    max_open_trades: int
    risk_level: float  # 0.1 = conservative, 1.0 = aggressive
    api_port: int
    db_file: str
    config_file: str
    is_active: bool
    process_id: Optional[int]
    performance_score: float  # Track bot performance
    
@dataclass
class BotPerformance:
    bot_id: str
    total_trades: int
    winning_trades: int
    total_profit: float
    win_rate: float
    sharpe_ratio: float
    max_drawdown: float
    last_updated: pd.Timestamp

class MultiBotCoordinator:
    """
    Advanced multi-bot trading ecosystem coordinator
    Manages 6 specialized trading bots with intelligent allocation
    """
    
    def __init__(self, base_capital: float = 6000):
        self.base_capital = base_capital
        self.capital_per_bot = 1000  # $1000 per bot
        self.regime_detector = AdvancedRegimeDetector()
        
        # Bot management
        self.bots: Dict[str, BotConfig] = {}
        self.bot_processes: Dict[str, subprocess.Popen] = {}
        self.bot_performances: Dict[str, BotPerformance] = {}
        
        # Coordination state
        self.current_regime = None
        self.last_regime_check = None
        self.regime_check_interval = 300  # 5 minutes
        self.allocation_weights = {}
        
        # Initialize bot configurations
        self._initialize_bot_configs()
        
        # Performance tracking
        self.coordinator_start_time = pd.Timestamp.now()
        self.total_system_profit = 0.0
        
        logger.info("🤖 Multi-Bot Coordinator initialized with 6 specialized bots")
    
    def _initialize_bot_configs(self):
        """Initialize configurations for all specialized bots"""
        
        bot_definitions = [
            {
                "bot_type": BotType.ELLIOTT_WAVE,
                "strategy": "ElliottWaveStrategy",
                "risk": 0.8,
                "max_trades": 2,
                "port": 8081,
                "description": "Elliott Wave pattern recognition specialist"
            },
            {
                "bot_type": BotType.ORDER_BOOK_PREDATOR,
                "strategy": "OrderBookPredatorStrategy",
                "risk": 0.9,
                "max_trades": 3,
                "port": 8082,
                "description": "Order book liquidity hunting specialist"
            },
            {
                "bot_type": BotType.SUPPORT_RESISTANCE,
                "strategy": "SupportResistanceStrategy",
                "risk": 0.6,
                "max_trades": 2,
                "port": 8083,
                "description": "Support/resistance level breakout specialist"
            },
            {
                "bot_type": BotType.SMART_MONEY_TRACKER,
                "strategy": "LiquiditySmartMoneyStrategy",  # We already have this
                "risk": 0.7,
                "max_trades": 2,
                "port": 8084,
                "description": "Institutional flow tracking specialist"
            },
            {
                "bot_type": BotType.VOLATILITY_SURFER,
                "strategy": "VolatilitySurferStrategy",
                "risk": 0.8,
                "max_trades": 3,
                "port": 8085,
                "description": "Volatility momentum specialist"
            },
            {
                "bot_type": BotType.MEAN_REVERSION,
                "strategy": "MeanReversionStrategy",
                "risk": 0.5,
                "max_trades": 2,
                "port": 8086,
                "description": "Counter-trend mean reversion specialist"
            }
        ]
        
        for i, bot_def in enumerate(bot_definitions):
            bot_id = f"bot_{i+1}_{bot_def['bot_type'].value}"
            
            bot_config = BotConfig(
                bot_id=bot_id,
                bot_type=bot_def['bot_type'],
                strategy_name=bot_def['strategy'],
                allocated_capital=self.capital_per_bot,
                max_open_trades=bot_def['max_trades'],
                risk_level=bot_def['risk'],
                api_port=bot_def['port'],
                db_file=f"tradesv3_{bot_id}.dryrun.sqlite",
                config_file=f"config/bot_configs/{bot_id}_config.json",
                is_active=False,
                process_id=None,
                performance_score=1.0
            )
            
            self.bots[bot_id] = bot_config
            logger.info(f"📋 Configured {bot_id}: {bot_def['description']}")
    
    async def start_trading_ecosystem(self):
        """Start the entire multi-bot trading ecosystem"""
        try:
            logger.info("🚀 Starting Sophisticated Multi-Bot Trading Ecosystem...")
            
            # 1. Analyze current market regime
            await self._update_market_regime()
            
            # 2. Create bot configurations
            await self._create_bot_configurations()
            
            # 3. Start bots based on regime allocation
            await self._start_allocated_bots()
            
            # 4. Begin coordination loop
            await self._start_coordination_loop()
            
        except Exception as e:
            logger.error(f"Error starting trading ecosystem: {e}")
            raise
    
    async def _update_market_regime(self):
        """Update market regime analysis"""
        try:
            # Get market data for analysis (simplified - would connect to exchange)
            # For now, we'll use dummy data structure
            sample_data = pd.DataFrame({
                'high': [100] * 100,
                'low': [98] * 100,
                'close': [99] * 100,
                'volume': [1000] * 100
            })
            
            regime_signal = self.regime_detector.analyze_market_regime(sample_data)
            self.current_regime = regime_signal
            self.last_regime_check = pd.Timestamp.now()
            
            # Update allocation weights based on regime
            self.allocation_weights = self._calculate_allocation_weights(regime_signal)
            
            logger.info(f"🌊 Market Regime: {regime_signal.regime.value.upper()} "
                       f"(Confidence: {regime_signal.confidence:.2%})")
            logger.info(f"📊 Bot Allocation: {regime_signal.recommendations}")
            
        except Exception as e:
            logger.error(f"Error updating market regime: {e}")
    
    def _calculate_allocation_weights(self, regime_signal) -> Dict[str, float]:
        """Calculate how much capital each bot should get based on regime"""
        base_allocations = {
            BotType.ELLIOTT_WAVE: 0.15,
            BotType.ORDER_BOOK_PREDATOR: 0.20,
            BotType.SUPPORT_RESISTANCE: 0.15,
            BotType.SMART_MONEY_TRACKER: 0.25,
            BotType.VOLATILITY_SURFER: 0.15,
            BotType.MEAN_REVERSION: 0.10
        }
        
        # Adjust based on regime
        if regime_signal.regime == MarketRegime.BULL:
            base_allocations[BotType.ELLIOTT_WAVE] *= 1.5
            base_allocations[BotType.VOLATILITY_SURFER] *= 1.3
            base_allocations[BotType.MEAN_REVERSION] *= 0.5
        
        elif regime_signal.regime == MarketRegime.BEAR:
            base_allocations[BotType.SMART_MONEY_TRACKER] *= 1.4
            base_allocations[BotType.MEAN_REVERSION] *= 1.5
            base_allocations[BotType.ELLIOTT_WAVE] *= 0.6
        
        elif regime_signal.regime == MarketRegime.SIDEWAYS:
            base_allocations[BotType.SUPPORT_RESISTANCE] *= 1.4
            base_allocations[BotType.MEAN_REVERSION] *= 1.6
            base_allocations[BotType.VOLATILITY_SURFER] *= 0.7
        
        # Normalize to ensure sum = 1
        total = sum(base_allocations.values())
        return {k: v/total for k, v in base_allocations.items()}
    
    async def _create_bot_configurations(self):
        """Create individual configuration files for each bot"""
        base_config_path = Path("config/config.json")
        bot_config_dir = Path("config/bot_configs")
        bot_config_dir.mkdir(exist_ok=True)
        
        # Load base configuration
        with open(base_config_path, 'r') as f:
            base_config = json.load(f)
        
        for bot_id, bot_config in self.bots.items():
            # Create specialized config for this bot
            specialized_config = base_config.copy()
            
            # Customize for this bot
            specialized_config.update({
                "bot_name": bot_id,
                "strategy": bot_config.strategy_name,
                "dry_run_wallet": bot_config.allocated_capital,
                "max_open_trades": bot_config.max_open_trades,
                "stake_amount": bot_config.allocated_capital / bot_config.max_open_trades,
                "api_server": {
                    **specialized_config["api_server"],
                    "listen_port": bot_config.api_port,
                    "username": f"bot_{bot_config.api_port}",
                    "password": f"bot_{bot_config.api_port}_pass"
                },
                "db_url": f"sqlite:///{bot_config.db_file}"
            })
            
            # Adjust risk based on bot type and market regime
            self._adjust_bot_risk_settings(specialized_config, bot_config)
            
            # Save bot configuration
            config_path = Path(bot_config.config_file)
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w') as f:
                json.dump(specialized_config, f, indent=2)
            
            logger.info(f"📝 Created configuration for {bot_id}")
    
    def _adjust_bot_risk_settings(self, config: dict, bot_config: BotConfig):
        """Adjust risk settings based on bot type and market conditions"""
        risk_multiplier = bot_config.risk_level
        
        # Adjust stop loss based on risk level
        base_stoploss = -0.03
        config["stoploss"] = base_stoploss * risk_multiplier
        
        # Adjust ROI targets
        if bot_config.bot_type == BotType.ELLIOTT_WAVE:
            # More aggressive ROI for Elliott Wave
            config["minimal_roi"] = {
                "40": 0.01,
                "20": 0.02,
                "10": 0.04,
                "0": 0.08
            }
        elif bot_config.bot_type == BotType.MEAN_REVERSION:
            # More conservative ROI for mean reversion
            config["minimal_roi"] = {
                "60": 0.005,
                "30": 0.01,
                "15": 0.02,
                "0": 0.03
            }
        
        # Add bot-specific parameters
        if bot_config.bot_type == BotType.ORDER_BOOK_PREDATOR:
            config["order_book_depth"] = 20
            config["liquidity_threshold"] = 50000
    
    async def _start_allocated_bots(self):
        """Start bots based on current regime allocation"""
        try:
            for bot_id, bot_config in self.bots.items():
                allocation_weight = self.allocation_weights.get(bot_config.bot_type, 0.1)
                
                # Start bot if allocation weight is significant
                if allocation_weight > 0.05:  # 5% minimum allocation
                    await self._start_individual_bot(bot_id)
                    logger.info(f"🤖 Started {bot_id} with {allocation_weight:.1%} allocation")
                else:
                    logger.info(f"⏸️ Skipping {bot_id} (allocation: {allocation_weight:.1%})")
            
        except Exception as e:
            logger.error(f"Error starting allocated bots: {e}")
    
    async def _start_individual_bot(self, bot_id: str):
        """Start an individual trading bot"""
        try:
            bot_config = self.bots[bot_id]
            
            # Command to start freqtrade with bot's config
            cmd = [
                "freqtrade", "trade",
                "--config", bot_config.config_file,
                "--strategy", bot_config.strategy_name,
                "--dry-run",
                "--logfile", f"logs/{bot_id}.log"
            ]
            
            # Start the process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            # Store process info
            self.bot_processes[bot_id] = process
            bot_config.process_id = process.pid
            bot_config.is_active = True
            
            logger.info(f"✅ Started {bot_id} (PID: {process.pid})")
            
        except Exception as e:
            logger.error(f"Error starting bot {bot_id}: {e}")
    
    async def _start_coordination_loop(self):
        """Main coordination loop"""
        logger.info("🔄 Starting coordination loop...")
        
        while True:
            try:
                # Check if regime update is needed
                if (pd.Timestamp.now() - self.last_regime_check).total_seconds() > self.regime_check_interval:
                    await self._update_market_regime()
                    await self._rebalance_bots()
                
                # Monitor bot health
                await self._monitor_bot_health()
                
                # Update performance metrics
                await self._update_performance_metrics()
                
                # Log system status
                await self._log_system_status()
                
                # Wait before next iteration
                await asyncio.sleep(60)  # Check every minute
                
            except KeyboardInterrupt:
                logger.info("👋 Coordination loop interrupted by user")
                break
            except Exception as e:
                logger.error(f"Error in coordination loop: {e}")
                await asyncio.sleep(30)  # Wait before retry
    
    async def _rebalance_bots(self):
        """Rebalance bot allocation based on new regime"""
        logger.info("⚖️ Rebalancing bot allocation based on regime change...")
        
        # Calculate new allocations
        new_weights = self._calculate_allocation_weights(self.current_regime)
        
        for bot_id, bot_config in self.bots.items():
            old_weight = self.allocation_weights.get(bot_config.bot_type, 0)
            new_weight = new_weights.get(bot_config.bot_type, 0)
            
            # Significant change in allocation?
            if abs(new_weight - old_weight) > 0.1:  # 10% change threshold
                if new_weight > 0.05 and not bot_config.is_active:
                    # Start bot
                    await self._start_individual_bot(bot_id)
                elif new_weight <= 0.05 and bot_config.is_active:
                    # Stop bot
                    await self._stop_individual_bot(bot_id)
        
        self.allocation_weights = new_weights
    
    async def _stop_individual_bot(self, bot_id: str):
        """Stop an individual trading bot"""
        try:
            bot_config = self.bots[bot_id]
            
            if bot_config.process_id and bot_config.is_active:
                process = self.bot_processes.get(bot_id)
                if process:
                    process.terminate()
                    process.wait(timeout=30)
                    
                bot_config.is_active = False
                bot_config.process_id = None
                
                logger.info(f"🛑 Stopped {bot_id}")
            
        except Exception as e:
            logger.error(f"Error stopping bot {bot_id}: {e}")
    
    async def _monitor_bot_health(self):
        """Monitor health of all active bots"""
        for bot_id, bot_config in self.bots.items():
            if bot_config.is_active and bot_config.process_id:
                try:
                    # Check if process is still running
                    process = psutil.Process(bot_config.process_id)
                    if not process.is_running():
                        logger.warning(f"⚠️ Bot {bot_id} process died, restarting...")
                        await self._start_individual_bot(bot_id)
                        
                except psutil.NoSuchProcess:
                    logger.warning(f"⚠️ Bot {bot_id} process not found, restarting...")
                    bot_config.is_active = False
                    await self._start_individual_bot(bot_id)
    
    async def _update_performance_metrics(self):
        """Update performance metrics for all bots"""
        # This would connect to each bot's API to get performance data
        # For now, we'll just log that we're tracking performance
        active_bots = [bid for bid, bc in self.bots.items() if bc.is_active]
        if active_bots:
            logger.debug(f"📊 Tracking performance for {len(active_bots)} active bots")
    
    async def _log_system_status(self):
        """Log current system status"""
        active_count = sum(1 for bc in self.bots.values() if bc.is_active)
        regime = self.current_regime.regime.value if self.current_regime else "unknown"
        
        logger.info(f"🎯 System Status: {active_count}/6 bots active | "
                   f"Regime: {regime.upper()} | "
                   f"Capital: ${self.base_capital:,.0f}")
    
    async def stop_all_bots(self):
        """Stop all trading bots"""
        logger.info("🛑 Stopping all trading bots...")
        
        for bot_id in list(self.bots.keys()):
            await self._stop_individual_bot(bot_id)
        
        logger.info("✅ All bots stopped")
    
    def get_system_summary(self) -> Dict:
        """Get comprehensive system summary for dashboard"""
        active_bots = [bc for bc in self.bots.values() if bc.is_active]
        
        return {
            "total_bots": len(self.bots),
            "active_bots": len(active_bots),
            "total_capital": self.base_capital,
            "current_regime": self.current_regime.regime.value if self.current_regime else "unknown",
            "regime_confidence": f"{self.current_regime.confidence:.1%}" if self.current_regime else "N/A",
            "allocation_weights": {bt.value: f"{w:.1%}" for bt, w in self.allocation_weights.items()},
            "active_bot_list": [bc.bot_id for bc in active_bots],
            "system_uptime": str(pd.Timestamp.now() - self.coordinator_start_time).split('.')[0]
        }

# Global coordinator instance
coordinator = None

async def start_multi_bot_system():
    """Start the multi-bot trading system"""
    global coordinator
    coordinator = MultiBotCoordinator()
    await coordinator.start_trading_ecosystem()

async def stop_multi_bot_system():
    """Stop the multi-bot trading system"""
    global coordinator
    if coordinator:
        await coordinator.stop_all_bots()

if __name__ == "__main__":
    # Run the multi-bot system
    asyncio.run(start_multi_bot_system())