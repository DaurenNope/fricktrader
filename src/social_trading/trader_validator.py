"""
Trader Performance Validation System
Implements blockchain-based trade verification, performance metrics calculation,
fraud detection, and comprehensive trader ranking algorithms.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import hashlib
import requests
import json
import sqlite3
import os
from threading import Lock

from .scraper_framework import TraderProfile, TradingSignal

logger = logging.getLogger(__name__)

@dataclass
class TradeRecord:
    """Data class for individual trade records"""
    trader_username: str
    platform: str
    pair: str
    signal_type: str  # 'BUY', 'SELL'
    entry_price: float
    exit_price: float = 0.0
    entry_timestamp: datetime = None
    exit_timestamp: datetime = None
    profit_loss: float = 0.0
    profit_loss_pct: float = 0.0
    verified: bool = False
    verification_source: str = ""
    confidence_score: float = 0.0

@dataclass
class PerformanceMetrics:
    """Data class for trader performance metrics"""
    trader_username: str
    platform: str
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    total_return: float = 0.0
    total_return_pct: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_pct: float = 0.0
    average_win: float = 0.0
    average_loss: float = 0.0
    profit_factor: float = 0.0
    calmar_ratio: float = 0.0
    volatility: float = 0.0
    risk_score: float = 0.0
    consistency_score: float = 0.0
    fraud_score: float = 0.0
    verification_score: float = 0.0
    overall_score: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)

class BlockchainVerifier:
    """
    Blockchain-based trade verification system
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.etherscan_api_key = self.config.get('etherscan_api_key', os.getenv('ETHERSCAN_API_KEY'))
        self.bscscan_api_key = self.config.get('bscscan_api_key', os.getenv('BSCSCAN_API_KEY'))
        
        # Known exchange wallet addresses for verification
        self.exchange_wallets = {
            'binance': [
                '0x3f5ce5fbfe3e9af3971dd833d26ba9b5c936f0be',  # Binance hot wallet
                '0xd551234ae421e3bcba99a0da6d736074f22192ff',  # Binance cold wallet
            ],
            'coinbase': [
                '0x71660c4005ba85c37ccec55d0c4493e66fe775d3',  # Coinbase hot wallet
                '0x503828976d22510aad0201ac7ec88293211d23da',  # Coinbase cold wallet
            ],
            'kraken': [
                '0x2910543af39aba0cd09dbb2d50200b3e800a63d2',  # Kraken wallet
                '0x0a869d79a7052c7f1b55a8ebabbea3420f0d1e13',  # Kraken wallet
            ]
        }
        
        logger.info("🔗 Blockchain verifier initialized")
    
    def verify_trade_on_chain(self, trade_record: TradeRecord, wallet_address: str = None) -> Tuple[bool, float, str]:
        """
        Verify a trade record using blockchain data
        Returns: (verified, confidence_score, verification_source)
        """
        try:
            if not wallet_address:
                logger.warning(f"No wallet address provided for trade verification")
                return False, 0.0, "no_wallet"
            
            # Get transaction history for the wallet
            transactions = self._get_wallet_transactions(wallet_address, trade_record.pair)
            
            if not transactions:
                return False, 0.0, "no_transactions"
            
            # Look for transactions matching the trade record
            matching_tx = self._find_matching_transaction(trade_record, transactions)
            
            if matching_tx:
                confidence = self._calculate_verification_confidence(trade_record, matching_tx)
                return True, confidence, "blockchain_verified"
            else:
                return False, 0.0, "no_matching_tx"
                
        except Exception as e:
            logger.error(f"Error verifying trade on-chain: {e}")
            return False, 0.0, "verification_error"
    
    def _get_wallet_transactions(self, wallet_address: str, pair: str) -> List[Dict]:
        """
        Get transaction history for a wallet address
        """
        try:
            # Extract token symbol from pair (e.g., BTC/USDT -> BTC)
            token_symbol = pair.split('/')[0]
            
            # For Ethereum-based tokens
            if self.etherscan_api_key:
                url = f"https://api.etherscan.io/api"
                params = {
                    'module': 'account',
                    'action': 'tokentx',
                    'address': wallet_address,
                    'startblock': 0,
                    'endblock': 99999999,
                    'sort': 'desc',
                    'apikey': self.etherscan_api_key
                }
                
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == '1':
                        return data.get('result', [])
            
            # For BSC-based tokens
            if self.bscscan_api_key:
                url = f"https://api.bscscan.com/api"
                params = {
                    'module': 'account',
                    'action': 'tokentx',
                    'address': wallet_address,
                    'startblock': 0,
                    'endblock': 99999999,
                    'sort': 'desc',
                    'apikey': self.bscscan_api_key
                }
                
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == '1':
                        return data.get('result', [])
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting wallet transactions: {e}")
            return []
    
    def _find_matching_transaction(self, trade_record: TradeRecord, transactions: List[Dict]) -> Optional[Dict]:
        """
        Find transaction matching the trade record
        """
        try:
            # Convert trade timestamp to unix timestamp for comparison
            trade_timestamp = int(trade_record.entry_timestamp.timestamp())
            
            # Look for transactions within a reasonable time window (±1 hour)
            time_window = 3600  # 1 hour in seconds
            
            for tx in transactions:
                tx_timestamp = int(tx.get('timeStamp', 0))
                
                # Check if transaction is within time window
                if abs(tx_timestamp - trade_timestamp) <= time_window:
                    # Check if transaction involves the correct token
                    token_symbol = tx.get('tokenSymbol', '').upper()
                    trade_token = trade_record.pair.split('/')[0].upper()
                    
                    if token_symbol == trade_token:
                        # Check transaction direction matches signal type
                        tx_value = float(tx.get('value', 0)) / (10 ** int(tx.get('tokenDecimal', 18)))
                        
                        # For buy signals, look for incoming transactions to known exchanges
                        # For sell signals, look for outgoing transactions from known exchanges
                        if self._transaction_matches_signal(tx, trade_record):
                            return tx
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding matching transaction: {e}")
            return None
    
    def _transaction_matches_signal(self, transaction: Dict, trade_record: TradeRecord) -> bool:
        """
        Check if transaction direction matches the trading signal
        """
        try:
            tx_from = transaction.get('from', '').lower()
            tx_to = transaction.get('to', '').lower()
            
            # Check if transaction involves known exchange wallets
            exchange_involved = False
            for exchange, wallets in self.exchange_wallets.items():
                for wallet in wallets:
                    if wallet.lower() in [tx_from, tx_to]:
                        exchange_involved = True
                        break
                if exchange_involved:
                    break
            
            if not exchange_involved:
                return False
            
            # For BUY signals, expect money flowing TO exchanges (selling other assets to buy target)
            # For SELL signals, expect money flowing FROM exchanges (selling target asset)
            if trade_record.signal_type == 'BUY':
                # Look for transactions TO exchange wallets
                return any(wallet.lower() == tx_to for exchange_wallets in self.exchange_wallets.values() for wallet in exchange_wallets)
            elif trade_record.signal_type == 'SELL':
                # Look for transactions FROM exchange wallets
                return any(wallet.lower() == tx_from for exchange_wallets in self.exchange_wallets.values() for wallet in exchange_wallets)
            
            return False
            
        except Exception as e:
            logger.error(f"Error matching transaction to signal: {e}")
            return False
    
    def _calculate_verification_confidence(self, trade_record: TradeRecord, transaction: Dict) -> float:
        """
        Calculate confidence score for trade verification
        """
        try:
            confidence = 0.0
            
            # Base confidence for finding matching transaction
            confidence += 0.4
            
            # Time proximity bonus (closer to trade time = higher confidence)
            trade_timestamp = int(trade_record.entry_timestamp.timestamp())
            tx_timestamp = int(transaction.get('timeStamp', 0))
            time_diff = abs(tx_timestamp - trade_timestamp)
            
            if time_diff <= 300:  # Within 5 minutes
                confidence += 0.3
            elif time_diff <= 1800:  # Within 30 minutes
                confidence += 0.2
            elif time_diff <= 3600:  # Within 1 hour
                confidence += 0.1
            
            # Transaction value relevance
            tx_value = float(transaction.get('value', 0)) / (10 ** int(transaction.get('tokenDecimal', 18)))
            if tx_value > 1000:  # Significant transaction
                confidence += 0.2
            elif tx_value > 100:
                confidence += 0.1
            
            # Exchange involvement bonus
            confidence += 0.1
            
            return min(confidence, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating verification confidence: {e}")
            return 0.0

class PerformanceCalculator:
    """
    Advanced performance metrics calculation system
    """
    
    def __init__(self):
        self.risk_free_rate = 0.02  # 2% annual risk-free rate
        logger.info("📊 Performance calculator initialized")
    
    def calculate_metrics(self, trades: List[TradeRecord]) -> PerformanceMetrics:
        """
        Calculate comprehensive performance metrics for a trader
        """
        try:
            if not trades:
                return PerformanceMetrics(
                    trader_username="unknown",
                    platform="unknown"
                )
            
            trader_username = trades[0].trader_username
            platform = trades[0].platform
            
            # Basic trade statistics
            total_trades = len(trades)
            completed_trades = [t for t in trades if t.exit_price > 0]
            winning_trades = len([t for t in completed_trades if t.profit_loss > 0])
            losing_trades = len([t for t in completed_trades if t.profit_loss < 0])
            
            # Calculate returns
            returns = [t.profit_loss_pct for t in completed_trades if t.profit_loss_pct != 0]
            total_return = sum([t.profit_loss for t in completed_trades])
            total_return_pct = sum(returns) if returns else 0.0
            
            # Win rate
            win_rate = winning_trades / len(completed_trades) if completed_trades else 0.0
            
            # Average win/loss
            wins = [t.profit_loss for t in completed_trades if t.profit_loss > 0]
            losses = [t.profit_loss for t in completed_trades if t.profit_loss < 0]
            average_win = np.mean(wins) if wins else 0.0
            average_loss = abs(np.mean(losses)) if losses else 0.0
            
            # Profit factor
            total_wins = sum(wins) if wins else 0.0
            total_losses = abs(sum(losses)) if losses else 0.0
            profit_factor = total_wins / total_losses if total_losses > 0 else 0.0
            
            # Risk metrics
            sharpe_ratio = self._calculate_sharpe_ratio(returns)
            sortino_ratio = self._calculate_sortino_ratio(returns)
            max_drawdown, max_drawdown_pct = self._calculate_max_drawdown(completed_trades)
            volatility = np.std(returns) if len(returns) > 1 else 0.0
            
            # Calmar ratio
            calmar_ratio = (total_return_pct / max_drawdown_pct) if max_drawdown_pct > 0 else 0.0
            
            # Risk and consistency scores
            risk_score = self._calculate_risk_score(volatility, max_drawdown_pct, win_rate)
            consistency_score = self._calculate_consistency_score(returns, win_rate)
            
            return PerformanceMetrics(
                trader_username=trader_username,
                platform=platform,
                total_trades=total_trades,
                winning_trades=winning_trades,
                losing_trades=losing_trades,
                win_rate=win_rate,
                total_return=total_return,
                total_return_pct=total_return_pct,
                sharpe_ratio=sharpe_ratio,
                sortino_ratio=sortino_ratio,
                max_drawdown=max_drawdown,
                max_drawdown_pct=max_drawdown_pct,
                average_win=average_win,
                average_loss=average_loss,
                profit_factor=profit_factor,
                calmar_ratio=calmar_ratio,
                volatility=volatility,
                risk_score=risk_score,
                consistency_score=consistency_score
            )
            
        except Exception as e:
            logger.error(f"Error calculating performance metrics: {e}")
            return PerformanceMetrics(trader_username="error", platform="error")
    
    def _calculate_sharpe_ratio(self, returns: List[float]) -> float:
        """Calculate Sharpe ratio"""
        try:
            if len(returns) < 2:
                return 0.0
            
            mean_return = np.mean(returns)
            std_return = np.std(returns)
            
            if std_return == 0:
                return 0.0
            
            # Annualized Sharpe ratio (assuming daily returns)
            excess_return = mean_return - (self.risk_free_rate / 365)
            sharpe = (excess_return / std_return) * np.sqrt(365)
            
            return sharpe
            
        except Exception as e:
            logger.error(f"Error calculating Sharpe ratio: {e}")
            return 0.0
    
    def _calculate_sortino_ratio(self, returns: List[float]) -> float:
        """Calculate Sortino ratio (downside deviation)"""
        try:
            if len(returns) < 2:
                return 0.0
            
            mean_return = np.mean(returns)
            downside_returns = [r for r in returns if r < 0]
            
            if not downside_returns:
                return float('inf') if mean_return > 0 else 0.0
            
            downside_deviation = np.std(downside_returns)
            
            if downside_deviation == 0:
                return 0.0
            
            # Annualized Sortino ratio
            excess_return = mean_return - (self.risk_free_rate / 365)
            sortino = (excess_return / downside_deviation) * np.sqrt(365)
            
            return sortino
            
        except Exception as e:
            logger.error(f"Error calculating Sortino ratio: {e}")
            return 0.0
    
    def _calculate_max_drawdown(self, trades: List[TradeRecord]) -> Tuple[float, float]:
        """Calculate maximum drawdown in absolute and percentage terms"""
        try:
            if not trades:
                return 0.0, 0.0
            
            # Calculate cumulative P&L
            cumulative_pnl = []
            running_total = 0.0
            
            for trade in sorted(trades, key=lambda x: x.entry_timestamp or datetime.now()):
                running_total += trade.profit_loss
                cumulative_pnl.append(running_total)
            
            if not cumulative_pnl:
                return 0.0, 0.0
            
            # Find maximum drawdown
            peak = cumulative_pnl[0]
            max_dd = 0.0
            max_dd_pct = 0.0
            
            for value in cumulative_pnl:
                if value > peak:
                    peak = value
                
                drawdown = peak - value
                if drawdown > max_dd:
                    max_dd = drawdown
                    max_dd_pct = (drawdown / peak * 100) if peak > 0 else 0.0
            
            return max_dd, max_dd_pct
            
        except Exception as e:
            logger.error(f"Error calculating max drawdown: {e}")
            return 0.0, 0.0
    
    def _calculate_risk_score(self, volatility: float, max_drawdown_pct: float, win_rate: float) -> float:
        """Calculate overall risk score (0-1, lower is better)"""
        try:
            # Normalize components to 0-1 scale
            vol_score = min(volatility / 0.5, 1.0)  # Normalize against 50% volatility
            dd_score = min(max_drawdown_pct / 50.0, 1.0)  # Normalize against 50% drawdown
            wr_score = 1.0 - win_rate  # Invert win rate (lower win rate = higher risk)
            
            # Weighted risk score
            risk_score = (vol_score * 0.4 + dd_score * 0.4 + wr_score * 0.2)
            
            return min(max(risk_score, 0.0), 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating risk score: {e}")
            return 1.0  # Maximum risk on error
    
    def _calculate_consistency_score(self, returns: List[float], win_rate: float) -> float:
        """Calculate consistency score (0-1, higher is better)"""
        try:
            if len(returns) < 2:
                return 0.0
            
            # Coefficient of variation (lower is more consistent)
            mean_return = np.mean(returns)
            std_return = np.std(returns)
            
            if mean_return == 0:
                cv = float('inf')
            else:
                cv = abs(std_return / mean_return)
            
            # Normalize coefficient of variation
            cv_score = max(0.0, 1.0 - min(cv / 2.0, 1.0))
            
            # Win rate consistency bonus
            wr_score = win_rate
            
            # Combined consistency score
            consistency = (cv_score * 0.7 + wr_score * 0.3)
            
            return min(max(consistency, 0.0), 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating consistency score: {e}")
            return 0.0

class FraudDetector:
    """
    Fraud detection system for identifying fake traders and pump schemes
    """
    
    def __init__(self):
        self.fraud_patterns = {
            'unrealistic_returns': 0.3,  # >300% monthly returns
            'perfect_win_rate': 0.95,    # >95% win rate
            'pump_keywords': ['moon', 'pump', '1000x', 'guaranteed', 'risk-free'],
            'suspicious_timing': 3600,   # All trades within 1 hour
            'fake_followers': 10000,     # Sudden follower spikes
            'copy_paste_signals': 0.8    # >80% identical signals
        }
        logger.info("🕵️ Fraud detector initialized")
    
    def detect_fraud(self, trader_profile: TraderProfile, trades: List[TradeRecord], 
                    signals: List[TradingSignal]) -> Tuple[float, List[str]]:
        """
        Detect fraud indicators and return fraud score (0-1) and reasons
        """
        try:
            fraud_score = 0.0
            fraud_reasons = []
            
            # Check for unrealistic returns
            if trades:
                total_return_pct = sum([t.profit_loss_pct for t in trades if t.profit_loss_pct != 0])
                if total_return_pct > self.fraud_patterns['unrealistic_returns']:
                    fraud_score += 0.3
                    fraud_reasons.append("unrealistic_returns")
            
            # Check for perfect win rate
            if trades:
                winning_trades = len([t for t in trades if t.profit_loss > 0])
                win_rate = winning_trades / len(trades)
                if win_rate > self.fraud_patterns['perfect_win_rate']:
                    fraud_score += 0.25
                    fraud_reasons.append("perfect_win_rate")
            
            # Check for pump keywords in signals
            pump_keyword_count = 0
            total_signals = len(signals)
            
            for signal in signals:
                signal_text = f"{signal.reasoning} {signal.pair}".lower()
                for keyword in self.fraud_patterns['pump_keywords']:
                    if keyword in signal_text:
                        pump_keyword_count += 1
                        break
            
            if total_signals > 0 and pump_keyword_count / total_signals > 0.5:
                fraud_score += 0.2
                fraud_reasons.append("pump_keywords")
            
            # Check for suspicious timing patterns
            if len(trades) > 5:
                timestamps = [t.entry_timestamp for t in trades if t.entry_timestamp]
                if len(timestamps) > 1:
                    time_diffs = []
                    for i in range(1, len(timestamps)):
                        diff = abs((timestamps[i] - timestamps[i-1]).total_seconds())
                        time_diffs.append(diff)
                    
                    avg_time_diff = np.mean(time_diffs)
                    if avg_time_diff < self.fraud_patterns['suspicious_timing']:
                        fraud_score += 0.15
                        fraud_reasons.append("suspicious_timing")
            
            # Check for fake follower patterns
            if trader_profile.followers > self.fraud_patterns['fake_followers']:
                # Simple heuristic: very high followers but low engagement
                if len(signals) < 10 and trader_profile.followers > 50000:
                    fraud_score += 0.1
                    fraud_reasons.append("fake_followers")
            
            # Check for copy-paste signals
            if len(signals) > 5:
                unique_reasonings = set([s.reasoning for s in signals])
                uniqueness_ratio = len(unique_reasonings) / len(signals)
                if uniqueness_ratio < (1 - self.fraud_patterns['copy_paste_signals']):
                    fraud_score += 0.1
                    fraud_reasons.append("copy_paste_signals")
            
            return min(fraud_score, 1.0), fraud_reasons
            
        except Exception as e:
            logger.error(f"Error detecting fraud: {e}")
            return 0.0, []

class TraderRankingSystem:
    """
    Comprehensive trader ranking algorithm
    """
    
    def __init__(self):
        self.ranking_weights = {
            'performance': 0.35,      # Returns, Sharpe ratio, etc.
            'risk_management': 0.25,  # Max drawdown, volatility
            'consistency': 0.20,      # Win rate, consistency score
            'verification': 0.15,     # Blockchain verification
            'fraud_penalty': 0.05     # Fraud detection penalty
        }
        logger.info("🏆 Trader ranking system initialized")
    
    def rank_traders(self, traders_data: List[Dict]) -> List[Dict]:
        """
        Rank traders based on comprehensive scoring algorithm
        """
        try:
            ranked_traders = []
            
            for trader_data in traders_data:
                score = self._calculate_overall_score(trader_data)
                trader_data['overall_score'] = score
                trader_data['rank'] = 0  # Will be set after sorting
                ranked_traders.append(trader_data)
            
            # Sort by overall score (descending)
            ranked_traders.sort(key=lambda x: x['overall_score'], reverse=True)
            
            # Assign ranks
            for i, trader in enumerate(ranked_traders):
                trader['rank'] = i + 1
            
            logger.info(f"🏆 Ranked {len(ranked_traders)} traders")
            return ranked_traders
            
        except Exception as e:
            logger.error(f"Error ranking traders: {e}")
            return traders_data
    
    def _calculate_overall_score(self, trader_data: Dict) -> float:
        """
        Calculate overall score for a trader
        """
        try:
            metrics = trader_data.get('performance_metrics')
            if not metrics:
                return 0.0
            
            # Performance score (0-1)
            performance_score = self._calculate_performance_score(metrics)
            
            # Risk management score (0-1)
            risk_score = self._calculate_risk_management_score(metrics)
            
            # Consistency score (0-1)
            consistency_score = metrics.consistency_score
            
            # Verification score (0-1)
            verification_score = metrics.verification_score
            
            # Fraud penalty (0-1, subtracted from total)
            fraud_penalty = metrics.fraud_score
            
            # Calculate weighted overall score
            overall_score = (
                performance_score * self.ranking_weights['performance'] +
                risk_score * self.ranking_weights['risk_management'] +
                consistency_score * self.ranking_weights['consistency'] +
                verification_score * self.ranking_weights['verification'] -
                fraud_penalty * self.ranking_weights['fraud_penalty']
            )
            
            return max(min(overall_score, 1.0), 0.0)
            
        except Exception as e:
            logger.error(f"Error calculating overall score: {e}")
            return 0.0
    
    def _calculate_performance_score(self, metrics: PerformanceMetrics) -> float:
        """Calculate performance component score"""
        try:
            # Normalize returns (target: 20% monthly return = 1.0)
            return_score = min(abs(metrics.total_return_pct) / 0.20, 1.0)
            
            # Normalize Sharpe ratio (target: 2.0 = 1.0)
            sharpe_score = min(max(metrics.sharpe_ratio, 0) / 2.0, 1.0)
            
            # Win rate score
            win_rate_score = metrics.win_rate
            
            # Profit factor score (target: 2.0 = 1.0)
            pf_score = min(metrics.profit_factor / 2.0, 1.0) if metrics.profit_factor > 0 else 0.0
            
            # Weighted performance score
            performance_score = (
                return_score * 0.4 +
                sharpe_score * 0.3 +
                win_rate_score * 0.2 +
                pf_score * 0.1
            )
            
            return min(max(performance_score, 0.0), 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating performance score: {e}")
            return 0.0
    
    def _calculate_risk_management_score(self, metrics: PerformanceMetrics) -> float:
        """Calculate risk management component score"""
        try:
            # Invert risk score (lower risk = higher score)
            risk_score = 1.0 - metrics.risk_score
            
            # Max drawdown score (lower drawdown = higher score)
            dd_score = max(0.0, 1.0 - (metrics.max_drawdown_pct / 50.0))
            
            # Volatility score (lower volatility = higher score)
            vol_score = max(0.0, 1.0 - (metrics.volatility / 0.5))
            
            # Sortino ratio score
            sortino_score = min(max(metrics.sortino_ratio, 0) / 2.0, 1.0)
            
            # Weighted risk management score
            risk_mgmt_score = (
                risk_score * 0.3 +
                dd_score * 0.3 +
                vol_score * 0.2 +
                sortino_score * 0.2
            )
            
            return min(max(risk_mgmt_score, 0.0), 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating risk management score: {e}")
            return 0.0

class TraderPerformanceValidator:
    """
    Main trader performance validation system that coordinates all components
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.blockchain_verifier = BlockchainVerifier(config)
        self.performance_calculator = PerformanceCalculator()
        self.fraud_detector = FraudDetector()
        self.ranking_system = TraderRankingSystem()
        
        # Database for storing validation results
        self.db_path = self.config.get('db_path', 'trader_validation.db')
        self._init_database()
        self._lock = Lock()
        
        logger.info("✅ Trader performance validator initialized")
    
    def _init_database(self):
        """Initialize SQLite database for storing validation results"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create tables for storing validation data
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS trader_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        trader_username TEXT NOT NULL,
                        platform TEXT NOT NULL,
                        metrics_json TEXT NOT NULL,
                        fraud_score REAL DEFAULT 0.0,
                        fraud_reasons TEXT DEFAULT '',
                        verification_score REAL DEFAULT 0.0,
                        overall_score REAL DEFAULT 0.0,
                        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(trader_username, platform)
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS trade_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        trader_username TEXT NOT NULL,
                        platform TEXT NOT NULL,
                        pair TEXT NOT NULL,
                        signal_type TEXT NOT NULL,
                        entry_price REAL,
                        exit_price REAL,
                        profit_loss REAL,
                        profit_loss_pct REAL,
                        verified BOOLEAN DEFAULT FALSE,
                        verification_source TEXT DEFAULT '',
                        confidence_score REAL DEFAULT 0.0,
                        entry_timestamp DATETIME,
                        exit_timestamp DATETIME,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
                logger.info("📊 Trader validation database initialized")
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
    
    def validate_trader(self, trader_profile: TraderProfile, trades: List[TradeRecord], 
                       signals: List[TradingSignal], wallet_address: str = None) -> Dict:
        """
        Comprehensive trader validation including all components
        """
        try:
            logger.info(f"🔍 Validating trader: {trader_profile.username} on {trader_profile.platform}")
            
            # 1. Blockchain verification for trades
            verified_trades = []
            total_verification_score = 0.0
            
            for trade in trades:
                if wallet_address:
                    verified, confidence, source = self.blockchain_verifier.verify_trade_on_chain(trade, wallet_address)
                    trade.verified = verified
                    trade.confidence_score = confidence
                    trade.verification_source = source
                    total_verification_score += confidence
                
                verified_trades.append(trade)
            
            avg_verification_score = total_verification_score / len(trades) if trades else 0.0
            
            # 2. Calculate performance metrics
            performance_metrics = self.performance_calculator.calculate_metrics(verified_trades)
            performance_metrics.verification_score = avg_verification_score
            
            # 3. Fraud detection
            fraud_score, fraud_reasons = self.fraud_detector.detect_fraud(trader_profile, verified_trades, signals)
            performance_metrics.fraud_score = fraud_score
            
            # 4. Calculate overall score
            trader_data = {
                'trader_profile': trader_profile,
                'performance_metrics': performance_metrics,
                'trades': verified_trades,
                'signals': signals
            }
            
            overall_score = self.ranking_system._calculate_overall_score(trader_data)
            performance_metrics.overall_score = overall_score
            
            # 5. Store results in database
            self._store_validation_results(trader_profile, performance_metrics, verified_trades, fraud_reasons)
            
            validation_result = {
                'trader_username': trader_profile.username,
                'platform': trader_profile.platform,
                'performance_metrics': performance_metrics,
                'verified_trades': verified_trades,
                'fraud_score': fraud_score,
                'fraud_reasons': fraud_reasons,
                'overall_score': overall_score,
                'validation_timestamp': datetime.now()
            }
            
            logger.info(f"✅ Trader validation completed: {trader_profile.username} (Score: {overall_score:.3f})")
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating trader {trader_profile.username}: {e}")
            return {
                'trader_username': trader_profile.username,
                'platform': trader_profile.platform,
                'error': str(e),
                'validation_timestamp': datetime.now()
            }
    
    def _store_validation_results(self, trader_profile: TraderProfile, metrics: PerformanceMetrics, 
                                 trades: List[TradeRecord], fraud_reasons: List[str]):
        """Store validation results in database"""
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Store trader metrics
                    metrics_json = json.dumps({
                        'total_trades': metrics.total_trades,
                        'win_rate': metrics.win_rate,
                        'total_return_pct': metrics.total_return_pct,
                        'sharpe_ratio': metrics.sharpe_ratio,
                        'max_drawdown_pct': metrics.max_drawdown_pct,
                        'risk_score': metrics.risk_score,
                        'consistency_score': metrics.consistency_score,
                        'verification_score': metrics.verification_score
                    })
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO trader_metrics 
                        (trader_username, platform, metrics_json, fraud_score, fraud_reasons, 
                         verification_score, overall_score, last_updated)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        trader_profile.username,
                        trader_profile.platform,
                        metrics_json,
                        metrics.fraud_score,
                        ','.join(fraud_reasons),
                        metrics.verification_score,
                        metrics.overall_score,
                        datetime.now()
                    ))
                    
                    # Store trade records
                    for trade in trades:
                        cursor.execute('''
                            INSERT OR REPLACE INTO trade_records
                            (trader_username, platform, pair, signal_type, entry_price, exit_price,
                             profit_loss, profit_loss_pct, verified, verification_source, 
                             confidence_score, entry_timestamp, exit_timestamp)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            trade.trader_username,
                            trade.platform,
                            trade.pair,
                            trade.signal_type,
                            trade.entry_price,
                            trade.exit_price,
                            trade.profit_loss,
                            trade.profit_loss_pct,
                            trade.verified,
                            trade.verification_source,
                            trade.confidence_score,
                            trade.entry_timestamp,
                            trade.exit_timestamp
                        ))
                    
                    conn.commit()
                    
        except Exception as e:
            logger.error(f"Error storing validation results: {e}")
    
    def get_trader_rankings(self, platform: str = None, limit: int = 50) -> List[Dict]:
        """Get ranked list of validated traders"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = '''
                    SELECT trader_username, platform, metrics_json, fraud_score, 
                           verification_score, overall_score, last_updated
                    FROM trader_metrics
                '''
                params = []
                
                if platform:
                    query += ' WHERE platform = ?'
                    params.append(platform)
                
                query += ' ORDER BY overall_score DESC LIMIT ?'
                params.append(limit)
                
                cursor.execute(query, params)
                results = cursor.fetchall()
                
                rankings = []
                for i, row in enumerate(results):
                    rankings.append({
                        'rank': i + 1,
                        'trader_username': row[0],
                        'platform': row[1],
                        'metrics': json.loads(row[2]),
                        'fraud_score': row[3],
                        'verification_score': row[4],
                        'overall_score': row[5],
                        'last_updated': row[6]
                    })
                
                return rankings
                
        except Exception as e:
            logger.error(f"Error getting trader rankings: {e}")
            return []

# Example usage and testing
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize validator
    validator = TraderPerformanceValidator()
    
    # Example trader profile
    trader = TraderProfile(
        username="test_trader",
        platform="tradingview",
        profile_url="https://tradingview.com/u/test_trader",
        followers=5000,
        verified=True
    )
    
    # Example trades
    trades = [
        TradeRecord(
            trader_username="test_trader",
            platform="tradingview",
            pair="BTC/USDT",
            signal_type="BUY",
            entry_price=45000,
            exit_price=47000,
            profit_loss=2000,
            profit_loss_pct=0.044,
            entry_timestamp=datetime.now() - timedelta(days=1),
            exit_timestamp=datetime.now()
        )
    ]
    
    # Example signals
    signals = [
        TradingSignal(
            trader_username="test_trader",
            platform="tradingview",
            pair="BTC/USDT",
            signal_type="BUY",
            confidence=0.8,
            reasoning="Technical breakout pattern"
        )
    ]
    
    # Validate trader
    result = validator.validate_trader(trader, trades, signals)
    print(f"Validation result: {result}")
    
    # Get rankings
    rankings = validator.get_trader_rankings(limit=10)
    print(f"Top traders: {rankings}")