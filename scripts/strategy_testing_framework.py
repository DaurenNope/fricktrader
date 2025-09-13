#!/usr/bin/env python3
"""
Multi-Strategy Testing Framework
Tests multiple strategies simultaneously and reports REAL performance data
"""

import json
import subprocess
import time
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
from pathlib import Path

class StrategyTestingFramework:
    def __init__(self, base_config_path="config/config.json"):
        self.base_config = json.load(open(base_config_path))
        self.test_results = {}
        self.running_processes = {}
        
    def create_strategy_config(self, strategy_name, config_modifications=None):
        """Create a config file for a specific strategy test"""
        config = self.base_config.copy()
        config["strategy"] = strategy_name
        config["db_url"] = f"sqlite:///tradesv3.{strategy_name.lower()}.sqlite"
        config["api_server"]["listen_port"] = self.get_port_for_strategy(strategy_name)
        
        if config_modifications:
            config.update(config_modifications)
            
        config_path = f"config/test_{strategy_name.lower()}.json"
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
            
        return config_path
    
    def get_port_for_strategy(self, strategy_name):
        """Assign unique ports for each strategy"""
        ports = {
            "MultiStrategy": 8080,
            "MeanReversionStrategy": 8081,
            "MomentumStrategy": 8082,
            "BreakoutStrategy": 8083,
            "ScalpingStrategy": 8084
        }
        return ports.get(strategy_name, 8090)
    
    def start_strategy_test(self, strategy_name, duration_hours=24):
        """Start testing a specific strategy"""
        print(f"🚀 Starting {strategy_name} test for {duration_hours} hours...")
        
        config_path = self.create_strategy_config(strategy_name)
        
        cmd = [
            "freqtrade", "trade",
            "--config", config_path,
            "--strategy", strategy_name,
            "--dry-run"
        ]
        
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.running_processes[strategy_name] = {
            "process": process,
            "start_time": datetime.now(),
            "duration_hours": duration_hours,
            "config_path": config_path
        }
        
        time.sleep(5)  # Let it start up
        return process.pid
    
    def get_strategy_performance(self, strategy_name):
        """Get real performance data from strategy database"""
        db_path = f"tradesv3.{strategy_name.lower()}.sqlite"
        
        if not Path(db_path).exists():
            return {"error": "No database found", "trades": 0}
            
        try:
            conn = sqlite3.connect(db_path)
            
            # Get trade statistics
            trades_query = """
            SELECT 
                COUNT(*) as total_trades,
                SUM(CASE WHEN profit_ratio > 0 THEN 1 ELSE 0 END) as winning_trades,
                AVG(profit_ratio) as avg_profit_ratio,
                SUM(profit_abs) as total_profit,
                MAX(profit_ratio) as best_trade,
                MIN(profit_ratio) as worst_trade,
                AVG(trade_duration) as avg_duration
            FROM trades 
            WHERE is_open = 0
            """
            
            trades_df = pd.read_sql_query(trades_query, conn)
            
            if trades_df['total_trades'].iloc[0] == 0:
                return {"error": "No completed trades", "trades": 0}
            
            # Get recent trade history
            recent_trades_query = """
            SELECT pair, profit_ratio, profit_abs, trade_duration, close_date
            FROM trades 
            WHERE is_open = 0 
            ORDER BY close_date DESC 
            LIMIT 10
            """
            
            recent_trades = pd.read_sql_query(recent_trades_query, conn)
            
            conn.close()
            
            result = trades_df.iloc[0].to_dict()
            result['win_rate'] = (result['winning_trades'] / result['total_trades']) * 100
            result['recent_trades'] = recent_trades.to_dict('records')
            result['last_updated'] = datetime.now().isoformat()
            
            return result
            
        except Exception as e:
            return {"error": str(e), "trades": 0}
    
    def create_performance_report(self):
        """Generate comprehensive performance report for all strategies"""
        report = {
            "generated_at": datetime.now().isoformat(),
            "strategies": {}
        }
        
        for strategy_name in self.running_processes.keys():
            performance = self.get_strategy_performance(strategy_name)
            report["strategies"][strategy_name] = performance
            
        return report
    
    def run_parallel_tests(self, strategies, duration_hours=24):
        """Run multiple strategies in parallel"""
        print(f"🧪 Starting parallel testing of {len(strategies)} strategies...")
        
        for strategy in strategies:
            try:
                pid = self.start_strategy_test(strategy, duration_hours)
                print(f"✅ {strategy} started (PID: {pid})")
            except Exception as e:
                print(f"❌ Failed to start {strategy}: {e}")
        
        print(f"\n📊 All strategies started. Monitoring for {duration_hours} hours...")
        return self.running_processes
    
    def stop_all_tests(self):
        """Stop all running strategy tests"""
        for strategy_name, proc_info in self.running_processes.items():
            try:
                proc_info["process"].terminate()
                print(f"🛑 Stopped {strategy_name}")
            except:
                pass
        
        self.running_processes.clear()
    
    def monitor_tests(self, check_interval_minutes=15):
        """Monitor running tests and generate periodic reports"""
        while self.running_processes:
            print(f"\n📈 Performance Update ({datetime.now().strftime('%H:%M:%S')}):")
            
            for strategy_name in list(self.running_processes.keys()):
                performance = self.get_strategy_performance(strategy_name)
                
                if performance.get("trades", 0) > 0:
                    print(f"  {strategy_name}: {performance['total_trades']} trades, "
                          f"{performance['win_rate']:.1f}% win rate, "
                          f"${performance['total_profit']:.2f} profit")
                else:
                    print(f"  {strategy_name}: No completed trades yet")
            
            time.sleep(check_interval_minutes * 60)

def main():
    """Main testing function"""
    framework = StrategyTestingFramework()
    
    # Strategies to test (you need to create these)
    strategies_to_test = [
        "MultiStrategy",  # Your fixed strategy
        # Add more strategies here when created
    ]
    
    try:
        # Start parallel testing
        framework.run_parallel_tests(strategies_to_test, duration_hours=4)
        
        # Monitor for 4 hours
        framework.monitor_tests(check_interval_minutes=15)
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping all tests...")
        framework.stop_all_tests()
    
    # Generate final report
    report = framework.create_performance_report()
    
    with open(f"strategy_test_report_{datetime.now().strftime('%Y%m%d_%H%M')}.json", 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📊 Final report saved")

if __name__ == "__main__":
    main()