"""
Trade Decision Capturer
Captures comprehensive decision data when trades are generated
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.trade_logic_schema import TradeLogicDBManager

class TradeDecisionCapturer:
    """
    Captures comprehensive decision data for each trade signal
    """
    
    def __init__(self, db_path="trade_logic.db"):
        self.db_manager = TradeLogicDBManager(db_path)
        self.signal_weights = {
            'technical': 0.40,
            'onchain': 0.35,
            'sentiment': 0.25
        }
    
    def capture_decision(self, strategy_instance, dataframe, metadata):
        """
        Capture complete decision context when trade signal is generated
        """
        try:
            print(f"📊 Capturing decision data for {metadata['pair']}")
            
            decision_data = {
                'timestamp': datetime.now(),
                'pair': metadata['pair'],
                'timeframe': metadata.get('timeframe', '1h'),
                
                # Technical Analysis Data
                'technical_signals': self._capture_technical_signals(dataframe),
                'technical_score': self._get_latest_value(dataframe, 'technical_score', 0.0),
                'technical_reasoning': self._generate_technical_reasoning(dataframe),
                
                # On-Chain Data
                'onchain_signals': self._capture_onchain_signals(dataframe),
                'onchain_score': self._get_latest_value(dataframe, 'onchain_score', 0.0),
                'onchain_reasoning': self._generate_onchain_reasoning(dataframe),
                
                # Sentiment Data
                'sentiment_signals': self._capture_sentiment_signals(dataframe),
                'sentiment_score': self._get_latest_value(dataframe, 'sentiment_score', 0.0),
                'sentiment_reasoning': self._generate_sentiment_reasoning(dataframe),
                
                # Market Regime
                'market_regime': self._get_latest_value(dataframe, 'market_regime', 'neutral'),
                'regime_confidence': self._get_latest_value(dataframe, 'regime_confidence', 0.5),
                
                # Composite Decision
                'composite_score': self._get_latest_value(dataframe, 'multi_signal_score', 0.0),
                'final_decision': self._get_latest_value(dataframe, 'enter_long', 0),
                'position_size': self._calculate_position_size(dataframe),
                'risk_assessment': self._assess_risk(dataframe),
                
                # Decision Logic
                'decision_tree': self._build_decision_tree(dataframe),
                'threshold_analysis': self._analyze_thresholds(dataframe),
                'signal_weights': self.signal_weights,
                
                # Market Context
                'market_conditions': self._capture_market_context(dataframe),
                'volatility_metrics': self._capture_volatility(dataframe),
                'correlation_data': self._capture_correlations(dataframe)
            }
            
            # Store in database
            decision_id = self.db_manager.store_decision(decision_data)
            
            if decision_id:
                print(f"✅ Captured decision {decision_id} for {metadata['pair']}")
                return decision_id
            else:
                print(f"❌ Failed to capture decision for {metadata['pair']}")
                return None
                
        except Exception as e:
            print(f"❌ Error capturing decision: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _get_latest_value(self, dataframe, column, default=None):
        """Safely get the latest value from a dataframe column"""
        try:
            if column in dataframe.columns and len(dataframe) > 0:
                value = dataframe[column].iloc[-1]
                if pd.isna(value):
                    return default
                return float(value) if isinstance(value, (int, float, np.number)) else value
            return default
        except Exception:
            return default
    
    def _capture_technical_signals(self, dataframe):
        """Extract all technical indicator values and states"""
        try:
            signals = {}
            
            # RSI Analysis
            rsi_value = self._get_latest_value(dataframe, 'rsi', 50.0)
            signals['rsi'] = {
                'value': rsi_value,
                'signal': 'oversold' if rsi_value < 30 else 'overbought' if rsi_value > 70 else 'neutral',
                'trend': self._get_trend(dataframe, 'rsi'),
                'weight': 0.25,
                'contribution': self._calculate_contribution(rsi_value, 'rsi')
            }
            
            # MACD Analysis
            macd_value = self._get_latest_value(dataframe, 'macd', 0.0)
            macd_signal = self._get_latest_value(dataframe, 'macdsignal', 0.0)
            macd_hist = self._get_latest_value(dataframe, 'macdhist', 0.0)
            
            signals['macd'] = {
                'macd': macd_value,
                'signal': macd_signal,
                'histogram': macd_hist,
                'crossover': macd_value > macd_signal,
                'momentum': 'bullish' if macd_hist > 0 else 'bearish',
                'weight': 0.30,
                'contribution': self._calculate_contribution(macd_hist, 'macd')
            }
            
            # Moving Averages
            sma_20 = self._get_latest_value(dataframe, 'sma_20', 0.0)
            sma_50 = self._get_latest_value(dataframe, 'sma_50', 0.0)
            ema_12 = self._get_latest_value(dataframe, 'ema_12', 0.0)
            close_price = self._get_latest_value(dataframe, 'close', 0.0)
            
            signals['moving_averages'] = {
                'sma_20': sma_20,
                'sma_50': sma_50,
                'ema_12': ema_12,
                'price_vs_sma20': 'above' if close_price > sma_20 else 'below',
                'golden_cross': sma_20 > sma_50 if sma_20 and sma_50 else False,
                'weight': 0.25,
                'contribution': self._calculate_ma_contribution(close_price, sma_20, sma_50)
            }
            
            # Volume Analysis
            volume = self._get_latest_value(dataframe, 'volume', 0.0)
            volume_sma = self._get_latest_value(dataframe, 'volume_sma', volume)
            
            signals['volume'] = {
                'volume': volume,
                'volume_sma': volume_sma,
                'volume_ratio': volume / volume_sma if volume_sma > 0 else 1.0,
                'volume_trend': self._get_trend(dataframe, 'volume'),
                'weight': 0.20,
                'contribution': self._calculate_volume_contribution(volume, volume_sma)
            }
            
            return signals
            
        except Exception as e:
            print(f"⚠️ Error capturing technical signals: {e}")
            return {}
    
    def _capture_onchain_signals(self, dataframe):
        """Extract on-chain data signals"""
        try:
            signals = {}
            
            # Whale Activity
            whale_score = self._get_latest_value(dataframe, 'whale_score', 0.0)
            signals['whale_activity'] = {
                'value': whale_score,
                'signal': 'bullish' if whale_score > 0.6 else 'bearish' if whale_score < 0.4 else 'neutral',
                'weight': 0.40,
                'contribution': whale_score * 0.40
            }
            
            # Exchange Flows
            exchange_flow = self._get_latest_value(dataframe, 'exchange_flow_score', 0.0)
            signals['exchange_flows'] = {
                'value': exchange_flow,
                'signal': 'bullish' if exchange_flow < -0.5 else 'bearish' if exchange_flow > 0.5 else 'neutral',
                'weight': 0.30,
                'contribution': abs(exchange_flow) * 0.30
            }
            
            # DeFi Activity
            defi_score = self._get_latest_value(dataframe, 'defi_score', 0.0)
            signals['defi_activity'] = {
                'value': defi_score,
                'signal': 'bullish' if defi_score > 0.6 else 'bearish' if defi_score < 0.4 else 'neutral',
                'weight': 0.20,
                'contribution': defi_score * 0.20
            }
            
            # Network Activity
            network_score = self._get_latest_value(dataframe, 'network_score', 0.0)
            signals['network_activity'] = {
                'value': network_score,
                'signal': 'bullish' if network_score > 0.6 else 'bearish' if network_score < 0.4 else 'neutral',
                'weight': 0.10,
                'contribution': network_score * 0.10
            }
            
            return signals
            
        except Exception as e:
            print(f"⚠️ Error capturing on-chain signals: {e}")
            return {}
    
    def _capture_sentiment_signals(self, dataframe):
        """Extract sentiment analysis signals"""
        try:
            signals = {}
            
            # Twitter Sentiment
            twitter_sentiment = self._get_latest_value(dataframe, 'twitter_sentiment', 0.0)
            signals['twitter_sentiment'] = {
                'value': twitter_sentiment,
                'signal': 'bullish' if twitter_sentiment > 0.6 else 'bearish' if twitter_sentiment < 0.4 else 'neutral',
                'weight': 0.40,
                'contribution': twitter_sentiment * 0.40
            }
            
            # Reddit Sentiment
            reddit_sentiment = self._get_latest_value(dataframe, 'reddit_sentiment', 0.0)
            signals['reddit_sentiment'] = {
                'value': reddit_sentiment,
                'signal': 'bullish' if reddit_sentiment > 0.6 else 'bearish' if reddit_sentiment < 0.4 else 'neutral',
                'weight': 0.30,
                'contribution': reddit_sentiment * 0.30
            }
            
            # News Sentiment
            news_sentiment = self._get_latest_value(dataframe, 'news_sentiment', 0.0)
            signals['news_sentiment'] = {
                'value': news_sentiment,
                'signal': 'bullish' if news_sentiment > 0.6 else 'bearish' if news_sentiment < 0.4 else 'neutral',
                'weight': 0.20,
                'contribution': news_sentiment * 0.20
            }
            
            # Fear & Greed Index
            fear_greed = self._get_latest_value(dataframe, 'fear_greed_index', 50.0)
            signals['fear_greed_index'] = {
                'value': fear_greed,
                'signal': 'bullish' if fear_greed < 30 else 'bearish' if fear_greed > 70 else 'neutral',
                'weight': 0.10,
                'contribution': (50 - fear_greed) / 50 * 0.10  # Contrarian indicator
            }
            
            return signals
            
        except Exception as e:
            print(f"⚠️ Error capturing sentiment signals: {e}")
            return {}
    
    def _generate_technical_reasoning(self, dataframe):
        """Generate human-readable reasoning for technical analysis"""
        try:
            reasoning = []
            
            # RSI Analysis
            rsi = self._get_latest_value(dataframe, 'rsi', 50.0)
            if rsi < 30:
                reasoning.append(f"RSI at {rsi:.1f} indicates oversold conditions, suggesting potential upward reversal")
            elif rsi > 70:
                reasoning.append(f"RSI at {rsi:.1f} shows overbought conditions, indicating possible downward pressure")
            else:
                reasoning.append(f"RSI at {rsi:.1f} is in neutral territory")
            
            # MACD Analysis
            macd = self._get_latest_value(dataframe, 'macd', 0.0)
            macd_signal = self._get_latest_value(dataframe, 'macdsignal', 0.0)
            macd_hist = self._get_latest_value(dataframe, 'macdhist', 0.0)
            
            if macd > macd_signal and len(dataframe) > 1:
                prev_macd = self._get_latest_value(dataframe.iloc[:-1], 'macd', 0.0)
                prev_signal = self._get_latest_value(dataframe.iloc[:-1], 'macdsignal', 0.0)
                if prev_macd <= prev_signal:
                    reasoning.append("MACD bullish crossover detected, momentum shifting positive")
            
            if macd_hist > 0:
                reasoning.append("MACD histogram positive, confirming bullish momentum")
            elif macd_hist < 0:
                reasoning.append("MACD histogram negative, indicating bearish momentum")
            
            # Moving Average Analysis
            close = self._get_latest_value(dataframe, 'close', 0.0)
            sma_20 = self._get_latest_value(dataframe, 'sma_20', 0.0)
            sma_50 = self._get_latest_value(dataframe, 'sma_50', 0.0)
            
            if close > sma_20 > sma_50:
                reasoning.append("Price above both 20 and 50 SMA, indicating strong uptrend")
            elif close < sma_20 < sma_50:
                reasoning.append("Price below both 20 and 50 SMA, indicating strong downtrend")
            
            # Volume Analysis
            volume = self._get_latest_value(dataframe, 'volume', 0.0)
            volume_sma = self._get_latest_value(dataframe, 'volume_sma', volume)
            
            if volume > volume_sma * 1.5:
                reasoning.append("High volume confirms price movement strength")
            elif volume < volume_sma * 0.5:
                reasoning.append("Low volume suggests weak conviction in price movement")
            
            return reasoning
            
        except Exception as e:
            print(f"⚠️ Error generating technical reasoning: {e}")
            return ["Technical analysis reasoning unavailable"]
    
    def _generate_onchain_reasoning(self, dataframe):
        """Generate reasoning for on-chain analysis"""
        try:
            reasoning = []
            
            whale_score = self._get_latest_value(dataframe, 'whale_score', 0.0)
            if whale_score > 0.7:
                reasoning.append("Strong whale accumulation detected, indicating institutional confidence")
            elif whale_score < 0.3:
                reasoning.append("Whale distribution pattern observed, suggesting potential selling pressure")
            
            exchange_flow = self._get_latest_value(dataframe, 'exchange_flow_score', 0.0)
            if exchange_flow < -0.5:
                reasoning.append("Net outflow from exchanges suggests hodling behavior")
            elif exchange_flow > 0.5:
                reasoning.append("Net inflow to exchanges indicates potential selling pressure")
            
            return reasoning if reasoning else ["On-chain analysis shows neutral conditions"]
            
        except Exception as e:
            print(f"⚠️ Error generating on-chain reasoning: {e}")
            return ["On-chain analysis reasoning unavailable"]
    
    def _generate_sentiment_reasoning(self, dataframe):
        """Generate reasoning for sentiment analysis"""
        try:
            reasoning = []
            
            twitter_sentiment = self._get_latest_value(dataframe, 'twitter_sentiment', 0.0)
            if twitter_sentiment > 0.7:
                reasoning.append("Highly positive Twitter sentiment indicates strong community optimism")
            elif twitter_sentiment < 0.3:
                reasoning.append("Negative Twitter sentiment suggests community pessimism")
            
            fear_greed = self._get_latest_value(dataframe, 'fear_greed_index', 50.0)
            if fear_greed < 25:
                reasoning.append("Extreme fear in market presents contrarian buying opportunity")
            elif fear_greed > 75:
                reasoning.append("Extreme greed suggests market may be overheated")
            
            return reasoning if reasoning else ["Sentiment analysis shows neutral market mood"]
            
        except Exception as e:
            print(f"⚠️ Error generating sentiment reasoning: {e}")
            return ["Sentiment analysis reasoning unavailable"]
    
    def _build_decision_tree(self, dataframe):
        """Build decision tree showing step-by-step logic"""
        try:
            tree = {
                'root': 'Multi-Signal Analysis',
                'branches': []
            }
            
            # Technical branch
            technical_score = self._get_latest_value(dataframe, 'technical_score', 0.0)
            tree['branches'].append({
                'type': 'technical',
                'score': technical_score,
                'weight': self.signal_weights['technical'],
                'weighted_score': technical_score * self.signal_weights['technical'],
                'decision': 'bullish' if technical_score > 0.6 else 'bearish' if technical_score < 0.4 else 'neutral'
            })
            
            # On-chain branch
            onchain_score = self._get_latest_value(dataframe, 'onchain_score', 0.0)
            tree['branches'].append({
                'type': 'onchain',
                'score': onchain_score,
                'weight': self.signal_weights['onchain'],
                'weighted_score': onchain_score * self.signal_weights['onchain'],
                'decision': 'bullish' if onchain_score > 0.6 else 'bearish' if onchain_score < 0.4 else 'neutral'
            })
            
            # Sentiment branch
            sentiment_score = self._get_latest_value(dataframe, 'sentiment_score', 0.0)
            tree['branches'].append({
                'type': 'sentiment',
                'score': sentiment_score,
                'weight': self.signal_weights['sentiment'],
                'weighted_score': sentiment_score * self.signal_weights['sentiment'],
                'decision': 'bullish' if sentiment_score > 0.6 else 'bearish' if sentiment_score < 0.4 else 'neutral'
            })
            
            # Final decision
            composite_score = sum(branch['weighted_score'] for branch in tree['branches'])
            tree['final_score'] = composite_score
            tree['final_decision'] = 'BUY' if composite_score > 0.65 else 'SELL' if composite_score < 0.35 else 'HOLD'
            
            return tree
            
        except Exception as e:
            print(f"⚠️ Error building decision tree: {e}")
            return {}
    
    def _analyze_thresholds(self, dataframe):
        """Analyze how close signals are to their thresholds"""
        try:
            analysis = {}
            
            # RSI threshold analysis
            rsi = self._get_latest_value(dataframe, 'rsi', 50.0)
            analysis['rsi'] = {
                'value': rsi,
                'oversold_threshold': 30,
                'overbought_threshold': 70,
                'distance_to_oversold': abs(rsi - 30),
                'distance_to_overbought': abs(rsi - 70),
                'threshold_status': 'triggered' if rsi < 30 or rsi > 70 else 'not_triggered'
            }
            
            # Composite score threshold
            composite = self._get_latest_value(dataframe, 'multi_signal_score', 0.0)
            analysis['composite_score'] = {
                'value': composite,
                'buy_threshold': 0.65,
                'sell_threshold': 0.35,
                'distance_to_buy': abs(composite - 0.65),
                'distance_to_sell': abs(composite - 0.35),
                'threshold_status': 'buy_triggered' if composite > 0.65 else 'sell_triggered' if composite < 0.35 else 'neutral'
            }
            
            return analysis
            
        except Exception as e:
            print(f"⚠️ Error analyzing thresholds: {e}")
            return {}
    
    def _calculate_position_size(self, dataframe):
        """Calculate recommended position size based on risk"""
        try:
            composite_score = self._get_latest_value(dataframe, 'multi_signal_score', 0.0)
            volatility = self._get_latest_value(dataframe, 'volatility', 0.02)
            
            # Base position size on signal strength and inverse volatility
            base_size = 0.1  # 10% base position
            signal_multiplier = abs(composite_score - 0.5) * 2  # 0 to 1 multiplier
            volatility_adjustment = min(1.0, 0.02 / volatility)  # Reduce size for high volatility
            
            position_size = base_size * signal_multiplier * volatility_adjustment
            return round(position_size, 4)
            
        except Exception as e:
            print(f"⚠️ Error calculating position size: {e}")
            return 0.05  # Default 5% position
    
    def _assess_risk(self, dataframe):
        """Assess risk metrics for the trade"""
        try:
            volatility = self._get_latest_value(dataframe, 'volatility', 0.02)
            composite_score = self._get_latest_value(dataframe, 'multi_signal_score', 0.0)
            
            risk_assessment = {
                'volatility': volatility,
                'risk_level': 'high' if volatility > 0.05 else 'medium' if volatility > 0.02 else 'low',
                'signal_confidence': abs(composite_score - 0.5) * 2,
                'recommended_stop_loss': volatility * 2,  # 2x volatility stop loss
                'risk_reward_ratio': 3.0,  # Target 3:1 risk/reward
                'max_position_risk': 0.02  # Max 2% account risk per trade
            }
            
            return risk_assessment
            
        except Exception as e:
            print(f"⚠️ Error assessing risk: {e}")
            return {'risk_level': 'unknown'}
    
    def _capture_market_context(self, dataframe):
        """Capture current market conditions"""
        try:
            return {
                'trend': self._determine_trend(dataframe),
                'volatility_regime': self._determine_volatility_regime(dataframe),
                'market_phase': self._determine_market_phase(dataframe),
                'support_resistance': self._find_support_resistance(dataframe)
            }
        except Exception as e:
            print(f"⚠️ Error capturing market context: {e}")
            return {}
    
    def _capture_volatility(self, dataframe):
        """Capture volatility metrics"""
        try:
            if 'close' in dataframe.columns and len(dataframe) > 20:
                returns = dataframe['close'].pct_change().dropna()
                return {
                    'current_volatility': returns.std() * np.sqrt(24),  # Annualized hourly volatility
                    'volatility_percentile': self._calculate_percentile(returns.std(), returns.rolling(20).std()),
                    'volatility_trend': 'increasing' if len(returns) > 1 and returns.iloc[-1] > returns.iloc[-2] else 'decreasing'
                }
            return {}
        except Exception as e:
            print(f"⚠️ Error capturing volatility: {e}")
            return {}
    
    def _capture_correlations(self, dataframe):
        """Capture correlation data (placeholder for now)"""
        return {
            'btc_correlation': 0.8,  # Placeholder
            'market_correlation': 0.6,  # Placeholder
            'sector_correlation': 0.7   # Placeholder
        }
    
    # Helper methods
    def _get_trend(self, dataframe, column):
        """Determine if a column is trending up or down"""
        try:
            if column in dataframe.columns and len(dataframe) > 1:
                current = dataframe[column].iloc[-1]
                previous = dataframe[column].iloc[-2]
                if pd.notna(current) and pd.notna(previous):
                    return 'rising' if current > previous else 'falling'
            return 'neutral'
        except Exception:
            return 'neutral'
    
    def _calculate_contribution(self, value, indicator_type):
        """Calculate how much an indicator contributes to the decision"""
        try:
            if indicator_type == 'rsi':
                if value < 30:
                    return (30 - value) / 30 * 0.5  # Oversold contribution
                elif value > 70:
                    return (value - 70) / 30 * -0.5  # Overbought contribution
                return 0
            elif indicator_type == 'macd':
                return np.tanh(value * 10) * 0.3  # Normalize MACD contribution
            return 0
        except Exception:
            return 0
    
    def _calculate_ma_contribution(self, price, sma_20, sma_50):
        """Calculate moving average contribution"""
        try:
            if price and sma_20 and sma_50:
                price_vs_sma20 = (price - sma_20) / sma_20
                sma_alignment = 1 if sma_20 > sma_50 else -1
                return price_vs_sma20 * sma_alignment * 0.2
            return 0
        except Exception:
            return 0
    
    def _calculate_volume_contribution(self, volume, volume_sma):
        """Calculate volume contribution"""
        try:
            if volume and volume_sma and volume_sma > 0:
                volume_ratio = volume / volume_sma
                return min(0.2, (volume_ratio - 1) * 0.1)  # Cap at 0.2
            return 0
        except Exception:
            return 0
    
    def _determine_trend(self, dataframe):
        """Determine overall trend"""
        try:
            if 'close' in dataframe.columns and len(dataframe) > 20:
                sma_20 = dataframe['close'].rolling(20).mean().iloc[-1]
                sma_50 = dataframe['close'].rolling(50).mean().iloc[-1] if len(dataframe) > 50 else sma_20
                current_price = dataframe['close'].iloc[-1]
                
                if current_price > sma_20 > sma_50:
                    return 'uptrend'
                elif current_price < sma_20 < sma_50:
                    return 'downtrend'
                else:
                    return 'sideways'
            return 'unknown'
        except Exception:
            return 'unknown'
    
    def _determine_volatility_regime(self, dataframe):
        """Determine volatility regime"""
        try:
            if 'close' in dataframe.columns and len(dataframe) > 20:
                returns = dataframe['close'].pct_change().dropna()
                current_vol = returns.rolling(20).std().iloc[-1]
                avg_vol = returns.std()
                
                if current_vol > avg_vol * 1.5:
                    return 'high_volatility'
                elif current_vol < avg_vol * 0.5:
                    return 'low_volatility'
                else:
                    return 'normal_volatility'
            return 'unknown'
        except Exception:
            return 'unknown'
    
    def _determine_market_phase(self, dataframe):
        """Determine market phase"""
        # Simplified market phase detection
        return 'accumulation'  # Placeholder
    
    def _find_support_resistance(self, dataframe):
        """Find support and resistance levels"""
        try:
            if 'high' in dataframe.columns and 'low' in dataframe.columns and len(dataframe) > 20:
                recent_high = dataframe['high'].rolling(20).max().iloc[-1]
                recent_low = dataframe['low'].rolling(20).min().iloc[-1]
                return {
                    'resistance': recent_high,
                    'support': recent_low,
                    'range': recent_high - recent_low
                }
            return {}
        except Exception:
            return {}
    
    def _calculate_percentile(self, current_value, historical_series):
        """Calculate percentile of current value in historical context"""
        try:
            if len(historical_series.dropna()) > 0:
                return (historical_series < current_value).mean() * 100
            return 50  # Default to 50th percentile
        except Exception:
            return 50

if __name__ == "__main__":
    # Test the decision capturer
    import pandas as pd
    import numpy as np
    
    # Create test dataframe
    dates = pd.date_range('2024-01-01', periods=100, freq='1H')
    test_data = {
        'close': np.random.randn(100).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, 100),
        'rsi': np.random.uniform(20, 80, 100),
        'macd': np.random.uniform(-0.1, 0.1, 100),
        'macdsignal': np.random.uniform(-0.1, 0.1, 100),
        'macdhist': np.random.uniform(-0.05, 0.05, 100),
        'multi_signal_score': np.random.uniform(0.3, 0.8, 100),
        'technical_score': np.random.uniform(0.3, 0.8, 100),
        'enter_long': [0] * 99 + [1]  # Signal on last candle
    }
    
    df = pd.DataFrame(test_data, index=dates)
    
    # Test decision capture
    capturer = TradeDecisionCapturer("test_trade_logic.db")
    
    metadata = {'pair': 'BTC/USDT', 'timeframe': '1h'}
    decision_id = capturer.capture_decision(None, df, metadata)
    
    if decision_id:
        print(f"✅ Successfully captured test decision: {decision_id}")
        
        # Retrieve and display the decision
        decision = capturer.db_manager.get_decision(decision_id)
        print(f"📊 Decision data: {decision['pair']} - Score: {decision['composite_score']}")
        print(f"🔍 Technical reasoning: {decision['technical_reasoning']}")
    
    # Clean up
    os.remove("test_trade_logic.db")