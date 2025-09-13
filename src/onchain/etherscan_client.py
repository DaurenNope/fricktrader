"""
Etherscan API Client for On-Chain Data Analysis
Tracks whale movements, exchange flows, and network activity
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class EtherscanClient:
    """
    Client for Etherscan API to fetch on-chain data
    Free tier: 5 calls/second, 100,000 calls/day
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or "YourApiKeyToken"  # Free tier default
        self.base_url = "https://api.etherscan.io/api"
        self.rate_limit_delay = 0.2  # 5 calls per second
        self.last_call_time = 0

        # Major exchange wallet addresses for flow monitoring
        self.exchange_wallets = {
            "binance": [
                "0x3f5ce5fbfe3e9af3971dd833d26ba9b5c936f0be",  # Binance Hot Wallet
                "0xd551234ae421e3bcba99a0da6d736074f22192ff",  # Binance Cold Wallet
                "0x564286362092d8e7936f0549571a803b203aaced",  # Binance Hot Wallet 2
            ],
            "coinbase": [
                "0x71660c4005ba85c37ccec55d0c4493e66fe775d3",  # Coinbase Hot Wallet
                "0x503828976d22510aad0201ac7ec88293211d23da",  # Coinbase Cold Wallet
                "0xddfabcdc4d8ffc6d5beaf154f18b778f892a0740",  # Coinbase Hot Wallet 2
            ],
            "kraken": [
                "0x2910543af39aba0cd09dbb2d50200b3e800a63d2",  # Kraken Hot Wallet
                "0x0a869d79a7052c7f1b55a8ebabbea3420f0d1e13",  # Kraken Cold Wallet
            ],
        }

        # Whale threshold amounts (in Wei)
        self.whale_thresholds = {
            "ETH": int(100 * 1e18),  # 100 ETH
            "BTC": int(10 * 1e8),  # 10 BTC (in satoshis)
            "USDT": int(1000000 * 1e6),  # 1M USDT
            "USDC": int(1000000 * 1e6),  # 1M USDC
        }

    def _rate_limit(self):
        """Enforce rate limiting"""
        current_time = time.time()
        time_since_last_call = current_time - self.last_call_time
        if time_since_last_call < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last_call)
        self.last_call_time = time.time()

    def _make_request(self, params: Dict) -> Optional[Dict]:
        """Make API request with rate limiting and error handling"""
        self._rate_limit()

        params["apikey"] = self.api_key

        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "1":
                return data.get("result")
            else:
                logger.warning(f"Etherscan API error: {data.get('message')}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Etherscan API request failed: {e}")
            return None

    def get_whale_transactions(self, hours_back: int = 24) -> List[Dict]:
        """
        Get large ETH transactions (whale movements)
        """
        whale_transactions = []

        # Get latest block number
        latest_block = self._get_latest_block_number()
        if not latest_block:
            return whale_transactions

        # Calculate approximate blocks for time range (13.5 sec per block average)
        blocks_back = int(hours_back * 3600 / 13.5)

        # Get transactions for recent blocks (sample approach)
        for block_offset in range(
            0, min(blocks_back, 100), 10
        ):  # Sample every 10th block
            block_number = latest_block - block_offset
            block_data = self._get_block_by_number(block_number)

            if block_data and "transactions" in block_data:
                for tx in block_data["transactions"]:
                    value_wei = int(tx.get("value", "0"), 16)

                    # Check if transaction is above whale threshold
                    if value_wei >= self.whale_thresholds["ETH"]:
                        whale_transactions.append(
                            {
                                "hash": tx["hash"],
                                "from": tx["from"],
                                "to": tx["to"],
                                "value_eth": value_wei / 1e18,
                                "block_number": block_number,
                                "timestamp": int(block_data["timestamp"], 16),
                                "gas_price": int(tx.get("gasPrice", "0"), 16)
                                / 1e9,  # Gwei
                            }
                        )

        return whale_transactions

    def get_exchange_flows(self, hours_back: int = 24) -> Dict[str, Dict]:
        """
        Monitor inflows and outflows to major exchanges
        """
        flows = {}

        for exchange, wallets in self.exchange_wallets.items():
            exchange_flows = {
                "inflow": 0.0,
                "outflow": 0.0,
                "net_flow": 0.0,
                "transaction_count": 0,
            }

            for wallet in wallets[
                :2
            ]:  # Limit to 2 wallets per exchange for rate limiting
                wallet_txs = self._get_wallet_transactions(wallet, hours_back)

                for tx in wallet_txs:
                    value_eth = float(tx.get("value", 0)) / 1e18

                    if tx["to"].lower() == wallet.lower():
                        # Inflow to exchange
                        exchange_flows["inflow"] += value_eth
                    elif tx["from"].lower() == wallet.lower():
                        # Outflow from exchange
                        exchange_flows["outflow"] += value_eth

                    exchange_flows["transaction_count"] += 1

            exchange_flows["net_flow"] = (
                exchange_flows["inflow"] - exchange_flows["outflow"]
            )
            flows[exchange] = exchange_flows

        return flows

    def get_gas_metrics(self) -> Dict:
        """
        Get current gas price and network activity metrics
        """
        params = {"module": "gastracker", "action": "gasoracle"}

        gas_data = self._make_request(params)
        if not gas_data:
            return {}

        return {
            "safe_gas_price": float(gas_data.get("SafeGasPrice", 0)),
            "standard_gas_price": float(gas_data.get("ProposeGasPrice", 0)),
            "fast_gas_price": float(gas_data.get("FastGasPrice", 0)),
            "timestamp": datetime.now().isoformat(),
        }

    def get_network_activity_score(self) -> float:
        """
        Calculate network activity score based on gas prices and transaction volume
        Returns score from 0.0 (low activity) to 1.0 (high activity)
        """
        gas_metrics = self.get_gas_metrics()
        if not gas_metrics:
            return 0.5  # Neutral score if data unavailable

        # Gas price thresholds (in Gwei)
        low_gas = 20
        high_gas = 100

        standard_gas = gas_metrics.get("standard_gas_price", 30)

        # Normalize gas price to 0-1 scale
        if standard_gas <= low_gas:
            activity_score = 0.2
        elif standard_gas >= high_gas:
            activity_score = 1.0
        else:
            activity_score = 0.2 + 0.8 * (standard_gas - low_gas) / (high_gas - low_gas)

        return min(1.0, max(0.0, activity_score))

    def _get_latest_block_number(self) -> Optional[int]:
        """Get the latest block number"""
        params = {"module": "proxy", "action": "eth_blockNumber"}

        result = self._make_request(params)
        if result:
            return int(result, 16)
        return None

    def _get_block_by_number(self, block_number: int) -> Optional[Dict]:
        """Get block data by number"""
        params = {
            "module": "proxy",
            "action": "eth_getBlockByNumber",
            "tag": hex(block_number),
            "boolean": "true",
        }

        return self._make_request(params)

    def _get_wallet_transactions(
        self, wallet_address: str, hours_back: int = 24
    ) -> List[Dict]:
        """Get recent transactions for a wallet address"""
        params = {
            "module": "account",
            "action": "txlist",
            "address": wallet_address,
            "startblock": 0,
            "endblock": 99999999,
            "page": 1,
            "offset": 100,  # Limit to recent transactions
            "sort": "desc",
        }

        result = self._make_request(params)
        if not result:
            return []

        # Filter transactions by time
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        cutoff_timestamp = int(cutoff_time.timestamp())

        recent_txs = []
        for tx in result:
            if int(tx.get("timeStamp", 0)) >= cutoff_timestamp:
                recent_txs.append(tx)

        return recent_txs


class DeFiTVLTracker:
    """
    Track DeFi Total Value Locked (TVL) changes
    Uses DeFiPulse API (free tier available)
    """

    def __init__(self):
        self.base_url = "https://api.defipulse.com/v1"
        self.rate_limit_delay = 1.0  # Conservative rate limiting
        self.last_call_time = 0

    def _rate_limit(self):
        """Enforce rate limiting"""
        current_time = time.time()
        time_since_last_call = current_time - self.last_call_time
        if time_since_last_call < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last_call)
        self.last_call_time = time.time()

    def get_total_tvl(self) -> Optional[float]:
        """Get total DeFi TVL"""
        self._rate_limit()

        try:
            # Using alternative free API since DeFiPulse requires API key
            response = requests.get("https://api.llama.fi/protocols", timeout=10)
            response.raise_for_status()
            data = response.json()

            # Calculate total TVL from all protocols
            total_tvl = sum(protocol.get("tvl", 0) for protocol in data)
            return total_tvl

        except requests.exceptions.RequestException as e:
            logger.error(f"DeFi TVL API request failed: {e}")
            return None

    def get_tvl_change_score(self) -> float:
        """
        Get TVL change score (simplified version)
        Returns score from -1.0 (major decrease) to 1.0 (major increase)
        """
        # For MVP, return neutral score
        # In production, would track TVL changes over time
        return 0.0


class OnChainAnalyzer:
    """
    Main on-chain data analyzer that combines all sources
    """

    def __init__(self, etherscan_api_key: Optional[str] = None):
        self.etherscan = EtherscanClient(etherscan_api_key)
        self.defi_tracker = DeFiTVLTracker()
        self.cache = {}
        self.cache_duration = 300  # 5 minutes cache

    def get_whale_activity_score(self, pair: str) -> float:
        """
        Calculate whale activity score for a trading pair
        Returns score from -1.0 (heavy selling) to 1.0 (heavy buying)
        """
        cache_key = f"whale_score_{pair}"
        if self._is_cached(cache_key):
            return self.cache[cache_key]["data"]

        try:
            # Get whale transactions
            whale_txs = self.etherscan.get_whale_transactions(hours_back=6)

            if not whale_txs:
                score = 0.0
            else:
                # Analyze whale transaction patterns
                total_volume = sum(tx["value_eth"] for tx in whale_txs)

                # Score based on volume and frequency
                # More transactions = higher activity
                # Larger average size = more significant moves
                volume_score = min(total_volume / 10000, 1.0)  # Normalize to 10k ETH
                frequency_score = min(
                    len(whale_txs) / 50, 1.0
                )  # Normalize to 50 transactions

                score = (volume_score + frequency_score) / 2

                # Adjust for market direction (simplified)
                # In production, would analyze exchange flows for direction
                score = score * 0.5  # Conservative positive bias

            self._cache_data(cache_key, score)
            return score

        except Exception as e:
            logger.error(f"Error calculating whale activity score: {e}")
            return 0.0

    def get_exchange_flow_score(self, pair: str) -> float:
        """
        Calculate exchange flow score
        Returns score from -1.0 (heavy inflows/selling pressure) to 1.0 (heavy outflows/buying pressure)
        """
        cache_key = f"exchange_flow_{pair}"
        if self._is_cached(cache_key):
            return self.cache[cache_key]["data"]

        try:
            flows = self.etherscan.get_exchange_flows(hours_back=12)

            if not flows:
                score = 0.0
            else:
                # Calculate aggregate net flow
                total_net_flow = sum(
                    exchange["net_flow"] for exchange in flows.values()
                )
                total_volume = sum(
                    exchange["inflow"] + exchange["outflow"]
                    for exchange in flows.values()
                )

                if total_volume == 0:
                    score = 0.0
                else:
                    # Positive net flow = outflows > inflows = bullish
                    # Negative net flow = inflows > outflows = bearish
                    flow_ratio = total_net_flow / total_volume
                    score = max(-1.0, min(1.0, flow_ratio * 2))  # Scale to -1 to 1

            self._cache_data(cache_key, score)
            return score

        except Exception as e:
            logger.error(f"Error calculating exchange flow score: {e}")
            return 0.0

    def get_defi_activity_score(self, pair: str) -> float:
        """
        Calculate DeFi activity score
        Returns score from -1.0 (decreasing activity) to 1.0 (increasing activity)
        """
        cache_key = f"defi_score_{pair}"
        if self._is_cached(cache_key):
            return self.cache[cache_key]["data"]

        try:
            # For MVP, use simplified DeFi scoring
            tvl_score = self.defi_tracker.get_tvl_change_score()

            self._cache_data(cache_key, tvl_score)
            return tvl_score

        except Exception as e:
            logger.error(f"Error calculating DeFi activity score: {e}")
            return 0.0

    def get_network_activity_score(self, pair: str) -> float:
        """
        Calculate network activity score based on gas prices and transaction volume
        Returns score from 0.0 (low activity) to 1.0 (high activity)
        """
        cache_key = f"network_score_{pair}"
        if self._is_cached(cache_key):
            return self.cache[cache_key]["data"]

        try:
            score = self.etherscan.get_network_activity_score()

            self._cache_data(cache_key, score)
            return score

        except Exception as e:
            logger.error(f"Error calculating network activity score: {e}")
            return 0.5  # Neutral score on error

    def get_composite_onchain_score(self, pair: str) -> float:
        """
        Calculate composite on-chain score combining all metrics
        Returns score from -1.0 to 1.0
        """
        whale_score = self.get_whale_activity_score(pair)
        exchange_score = self.get_exchange_flow_score(pair)
        defi_score = self.get_defi_activity_score(pair)
        network_score = self.get_network_activity_score(pair)

        # Weighted combination
        composite_score = (
            whale_score * 0.4  # Whale activity: 40%
            + exchange_score * 0.3  # Exchange flows: 30%
            + defi_score * 0.2  # DeFi activity: 20%
            + network_score * 0.1  # Network activity: 10%
        )

        return max(-1.0, min(1.0, composite_score))

    def _is_cached(self, key: str) -> bool:
        """Check if data is cached and still valid"""
        if key not in self.cache:
            return False

        cache_time = self.cache[key]["timestamp"]
        return (time.time() - cache_time) < self.cache_duration

    def _cache_data(self, key: str, data):
        """Cache data with timestamp"""
        self.cache[key] = {"data": data, "timestamp": time.time()}
