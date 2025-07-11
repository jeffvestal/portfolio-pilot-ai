# Portfolio-Pilot-AI

## Project Overview

Portfolio-Pilot-AI is an AI-powered financial analyst dashboard that demonstrates cutting-edge integration with Elasticsearch's built-in MCP (Model Context Protocol) server. This application showcases a dual-layer architecture combining traditional financial dashboards with conversational AI capabilities, all powered by real financial data stored in Elasticsearch.

## Key Features

### 🏦 Financial Dashboard
- **Real-time metrics** - Live view of total accounts, AUM, news, and reports
- **Enhanced content summaries** - AI-powered news and reports summaries via MCP servers
- **2-column responsive layout** - Side-by-side news and reports with expandable previews
- **Interactive content** - "Show More/Less" expandable summaries and full content modals
- **Start Day workflow** - Trigger daily analysis and load enhanced content
- **Account drilldowns** - Detailed portfolio holdings and relevant news per client

### 🤖 Conversational AI Chat
- **Multi-turn conversations** - Session-based chat with context preservation
- **MCP tool integration** - Dynamic tool discovery and execution via Elasticsearch's MCP server
- **Real-time streaming** - Live responses with tool execution feedback
- **Conversation persistence** - Hybrid approach supporting both server-native and client sessions

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
2. **Click "Start Day"** - Triggers analysis and loads enhanced content from MCP servers
3. **Explore content summaries** - Expandable news and reports in 2-column layout
4. **Read full content** - Click "Read Full Article/Report" for complete content in modal dialogs
5. **Drill down into accounts** - Click on specific accounts for detailed holdings and relevant news

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

### Content  
- `GET /article/full/{document_id}?index={index}` - Full article/report via MCP
- `GET /account/{account_id}` - Account details and holdings

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
- **Azure OpenAI** - GPT-4o for conversational AI
- **MCP Protocol** - JSON-RPC 2.0 for tool integration

### Frontend  
- **React** - Modern UI framework
- **Material-UI** - Component library for professional financial interfaces
- **Axios** - HTTP client for API communication

## Development Notes

This application demonstrates several advanced concepts:

- **MCP Integration** - First-class integration with Elasticsearch's built-in MCP server
- **Hybrid Architecture** - Combining direct queries with MCP enhancement
- **Conversation Persistence** - Supporting both server-native and client-side sessions
- **Dynamic Tool Discovery** - Runtime discovery and execution of MCP tools
- **Content Enhancement** - Using MCP servers to enrich dashboard content

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

3. **Chat Not Working**
   - Verify Azure OpenAI credentials in `.env` file
   - Check that MCP servers are connected and tools are discovered
   - Review conversation logs for authentication or tool execution errors

For additional help, check the backend logs and ensure all services are properly configured and running.