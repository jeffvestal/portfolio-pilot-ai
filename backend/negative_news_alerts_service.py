"""
Negative news alerts service for querying designated MCP servers 
to find accounts with positions in negative sentiment news/reports.
"""

import logging
import json
from typing import Dict, List, Any, Optional
from mcp_config import config_manager
from mcp_client import mcp_manager
from es_data_client import es_data_client

logger = logging.getLogger(__name__)


class NegativeNewsAlertsService:
    """Service for fetching negative news alerts from designated MCP servers"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.NegativeNewsAlertsService")
    
    async def get_negative_news_alerts(self, time_period: int, time_unit: str) -> Dict[str, Any]:
        """Get negative news alerts for accounts with positions in negative sentiment news/reports"""
        try:
            # Get servers designated for main page data
            main_page_servers = config_manager.get_main_page_servers()
            
            if not main_page_servers:
                return {
                    "status": "no_servers",
                    "message": "No MCP servers configured for main page data",
                    "alerts": []
                }
            
            self.logger.info(f"Found {len(main_page_servers)} servers designated for main page data")
            
            # Try to get negative news alerts from each designated server
            for server_id, server in main_page_servers.items():
                try:
                    # Check if server has the required tool
                    if "neg_news_reports_with_pos" not in server.tools:
                        self.logger.warning(f"Server {server_id} does not have neg_news_reports_with_pos tool")
                        continue
                    
                    # Get alerts from this server
                    alerts = await self._get_alerts_from_server(server_id, server, time_period, time_unit)
                    if alerts:
                        return {
                            "status": "success",
                            "server_used": server.name,
                            "alerts": alerts
                        }
                except Exception as e:
                    self.logger.warning(f"Failed to get negative news alerts from server {server_id}: {e}")
                    continue
            
            # Check if any server had the required tool
            has_required_tool = any(
                "neg_news_reports_with_pos" in server.tools 
                for server in main_page_servers.values()
            )
            
            if not has_required_tool:
                return {
                    "status": "tool_not_available",
                    "message": "Connected MCP servers do not support negative news analysis tool (neg_news_reports_with_pos)",
                    "alerts": []
                }
            
            # If we get here, servers have the tool but no alerts were found
            return {
                "status": "no_data",
                "message": f"No negative news alerts found for accounts in the last {time_period} {time_unit}",
                "alerts": []
            }
            
        except Exception as e:
            self.logger.error(f"Error getting negative news alerts: {e}")
            return {
                "status": "error", 
                "message": f"Error retrieving negative news alerts: {e}",
                "alerts": []
            }
    
    async def _get_alerts_from_server(self, server_id: str, server, time_period: int, time_unit: str) -> List[Dict[str, Any]]:
        """Get negative news alerts from a specific MCP server"""
        alerts = []
        
        self.logger.info(f"Calling neg_news_reports_with_pos tool on server {server_id} with {time_period} {time_unit}")
        
        # Prepare arguments for the neg_news_reports_with_pos tool
        # The tool expects time_duration as a single string like "48 hours"
        arguments = {
            "time_duration": f"{time_period} {time_unit}"
        }
        
        try:
            async for result in mcp_manager.execute_tool(server_id, "neg_news_reports_with_pos", arguments):
                if result["type"] == "tool_result":
                    content = result["content"]
                    if isinstance(content, dict) and "text" in content:
                        try:
                            data = json.loads(content["text"])
                            self.logger.info(f"Parsed neg_news_reports_with_pos data: {json.dumps(data, indent=2)}")
                            
                            # Parse the alerts from the response
                            alerts = await self._parse_alerts_response(data)
                            
                            if alerts:
                                self.logger.info(f"Successfully parsed {len(alerts)} negative news alerts")
                                return alerts
                                
                        except json.JSONDecodeError as e:
                            self.logger.warning(f"Could not parse neg_news_reports_with_pos response as JSON: {e}")
                    break
                elif result["type"] == "error":
                    self.logger.error(f"Error from neg_news_reports_with_pos tool: {result.get('error', 'Unknown error')}")
                    break
                    
        except Exception as e:
            self.logger.error(f"Error executing neg_news_reports_with_pos tool on server {server_id}: {e}")
        
        return alerts
    
    async def _parse_alerts_response(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse the response from neg_news_reports_with_pos tool into grouped news stories"""
        raw_alerts = []
        
        try:
            # The response format may vary depending on the MCP server implementation
            # Try different response formats
            
            # Format 1: Standard ES response with hits
            if "result" in data and "hits" in data["result"]:
                hits = data["result"]["hits"]["hits"]
                for hit in hits:
                    source = hit.get("_source", {})
                    alert = await self._create_alert_from_source(source, hit.get("_id", ""))
                    if alert:
                        raw_alerts.append(alert)
            
            # Format 2: ES|QL response with values and columns
            elif "result" in data and "values" in data["result"]:
                columns = data["result"].get("columns", [])
                values = data["result"].get("values", [])
                
                # Map column names to indices for easier access
                col_map = {col.get("name", f"col_{i}"): i for i, col in enumerate(columns)}
                
                for row in values:
                    alert = await self._create_alert_from_esql_row(row, col_map)
                    if alert:
                        raw_alerts.append(alert)
            
            # Format 3: Custom format with alerts array
            elif "alerts" in data:
                raw_alerts = data["alerts"]
            
            # Format 4: Direct array response
            elif isinstance(data, list):
                raw_alerts = data
                
        except Exception as e:
            self.logger.error(f"Error parsing alerts response: {e}")
        
        # Group alerts by news title and create grouped news stories
        return await self._group_alerts_by_news_title(raw_alerts[:50])  # Limit to top 50 raw alerts
    
    async def _create_alert_from_source(self, source: Dict[str, Any], doc_id: str) -> Optional[Dict[str, Any]]:
        """Create an alert object from Elasticsearch document source"""
        try:
            return {
                "account_id": source.get("account_id", ""),
                "account_name": source.get("account_name", source.get("account_holder_name", "")),
                "symbol": source.get("symbol", ""),
                "company_name": source.get("company_name", ""),
                "position_value": source.get("position_value", 0),
                "news_title": source.get("news_title", source.get("title", "")),
                "news_summary": source.get("news_summary", source.get("summary", ""))[:200] + "..." if source.get("news_summary", source.get("summary", "")) else "No summary available",
                "sentiment": source.get("sentiment", "negative"),
                "published_date": source.get("published_date", ""),
                "news_source": source.get("news_source", source.get("source", "")),
                "document_id": doc_id,
                "severity": self._calculate_severity(source)
            }
        except Exception as e:
            self.logger.warning(f"Error creating alert from source: {e}")
            return None
    
    async def _create_alert_from_esql_row(self, row: List[Any], col_map: Dict[str, int]) -> Optional[Dict[str, Any]]:
        """Create an alert object from ES|QL query result row"""
        try:
            def get_col_value(col_name: str, default: Any = "") -> Any:
                """Get column value by name with fallback"""
                idx = col_map.get(col_name, -1)
                if idx >= 0 and idx < len(row):
                    return row[idx] if row[idx] is not None else default
                return default
            
            # Map common column patterns
            account_id = get_col_value("account_id") or get_col_value("account")
            symbol = get_col_value("symbol") or get_col_value("ticker")
            title = get_col_value("title") or get_col_value("news_title")
            summary = get_col_value("summary") or get_col_value("news_summary")
            
            if not account_id and not symbol:
                return None  # Skip invalid rows
            
            return {
                "account_id": str(account_id),
                "account_name": str(get_col_value("account_name", get_col_value("account_holder_name"))),
                "symbol": str(symbol),
                "company_name": str(get_col_value("company_name")),
                "position_value": float(get_col_value("position_value", 0)) if get_col_value("position_value") else 0,
                "news_title": str(title),
                "news_summary": str(summary)[:200] + "..." if str(summary) and len(str(summary)) > 200 else str(summary),
                "sentiment": str(get_col_value("sentiment", "negative")),
                "published_date": str(get_col_value("published_date")),
                "news_source": str(get_col_value("source", get_col_value("news_source"))),
                "document_id": str(get_col_value("document_id", get_col_value("_id"))),
                "severity": self._calculate_severity_from_row(row, col_map)
            }
        except Exception as e:
            self.logger.warning(f"Error creating alert from ES|QL row: {e}")
            return None
    
    def _calculate_severity(self, source: Dict[str, Any]) -> str:
        """Calculate alert severity based on source data"""
        # Simple severity calculation based on keywords and position value
        title = (source.get("title", "") + " " + source.get("summary", "")).lower()
        position_value = source.get("position_value", 0)
        
        # High severity keywords
        high_keywords = ["fraud", "lawsuit", "investigation", "bankruptcy", "scandal", "criminal"]
        # Medium severity keywords  
        medium_keywords = ["decline", "loss", "warning", "concern", "risk", "downturn"]
        
        if any(keyword in title for keyword in high_keywords):
            return "high"
        elif any(keyword in title for keyword in medium_keywords) or position_value > 100000:
            return "medium"
        else:
            return "low"
    
    def _calculate_severity_from_row(self, row: List[Any], col_map: Dict[str, int]) -> str:
        """Calculate alert severity from ES|QL row"""
        try:
            # Get title and summary for keyword analysis
            title_idx = col_map.get("title", col_map.get("news_title", -1))
            summary_idx = col_map.get("summary", col_map.get("news_summary", -1))
            position_idx = col_map.get("position_value", -1)
            
            title = ""
            if title_idx >= 0 and title_idx < len(row) and row[title_idx]:
                title += str(row[title_idx]).lower()
            if summary_idx >= 0 and summary_idx < len(row) and row[summary_idx]:
                title += " " + str(row[summary_idx]).lower()
            
            position_value = 0
            if position_idx >= 0 and position_idx < len(row) and row[position_idx]:
                try:
                    position_value = float(row[position_idx])
                except (ValueError, TypeError):
                    position_value = 0
            
            # High severity keywords
            high_keywords = ["fraud", "lawsuit", "investigation", "bankruptcy", "scandal", "criminal"]
            # Medium severity keywords  
            medium_keywords = ["decline", "loss", "warning", "concern", "risk", "downturn"]
            
            if any(keyword in title for keyword in high_keywords):
                return "high"
            elif any(keyword in title for keyword in medium_keywords) or position_value > 100000:
                return "medium"
            else:
                return "low"
                
        except Exception as e:
            self.logger.warning(f"Error calculating severity: {e}")
            return "low"
    
    async def _group_alerts_by_news_title(self, raw_alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Group raw alerts by news title and add position details"""
        grouped_stories = {}
        
        for alert in raw_alerts:
            news_title = alert.get("news_title", "Unknown News")
            
            # Initialize story group if not exists
            if news_title not in grouped_stories:
                grouped_stories[news_title] = {
                    "news_title": news_title,
                    "news_summary": alert.get("news_summary", ""),
                    "sentiment": alert.get("sentiment", "negative"),
                    "published_date": alert.get("published_date", ""),
                    "news_source": alert.get("news_source", ""),
                    "document_id": alert.get("document_id", ""),
                    "symbol": alert.get("symbol", ""),
                    "severity": alert.get("severity", "low"),
                    "total_accounts_affected": 0,
                    "total_exposure": 0.0,
                    "affected_accounts": []
                }
            
            story = grouped_stories[news_title]
            
            # Get detailed position information
            account_id = alert.get("account_id", "")
            symbol = alert.get("symbol", "")
            
            position_details = None
            if account_id and symbol:
                position_details = await es_data_client.get_position_details(account_id, symbol)
            
            # Create account entry with position details
            account_info = {
                "account_id": account_id,
                "account_name": alert.get("account_name", ""),
                "symbol": symbol,
                "company_name": alert.get("company_name", ""),
                "basic_position_value": alert.get("position_value", 0),  # From original alert
            }
            
            # Add detailed position info if available
            if position_details:
                account_info.update({
                    "quantity": position_details.get("quantity", 0),
                    "purchase_price": position_details.get("purchase_price", 0),
                    "current_price": position_details.get("current_price", 0),
                    "total_cost": position_details.get("total_cost", 0),
                    "current_value": position_details.get("current_value", 0),
                    "unrealized_pnl": position_details.get("unrealized_pnl", 0),
                    "unrealized_pnl_pct": position_details.get("unrealized_pnl_pct", 0)
                })
                # Use more accurate current value from position details
                exposure = position_details.get("current_value", 0)
            else:
                # Fallback to basic position value
                exposure = alert.get("position_value", 0)
            
            story["affected_accounts"].append(account_info)
            story["total_accounts_affected"] += 1
            story["total_exposure"] += exposure
            
            # Update story severity to highest found
            alert_severity = alert.get("severity", "low")
            if (alert_severity == "high" or 
                (alert_severity == "medium" and story["severity"] == "low")):
                story["severity"] = alert_severity
        
        # Convert to list and sort by total exposure (highest first)
        result = list(grouped_stories.values())
        result.sort(key=lambda x: x["total_exposure"], reverse=True)
        
        self.logger.info(f"Grouped {len(raw_alerts)} alerts into {len(result)} news stories")
        return result[:10]  # Limit to top 10 stories


# Global instance
negative_news_alerts_service = NegativeNewsAlertsService()