#!/usr/bin/env python3
"""
Entry point for running the MMORPG client.

Usage:
    python -m scripts.run_client [options]
    
Or directly:
    python scripts/run_client.py [options]
"""

import argparse
import logging
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.client import MMORPGClient
from src.utils import load_client_config, ConfigManager


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="MMORPG Client",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--config", "-c",
        type=str,
        default=None,
        help="Path to client configuration file"
    )
    
    parser.add_argument(
        "--host", "-H",
        type=str,
        default=None,
        help="Server host address (default: localhost)"
    )
    
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=None,
        help="Server port (default: 5000)"
    )
    
    parser.add_argument(
        "--width", "-W",
        type=int,
        default=None,
        help="Window width (default: 640)"
    )
    
    parser.add_argument(
        "--height", "-T",
        type=int,
        default=None,
        help="Window height (default: 480)"
    )
    
    parser.add_argument(
        "--fps",
        type=int,
        default=None,
        help="Target FPS (default: 60)"
    )
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()
    
    # Load configuration
    config_manager = ConfigManager()
    
    if args.config:
        config = config_manager.load_client_config(args.config)
    else:
        config = config_manager.load_client_config()
    
    # Override config with command line arguments
    if args.host:
        config.server_host = args.host
    if args.port:
        config.server_port = args.port
    if args.width:
        config.window_width = args.width
    if args.height:
        config.window_height = args.height
    if args.fps:
        config.fps = args.fps
    
    # Setup logging
    os.makedirs(os.path.dirname(config.log_file), exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, config.log_level),
        format=config.log_format,
        handlers=[
            logging.FileHandler(config.log_file),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting MMORPG Client...")
    logger.info(f"Connecting to {config.server_host}:{config.server_port}")
    logger.info(f"Window size: {config.window_width}x{config.window_height}")
    logger.info(f"Target FPS: {config.fps}")
    
    # Create and run client
    client = MMORPGClient(
        window_width=config.window_width,
        window_height=config.window_height,
        fps=config.fps,
        server_host=config.server_host,
        server_port=config.server_port,
    )
    
    try:
        if client.initialize():
            client.run()
        else:
            logger.error("Failed to initialize client")
            return 1
    except KeyboardInterrupt:
        logger.info("Client shutting down...")
    finally:
        client.shutdown()
        logger.info("Client stopped")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
