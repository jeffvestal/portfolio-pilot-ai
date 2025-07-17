"""
Dedicated Elasticsearch data client for dashboard functionality.
This is separate from MCP and provides direct ES access for the financial analyst UI.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from elasticsearch import AsyncElasticsearch
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class ESDataClient:
    """Elasticsearch client for dashboard data access"""
    
    def __init__(self):
        # Use the ES configuration from environment
        self.es_endpoint = os.getenv("ES_ENDPOINT_URL", "https://localhost:9200")
        self.es_api_key = os.getenv("ES_API_KEY", "VjJDYTVaY0JxOVM3M2tfUkxrV2w6azExUG1SZXZ4WTkxd25hY1JaUExCZw==")
        
        # Create async ES client with SSL verification disabled for local development
        self.client = AsyncElasticsearch(
            hosts=[self.es_endpoint],
            api_key=self.es_api_key,
            verify_certs=False,  # Disable SSL certificate verification
            ssl_show_warn=False  # Suppress SSL warnings
        )
        
        logger.info(f"ES Data Client initialized for dashboard at {self.es_endpoint}")
    
    async def get_metrics_overview(self) -> Dict[str, Any]:
        """Get overview metrics for the dashboard"""
        try:
            # Get total accounts count
            accounts_response = await self.client.count(index="financial_accounts")
            total_accounts = accounts_response["count"]
            
            # Get total AUM by aggregating portfolio values
            aum_response = await self.client.search(
                index="financial_accounts",
                body={
                    "size": 0,
                    "aggs": {
                        "total_aum": {
                            "sum": {"field": "total_portfolio_value"}
                        }
                    }
                }
            )
            total_aum = aum_response["aggregations"]["total_aum"]["value"] or 0
            
            # Get total news count
            news_response = await self.client.count(index="financial_news")
            total_news = news_response["count"]
            
            # Get total reports count
            reports_response = await self.client.count(index="financial_reports")
            total_reports = reports_response["count"]
            
            return {
                "total_accounts": total_accounts,
                "total_aum": int(total_aum),
                "total_news": total_news,
                "total_reports": total_reports
            }
            
        except Exception as e:
            logger.error(f"Error fetching metrics overview: {e}")
            # Return fallback data
            return {
                "total_accounts": 0,
                "total_aum": 0,
                "total_news": 0,
                "total_reports": 0
            }
    
    async def get_account_details(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed account information including holdings and relevant news"""
        try:
            # Get account basic info
            account_response = await self.client.get(
                index="financial_accounts",
                id=account_id
            )
            account_data = account_response["_source"]
            
            # Get account holdings
            holdings_response = await self.client.search(
                index="financial_holdings",
                body={
                    "query": {"term": {"account_id": account_id}},
                    "size": 100
                }
            )
            holdings = [hit["_source"] for hit in holdings_response["hits"]["hits"]]
            
            # Get relevant news for this account's holdings symbols
            symbols = list(set([holding.get("symbol") for holding in holdings if holding.get("symbol")]))
            
            relevant_news = []
            if symbols:
                news_response = await self.client.search(
                    index="financial_news",
                    body={
                        "query": {"terms": {"symbol": symbols}},
                        "size": 10,
                        "sort": [{"published_date": {"order": "desc"}}]
                    }
                )
                relevant_news = [hit["_source"] for hit in news_response["hits"]["hits"]]
            
            # Format the response for the frontend
            return {
                "account_id": account_id,
                "account_name": account_data.get("account_holder_name", "Unknown Account"),
                "state": account_data.get("state", "Unknown"),
                "type": account_data.get("account_type", "Unknown"),
                "risk_profile": account_data.get("risk_profile", "Unknown"),
                "total_portfolio_value": account_data.get("total_portfolio_value", 0),
                "holdings": [
                    {
                        "symbol": holding.get("symbol", ""),
                        "company_name": holding.get("symbol", ""),  # Could be enhanced with company lookup
                        "total_quantity": holding.get("quantity", 0),
                        "total_current_value": holding.get("quantity", 0) * holding.get("purchase_price", 0),
                        "sector": "Technology"  # Could be enhanced with sector lookup
                    }
                    for holding in holdings
                ],
                "relevant_news": {
                    "summary": f"Found {len(relevant_news)} recent news articles for this account's holdings.",
                    "articles": [
                        {
                            "id": news.get("id", ""),
                            "title": news.get("title", ""),
                            "symbol": news.get("symbol", ""),
                            "published_date": news.get("published_date", "")
                        }
                        for news in relevant_news
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Error fetching account {account_id}: {e}")
            return None
    
    async def get_all_accounts(self) -> List[Dict[str, Any]]:
        """Get all accounts for listing/selection"""
        try:
            response = await self.client.search(
                index="financial_accounts",
                body={"query": {"match_all": {}}, "size": 1000}
            )
            
            return [
                {
                    "account_id": hit["_id"],
                    "account_holder_name": hit["_source"].get("account_holder_name", ""),
                    "state": hit["_source"].get("state", ""),
                    "total_portfolio_value": hit["_source"].get("total_portfolio_value", 0)
                }
                for hit in response["hits"]["hits"]
            ]
            
        except Exception as e:
            logger.error(f"Error fetching all accounts: {e}")
            return []
    
    async def get_article_content(self, article_id: str) -> Optional[str]:
        """Get news article content"""
        try:
            response = await self.client.get(
                index="financial_news",
                id=article_id
            )
            return response["_source"].get("content", "Content not available")
            
        except Exception as e:
            logger.error(f"Error fetching article {article_id}: {e}")
            return None
    
    async def get_report_content(self, report_id: str) -> Optional[str]:
        """Get financial report content"""
        try:
            response = await self.client.get(
                index="financial_reports",
                id=report_id
            )
            return response["_source"].get("content", "Content not available")
            
        except Exception as e:
            logger.error(f"Error fetching report {report_id}: {e}")
            return None
    
    async def get_all_news(self) -> List[Dict[str, Any]]:
        """Get all news articles for the news list page"""
        try:
            response = await self.client.search(
                index="financial_news",
                body={
                    "query": {"match_all": {}}, 
                    "size": 1000,
                    "sort": [{"published_date": {"order": "desc"}}]
                }
            )
            
            return [
                {
                    "id": hit["_id"],
                    "title": hit["_source"].get("title", "No title"),
                    "symbol": hit["_source"].get("symbol", ""),
                    "published_date": hit["_source"].get("published_date", ""),
                    "summary": hit["_source"].get("summary", "")[:200] + "..." if hit["_source"].get("summary", "") else "No summary available",
                    "source": hit["_source"].get("source", ""),
                    "url": hit["_source"].get("url", ""),
                    "document_id": hit["_id"],
                    "index": "financial_news"
                }
                for hit in response["hits"]["hits"]
            ]
            
        except Exception as e:
            logger.error(f"Error fetching all news: {e}")
            return []
    
    async def get_all_reports(self) -> List[Dict[str, Any]]:
        """Get all reports for the reports list page"""
        try:
            logger.info("🔍 ES Client: Searching financial_reports index")
            response = await self.client.search(
                index="financial_reports",
                body={
                    "query": {"match_all": {}}, 
                    "size": 1000,
                    "sort": [{"report_date": {"order": "desc"}}]
                }
            )
            logger.info(f"🔍 ES Client: Query response - total hits: {response['hits']['total']['value'] if 'hits' in response and 'total' in response['hits'] else 'unknown'}")
            logger.info(f"🔍 ES Client: Returned {len(response['hits']['hits']) if 'hits' in response else 0} documents")
            
            return [
                {
                    "id": hit["_id"],
                    "title": hit["_source"].get("title", "No title"),
                    "symbol": hit["_source"].get("primary_symbol", hit["_source"].get("company_symbol", "")),
                    "published_date": hit["_source"].get("report_date", ""),
                    "summary": hit["_source"].get("content", "")[:200] + "..." if hit["_source"].get("content", "") else "No summary available",
                    "source": hit["_source"].get("author", ""),
                    "url": hit["_source"].get("url", ""),
                    "document_id": hit["_id"],
                    "index": "financial_reports"
                }
                for hit in response["hits"]["hits"]
            ]
            
        except Exception as e:
            logger.error(f"❌ ES Client: Error fetching all reports: {e}", exc_info=True)
            return []
    
    async def get_position_details(self, account_id: str, symbol: str) -> Optional[Dict[str, Any]]:
        """Get detailed position information for a specific account and symbol"""
        try:
            response = await self.client.search(
                index="financial_holdings",
                body={
                    "query": {
                        "bool": {
                            "must": [
                                {"term": {"account_id": account_id}},
                                {"term": {"symbol": symbol}}
                            ]
                        }
                    },
                    "size": 1
                }
            )
            
            if not response["hits"]["hits"]:
                return None
                
            holding = response["hits"]["hits"][0]["_source"]
            quantity = holding.get("quantity", 0)
            purchase_price = holding.get("purchase_price", 0)
            current_price = holding.get("current_price", purchase_price)  # Fallback to purchase price if no current price
            
            total_cost = quantity * purchase_price
            current_value = quantity * current_price
            unrealized_pnl = current_value - total_cost
            unrealized_pnl_pct = (unrealized_pnl / total_cost * 100) if total_cost > 0 else 0
            
            return {
                "account_id": account_id,
                "symbol": symbol,
                "quantity": quantity,
                "purchase_price": purchase_price,
                "current_price": current_price,
                "total_cost": total_cost,
                "current_value": current_value,
                "unrealized_pnl": unrealized_pnl,
                "unrealized_pnl_pct": unrealized_pnl_pct
            }
            
        except Exception as e:
            logger.error(f"Error fetching position details for {account_id}/{symbol}: {e}")
            return None
    
    async def close(self):
        """Close the ES client connection"""
        if self.client:
            await self.client.close()


# Global instance
es_data_client = ESDataClient()