"""
Clean HTTP-based MCP client implementation following the standard MCP protocol.
Based on the mcp-remote package approach and MCP specification.
"""

import json
import logging
import asyncio
import uuid
from typing import Dict, List, Any, Optional, AsyncGenerator
from dataclasses import dataclass, asdict
from enum import Enum
import httpx
import time

logger = logging.getLogger(__name__)


class MCPTransportType(Enum):
    HTTP = "http"
    SSE = "sse"
    HTTP_FIRST = "http-first"
    SSE_FIRST = "sse-first"


@dataclass
class MCPTool:
    """Represents an MCP tool with its metadata"""
    name: str
    description: str
    parameters: Dict[str, Any]
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MCPServer:
    """Represents an MCP server configuration"""
    id: str
    name: str
    url: str
    api_key: Optional[str] = None
    transport: MCPTransportType = MCPTransportType.HTTP_FIRST
    enabled: bool = True
    tools: Dict[str, MCPTool] = None
    last_connected: Optional[float] = None
    connection_status: str = "unknown"  # unknown, connected, error, disconnected
    # Conversation persistence settings
    conversation_field: Optional[str] = None  # Field name for conversation ID (e.g., "runId")
    conversation_location: str = "response"   # Where to find/send conversation ID: "response" or "params"
    # Main page data settings
    use_for_main_page: bool = False          # Whether to use this server for main page data enhancement
    
    def __post_init__(self):
        if self.tools is None:
            self.tools = {}
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        # Convert tools to dict format
        result['tools'] = {name: tool.to_dict() for name, tool in self.tools.items()}
        # Convert enum to string for JSON serialization
        result['transport'] = self.transport.value if isinstance(self.transport, MCPTransportType) else self.transport
        return result


class MCPClientError(Exception):
    """Base exception for MCP client errors"""
    pass


class MCPConnectionError(MCPClientError):
    """Raised when connection to MCP server fails"""
    pass


class MCPToolExecutionError(MCPClientError):
    """Raised when tool execution fails"""
    pass


class MCPClient:
    """
    HTTP-based MCP client following the standard MCP protocol.
    Supports JSON-RPC 2.0 over HTTP with proper error handling and logging.
    """
    
    def __init__(self, server: MCPServer, timeout: int = 30):
        self.server = server
        self.timeout = timeout
        self.session_id = str(uuid.uuid4())
        self.http_client = None
        self.logger = logging.getLogger(f"mcp_client.{server.id}")
        
        # Configure extensive logging
        self.logger.setLevel(logging.DEBUG)
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()
        
    async def connect(self) -> None:
        """Establish connection to the MCP server"""
        try:
            self.logger.info(f"Connecting to MCP server: {self.server.url}")
            
            # Create HTTP client with proper headers
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "Portfolio-Pilot-AI/1.0"
            }
            
            if self.server.api_key:
                headers["Authorization"] = f"ApiKey {self.server.api_key}"
                self.logger.debug(f"Added API key authentication for server {self.server.id}")
            
            self.http_client = httpx.AsyncClient(
                headers=headers,
                timeout=self.timeout,
                follow_redirects=True
            )
            
            # Test connection with initialize request
            await self._initialize_session()
            
            self.server.connection_status = "connected"
            self.server.last_connected = time.time()
            self.logger.info(f"Successfully connected to MCP server: {self.server.name}")
            
        except Exception as e:
            self.server.connection_status = "error"
            self.logger.error(f"Failed to connect to MCP server {self.server.id}: {e}")
            raise MCPConnectionError(f"Failed to connect to {self.server.url}: {e}")
    
    async def disconnect(self) -> None:
        """Close connection to the MCP server"""
        if self.http_client:
            await self.http_client.aclose()
            self.http_client = None
            self.server.connection_status = "disconnected"
            self.logger.info(f"Disconnected from MCP server: {self.server.name}")
    
    async def _initialize_session(self) -> None:
        """Initialize the MCP session"""
        self.logger.debug(f"Initializing MCP session for server {self.server.id}")
        
        # Send initialize request following MCP protocol
        response = await self._send_jsonrpc_request(
            method="initialize",
            params={
                "clientInfo": {
                    "name": "Portfolio-Pilot-AI",
                    "version": "1.0.0"
                },
                "protocolVersion": "2025-06-18",
                "capabilities": {
                    "tools": {},
                    "logging": {}
                }
            }
        )
        
        self.logger.debug(f"Initialize response: {response}")
        
        # Send initialized notification
        await self._send_jsonrpc_notification(
            method="initialized",
            params={}
        )
        
        self.logger.info(f"MCP session initialized for server {self.server.id}")
    
    async def discover_tools(self) -> Dict[str, MCPTool]:
        """Discover available tools from the MCP server"""
        try:
            self.logger.info(f"Discovering tools for server {self.server.id}")
            
            response = await self._send_jsonrpc_request(
                method="tools/list",
                params={}
            )
            
            tools = {}
            if "tools" in response:
                for tool_data in response["tools"]:
                    tool = MCPTool(
                        name=tool_data["name"],
                        description=tool_data.get("description", ""),
                        parameters=tool_data.get("inputSchema", {}),
                        enabled=True  # Enable newly discovered tools by default
                    )
                    tools[tool.name] = tool
                    
            self.server.tools = tools
            self.logger.info(f"Discovered {len(tools)} tools for server {self.server.id}: {list(tools.keys())}")
            
            return tools
            
        except Exception as e:
            self.logger.error(f"Failed to discover tools for server {self.server.id}: {e}")
            raise MCPClientError(f"Tool discovery failed: {e}")
    
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute a tool with streaming response"""
        try:
            self.logger.info(f"Executing tool '{tool_name}' with arguments: {arguments}")
            
            # Validate tool exists
            if tool_name not in self.server.tools:
                raise MCPToolExecutionError(f"Tool '{tool_name}' not found in server {self.server.id}")
            
            # Send tool execution request
            response = await self._send_jsonrpc_request(
                method="tools/call",
                params={
                    "name": tool_name,
                    "arguments": arguments
                }
            )
            
            # Enhanced logging for ES MCP response analysis
            self.logger.info(f"=== FULL ES MCP RESPONSE FOR {tool_name} ===")
            self.logger.info(f"Response type: {type(response)}")
            self.logger.info(f"Response keys: {list(response.keys()) if isinstance(response, dict) else 'Not a dict'}")
            self.logger.info(f"Full response: {json.dumps(response, indent=2, default=str)}")
            
            # Check for conversation-related fields
            if isinstance(response, dict):
                for key in response.keys():
                    if 'conversation' in key.lower() or 'session' in key.lower() or 'context' in key.lower():
                        self.logger.info(f"*** FOUND CONVERSATION-RELATED FIELD: {key} = {response[key]} ***")
            
            self.logger.info("=== END ES MCP RESPONSE ===")
            
            # Handle streaming response
            if "content" in response:
                for i, content_item in enumerate(response["content"]):
                    self.logger.info(f"Content item {i}: {type(content_item)} = {content_item}")
                    yield {
                        "type": "tool_result",
                        "content": content_item,
                        "tool_name": tool_name,
                        "raw_response": response  # Include raw response for conversation ID extraction
                    }
            else:
                yield {
                    "type": "tool_result",
                    "content": response,
                    "tool_name": tool_name,
                    "raw_response": response
                }
                
            self.logger.info(f"Successfully executed tool '{tool_name}' on server {self.server.id}")
            
        except Exception as e:
            self.logger.error(f"Failed to execute tool '{tool_name}' on server {self.server.id}: {e}")
            yield {
                "type": "error",
                "error": str(e),
                "tool_name": tool_name
            }
    
    async def _send_jsonrpc_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send a JSON-RPC request to the MCP server"""
        request_id = str(uuid.uuid4())
        
        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params
        }
        
        self.logger.debug(f"Sending JSON-RPC request: {json.dumps(payload, indent=2)}")
        
        try:
            response = await self.http_client.post(
                self.server.url,
                json=payload
            )
            
            self.logger.debug(f"HTTP response status: {response.status_code}")
            self.logger.debug(f"HTTP response headers: {dict(response.headers)}")
            
            response.raise_for_status()
            
            response_data = response.json()
            
            # Enhanced logging for ES MCP analysis
            self.logger.info(f"=== RAW JSON-RPC RESPONSE FROM ES MCP ===")
            self.logger.info(f"Full response: {json.dumps(response_data, indent=2, default=str)}")
            
            # Look for conversation/session/context fields at all levels
            def scan_for_conversation_fields(obj, path=""):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        current_path = f"{path}.{key}" if path else key
                        if any(keyword in key.lower() for keyword in ['conversation', 'session', 'context', 'id']):
                            self.logger.info(f"*** POTENTIAL CONVERSATION FIELD: {current_path} = {value} ***")
                        scan_for_conversation_fields(value, current_path)
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        scan_for_conversation_fields(item, f"{path}[{i}]")
            
            scan_for_conversation_fields(response_data)
            self.logger.info("=== END RAW JSON-RPC RESPONSE ===")
            
            if "error" in response_data:
                error_msg = response_data["error"]["message"]
                self.logger.error(f"JSON-RPC error: {error_msg}")
                raise MCPClientError(f"Server error: {error_msg}")
            
            return response_data.get("result", {})
            
        except httpx.HTTPStatusError as e:
            self.logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            raise MCPConnectionError(f"HTTP error {e.response.status_code}: {e.response.text}")
        except httpx.RequestError as e:
            self.logger.error(f"Request error: {e}")
            raise MCPConnectionError(f"Request failed: {e}")
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error: {e}")
            raise MCPClientError(f"Invalid JSON response: {e}")
    
    async def _send_jsonrpc_notification(self, method: str, params: Dict[str, Any]) -> None:
        """Send a JSON-RPC notification (no response expected)"""
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params
        }
        
        self.logger.debug(f"Sending JSON-RPC notification: {json.dumps(payload, indent=2)}")
        
        try:
            response = await self.http_client.post(
                self.server.url,
                json=payload
            )
            
            self.logger.debug(f"Notification response status: {response.status_code}")
            response.raise_for_status()
            
        except httpx.HTTPStatusError as e:
            self.logger.warning(f"Notification HTTP error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            self.logger.warning(f"Notification request error: {e}")
    
    async def health_check(self) -> bool:
        """Check if the server is healthy"""
        try:
            # Try to ping the server with a simple request
            await self._send_jsonrpc_request(
                method="ping",
                params={}
            )
            return True
        except Exception as e:
            self.logger.warning(f"Health check failed for server {self.server.id}: {e}")
            return False


class MCPClientManager:
    """
    Manages multiple MCP clients with connection pooling and error handling.
    """
    
    def __init__(self):
        self.clients: Dict[str, MCPClient] = {}
        self.servers: Dict[str, MCPServer] = {}
        self.logger = logging.getLogger("mcp_client_manager")
        
    async def add_server(self, server: MCPServer) -> None:
        """Add a new MCP server"""
        self.logger.info(f"Adding MCP server: {server.id} ({server.name})")
        
        # Create client for the server
        client = MCPClient(server)
        
        try:
            # Test connection and discover tools
            async with client:
                await client.discover_tools()
                
            self.servers[server.id] = server
            self.clients[server.id] = client
            
            self.logger.info(f"Successfully added MCP server: {server.id}")
            
        except Exception as e:
            self.logger.error(f"Failed to add MCP server {server.id}: {e}")
            raise
    
    async def remove_server(self, server_id: str) -> None:
        """Remove an MCP server"""
        if server_id in self.clients:
            client = self.clients[server_id]
            await client.disconnect()
            del self.clients[server_id]
            
        if server_id in self.servers:
            del self.servers[server_id]
            
        self.logger.info(f"Removed MCP server: {server_id}")
    
    async def execute_tool(self, server_id: str, tool_name: str, arguments: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute a tool on a specific server"""
        if server_id not in self.clients:
            raise MCPClientError(f"Server {server_id} not found")
            
        client = self.clients[server_id]
        
        # Ensure connection is active
        if client.server.connection_status != "connected":
            await client.connect()
            
        async for result in client.execute_tool(tool_name, arguments):
            yield result
    
    async def get_all_tools(self) -> Dict[str, List[MCPTool]]:
        """Get all tools from all enabled servers"""
        all_tools = {}
        
        for server_id, server in self.servers.items():
            if server.enabled:
                all_tools[server_id] = list(server.tools.values())
                
        return all_tools
    
    async def health_check_all(self) -> Dict[str, bool]:
        """Check health of all servers"""
        results = {}
        
        for server_id, client in self.clients.items():
            results[server_id] = await client.health_check()
            
        return results
    
    def get_server_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all servers"""
        return {
            server_id: {
                "name": server.name,
                "enabled": server.enabled,
                "connection_status": server.connection_status,
                "last_connected": server.last_connected,
                "tool_count": len(server.tools)
            }
            for server_id, server in self.servers.items()
        }


# Global client manager instance
mcp_manager = MCPClientManager()