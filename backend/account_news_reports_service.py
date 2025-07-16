"""
Account-specific news and reports service for querying designated MCP servers 
to find news/reports related to specific symbols in an account's holdings.
"""

import logging
import json
from typing import Dict, List, Any, Optional
from mcp_config import config_manager
from mcp_client import mcp_manager
from es_data_client import es_data_client

logger = logging.getLogger(__name__)


class AccountNewsReportsService:
    """Service for fetching news and reports for account symbols from designated MCP servers"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.AccountNewsReportsService")
    
    async def get_account_news_reports(self, account_id: str, time_period: int = 72, time_unit: str = "hours") -> Dict[str, Any]:
        """Get news and reports for all symbols in an account's holdings"""
        try:
            # First get the account details to extract symbols
            account_data = await es_data_client.get_account_details(account_id)
            if not account_data or "holdings" not in account_data:
                return {
                    "status": "error",
                    "message": "Account not found or has no holdings",
                    "articles": []
                }
            
            # Extract unique symbols from holdings
            symbols = []
            for holding in account_data["holdings"]:
                symbol = holding.get("symbol", "").strip()
                if symbol and symbol not in symbols:
                    symbols.append(symbol)
            
            if not symbols:
                return {
                    "status": "no_data",
                    "message": "No symbols found in account holdings",
                    "articles": []
                }
            
            self.logger.info(f"Looking up news/reports for account {account_id} symbols: {symbols}")
            
            # Get servers designated for main page data
            main_page_servers = config_manager.get_main_page_servers()
            
            if not main_page_servers:
                return {
                    "status": "no_servers",
                    "message": "No MCP servers configured for news/reports lookup",
                    "articles": []
                }
            
            # Try to get news/reports from each designated server
            all_articles = []
            server_used = None
            
            for server_id, server in main_page_servers.items():
                try:
                    # Check if server has the required tool
                    if "news_and_report_lookup_with_symbol_detail" not in server.tools:
                        self.logger.warning(f"Server {server_id} does not have news_and_report_lookup_with_symbol_detail tool")
                        continue
                    
                    # Get articles for all symbols from this server
                    server_articles = await self._get_articles_for_symbols(server_id, server, symbols, time_period, time_unit)
                    if server_articles:
                        all_articles.extend(server_articles)
                        server_used = server.name
                        break  # Use first working server
                        
                except Exception as e:
                    self.logger.warning(f"Failed to get news/reports from server {server_id}: {e}")
                    continue
            
            # Check if any server had the required tool
            has_required_tool = any(
                "news_and_report_lookup_with_symbol_detail" in server.tools 
                for server in main_page_servers.values()
            )
            
            if not has_required_tool:
                return {
                    "status": "tool_not_available",
                    "message": "Connected MCP servers do not support news/reports lookup tool (news_and_report_lookup_with_symbol_detail)",
                    "articles": []
                }
            
            if not all_articles:
                return {
                    "status": "no_data",
                    "message": f"No news or reports found for account symbols in the last {time_period} {time_unit}",
                    "articles": []
                }
            
            return {
                "status": "success",
                "server_used": server_used,
                "symbols_searched": symbols,
                "articles": all_articles[:20]  # Limit to top 20 articles
            }
            
        except Exception as e:
            self.logger.error(f"Error getting account news/reports: {e}")
            return {
                "status": "error", 
                "message": f"Error retrieving news/reports: {e}",
                "articles": []
            }
    
    async def _get_articles_for_symbols(self, server_id: str, server, symbols: List[str], time_period: int, time_unit: str) -> List[Dict[str, Any]]:
        """Get news and reports for a list of symbols from a specific MCP server"""
        all_articles = []
        
        for symbol in symbols:
            try:
                self.logger.info(f"Calling news_and_report_lookup_with_symbol_detail for symbol {symbol} on server {server_id}")
                
                # Prepare arguments for the tool
                arguments = {
                    "time_duration": f"{time_period} {time_unit}",
                    "symbol": symbol
                }
                
                articles = await self._execute_tool_for_symbol(server_id, symbol, arguments)
                if articles:
                    all_articles.extend(articles)
                    
            except Exception as e:
                self.logger.warning(f"Error getting articles for symbol {symbol}: {e}")
                continue
        
        # Sort by relevance/date and remove duplicates
        return self._deduplicate_articles(all_articles)
    
    async def _execute_tool_for_symbol(self, server_id: str, symbol: str, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute the MCP tool for a specific symbol"""
        articles = []
        
        try:
            async for result in mcp_manager.execute_tool(server_id, "news_and_report_lookup_with_symbol_detail", arguments):
                if result["type"] == "tool_result":
                    content = result["content"]
                    if isinstance(content, dict) and "text" in content:
                        try:
                            data = json.loads(content["text"])
                            self.logger.info(f"Parsed news_and_report_lookup_with_symbol_detail data for {symbol}")
                            
                            # Parse the response
                            parsed_articles = await self._parse_articles_response(data, symbol)
                            articles.extend(parsed_articles)
                            
                        except json.JSONDecodeError as e:
                            self.logger.warning(f"Could not parse response as JSON for {symbol}: {e}")
                    break
                elif result["type"] == "error":
                    self.logger.error(f"Error from tool for {symbol}: {result.get('error', 'Unknown error')}")
                    break
                    
        except Exception as e:
            self.logger.error(f"Error executing tool for symbol {symbol}: {e}")
        
        return articles
    
    async def _parse_articles_response(self, data: Dict[str, Any], symbol: str) -> List[Dict[str, Any]]:
        """Parse the response from news_and_report_lookup_with_symbol_detail tool"""
        articles = []
        
        try:
            # The response format may vary - try different patterns
            
            # Format 1: Standard ES response with hits
            if "result" in data and "hits" in data["result"]:
                hits = data["result"]["hits"]["hits"]
                for hit in hits:
                    source = hit.get("_source", {})
                    article = self._create_article_from_source(source, hit.get("_id", ""), symbol)
                    if article:
                        articles.append(article)
            
            # Format 2: ES|QL response with values and columns
            elif "result" in data and "values" in data["result"]:
                columns = data["result"].get("columns", [])
                values = data["result"].get("values", [])
                
                col_map = {col.get("name", f"col_{i}"): i for i, col in enumerate(columns)}
                
                for row in values:
                    article = self._create_article_from_esql_row(row, col_map, symbol)
                    if article:
                        articles.append(article)
            
            # Format 3: Direct array of articles
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        article = self._create_article_from_source(item, item.get("id", ""), symbol)
                        if article:
                            articles.append(article)
            
            # Format 4: Articles array in response
            elif "articles" in data:
                for item in data["articles"]:
                    article = self._create_article_from_source(item, item.get("id", ""), symbol)
                    if article:
                        articles.append(article)
                        
        except Exception as e:
            self.logger.error(f"Error parsing articles response for {symbol}: {e}")
        
        return articles
    
    def _create_article_from_source(self, source: Dict[str, Any], doc_id: str, symbol: str) -> Optional[Dict[str, Any]]:
        """Create an article object from source data"""
        try:
            title = source.get("title", source.get("news_title", ""))
            content = source.get("content", source.get("full_text", source.get("summary", "")))
            
            return {
                "id": doc_id,
                "title": title,
                "content": content,
                "summary": source.get("summary", content[:200] + "..." if len(content) > 200 else content),
                "symbol": symbol,
                "type": source.get("type", source.get("document_type", "news")),
                "published_date": source.get("published_date", source.get("date", "")),
                "source": source.get("source", source.get("news_source", "")),
                "sentiment": source.get("sentiment", source.get("sentiment_score", source.get("news_sentiment", ""))),
                "url": source.get("url", "")
            }
        except Exception as e:
            self.logger.warning(f"Error creating article from source: {e}")
            return None
    
    def _create_article_from_esql_row(self, row: List[Any], col_map: Dict[str, int], symbol: str) -> Optional[Dict[str, Any]]:
        """Create an article object from ES|QL query result row"""
        try:
            def get_col_value(col_name: str, default: Any = "") -> Any:
                idx = col_map.get(col_name, -1)
                if idx >= 0 and idx < len(row):
                    return row[idx] if row[idx] is not None else default
                return default
            
            title = get_col_value("title") or get_col_value("news_title")
            content = get_col_value("content") or get_col_value("full_text") or get_col_value("summary")
            
            if not title and not content:
                return None
            
            return {
                "id": str(get_col_value("_id", get_col_value("id"))),
                "title": str(title),
                "content": str(content),
                "summary": str(get_col_value("summary", content[:200] + "..." if len(str(content)) > 200 else content)),
                "symbol": symbol,
                "type": str(get_col_value("type", get_col_value("document_type", "news"))),
                "published_date": str(get_col_value("published_date", get_col_value("date"))),
                "source": str(get_col_value("source", get_col_value("news_source"))),
                "sentiment": str(get_col_value("sentiment", get_col_value("sentiment_score", get_col_value("news_sentiment")))),
                "url": str(get_col_value("url"))
            }
        except Exception as e:
            self.logger.warning(f"Error creating article from ES|QL row: {e}")
            return None
    
    def _deduplicate_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate articles based on title similarity"""
        seen_titles = set()
        unique_articles = []
        
        for article in articles:
            title_key = article.get("title", "").lower().strip()
            if title_key and title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_articles.append(article)
        
        return unique_articles


# Global instance
account_news_reports_service = AccountNewsReportsService()