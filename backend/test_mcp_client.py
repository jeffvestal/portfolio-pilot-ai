"""
Test the new MCP client implementation with proper environment variables.
"""

import asyncio
import logging
import os
from mcp_client import MCPServer, MCPClient, MCPTransportType

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Configuration from environment variables
ES_ENDPOINT = os.getenv("ES_ENDPOINT", "http://localhost:5601/api/mcp")
ES_API_KEY = os.getenv("ES_API_KEY", "")

async def test_mcp_client():
    """Test the new MCP client implementation"""
    
    if not ES_API_KEY:
        logger.warning("ES_API_KEY environment variable not set. Please set it to test with Elasticsearch MCP server.")
        return
    
    # Create server configuration
    server = MCPServer(
        id="elasticsearch",
        name="Elasticsearch MCP Server",
        url=ES_ENDPOINT,
        api_key=ES_API_KEY,
        transport=MCPTransportType.HTTP,
        enabled=True
    )
    
    logger.info(f"Testing MCP client with server: {server.name} at {server.url}")
    
    try:
        # Test connection and tool discovery
        async with MCPClient(server) as client:
            logger.info("Connected to MCP server successfully")
            
            # Discover tools
            tools = await client.discover_tools()
            logger.info(f"Discovered {len(tools)} tools:")
            for tool_name, tool in tools.items():
                logger.info(f"  - {tool_name}: {tool.description}")
            
            # Test a tool call (if tools are available)
            if tools:
                # Find a tool that doesn't require parameters or use a safe one
                test_cases = [
                    # Try tools that might not require parameters first
                    ("list_indices", {}),
                    ("get_cluster_info", {}),
                    ("list_aliases", {}),
                    # If those don't exist, try with safe parameters
                    ("search_documents", {"query": "test", "index": "_all", "size": 1}),
                    ("get_document_by_id", {"id": "test", "index": "test-index"}),
                ]
                
                tested = False
                for tool_name, test_args in test_cases:
                    if tool_name in tools:
                        logger.info(f"Testing tool call: {tool_name} with args: {test_args}")
                        
                        async for result in client.execute_tool(tool_name, test_args):
                            if result["type"] == "error":
                                logger.info(f"Tool result (expected errors are OK): {result}")
                            else:
                                logger.info(f"Tool result: {result}")
                            break  # Just test the first result
                        
                        tested = True
                        break
                
                if not tested:
                    # If none of our preferred tools exist, just test the first one with empty args
                    # This will likely fail with validation error, but that's OK for testing
                    tool_name = list(tools.keys())[0]
                    logger.info(f"Testing tool call: {tool_name} with empty args (validation error expected)")
                    
                    async for result in client.execute_tool(tool_name, {}):
                        logger.info(f"Tool result (validation error expected): {result}")
                        break
                
            logger.info("MCP client test completed successfully")
            
    except Exception as e:
        logger.error(f"MCP client test failed: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_mcp_client())