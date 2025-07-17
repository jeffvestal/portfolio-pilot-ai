"""
Action Item service for getting top accounts by position value and analyzing negative news.
"""

import logging
import json
from typing import Dict, List, Any, Optional
from es_data_client import es_data_client
from mcp_config import config_manager
from mcp_client import mcp_manager

logger = logging.getLogger(__name__)


class ActionItemService:
    """Service for generating action items about top accounts and negative news"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.ActionItemService")
    
    async def get_top_accounts_by_position_value(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top accounts by total position value"""
        try:
            # Query to get accounts with their total portfolio values
            response = await es_data_client.client.search(
                index="financial_accounts",
                body={
                    "query": {"match_all": {}},
                    "size": limit,
                    "sort": [{"total_portfolio_value": {"order": "desc"}}]
                }
            )
            
            top_accounts = []
            for hit in response["hits"]["hits"]:
                source = hit["_source"]
                account_data = {
                    "account_id": hit["_id"],
                    "account_name": source.get("account_holder_name", "Unknown Account"),
                    "total_portfolio_value": source.get("total_portfolio_value", 0),
                    "account_type": source.get("account_type", "Unknown"),
                    "state": source.get("state", "Unknown"),
                    "risk_profile": source.get("risk_profile", "Unknown")
                }
                top_accounts.append(account_data)
            
            self.logger.info(f"Found {len(top_accounts)} top accounts by position value")
            return top_accounts
            
        except Exception as e:
            self.logger.error(f"Error getting top accounts by position value: {e}")
            return []
    
    async def get_action_item_analysis(self, time_period: int = 48, time_unit: str = "hours") -> Dict[str, Any]:
        """Get action item analysis for top accounts with negative news"""
        try:
            # Get top accounts by position value
            top_accounts = await self.get_top_accounts_by_position_value(limit=10)
            
            if not top_accounts:
                return {
                    "status": "error",
                    "message": "Unable to retrieve top accounts",
                    "top_accounts": [],
                    "negative_news": []
                }
            
            # Get total value of top accounts for context
            total_value = sum(acc["total_portfolio_value"] for acc in top_accounts)
            
            # Query MCP server for negative news about these accounts
            negative_news_result = await self._query_negative_news_for_accounts(
                top_accounts, time_period, time_unit
            )
            
            if negative_news_result["status"] == "success" and negative_news_result["alerts"]:
                # Found negative news
                affected_accounts = self._get_affected_accounts_from_alerts(
                    negative_news_result["alerts"], top_accounts
                )
                
                return {
                    "status": "success",
                    "message": f"Found negative news affecting {len(affected_accounts)} of your top {len(top_accounts)} accounts (${total_value:,.0f} total value)",
                    "top_accounts": top_accounts,
                    "negative_news": negative_news_result["alerts"],
                    "affected_accounts": affected_accounts,
                    "server_used": negative_news_result.get("server_used", "MCP Server")
                }
            else:
                # No negative news found (or error)
                return {
                    "status": "no_negative_news",
                    "message": f"No negative news found for your top {len(top_accounts)} accounts (${total_value:,.0f} total value)",
                    "top_accounts": top_accounts,
                    "negative_news": [],
                    "affected_accounts": [],
                    "server_used": negative_news_result.get("server_used", "MCP Server")
                }
            
        except Exception as e:
            self.logger.error(f"Error getting action item analysis: {e}")
            return {
                "status": "error",
                "message": f"Error analyzing top accounts: {str(e)}",
                "top_accounts": [],
                "negative_news": [],
                "affected_accounts": []
            }
    
    async def _query_negative_news_for_accounts(self, top_accounts: List[Dict[str, Any]], 
                                              time_period: int, time_unit: str) -> Dict[str, Any]:
        """Query MCP server for negative news about specific accounts"""
        try:
            # Get servers designated for main page data
            main_page_servers = config_manager.get_main_page_servers()
            
            if not main_page_servers:
                return {
                    "status": "no_servers",
                    "message": "No MCP servers configured for main page data",
                    "alerts": []
                }
            
            # Try to get negative news alerts from each designated server
            for server_id, server in main_page_servers.items():
                try:
                    # Check if server has the required tool
                    if "neg_news_reports_with_pos" not in server.tools:
                        self.logger.warning(f"Server {server_id} does not have neg_news_reports_with_pos tool")
                        continue
                    
                    # Get alerts from this server
                    alerts = await self._get_alerts_from_server(server_id, server, time_period, time_unit)
                    
                    # Filter alerts to only include our top accounts
                    filtered_alerts = self._filter_alerts_for_top_accounts(alerts, top_accounts)
                    
                    if filtered_alerts:
                        return {
                            "status": "success",
                            "server_used": server.name,
                            "alerts": filtered_alerts
                        }
                        
                except Exception as e:
                    self.logger.warning(f"Failed to get negative news from server {server_id}: {e}")
                    continue
            
            return {
                "status": "no_data",
                "message": "No negative news found for top accounts",
                "alerts": []
            }
            
        except Exception as e:
            self.logger.error(f"Error querying negative news for accounts: {e}")
            return {
                "status": "error",
                "message": f"Error querying negative news: {str(e)}",
                "alerts": []
            }
    
    async def _get_alerts_from_server(self, server_id: str, server, time_period: int, time_unit: str) -> List[Dict[str, Any]]:
        """Get negative news alerts from a specific MCP server"""
        alerts = []
        
        self.logger.info(f"Calling neg_news_reports_with_pos tool on server {server_id}")
        
        # Prepare arguments for the neg_news_reports_with_pos tool
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
                            self.logger.info(f"Got neg_news_reports_with_pos data from server {server_id}")
                            
                            # Parse the alerts from the response (reuse existing parsing logic)
                            alerts = await self._parse_alerts_response(data)
                            
                            if alerts:
                                self.logger.info(f"Successfully parsed {len(alerts)} alerts")
                                return alerts
                                
                        except json.JSONDecodeError as e:
                            self.logger.warning(f"Could not parse response as JSON: {e}")
                    break
                elif result["type"] == "error":
                    self.logger.error(f"Error from neg_news_reports_with_pos tool: {result.get('error', 'Unknown error')}")
                    break
                    
        except Exception as e:
            self.logger.error(f"Error executing neg_news_reports_with_pos tool: {e}")
        
        return alerts
    
    async def _parse_alerts_response(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse the response from neg_news_reports_with_pos tool"""
        alerts = []
        
        try:
            # Standard ES response with hits
            if "result" in data and "hits" in data["result"]:
                hits = data["result"]["hits"]["hits"]
                for hit in hits:
                    source = hit.get("_source", {})
                    alert = {
                        "account_id": source.get("account_id", ""),
                        "account_name": source.get("account_name", source.get("account_holder_name", "")),
                        "symbol": source.get("symbol", ""),
                        "company_name": source.get("company_name", ""),
                        "position_value": source.get("position_value", 0),
                        "news_title": source.get("news_title", source.get("title", "")),
                        "news_summary": source.get("news_summary", source.get("summary", ""))[:200] + "..." if source.get("news_summary", source.get("summary", "")) else "",
                        "sentiment": source.get("sentiment", "negative"),
                        "published_date": source.get("published_date", ""),
                        "news_source": source.get("news_source", source.get("source", "")),
                        "document_id": hit.get("_id", "")
                    }
                    alerts.append(alert)
            
            # ES|QL response with values and columns
            elif "result" in data and "values" in data["result"]:
                columns = data["result"].get("columns", [])
                values = data["result"].get("values", [])
                
                col_map = {col.get("name", f"col_{i}"): i for i, col in enumerate(columns)}
                
                for row in values:
                    alert = self._create_alert_from_row(row, col_map)
                    if alert:
                        alerts.append(alert)
                        
        except Exception as e:
            self.logger.error(f"Error parsing alerts response: {e}")
        
        return alerts
    
    def _create_alert_from_row(self, row: List[Any], col_map: Dict[str, int]) -> Optional[Dict[str, Any]]:
        """Create alert from ES|QL row"""
        try:
            def get_col_value(col_name: str, default: Any = "") -> Any:
                idx = col_map.get(col_name, -1)
                if idx >= 0 and idx < len(row):
                    return row[idx] if row[idx] is not None else default
                return default
            
            account_id = get_col_value("account_id") or get_col_value("account")
            symbol = get_col_value("symbol") or get_col_value("ticker")
            
            if not account_id:
                return None
            
            return {
                "account_id": str(account_id),
                "account_name": str(get_col_value("account_name", get_col_value("account_holder_name"))),
                "symbol": str(symbol),
                "company_name": str(get_col_value("company_name")),
                "position_value": float(get_col_value("position_value", 0)) if get_col_value("position_value") else 0,
                "news_title": str(get_col_value("title") or get_col_value("news_title")),
                "news_summary": str(get_col_value("summary") or get_col_value("news_summary"))[:200] + "..." if str(get_col_value("summary") or get_col_value("news_summary")) else "",
                "sentiment": str(get_col_value("sentiment", "negative")),
                "published_date": str(get_col_value("published_date")),
                "news_source": str(get_col_value("source", get_col_value("news_source"))),
                "document_id": str(get_col_value("document_id", get_col_value("_id")))
            }
        except Exception as e:
            self.logger.warning(f"Error creating alert from row: {e}")
            return None
    
    def _filter_alerts_for_top_accounts(self, alerts: List[Dict[str, Any]], 
                                       top_accounts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter alerts to only include top accounts"""
        top_account_ids = {acc["account_id"] for acc in top_accounts}
        
        filtered_alerts = []
        for alert in alerts:
            if alert.get("account_id") in top_account_ids:
                filtered_alerts.append(alert)
        
        self.logger.info(f"Filtered {len(alerts)} alerts to {len(filtered_alerts)} for top accounts")
        return filtered_alerts
    
    def _get_affected_accounts_from_alerts(self, alerts: List[Dict[str, Any]], 
                                         top_accounts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get list of affected accounts from alerts"""
        affected_account_ids = {alert.get("account_id") for alert in alerts}
        
        affected_accounts = []
        for account in top_accounts:
            if account["account_id"] in affected_account_ids:
                affected_accounts.append(account)
        
        return affected_accounts


# Global instance
action_item_service = ActionItemService()