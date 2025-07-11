import os
import logging
import json
import asyncio
from typing import List, Dict, Any, Optional
import httpx

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from otel_config import setup_telemetry
from eis_client import get_chat_response_stream, get_chat_response_stream_with_messages
from mcp_client import mcp_manager, MCPServer, MCPTransportType, MCPClientError, MCPConnectionError, MCPToolExecutionError
from mcp_config import config_manager
from conversation_manager import conversation_manager
from es_data_client import es_data_client
from main_page_data_service import main_page_data_service

# Simple logging status management
LOG_MCP_COMMUNICATIONS = os.getenv("LOG_MCP_COMMUNICATIONS", "false").lower() == "true"

def get_logging_status():
    """Returns the current MCP logging status."""
    return {"enabled": LOG_MCP_COMMUNICATIONS}

def update_logging_status(status: bool):
    """Updates the MCP logging status."""
    global LOG_MCP_COMMUNICATIONS
    LOG_MCP_COMMUNICATIONS = status
    return {"enabled": LOG_MCP_COMMUNICATIONS}

load_dotenv()

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("main_logger")

app = FastAPI(
    title="Portfolio-Pilot-AI",
    description="An AI-powered insights dashboard for financial analysts.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- In-memory store ---
impact_summary_global = "No analysis performed yet."

def get_all_tool_definitions() -> List[Dict[str, Any]]:
    """Gathers all enabled tool definitions from MCP servers."""
    all_defs = []
    
    # Get all enabled MCP servers and their tools
    enabled_servers = config_manager.get_enabled_servers()
    
    for server_id, server in enabled_servers.items():
        logger.debug(f"Processing tools for server {server_id}: {server.name}")
        
        for tool_name, tool in server.tools.items():
            logger.debug(f"Adding MCP tool: {tool_name} from server {server_id}")
            all_defs.append({
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                }
            })
    
    logger.info(f"Collected {len(all_defs)} tool definitions from {len(enabled_servers)} MCP servers")
    return all_defs


@app.on_event("startup")
async def startup_event():
    """Initialize MCP servers on startup"""
    logger.info("Starting Portfolio-Pilot-AI with MCP client manager")
    
    try:
        # Load all configured servers
        all_servers = config_manager.get_all_servers()
        logger.info(f"Found {len(all_servers)} configured MCP servers")
        
        # Initialize enabled servers in the manager
        for server_id, server in all_servers.items():
            if server.enabled:
                try:
                    logger.info(f"Initializing MCP server: {server_id} ({server.name})")
                    await mcp_manager.add_server(server)
                    logger.info(f"Successfully initialized server: {server_id}")
                except Exception as e:
                    logger.error(f"Failed to initialize server {server_id}: {e}")
                    # Mark server as error status in config
                    server.connection_status = "error"
                    config_manager.update_server(server)
            else:
                logger.debug(f"Skipping disabled server: {server_id}")
        
        logger.info("MCP client manager initialization complete")
        
    except Exception as e:
        logger.error(f"Error during MCP startup: {e}", exc_info=True)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup connections on shutdown"""
    logger.info("Shutting down application")
    
    try:
        # Disconnect all MCP clients
        for server_id in list(mcp_manager.clients.keys()):
            await mcp_manager.remove_server(server_id)
        
        # Close ES data client
        await es_data_client.close()
        
        logger.info("Application shutdown complete")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}", exc_info=True)


# --- API endpoints ---
@app.get("/metrics/overview")
async def get_metrics_overview(include_news: bool = False, include_reports: bool = False):
    """Get overview metrics for the financial dashboard"""
    try:
        # Get base metrics from ES
        metrics = await es_data_client.get_metrics_overview()
        metrics["impact_summary"] = impact_summary_global
        
        # Only include news summary if requested (e.g., after "Start Day" is clicked)
        if include_news:
            news_summary = await main_page_data_service.get_news_summary()
            metrics["news_summary"] = news_summary
        else:
            metrics["news_summary"] = None
        
        # Only include reports summary if requested
        if include_reports:
            reports_summary = await main_page_data_service.get_reports_summary()
            metrics["reports_summary"] = reports_summary
        else:
            metrics["reports_summary"] = None
        
        return metrics
    except Exception as e:
        logger.error(f"Error fetching metrics overview: {e}")
        return {
            "total_accounts": 0,
            "total_aum": 0,
            "total_news": 0,
            "total_reports": 0,
            "impact_summary": impact_summary_global,
            "news_summary": {
                "status": "error",
                "message": "Error loading news summary",
                "news_stories": []
            } if include_news else None,
            "reports_summary": {
                "status": "error",
                "message": "Error loading reports summary", 
                "reports": []
            } if include_reports else None
        }

@app.get("/account/{account_id}")
async def get_account_details(account_id: str):
    """Get detailed account information for the drilldown page"""
    try:
        account_data = await es_data_client.get_account_details(account_id)
        if account_data:
            return account_data
        else:
            raise HTTPException(status_code=404, detail="Account not found")
    except Exception as e:
        logger.error(f"Error fetching account {account_id}: {e}")
        raise HTTPException(status_code=500, detail="Error fetching account data")

@app.post("/agent/start_day")
async def start_day():
    """Trigger the daily analysis workflow"""
    try:
        global impact_summary_global
        # This could trigger a more sophisticated analysis workflow
        impact_summary_global = "Daily analysis completed - market conditions favorable, no significant alerts."
        logger.info("Daily analysis workflow triggered")
        return {"status": "success", "message": "Daily analysis completed"}
    except Exception as e:
        logger.error(f"Error starting day: {e}")
        raise HTTPException(status_code=500, detail="Error starting daily analysis")

@app.post("/email/draft")
async def draft_email(request: Dict[str, str]):
    """Draft an email for client communication"""
    try:
        account_id = request.get("account_id")
        article_id = request.get("article_id")
        
        # Get account info
        account_data = await es_data_client.get_account_details(account_id)
        if not account_data:
            raise HTTPException(status_code=404, detail="Account not found")
        
        # Generate a simple email draft
        subject = f"Market Update for {account_data['account_name']}"
        body = f"""Dear {account_data['account_name']},

I hope this message finds you well. I wanted to reach out with a brief update on your portfolio and some relevant market developments.

Your current portfolio value stands at ${account_data['total_portfolio_value']:,.2f}, and I've been monitoring several factors that may impact your holdings.

Recent market developments include news related to your current positions. I recommend we schedule a brief call to discuss these developments and any potential adjustments to your investment strategy.

Please let me know your availability for a 15-minute call this week.

Best regards,
Your Financial Advisor"""

        return {"subject": subject, "body": body}
        
    except Exception as e:
        logger.error(f"Error drafting email: {e}")
        raise HTTPException(status_code=500, detail="Error drafting email")

@app.get("/article/{article_id}")
async def get_article_content(article_id: str):
    """Get news article content"""
    try:
        content = await es_data_client.get_article_content(article_id)
        if content:
            return {"content": content}
        else:
            raise HTTPException(status_code=404, detail="Article not found")
    except Exception as e:
        logger.error(f"Error fetching article {article_id}: {e}")
        raise HTTPException(status_code=500, detail="Error fetching article")

@app.get("/report/{report_id}")
async def get_report_content(report_id: str):
    """Get financial report content"""
    try:
        content = await es_data_client.get_report_content(report_id)
        if content:
            return {"content": content}
        else:
            raise HTTPException(status_code=404, detail="Report not found")
    except Exception as e:
        logger.error(f"Error fetching report {report_id}: {e}")
        raise HTTPException(status_code=500, detail="Error fetching report")

@app.get("/article/full/{document_id}")
async def get_full_article(document_id: str, index: str = "financial_news"):
    """Get full article/report content from ES using MCP server"""
    try:
        # Get the MCP server configured for main page data
        main_page_servers = config_manager.get_main_page_servers()
        
        if not main_page_servers:
            raise HTTPException(status_code=503, detail="No MCP servers configured for article retrieval")
        
        # Use the first available server that supports main page data
        server_id = list(main_page_servers.keys())[0]
        server = main_page_servers[server_id]
        
        # Check if the server has the get_document_by_id tool
        if "get_document_by_id" not in server.tools:
            raise HTTPException(status_code=503, detail="MCP server does not support document retrieval")
        
        # Determine content type based on index
        content_type = "report" if index == "financial_reports" else "article"
        logger.info(f"Fetching full {content_type} {document_id} from index {index} using server {server_id}")
        
        # Execute the get_document_by_id tool
        arguments = {
            "id": document_id,
            "index": index
        }
        
        async for result in mcp_manager.execute_tool(server_id, "get_document_by_id", arguments):
            if result["type"] == "tool_result":
                content = result["content"]
                if isinstance(content, dict) and "text" in content:
                    try:
                        data = json.loads(content["text"])
                        logger.info(f"Retrieved full {content_type} data: {json.dumps(data, indent=2)}")
                        
                        # Extract the content from ES response
                        if "result" in data and "_source" in data["result"]:
                            source = data["result"]["_source"]
                            
                            # Set appropriate default title based on content type
                            default_title = "Financial Report" if content_type == "report" else "Financial Article"
                            
                            return {
                                "title": source.get("title", default_title),
                                "content": source.get("content", source.get("summary", "Content not available")),
                                "published_date": source.get("published_date", ""),
                                "symbol": source.get("symbol", ""),
                                "source": source.get("source", ""),
                                "url": source.get("url", ""),
                                "document_id": document_id,
                                "index": index,
                                "content_type": content_type
                            }
                        else:
                            logger.warning(f"Unexpected response format for document {document_id}")
                            raise HTTPException(status_code=404, detail=f"{content_type.title()} not found")
                            
                    except json.JSONDecodeError as e:
                        logger.error(f"Could not parse {content_type} response: {e}")
                        raise HTTPException(status_code=500, detail=f"Error parsing {content_type} data")
            elif result["type"] == "error":
                logger.error(f"Error retrieving {content_type} {document_id}: {result.get('error', 'Unknown error')}")
                raise HTTPException(status_code=404, detail=f"{content_type.title()} not found")
        
        # If we get here, no valid result was returned
        raise HTTPException(status_code=404, detail=f"{content_type.title()} not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching full article {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Error fetching article")

async def chat_stream_generator(prompt: str, session_id: Optional[str] = None):
    """
    Multi-turn conversation generator with hybrid conversation persistence.
    """
    print(f"--- USER PROMPT ---: {prompt}")
    
    # Handle conversation session
    if session_id:
        # Continue existing conversation
        messages = conversation_manager.get_messages(session_id)
        if not messages:
            # Session not found, create new one
            session_id = conversation_manager.create_session(prompt)
            messages = [{"role": "user", "content": prompt}]
        else:
            # Add new user message to existing conversation
            conversation_manager.add_message(session_id, {"role": "user", "content": prompt})
            messages.append({"role": "user", "content": prompt})
    else:
        # Create new conversation session
        session_id = conversation_manager.create_session(prompt)
        messages = [{"role": "user", "content": prompt}]
    
    yield f"Session ID: {session_id}\n\n"
    
    dynamic_tools = get_all_tool_definitions()
    max_turns = 5  # Prevent infinite loops
    turn = 0
    
    while turn < max_turns:
        turn += 1
        print(f"--- TURN {turn} ---")
        
        tool_calls = {}  # Use dict to accumulate by index
        assistant_response = ""

        # Make LLM call with current conversation history
        async for data in get_chat_response_stream_with_messages(messages, dynamic_tools=dynamic_tools):
            if data.get("error"):
                yield f"Error: {data['error']}"
                return

            # Safe access to choices array
            choices = data.get("choices", [])
            if not choices:
                continue
                
            delta = choices[0].get("delta", {})
            
            # Accumulate tool calls properly
            if "tool_calls" in delta and delta["tool_calls"]:
                for tool_call in delta["tool_calls"]:
                    index = tool_call.get("index", 0)
                    if index not in tool_calls:
                        tool_calls[index] = {"name": "", "arguments": ""}
                    
                    function_data = tool_call.get("function", {})
                    if "name" in function_data:
                        tool_calls[index]["name"] = function_data["name"]
                    if "arguments" in function_data:
                        tool_calls[index]["arguments"] += function_data["arguments"]
            
            content = delta.get("content")
            if content:
                assistant_response += content
                yield content
        
        print(f"--- ASSISTANT RESPONSE TURN {turn} ---: {assistant_response}")

        # If no tool calls, we have the final answer
        if not tool_calls:
            print(f"--- FINAL ANSWER REACHED IN {turn} TURNS ---")
            break
        
        # Execute tools and build tool results for next turn
        tool_results = []
        enabled_servers = config_manager.get_enabled_servers()
        
        # Add assistant message with tool calls to conversation
        assistant_message = {"role": "assistant", "content": assistant_response}
        if tool_calls:
            assistant_message["tool_calls"] = [
                {
                    "id": f"call_{i}",
                    "type": "function", 
                    "function": {"name": tc["name"], "arguments": tc["arguments"]}
                }
                for i, tc in tool_calls.items()
            ]
        messages.append(assistant_message)
        conversation_manager.add_message(session_id, assistant_message)

        for i, tool_call in tool_calls.items():
            function_name = tool_call.get("name")
            
            # Skip tool calls with no function name
            if not function_name:
                logger.warning(f"Skipping tool call with no function name: {tool_call}")
                continue
            
            # Handle empty or invalid arguments safely
            args_str = tool_call.get("arguments", "{}")
            if not args_str.strip():
                args_str = "{}"
            
            try:
                function_args = json.loads(args_str)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse tool arguments '{args_str}': {e}")
                function_args = {}
            
            logger.info(f"Executing tool call: {function_name}({function_args})")
            
            result = None
            
            # Check MCP servers for the tool
            tool_found = False
            for server_id, server in enabled_servers.items():
                if function_name in server.tools:
                    logger.debug(f"Executing MCP tool {function_name} on server {server_id}")
                    tool_found = True
                    
                    try:
                        # Prepare arguments with conversation context
                        enhanced_args = conversation_manager.prepare_tool_arguments(
                            session_id, server_id, server.to_dict(), function_args
                        )
                        
                        # Use the MCP client with streaming support
                        async for tool_result in mcp_manager.execute_tool(server_id, function_name, enhanced_args):
                            if tool_result["type"] == "error":
                                result = f"Error calling MCP tool {function_name}: {tool_result['error']}"
                                logger.error(f"MCP tool error: {tool_result['error']}")
                            else:
                                result = tool_result["content"]
                                logger.info(f"MCP tool {function_name} executed successfully on server {server_id}")
                                
                                # Extract and store conversation ID if server supports it
                                raw_response = tool_result.get("raw_response", {})
                                conversation_id = conversation_manager.extract_conversation_id(
                                    server_id, server.to_dict(), raw_response
                                )
                                if conversation_id:
                                    conversation_manager.store_server_conversation_id(
                                        session_id, server_id, conversation_id
                                    )
                            break  # Take first result for now
                    except Exception as e:
                        logger.error(f"Error executing MCP tool {function_name} on server {server_id}: {e}")
                        result = f"Error calling MCP tool {function_name}: {e}"
                    break
            
            if not tool_found:
                logger.warning(f"Tool {function_name} not found in any enabled MCP server")
                result = f"Tool {function_name} not found in any enabled MCP server"
            
            if result is not None:
                logger.debug(f"Tool result for {function_name}: {result}")
                tool_results.append({"tool_name": function_name, "result": result})
                
                # Add tool result to conversation history
                tool_message = {
                    "role": "tool",
                    "tool_call_id": f"call_{i}",
                    "content": str(result)
                }
                messages.append(tool_message)
                conversation_manager.add_message(session_id, tool_message)

        # Show tool results to user
        if tool_results:
            yield f"\n\n--- Tool Results (Turn {turn}) ---\n"
            for tr in tool_results:
                yield f"**{tr['tool_name']}**: {tr['result']}\n"
            yield "\n"

@app.post("/chat/query")
async def chat_query(query: Dict[str, str]):
    prompt = query.get("query", "")
    session_id = query.get("session_id")  # Optional session ID for conversation persistence
    return StreamingResponse(chat_stream_generator(prompt, session_id), media_type="text/plain")

# --- Settings Endpoints ---

@app.get("/settings")
async def get_current_settings():
    """Get current MCP server settings (without API keys)"""
    safe_config = config_manager.get_safe_config()
    # Return just the servers part to match frontend expectations
    return safe_config.get("servers", {})

@app.post("/settings")
async def update_current_settings(new_settings: Dict[str, Any]):
    """Update MCP server settings"""
    try:
        # This endpoint could be used for bulk updates
        # For now, we'll return the current settings
        logger.info("Settings update requested (not implemented for bulk updates)")
        return config_manager.get_safe_config()
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        raise HTTPException(status_code=400, detail=f"Error updating settings: {e}")

@app.get("/settings/logging")
async def get_logging_config():
    return get_logging_status()

@app.put("/settings/logging")
async def update_logging_config(status: Dict[str, bool]):
    return update_logging_status(status.get("enabled", False))

@app.post("/servers")
async def register_external_server(server_config: Dict[str, Any]):
    """Registers a new external MCP server using the clean HTTP-based client."""
    server_id = server_config.get("id")
    if not server_id:
        raise HTTPException(status_code=400, detail="Server ID is required.")
    
    url = server_config.get("url")
    api_key = server_config.get("apiKey")
    name = server_config.get("name", "Unnamed Server")
    transport = server_config.get("transport", "http")
    conversation_field = server_config.get("conversationField")
    conversation_location = server_config.get("conversationLocation", "response")
    use_for_main_page = server_config.get("useForMainPage", False)
    
    logger.info(f"Registering new MCP server: {server_id} at {url}")
    if conversation_field:
        logger.info(f"Server supports conversation persistence: {conversation_field} in {conversation_location}")
    if use_for_main_page:
        logger.info(f"Server designated for main page data enhancement")
    
    try:
        # Create MCPServer instance
        server = MCPServer(
            id=server_id,
            name=name,
            url=url,
            api_key=api_key,
            transport=MCPTransportType(transport),
            enabled=True,
            conversation_field=conversation_field,
            conversation_location=conversation_location,
            use_for_main_page=use_for_main_page
        )
        
        # Add server to manager (this will test connection and discover tools)
        await mcp_manager.add_server(server)
        
        # Save to persistent configuration
        config_manager.add_server(server)
        
        logger.info(f"Successfully registered MCP server: {server_id} with {len(server.tools)} tools")
        
        # Return server config without API key
        result = server.to_dict()
        result.pop("api_key", None)
        return result
        
    except MCPConnectionError as e:
        logger.error(f"Connection error registering server {server_id}: {e}")
        raise HTTPException(status_code=400, detail=f"Connection error: {e}")
    except MCPClientError as e:
        logger.error(f"Client error registering server {server_id}: {e}")
        raise HTTPException(status_code=400, detail=f"Client error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error registering server {server_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

@app.delete("/servers/{server_id}")
async def unregister_external_server(server_id: str):
    try:
        # Remove from MCP manager
        await mcp_manager.remove_server(server_id)
        # Remove from config
        config_manager.remove_server(server_id)
        return {"message": f"Server {server_id} removed successfully."}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error removing server: {e}")

@app.get("/tools")
async def get_available_tools():
    """Get all available tools from MCP servers"""
    tools = []
    enabled_servers = config_manager.get_enabled_servers()
    
    for server_id, server in enabled_servers.items():
        for tool_name, tool in server.tools.items():
            tools.append({
                "name": tool_name,
                "description": tool.description,
                "server": server.name,
                "server_id": server_id
            })
    
    return {
        "server_name": "MCP Servers",
        "tools": tools
    }