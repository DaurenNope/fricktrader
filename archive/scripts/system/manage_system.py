#!/usr/bin/env python3
"""
Professional Trading System Manager
Unified management script for FrickTrader system components

Usage:
    python manage_system.py start       # Start all services
    python manage_system.py stop        # Stop all services  
    python manage_system.py restart     # Restart all services
    python manage_system.py status      # Show system status
    python manage_system.py dashboard   # Start only dashboard
    python manage_system.py trading     # Start only trading engine
    python manage_system.py logs        # Show live logs
    python manage_system.py health      # Run health checks
    python manage_system.py install     # Install/setup dependencies

Author: FrickTrader Team
Version: 2.0.0
"""

import argparse
import logging
import os
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import psutil
import requests
from rich.console import Console
from rich.table import Table

# Initialize rich console for beautiful output
console = Console()

# Configuration
CONFIG = {
    "project_root": Path(__file__).parent.absolute(),
    "log_dir": Path(__file__).parent / "logs",
    "config_dir": Path(__file__).parent / "config",
    "venv_dir": Path(__file__).parent / ".venv",
    "pid_dir": Path(__file__).parent,
    "freqtrade_config": Path(__file__).parent / "config" / "config.json",
    "dashboard_host": "127.0.0.1",
    "dashboard_port": 5001,
    "freqtrade_host": "127.0.0.1", 
    "freqtrade_port": 8080,
    "services": {
        "freqtrade": {
            "name": "Freqtrade Trading Engine",
            "pid_file": ".freqtrade.pid",
            "log_file": "logs/freqtrade.log",
            "health_url": "http://127.0.0.1:8080/api/v1/ping",
            "start_delay": 5,
            "required": True
        },
        "dashboard": {
            "name": "Advanced Trading Dashboard", 
            "pid_file": ".dashboard.pid",
            "log_file": "logs/dashboard.log",
            "health_url": "http://127.0.0.1:5001/",
            "start_delay": 3,
            "required": False
        }
    }
}


class SystemManager:
    """Professional system management for trading platform."""
    
    def __init__(self) -> None:
        """Initialize system manager."""
        self.console = console
        self.project_root = CONFIG["project_root"]
        self.setup_logging()
        self.ensure_directories()
        
    def setup_logging(self) -> None:
        """Set up professional logging configuration."""
        log_dir = CONFIG["log_dir"]
        log_dir.mkdir(exist_ok=True)
        
        # Configure root logger
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "system_manager.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        required_dirs = [
            CONFIG["log_dir"],
            CONFIG["config_dir"],
            Path("reports"),
            Path("tests"),
        ]
        
        for directory in required_dirs:
            directory.mkdir(exist_ok=True)
            
    def get_virtual_env_python(self) -> str:
        """Get path to virtual environment Python executable."""
        venv_dir = CONFIG["venv_dir"]
        if sys.platform == "win32":
            return str(venv_dir / "Scripts" / "python.exe")
        return str(venv_dir / "bin" / "python")
        
    def is_virtual_env_active(self) -> bool:
        """Check if virtual environment is active."""
        return sys.prefix != sys.base_prefix
        
    def activate_virtual_env(self) -> bool:
        """Activate virtual environment if not already active."""
        if self.is_virtual_env_active():
            return True
            
        venv_python = self.get_virtual_env_python()
        if not Path(venv_python).exists():
            self.console.print("[red]❌ Virtual environment not found. Run 'python manage_system.py install' first.[/red]")
            return False
            
        # If not in venv, restart with venv python
        if sys.executable != venv_python:
            self.logger.info("Restarting with virtual environment...")
            os.execv(venv_python, [venv_python] + sys.argv)
            
        return True
        
    def get_service_pid(self, service: str) -> Optional[int]:
        """Get PID of a service if running."""
        pid_file = self.project_root / CONFIG["services"][service]["pid_file"]
        
        if not pid_file.exists():
            return None
            
        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
                
            # Check if process is still running
            if psutil.pid_exists(pid):
                return pid
            else:
                # Clean up stale PID file
                pid_file.unlink()
                return None
                
        except (ValueError, IOError):
            return None
            
    def is_service_running(self, service: str) -> bool:
        """Check if a service is currently running."""
        return self.get_service_pid(service) is not None
        
    def check_service_health(self, service: str) -> bool:
        """Check service health via HTTP endpoint."""
        if not self.is_service_running(service):
            return False
            
        health_url = CONFIG["services"][service].get("health_url")
        if not health_url:
            return True  # No health check available, assume healthy
            
        try:
            response = requests.get(health_url, timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False
            
    def start_freqtrade(self) -> bool:
        """Start Freqtrade trading engine."""
        if self.is_service_running("freqtrade"):
            self.console.print("✅ Freqtrade is already running")
            return True
            
        # Ensure config exists
        config_file = CONFIG["freqtrade_config"]
        if not config_file.exists():
            self.console.print(f"[red]❌ Config file not found: {config_file}[/red]")
            return False
            
        # Ensure Freqtrade UI is installed
        try:
            subprocess.run(["freqtrade", "install-ui"], 
                         cwd=self.project_root, 
                         capture_output=True, 
                         check=False)
        except Exception:
            pass  # UI installation not critical
            
        # Start Freqtrade
        log_file = self.project_root / CONFIG["services"]["freqtrade"]["log_file"]
        
        with self.console.status("🚀 Starting Freqtrade trading engine..."):
            try:
                process = subprocess.Popen([
                    "freqtrade", "trade",
                    "--config", str(config_file),
                    "--strategy", "MultiSignalStrategy"
                ], 
                cwd=self.project_root,
                stdout=open(log_file, 'w'),
                stderr=subprocess.STDOUT,
                preexec_fn=os.setsid if sys.platform != "win32" else None
                )
                
                # Save PID
                pid_file = self.project_root / CONFIG["services"]["freqtrade"]["pid_file"]
                with open(pid_file, 'w') as f:
                    f.write(str(process.pid))
                    
                # Wait for startup
                time.sleep(CONFIG["services"]["freqtrade"]["start_delay"])
                
                # Check if process is still running
                if process.poll() is None:
                    self.console.print("✅ Freqtrade started successfully")
                    self.logger.info(f"Freqtrade started with PID {process.pid}")
                    return True
                else:
                    self.console.print("[red]❌ Freqtrade failed to start[/red]")
                    return False
                    
            except Exception as e:
                self.console.print(f"[red]❌ Error starting Freqtrade: {e}[/red]")
                return False
                
    def start_dashboard(self) -> bool:
        """Start advanced trading dashboard."""
        if self.is_service_running("dashboard"):
            self.console.print("✅ Dashboard is already running")
            return True
            
        # Ensure dashboard app exists
        dashboard_app = self.project_root / "src" / "web_ui" / "app.py"
        if not dashboard_app.exists():
            self.console.print(f"[red]❌ Dashboard app not found: {dashboard_app}[/red]")
            return False
            
        log_file = self.project_root / CONFIG["services"]["dashboard"]["log_file"]
        
        with self.console.status("🎨 Starting advanced dashboard..."):
            try:
                # Change to dashboard directory
                dashboard_dir = self.project_root / "src" / "web_ui"
                
                process = subprocess.Popen([
                    sys.executable, "app.py"
                ],
                cwd=dashboard_dir,
                stdout=open(log_file, 'w'),
                stderr=subprocess.STDOUT,
                preexec_fn=os.setsid if sys.platform != "win32" else None
                )
                
                # Save PID
                pid_file = self.project_root / CONFIG["services"]["dashboard"]["pid_file"]
                with open(pid_file, 'w') as f:
                    f.write(str(process.pid))
                    
                # Wait for startup
                time.sleep(CONFIG["services"]["dashboard"]["start_delay"])
                
                # Check if process is still running
                if process.poll() is None:
                    self.console.print("✅ Dashboard started successfully")
                    self.logger.info(f"Dashboard started with PID {process.pid}")
                    return True
                else:
                    self.console.print("[red]❌ Dashboard failed to start[/red]")
                    return False
                    
            except Exception as e:
                self.console.print(f"[red]❌ Error starting dashboard: {e}[/red]")
                return False
                
    def stop_service(self, service: str) -> bool:
        """Stop a specific service."""
        pid = self.get_service_pid(service)
        if not pid:
            return True  # Already stopped
            
        service_name = CONFIG["services"][service]["name"]
        
        with self.console.status(f"🛑 Stopping {service_name}..."):
            try:
                # Try graceful shutdown first
                if sys.platform == "win32":
                    subprocess.run(["taskkill", "/pid", str(pid), "/f"], 
                                 capture_output=True)
                else:
                    os.killpg(os.getpgid(pid), signal.SIGTERM)
                    
                # Wait for graceful shutdown
                for _ in range(10):
                    if not psutil.pid_exists(pid):
                        break
                    time.sleep(0.5)
                    
                # Force kill if still running
                if psutil.pid_exists(pid):
                    if sys.platform == "win32":
                        subprocess.run(["taskkill", "/pid", str(pid), "/f"], 
                                     capture_output=True)
                    else:
                        os.killpg(os.getpgid(pid), signal.SIGKILL)
                        
                # Clean up PID file
                pid_file = self.project_root / CONFIG["services"][service]["pid_file"]
                pid_file.unlink(missing_ok=True)
                
                self.console.print(f"✅ {service_name} stopped")
                self.logger.info(f"{service_name} stopped (PID: {pid})")
                return True
                
            except Exception as e:
                self.console.print(f"[red]❌ Error stopping {service_name}: {e}[/red]")
                return False
                
    def cleanup_processes(self) -> None:
        """Clean up any orphaned processes."""
        with self.console.status("🧹 Cleaning up orphaned processes..."):
            try:
                # Kill any orphaned freqtrade processes
                subprocess.run(["pkill", "-f", "freqtrade"], 
                             capture_output=True, check=False)
                
                # Kill any orphaned dashboard processes  
                subprocess.run(["pkill", "-f", "app.py"], 
                             capture_output=True, check=False)
                             
                # Clean up PID files
                for service in CONFIG["services"]:
                    pid_file = self.project_root / CONFIG["services"][service]["pid_file"]
                    pid_file.unlink(missing_ok=True)
                    
                time.sleep(2)  # Wait for cleanup
                self.console.print("✅ Cleanup completed")
                
            except Exception as e:
                self.console.print(f"[yellow]⚠️ Cleanup warning: {e}[/yellow]")
                
    def show_status(self) -> None:
        """Show comprehensive system status."""
        table = Table(title="🎯 FrickTrader System Status", show_header=True)
        table.add_column("Service", style="cyan", no_wrap=True)
        table.add_column("Status", justify="center")
        table.add_column("PID", justify="center")
        table.add_column("Health", justify="center") 
        table.add_column("URL", style="blue")
        
        for service, config in CONFIG["services"].items():
            pid = self.get_service_pid(service)
            
            if pid:
                status = "🟢 Running"
                pid_str = str(pid)
                health = "✅ Healthy" if self.check_service_health(service) else "❌ Unhealthy"
            else:
                status = "🔴 Stopped"
                pid_str = "-"
                health = "-"
                
            url = config.get("health_url", "-")
            table.add_row(config["name"], status, pid_str, health, url)
            
        self.console.print(table)
        
        # Show system info
        self.console.print("\n📊 System Information:")
        self.console.print(f"  • Project Root: {self.project_root}")
        self.console.print(f"  • Virtual Env: {'✅ Active' if self.is_virtual_env_active() else '❌ Inactive'}")
        self.console.print(f"  • Python: {sys.executable}")
        self.console.print(f"  • Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    def run_health_checks(self) -> bool:
        """Run comprehensive health checks."""
        self.console.print("🏥 Running system health checks...\n")
        
        all_healthy = True
        
        # Check virtual environment
        if self.is_virtual_env_active():
            self.console.print("✅ Virtual environment is active")
        else:
            self.console.print("[red]❌ Virtual environment is not active[/red]")
            all_healthy = False
            
        # Check required files
        required_files = [
            CONFIG["freqtrade_config"],
            self.project_root / "requirements.txt",
            self.project_root / "user_data" / "strategies" / "MultiSignalStrategy.py"
        ]
        
        for file in required_files:
            if file.exists():
                self.console.print(f"✅ Required file exists: {file.name}")
            else:
                self.console.print(f"[red]❌ Missing required file: {file}[/red]")
                all_healthy = False
                
        # Check service health
        for service, config in CONFIG["services"].items():
            if self.is_service_running(service):
                if self.check_service_health(service):
                    self.console.print(f"✅ {config['name']} is healthy")
                else:
                    self.console.print(f"[yellow]⚠️ {config['name']} is running but unhealthy[/yellow]")
                    all_healthy = False
            else:
                if config.get("required", False):
                    self.console.print(f"[red]❌ {config['name']} is not running (required)[/red]")
                    all_healthy = False
                else:
                    self.console.print(f"[blue]ℹ️ {config['name']} is not running (optional)[/blue]")
                    
        # Check disk space
        disk_usage = psutil.disk_usage(self.project_root)
        free_gb = disk_usage.free / (1024**3)
        if free_gb > 1:
            self.console.print(f"✅ Sufficient disk space: {free_gb:.1f} GB free")
        else:
            self.console.print(f"[red]❌ Low disk space: {free_gb:.1f} GB free[/red]")
            all_healthy = False
            
        # Check memory usage
        memory = psutil.virtual_memory()
        if memory.percent < 90:
            self.console.print(f"✅ Memory usage OK: {memory.percent:.1f}%")
        else:
            self.console.print(f"[yellow]⚠️ High memory usage: {memory.percent:.1f}%[/yellow]")
            
        self.console.print(f"\n{'✅' if all_healthy else '❌'} Overall health: {'Healthy' if all_healthy else 'Issues detected'}")
        return all_healthy
        
    def install_dependencies(self) -> bool:
        """Install and set up all dependencies."""
        self.console.print("📦 Installing dependencies and setting up environment...\n")
        
        # Create virtual environment if it doesn't exist
        venv_dir = CONFIG["venv_dir"]
        if not venv_dir.exists():
            with self.console.status("🐍 Creating virtual environment..."):
                try:
                    subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], 
                                 check=True, cwd=self.project_root)
                    self.console.print("✅ Virtual environment created")
                except subprocess.CalledProcessError as e:
                    self.console.print(f"[red]❌ Failed to create virtual environment: {e}[/red]")
                    return False
                    
        # Install requirements
        venv_python = self.get_virtual_env_python()
        requirements_file = self.project_root / "requirements.txt"
        
        if requirements_file.exists():
            with self.console.status("📦 Installing Python dependencies..."):
                try:
                    subprocess.run([
                        venv_python, "-m", "pip", "install", "--upgrade", "pip"
                    ], check=True, cwd=self.project_root)
                    
                    subprocess.run([
                        venv_python, "-m", "pip", "install", "-r", str(requirements_file)
                    ], check=True, cwd=self.project_root)
                    
                    # Install development dependencies
                    subprocess.run([
                        venv_python, "-m", "pip", "install", "-e", ".[dev]"
                    ], check=True, cwd=self.project_root)
                    
                    self.console.print("✅ Python dependencies installed")
                    
                except subprocess.CalledProcessError as e:
                    self.console.print(f"[red]❌ Failed to install dependencies: {e}[/red]")
                    return False
        else:
            self.console.print("[yellow]⚠️ requirements.txt not found[/yellow]")
            
        # Install pre-commit hooks
        if Path(".pre-commit-config.yaml").exists():
            with self.console.status("🔧 Installing pre-commit hooks..."):
                try:
                    subprocess.run([
                        venv_python, "-m", "pre_commit", "install"
                    ], check=True, cwd=self.project_root)
                    self.console.print("✅ Pre-commit hooks installed")
                except subprocess.CalledProcessError:
                    self.console.print("[yellow]⚠️ Failed to install pre-commit hooks[/yellow]")
                    
        self.console.print("\n🎉 Installation completed successfully!")
        return True
        
    def show_logs(self, service: Optional[str] = None, lines: int = 50) -> None:
        """Show live logs from services."""
        if service:
            services = [service] if service in CONFIG["services"] else []
        else:
            services = list(CONFIG["services"].keys())
            
        if not services:
            self.console.print("[red]❌ No valid services specified[/red]")
            return
            
        self.console.print(f"📜 Showing logs (last {lines} lines)...\n")
        
        for service in services:
            log_file = self.project_root / CONFIG["services"][service]["log_file"]
            if log_file.exists():
                self.console.print(f"[bold cyan]--- {CONFIG['services'][service]['name']} ---[/bold cyan]")
                try:
                    with open(log_file, 'r') as f:
                        log_lines = f.readlines()
                        for line in log_lines[-lines:]:
                            self.console.print(line.rstrip())
                except Exception as e:
                    self.console.print(f"[red]Error reading log: {e}[/red]")
            else:
                self.console.print(f"[yellow]⚠️ Log file not found: {log_file}[/yellow]")
                
            if len(services) > 1:
                self.console.print()


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Professional FrickTrader System Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python manage_system.py start              # Start all services
  python manage_system.py stop               # Stop all services
  python manage_system.py status             # Show system status
  python manage_system.py logs               # Show recent logs
  python manage_system.py health             # Run health checks
  python manage_system.py install            # Install dependencies
        """
    )
    
    parser.add_argument(
        "command",
        choices=["start", "stop", "restart", "status", "dashboard", "trading", 
                "logs", "health", "install", "cleanup"],
        help="Command to execute"
    )
    
    parser.add_argument(
        "--lines", "-n",
        type=int,
        default=50,
        help="Number of log lines to show (default: 50)"
    )
    
    args = parser.parse_args()
    
    # Initialize system manager
    manager = SystemManager()
    
    # Ensure virtual environment for most commands
    if args.command not in ["install", "cleanup", "status"]:
        if not manager.activate_virtual_env():
            sys.exit(1)
    
    # Execute command
    try:
        if args.command == "start":
            console.print("🚀 [bold green]Starting FrickTrader System[/bold green]\n")
            success = True
            success &= manager.start_freqtrade()
            success &= manager.start_dashboard()
            
            if success:
                console.print("\n🎉 [bold green]All services started successfully![/bold green]")
                console.print("\n📊 Access URLs:")
                console.print("  • Freqtrade UI: http://127.0.0.1:8080")
                console.print("  • Advanced Dashboard: http://127.0.0.1:5001")
            else:
                console.print("\n❌ [bold red]Some services failed to start[/bold red]")
                sys.exit(1)
                
        elif args.command == "stop":
            console.print("🛑 [bold red]Stopping FrickTrader System[/bold red]\n")
            manager.stop_service("dashboard")
            manager.stop_service("freqtrade")
            manager.cleanup_processes()
            console.print("\n✅ [bold green]All services stopped[/bold green]")
            
        elif args.command == "restart":
            console.print("🔄 [bold yellow]Restarting FrickTrader System[/bold yellow]\n")
            manager.stop_service("dashboard")
            manager.stop_service("freqtrade")
            manager.cleanup_processes()
            time.sleep(2)
            manager.start_freqtrade()
            manager.start_dashboard()
            console.print("\n🎉 [bold green]System restarted successfully![/bold green]")
            
        elif args.command == "status":
            manager.show_status()
            
        elif args.command == "dashboard":
            console.print("🎨 [bold blue]Starting Dashboard Only[/bold blue]\n")
            if manager.start_dashboard():
                console.print("\n✅ Dashboard: http://127.0.0.1:5001")
            else:
                sys.exit(1)
                
        elif args.command == "trading":
            console.print("⚡ [bold cyan]Starting Trading Engine Only[/bold cyan]\n")
            if manager.start_freqtrade():
                console.print("\n✅ Freqtrade UI: http://127.0.0.1:8080")
            else:
                sys.exit(1)
                
        elif args.command == "logs":
            manager.show_logs(lines=args.lines)
            
        elif args.command == "health":
            if not manager.run_health_checks():
                sys.exit(1)
                
        elif args.command == "install":
            if not manager.install_dependencies():
                sys.exit(1)
                
        elif args.command == "cleanup":
            manager.cleanup_processes()
            
    except KeyboardInterrupt:
        console.print("\n\n⚠️ [bold yellow]Operation cancelled by user[/bold yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n💥 [bold red]Unexpected error: {e}[/bold red]")
        sys.exit(1)


if __name__ == "__main__":
    main()