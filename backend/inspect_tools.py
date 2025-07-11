"""
Inspect MCP tools and their required parameters to help with debugging.
"""

import asyncio
import logging
import os
import json
from mcp_client import MCPServer, MCPClient, MCPTransportType

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration from environment variables
ES_ENDPOINT = os.getenv("ES_ENDPOINT", "http://localhost:5601/api/mcp")
ES_API_KEY = os.getenv("ES_API_KEY", "")

async def inspect_tools():
    """Inspect MCP tools and show their parameter requirements"""
    
    if not ES_API_KEY:
        logger.warning("ES_API_KEY environment variable not set. Please set it to inspect Elasticsearch MCP tools.")
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
    
    logger.info(f"Inspecting MCP tools from: {server.name} at {server.url}")
    
    try:
        # Connect and discover tools
        async with MCPClient(server) as client:
            tools = await client.discover_tools()
            
            print("\n" + "="*80)
            print(f"DISCOVERED {len(tools)} TOOLS FROM ELASTICSEARCH MCP SERVER")
            print("="*80)
            
            for i, (tool_name, tool) in enumerate(tools.items(), 1):
                print(f"\n{i}. {tool_name}")
                print(f"   Description: {tool.description}")
                print(f"   Parameters: {json.dumps(tool.parameters, indent=6)}")
                
                # Try to suggest example usage based on parameters
                if tool.parameters and "properties" in tool.parameters:
                    properties = tool.parameters["properties"]
                    required = tool.parameters.get("required", [])
                    
                    print(f"   Required params: {required}")
                    
                    # Create example arguments
                    example_args = {}
                    for param_name, param_info in properties.items():
                        param_type = param_info.get("type", "string")
                        if param_type == "string":
                            if "index" in param_name.lower():
                                example_args[param_name] = "your-index-name"
                            elif "id" in param_name.lower():
                                example_args[param_name] = "document-id"
                            elif "query" in param_name.lower():
                                example_args[param_name] = "search term"
                            else:
                                example_args[param_name] = f"example_{param_name}"
                        elif param_type == "integer":
                            example_args[param_name] = 10
                        elif param_type == "boolean":
                            example_args[param_name] = True
                        else:
                            example_args[param_name] = f"example_{param_name}"
                    
                    if example_args:
                        print(f"   Example args: {json.dumps(example_args, indent=6)}")
                
                print("-" * 40)
            
            print(f"\n{'='*80}")
            print("TOOL INSPECTION COMPLETE")
            print("="*80)
            
    except Exception as e:
        logger.error(f"Error inspecting tools: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(inspect_tools())