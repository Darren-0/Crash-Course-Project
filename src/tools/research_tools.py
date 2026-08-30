"""
Fixed research toolset for the investment analysis agent.
Each tool has a single, well-defined capability.
"""

from typing import Any, Dict, Optional
from datetime import datetime
from edgar import Company, set_identity
import json
import yfinance as yf

set_identity("DueDiligenceBot admin@localresearch.internal")


class ToolExecutor:
    """Wrapper that executes research tools and logs results."""

    @staticmethod
    def fetch_filing_section(company: str, item: str) -> Dict[str, Any]:
        """
        Fetch a specific section from the latest 10-K filing.
        
        Args:
            company: Ticker symbol (e.g., "AAPL")
            item: Section name like "risk_factors", "business", "md_a"
        
        Returns:
            Dict with section text and metadata
        """
        try:
            ticker = company.upper()
            c = Company(ticker)
            filings = c.get_filings(form="10-K")
            
            if not filings:
                return {
                    "status": "error",
                    "error": f"No 10-K filings found for {ticker}",
                    "data": None
                }
            
            latest_filing = filings.latest(1)
            tenk = latest_filing.obj()
            
            # Map item names to tenk attributes
            item_mapping = {
                "risk_factors": "risk_factors",
                "business": "business",
                "md_a": "management_discussion_and_analysis",
                "legal": "legal_proceedings",
            }
            
            attribute_name = item_mapping.get(item.lower(), item.lower())
            section_text = getattr(tenk, attribute_name, None)
            
            if section_text is None:
                return {
                    "status": "not_found",
                    "error": f"Section '{item}' not found in 10-K",
                    "data": None
                }
            
            return {
                "status": "success",
                "ticker": ticker,
                "section": item,
                "data": str(section_text)[:5000],  # Cap at 5000 chars
                "filing_date": str(latest_filing.filing_date) if hasattr(latest_filing, 'filing_date') else "unknown"
            }
        
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "data": None
            }

    @staticmethod
    def search_news(company: str, topic: str) -> Dict[str, Any]:
        """
        Search for recent news/announcements about a company and topic using yfinance.
        
        Args:
            company: Company name or ticker
            topic: Topic to search for (e.g., "earnings", "acquisition", "leadership")
        
        Returns:
            Dict with news results from yfinance
        """
        try:
            ticker = company.upper()
            stock = yf.Ticker(ticker)
            
            # Get news from yfinance
            news = stock.news
            
            if not news:
                return {
                    "status": "info",
                    "ticker": ticker,
                    "topic": topic,
                    "note": "No news found for this ticker",
                    "results": []
                }
            
            # Filter news by topic (case-insensitive keyword matching)
            topic_lower = topic.lower()
            filtered_news = []
            
            for article in news:
                title = article.get('title', '').lower()
                summary = article.get('summary', '').lower()
                
                # Include article if topic keyword appears in title or summary
                if topic_lower in title or topic_lower in summary:
                    filtered_news.append({
                        "title": article.get('title', ''),
                        "link": article.get('link', ''),
                        "date": article.get('providerPublishTime', ''),
                        "source": article.get('source', ''),
                        "summary": article.get('summary', '')[:300]  # Cap summary at 300 chars
                    })
            
            # If no exact topic match, return all recent news (up to 5 most recent)
            if not filtered_news:
                filtered_news = [{
                    "title": article.get('title', ''),
                    "link": article.get('link', ''),
                    "date": article.get('providerPublishTime', ''),
                    "source": article.get('source', ''),
                    "summary": article.get('summary', '')[:300]
                } for article in news[:5]]
            
            return {
                "status": "success",
                "ticker": ticker,
                "topic": topic,
                "news_count": len(filtered_news),
                "results": filtered_news
            }
        
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to fetch news for {company}: {str(e)}",
                "topic": topic,
                "results": []
            }

    @staticmethod
    def get_peer_financials(ticker: str) -> Dict[str, Any]:
        """
        Fetch financial metrics for peer companies in the same industry, filtered by market cap.
        
        Args:
            ticker: Company ticker symbol
        
        Returns:
            Dict with peer company financials and market cap comparison
        """
        try:
            ticker = ticker.upper()
            stock = yf.Ticker(ticker)
            
            # Get target company info
            info = stock.info
            target_market_cap = info.get('marketCap', None)
            target_sector = info.get('sector', 'Unknown')
            target_industry = info.get('industry', 'Unknown')
            
            if not target_market_cap:
                return {
                    "status": "error",
                    "error": f"Could not determine market cap for {ticker}",
                    "ticker": ticker
                }
            
            # Define peer companies by sector (major competitors)
            # This is a curated list for common sectors
            peer_map = {
                'Technology': ['MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'AMD', 'INTC', 'CSCO'],
                'Healthcare': ['JNJ', 'UNH', 'PFE', 'ABBV', 'LLY', 'MRK', 'AZN', 'TMO'],
                'Financial Services': ['JPM', 'BAC', 'WFC', 'GS', 'MS', 'BLK', 'SCHW', 'AMG'],
                'Consumer Cyclical': ['AMZN', 'HD', 'MCD', 'TSLA', 'NKE', 'TJX', 'SBUX', 'CMG'],
                'Industrials': ['BA', 'CAT', 'GE', 'HON', 'LMT', 'RTX', 'ITW', 'PH'],
                'Energy': ['XOM', 'CVX', 'COP', 'MPC', 'SLB', 'EOG', 'OXY', 'PSX'],
                'Utilities': ['NEE', 'DUK', 'SO', 'EXC', 'AEP', 'PEG', 'ED', 'XEL'],
                'Consumer Defensive': ['PG', 'KO', 'PEP', 'WMT', 'COST', 'MO', 'CL', 'KMB'],
                'Communication Services': ['GOOG', 'META', 'DIS', 'CMCSA', 'VZ', 'T', 'LBRDK', 'PARA'],
                'Real Estate': ['SPG', 'PLD', 'AVB', 'EQR', 'PSA', 'CBRE', 'DRE', 'LTC'],
            }
            
            # Get potential peers for this sector
            potential_peers = peer_map.get(target_sector, [])
            
            if not potential_peers:
                return {
                    "status": "info",
                    "note": f"No peer data available for sector: {target_sector}",
                    "ticker": ticker,
                    "sector": target_sector,
                    "peers": []
                }
            
            # Filter out the target company and fetch peer data
            peers_data = []
            market_cap_range = (target_market_cap * 0.5, target_market_cap * 2.0)  # 0.5x to 2x
            
            for peer_ticker in potential_peers:
                if peer_ticker.upper() == ticker:
                    continue  # Skip the target company itself
                
                try:
                    peer_stock = yf.Ticker(peer_ticker)
                    peer_info = peer_stock.info
                    
                    peer_market_cap = peer_info.get('marketCap', None)
                    
                    # Only include if market cap is within range
                    if peer_market_cap and market_cap_range[0] <= peer_market_cap <= market_cap_range[1]:
                        peer_data = {
                            "ticker": peer_ticker,
                            "company_name": peer_info.get('longName', peer_ticker),
                            "market_cap": peer_market_cap,
                            "market_cap_millions": peer_market_cap / 1_000_000 if peer_market_cap else None,
                            "pe_ratio": peer_info.get('trailingPE', None),
                            "pb_ratio": peer_info.get('priceToBook', None),
                            "dividend_yield": peer_info.get('dividendYield', None),
                            "revenue": peer_info.get('totalRevenue', None),
                            "net_income": peer_info.get('netIncomeToCommon', None),
                            "gross_margin": peer_info.get('grossMargins', None),
                            "operating_margin": peer_info.get('operatingMargins', None),
                            "profit_margin": peer_info.get('profitMargins', None),
                            "current_ratio": peer_info.get('currentRatio', None),
                            "debt_to_equity": peer_info.get('debtToEquity', None),
                        }
                        peers_data.append(peer_data)
                
                except Exception:
                    # Skip peers that can't be fetched
                    continue
            
            return {
                "status": "success",
                "ticker": ticker,
                "sector": target_sector,
                "industry": target_industry,
                "target_market_cap": target_market_cap,
                "target_market_cap_millions": target_market_cap / 1_000_000 if target_market_cap else None,
                "market_cap_range_millions": (market_cap_range[0] / 1_000_000, market_cap_range[1] / 1_000_000),
                "peers_found": len(peers_data),
                "peers": peers_data
            }
        
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to fetch peer financials for {ticker}: {str(e)}",
                "ticker": ticker
            }

    @staticmethod
    def get_analyst_estimates(ticker: str) -> Dict[str, Any]:
        """
        Fetch analyst estimates, target prices, and consensus ratings using yfinance.
        
        Args:
            ticker: Company ticker symbol
        
        Returns:
            Dict with analyst consensus and estimates
        """
        try:
            ticker = ticker.upper()
            stock = yf.Ticker(ticker)
            
            # Get analyst info from yfinance
            info = stock.info
            
            # Extract analyst data
            recommendation_key = info.get('recommendationKey', 'hold')
            target_mean_price = info.get('targetMeanPrice', None)
            number_of_analysts = info.get('numberOfAnalystOpinions', 0)
            
            # Map recommendation keys to ratings
            rating_map = {
                'strong_buy': 'Strong Buy',
                'buy': 'Buy',
                'hold': 'Hold',
                'sell': 'Sell',
                'strong_sell': 'Strong Sell'
            }
            
            consensus_rating = rating_map.get(recommendation_key, recommendation_key.title() if recommendation_key else 'Unknown')
            
            # Get current price for comparison
            current_price = info.get('currentPrice') or info.get('regularMarketPrice', None)
            
            # Calculate upside/downside
            upside_downside = None
            if current_price and target_mean_price:
                upside_downside = ((target_mean_price - current_price) / current_price * 100)
            
            # Get earnings estimates if available
            earnings_data = {
                "current_eps": info.get('trailingEps', None),
                "forward_eps": info.get('forwardEps', None),
                "eps_growth": info.get('epsTrailingTwelveMonths', None)
            }
            
            return {
                "status": "success",
                "ticker": ticker,
                "consensus_rating": consensus_rating,
                "target_price": target_mean_price,
                "current_price": current_price,
                "upside_downside_percent": round(upside_downside, 2) if upside_downside else None,
                "number_of_analysts": number_of_analysts,
                "earnings_estimates": earnings_data,
                "last_updated": datetime.now().isoformat()
            }
        
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to fetch analyst estimates for {ticker}: {str(e)}",
                "ticker": ticker
            }

    @staticmethod
    def extract_financial_metrics(ticker: str) -> Dict[str, Any]:
        """
        Extract and compute standard financial ratios from latest 10-K.
        
        Args:
            ticker: Company ticker symbol
        
        Returns:
            Dict with extracted metrics
        """
        try:
            ticker = ticker.upper()
            c = Company(ticker)
            filings = c.get_filings(form="10-K")
            
            if not filings:
                return {
                    "status": "error",
                    "error": f"No 10-K filings found for {ticker}",
                    "metrics": {}
                }
            
            latest_filing = filings.latest(1)
            tenk = latest_filing.obj()
            
            # Placeholder metrics extraction
            # In a real scenario, you'd use the deterministic math node
            return {
                "status": "success",
                "ticker": ticker,
                "filing_date": str(latest_filing.filing_date) if hasattr(latest_filing, 'filing_date') else "unknown",
                "metrics": {
                    "extraction_status": "ready_for_deterministic_calculation"
                }
            }
        
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "metrics": {}
            }

    @staticmethod
    def execute_tool(tool_name: str, tool_input: Dict[str, Any]) -> Any:
        """
        Route to the appropriate tool and execute it.
        
        Args:
            tool_name: Name of the tool to execute
            tool_input: Input parameters for the tool
        
        Returns:
            Result from the tool
        """
        tools_map = {
            "fetch_filing_section": ToolExecutor.fetch_filing_section,
            "search_news": ToolExecutor.search_news,
            "get_peer_financials": ToolExecutor.get_peer_financials,
            "get_analyst_estimates": ToolExecutor.get_analyst_estimates,
            "extract_financial_metrics": ToolExecutor.extract_financial_metrics,
        }
        
        if tool_name not in tools_map:
            return {
                "status": "error",
                "error": f"Unknown tool: {tool_name}",
                "available_tools": list(tools_map.keys())
            }
        
        tool_func = tools_map[tool_name]
        try:
            result = tool_func(**tool_input)
            return result
        except TypeError as e:
            return {
                "status": "error",
                "error": f"Invalid parameters for {tool_name}: {str(e)}",
                "expected_params": tool_func.__doc__
            }

    @staticmethod
    def get_tool_definitions() -> list[Dict[str, Any]]:
        """
        Return LangChain-compatible tool definitions for the agent.
        """
        return [
            {
                "name": "fetch_filing_section",
                "description": "Fetch a specific section from the latest 10-K filing (risk_factors, business, md_a, legal)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "company": {"type": "string", "description": "Ticker symbol"},
                        "item": {"type": "string", "description": "Section name"}
                    },
                    "required": ["company", "item"]
                }
            },
            {
                "name": "search_news",
                "description": "Search for recent news about a company on a specific topic",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "company": {"type": "string", "description": "Company name or ticker"},
                        "topic": {"type": "string", "description": "Topic to search for"}
                    },
                    "required": ["company", "topic"]
                }
            },
            {
                "name": "get_peer_financials",
                "description": "Fetch financial metrics for peer companies in the same industry",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "ticker": {"type": "string", "description": "Company ticker"}
                    },
                    "required": ["ticker"]
                }
            },
            {
                "name": "get_analyst_estimates",
                "description": "Fetch analyst estimates, target prices, and consensus ratings",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "ticker": {"type": "string", "description": "Company ticker"}
                    },
                    "required": ["ticker"]
                }
            },
            {
                "name": "extract_financial_metrics",
                "description": "Extract and compute financial ratios from the latest 10-K",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "ticker": {"type": "string", "description": "Company ticker"}
                    },
                    "required": ["ticker"]
                }
            }
        ]
