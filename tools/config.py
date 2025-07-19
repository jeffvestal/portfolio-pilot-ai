"""
Shared configuration constants for Portfolio-Pilot-AI data generation scripts.

This module centralizes all configuration settings used across the data generation tools.
Update settings here to affect all scripts that use them.

Usage:
    from config import ES_CONFIG, GEMINI_CONFIG, FILE_PATHS, GENERATION_SETTINGS
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Elasticsearch Configuration ---
ES_CONFIG = {
    'endpoint_url': os.getenv("ES_ENDPOINT_URL", "https://localhost:9200"),
    'api_key': os.getenv("ES_API_KEY"),
    'bulk_batch_size': 100,
    'request_timeout': 60,
    'verify_certs': False,
    
    # Index names
    'indices': {
        'accounts': "financial_accounts",
        'holdings': "financial_holdings", 
        'asset_details': "financial_asset_details",
        'news': "financial_news",
        'reports': "financial_reports"
    }
}

# --- Gemini API Configuration ---
GEMINI_CONFIG = {
    'api_key': os.getenv("GEMINI_API_KEY"),
    'model_name': 'gemini-2.5-pro',
    'request_delay_seconds': 0.5,
    'max_retries': 3,
    'response_mime_type': "application/json",
    'safety_settings': {
        'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE',
        'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE',
        'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_NONE',
        'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE',
    }
}

# --- File Paths Configuration ---
FILE_PATHS = {
    # Generated data files
    'generated_accounts': "generated_accounts.jsonl",
    'generated_holdings': "generated_holdings.jsonl", 
    'generated_asset_details': "generated_asset_details.jsonl",
    'generated_news': "generated_news.jsonl",
    'generated_reports': "generated_reports.jsonl",
    'generated_controlled_news': "generated_controlled_news.jsonl",
    'generated_controlled_reports': "generated_controlled_reports.jsonl",
    
    # Prompt template files
    'prompts': {
        'general_news': "general_market_news.txt",
        'specific_news': "specific_news.txt", 
        'specific_report': "specific_report.txt",
        'thematic_report': "thematic_sector_report.txt",
    }
}

# --- Data Generation Settings ---
GENERATION_SETTINGS = {
    # Account and holdings generation
    'accounts': {
        'num_accounts': 7000,
        'min_holdings_per_account': 10,
        'max_holdings_per_account': 25
    },
    
    # News generation (main script)
    'news': {
        'num_specific_per_asset': 1,
        'num_general_articles': 500,
        'num_specific_assets_for_news': 50
    },
    
    # Reports generation (main script)
    'reports': {
        'num_specific_per_asset': 1,
        'num_thematic_reports': 100,
        'num_specific_assets_for_reports': 20
    },
    
    # Controlled generation (trigger script)
    'controlled': {
        'num_specific_news': 5,
        'num_general_news': 4,
        'num_specific_reports': 2,
        'num_thematic_reports': 1
    }
}

# --- Account Generation Constants ---
ACCOUNT_SETTINGS = {
    'types': ['Growth', 'Conservative', 'Income-Focused', 'Balanced', 'Aggressive Growth', 'Retirement'],
    'risk_profiles': ['High', 'Medium', 'Low', 'Very Low'],
    'contact_preferences': ['email', 'app_notification', 'none'],
    'us_states': [
        "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
        "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
        "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
        "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
        "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
    ]
}

# --- Content Generation Constants ---
CONTENT_SETTINGS = {
    'sentiment_options': ["positive", "negative", "neutral", "mixed"],
    
    'news_event_themes': [
        "strong earnings", "new product launch", "regulatory challenge", "economic slowdown",
        "acquisition rumor", "patent dispute", "CEO change", "supply chain disruption",
        "dividend increase", "stock split announcement", "cybersecurity breach", "environmental lawsuit"
    ],
    
    'general_market_events': [
        "inflation data release", "central bank interest rate decision", "global supply chain disruption",
        "energy prices fluctuation", "consumer spending trends", "employment report surprising figures",
        "geopolitical tensions impacting trade", "housing market slowdown", "manufacturing PMI growth"
    ],
    
    'report_types': [
        "Q1 Earnings Summary", "Q2 Earnings Summary", "Q3 Earnings Summary", "Q4 Earnings Summary",
        "Annual Analyst Report", "Regulatory Filing Update", "Sustainability Report Summary"
    ],
    
    'report_focus_themes': [
        "revenue growth", "new product pipeline", "compliance challenges", "market share shifts",
        "sustainability efforts", "cost-cutting measures", "research & development breakthroughs",
        "debt restructuring", "merger and acquisition impact", "divestiture plans"
    ],
    
    'theme_industries': [
        "impact of AI on enterprise software", "future of renewable energy investment",
        "global supply chain resilience", "consumer spending habits in inflationary environment",
        "rise of fintech innovation", "challenges in global semiconductor production",
        "evolution of healthcare technology", "urban development and real estate trends",
        "future of remote work and its economic impact"
    ]
}

# --- Bad Event Configuration (for trigger script) ---
BAD_EVENT_CONFIG = {
    'target_news_symbol': 'TSLA',
    'news_theme': "major recall impacting new vehicle launches and brand reputation",
    'target_report_symbol': 'FCX',
    'report_focus': "unexpected production shortfall due to severe weather disrupting mining operations", 
    'sentiment': "negative"
}

# --- Common Field Names ---
FIELD_NAMES = {
    'primary_symbol': "primary_symbol",
    'company_symbol': "company_symbol"
}

# --- Price Generation Settings ---
PRICE_SETTINGS = {
    'stock_price_range': (20, 1500),
    'etf_price_range': (50, 600), 
    'bond_price_range': (85, 115),  # Bonds typically around 100 (par)
    'price_fluctuation_range': (0.98, 1.02)  # Small daily fluctuation
}

# --- Holdings Generation Settings ---
HOLDINGS_SETTINGS = {
    'stock_quantity_range': (5, 200),
    'etf_quantity_range': (1, 50),
    'bond_face_values': [1000, 5000, 10000, 25000, 50000],
    'high_value_threshold': 75000,  # Threshold for marking holdings as high value
    'purchase_date_range_years': 10,  # How far back purchases can go
    'purchase_date_buffer_days': 30   # No purchases in last N days
}

# --- Validation Functions ---
def validate_config():
    """
    Validate that required configuration values are set.
    
    Returns:
        tuple: (bool, list) - (is_valid, list_of_errors)
    """
    errors = []
    
    # Check required environment variables
    if not ES_CONFIG['api_key']:
        errors.append("ES_API_KEY environment variable not set")
    
    if not GEMINI_CONFIG['api_key']:
        errors.append("GEMINI_API_KEY environment variable not set")
    
    # Check required directories exist for prompt files
    for prompt_name, prompt_file in FILE_PATHS['prompts'].items():
        if not os.path.exists(prompt_file):
            errors.append(f"Prompt file not found: {prompt_file}")
    
    return len(errors) == 0, errors

def get_elasticsearch_client_config():
    """
    Get Elasticsearch client configuration ready for use.
    
    Returns:
        dict: Configuration for Elasticsearch client
    """
    return {
        'hosts': [ES_CONFIG['endpoint_url']],
        'api_key': ES_CONFIG['api_key'],
        'request_timeout': ES_CONFIG['request_timeout'],
        'verify_certs': ES_CONFIG['verify_certs']
    }

def get_gemini_generation_config():
    """
    Get Gemini generation configuration ready for use.
    
    Returns:
        dict: Configuration for Gemini generation
    """
    return {
        'response_mime_type': GEMINI_CONFIG['response_mime_type']
    }

# --- Debug and Logging Settings ---
DEBUG_SETTINGS = {
    'log_level': 'INFO',
    'log_format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'show_progress_bars': True,
    'verbose_api_calls': False
}