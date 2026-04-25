"""
Configuration management for MMORPG.

This module provides configuration loading and validation for both
server and client components.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


logger = logging.getLogger(__name__)


@dataclass
class ServerConfig:
    """Server configuration settings."""
    
    host: str = "0.0.0.0"
    port: int = 5000
    tick_rate: int = 30
    max_clients: int = 10
    heartbeat_timeout: float = 10.0
    heartbeat_interval: float = 2.0
    movement_speed: float = 5.0
    
    # World settings
    world_width: int = 500
    world_height: int = 500
    tile_size: int = 40
    map_file: str = "resources/world_map.json"
    object_file: str = "resources/world_objects.json"
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/server.log"
    log_format: str = "%(asctime)s - %(levelname)s - %(message)s"


@dataclass
class ClientConfig:
    """Client configuration settings."""
    
    window_width: int = 640
    window_height: int = 480
    fps: int = 60
    tile_size: int = 40
    server_host: str = "localhost"
    server_port: int = 5000
    reconnect_delay: float = 3.0
    prediction_enabled: bool = True
    
    # Resources
    sprites_folder: str = "resources/sprites"
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/client.log"
    log_format: str = "%(asctime)s - %(levelname)s - %(message)s"


class ConfigManager:
    """
    Manages configuration loading and access.
    
    Supports loading from JSON files and provides type-safe access
    to configuration values.
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_dir: Directory containing configuration files.
                       Defaults to 'config' in the current directory.
        """
        if config_dir is None:
            config_dir = "config"
        
        self.config_dir = Path(config_dir)
        self.server_config: Optional[ServerConfig] = None
        self.client_config: Optional[ClientConfig] = None
    
    def load_server_config(self, filepath: Optional[str] = None) -> ServerConfig:
        """
        Load server configuration from file.
        
        Args:
            filepath: Path to server config file. If None, uses default location.
        
        Returns:
            ServerConfig: Loaded server configuration.
        """
        if filepath is None:
            filepath = self.config_dir / "server_config.json"
        else:
            filepath = Path(filepath)
        
        if not filepath.exists():
            logger.warning(f"Server config file not found: {filepath}")
            logger.info("Using default server configuration")
            self.server_config = ServerConfig()
            return self.server_config
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            server_data = data.get('server', {})
            world_data = data.get('world', {})
            movement_data = data.get('movement', {})
            logging_data = data.get('logging', {})
            
            self.server_config = ServerConfig(
                host=server_data.get('host', ServerConfig.host),
                port=server_data.get('port', ServerConfig.port),
                tick_rate=server_data.get('tick_rate', ServerConfig.tick_rate),
                max_clients=server_data.get('max_clients', ServerConfig.max_clients),
                heartbeat_timeout=server_data.get('heartbeat_timeout', ServerConfig.heartbeat_timeout),
                heartbeat_interval=server_data.get('heartbeat_interval', ServerConfig.heartbeat_interval),
                
                movement_speed=movement_data.get('speed', ServerConfig.movement_speed),
                
                world_width=world_data.get('width', ServerConfig.world_width),
                world_height=world_data.get('height', ServerConfig.world_height),
                tile_size=world_data.get('tile_size', ServerConfig.tile_size),
                map_file=world_data.get('map_file', ServerConfig.map_file),
                object_file=world_data.get('object_file', ServerConfig.object_file),
                
                log_level=logging_data.get('level', ServerConfig.log_level),
                log_file=logging_data.get('file', ServerConfig.log_file),
                log_format=logging_data.get('format', ServerConfig.log_format),
            )
            
            logger.info(f"Server configuration loaded from {filepath}")
            return self.server_config
            
        except Exception as e:
            logger.error(f"Error loading server config: {e}")
            logger.info("Using default server configuration")
            self.server_config = ServerConfig()
            return self.server_config
    
    def load_client_config(self, filepath: Optional[str] = None) -> ClientConfig:
        """
        Load client configuration from file.
        
        Args:
            filepath: Path to client config file. If None, uses default location.
        
        Returns:
            ClientConfig: Loaded client configuration.
        """
        if filepath is None:
            filepath = self.config_dir / "client_config.json"
        else:
            filepath = Path(filepath)
        
        if not filepath.exists():
            logger.warning(f"Client config file not found: {filepath}")
            logger.info("Using default client configuration")
            self.client_config = ClientConfig()
            return self.client_config
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            client_data = data.get('client', {})
            resources_data = data.get('resources', {})
            logging_data = data.get('logging', {})
            
            self.client_config = ClientConfig(
                window_width=client_data.get('window_width', ClientConfig.window_width),
                window_height=client_data.get('window_height', ClientConfig.window_height),
                fps=client_data.get('fps', ClientConfig.fps),
                tile_size=client_data.get('tile_size', ClientConfig.tile_size),
                server_host=client_data.get('server_host', ClientConfig.server_host),
                server_port=client_data.get('server_port', ClientConfig.server_port),
                reconnect_delay=client_data.get('reconnect_delay', ClientConfig.reconnect_delay),
                prediction_enabled=client_data.get('prediction_enabled', ClientConfig.prediction_enabled),
                
                sprites_folder=resources_data.get('sprites_folder', ClientConfig.sprites_folder),
                
                log_level=logging_data.get('level', ClientConfig.log_level),
                log_file=logging_data.get('file', ClientConfig.log_file),
                log_format=logging_data.get('format', ClientConfig.log_format),
            )
            
            logger.info(f"Client configuration loaded from {filepath}")
            return self.client_config
            
        except Exception as e:
            logger.error(f"Error loading client config: {e}")
            logger.info("Using default client configuration")
            self.client_config = ClientConfig()
            return self.client_config
    
    def get_server_config(self) -> ServerConfig:
        """
        Get server configuration, loading if necessary.
        
        Returns:
            ServerConfig: Server configuration.
        """
        if self.server_config is None:
            return self.load_server_config()
        return self.server_config
    
    def get_client_config(self) -> ClientConfig:
        """
        Get client configuration, loading if necessary.
        
        Returns:
            ClientConfig: Client configuration.
        """
        if self.client_config is None:
            return self.load_client_config()
        return self.client_config


def load_server_config(filepath: Optional[str] = None) -> ServerConfig:
    """
    Convenience function to load server configuration.
    
    Args:
        filepath: Path to server config file.
    
    Returns:
        ServerConfig: Loaded server configuration.
    """
    manager = ConfigManager()
    return manager.load_server_config(filepath)


def load_client_config(filepath: Optional[str] = None) -> ClientConfig:
    """
    Convenience function to load client configuration.
    
    Args:
        filepath: Path to client config file.
    
    Returns:
        ClientConfig: Loaded client configuration.
    """
    manager = ConfigManager()
    return manager.load_client_config(filepath)
