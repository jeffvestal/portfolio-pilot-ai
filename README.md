# Portfolio-Pilot-AI

## Project Overview

Portfolio-Pilot-AI is an AI-powered financial analyst dashboard that demonstrates cutting-edge integration with Elasticsearch's built-in MCP (Model Context Protocol) server. This application showcases a dual-layer architecture combining traditional financial dashboards with conversational AI capabilities, all powered by real financial data stored in Elasticsearch.

## Key Features

### 🏦 Financial Dashboard
- **Real-time metrics** - Live view of total accounts, AUM, news, and reports with clickable navigation
- **Enhanced content summaries** - AI-powered news and reports summaries via MCP servers
- **2-column responsive layout** - Side-by-side news and reports with expandable previews
- **Interactive content** - "Show More/Less" expandable summaries and full content modals
- **Start Day workflow** - Trigger daily analysis and load enhanced content
- **Dedicated list pages** - Navigate to detailed accounts, news, and reports pages from overview metrics
- **Action Item Analysis** - Intelligent monitoring of top accounts for negative news exposure
- **MCP Tool Notifications** - Visual indicators showing when MCP tools are being executed
- **Optimized search functionality** - Robust filtering across all content types with error handling

### 📊 Advanced Account Management
- **Professional holdings display** - Clean card-based layout for portfolio positions
- **Account drilldowns** - Detailed portfolio holdings with quantity, value, and sector information
- **Personalized news & reports** - Symbol-specific articles and analysis for account holdings
- **AI-powered article summaries** - Context-aware summaries with portfolio impact analysis
- **Back navigation** - Seamless navigation with state preservation

### 🚨 Negative News Monitoring
- **Automated alerts** - Real-time monitoring using `neg_news_reports_with_pos` MCP tool
- **Configurable time periods** - Flexible time range selection (minutes, hours, days)
- **Manual refresh control** - "Check Time Range" button for on-demand updates
- **Grouped alerts** - News stories grouped by title with affected accounts summary
- **Position details** - Detailed holdings information including P&L analysis
- **Severity indicators** - Color-coded alerts based on content analysis

### 🤖 Conversational AI Chat
- **Multi-turn conversations** - Session-based chat with context preservation
- **MCP tool integration** - Dynamic tool discovery and execution via Elasticsearch's MCP server
- **Real-time streaming** - Live responses with tool execution feedback
- **Conversation persistence** - Hybrid approach supporting both server-native and client sessions
- **Collapsible tool results** - Clean accordion-style display for MCP tool execution details
- **Click-outside-to-close** - Intuitive interface behavior with state preservation
- **Resizable chat panel** - Drag-to-resize for optimal screen usage

### 📰 Intelligent Content Analysis
- **Symbol-specific lookup** - News and reports analysis using `news_and_report_lookup_with_symbol_detail` MCP tool
- **Sentiment analysis** - Color-coded sentiment indicators (positive/negative/neutral)
- **Expandable articles** - Click-to-expand full content with professional formatting
- **AI summarization** - Personalized article summaries with account context
- **Real-time streaming summaries** - Live AI analysis with portfolio impact focus

### ⚙️ MCP Server Management
- **Multiple server support** - Connect to various MCP servers beyond Elasticsearch
- **Dynamic configuration** - Add/remove servers via intuitive UI
- **Main page designation** - Select specific servers to enhance dashboard content
- **Tool discovery** - Automatic discovery of available tools from connected servers

## Architecture

This application demonstrates a **hybrid architecture** that leverages both direct Elasticsearch queries and MCP server integration:

- **Dashboard Layer** - Direct ES queries for basic financial metrics + MCP enhancement for content summaries
- **Chat Layer** - Pure MCP integration for conversational AI with Elasticsearch's built-in MCP server
- **Content Enhancement** - Designated MCP servers provide news/reports summaries for the dashboard
- **Alert System** - MCP-powered negative news monitoring with position analysis
- **AI Analysis** - Streaming LLM integration for personalized content summarization

## Synthetic Data Generation Tools

The `tools/` directory contains Python scripts for generating synthetic financial data to populate your Elasticsearch cluster. These tools create realistic test data including accounts, holdings, news articles, and research reports for demonstration purposes.

### 📁 Tools Directory Structure

#### Core Scripts
- **`generate_holdings_accounts.py`** - Creates synthetic financial accounts with portfolio holdings and asset details
- **`generate_reports_and_news.py`** - Generates financial news articles and research reports using AI
- **`trigger_bad_news_event.py`** - Creates controlled negative events for testing alert systems

#### Shared Modules (Consolidated Architecture)
- **`symbols_config.py`** - Central symbol definitions for stocks, ETFs, and bonds
- **`config.py`** - Shared configuration constants and environment settings
- **`common_utils.py`** - Shared utility functions for API calls, ES ingestion, and data processing
- **`symbol_manager.py`** - Advanced symbol management and filtering utilities

#### Templates & Data
- **`*.txt`** - AI prompt templates for content generation
- **`*.jsonl`** - Generated data files ready for Elasticsearch ingestion

### 🔧 Configuration & Setup

**Environment Variables Required:**
```bash
# Elasticsearch Configuration
ES_ENDPOINT_URL=https://localhost:9200
ES_API_KEY=your_elasticsearch_api_key

# Gemini AI Configuration (for content generation)
GEMINI_API_KEY=your_gemini_api_key
```

**Key Configuration Files:**
- **`tools/config.py`** - Centralized settings for all data generation
  - ES indices and connection settings
  - Generation parameters (number of accounts, articles, etc.)
  - File paths and API configurations
  - Content themes and sentiment options

### 📊 Data Generation Workflow

#### 1. Generate Core Financial Data
```bash
cd tools
python generate_holdings_accounts.py
```
**Creates:**
- 7,000 synthetic financial accounts
- 70,000-175,000 portfolio holdings (10-25 per account)
- 100+ unique asset details (stocks, ETFs, bonds)
- Data files: `generated_accounts.jsonl`, `generated_holdings.jsonl`, `generated_asset_details.jsonl`

#### 2. Generate News & Reports
```bash
python generate_reports_and_news.py
```
**Creates:**
- 50+ specific company news articles
- 500+ general market news articles  
- 20+ specific company reports
- 100+ thematic industry reports
- Data files: `generated_news.jsonl`, `generated_reports.jsonl`

#### 3. Trigger Controlled Events (Optional)
```bash
python trigger_bad_news_event.py
```
**Creates controlled negative events for testing:**
- 5 specific news articles (1 negative for TSLA)
- 4 general market articles
- 2 specific reports (1 negative for FCX)
- 1 thematic report
- Data files: `generated_controlled_news.jsonl`, `generated_controlled_reports.jsonl`

### 🎯 Centralized Symbol Management

**Single Source of Truth:** All scripts now share symbol definitions from `symbols_config.py`

**Symbol Categories:**
- **Stocks:** 100+ major US stocks (NASDAQ 100, S&P 500, DJIA)
- **ETFs:** 30+ sector and international ETFs
- **Bonds:** 35+ government and corporate bonds

**Easy Updates:** Change symbols in one file to affect all scripts
```python
# Example: Adding a new stock symbol
STOCK_SYMBOLS_AND_INFO = {
    'NVDA': {'name': 'NVIDIA Corp.', 'sector': 'Technology', 'indices': ['NASDAQ 100', 'S&P 500']},
    # Add your new symbol here
}
```

### 🔄 Data Ingestion Control

Each script includes control flags for selective generation and ingestion:

```python
# Control what gets generated/ingested
DO_GENERATE_DATA = True     # Generate new data files
DO_INGEST_TO_ES = True      # Upload to Elasticsearch
```

### 🛠 Advanced Features

#### Symbol Manager
```python
from symbol_manager import SymbolManager

sm = SymbolManager()
tech_stocks = sm.get_symbols_by_sector('Technology')
random_etfs = sm.get_random_etfs(10)
sp500_symbols = sm.get_symbols_by_index('S&P 500')
```

#### Configurable Data Generation
- **Account settings:** Risk profiles, contact preferences, geographic distribution
- **Content generation:** Sentiment distribution, event themes, market scenarios
- **Technical settings:** Batch sizes, API delays, validation rules

#### Error Handling & Validation
- Environment variable validation
- File existence checks
- JSON validation and error recovery
- Rate limiting for external APIs

### 📈 Generated Data Statistics

**Typical Output:**
- **7,000 accounts** with realistic personal and financial details
- **~120,000 holdings** across diverse asset classes
- **~150 unique assets** with current and historical pricing
- **550+ news articles** with sentiment analysis
- **120+ research reports** across companies and sectors
- **Full Elasticsearch compatibility** with proper indexing

### 🔧 Maintenance & Updates

**Benefits of Consolidated Architecture:**
- ✅ **No code duplication** - Eliminated 2,250+ lines of duplicate code
- ✅ **Easy symbol updates** - Change once, update everywhere
- ✅ **Consistent configuration** - Centralized settings management
- ✅ **Shared utilities** - Common functions for all scripts
- ✅ **Better maintainability** - Bug fixes and improvements apply globally

**Making Changes:**
1. **Add new symbols** → Edit `symbols_config.py`
2. **Adjust generation settings** → Modify `config.py`
3. **Update utility functions** → Enhance `common_utils.py`
4. **Add symbol filtering** → Extend `symbol_manager.py`

All scripts will automatically use your updates without modification.

## Prerequisites

- **Python 3.10+**
- **Node.js 18+ and npm**
- **Elasticsearch cluster** running locally on `localhost:9200` with financial data
- **Elasticsearch's built-in MCP server** (beta feature) running on `localhost:5601/api/mcp`
- **Azure OpenAI** account for GPT-4o access

### Required Elasticsearch Indices

Your Elasticsearch cluster should contain these indices with financial data:
- `financial_accounts` - Client account information and portfolio values
- `financial_holdings` - Individual security positions per account  
- `financial_news` - Financial news articles with sentiment analysis
- `financial_reports` - Research reports and financial analysis documents

### Required MCP Tools

Your MCP server should support these tools:
- `neg_news_reports_with_pos` - For negative news alerts monitoring
- `news_and_report_lookup_with_symbol_detail` - For symbol-specific content analysis

## Getting Started

### 1. Clone the Repository
```bash
git clone <repository-url>
cd portfolio-pilot-ai
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
```

**Configure your `.env` file:**
```env
# Elasticsearch Configuration
ES_ENDPOINT_URL=https://localhost:9200
ES_API_KEY=your_elasticsearch_api_key

# Azure OpenAI Configuration  
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_DEPLOYMENT=gpt-4o

# Optional: MCP Communication Logging
LOG_MCP_COMMUNICATIONS=false
```

```bash
# Start the backend server
uvicorn main:app --reload
```
Backend will be available at `http://localhost:8000`

### 3. Frontend Setup

```bash
# Navigate to frontend directory (from project root)
cd frontend

# Install dependencies
npm install

# Start the development server
npm start
```
Frontend will be available at `http://localhost:3000`

### 4. Configure MCP Servers

1. **Access the Settings page** by clicking the gear icon in the header
2. **Register Elasticsearch's MCP server:**
   - URL: `http://localhost:5601/api/mcp`
   - Enable "Use for main page data" for dashboard content enhancement
3. **Add additional MCP servers** as needed for extended functionality

## Usage Examples

### Dashboard Workflow
1. **View overview metrics** - See total accounts, AUM, news, and reports counts
2. **Navigate to detail pages** - Click metric cards to view accounts, news, or reports lists
3. **Click "Start Day"** - Triggers analysis and loads enhanced content from MCP servers
4. **Explore content summaries** - Expandable news and reports in 2-column layout
5. **Read full content** - Click "Read Full Article/Report" for complete content in modal dialogs
6. **Drill down into accounts** - Click on specific accounts for detailed holdings and relevant news

### Negative News Monitoring
1. **Navigate to "Negative News"** - Click the navigation button to access alerts
2. **Configure time period** - Select from presets or custom time ranges
3. **Click "Check Time Range"** - Manually refresh to see latest alerts
4. **Review grouped alerts** - See news stories with affected accounts summary
5. **Expand account details** - View detailed position information and P&L
6. **Navigate to account details** - Click "View Account Details" for full portfolio analysis

### Enhanced Account Details
1. **Professional holdings view** - Clean card-based layout for easy scanning
2. **Symbol-specific news & reports** - Automatically fetched using account holdings
3. **Sentiment analysis** - Color-coded sentiment indicators for quick assessment
4. **Expandable articles** - Click titles to read full content
5. **AI summarization** - Click "Summarize" for personalized analysis
6. **Portfolio impact analysis** - Context-aware summaries considering account positions

### Chat Interface
1. **Start a conversation** - Ask questions about your financial data
2. **Use natural language** - "Show me accounts with exposure to tech stocks"
3. **Get tool-powered responses** - AI uses MCP tools to query Elasticsearch and provide insights
4. **Continue conversations** - Multi-turn chat with context preservation

### MCP Server Management
1. **Connect additional servers** - Extend functionality with custom MCP servers
2. **Designate content servers** - Select which servers enhance dashboard content
3. **Manage tool availability** - Enable/disable specific tools as needed

## API Endpoints

### Dashboard
- `GET /metrics/overview` - Basic financial metrics
- `GET /metrics/overview?include_news=true&include_reports=true` - Enhanced with MCP content
- `POST /agent/start_day` - Trigger daily analysis workflow
- `GET /accounts` - List all accounts
- `GET /news` - List all news articles
- `GET /reports` - List all reports
- `GET /action-item` - Get action item analysis for top accounts with negative news exposure

### Negative News Alerts
- `GET /alerts/negative-news?time_period=48&time_unit=hours` - Get negative news alerts

### Account Details
- `GET /account/{account_id}` - Account details and holdings
- `GET /account/{account_id}/news-reports?time_period=72&time_unit=hours` - Symbol-specific news and reports

### Content Analysis
- `GET /article/full/{document_id}?index={index}` - Full article/report via MCP
- `POST /article/summarize` - AI-powered article summarization with account context

### Chat
- `POST /chat/query` - Conversational AI with MCP integration

### Configuration
- `GET /settings` - MCP server configuration
- `POST /servers` - Register new MCP servers
- `DELETE /servers/{server_id}` - Remove MCP servers

## Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **Elasticsearch** - Data storage and MCP server integration
- **Azure OpenAI** - GPT-4o for conversational AI and article summarization
- **MCP Protocol** - JSON-RPC 2.0 for tool integration

### Frontend  
- **React** - Modern UI framework
- **Material-UI** - Component library for professional financial interfaces
- **Axios** - HTTP client for API communication
- **React Router** - Navigation with state preservation

## Development Notes

This application demonstrates several advanced concepts:

- **MCP Integration** - First-class integration with Elasticsearch's built-in MCP server
- **Hybrid Architecture** - Combining direct queries with MCP enhancement
- **Conversation Persistence** - Supporting both server-native and client-side sessions
- **Dynamic Tool Discovery** - Runtime discovery and execution of MCP tools
- **Content Enhancement** - Using MCP servers to enrich dashboard content
- **State Preservation** - Seamless navigation with preserved application state
- **Streaming AI Responses** - Real-time LLM integration for dynamic content analysis
- **Context-Aware Analysis** - Personalized summaries based on account holdings

## Troubleshooting

### Common Issues

1. **MCP Server Connection Failed**
   - Verify Elasticsearch cluster is running on `localhost:9200`
   - Ensure MCP server feature is enabled in Elasticsearch (beta feature)
   - Check that MCP server is accessible at `localhost:5601/api/mcp`

2. **No Content in News/Reports Summaries**
   - Verify MCP server is designated for "main page data" in settings
   - Check that financial data exists in your Elasticsearch indices
   - Review backend logs for MCP tool execution errors

3. **Negative News Alerts Not Working**
   - Ensure your MCP server has the `neg_news_reports_with_pos` tool
   - Verify the tool accepts `time_duration` parameter (e.g., "48 hours")
   - Check server connectivity and tool availability in settings

4. **Article Summarization Failing**
   - Verify Azure OpenAI credentials are correct
   - Check that the article content is not empty
   - Review backend logs for streaming response errors

5. **Sentiment Analysis Showing "Unknown"**
   - Verify your Elasticsearch data includes sentiment fields
   - Check that MCP tools return sentiment data in expected format
   - Review backend logs for data parsing errors

6. **Chat Not Working**
   - Verify Azure OpenAI credentials in `.env` file
   - Check that MCP servers are connected and tools are discovered
   - Review conversation logs for authentication or tool execution errors

For additional help, check the backend logs and ensure all services are properly configured and running.