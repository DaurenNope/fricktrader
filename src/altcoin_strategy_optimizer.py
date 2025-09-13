#!/usr/bin/env python3
"""
Altcoin Strategy Optimizer - Advanced Testing System
Focus: Top 100 cryptocurrencies with shorts, longs, futures, hedging
Target: 1:4 Risk-to-Reward ratio optimization
"""

import subprocess
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
import itertools
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import requests

class AltcoinStrategyOptimizer:
    """
    Advanced altcoin strategy testing system focusing on top 100 cryptocurrencies
    with comprehensive long/short/futures/hedging strategies
    """
    
    def __init__(self, config_path: str = "config/config.json"):
        self.config_path = config_path
        self.results_dir = "user_data/backtest_results"
        self.strategies_dir = "user_data/strategies"
        
        # Top 100 altcoins (focusing on high-volume, liquid pairs)
        self.top_altcoins = [
            'ETH/USDT', 'BNB/USDT', 'XRP/USDT', 'ADA/USDT', 'DOGE/USDT',
            'MATIC/USDT', 'SOL/USDT', 'DOT/USDT', 'LTC/USDT', 'AVAX/USDT',
            'UNI/USDT', 'LINK/USDT', 'ATOM/USDT', 'ETC/USDT', 'XLM/USDT',
            'NEAR/USDT', 'ALGO/USDT', 'VET/USDT', 'ICP/USDT', 'FIL/USDT',
            'TRX/USDT', 'EOS/USDT', 'AAVE/USDT', 'GRT/USDT', 'SAND/USDT',
            'MANA/USDT', 'CRV/USDT', 'LRC/USDT', 'ENJ/USDT', 'COMP/USDT',
            'MKR/USDT', 'YFI/USDT', 'SNX/USDT', '1INCH/USDT', 'SUSHI/USDT',
            'BAL/USDT', 'REN/USDT', 'KNC/USDT', 'ZRX/USDT', 'BAND/USDT',
            'STORJ/USDT', 'ANT/USDT', 'BNT/USDT', 'NMR/USDT', 'MLN/USDT'
        ]
        
        # Advanced strategy configurations with 1:4 R:R focus
        self.altcoin_strategies = {
            'AltcoinMomentumLong': {
                'description': 'Long momentum strategy for altcoins with 1:4 R:R',
                'parameters': {
                    'buy_rsi': [25, 30, 35, 40, 45],
                    'buy_macd_above': [-0.02, -0.01, 0],
                    'buy_volume_factor': [1.2, 1.5, 2.0, 2.5],
                    'roi_1': [0.04, 0.05, 0.06],  # 4-6% for 1:4 R:R
                    'roi_2': [0.02, 0.025, 0.03],
                    'roi_3': [0.01, 0.015, 0.02],
                    'stoploss': [-0.01, -0.015, -0.02],  # 1-2% stop for 1:4 R:R
                    'trailing_stop': [True, False],
                    'trailing_stop_positive': [0.01, 0.015, 0.02]
                },
                'trading_mode': 'spot'
            },
            
            'AltcoinMeanReversionShort': {
                'description': 'Short mean reversion for overbought altcoins',
                'parameters': {
                    'sell_rsi': [70, 75, 80, 85, 90],
                    'sell_bb_upper_close': [0.99, 0.995, 1.0, 1.005],
                    'sell_volume_factor': [1.5, 2.0, 2.5, 3.0],
                    'roi_1': [0.04, 0.05, 0.06],  # Short profit targets
                    'roi_2': [0.02, 0.025, 0.03],
                    'stoploss': [-0.01, -0.015, -0.02],  # Tight stops
                    'use_short': [True],
                    'leverage': [2, 3, 5]  # Futures leverage
                },
                'trading_mode': 'futures'
            },
            
            'AltcoinBreakoutStrategy': {
                'description': 'Breakout strategy for altcoin pumps',
                'parameters': {
                    'buy_volume_factor': [2.0, 3.0, 4.0, 5.0],  # High volume breakouts
                    'buy_price_above_ema': [1.02, 1.03, 1.05],  # Above EMA by %
                    'buy_rsi_above': [50, 55, 60, 65],
                    'roi_1': [0.08, 0.10, 0.12, 0.15],  # Big altcoin moves
                    'roi_2': [0.04, 0.05, 0.06],
                    'roi_3': [0.02, 0.025, 0.03],
                    'stoploss': [-0.02, -0.025, -0.03],  # 2-3% stop
                    'timeframe_detail': ['5m', '15m', '1h'],
                    'confirm_trades_timeout': [300, 600, 900]  # Quick confirmation
                },
                'trading_mode': 'spot'
            },
            
            'AltcoinScalpingStrategy': {
                'description': 'High-frequency scalping for liquid altcoins',
                'parameters': {
                    'buy_rsi': [40, 45, 50],
                    'sell_rsi': [60, 65, 70],
                    'roi_1': [0.015, 0.02, 0.025],  # Quick profits
                    'roi_2': [0.01, 0.012, 0.015],
                    'stoploss': [-0.005, -0.008, -0.01],  # Very tight stops
                    'minimal_roi': {
                        "0": 0.02,   # 2% immediate
                        "10": 0.015, # 1.5% after 10 min
                        "30": 0.01,  # 1% after 30 min
                        "60": 0.005  # 0.5% after 1 hour
                    },
                    'timeframe': ['1m', '3m', '5m']
                },
                'trading_mode': 'spot'
            },
            
            'AltcoinHedgeStrategy': {
                'description': 'Long/short hedging strategy for market neutral',
                'parameters': {
                    'hedge_ratio': [0.5, 0.7, 0.8, 1.0],  # Long vs short ratio
                    'rebalance_threshold': [0.05, 0.10, 0.15],  # When to rebalance
                    'long_rsi_below': [40, 45, 50],
                    'short_rsi_above': [55, 60, 65, 70],
                    'correlation_threshold': [0.6, 0.7, 0.8],  # Pair correlation
                    'roi_target': [0.04, 0.06, 0.08],  # Total portfolio target
                    'max_drawdown_stop': [0.03, 0.05, 0.08]  # Portfolio stop
                },
                'trading_mode': 'futures'
            },
            
            'AltcoinVolatilityStrategy': {
                'description': 'High volatility altcoin strategy',
                'parameters': {
                    'volatility_threshold': [0.05, 0.08, 0.10, 0.15],  # Min volatility
                    'atr_multiplier': [1.5, 2.0, 2.5, 3.0],
                    'buy_on_dip': [-0.05, -0.08, -0.10, -0.15],  # Buy dips
                    'roi_1': [0.06, 0.08, 0.10, 0.12],  # High vol targets
                    'roi_2': [0.03, 0.04, 0.05],
                    'stoploss_atr': [1.0, 1.5, 2.0],  # ATR-based stops
                    'position_sizing': ['volatility_scaled', 'fixed', 'kelly']
                },
                'trading_mode': 'spot'
            }
        }
        
        # Timeframes for different strategies
        self.timeframe_configs = {
            'scalping': ['1m', '3m', '5m'],
            'swing': ['15m', '1h', '4h'],
            'position': ['1h', '4h', '1d'],
            'hedge': ['15m', '1h', '4h']
        }
        
        # Test periods for altcoin analysis
        self.altcoin_test_periods = [
            "20250801-20250906",  # Recent bull run
            "20250601-20250801",  # Summer period
            "20250401-20250601",  # Spring altcoin season
            "20250201-20250401",  # Winter recovery
            "20241201-20250201"   # Bear market test
        ]
    
    def get_top_altcoins_by_volume(self, limit: int = 50) -> List[str]:
        """Get top altcoins by 24h volume from Binance"""
        try:
            # Get 24hr ticker statistics from Binance
            response = requests.get(
                'https://api.binance.com/api/v3/ticker/24hr',
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Filter USDT pairs, exclude BTC, sort by volume
                altcoins = []
                for ticker in data:
                    symbol = ticker['symbol']
                    if (symbol.endswith('USDT') and 
                        not symbol.startswith('BTC') and
                        float(ticker['quoteVolume']) > 10000000):  # >10M USDT volume
                        
                        # Format for Freqtrade
                        pair = symbol.replace('USDT', '/USDT')
                        altcoins.append({
                            'pair': pair,
                            'volume': float(ticker['quoteVolume']),
                            'price_change': float(ticker['priceChangePercent'])
                        })
                
                # Sort by volume and take top N
                altcoins.sort(key=lambda x: x['volume'], reverse=True)
                return [coin['pair'] for coin in altcoins[:limit]]
            
        except Exception as e:
            print(f"Failed to fetch live altcoin data: {e}")
        
        # Fallback to hardcoded list
        return self.top_altcoins[:limit]
    
    def generate_strategy_parameters(self, strategy_name: str, 
                                   max_combinations: int = 20) -> List[Dict]:
        """Generate parameter combinations for altcoin strategies"""
        if strategy_name not in self.altcoin_strategies:
            return [{}]
        
        strategy_config = self.altcoin_strategies[strategy_name]
        params = strategy_config['parameters']
        
        # Generate all combinations
        keys = list(params.keys())
        values = list(params.values())
        
        all_combinations = list(itertools.product(*values))
        
        # Intelligent sampling for large parameter spaces
        if len(all_combinations) > max_combinations:
            # Use stratified sampling to cover parameter space well
            step = len(all_combinations) // max_combinations
            combinations = all_combinations[::step][:max_combinations]
            
            # Add some random combinations for exploration
            import random
            random_additions = random.sample(
                all_combinations, 
                min(5, max_combinations // 4)
            )
            combinations.extend(random_additions)
        else:
            combinations = all_combinations
        
        return [dict(zip(keys, combo)) for combo in combinations[:max_combinations]]
    
    def run_altcoin_strategy_test(self, strategy: str, pair: str, timeframe: str, 
                                 timerange: str, params: Dict) -> Optional[Dict]:
        """Run backtest for specific altcoin strategy"""
        try:
            # Build Freqtrade command
            cmd = [
                'freqtrade', 'backtesting',
                '--config', self.config_path,
                '--strategy', strategy,
                '--timeframe', timeframe,
                '--timerange', timerange,
                '--pairs', pair,
                '--export', 'trades',
                '--quiet'
            ]
            
            # Add strategy parameters
            for key, value in params.items():
                if key == 'minimal_roi' and isinstance(value, dict):
                    # Handle ROI dictionary
                    roi_str = json.dumps(value).replace(' ', '')
                    cmd.extend(['--strategy-parameter', f'{key}={roi_str}'])
                else:
                    cmd.extend(['--strategy-parameter', f'{key}={value}'])
            
            # Add trading mode if specified
            strategy_config = self.altcoin_strategies.get(strategy, {})
            trading_mode = strategy_config.get('trading_mode', 'spot')
            
            if trading_mode == 'futures':
                cmd.extend(['--enable-shorts'])
            
            print(f"🧪 Testing {strategy} on {pair} ({timeframe}) - {timerange}")
            
            # Execute backtest
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=240)
            
            if result.returncode != 0:
                print(f"❌ Failed: {result.stderr[:200]}")
                return None
            
            # Parse results
            with open(f'{self.results_dir}/.last_result.json', 'r') as f:
                backtest_data = json.load(f)
            
            if strategy not in backtest_data.get('strategy', {}):
                return None
            
            strategy_results = backtest_data['strategy'][strategy]
            
            # Calculate 1:4 R:R metrics
            total_return = strategy_results.get('profit_total_percent', 0)
            max_drawdown = abs(strategy_results.get('max_drawdown_percent', 0))
            
            # Risk-reward ratio calculation
            avg_win = strategy_results.get('avg_profit_winner', 0)
            avg_loss = abs(strategy_results.get('avg_profit_loser', 0.01))  # Avoid division by zero
            rr_ratio = avg_win / avg_loss if avg_loss > 0 else 0
            
            # 1:4 R:R score (higher is better when close to 4)
            rr_score = min(rr_ratio / 4.0, 2.0) if rr_ratio > 0 else 0
            
            # Altcoin-specific metrics
            volatility_adjusted_return = total_return / (max_drawdown + 0.1)
            consistency_score = strategy_results.get('winrate', 0) * strategy_results.get('profit_factor', 0)
            
            # Composite altcoin score
            altcoin_score = (
                total_return * 0.25 +                    # 25% weight on returns
                volatility_adjusted_return * 0.25 +      # 25% weight on risk-adjusted returns
                rr_score * 30 +                         # 30% weight on R:R ratio (key metric)
                strategy_results.get('sharpe', 0) * 5 +  # 10% weight on Sharpe (scaled)
                consistency_score * 0.05                 # 5% weight on consistency
            )
            
            formatted_result = {
                'strategy': strategy,
                'pair': pair,
                'timeframe': timeframe,
                'timerange': timerange,
                'parameters': params,
                'trading_mode': trading_mode,
                
                # Core performance metrics
                'total_return_pct': total_return,
                'max_drawdown_pct': max_drawdown,
                'volatility_adjusted_return': volatility_adjusted_return,
                
                # R:R specific metrics
                'risk_reward_ratio': rr_ratio,
                'rr_score': rr_score,
                'avg_win_pct': avg_win,
                'avg_loss_pct': avg_loss,
                
                # Trading metrics
                'total_trades': strategy_results.get('trade_count', 0),
                'win_rate': strategy_results.get('winrate', 0),
                'profit_factor': strategy_results.get('profit_factor', 0),
                'sharpe_ratio': strategy_results.get('sharpe', 0),
                'sortino_ratio': strategy_results.get('sortino', 0),
                'calmar_ratio': strategy_results.get('calmar', 0),
                
                # Best/worst trades
                'best_trade_pct': strategy_results.get('best_pair_profit_ratio', 0) * 100,
                'worst_trade_pct': strategy_results.get('worst_pair_profit_ratio', 0) * 100,
                
                # Composite scoring
                'altcoin_score': altcoin_score,
                'consistency_score': consistency_score,
                
                'timestamp': datetime.now().isoformat()
            }
            
            # Print progress
            rr_status = "🎯" if rr_ratio >= 3.5 else "⚠️" if rr_ratio >= 2.0 else "❌"
            print(f"{rr_status} {pair}: {total_return:.2f}% return, {rr_ratio:.2f}:1 R:R, Score: {altcoin_score:.2f}")
            
            return formatted_result
            
        except subprocess.TimeoutExpired:
            print(f"⏰ Timeout: {strategy} on {pair}")
            return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def run_comprehensive_altcoin_testing(self, 
                                        strategies: Optional[List[str]] = None,
                                        max_pairs: int = 30,
                                        max_param_combinations: int = 15,
                                        max_workers: int = 4) -> List[Dict]:
        """Run comprehensive altcoin strategy testing"""
        
        if strategies is None:
            strategies = list(self.altcoin_strategies.keys())
        
        # Get top altcoins by volume
        top_pairs = self.get_top_altcoins_by_volume(max_pairs)
        
        print("🚀 ALTCOIN STRATEGY OPTIMIZATION")
        print("=" * 60)
        print(f"🪙 Testing {len(strategies)} strategies on {len(top_pairs)} top altcoin pairs")
        print("🎯 Target: 1:4 Risk-to-Reward ratio optimization")
        print("💼 Modes: Spot, Futures, Shorts, Longs, Hedging")
        print(f"⚡ Max workers: {max_workers}")
        print()
        
        # Generate all test combinations
        all_tests = []
        for strategy in strategies:
            param_combinations = self.generate_strategy_parameters(
                strategy, max_param_combinations
            )
            
            # Select appropriate timeframes for strategy
            strategy_type = strategy.lower()
            if 'scalp' in strategy_type:
                timeframes = self.timeframe_configs['scalping']
            elif 'hedge' in strategy_type:
                timeframes = self.timeframe_configs['hedge']
            elif 'breakout' in strategy_type or 'momentum' in strategy_type:
                timeframes = self.timeframe_configs['swing']
            else:
                timeframes = ['1h', '4h']
            
            for params in param_combinations:
                for pair in top_pairs:
                    for timeframe in timeframes:
                        for timerange in self.altcoin_test_periods[:2]:  # Recent periods
                            all_tests.append((strategy, pair, timeframe, timerange, params))
        
        print(f"📊 Total tests to run: {len(all_tests)}")
        print(f"⏱️ Estimated time: {len(all_tests) * 30 / max_workers / 60:.1f} minutes")
        print()
        
        # Run tests in parallel
        results = []
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(self.run_altcoin_strategy_test, *test_args)
                for test_args in all_tests
            ]
            
            completed = 0
            successful = 0
            
            for future in as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)
                    successful += 1
                
                completed += 1
                
                if completed % 25 == 0 or completed == len(all_tests):
                    elapsed = time.time() - start_time
                    progress = completed / len(all_tests) * 100
                    eta = (elapsed / completed * (len(all_tests) - completed)) if completed > 0 else 0
                    
                    print(f"📈 Progress: {completed}/{len(all_tests)} ({progress:.1f}%) | "
                          f"Success: {successful} | ETA: {eta/60:.1f}m")
        
        total_time = time.time() - start_time
        print(f"\n✅ Testing completed in {total_time/60:.1f} minutes")
        print(f"🎯 Successful tests: {len(results)}/{len(all_tests)} ({len(results)/len(all_tests)*100:.1f}%)")
        
        return results
    
    def analyze_altcoin_results(self, results: List[Dict]) -> Dict:
        """Analyze altcoin testing results with focus on 1:4 R:R"""
        
        if not results:
            return {'error': 'No results to analyze'}
        
        df = pd.DataFrame(results)
        
        print(f"\n🔍 ANALYZING {len(results)} ALTCOIN STRATEGY RESULTS")
        print("=" * 60)
        
        # Filter for strategies with good R:R ratios
        high_rr_strategies = df[df['risk_reward_ratio'] >= 3.0]  # Close to 1:4
        decent_rr_strategies = df[df['risk_reward_ratio'] >= 2.0]  # Decent R:R
        
        print(f"🎯 Strategies with ≥3:1 R:R: {len(high_rr_strategies)} ({len(high_rr_strategies)/len(df)*100:.1f}%)")
        print(f"⚖️ Strategies with ≥2:1 R:R: {len(decent_rr_strategies)} ({len(decent_rr_strategies)/len(df)*100:.1f}%)")
        
        # Rank by altcoin score (which heavily weights R:R ratio)
        df_sorted = df.sort_values('altcoin_score', ascending=False)
        
        # Get best overall strategy
        best_strategy = df_sorted.iloc[0]
        
        # Get best R:R strategy specifically
        best_rr_strategy = df.loc[df['risk_reward_ratio'].idxmax()]
        
        # Analyze by trading mode
        mode_analysis = df.groupby('trading_mode').agg({
            'altcoin_score': 'mean',
            'total_return_pct': 'mean',
            'risk_reward_ratio': 'mean',
            'win_rate': 'mean',
            'max_drawdown_pct': 'mean'
        }).round(2)
        
        # Analyze by pair performance
        pair_analysis = df.groupby('pair').agg({
            'altcoin_score': 'mean',
            'total_return_pct': 'mean',
            'risk_reward_ratio': 'mean'
        }).sort_values('altcoin_score', ascending=False).head(10)
        
        # Analyze by strategy type
        strategy_analysis = df.groupby('strategy').agg({
            'altcoin_score': 'mean',
            'total_return_pct': 'mean',
            'risk_reward_ratio': 'mean',
            'win_rate': 'mean'
        }).sort_values('altcoin_score', ascending=False)
        
        analysis = {
            'total_strategies_tested': len(results),
            'high_rr_count': len(high_rr_strategies),
            'decent_rr_count': len(decent_rr_strategies),
            
            'best_overall_strategy': {
                'strategy': best_strategy['strategy'],
                'pair': best_strategy['pair'],
                'timeframe': best_strategy['timeframe'],
                'trading_mode': best_strategy['trading_mode'],
                'parameters': best_strategy['parameters'],
                'performance': {
                    'altcoin_score': float(best_strategy['altcoin_score']),
                    'total_return_pct': float(best_strategy['total_return_pct']),
                    'risk_reward_ratio': float(best_strategy['risk_reward_ratio']),
                    'win_rate': float(best_strategy['win_rate']),
                    'max_drawdown_pct': float(best_strategy['max_drawdown_pct']),
                    'sharpe_ratio': float(best_strategy['sharpe_ratio']),
                    'total_trades': int(best_strategy['total_trades'])
                }
            },
            
            'best_rr_strategy': {
                'strategy': best_rr_strategy['strategy'],
                'pair': best_rr_strategy['pair'],
                'timeframe': best_rr_strategy['timeframe'],
                'trading_mode': best_rr_strategy['trading_mode'],
                'performance': {
                    'risk_reward_ratio': float(best_rr_strategy['risk_reward_ratio']),
                    'total_return_pct': float(best_rr_strategy['total_return_pct']),
                    'win_rate': float(best_rr_strategy['win_rate']),
                    'avg_win_pct': float(best_rr_strategy['avg_win_pct']),
                    'avg_loss_pct': float(best_rr_strategy['avg_loss_pct'])
                }
            },
            
            'top_10_strategies': [
                {
                    'rank': idx + 1,
                    'strategy': row['strategy'],
                    'pair': row['pair'],
                    'timeframe': row['timeframe'],
                    'trading_mode': row['trading_mode'],
                    'altcoin_score': float(row['altcoin_score']),
                    'total_return_pct': float(row['total_return_pct']),
                    'risk_reward_ratio': float(row['risk_reward_ratio']),
                    'win_rate': float(row['win_rate']),
                    'parameters': row['parameters']
                }
                for idx, (_, row) in enumerate(df_sorted.head(10).iterrows())
            ],
            
            'trading_mode_analysis': mode_analysis.to_dict('index'),
            'top_pairs': pair_analysis.to_dict('index'),
            'strategy_rankings': strategy_analysis.to_dict('index'),
            
            'summary_stats': {
                'avg_return_pct': float(df['total_return_pct'].mean()),
                'avg_rr_ratio': float(df['risk_reward_ratio'].mean()),
                'avg_win_rate': float(df['win_rate'].mean()),
                'avg_max_drawdown': float(df['max_drawdown_pct'].mean()),
                'best_single_return': float(df['total_return_pct'].max()),
                'best_rr_ratio': float(df['risk_reward_ratio'].max()),
                'strategies_above_4_rr': len(df[df['risk_reward_ratio'] >= 4.0])
            },
            
            'timestamp': datetime.now().isoformat()
        }
        
        return analysis

def main():
    """Main execution function"""
    optimizer = AltcoinStrategyOptimizer()
    
    print("🚀 ALTCOIN STRATEGY OPTIMIZATION SYSTEM")
    print("🎯 Target: 1:4 Risk-to-Reward Ratio")
    print("🪙 Focus: Top 100 Altcoins")
    print("💼 Tools: Longs, Shorts, Futures, Hedging")
    print("=" * 60)
    
    # Run comprehensive testing
    results = optimizer.run_comprehensive_altcoin_testing(
        max_pairs=25,           # Test top 25 altcoins
        max_param_combinations=10,  # 10 parameter combos per strategy
        max_workers=3           # 3 parallel workers
    )
    
    if results:
        # Analyze results
        analysis = optimizer.analyze_altcoin_results(results)
        
        # Print key findings
        print("\n🏆 KEY FINDINGS:")
        print("=" * 60)
        
        best = analysis['best_overall_strategy']
        print(f"🥇 Best Overall: {best['strategy']} on {best['pair']} ({best['timeframe']})")
        print(f"   💰 Return: {best['performance']['total_return_pct']:.2f}%")
        print(f"   🎯 R:R Ratio: {best['performance']['risk_reward_ratio']:.2f}:1")
        print(f"   ✅ Win Rate: {best['performance']['win_rate']:.1f}%")
        print(f"   📉 Max DD: {best['performance']['max_drawdown_pct']:.2f}%")
        
        best_rr = analysis['best_rr_strategy']
        print(f"\n🎯 Best R:R: {best_rr['strategy']} on {best_rr['pair']}")
        print(f"   🏹 R:R Ratio: {best_rr['performance']['risk_reward_ratio']:.2f}:1")
        print(f"   💰 Avg Win: {best_rr['performance']['avg_win_pct']:.2f}%")
        print(f"   💀 Avg Loss: {best_rr['performance']['avg_loss_pct']:.2f}%")
        
        print("\n📊 Summary:")
        stats = analysis['summary_stats']
        print(f"   🎯 Strategies ≥4:1 R:R: {stats['strategies_above_4_rr']}")
        print(f"   📈 Best R:R Found: {stats['best_rr_ratio']:.2f}:1")
        print(f"   💰 Best Return: {stats['best_single_return']:.2f}%")
        print(f"   ⚖️ Avg R:R: {stats['avg_rr_ratio']:.2f}:1")
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(f'altcoin_optimization_{timestamp}.json', 'w') as f:
            json.dump({
                'raw_results': results,
                'analysis': analysis
            }, f, indent=2)
        
        print(f"\n💾 Results saved to altcoin_optimization_{timestamp}.json")
        print("\n🚀 Ready to implement the best altcoin strategies!")
        
    else:
        print("❌ No results obtained. Check Freqtrade configuration.")

if __name__ == "__main__":
    main()