#!/usr/bin/env python3
"""
FrickTrader - Main Application Entry Point
Professional crypto trading platform with clean architecture
"""

import asyncio
import logging
from logging.handlers import RotatingFileHandler
import os
import signal
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.logging import RichHandler

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.config_manager import get_config
from src.core.trading_engine import TradingEngine

console = Console()


def setup_logging(config) -> None:
    """Setup professional logging with Rich formatting."""
    
    # Create logs directory
    log_path = Path(config.logging.file_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure logging
    # Use RotatingFileHandler to support maxBytes and backupCount
    file_handler = RotatingFileHandler(
        config.logging.file_path,
        maxBytes=getattr(config.logging, 'max_bytes', 10 * 1024 * 1024),
        backupCount=getattr(config.logging, 'backup_count', 5),
    )

    logging.basicConfig(
        level=getattr(logging, config.logging.level.upper()),
        format=config.logging.format,
        handlers=[
            RichHandler(console=console, rich_tracebacks=True),
            file_handler,
        ],
    )
    
    # Set specific logger levels
    logging.getLogger("ccxt").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("websockets").setLevel(logging.WARNING)


class FrickTraderApp:
    """Main application class."""
    
    def __init__(self):
        """Initialize the application."""
        self.config = get_config()
        setup_logging(self.config)
        
        self.logger = logging.getLogger(__name__)
        self.trading_engine: Optional[TradingEngine] = None
        self.dashboard_process: Optional[asyncio.subprocess.Process] = None
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully.

        Schedule the async shutdown on the running event loop in a thread-safe way.
        """
        self.logger.info(f"Received signal {signum}, shutting down...")
        try:
            # Schedule shutdown on the running loop if available
            loop = asyncio.get_running_loop()
            loop.call_soon_threadsafe(asyncio.create_task, self.shutdown())
        except RuntimeError:
            # No running loop (e.g., during startup); best-effort: log and exit
            self.logger.warning("No running asyncio loop to schedule shutdown; exiting now")
            try:
                # Attempt synchronous shutdown as a fallback
                asyncio.run(self.shutdown())
            except Exception:
                pass
    
    async def start_dashboard(self) -> bool:
        """Start the web dashboard."""
        try:
            dashboard_script = Path(__file__).parent / "src" / "web_ui" / "app.py"
            
            if not dashboard_script.exists():
                self.logger.error(f"Dashboard script not found: {dashboard_script}")
                return False
            
            # Start dashboard as subprocess
            self.dashboard_process = await asyncio.create_subprocess_exec(
                sys.executable, str(dashboard_script),
                env={
                    **dict(os.environ),
                    "DASHBOARD_HOST": self.config.dashboard.host,
                    "DASHBOARD_PORT": str(self.config.dashboard.port),
                    "DASHBOARD_DEBUG": str(self.config.dashboard.debug).lower()
                },
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Wait a moment to check if it started successfully
            await asyncio.sleep(2)
            
            if self.dashboard_process.returncode is None:
                self.logger.info(f"✅ Dashboard started on {self.config.dashboard.host}:{self.config.dashboard.port}")
                return True
            else:
                self.logger.error("❌ Dashboard failed to start")
                return False
                
        except Exception as e:
            self.logger.error(f"Error starting dashboard: {e}")
            return False
    
    async def start_trading_engine(self) -> bool:
        """Start the trading engine."""
        try:
            self.trading_engine = TradingEngine()
            await self.trading_engine.start()
            self.logger.info("✅ Trading engine started")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting trading engine: {e}")
            return False
    
    async def run_full_system(self) -> None:
        """Run the complete FrickTrader system."""
        console.print("🚀 [bold green]Starting FrickTrader System[/bold green]")
        console.print(f"Environment: {self.config.environment}")
        console.print(f"Exchange: {self.config.exchange.name} ({'sandbox' if self.config.exchange.sandbox else 'live'})")
        
        try:
            # Start dashboard
            dashboard_started = await self.start_dashboard()
            if not dashboard_started:
                console.print("[red]❌ Failed to start dashboard[/red]")
                return
            
            # Start trading engine
            trading_started = await self.start_trading_engine()
            if not trading_started:
                console.print("[red]❌ Failed to start trading engine[/red]")
                return
            
            console.print("\n🎉 [bold green]FrickTrader System Running![/bold green]")
            console.print(f"📊 Dashboard: http://{self.config.dashboard.host}:{self.config.dashboard.port}")
            console.print("Press Ctrl+C to stop")
            
            # Keep running until shutdown
            while True:
                await asyncio.sleep(1)
                
                # Check if processes are still running
                if self.dashboard_process and self.dashboard_process.returncode is not None:
                    self.logger.error("Dashboard process died")
                    break
                    
                if self.trading_engine and not self.trading_engine.state.is_running:
                    self.logger.error("Trading engine stopped")
                    break
                    
        except asyncio.CancelledError:
            self.logger.info("System shutdown requested")
        except Exception as e:
            self.logger.error(f"System error: {e}")
        finally:
            await self.shutdown()
    
    async def run_dashboard_only(self) -> None:
        """Run only the dashboard."""
        console.print("🎨 [bold blue]Starting FrickTrader Dashboard[/bold blue]")
        
        try:
            dashboard_started = await self.start_dashboard()
            if not dashboard_started:
                console.print("[red]❌ Failed to start dashboard[/red]")
                return
            
            console.print(f"✅ Dashboard: http://{self.config.dashboard.host}:{self.config.dashboard.port}")
            console.print("Press Ctrl+C to stop")
            
            # Wait for dashboard process
            await self.dashboard_process.wait()
            
        except asyncio.CancelledError:
            self.logger.info("Dashboard shutdown requested")
        except Exception as e:
            self.logger.error(f"Dashboard error: {e}")
        finally:
            await self.shutdown()
    
    async def run_trading_only(self) -> None:
        """Run only the trading engine."""
        console.print("⚡ [bold cyan]Starting FrickTrader Trading Engine[/bold cyan]")
        
        try:
            trading_started = await self.start_trading_engine()
            if not trading_started:
                console.print("[red]❌ Failed to start trading engine[/red]")
                return
            
            console.print("✅ Trading engine running")
            console.print("Press Ctrl+C to stop")
            
            # Keep running until shutdown
            while self.trading_engine.state.is_running:
                await asyncio.sleep(1)
                
        except asyncio.CancelledError:
            self.logger.info("Trading engine shutdown requested")
        except Exception as e:
            self.logger.error(f"Trading engine error: {e}")
        finally:
            await self.shutdown()
    
    async def shutdown(self) -> None:
        """Shutdown all components gracefully."""
        self.logger.info("🛑 Shutting down FrickTrader...")
        
        # Stop trading engine
        if self.trading_engine:
            await self.trading_engine.stop()
        
        # Stop dashboard
        if self.dashboard_process and self.dashboard_process.returncode is None:
            self.dashboard_process.terminate()
            try:
                await asyncio.wait_for(self.dashboard_process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self.dashboard_process.kill()
                await self.dashboard_process.wait()
        
        console.print("✅ [bold green]Shutdown complete[/bold green]")


@click.group()
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration file path')
@click.option('--env', '-e', default='development', help='Environment (development/production)')
def cli(config, env):
    """FrickTrader - Professional Crypto Trading Platform"""
    import os
    if env:
        os.environ['FRICKTRADER_ENV'] = env
    if config:
        os.environ['FRICKTRADER_CONFIG'] = config


@cli.command()
def start():
    """Start the complete FrickTrader system (dashboard + trading)"""
    app = FrickTraderApp()
    asyncio.run(app.run_full_system())


@cli.command()
def dashboard():
    """Start only the web dashboard"""
    app = FrickTraderApp()
    asyncio.run(app.run_dashboard_only())


@cli.command()
def trading():
    """Start only the trading engine"""
    app = FrickTraderApp()
    asyncio.run(app.run_trading_only())


@cli.command()
def status():
    """Show system status"""
    from src.core.config_manager import get_config_manager
    
    config_manager = get_config_manager()
    config = config_manager.get_config()
    
    console.print("📊 [bold]FrickTrader System Status[/bold]")
    console.print(f"Environment: {config.environment}")
    console.print(f"Database: {config.database.url}")
    console.print(f"Exchange: {config.exchange.name}")
    console.print(f"Dashboard: {config.dashboard.host}:{config.dashboard.port}")


@cli.command()
def config():
    """Show current configuration"""
    from src.core.config_manager import get_config_manager
    import yaml
    
    config_manager = get_config_manager()
    config = config_manager.get_config()
    
    # Convert to dict for display
    config_dict = {
        "environment": config.environment,
        "database": {
            "url": config.database.url,
            "pool_size": config.database.pool_size
        },
        "exchange": {
            "name": config.exchange.name,
            "sandbox": config.exchange.sandbox
        },
        "dashboard": {
            "host": config.dashboard.host,
            "port": config.dashboard.port
        },
        "trading": {
            "max_open_positions": config.trading.max_open_positions,
            "risk_per_trade": config.trading.risk_per_trade
        }
    }
    
    console.print("⚙️ [bold]Current Configuration[/bold]")
    console.print(yaml.dump(config_dict, default_flow_style=False))


if __name__ == "__main__":
    cli()