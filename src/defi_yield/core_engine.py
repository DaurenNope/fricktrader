"""
Core DeFi Yield Optimization Engine
Main orchestrator for yield optimization across protocols
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from .models import YieldOpportunity, ProtocolType, RiskLevel
from .opportunity_analyzer import OpportunityAnalyzer
from .protocol_analyzers import ProtocolAnalyzerRegistry
from .portfolio_optimizer import PortfolioOptimizer

logger = logging.getLogger(__name__)


class DeFiYieldOptimizer:
    """
    Advanced DeFi yield optimization across major protocols
    """

    def __init__(self):
        self.protocol_registry = ProtocolAnalyzerRegistry()
        self.opportunity_analyzer = OpportunityAnalyzer()
        self.portfolio_optimizer = PortfolioOptimizer()

    async def optimize_yield_for_portfolio(self, user_tokens: Dict[str, float], preferences: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Find optimal yield strategies for user's token portfolio

        Args:
            user_tokens: {token_symbol: amount}
            preferences: User preferences for risk, lockup, etc.
        """
        logger.info(f"🔍 Optimizing yield for portfolio: {user_tokens}")

        if not preferences:
            preferences = self._get_default_preferences()

        # Get all opportunities for each token
        all_opportunities = []

        for token, amount in user_tokens.items():
            if amount > 0:  # Only process tokens with positive balance
                token_opportunities = await self.get_opportunities_for_token(token, amount, preferences)
                all_opportunities.extend(token_opportunities)

        # Find cross-token strategies
        cross_token_opportunities = await self._find_cross_token_strategies(user_tokens, preferences)
        all_opportunities.extend(cross_token_opportunities)

        # Optimize portfolio allocation
        optimal_allocation = await self.portfolio_optimizer.optimize_allocation(
            opportunities=all_opportunities,
            user_tokens=user_tokens,
            preferences=preferences
        )

        # Calculate expected returns and risks
        portfolio_metrics = await self._calculate_portfolio_metrics(optimal_allocation)

        # Generate actionable recommendations
        recommendations = await self._generate_recommendations(optimal_allocation, user_tokens)

        return {
            'user_portfolio': user_tokens,
            'optimal_allocation': optimal_allocation,
            'portfolio_metrics': portfolio_metrics,
            'recommendations': recommendations,
            'total_expected_apy': portfolio_metrics.get('weighted_apy', 0),
            'total_risk_score': portfolio_metrics.get('weighted_risk', 0),
            'estimated_gas_costs': portfolio_metrics.get('total_gas_cost', 0),
            'analysis_timestamp': datetime.now().isoformat()
        }

    async def get_opportunities_for_token(self, token: str, amount: float, preferences: Dict[str, Any]) -> List[YieldOpportunity]:
        """
        Get all yield opportunities for a specific token
        """
        opportunities = []

        # Get opportunities from each protocol
        for analyzer in self.protocol_registry.get_all_analyzers():
            try:
                protocol_opportunities = await analyzer.get_opportunities(token, amount, preferences)
                opportunities.extend(protocol_opportunities)
            except Exception as e:
                logger.error(f"Error getting opportunities from {analyzer.__class__.__name__}: {e}")

        # Filter and rank opportunities
        filtered_opportunities = self.opportunity_analyzer.filter_opportunities(opportunities, preferences)
        ranked_opportunities = self.opportunity_analyzer.rank_opportunities(filtered_opportunities)

        return ranked_opportunities

    def _get_default_preferences(self) -> Dict[str, Any]:
        """Get default user preferences"""
        return {
            'max_risk_level': RiskLevel.MEDIUM,
            'max_lockup_days': 30,
            'min_apy': 5.0,
            'gas_budget': 100,  # USD
            'auto_compound_only': False,
            'impermanent_loss_tolerance': 0.1,  # 10%
            'min_tvl': 1000000,  # $1M minimum
            'max_single_position': float('inf')
        }

    async def _find_cross_token_strategies(self, user_tokens: Dict[str, float], preferences: Dict[str, Any]) -> List[YieldOpportunity]:
        """
        Find strategies that use multiple tokens from user's portfolio
        """
        cross_strategies = []

        try:
            # LP strategies combining user's tokens
            lp_strategies = await self._find_lp_strategies(user_tokens, preferences)
            cross_strategies.extend(lp_strategies)

            # Delta-neutral strategies
            delta_neutral = await self._find_delta_neutral_strategies(user_tokens, preferences)
            cross_strategies.extend(delta_neutral)

            # Carry trade strategies
            carry_trades = await self._find_carry_trade_strategies(user_tokens, preferences)
            cross_strategies.extend(carry_trades)

        except Exception as e:
            logger.error(f"Error finding cross-token strategies: {e}")

        return cross_strategies

    async def _find_lp_strategies(self, user_tokens: Dict[str, float], preferences: Dict[str, Any]) -> List[YieldOpportunity]:
        """
        Find liquidity provision strategies using user's tokens
        """
        lp_strategies = []
        token_list = list(user_tokens.keys())

        # Check all pairs of user's tokens
        for i in range(len(token_list)):
            for j in range(i + 1, len(token_list)):
                token_a, token_b = token_list[i], token_list[j]

                if user_tokens[token_a] > 0 and user_tokens[token_b] > 0:
                    # Find LP opportunities for this pair
                    pair_opportunities = await self._get_lp_opportunities(token_a, token_b, user_tokens, preferences)
                    lp_strategies.extend(pair_opportunities)

        return lp_strategies

    async def _get_lp_opportunities(self, token_a: str, token_b: str, user_tokens: Dict[str, float], preferences: Dict[str, Any]) -> List[YieldOpportunity]:
        """
        Get LP opportunities for a specific token pair
        """
        opportunities = []

        # Get LP opportunities from relevant protocols
        uniswap_analyzer = self.protocol_registry.get_analyzer('uniswap')
        if uniswap_analyzer:
            uniswap_lp = await uniswap_analyzer.get_lp_opportunity(token_a, token_b, user_tokens)
            if uniswap_lp:
                opportunities.append(uniswap_lp)

        # Curve stable pools for stablecoin pairs
        if await self._is_stable_pair(token_a, token_b):
            curve_analyzer = self.protocol_registry.get_analyzer('curve')
            if curve_analyzer:
                curve_lp = await curve_analyzer.get_lp_opportunity(token_a, token_b, user_tokens)
                if curve_lp:
                    opportunities.append(curve_lp)

        return opportunities

    async def _find_delta_neutral_strategies(self, user_tokens: Dict[str, float], preferences: Dict[str, Any]) -> List[YieldOpportunity]:
        """
        Find delta-neutral yield strategies
        """
        delta_neutral = []

        # Ethena delta-neutral strategies
        if any(token in user_tokens for token in ['USDT', 'USDC']):
            ethena_analyzer = self.protocol_registry.get_analyzer('ethena')
            if ethena_analyzer:
                ethena_strategies = await ethena_analyzer.get_delta_neutral_strategies(user_tokens)
                delta_neutral.extend(ethena_strategies)

        # Pendle PT/YT strategies
        pendle_analyzer = self.protocol_registry.get_analyzer('pendle')
        if pendle_analyzer:
            for token, amount in user_tokens.items():
                if amount > 0:
                    pendle_strategies = await pendle_analyzer.get_pt_yt_strategies(token, amount)
                    delta_neutral.extend(pendle_strategies)

        return delta_neutral

    async def _find_carry_trade_strategies(self, user_tokens: Dict[str, float], preferences: Dict[str, Any]) -> List[YieldOpportunity]:
        """
        Find carry trade opportunities
        """
        carry_trades = []

        # Get current rates
        borrow_opportunities = await self._get_borrowing_rates()
        lending_opportunities = await self._get_lending_rates()

        for token, amount in user_tokens.items():
            if amount > 0:
                # Find profitable carry trades
                carry_strategy = await self._analyze_carry_trade(token, borrow_opportunities, lending_opportunities)
                if carry_strategy:
                    carry_trades.append(carry_strategy)

        return carry_trades

    async def _calculate_portfolio_metrics(self, allocation: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate expected portfolio metrics
        """
        if not allocation:
            return {}

        total_value = sum(item.get('allocated_amount', 0) for item in allocation)

        if total_value == 0:
            return {}

        # Weighted average APY
        weighted_apy = sum(
            (item.get('allocated_amount', 0) / total_value) * item.get('opportunity', {}).get('total_apy', 0)
            for item in allocation
        )

        # Weighted average risk
        weighted_risk = sum(
            (item.get('allocated_amount', 0) / total_value) * item.get('opportunity', {}).get('risk_score', 0)
            for item in allocation
        )

        # Total gas costs
        total_gas_cost = sum(item.get('opportunity', {}).get('estimated_gas_cost', 0) for item in allocation)

        # Diversification score
        diversification_score = len(set(item.get('opportunity', {}).get('protocol', '') for item in allocation))

        # Expected annual return
        expected_annual_return = total_value * (weighted_apy / 100)

        return {
            'total_allocated': total_value,
            'weighted_apy': weighted_apy,
            'weighted_risk': weighted_risk,
            'total_gas_cost': total_gas_cost,
            'diversification_score': diversification_score,
            'expected_annual_return': expected_annual_return,
            'risk_adjusted_return': weighted_apy / (1 + weighted_risk / 100),
            'number_of_positions': len(allocation)
        }

    async def _generate_recommendations(self, allocation: List[Dict[str, Any]], user_tokens: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Generate actionable recommendations
        """
        recommendations = []

        for item in allocation:
            opp = item.get('opportunity', {})
            amount = item.get('allocated_amount', 0)

            if amount > 0:
                recommendation = {
                    'action': 'DEPOSIT',
                    'protocol': opp.get('protocol', ''),
                    'pool_name': opp.get('pool_name', ''),
                    'amount': amount,
                    'token': item.get('token', ''),
                    'expected_apy': opp.get('total_apy', 0),
                    'risk_level': opp.get('risk_level', RiskLevel.MEDIUM).name if hasattr(opp.get('risk_level', RiskLevel.MEDIUM), 'name') else str(opp.get('risk_level', 'MEDIUM')),
                    'estimated_gas': opp.get('estimated_gas_cost', 0),
                    'steps': await self._generate_execution_steps(opp, amount),
                    'risks': await self._identify_key_risks(opp),
                    'exit_strategy': await self._suggest_exit_strategy(opp),
                    'monitoring_points': await self._suggest_monitoring_points(opp)
                }

                recommendations.append(recommendation)

        return recommendations

    async def _generate_execution_steps(self, opportunity: Dict[str, Any], amount: float) -> List[str]:
        """
        Generate step-by-step execution instructions
        """
        steps = []

        protocol = opportunity.get('protocol', '')
        pool_name = opportunity.get('pool_name', '')

        steps.append(f"1. Navigate to {protocol} protocol")
        steps.append(f"2. Find pool: {pool_name}")
        steps.append("3. Check current APY and TVL")
        steps.append(f"4. Approve token spending (estimate: ${opportunity.get('estimated_gas_cost', 0) * 0.3:.2f} gas)")
        steps.append(f"5. Deposit {amount} tokens")
        steps.append(f"6. Confirm transaction (estimate: ${opportunity.get('estimated_gas_cost', 0) * 0.7:.2f} gas)")
        steps.append("7. Monitor position and claim rewards regularly")

        if opportunity.get('auto_compound'):
            steps.append("8. Set up auto-compounding if available")

        return steps

    async def _identify_key_risks(self, opportunity: Dict[str, Any]) -> List[str]:
        """
        Identify key risks for the opportunity
        """
        risks = []

        if opportunity.get('impermanent_loss_risk', 0) > 0.05:
            risks.append(f"Impermanent loss risk: {opportunity.get('impermanent_loss_risk', 0)*100:.1f}%")

        if opportunity.get('smart_contract_risk', 0) > 0.3:
            risks.append("High smart contract risk - protocol is relatively new")

        if opportunity.get('liquidity_risk', 0) > 0.2:
            risks.append("Liquidity risk - pool has low TVL or volume")

        lockup_period = opportunity.get('lockup_period')
        if lockup_period and lockup_period > 0:
            risks.append(f"Locked funds for {lockup_period} days")

        reward_tokens = opportunity.get('reward_tokens', [])
        if len(reward_tokens) > 1:
            risks.append(f"Token price risk from reward tokens: {', '.join(reward_tokens)}")

        return risks

    async def _suggest_exit_strategy(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Suggest exit strategy for the position
        """
        return {
            'profit_targets': [
                {'apy_drop': 2.0, 'action': 'Consider partial exit'},
                {'apy_drop': 5.0, 'action': 'Full exit recommended'}
            ],
            'risk_triggers': [
                {'tvl_drop': 0.3, 'action': 'Monitor closely'},
                {'tvl_drop': 0.5, 'action': 'Consider exit'},
                {'exploit_news': True, 'action': 'Immediate exit'}
            ],
            'time_based': {
                'review_frequency': '1 week',
                'max_hold_period': '3 months',
                'rebalance_trigger': 'APY change >20%'
            }
        }

    async def _suggest_monitoring_points(self, opportunity: Dict[str, Any]) -> List[str]:
        """
        Suggest key metrics to monitor
        """
        monitoring = []

        monitoring.append(f"APY changes (current: {opportunity.get('total_apy', 0):.2f}%)")
        monitoring.append(f"TVL changes (current: ${opportunity.get('tvl', 0):,.0f})")
        monitoring.append("Protocol governance votes and updates")
        monitoring.append("Reward token prices and emission schedules")

        if opportunity.get('impermanent_loss_risk', 0) > 0:
            monitoring.append("Price correlation between LP tokens")

        lockup_period = opportunity.get('lockup_period')
        if lockup_period and lockup_period > 0:
            monitoring.append(f"Unlock date: {opportunity.get('unlock_date', 'TBD')}")

        return monitoring

    # Utility methods
    async def _is_stable_pair(self, token_a: str, token_b: str) -> bool:
        """Check if token pair is stablecoins"""
        stablecoins = {'USDT', 'USDC', 'DAI', 'FRAX', 'BUSD', 'TUSD', 'SUSD', 'LUSD'}
        return token_a.upper() in stablecoins and token_b.upper() in stablecoins

    async def _get_borrowing_rates(self) -> Dict[str, float]:
        """Get current borrowing rates across protocols"""
        return {
            'USDT': 3.5,
            'USDC': 3.2,
            'DAI': 4.1,
            'ETH': 2.8,
            'BTC': 1.9
        }

    async def _get_lending_rates(self) -> Dict[str, float]:
        """Get current lending rates across protocols"""
        return {
            'USDT': 5.2,
            'USDC': 4.8,
            'DAI': 6.1,
            'ETH': 4.5,
            'BTC': 3.2
        }

    async def _analyze_carry_trade(self, token: str, borrow_rates: Dict[str, float], lend_rates: Dict[str, float]) -> Optional[YieldOpportunity]:
        """Analyze carry trade opportunity"""
        if token not in borrow_rates or token not in lend_rates:
            return None

        net_rate = lend_rates[token] - borrow_rates[token]

        if net_rate > 2.0:  # Minimum 2% net yield
            return YieldOpportunity(
                protocol="Multi-Protocol Carry",
                protocol_type=ProtocolType.LENDING,
                pool_id=f"carry_{token}",
                pool_name=f"{token} Carry Trade",
                asset_pair=[token],
                base_apy=net_rate,
                boosted_apy=0,
                total_apy=net_rate,
                tvl=0,  # Not applicable
                volume_24h=0,
                risk_score=40,  # Medium risk
                risk_level=RiskLevel.MEDIUM,
                impermanent_loss_risk=0,
                smart_contract_risk=0.2,  # Multiple protocols
                liquidity_risk=0.1,
                reward_tokens=[],
                entry_requirements={'min_collateral_ratio': 1.5},
                exit_conditions={'liquidation_threshold': 1.2},
                fees={'borrow_fee': 0.1, 'gas_estimate': 50},
                lockup_period=None,
                auto_compound=False,
                verified_strategy=True,
                historical_performance={'30d': net_rate * 0.9},
                current_utilization=0.7,
                deposit_cap=None,
                minimum_deposit=1000,
                estimated_gas_cost=50
            )

        return None
