# Portfolio-Pilot-AI

## Project Overview

Portfolio-Pilot-AI is an AI-powered insights dashboard for financial analysts. It allows analysts to proactively monitor client portfolios, explore data conversationally, and streamline communication. The application is built with a React frontend and a Python FastAPI backend, using Elasticsearch as the primary data source and for powering AI search and generation features.

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js and npm
- An Elasticsearch instance with the required indices and an Inference API endpoint configured.

### Backend Setup

1.  **Navigate to the backend directory:**
    ```bash
    cd backend
    ```

2.  **Create a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install the required packages:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up your environment variables:**
    Create a `.env` file in the `backend` directory and add the following:
    ```
    ES_ENDPOINT_URL="<your_elasticsearch_endpoint>"
    ES_API_KEY="<your_elasticsearch_api_key>"
    INFERENCE_ID="<your_inference_id>" # Optional, defaults to .rainbow-sprinkles-elastic
    ```

5.  **Run the backend server:**
    ```bash
    uvicorn main:app --reload
    ```
    The backend will be available at `http://localhost:8000`.

### Frontend Setup

1.  **Navigate to the frontend directory:**
    ```bash
    cd frontend
    ```

2.  **Install the required packages:**
    ```bash
    npm install
    ```

3.  **Run the frontend development server:**
    ```bash
    npm start
    ```
    The frontend will be available at `http://localhost:3000`.

## Features

- **Overview Dashboard:** Get a high-level view of all client portfolios, including total assets under management and key market events.
- **Proactive Alerts:** Receive AI-generated alerts about news and reports that could impact specific client portfolios.
- **Account Drill-down:** Dive deep into individual accounts to see detailed holdings and relevant news.
- **Conversational AI Chat:** Ask natural language questions about your data and get immediate answers.
- **Dynamic Email Drafting:** Generate client-facing emails summarizing portfolio impacts with a single click.
- **Settings Management:** Configure and manage connections to multiple MCP (Managed Component Platform) servers and toggle individual tools on or off.

## MCP Server and Tool Management

The application can connect to multiple MCP servers to extend its toolset. By default, it uses its own internal tools, but you can register external servers that adhere to a simple discovery protocol.

### Registering a New MCP Server

1.  Navigate to the **Settings** page by clicking the gear icon in the header.
2.  In the "Register New Server" section, enter the base URL of the external MCP server (e.g., `http://localhost:8001`).
3.  Click "Add Server".

The application will attempt to connect to the server and discover its available tools by making a `GET` request to the `/tools` endpoint on that server.

### External MCP Server Protocol

An external MCP server must expose a `/tools` endpoint that returns a JSON object with the following structure:

```json
{
  "server_name": "My Custom Financial Tools",
  "tools": [
    {
      "name": "get_stock_beta",
      "description": "Calculates the beta of a given stock symbol.",
      "parameters": {
        "symbol": "string"
      }
    },
    {
      "name": "get_analyst_ratings",
      "description": "Retrieves analyst ratings for a stock.",
      "parameters": {
        "symbol": "string"
      }
    }
  ]
}
```

### Enabling/Disabling Servers and Tools

On the Settings page, you can:
- Use the main toggle next to a server's name to enable or disable all of its tools at once.
- Use the individual toggles next to each tool name to control specific tools.

Disabled tools will not be used by the conversational AI.
