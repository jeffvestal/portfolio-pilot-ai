"""
JSON-based configuration storage for MCP servers.
Handles persistent storage of server configurations with security considerations.
"""

import json
import os
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import asdict
import time

from mcp_client import MCPServer, MCPTool, MCPTransportType

logger = logging.getLogger(__name__)

CONFIG_FILE = Path(__file__).parent / "mcp_servers.json"


class MCPConfigManager:
    """Manages persistent configuration for MCP servers"""
    
    def __init__(self, config_file: Optional[Path] = None):
        self.config_file = config_file or CONFIG_FILE
        self.logger = logging.getLogger("mcp_config_manager")
        
        # Ensure config directory exists
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize with default local server if config doesn't exist
        if not self.config_file.exists():
            self._create_default_config()
    
    def _create_default_config(self) -> None:
        """Create default configuration with local server"""
        self.logger.info("Creating default MCP configuration")
        
        default_config = {
            "version": "1.0",
            "created_at": time.time(),
            "servers": {
                "local": {
                    "id": "local", 
                    "name": "Portfolio-Pilot-AI (Local)",
                    "url": "http://localhost:8000",
                    "api_key": None,
                    "transport": "http",
                    "enabled": False,  # Disable by default to avoid circular dependency
                    "tools": {
                        "get_high_value_holdings_by_sector": {
                            "name": "get_high_value_holdings_by_sector",
                            "description": "Get high value holdings by sector",
                            "enabled": True,
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "sector": {"type": "string"}
                                },
                                "required": ["sector"]
                            }
                        },
                        "get_accounts_by_state": {
                            "name": "get_accounts_by_state",
                            "description": "Get accounts by state",
                            "enabled": True,
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "state": {"type": "string"}
                                },
                                "required": ["state"]
                            }
                        },
                        "get_all_news": {
                            "name": "get_all_news",
                            "description": "Get all financial news",
                            "enabled": True,
                            "parameters": {
                                "type": "object",
                                "properties": {}
                            }
                        },
                        "get_all_reports": {
                            "name": "get_all_reports",
                            "description": "Get all financial reports",
                            "enabled": True,
                            "parameters": {
                                "type": "object",
                                "properties": {}
                            }
                        },
                        "get_all_accounts": {
                            "name": "get_all_accounts",
                            "description": "Get all accounts",
                            "enabled": True,
                            "parameters": {
                                "type": "object",
                                "properties": {}
                            }
                        },
                        "get_account_details_by_id": {
                            "name": "get_account_details_by_id",
                            "description": "Get account details by ID",
                            "enabled": True,
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "account_id": {"type": "string"}
                                },
                                "required": ["account_id"]
                            }
                        },
                        "get_news_by_asset": {
                            "name": "get_news_by_asset",
                            "description": "Get news by asset symbol",
                            "enabled": True,
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "symbol": {"type": "string"}
                                },
                                "required": ["symbol"]
                            }
                        }
                    },
                    "last_connected": None,
                    "connection_status": "unknown"
                }
            }
        }
        
        self._save_config(default_config)
        self.logger.info("Default MCP configuration created")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                
            self.logger.debug(f"Loaded MCP configuration from {self.config_file}")
            return config
            
        except FileNotFoundError:
            self.logger.warning(f"Config file not found: {self.config_file}")
            self._create_default_config()
            return self._load_config()
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in config file: {e}")
            # Backup corrupted config and create new one
            backup_file = self.config_file.with_suffix('.json.backup')
            self.config_file.rename(backup_file)
            self.logger.info(f"Backed up corrupted config to {backup_file}")
            self._create_default_config()
            return self._load_config()
            
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            raise
    
    def _save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to JSON file"""
        try:
            # Create backup of existing config
            if self.config_file.exists():
                backup_file = self.config_file.with_suffix('.json.backup')
                self.config_file.rename(backup_file)
            
            # Update timestamp
            config["updated_at"] = time.time()
            
            # Save with proper formatting
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2, sort_keys=True)
            
            self.logger.debug(f"Saved MCP configuration to {self.config_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")
            raise
    
    def get_all_servers(self) -> Dict[str, MCPServer]:
        """Get all configured MCP servers"""
        config = self._load_config()
        servers = {}
        
        for server_id, server_data in config.get("servers", {}).items():
            try:
                # Convert tools data to MCPTool objects
                tools = {}
                for tool_name, tool_data in server_data.get("tools", {}).items():
                    tools[tool_name] = MCPTool(
                        name=tool_data["name"],
                        description=tool_data["description"],
                        parameters=tool_data["parameters"],
                        enabled=tool_data.get("enabled", True)
                    )
                
                server = MCPServer(
                    id=server_data["id"],
                    name=server_data["name"],
                    url=server_data["url"],
                    api_key=server_data.get("api_key"),
                    transport=MCPTransportType(server_data.get("transport", "http")),
                    enabled=server_data.get("enabled", True),
                    tools=tools,
                    last_connected=server_data.get("last_connected"),
                    connection_status=server_data.get("connection_status", "unknown"),
                    conversation_field=server_data.get("conversation_field"),
                    conversation_location=server_data.get("conversation_location", "response"),
                    use_for_main_page=server_data.get("use_for_main_page", False)
                )
                
                servers[server_id] = server
                
            except Exception as e:
                self.logger.error(f"Error parsing server config for {server_id}: {e}")
                continue
        
        self.logger.debug(f"Loaded {len(servers)} MCP servers from config")
        return servers
    
    def get_server(self, server_id: str) -> Optional[MCPServer]:
        """Get a specific MCP server by ID"""
        servers = self.get_all_servers()
        return servers.get(server_id)
    
    def add_server(self, server: MCPServer) -> None:
        """Add a new MCP server to configuration"""
        config = self._load_config()
        
        # Convert server to dict format
        server_dict = server.to_dict()
        
        # Add to config
        config["servers"][server.id] = server_dict
        
        # Save config
        self._save_config(config)
        
        self.logger.info(f"Added MCP server to config: {server.id} ({server.name})")
    
    def update_server(self, server: MCPServer) -> None:
        """Update an existing MCP server in configuration"""
        config = self._load_config()
        
        if server.id not in config["servers"]:
            raise ValueError(f"Server {server.id} not found in configuration")
        
        # Convert server to dict format
        server_dict = server.to_dict()
        
        # Update config
        config["servers"][server.id] = server_dict
        
        # Save config
        self._save_config(config)
        
        self.logger.info(f"Updated MCP server in config: {server.id} ({server.name})")
    
    def remove_server(self, server_id: str) -> None:
        """Remove an MCP server from configuration"""
        config = self._load_config()
        
        if server_id not in config["servers"]:
            raise ValueError(f"Server {server_id} not found in configuration")
        
        # Remove from config
        del config["servers"][server_id]
        
        # Save config
        self._save_config(config)
        
        self.logger.info(f"Removed MCP server from config: {server_id}")
    
    def get_enabled_servers(self) -> Dict[str, MCPServer]:
        """Get only enabled MCP servers"""
        all_servers = self.get_all_servers()
        return {sid: server for sid, server in all_servers.items() if server.enabled}
    
    def get_main_page_servers(self) -> Dict[str, MCPServer]:
        """Get enabled MCP servers designated for main page data"""
        enabled_servers = self.get_enabled_servers()
        return {
            server_id: server
            for server_id, server in enabled_servers.items()
            if server.use_for_main_page
        }
    
    def get_server_tools(self, server_id: str) -> Dict[str, MCPTool]:
        """Get tools for a specific server"""
        server = self.get_server(server_id)
        if server:
            return server.tools
        return {}
    
    def get_all_enabled_tools(self) -> Dict[str, Dict[str, MCPTool]]:
        """Get all tools from all enabled servers"""
        enabled_servers = self.get_enabled_servers()
        all_tools = {}
        
        for server_id, server in enabled_servers.items():
            if server.tools:
                all_tools[server_id] = server.tools
        
        return all_tools
    
    def enable_server(self, server_id: str) -> None:
        """Enable a server"""
        server = self.get_server(server_id)
        if server:
            server.enabled = True
            self.update_server(server)
            self.logger.info(f"Enabled MCP server: {server_id}")
    
    def disable_server(self, server_id: str) -> None:
        """Disable a server"""
        server = self.get_server(server_id)
        if server:
            server.enabled = False
            self.update_server(server)
            self.logger.info(f"Disabled MCP server: {server_id}")
    
    def get_safe_config(self) -> Dict[str, Any]:
        """Get configuration without sensitive data (API keys)"""
        config = self._load_config()
        safe_config = config.copy()
        
        # Remove API keys from server configurations
        for server_id in safe_config.get("servers", {}):
            if "api_key" in safe_config["servers"][server_id]:
                safe_config["servers"][server_id]["api_key"] = "***" if safe_config["servers"][server_id]["api_key"] else None
        
        return safe_config
    
    def export_config(self, file_path: Path) -> None:
        """Export configuration to a file"""
        config = self._load_config()
        
        with open(file_path, 'w') as f:
            json.dump(config, f, indent=2, sort_keys=True)
        
        self.logger.info(f"Exported MCP configuration to {file_path}")
    
    def import_config(self, file_path: Path) -> None:
        """Import configuration from a file"""
        with open(file_path, 'r') as f:
            config = json.load(f)
        
        # Validate config structure
        if "servers" not in config:
            raise ValueError("Invalid configuration format: missing 'servers' key")
        
        # Save imported config
        self._save_config(config)
        
        self.logger.info(f"Imported MCP configuration from {file_path}")


# Global config manager instance
config_manager = MCPConfigManager()