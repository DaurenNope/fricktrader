#!/bin/bash
# Fix DNS resolution for crypto exchanges

echo "🔧 Configuring DNS to bypass ISP blocking..."

# Add custom DNS entries to /etc/hosts for crypto exchanges
sudo tee -a /etc/hosts << EOF

# Crypto Exchange DNS Bypass
44.195.64.186    api.binance.com
44.195.64.186    www.binance.com
162.159.135.233  api.bybit.com  
162.159.135.233  www.bybit.com
EOF

echo "✅ DNS entries added to /etc/hosts"
echo "Testing connectivity..."

ping -c 2 api.binance.com
ping -c 2 api.bybit.com