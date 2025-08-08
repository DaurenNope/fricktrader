"""
Enhanced OpenBB Platform Capabilities
Demonstrates the FULL power of OpenBB beyond basic market data
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import asyncio

logger = logging.getLogger(__name__)

try:
    from openbb import obb
    OPENBB_AVAILABLE = True
    logger.info("✅ OpenBB Platform loaded successfully")
except ImportError as e:
    OPENBB_AVAILABLE = False
    logger.error(f"❌ OpenBB Platform not available: {e}")

class EnhancedOpenBBCapabilities:
    """
    Comprehensive OpenBB Platform integration showing ALL capabilities
    Far beyond just market data - this is a complete financial analysis platform!
    """
    
    def __init__(self):
        self.obb_available = OPENBB_AVAILABLE
        
    # =============================================================================
    # 1. FUNDAMENTAL ANALYSIS (Company/Crypto Fundamentals)
    # =============================================================================
    
    async def get_fundamental_analysis(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive fundamental analysis"""
        if not self.obb_available:
            return {"error": "OpenBB not available"}
        
        try:
            # Company fundamentals
            income_statement = obb.equity.fundamental.income(symbol, period="annual", limit=5)
            balance_sheet = obb.equity.fundamental.balance(symbol, period="annual", limit=5)
            cash_flow = obb.equity.fundamental.cash(symbol, period="annual", limit=5)
            
            # Financial ratios
            ratios = obb.equity.fundamental.ratios(symbol, period="annual", limit=5)
            
            # Analyst estimates
            estimates = obb.equity.estimates.consensus(symbol)
            
            return {
                "income_statement": income_statement.to_dict() if hasattr(income_statement, 'to_dict') else str(income_statement),
                "balance_sheet": balance_sheet.to_dict() if hasattr(balance_sheet, 'to_dict') else str(balance_sheet),
                "cash_flow": cash_flow.to_dict() if hasattr(cash_flow, 'to_dict') else str(cash_flow),
                "ratios": ratios.to_dict() if hasattr(ratios, 'to_dict') else str(ratios),
                "estimates": estimates.to_dict() if hasattr(estimates, 'to_dict') else str(estimates)
            }
            
        except Exception as e:
            logger.error(f"Error getting fundamental analysis: {e}")
            return {"error": str(e)}
    
    # =============================================================================
    # 2. OPTIONS ANALYSIS (Advanced Options Data)
    # =============================================================================
    
    async def get_options_analysis(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive options analysis"""
        if not self.obb_available:
            return {"error": "OpenBB not available"}
        
        try:
            # Options chain
            options_chain = obb.derivatives.options.chains(symbol)
            
            # Options flow (unusual activity)
            options_flow = obb.derivatives.options.unusual(symbol)
            
            # Put/Call ratio
            put_call_ratio = obb.derivatives.options.pcr(symbol)
            
            # Max pain
            max_pain = obb.derivatives.options.max_pain(symbol)
            
            # Volatility surface
            vol_surface = obb.derivatives.options.vol_surface(symbol)
            
            return {
                "options_chain": options_chain.to_dict() if hasattr(options_chain, 'to_dict') else str(options_chain),
                "unusual_flow": options_flow.to_dict() if hasattr(options_flow, 'to_dict') else str(options_flow),
                "put_call_ratio": put_call_ratio,
                "max_pain": max_pain,
                "volatility_surface": vol_surface.to_dict() if hasattr(vol_surface, 'to_dict') else str(vol_surface)
            }
            
        except Exception as e:
            logger.error(f"Error getting options analysis: {e}")
            return {"error": str(e)}
    
    # =============================================================================
    # 3. ECONOMIC DATA (Macro Economic Indicators)
    # =============================================================================
    
    async def get_economic_indicators(self) -> Dict[str, Any]:
        """Get comprehensive economic indicators"""
        if not self.obb_available:
            return {"error": "OpenBB not available"}
        
        try:
            # GDP data
            gdp = obb.economy.gdp()
            
            # Inflation data
            cpi = obb.economy.cpi()
            
            # Employment data
            unemployment = obb.economy.unemployment()
            
            # Interest rates
            interest_rates = obb.economy.interest_rates()
            
            # Treasury yields
            treasury_yields = obb.fixedincome.government.treasury_rates()
            
            # Economic calendar
            economic_calendar = obb.economy.calendar()
            
            return {
                "gdp": gdp.to_dict() if hasattr(gdp, 'to_dict') else str(gdp),
                "cpi": cpi.to_dict() if hasattr(cpi, 'to_dict') else str(cpi),
                "unemployment": unemployment.to_dict() if hasattr(unemployment, 'to_dict') else str(unemployment),
                "interest_rates": interest_rates.to_dict() if hasattr(interest_rates, 'to_dict') else str(interest_rates),
                "treasury_yields": treasury_yields.to_dict() if hasattr(treasury_yields, 'to_dict') else str(treasury_yields),
                "economic_calendar": economic_calendar.to_dict() if hasattr(economic_calendar, 'to_dict') else str(economic_calendar)
            }
            
        except Exception as e:
            logger.error(f"Error getting economic indicators: {e}")
            return {"error": str(e)}
    
    # =============================================================================
    # 4. CRYPTO SPECIFIC DATA (DeFi, NFTs, On-Chain)
    # =============================================================================
    
    async def get_crypto_analysis(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive crypto analysis"""
        if not self.obb_available:
            return {"error": "OpenBB not available"}
        
        try:
            # DeFi protocols
            defi_protocols = obb.crypto.defi.protocols()
            
            # DeFi TVL
            defi_tvl = obb.crypto.defi.tvl()
            
            # Crypto news
            crypto_news = obb.news.crypto()
            
            # Social sentiment
            social_sentiment = obb.crypto.social.trending()
            
            # On-chain metrics (if available)
            try:
                onchain_metrics = obb.crypto.onchain.active_addresses(symbol.replace('/USDT', ''))
            except:
                onchain_metrics = "Not available"
            
            return {
                "defi_protocols": defi_protocols.to_dict() if hasattr(defi_protocols, 'to_dict') else str(defi_protocols),
                "defi_tvl": defi_tvl.to_dict() if hasattr(defi_tvl, 'to_dict') else str(defi_tvl),
                "crypto_news": crypto_news.to_dict() if hasattr(crypto_news, 'to_dict') else str(crypto_news),
                "social_sentiment": social_sentiment.to_dict() if hasattr(social_sentiment, 'to_dict') else str(social_sentiment),
                "onchain_metrics": onchain_metrics
            }
            
        except Exception as e:
            logger.error(f"Error getting crypto analysis: {e}")
            return {"error": str(e)}
    
    # =============================================================================
    # 5. ALTERNATIVE DATA (Insider Trading, Short Interest, etc.)
    # =============================================================================
    
    async def get_alternative_data(self, symbol: str) -> Dict[str, Any]:
        """Get alternative data sources"""
        if not self.obb_available:
            return {"error": "OpenBB not available"}
        
        try:
            # Insider trading
            insider_trading = obb.equity.ownership.insider_trading(symbol)
            
            # Short interest
            short_interest = obb.equity.short.short_interest(symbol)
            
            # Institutional ownership
            institutional = obb.equity.ownership.institutional(symbol)
            
            # Analyst recommendations
            analyst_recs = obb.equity.estimates.analyst(symbol)
            
            # Price targets
            price_targets = obb.equity.estimates.price_target(symbol)
            
            return {
                "insider_trading": insider_trading.to_dict() if hasattr(insider_trading, 'to_dict') else str(insider_trading),
                "short_interest": short_interest.to_dict() if hasattr(short_interest, 'to_dict') else str(short_interest),
                "institutional": institutional.to_dict() if hasattr(institutional, 'to_dict') else str(institutional),
                "analyst_recommendations": analyst_recs.to_dict() if hasattr(analyst_recs, 'to_dict') else str(analyst_recs),
                "price_targets": price_targets.to_dict() if hasattr(price_targets, 'to_dict') else str(price_targets)
            }
            
        except Exception as e:
            logger.error(f"Error getting alternative data: {e}")
            return {"error": str(e)}
    
    # =============================================================================
    # 6. FIXED INCOME & BONDS
    # =============================================================================
    
    async def get_fixed_income_analysis(self) -> Dict[str, Any]:
        """Get fixed income and bond analysis"""
        if not self.obb_available:
            return {"error": "OpenBB not available"}
        
        try:
            # Treasury rates
            treasury_rates = obb.fixedincome.government.treasury_rates()
            
            # Corporate bonds
            corporate_bonds = obb.fixedincome.corporate.bonds()
            
            # Yield curve
            yield_curve = obb.fixedincome.government.yield_curve()
            
            # Credit spreads
            try:
                credit_spreads = obb.fixedincome.spreads.credit()
            except:
                credit_spreads = "Not available"
            
            return {
                "treasury_rates": treasury_rates.to_dict() if hasattr(treasury_rates, 'to_dict') else str(treasury_rates),
                "corporate_bonds": corporate_bonds.to_dict() if hasattr(corporate_bonds, 'to_dict') else str(corporate_bonds),
                "yield_curve": yield_curve.to_dict() if hasattr(yield_curve, 'to_dict') else str(yield_curve),
                "credit_spreads": credit_spreads
            }
            
        except Exception as e:
            logger.error(f"Error getting fixed income analysis: {e}")
            return {"error": str(e)}
    
    # =============================================================================
    # 7. ETF & MUTUAL FUND ANALYSIS
    # =============================================================================
    
    async def get_etf_analysis(self, symbol: str) -> Dict[str, Any]:
        """Get ETF and mutual fund analysis"""
        if not self.obb_available:
            return {"error": "OpenBB not available"}
        
        try:
            # ETF holdings
            etf_holdings = obb.etf.holdings(symbol)
            
            # ETF info
            etf_info = obb.etf.info(symbol)
            
            # ETF sectors
            etf_sectors = obb.etf.sectors(symbol)
            
            # ETF countries
            etf_countries = obb.etf.countries(symbol)
            
            return {
                "holdings": etf_holdings.to_dict() if hasattr(etf_holdings, 'to_dict') else str(etf_holdings),
                "info": etf_info.to_dict() if hasattr(etf_info, 'to_dict') else str(etf_info),
                "sectors": etf_sectors.to_dict() if hasattr(etf_sectors, 'to_dict') else str(etf_sectors),
                "countries": etf_countries.to_dict() if hasattr(etf_countries, 'to_dict') else str(etf_countries)
            }
            
        except Exception as e:
            logger.error(f"Error getting ETF analysis: {e}")
            return {"error": str(e)}
    
    # =============================================================================
    # 8. COMPREHENSIVE ANALYSIS FUNCTION
    # =============================================================================
    
    async def get_comprehensive_analysis(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive analysis using ALL OpenBB capabilities"""
        logger.info(f"🔍 Running comprehensive OpenBB analysis for {symbol}")
        
        results = {}
        
        # Run all analyses in parallel for speed
        tasks = [
            ("fundamental", self.get_fundamental_analysis(symbol)),
            ("options", self.get_options_analysis(symbol)),
            ("economic", self.get_economic_indicators()),
            ("crypto", self.get_crypto_analysis(symbol)),
            ("alternative", self.get_alternative_data(symbol)),
            ("fixed_income", self.get_fixed_income_analysis()),
            ("etf", self.get_etf_analysis(symbol))
        ]
        
        # Execute all tasks
        for name, task in tasks:
            try:
                results[name] = await task
                logger.info(f"✅ Completed {name} analysis")
            except Exception as e:
                logger.error(f"❌ Failed {name} analysis: {e}")
                results[name] = {"error": str(e)}
        
        return {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "analyses": results,
            "summary": {
                "total_analyses": len(tasks),
                "successful": len([r for r in results.values() if "error" not in r]),
                "failed": len([r for r in results.values() if "error" in r])
            }
        }


# =============================================================================
# OPENBB CAPABILITIES SUMMARY
# =============================================================================

OPENBB_FULL_CAPABILITIES = {
    "equity": [
        "Fundamental analysis (income, balance sheet, cash flow)",
        "Financial ratios and metrics",
        "Analyst estimates and recommendations",
        "Price targets and upgrades/downgrades",
        "Insider trading activity",
        "Institutional ownership",
        "Short interest and squeeze metrics",
        "Earnings data and surprises",
        "Dividend information",
        "Stock screeners and comparisons"
    ],
    
    "options": [
        "Options chains (calls/puts)",
        "Unusual options activity",
        "Put/call ratios",
        "Max pain calculations",
        "Volatility surface analysis",
        "Greeks calculations",
        "Options flow and sentiment",
        "Implied volatility analysis"
    ],
    
    "crypto": [
        "DeFi protocols and TVL",
        "On-chain metrics",
        "Social sentiment analysis",
        "Crypto news aggregation",
        "NFT data and trends",
        "Staking rewards",
        "Yield farming opportunities",
        "Cross-chain analytics"
    ],
    
    "economy": [
        "GDP and economic growth",
        "Inflation data (CPI, PPI)",
        "Employment statistics",
        "Interest rates and Fed policy",
        "Economic calendar",
        "Consumer confidence",
        "Manufacturing data",
        "International trade data"
    ],
    
    "fixed_income": [
        "Treasury rates and yields",
        "Corporate bond data",
        "Yield curve analysis",
        "Credit spreads",
        "Municipal bonds",
        "International bonds",
        "Bond ETF analysis"
    ],
    
    "etf": [
        "ETF holdings and allocations",
        "Sector and geographic exposure",
        "ETF performance comparison",
        "Expense ratios and fees",
        "Dividend yields",
        "ETF flows and sentiment"
    ],
    
    "alternative_data": [
        "Satellite data analysis",
        "Social media sentiment",
        "Patent filings",
        "Supply chain analysis",
        "ESG scores and ratings",
        "Regulatory filings",
        "Executive compensation"
    ],
    
    "technical_analysis": [
        "Advanced charting",
        "Custom indicators",
        "Pattern recognition",
        "Backtesting frameworks",
        "Risk management tools",
        "Portfolio optimization"
    ]
}

def print_openbb_capabilities():
    """Print all OpenBB capabilities"""
    print("🚀 OpenBB Platform - FULL CAPABILITIES")
    print("=" * 60)
    
    for category, capabilities in OPENBB_FULL_CAPABILITIES.items():
        print(f"\n📊 {category.upper().replace('_', ' ')}")
        for capability in capabilities:
            print(f"   • {capability}")
    
    print(f"\n🎯 TOTAL CAPABILITIES: {sum(len(caps) for caps in OPENBB_FULL_CAPABILITIES.values())}")
    print("💡 We're currently using <5% of OpenBB's power!")

if __name__ == "__main__":
    print_openbb_capabilities()