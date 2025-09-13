"""
Portfolio Optimization Engine
Handles allocation optimization across DeFi opportunities
"""

import logging
from typing import Dict, List, Any
from .models import YieldOpportunity, RiskLevel

logger = logging.getLogger(__name__)


class PortfolioOptimizer:
    """
    Optimize DeFi portfolio allocation across opportunities
    """

    async def optimize_allocation(self, opportunities: List[YieldOpportunity], user_tokens: Dict[str, float], preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Optimize allocation across opportunities

        Args:
            opportunities: Available yield opportunities
            user_tokens: User's token balances
            preferences: User preferences

        Returns:
            List of allocation recommendations
        """
        logger.info(f"Optimizing allocation for {len(opportunities)} opportunities")

        if not opportunities or not user_tokens:
            return []

        # Group opportunities by token
        token_opportunities = self._group_opportunities_by_token(opportunities, user_tokens)

        # Apply allocation strategy based on preferences
        strategy = preferences.get('allocation_strategy', 'balanced')

        if strategy == 'conservative':
            return await self._conservative_allocation(token_opportunities, user_tokens, preferences)
        elif strategy == 'aggressive':
            return await self._aggressive_allocation(token_opportunities, user_tokens, preferences)
        elif strategy == 'max_diversification':
            return await self._max_diversification_allocation(token_opportunities, user_tokens, preferences)
        else:  # balanced (default)
            return await self._balanced_allocation(token_opportunities, user_tokens, preferences)

    async def calculate_portfolio_risk(self, allocations: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate portfolio-wide risk metrics

        Args:
            allocations: List of allocation decisions

        Returns:
            Risk metrics dictionary
        """
        if not allocations:
            return {'total_risk': 0, 'risk_score': 0}

        total_value = sum(alloc.get('allocated_amount', 0) for alloc in allocations)
        if total_value == 0:
            return {'total_risk': 0, 'risk_score': 0}

        # Weighted risk calculation
        weighted_risk = 0
        for alloc in allocations:
            weight = alloc.get('allocated_amount', 0) / total_value
            opp_risk = alloc.get('opportunity', {}).get('risk_score', 50)
            weighted_risk += weight * opp_risk

        # Calculate risk diversification benefit
        protocols = set(alloc.get('opportunity', {}).get('protocol', '') for alloc in allocations)
        diversification_benefit = min(len(protocols) * 2, 10)  # Max 10 point reduction

        adjusted_risk = max(weighted_risk - diversification_benefit, 0)

        return {
            'total_risk': adjusted_risk,
            'weighted_risk': weighted_risk,
            'diversification_benefit': diversification_benefit,
            'risk_score': adjusted_risk,
            'concentration_risk': self._calculate_concentration_risk(allocations)
        }

    async def optimize_for_target_return(self, opportunities: List[YieldOpportunity], user_tokens: Dict[str, float], target_apy: float, max_risk: float) -> List[Dict[str, Any]]:
        """
        Optimize allocation to achieve target return within risk constraints

        Args:
            opportunities: Available opportunities
            user_tokens: User's tokens
            target_apy: Target APY to achieve
            max_risk: Maximum acceptable risk score

        Returns:
            Optimized allocation
        """
        logger.info(f"Optimizing for target APY: {target_apy}%, max risk: {max_risk}")

        # Filter opportunities by risk constraint
        suitable_opps = [opp for opp in opportunities if opp.risk_score <= max_risk]

        if not suitable_opps:
            logger.warning("No opportunities meet risk constraints")
            return []

        # Sort by efficiency score (APY/risk ratio)
        sorted_opps = sorted(suitable_opps, key=lambda x: x.total_apy / (1 + x.risk_score / 100), reverse=True)

        allocation = []
        remaining_tokens = user_tokens.copy()

        for opp in sorted_opps:
            for token in opp.asset_pair:
                if token in remaining_tokens and remaining_tokens[token] > 0:
                    # Calculate how much to allocate to achieve target while staying within risk
                    allocation_amount = min(
                        remaining_tokens[token] * 0.8,  # Max 80% of available
                        opp.minimum_deposit * 2  # Conservative sizing
                    )

                    if allocation_amount >= opp.minimum_deposit:
                        allocation.append({
                            'token': token,
                            'opportunity': opp.__dict__,
                            'allocated_amount': allocation_amount,
                            'allocation_percent': allocation_amount / user_tokens[token]
                        })

                        remaining_tokens[token] -= allocation_amount

                        # Check if we've reached target return
                        current_apy = await self._calculate_portfolio_apy(allocation)
                        if current_apy >= target_apy:
                            break

        return allocation

    def _group_opportunities_by_token(self, opportunities: List[YieldOpportunity], user_tokens: Dict[str, float]) -> Dict[str, List[YieldOpportunity]]:
        """
        Group opportunities by the tokens user holds

        Args:
            opportunities: List of opportunities
            user_tokens: User's token balances

        Returns:
            Dictionary mapping tokens to relevant opportunities
        """
        token_opps = {}

        for token in user_tokens.keys():
            if user_tokens[token] > 0:
                token_opps[token] = []

                for opp in opportunities:
                    if token in opp.asset_pair:
                        token_opps[token].append(opp)

                # Sort by efficiency score
                token_opps[token].sort(key=lambda x: x.get_efficiency_score(), reverse=True)

        return token_opps

    async def _balanced_allocation(self, token_opportunities: Dict[str, List[YieldOpportunity]], user_tokens: Dict[str, float], preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Balanced allocation strategy - moderate diversification and risk
        """
        allocation = []

        for token, amount in user_tokens.items():
            if amount > 0 and token in token_opportunities:
                opps = token_opportunities[token]

                if opps:
                    # Take top 2-3 opportunities for diversification
                    selected_opps = opps[:min(3, len(opps))]

                    # Allocate with decreasing weights
                    weights = [0.5, 0.3, 0.2][:len(selected_opps)]
                    remaining_amount = amount

                    for i, opp in enumerate(selected_opps):
                        allocation_amount = remaining_amount * weights[i]

                        if allocation_amount >= opp.minimum_deposit:
                            allocation.append({
                                'token': token,
                                'opportunity': opp.__dict__,
                                'allocated_amount': allocation_amount,
                                'allocation_percent': allocation_amount / amount
                            })
                            remaining_amount -= allocation_amount

        return allocation

    async def _conservative_allocation(self, token_opportunities: Dict[str, List[YieldOpportunity]], user_tokens: Dict[str, float], preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Conservative allocation - prioritize low risk, proven protocols
        """
        allocation = []

        for token, amount in user_tokens.items():
            if amount > 0 and token in token_opportunities:
                # Filter for low-risk opportunities
                low_risk_opps = [opp for opp in token_opportunities[token] if opp.risk_level in [RiskLevel.VERY_LOW, RiskLevel.LOW]]

                if low_risk_opps:
                    # Take the best low-risk opportunity
                    best_opp = low_risk_opps[0]
                    allocation_amount = amount * 0.6  # Conservative 60% allocation

                    if allocation_amount >= best_opp.minimum_deposit:
                        allocation.append({
                            'token': token,
                            'opportunity': best_opp.__dict__,
                            'allocated_amount': allocation_amount,
                            'allocation_percent': 0.6
                        })

        return allocation

    async def _aggressive_allocation(self, token_opportunities: Dict[str, List[YieldOpportunity]], user_tokens: Dict[str, float], preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Aggressive allocation - maximize yield, accept higher risk
        """
        allocation = []

        for token, amount in user_tokens.items():
            if amount > 0 and token in token_opportunities:
                opps = token_opportunities[token]

                if opps:
                    # Take the highest APY opportunity
                    best_opp = max(opps, key=lambda x: x.total_apy)
                    allocation_amount = amount * 0.9  # Aggressive 90% allocation

                    if allocation_amount >= best_opp.minimum_deposit:
                        allocation.append({
                            'token': token,
                            'opportunity': best_opp.__dict__,
                            'allocated_amount': allocation_amount,
                            'allocation_percent': 0.9
                        })

        return allocation

    async def _max_diversification_allocation(self, token_opportunities: Dict[str, List[YieldOpportunity]], user_tokens: Dict[str, float], preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Maximum diversification - spread across many protocols and strategies
        """
        allocation = []

        # Collect all unique opportunities across all tokens
        all_opportunities = []
        for token, opps in token_opportunities.items():
            for opp in opps:
                if user_tokens.get(token, 0) > 0:
                    all_opportunities.append((token, opp))

        # Remove duplicates based on protocol and pool
        unique_opportunities = []
        seen = set()

        for token, opp in all_opportunities:
            key = (opp.protocol, opp.pool_id)
            if key not in seen:
                unique_opportunities.append((token, opp))
                seen.add(key)

        # Allocate equally across all unique opportunities
        if unique_opportunities:
            equal_weight = 1.0 / len(unique_opportunities)

            for token, opp in unique_opportunities:
                available_amount = user_tokens[token]
                allocation_amount = available_amount * equal_weight * 0.8  # 80% of equal weight

                if allocation_amount >= opp.minimum_deposit:
                    allocation.append({
                        'token': token,
                        'opportunity': opp.__dict__,
                        'allocated_amount': allocation_amount,
                        'allocation_percent': allocation_amount / available_amount
                    })

        return allocation

    def _calculate_concentration_risk(self, allocations: List[Dict[str, Any]]) -> float:
        """
        Calculate concentration risk (higher when concentrated in few protocols/assets)
        """
        if not allocations:
            return 0

        total_value = sum(alloc.get('allocated_amount', 0) for alloc in allocations)
        if total_value == 0:
            return 0

        # Protocol concentration
        protocol_weights = {}
        for alloc in allocations:
            protocol = alloc.get('opportunity', {}).get('protocol', 'unknown')
            weight = alloc.get('allocated_amount', 0) / total_value
            protocol_weights[protocol] = protocol_weights.get(protocol, 0) + weight

        # Calculate Herfindahl index for concentration
        herfindahl = sum(weight ** 2 for weight in protocol_weights.values())

        # Convert to risk score (0-100, where 100 is maximum concentration)
        concentration_risk = min(herfindahl * 100, 100)

        return concentration_risk

    async def _calculate_portfolio_apy(self, allocations: List[Dict[str, Any]]) -> float:
        """
        Calculate weighted average APY for portfolio
        """
        if not allocations:
            return 0

        total_value = sum(alloc.get('allocated_amount', 0) for alloc in allocations)
        if total_value == 0:
            return 0

        weighted_apy = 0
        for alloc in allocations:
            weight = alloc.get('allocated_amount', 0) / total_value
            apy = alloc.get('opportunity', {}).get('total_apy', 0)
            weighted_apy += weight * apy

        return weighted_apy

    async def rebalance_portfolio(self, current_allocations: List[Dict[str, Any]], new_opportunities: List[YieldOpportunity], rebalance_threshold: float = 0.02) -> Dict[str, Any]:
        """
        Determine if portfolio should be rebalanced based on new opportunities

        Args:
            current_allocations: Current portfolio allocation
            new_opportunities: New opportunities available
            rebalance_threshold: Minimum improvement threshold to trigger rebalance

        Returns:
            Rebalancing recommendation
        """
        current_apy = await self._calculate_portfolio_apy(current_allocations)
        current_risk = await self.calculate_portfolio_risk(current_allocations)

        # Find optimal allocation with new opportunities
        user_tokens = {}
        for alloc in current_allocations:
            token = alloc.get('token', '')
            amount = alloc.get('allocated_amount', 0)
            user_tokens[token] = user_tokens.get(token, 0) + amount

        new_allocation = await self.optimize_allocation(new_opportunities, user_tokens, {})
        new_apy = await self._calculate_portfolio_apy(new_allocation)
        new_risk = await self.calculate_portfolio_risk(new_allocation)

        # Calculate improvement
        apy_improvement = new_apy - current_apy
        risk_change = new_risk.get('risk_score', 0) - current_risk.get('risk_score', 0)

        # Risk-adjusted improvement
        risk_adjusted_improvement = apy_improvement - (risk_change * 0.1)  # Penalize risk increase

        should_rebalance = risk_adjusted_improvement > rebalance_threshold * 100  # Convert to percentage

        return {
            'should_rebalance': should_rebalance,
            'current_apy': current_apy,
            'new_apy': new_apy,
            'apy_improvement': apy_improvement,
            'current_risk': current_risk.get('risk_score', 0),
            'new_risk': new_risk.get('risk_score', 0),
            'risk_change': risk_change,
            'risk_adjusted_improvement': risk_adjusted_improvement,
            'recommended_allocation': new_allocation if should_rebalance else current_allocations
        }
