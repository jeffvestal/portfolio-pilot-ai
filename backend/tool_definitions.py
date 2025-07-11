
def get_tools():
    return [
        {
            "type": "function",
            "function": {
                "name": "get_high_value_holdings_by_sector",
                "description": "Retrieves a list of high-value financial holdings, filtered by a specific industry sector.",
                "parameters": {
                    "type": "object",
                    "properties": {"sector": {"type": "string", "description": "The sector to search for (e.g., 'Technology')"}},
                    "required": ["sector"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_accounts_by_state",
                "description": "Finds all financial accounts located in a given US state.",
                "parameters": {
                    "type": "object",
                    "properties": {"state": {"type": "string", "description": "The two-letter state code to search for (e.g., 'CA')"}},
                    "required": ["state"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_all_news",
                "description": "Fetches all news articles from Elasticsearch.",
                "parameters": {"type": "object", "properties": {}},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_all_reports",
                "description": "Fetches all financial reports from Elasticsearch.",
                "parameters": {"type": "object", "properties": {}},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_all_accounts",
                "description": "Fetches all financial accounts from Elasticsearch.",
                "parameters": {"type": "object", "properties": {}},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_account_details_by_id",
                "description": "Fetches details for a specific account by its ID.",
                "parameters": {
                    "type": "object",
                    "properties": {"account_id": {"type": "string", "description": "The ID of the account to retrieve."}},
                    "required": ["account_id"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_news_by_asset",
                "description": "Fetches news articles relevant to a specific asset symbol.",
                "parameters": {
                    "type": "object",
                    "properties": {"symbol": {"type": "string", "description": "The asset symbol to find news for (e.g., 'AAPL')"}},
                    "required": ["symbol"],
                },
            },
        },
    ]
