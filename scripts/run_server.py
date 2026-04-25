#!/usr/bin/env python3
"""
Entry point for running the MMORPG server.

Usage:
    python -m scripts.run_server [options]
    
Or directly:
    python scripts/run_server.py [options]
"""

import argparse
import logging
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.server import MMORPGServer
from src.utils import load_server_config, ConfigManager


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="MMORPG Server",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--config", "-c",
        type=str,
        default=None,
        help="Path to server configuration file"
    )
    
    parser.add_argument(
        "--host", "-H",
        type=str,
        default=None,
        help="Server host address (default: 0.0.0.0)"
    )
    
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=None,
        help="Server port (default: 5000)"
    )
    
    parser.add_argument(
        "--max-clients",
        type=int,
        default=None,
        help="Maximum number of clients (default: 10)"
    )
    
    parser.add_argument(
        "--tick-rate",
        type=int,
        default=None,
        help="Server tick rate (default: 30)"
    )
    
    parser.add_argument(
        "--map-file",
        type=str,
        default=None,
        help="Path to world map file"
    )
    
    parser.add_argument(
        "--object-file",
        type=str,
        default=None,
        help="Path to world objects file"
    )
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()
    
    # Load configuration
    config_manager = ConfigManager()
    
    if args.config:
        config = config_manager.load_server_config(args.config)
    else:
        config = config_manager.load_server_config()
    
    # Override config with command line arguments
    if args.host:
        config.host = args.host
    if args.port:
        config.port = args.port
    if args.max_clients:
        config.max_clients = args.max_clients
    if args.tick_rate:
        config.tick_rate = args.tick_rate
    if args.map_file:
        config.map_file = args.map_file
    if args.object_file:
        config.object_file = args.object_file
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, config.log_level),
        format=config.log_format,
        handlers=[
            logging.FileHandler(config.log_file),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting MMORPG Server...")
    logger.info(f"Host: {config.host}:{config.port}")
    logger.info(f"Max clients: {config.max_clients}")
    logger.info(f"Tick rate: {config.tick_rate}")
    
    # Create and start server
    server = MMORPGServer(
        host=config.host,
        port=config.port,
        max_clients=config.max_clients,
        tick_rate=config.tick_rate,
        heartbeat_timeout=config.heartbeat_timeout,
        heartbeat_interval=config.heartbeat_interval,
        movement_speed=config.movement_speed,
    )
    
    # Load world from files if specified
    if os.path.exists(config.map_file) and os.path.exists(config.object_file):
        logger.info(f"Loading world from {config.map_file} and {config.object_file}")
        server.world.load_from_file(config.map_file, config.object_file)
    
    try:
        server.start()
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
    finally:
        server.stop()
        logger.info("Server stopped")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
