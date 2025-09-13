"""
Trading Engine - Core orchestration of trading operations
One file per feature: Main trading system coordination
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional
from dataclasses import dataclass

from .config_manager import get_config
from ..strategy_framework import StrategyManager, TradingSignal
from ..unified_data_pipeline import UnifiedDataPipeline

logger = logging.getLogger(__name__)


@dataclass
class TradingState:
    """Current state of the trading engine."""
    is_running: bool = False
    active_positions: int = 0
    total_pnl: float = 0.0
    last_signal_time: Optional[datetime] = None
    error_count: int = 0


class TradingEngine:
    """
    Core trading engine that orchestrates all trading operations.
    Coordinates data pipeline, strategies, and execution.
    """
    
    def __init__(self):
        """Initialize trading engine."""
        self.config = get_config()
        self.state = TradingState()
        
        # Initialize components
        self.data_pipeline = UnifiedDataPipeline(self.config.__dict__)
        self.strategy_manager = StrategyManager(self.data_pipeline)
        
        # Trading symbols
        self.active_symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "ADA/USDT"]
        
        # Control flags
        self._shutdown_requested = False
        
        logger.info("Trading engine initialized")
    
    async def start(self) -> None:
        """Start the trading engine."""
        if self.state.is_running:
            logger.warning("Trading engine is already running")
            return
            
        logger.info("🚀 Starting FrickTrader trading engine")
        
        try:
            # Initialize data pipeline
            await self.data_pipeline.start_real_time_feeds(self.active_symbols)
            
            # Start main trading loop
            self.state.is_running = True
            await self._main_trading_loop()
            
        except Exception as e:
            logger.error(f"Error starting trading engine: {e}")
            self.state.is_running = False
            raise
    
    async def stop(self) -> None:
        """Stop the trading engine gracefully."""
        logger.info("🛑 Stopping trading engine")
        
        self._shutdown_requested = True
        self.state.is_running = False
        
        # Stop data feeds
        await self.data_pipeline.stop_real_time_feeds()
        
        logger.info("Trading engine stopped")
    
    async def _main_trading_loop(self) -> None:
        """Main trading loop - runs continuously."""
        logger.info("Starting main trading loop")
        
        while self.state.is_running and not self._shutdown_requested:
            try:
                # Process each symbol
                for symbol in self.active_symbols:
                    if self._shutdown_requested:
                        break
                        
                    await self._process_symbol(symbol)
                
                # Wait before next iteration
                await asyncio.sleep(30)  # 30 second intervals
                
            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
                self.state.error_count += 1
                
                # Stop if too many errors
                if self.state.error_count > 10:
                    logger.error("Too many errors, stopping trading engine")
                    break
                    
                await asyncio.sleep(60)  # Wait longer after error
    
    async def _process_symbol(self, symbol: str) -> None:
        """Process trading signals for a specific symbol."""
        try:
            # Check if we can open new positions
            if self.state.active_positions >= self.config.trading.max_open_positions:
                logger.debug(f"Max positions reached, skipping {symbol}")
                return
            
            # Execute all strategies for this symbol
            signals = await self.strategy_manager.execute_all_strategies(symbol)
            
            if signals:
                logger.info(f"Generated {len(signals)} signals for {symbol}")
                
                # Process each signal
                for signal in signals:
                    await self._process_signal(signal)
                    
                self.state.last_signal_time = datetime.now()
            
        except Exception as e:
            logger.error(f"Error processing {symbol}: {e}")
    
    async def _process_signal(self, signal: TradingSignal) -> None:
        """Process a trading signal."""
        try:
            logger.info(
                f"Processing signal: {signal.symbol} {signal.signal_type.value} "
                f"(strength: {signal.strength:.2f}, confidence: {signal.confidence:.2f})"
            )
            
            # For now, just log the signal
            # In production, this would:
            # 1. Validate the signal
            # 2. Check risk management rules
            # 3. Calculate position size
            # 4. Submit order to exchange
            # 5. Track the position
            
            logger.info(f"Signal processed: {signal.reasoning}")
            
        except Exception as e:
            logger.error(f"Error processing signal: {e}")
    
    def get_status(self) -> Dict:
        """Get current trading engine status."""
        return {
            "is_running": self.state.is_running,
            "active_positions": self.state.active_positions,
            "total_pnl": self.state.total_pnl,
            "last_signal_time": self.state.last_signal_time.isoformat() if self.state.last_signal_time else None,
            "error_count": self.state.error_count,
            "active_symbols": self.active_symbols,
            "strategy_status": self.strategy_manager.get_strategy_status(),
            "data_pipeline_status": self.data_pipeline.get_data_status()
        }
    
    def get_performance_metrics(self) -> Dict:
        """Get trading performance metrics."""
        return {
            "total_pnl": self.state.total_pnl,
            "active_positions": self.state.active_positions,
            "max_positions": self.config.trading.max_open_positions,
            "error_rate": self.state.error_count,
            "uptime": "N/A",  # Would calculate actual uptime
            "signals_generated": "N/A",  # Would track signal count
            "win_rate": "N/A",  # Would calculate from trade history
        }
    
    async def add_symbol(self, symbol: str) -> bool:
        """Add a new symbol to active trading."""
        if symbol in self.active_symbols:
            logger.warning(f"Symbol {symbol} already active")
            return False
            
        try:
            # Validate symbol with data pipeline
            test_data = await self.data_pipeline.get_real_time_data(symbol)
            if "error" in test_data:
                logger.error(f"Cannot add symbol {symbol}: {test_data['error']}")
                return False
                
            self.active_symbols.append(symbol)
            logger.info(f"Added symbol to active trading: {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding symbol {symbol}: {e}")
            return False
    
    async def remove_symbol(self, symbol: str) -> bool:
        """Remove a symbol from active trading."""
        if symbol not in self.active_symbols:
            logger.warning(f"Symbol {symbol} not in active list")
            return False
            
        try:
            self.active_symbols.remove(symbol)
            logger.info(f"Removed symbol from active trading: {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing symbol {symbol}: {e}")
            return False