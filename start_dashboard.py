#!/usr/bin/env python3
"""
Launch the Advanced Trading Dashboard
Shows OpenBB integration with Tiger Trade-like interface
"""

import sys
import os
import subprocess
import time
import webbrowser
from pathlib import Path

def start_dashboard():
    """Start the trading dashboard"""
    
    print("🚀 Starting Advanced Trading Dashboard")
    print("=" * 50)
    
    # Change to the web UI directory
    web_ui_dir = Path(__file__).parent / "src" / "web_ui"
    os.chdir(web_ui_dir)
    
    # Start the Flask app
    print("📊 Starting Flask server...")
    
    try:
        # Use the virtual environment Python
        venv_python = Path(__file__).parent / "trading_env" / "bin" / "python"
        
        if venv_python.exists():
            cmd = [str(venv_python), "app.py"]
        else:
            cmd = [sys.executable, "app.py"]
        
        # Start the server
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a moment for the server to start
        time.sleep(3)
        
        # Check if server is running
        if process.poll() is None:
            print("✅ Flask server started successfully!")
            print("🌐 Dashboard URL: http://127.0.0.1:5001")
            print("🔥 Features Available:")
            print("   ✅ Real-time OpenBB market data")
            print("   ✅ Advanced delta analysis")
            print("   ✅ Volume profile with POC")
            print("   ✅ Market depth analysis")
            print("   ✅ Institutional activity tracking")
            print("   ✅ Tiger Trade-like interface")
            print("\n🎯 Try these symbols:")
            print("   📈 AAPL, TSLA, MSFT (stocks)")
            print("   🪙 BTC/USDT, ETH/USDT (crypto)")
            print("\n⚡ Auto-refreshes every 30 seconds")
            print("🛑 Press Ctrl+C to stop")
            
            # Open browser
            try:
                webbrowser.open("http://127.0.0.1:5001")
                print("🌐 Opening dashboard in browser...")
            except:
                print("💡 Manually open: http://127.0.0.1:5001")
            
            # Wait for the process
            try:
                process.wait()
            except KeyboardInterrupt:
                print("\n🛑 Stopping dashboard...")
                process.terminate()
                process.wait()
                print("✅ Dashboard stopped")
        else:
            stdout, stderr = process.communicate()
            print("❌ Failed to start Flask server")
            print("STDOUT:", stdout.decode())
            print("STDERR:", stderr.decode())
            
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")
        import traceback
        traceback.print_exc()
        print("💡 Tip: Make sure you're in the correct directory and have dependencies installed")
        print("   Try manual start with:")
        print("   cd src/web_ui")
        print("   python app.py")

if __name__ == "__main__":
    start_dashboard()