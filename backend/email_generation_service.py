import asyncio
import logging
from typing import Dict, List, Any, Optional
from es_data_client import es_data_client
from mcp_client import mcp_manager
from mcp_config import config_manager

logger = logging.getLogger(__name__)

class EmailGenerationService:
    """Service for generating contextual emails about market developments affecting client accounts"""
    
    async def generate_account_email(self, account_id: str, time_period: int = 48, time_unit: str = "hours") -> Dict[str, str]:
        """
        Generate a contextual email for an account based on holdings and recent market developments
        
        Args:
            account_id: The account to generate email for
            time_period: Time period to look back for news (default 48)  
            time_unit: Unit for time period - hours, days, etc (default "hours")
            
        Returns:
            Dict with email subject and body
        """
        try:
            # Get account details
            account_data = await es_data_client.get_account_details(account_id)
            if not account_data:
                raise ValueError(f"Account {account_id} not found")
            
            # Get account holdings symbols
            holdings_symbols = []
            total_portfolio_value = account_data.get('total_portfolio_value', 0)
            account_name = account_data.get('account_name', 'Unknown Account')
            
            if 'holdings' in account_data:
                for holding in account_data['holdings']:
                    symbol = holding.get('symbol')
                    if symbol:
                        holdings_symbols.append(symbol)
            
            logger.info(f"Generating email for account {account_name} with {len(holdings_symbols)} holdings")
            
            # Try to get recent negative news for holdings using MCP tools
            market_insights = await self._get_market_insights_for_symbols(holdings_symbols, time_period, time_unit)
            
            # Generate email content
            subject = f"Portfolio Update - {account_name}"
            body = self._generate_email_body(account_data, market_insights)
            
            return {
                "subject": subject,
                "body": body
            }
            
        except Exception as e:
            logger.error(f"Error generating email for account {account_id}: {e}")
            # Fallback to basic email
            return await self._generate_fallback_email(account_id)
    
    async def _get_market_insights_for_symbols(self, symbols: List[str], time_period: int, time_unit: str) -> Dict[str, Any]:
        """Get market insights for account symbols using MCP tools"""
        insights = {
            "negative_news": [],
            "positive_news": [],
            "neutral_news": [],
            "analysis_performed": False
        }
        
        try:
            # Get enabled MCP servers
            enabled_servers = config_manager.get_enabled_servers()
            
            if not enabled_servers:
                logger.warning("No MCP servers available for market analysis")
                return insights
            
            # Look for news analysis tools
            analysis_server = None
            analysis_tool = None
            
            for server_id, server in enabled_servers.items():
                # Look for tools that can analyze news/sentiment
                if "news_and_report_lookup_with_symbol_detail" in server.tools:
                    analysis_server = server_id
                    analysis_tool = "news_and_report_lookup_with_symbol_detail"
                    break
                elif "search_financial_data" in server.tools:
                    analysis_server = server_id
                    analysis_tool = "search_financial_data"
                    break
                elif "news_analysis" in server.tools:
                    analysis_server = server_id
                    analysis_tool = "news_analysis"
                    break
            
            if not analysis_server:
                logger.warning("No suitable MCP tools found for news analysis")
                return insights
            
            logger.info(f"Using MCP server {analysis_server} with tool {analysis_tool} for news analysis")
            
            # Execute news lookup for symbols
            for symbol in symbols[:5]:  # Limit to top 5 holdings to avoid overwhelming
                try:
                    arguments = {
                        "symbol": symbol,
                        "time_period": time_period,
                        "time_unit": time_unit
                    }
                    
                    # Execute the MCP tool
                    async for result in mcp_manager.execute_tool(analysis_server, analysis_tool, arguments):
                        if result["type"] == "tool_result":
                            content = result["content"]
                            if isinstance(content, dict) and "text" in content:
                                # Parse the news results
                                news_data = self._parse_news_results(content["text"], symbol)
                                insights["negative_news"].extend(news_data.get("negative", []))
                                insights["positive_news"].extend(news_data.get("positive", []))
                                insights["neutral_news"].extend(news_data.get("neutral", []))
                                insights["analysis_performed"] = True
                            break
                        elif result["type"] == "error":
                            logger.warning(f"MCP tool error for symbol {symbol}: {result.get('error', 'Unknown error')}")
                            break
                            
                except Exception as e:
                    logger.warning(f"Error analyzing symbol {symbol}: {e}")
                    continue
            
            return insights
            
        except Exception as e:
            logger.error(f"Error getting market insights: {e}")
            return insights
    
    def _parse_news_results(self, news_text: str, symbol: str) -> Dict[str, List[Dict]]:
        """Parse news results and categorize by sentiment"""
        results = {
            "negative": [],
            "positive": [],
            "neutral": []
        }
        
        try:
            import json
            
            # Try to parse as JSON first
            try:
                data = json.loads(news_text)
                if isinstance(data, dict) and "articles" in data:
                    articles = data["articles"]
                elif isinstance(data, list):
                    articles = data
                else:
                    articles = []
            except json.JSONDecodeError:
                # If not JSON, try to extract useful information from text
                articles = []
                
            # Categorize articles by sentiment
            for article in articles:
                if isinstance(article, dict):
                    sentiment = article.get("sentiment", "").lower()
                    article_info = {
                        "title": article.get("title", "Market Update"),
                        "summary": article.get("summary", "")[:200],
                        "symbol": symbol,
                        "published_date": article.get("published_date", "")
                    }
                    
                    if "negative" in sentiment:
                        results["negative"].append(article_info)
                    elif "positive" in sentiment:
                        results["positive"].append(article_info)
                    else:
                        results["neutral"].append(article_info)
            
            return results
            
        except Exception as e:
            logger.error(f"Error parsing news results for {symbol}: {e}")
            return results
    
    def _generate_email_body(self, account_data: Dict[str, Any], market_insights: Dict[str, Any]) -> str:
        """Generate the email body content"""
        account_name = account_data.get('account_name', 'Unknown Account')
        total_value = account_data.get('total_portfolio_value', 0)
        risk_profile = account_data.get('risk_profile', 'Unknown')
        
        # Get top holdings for context
        top_holdings = []
        if 'holdings' in account_data:
            sorted_holdings = sorted(
                account_data['holdings'], 
                key=lambda x: x.get('total_current_value', 0), 
                reverse=True
            )
            top_holdings = sorted_holdings[:3]  # Top 3 holdings
        
        # Start building email
        email_body = f"""Dear {account_name},

I hope this message finds you well. I wanted to provide you with a brief update on your portfolio and some relevant market developments that may impact your investments.

## Portfolio Summary
Your current portfolio value stands at ${total_value:,.2f}. As a {risk_profile.lower()} risk profile investor, I've been closely monitoring market conditions that could affect your holdings."""

        # Add top holdings information
        if top_holdings:
            email_body += f"""

## Your Key Holdings
Your largest positions include:"""
            
            for holding in top_holdings:
                symbol = holding.get('symbol', 'N/A')
                company = holding.get('company_name', 'Unknown Company')
                value = holding.get('total_current_value', 0)
                shares = holding.get('total_quantity', 0)
                
                email_body += f"""
• {symbol} ({company}): {shares:,.0f} shares worth ${value:,.2f}"""

        # Add market insights if available
        if market_insights.get("analysis_performed"):
            negative_news = market_insights.get("negative_news", [])
            positive_news = market_insights.get("positive_news", [])
            
            if negative_news:
                email_body += f"""

## Market Developments of Note
I've identified some recent market developments that may be relevant to your portfolio:"""
                
                for news in negative_news[:2]:  # Limit to 2 most relevant
                    title = news.get("title", "Market Update")
                    symbol = news.get("symbol", "")
                    summary = news.get("summary", "")
                    
                    email_body += f"""

**{symbol} - {title}**
{summary}"""
                
                email_body += """

While these developments warrant attention, please remember that market volatility is normal and your portfolio is positioned for long-term growth."""
            
            elif positive_news:
                email_body += f"""

## Positive Market Developments
I'm pleased to share some positive developments affecting your holdings:"""
                
                for news in positive_news[:2]:
                    title = news.get("title", "Market Update")
                    symbol = news.get("symbol", "")
                    summary = news.get("summary", "")
                    
                    email_body += f"""

**{symbol} - {title}**
{summary}"""
            
            else:
                email_body += """

## Market Update
The markets have been relatively stable with no significant developments directly impacting your core holdings. This is often a positive sign for long-term investors."""
                
        else:
            email_body += """

## Market Update
I continue to monitor market conditions and news that could impact your portfolio. Current market conditions appear stable for your investment strategy."""

        # Add closing
        email_body += """

## Next Steps
I recommend we schedule a brief 15-minute call this week to discuss these developments and review your portfolio performance. Please let me know your availability.

If you have any immediate questions or concerns, please don't hesitate to reach out.

Best regards,
Your Financial Advisor

---
This update was generated using our advanced market monitoring system to ensure you stay informed about developments affecting your investments."""

        return email_body
    
    async def _generate_fallback_email(self, account_id: str) -> Dict[str, str]:
        """Generate a basic fallback email when detailed analysis fails"""
        try:
            account_data = await es_data_client.get_account_details(account_id)
            account_name = account_data.get('account_name', 'Valued Client') if account_data else 'Valued Client'
            total_value = account_data.get('total_portfolio_value', 0) if account_data else 0
            
            subject = f"Portfolio Check-in - {account_name}"
            body = f"""Dear {account_name},

I hope you're doing well. I wanted to reach out with a brief update on your portfolio.

Your current portfolio value stands at ${total_value:,.2f}. I'm continuously monitoring market conditions and developments that could impact your investments.

I'd like to schedule a brief call this week to discuss your portfolio performance and any questions you might have about current market conditions.

Please let me know your availability for a 15-minute conversation.

Best regards,
Your Financial Advisor"""

            return {"subject": subject, "body": body}
            
        except Exception as e:
            logger.error(f"Error generating fallback email: {e}")
            return {
                "subject": "Portfolio Update",
                "body": "Dear Valued Client,\n\nI'd like to schedule a time to discuss your portfolio. Please let me know your availability.\n\nBest regards,\nYour Financial Advisor"
            }

# Create singleton instance
email_generation_service = EmailGenerationService()