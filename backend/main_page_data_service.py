"""
Main page data service for querying designated MCP servers 
to enhance dashboard content with additional data like news summaries.
"""

import logging
import json
from typing import Dict, List, Any, Optional
from mcp_config import config_manager
from mcp_client import mcp_manager

logger = logging.getLogger(__name__)


class MainPageDataService:
    """Service for fetching additional data from designated MCP servers for the main page"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.MainPageDataService")
    
    async def get_news_summary(self) -> Dict[str, Any]:
        """Get top 10 latest news stories from designated MCP servers"""
        try:
            # Get servers designated for main page data
            main_page_servers = config_manager.get_main_page_servers()
            
            if not main_page_servers:
                return {
                    "status": "no_servers",
                    "message": "No MCP servers configured for main page data",
                    "news_stories": []
                }
            
            self.logger.info(f"Found {len(main_page_servers)} servers designated for main page data")
            
            # Try to get news from each designated server
            for server_id, server in main_page_servers.items():
                try:
                    # Try different approaches to get news data
                    news_stories = await self._get_news_from_server(server_id, server)
                    if news_stories:
                        return {
                            "status": "success",
                            "server_used": server.name,
                            "news_stories": news_stories[:10]  # Top 10
                        }
                except Exception as e:
                    self.logger.warning(f"Failed to get news from server {server_id}: {e}")
                    continue
            
            # If we get here, no servers successfully provided news
            return {
                "status": "no_data",
                "message": "MCP servers configured but unable to retrieve news data",
                "news_stories": []
            }
            
        except Exception as e:
            self.logger.error(f"Error getting news summary: {e}")
            return {
                "status": "error", 
                "message": f"Error retrieving news: {e}",
                "news_stories": []
            }
    
    async def get_reports_summary(self) -> Dict[str, Any]:
        """Get top 10 latest financial reports from designated MCP servers"""
        try:
            # Get servers designated for main page data
            main_page_servers = config_manager.get_main_page_servers()
            
            if not main_page_servers:
                return {
                    "status": "no_servers",
                    "message": "No MCP servers configured for main page data",
                    "reports": []
                }
            
            self.logger.info(f"Found {len(main_page_servers)} servers designated for main page data")
            
            # Try to get reports from each designated server
            for server_id, server in main_page_servers.items():
                try:
                    # Try different approaches to get reports data
                    reports = await self._get_reports_from_server(server_id, server)
                    if reports:
                        return {
                            "status": "success",
                            "server_used": server.name,
                            "reports": reports[:10]  # Top 10
                        }
                except Exception as e:
                    self.logger.warning(f"Failed to get reports from server {server_id}: {e}")
                    continue
            
            # If we get here, no servers successfully provided reports
            return {
                "status": "no_data",
                "message": "MCP servers configured but unable to retrieve reports data",
                "reports": []
            }
            
        except Exception as e:
            self.logger.error(f"Error getting reports summary: {e}")
            return {
                "status": "error", 
                "message": f"Error retrieving reports: {e}",
                "reports": []
            }
    
    async def _get_reports_from_server(self, server_id: str, server) -> List[Dict[str, Any]]:
        """Try to get reports data from a specific MCP server"""
        reports = []
        
        # Check what tools this server has available for reports
        available_tools = server.tools.keys()
        self.logger.debug(f"Server {server_id} has tools: {list(available_tools)}")
        
        # Try different strategies based on available tools
        
        # Strategy 1: Use execute_esql if available (more reliable for ES MCP)
        if "execute_esql" in available_tools:
            try:
                reports = await self._get_reports_via_esql(server_id)
                if reports:
                    return reports
            except Exception as e:
                self.logger.warning(f"execute_esql failed on {server_id}: {e}")
        
        # Strategy 2: Use nl_search if available  
        if "nl_search" in available_tools:
            try:
                reports = await self._get_reports_via_nl_search(server_id)
                if reports:
                    return reports
            except Exception as e:
                self.logger.warning(f"nl_search failed on {server_id}: {e}")
        
        # Strategy 3: Use relevance_search if available
        if "relevance_search" in available_tools:
            try:
                reports = await self._get_reports_via_relevance_search(server_id)
                if reports:
                    return reports
            except Exception as e:
                self.logger.warning(f"relevance_search failed on {server_id}: {e}")
        
        return reports
    
    async def _get_reports_via_nl_search(self, server_id: str) -> List[Dict[str, Any]]:
        """Get reports using natural language search"""
        arguments = {
            "query": "latest financial reports and analysis published in the last 30 days",
            "index": "financial_reports",
            "size": 10,
            "include_source": True
        }
        
        reports = []
        async for result in mcp_manager.execute_tool(server_id, "nl_search", arguments):
            if result["type"] == "tool_result":
                content = result["content"]
                if isinstance(content, dict) and "text" in content:
                    # Parse the JSON response
                    try:
                        data = json.loads(content["text"])
                        self.logger.info(f"Parsed nl_search reports data: {json.dumps(data, indent=2)}")
                        
                        # Handle ES MCP server response format
                        if "result" in data and "results" in data["result"]:
                            results = data["result"]["results"]
                            for i, result_item in enumerate(results[:10]):  # Top 10
                                # Extract highlights as summary
                                highlights = result_item.get("highlights", [])
                                full_summary = " ".join(highlights) if highlights else "No summary available"
                                short_summary = full_summary[:100] + "..." if len(full_summary) > 100 else full_summary
                                
                                # Create a more descriptive title from highlights or use a generic one
                                title = f"Financial Report {i+1}"
                                if highlights:
                                    # Try to extract a title-like phrase from the first highlight
                                    first_highlight = highlights[0]
                                    # Remove HTML tags and take first part
                                    clean_highlight = first_highlight.replace('<em>', '').replace('</em>', '')
                                    if len(clean_highlight) > 20:
                                        title = clean_highlight[:60] + "..." if len(clean_highlight) > 60 else clean_highlight
                                
                                reports.append({
                                    "title": title,
                                    "symbol": "",  # Not available in highlights format
                                    "published_date": "",  # Not available in highlights format  
                                    "summary": short_summary,  # Short version for display
                                    "summary_full": full_summary,  # Full version for expansion
                                    "document_id": result_item.get("id", ""),  # ES document ID for full report retrieval
                                    "index": result_item.get("index", "financial_reports")  # ES index name
                                })
                            
                            if reports:
                                self.logger.info(f"Successfully parsed {len(reports)} reports from nl_search")
                                return reports
                        # Fallback to standard Elasticsearch format
                        elif "result" in data and "hits" in data["result"]:
                            hits = data["result"]["hits"]["hits"]
                            for hit in hits[:10]:  # Top 10
                                source = hit.get("_source", {})
                                reports.append({
                                    "title": source.get("title", "No title"),
                                    "symbol": source.get("symbol", ""),
                                    "published_date": source.get("published_date", ""),
                                    "summary": source.get("summary", source.get("content", ""))[:100] + "..." if source.get("summary", source.get("content", "")) else "No summary available",
                                    "summary_full": source.get("summary", source.get("content", "")) or "No summary available",
                                    "document_id": hit.get("_id", ""),
                                    "index": "financial_reports"
                                })
                    except json.JSONDecodeError:
                        self.logger.warning(f"Could not parse nl_search reports response as JSON")
                break
        
        return reports
    
    async def _get_reports_via_esql(self, server_id: str) -> List[Dict[str, Any]]:
        """Get reports using ES|QL query"""
        # Try different ES|QL queries to get reports data
        queries = [
            "FROM financial_reports | SORT published_date DESC | LIMIT 10 | KEEP title, symbol, published_date, summary",
            "FROM financial_reports | SORT @timestamp DESC | LIMIT 10 | KEEP title, symbol, published_date, summary", 
            "FROM financial_reports | LIMIT 10 | KEEP title, symbol, published_date, summary, content"
        ]
        
        for query in queries:
            self.logger.info(f"Trying ES|QL reports query: {query}")
            arguments = {"query": query}
            
            reports = []
            try:
                async for result in mcp_manager.execute_tool(server_id, "execute_esql", arguments):
                    if result["type"] == "tool_result":
                        content = result["content"]
                        self.logger.info(f"ES|QL reports result content: {content}")
                        
                        if isinstance(content, dict) and "text" in content:
                            try:
                                data = json.loads(content["text"])
                                self.logger.info(f"Parsed ES|QL reports data: {json.dumps(data, indent=2)}")
                                
                                if "result" in data and "values" in data["result"]:
                                    columns = data["result"].get("columns", [])
                                    values = data["result"].get("values", [])
                                    self.logger.info(f"ES|QL reports columns: {columns}")
                                    self.logger.info(f"ES|QL reports values count: {len(values)}")
                                    
                                    # Map columns to values
                                    for row in values:
                                        if len(row) >= 3:  # At least title, symbol, date
                                            full_summary = str(row[3]) if len(row) > 3 and row[3] else (str(row[4]) if len(row) > 4 and row[4] else "No summary available")
                                            short_summary = full_summary[:100] + "..." if len(full_summary) > 100 else full_summary
                                            
                                            reports.append({
                                                "title": str(row[0])[:100] if len(row) > 0 and row[0] else "Financial Report",
                                                "symbol": str(row[1]) if len(row) > 1 and row[1] else "",
                                                "published_date": str(row[2]) if len(row) > 2 and row[2] else "",
                                                "summary": short_summary,
                                                "summary_full": full_summary,
                                                "document_id": str(row[0])[:50] if len(row) > 0 and row[0] else "",  # Use title as temp ID
                                                "index": "financial_reports"
                                            })
                                    
                                    if reports:
                                        self.logger.info(f"Successfully parsed {len(reports)} reports from ES|QL")
                                        return reports
                                        
                            except json.JSONDecodeError as e:
                                self.logger.warning(f"Could not parse execute_esql reports response as JSON: {e}")
                        break
                        
            except Exception as e:
                self.logger.warning(f"ES|QL reports query failed: {query} - {e}")
                continue
        
        return reports
    
    async def _get_reports_via_relevance_search(self, server_id: str) -> List[Dict[str, Any]]:
        """Get reports using relevance search"""
        arguments = {
            "term": "financial reports analysis",
            "index": "financial_reports",
            "size": 10
        }
        
        reports = []
        async for result in mcp_manager.execute_tool(server_id, "relevance_search", arguments):
            if result["type"] == "tool_result":
                content = result["content"]
                if isinstance(content, dict) and "text" in content:
                    try:
                        data = json.loads(content["text"])
                        self.logger.info(f"Parsed relevance_search reports data: {json.dumps(data, indent=2)}")
                        
                        # Handle ES MCP server response format (same as nl_search)
                        if "result" in data and "results" in data["result"]:
                            results = data["result"]["results"]
                            for i, result_item in enumerate(results[:10]):  # Top 10
                                # Extract highlights as summary
                                highlights = result_item.get("highlights", [])
                                full_summary = " ".join(highlights) if highlights else "No summary available"
                                short_summary = full_summary[:100] + "..." if len(full_summary) > 100 else full_summary
                                
                                # Create a more descriptive title from highlights or use a generic one
                                title = f"Financial Report {i+1}"
                                if highlights:
                                    # Try to extract a title-like phrase from the first highlight
                                    first_highlight = highlights[0]
                                    # Remove HTML tags and take first part
                                    clean_highlight = first_highlight.replace('<em>', '').replace('</em>', '')
                                    if len(clean_highlight) > 20:
                                        title = clean_highlight[:60] + "..." if len(clean_highlight) > 60 else clean_highlight
                                
                                reports.append({
                                    "title": title,
                                    "symbol": "",  # Not available in highlights format
                                    "published_date": "",  # Not available in highlights format  
                                    "summary": short_summary,  # Short version for display
                                    "summary_full": full_summary,  # Full version for expansion
                                    "document_id": result_item.get("id", ""),  # ES document ID for full report retrieval
                                    "index": result_item.get("index", "financial_reports")  # ES index name
                                })
                            
                            if reports:
                                self.logger.info(f"Successfully parsed {len(reports)} reports from relevance_search")
                                return reports
                        # Fallback to standard Elasticsearch format
                        elif "result" in data and "hits" in data["result"]:
                            hits = data["result"]["hits"]["hits"]
                            for hit in hits:
                                source = hit.get("_source", {})
                                reports.append({
                                    "title": source.get("title", "No title"),
                                    "symbol": source.get("symbol", ""),
                                    "published_date": source.get("published_date", ""),
                                    "summary": (source.get("summary", source.get("content", ""))[:100] + "...") if source.get("summary", source.get("content", "")) else "No summary available",
                                    "summary_full": source.get("summary", source.get("content", "")) or "No summary available",
                                    "document_id": hit.get("_id", ""),
                                    "index": "financial_reports"
                                })
                    except json.JSONDecodeError:
                        self.logger.warning(f"Could not parse relevance_search reports response as JSON")
                break
        
        return reports
    
    async def _get_news_from_server(self, server_id: str, server) -> List[Dict[str, Any]]:
        """Try to get news data from a specific MCP server"""
        news_stories = []
        
        # Check what tools this server has available for news
        available_tools = server.tools.keys()
        self.logger.debug(f"Server {server_id} has tools: {list(available_tools)}")
        
        # Try different strategies based on available tools
        
        # Strategy 1: Use execute_esql if available (more reliable for ES MCP)
        if "execute_esql" in available_tools:
            try:
                news_stories = await self._get_news_via_esql(server_id)
                if news_stories:
                    return news_stories
            except Exception as e:
                self.logger.warning(f"execute_esql failed on {server_id}: {e}")
        
        # Strategy 2: Use nl_search if available  
        if "nl_search" in available_tools:
            try:
                news_stories = await self._get_news_via_nl_search(server_id)
                if news_stories:
                    return news_stories
            except Exception as e:
                self.logger.warning(f"nl_search failed on {server_id}: {e}")
        
        # Strategy 3: Use relevance_search if available
        if "relevance_search" in available_tools:
            try:
                news_stories = await self._get_news_via_relevance_search(server_id)
                if news_stories:
                    return news_stories
            except Exception as e:
                self.logger.warning(f"relevance_search failed on {server_id}: {e}")
        
        return news_stories
    
    async def _get_news_via_nl_search(self, server_id: str) -> List[Dict[str, Any]]:
        """Get news using natural language search"""
        arguments = {
            "query": "latest financial news stories published in the last 7 days",
            "index": "financial_news",
            "size": 10,
            "include_source": True
        }
        
        news_stories = []
        async for result in mcp_manager.execute_tool(server_id, "nl_search", arguments):
            if result["type"] == "tool_result":
                content = result["content"]
                if isinstance(content, dict) and "text" in content:
                    # Parse the JSON response
                    try:
                        data = json.loads(content["text"])
                        self.logger.info(f"Parsed nl_search data: {json.dumps(data, indent=2)}")
                        
                        # Handle ES MCP server response format
                        if "result" in data and "results" in data["result"]:
                            results = data["result"]["results"]
                            for i, result_item in enumerate(results[:10]):  # Top 10
                                # Extract highlights as summary
                                highlights = result_item.get("highlights", [])
                                full_summary = " ".join(highlights) if highlights else "No summary available"
                                short_summary = full_summary[:100] + "..." if len(full_summary) > 100 else full_summary
                                
                                # Create a more descriptive title from highlights or use a generic one
                                title = f"Financial News Story {i+1}"
                                if highlights:
                                    # Try to extract a title-like phrase from the first highlight
                                    first_highlight = highlights[0]
                                    # Remove HTML tags and take first part
                                    clean_highlight = first_highlight.replace('<em>', '').replace('</em>', '')
                                    if len(clean_highlight) > 20:
                                        title = clean_highlight[:60] + "..." if len(clean_highlight) > 60 else clean_highlight
                                
                                news_stories.append({
                                    "title": title,
                                    "symbol": "",  # Not available in highlights format
                                    "published_date": "",  # Not available in highlights format  
                                    "summary": short_summary,  # Short version for display
                                    "summary_full": full_summary,  # Full version for expansion
                                    "document_id": result_item.get("id", ""),  # ES document ID for full article retrieval
                                    "index": result_item.get("index", "financial_news")  # ES index name
                                })
                            
                            if news_stories:
                                self.logger.info(f"Successfully parsed {len(news_stories)} news stories from nl_search")
                                return news_stories
                        # Fallback to standard Elasticsearch format
                        elif "result" in data and "hits" in data["result"]:
                            hits = data["result"]["hits"]["hits"]
                            for hit in hits[:10]:  # Top 10
                                source = hit.get("_source", {})
                                news_stories.append({
                                    "title": source.get("title", "No title"),
                                    "symbol": source.get("symbol", ""),
                                    "published_date": source.get("published_date", ""),
                                    "summary": source.get("summary", source.get("content", ""))[:200] + "..." if source.get("summary", source.get("content", "")) else "No summary available"
                                })
                    except json.JSONDecodeError:
                        self.logger.warning(f"Could not parse nl_search response as JSON")
                break
        
        return news_stories
    
    async def _get_news_via_esql(self, server_id: str) -> List[Dict[str, Any]]:
        """Get news using ES|QL query"""
        # Try different ES|QL queries to get news data
        queries = [
            "FROM financial_news | SORT published_date DESC | LIMIT 10 | KEEP title, symbol, published_date, summary",
            "FROM financial_news | SORT @timestamp DESC | LIMIT 10 | KEEP title, symbol, published_date, summary", 
            "FROM financial_news | LIMIT 10 | KEEP title, symbol, published_date, summary, content"
        ]
        
        for query in queries:
            self.logger.info(f"Trying ES|QL query: {query}")
            arguments = {"query": query}
            
            news_stories = []
            try:
                async for result in mcp_manager.execute_tool(server_id, "execute_esql", arguments):
                    if result["type"] == "tool_result":
                        content = result["content"]
                        self.logger.info(f"ES|QL result content: {content}")
                        
                        if isinstance(content, dict) and "text" in content:
                            try:
                                data = json.loads(content["text"])
                                self.logger.info(f"Parsed ES|QL data: {json.dumps(data, indent=2)}")
                                
                                if "result" in data and "values" in data["result"]:
                                    columns = data["result"].get("columns", [])
                                    values = data["result"].get("values", [])
                                    self.logger.info(f"ES|QL columns: {columns}")
                                    self.logger.info(f"ES|QL values count: {len(values)}")
                                    
                                    # Map columns to values
                                    for row in values:
                                        if len(row) >= 3:  # At least title, symbol, date
                                            news_stories.append({
                                                "title": str(row[0])[:100] if len(row) > 0 and row[0] else "Financial News",
                                                "symbol": str(row[1]) if len(row) > 1 and row[1] else "",
                                                "published_date": str(row[2]) if len(row) > 2 and row[2] else "",
                                                "summary": (str(row[3])[:200] + "...") if len(row) > 3 and row[3] else (str(row[4])[:200] + "..." if len(row) > 4 and row[4] else "No summary available")
                                            })
                                    
                                    if news_stories:
                                        self.logger.info(f"Successfully parsed {len(news_stories)} news stories from ES|QL")
                                        return news_stories
                                        
                            except json.JSONDecodeError as e:
                                self.logger.warning(f"Could not parse execute_esql response as JSON: {e}")
                        break
                        
            except Exception as e:
                self.logger.warning(f"ES|QL query failed: {query} - {e}")
                continue
        
        return news_stories
    
    async def _get_news_via_relevance_search(self, server_id: str) -> List[Dict[str, Any]]:
        """Get news using relevance search"""
        arguments = {
            "term": "financial news",
            "index": "financial_news",
            "size": 10
        }
        
        news_stories = []
        async for result in mcp_manager.execute_tool(server_id, "relevance_search", arguments):
            if result["type"] == "tool_result":
                content = result["content"]
                if isinstance(content, dict) and "text" in content:
                    try:
                        data = json.loads(content["text"])
                        self.logger.info(f"Parsed relevance_search data: {json.dumps(data, indent=2)}")
                        
                        # Handle ES MCP server response format (same as nl_search)
                        if "result" in data and "results" in data["result"]:
                            results = data["result"]["results"]
                            for i, result_item in enumerate(results[:10]):  # Top 10
                                # Extract highlights as summary
                                highlights = result_item.get("highlights", [])
                                full_summary = " ".join(highlights) if highlights else "No summary available"
                                short_summary = full_summary[:100] + "..." if len(full_summary) > 100 else full_summary
                                
                                # Create a more descriptive title from highlights or use a generic one
                                title = f"Financial News Story {i+1}"
                                if highlights:
                                    # Try to extract a title-like phrase from the first highlight
                                    first_highlight = highlights[0]
                                    # Remove HTML tags and take first part
                                    clean_highlight = first_highlight.replace('<em>', '').replace('</em>', '')
                                    if len(clean_highlight) > 20:
                                        title = clean_highlight[:60] + "..." if len(clean_highlight) > 60 else clean_highlight
                                
                                news_stories.append({
                                    "title": title,
                                    "symbol": "",  # Not available in highlights format
                                    "published_date": "",  # Not available in highlights format  
                                    "summary": short_summary,  # Short version for display
                                    "summary_full": full_summary,  # Full version for expansion
                                    "document_id": result_item.get("id", ""),  # ES document ID for full article retrieval
                                    "index": result_item.get("index", "financial_news")  # ES index name
                                })
                            
                            if news_stories:
                                self.logger.info(f"Successfully parsed {len(news_stories)} news stories from relevance_search")
                                return news_stories
                        # Fallback to standard Elasticsearch format
                        elif "result" in data and "hits" in data["result"]:
                            hits = data["result"]["hits"]["hits"]
                            for hit in hits:
                                source = hit.get("_source", {})
                                news_stories.append({
                                    "title": source.get("title", "No title"),
                                    "symbol": source.get("symbol", ""),
                                    "published_date": source.get("published_date", ""),
                                    "summary": (source.get("summary", source.get("content", ""))[:200] + "...") if source.get("summary", source.get("content", "")) else "No summary available"
                                })
                    except json.JSONDecodeError:
                        self.logger.warning(f"Could not parse relevance_search response as JSON")
                break
        
        return news_stories


# Global instance
main_page_data_service = MainPageDataService()