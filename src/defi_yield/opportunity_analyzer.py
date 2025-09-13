"""
Opportunity Analysis and Filtering
Handles filtering, ranking, and analysis of yield opportunities
"""

import logging
from typing import Dict, List, Any
from .models import YieldOpportunity, RiskLevel

logger = logging.getLogger(__name__)


class OpportunityAnalyzer:
    """
    Analyzes and filters DeFi yield opportunities based on user preferences
    """

    def filter_opportunities(self, opportunities: List[YieldOpportunity], preferences: Dict[str, Any]) -> List[YieldOpportunity]:
        """
        Filter opportunities based on user preferences

        Args:
            opportunities: List of yield opportunities to filter
            preferences: User preferences dictionary

        Returns:
            List of filtered opportunities
        """
        filtered = []

        for opp in opportunities:
            if self._passes_filters(opp, preferences):
                filtered.append(opp)

        logger.info(f"Filtered {len(opportunities)} opportunities down to {len(filtered)}")
        return filtered

    def rank_opportunities(self, opportunities: List[YieldOpportunity]) -> List[YieldOpportunity]:
        """
        Rank opportunities by efficiency score

        Args:
            opportunities: List of opportunities to rank

        Returns:
            List of opportunities ranked by efficiency score (highest first)
        """
        # Calculate efficiency scores
        for opp in opportunities:
            opp.efficiency_score = opp.get_efficiency_score()

        # Sort by efficiency score (highest first)
        ranked = sorted(opportunities, key=lambda x: getattr(x, 'efficiency_score', 0), reverse=True)

        logger.info(f"Ranked {len(opportunities)} opportunities")
        return ranked

    def analyze_opportunity_distribution(self, opportunities: List[YieldOpportunity]) -> Dict[str, Any]:
        """
        Analyze the distribution of opportunities across protocols and risk levels

        Args:
            opportunities: List of opportunities to analyze

        Returns:
            Dictionary with distribution analysis
        """
        if not opportunities:
            return {}

        # Protocol distribution
        protocol_count = {}
        for opp in opportunities:
            protocol_count[opp.protocol] = protocol_count.get(opp.protocol, 0) + 1

        # Risk level distribution
        risk_distribution = {}
        for opp in opportunities:
            risk_name = opp.risk_level.name
            risk_distribution[risk_name] = risk_distribution.get(risk_name, 0) + 1

        # APY statistics
        apys = [opp.total_apy for opp in opportunities]
        apy_stats = {
            'min': min(apys),
            'max': max(apys),
            'avg': sum(apys) / len(apys),
            'median': sorted(apys)[len(apys) // 2]
        }

        # TVL statistics
        tvls = [opp.tvl for opp in opportunities]
        tvl_stats = {
            'min': min(tvls),
            'max': max(tvls),
            'avg': sum(tvls) / len(tvls),
            'total': sum(tvls)
        }

        return {
            'total_opportunities': len(opportunities),
            'protocol_distribution': protocol_count,
            'risk_distribution': risk_distribution,
            'apy_statistics': apy_stats,
            'tvl_statistics': tvl_stats,
            'top_opportunities': self._get_top_opportunities(opportunities, 5)
        }

    def calculate_diversification_score(self, opportunities: List[YieldOpportunity]) -> float:
        """
        Calculate diversification score for a set of opportunities

        Args:
            opportunities: List of opportunities

        Returns:
            Diversification score (0-100)
        """
        if not opportunities:
            return 0.0

        # Protocol diversification (40% weight)
        protocols = set(opp.protocol for opp in opportunities)
        protocol_score = min(len(protocols) / 5.0, 1.0) * 40

        # Protocol type diversification (30% weight)
        protocol_types = set(opp.protocol_type for opp in opportunities)
        type_score = min(len(protocol_types) / 4.0, 1.0) * 30

        # Risk level diversification (20% weight)
        risk_levels = set(opp.risk_level for opp in opportunities)
        risk_score = min(len(risk_levels) / 3.0, 1.0) * 20

        # Asset diversification (10% weight)
        all_assets = set()
        for opp in opportunities:
            all_assets.update(opp.asset_pair)
        asset_score = min(len(all_assets) / 8.0, 1.0) * 10

        return protocol_score + type_score + risk_score + asset_score

    def identify_correlation_risks(self, opportunities: List[YieldOpportunity]) -> List[Dict[str, Any]]:
        """
        Identify potential correlation risks between opportunities

        Args:
            opportunities: List of opportunities to analyze

        Returns:
            List of identified correlation risks
        """
        correlation_risks = []

        # Check for protocol concentration
        protocol_counts = {}
        for opp in opportunities:
            protocol_counts[opp.protocol] = protocol_counts.get(opp.protocol, 0) + 1

        for protocol, count in protocol_counts.items():
            if count > len(opportunities) * 0.4:  # >40% concentration
                correlation_risks.append({
                    'type': 'protocol_concentration',
                    'protocol': protocol,
                    'concentration': count / len(opportunities),
                    'risk_level': 'HIGH' if count > len(opportunities) * 0.6 else 'MEDIUM',
                    'description': f'High concentration in {protocol} protocol'
                })

        # Check for asset concentration
        asset_counts = {}
        for opp in opportunities:
            for asset in opp.asset_pair:
                asset_counts[asset] = asset_counts.get(asset, 0) + 1

        for asset, count in asset_counts.items():
            if count > len(opportunities) * 0.5:  # >50% concentration
                correlation_risks.append({
                    'type': 'asset_concentration',
                    'asset': asset,
                    'concentration': count / len(opportunities),
                    'risk_level': 'HIGH' if count > len(opportunities) * 0.7 else 'MEDIUM',
                    'description': f'High exposure to {asset}'
                })

        # Check for reward token correlation
        reward_tokens = {}
        for opp in opportunities:
            for token in opp.reward_tokens:
                reward_tokens[token] = reward_tokens.get(token, 0) + 1

        for token, count in reward_tokens.items():
            if count > 3:  # Multiple strategies depend on same reward token
                correlation_risks.append({
                    'type': 'reward_token_correlation',
                    'token': token,
                    'strategies_affected': count,
                    'risk_level': 'MEDIUM',
                    'description': f'Multiple strategies depend on {token} rewards'
                })

        return correlation_risks

    def _passes_filters(self, opp: YieldOpportunity, preferences: Dict[str, Any]) -> bool:
        """
        Check if an opportunity passes all user-defined filters

        Args:
            opp: Yield opportunity to check
            preferences: User preferences

        Returns:
            True if opportunity passes all filters
        """
        # Risk level filter
        if opp.risk_level.value > preferences.get('max_risk_level', RiskLevel.MEDIUM).value:
            return False

        # Minimum APY filter
        if opp.total_apy < preferences.get('min_apy', 5.0):
            return False

        # Lockup period filter
        if opp.lockup_period and opp.lockup_period > preferences.get('max_lockup_days', 30):
            return False

        # Impermanent loss filter
        if opp.impermanent_loss_risk > preferences.get('impermanent_loss_tolerance', 0.1):
            return False

        # Gas cost filter
        if opp.estimated_gas_cost > preferences.get('gas_budget', 100):
            return False

        # Minimum deposit filter
        if opp.minimum_deposit > preferences.get('max_single_position', float('inf')):
            return False

        # Auto-compound filter
        if preferences.get('auto_compound_only', False) and not opp.auto_compound:
            return False

        # TVL threshold (avoid small/unproven pools)
        if opp.tvl < preferences.get('min_tvl', 1000000):  # $1M minimum
            return False

        # Verified strategy filter
        if preferences.get('verified_only', False) and not opp.verified_strategy:
            return False

        # Protocol whitelist/blacklist
        whitelisted_protocols = preferences.get('whitelisted_protocols', [])
        if whitelisted_protocols and opp.protocol not in whitelisted_protocols:
            return False

        blacklisted_protocols = preferences.get('blacklisted_protocols', [])
        if opp.protocol in blacklisted_protocols:
            return False

        return True

    def _get_top_opportunities(self, opportunities: List[YieldOpportunity], n: int) -> List[Dict[str, Any]]:
        """
        Get top N opportunities with key metrics

        Args:
            opportunities: List of opportunities
            n: Number of top opportunities to return

        Returns:
            List of top opportunities with summary data
        """
        # Sort by efficiency score if available, otherwise by total APY
        sorted_opps = sorted(opportunities,
                           key=lambda x: getattr(x, 'efficiency_score', x.total_apy),
                           reverse=True)

        top_opps = []
        for opp in sorted_opps[:n]:
            top_opps.append({
                'protocol': opp.protocol,
                'pool_name': opp.pool_name,
                'total_apy': opp.total_apy,
                'risk_level': opp.risk_level.name,
                'tvl': opp.tvl,
                'efficiency_score': getattr(opp, 'efficiency_score', None)
            })

        return top_opps
