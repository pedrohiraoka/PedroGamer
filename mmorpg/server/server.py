"""
MMORPG Server - Main server application.

This module implements a multithreaded TCP server that handles
multiple client connections, manages game state, and validates
all player actions.
"""

import socket
import threading
import json
import logging
import time
import uuid
from typing import Dict, Optional, Any, List, Tuple
from dataclasses import dataclass, asdict
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.protocol import (
    MessageType, Message, create_message, validate_message,
    AuthRequest, AuthResponse, MoveRequest, MoveResponse,
    PositionUpdate, ChatMessage, PlayerInfo
)
from server.world import World


@dataclass
class Client:
    """Represents a connected client."""
    
    client_id: str
    player_id: str
    player_name: str
    socket: socket.socket
    address: Tuple[str, int]
    x: float = 0.0
    y: float = 0.0
    last_heartbeat: float = 0.0
    authenticated: bool = False
    direction_x: float = 0.0
    direction_y: float = 0.0


class MMORPGServer:
    """
    Main MMORPG server class.
    
    Handles client connections, game state management, and message routing.
    
    Attributes:
        host: Server host address.
        port: Server port number.
        max_clients: Maximum number of concurrent clients.
        tick_rate: Server update rate in ticks per second.
    """
    
    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 5000,
        max_clients: int = 10,
        tick_rate: int = 30,
        heartbeat_timeout: float = 10.0,
        heartbeat_interval: float = 2.0,
        movement_speed: float = 5.0
    ):
        """
        Initialize the MMORPG server.
        
        Args:
            host: Server host address. Defaults to "0.0.0.0".
            port: Server port number. Defaults to 5000.
            max_clients: Maximum concurrent clients. Defaults to 10.
            tick_rate: Server tick rate. Defaults to 30.
            heartbeat_timeout: Heartbeat timeout in seconds. Defaults to 10.0.
            heartbeat_interval: Heartbeat interval in seconds. Defaults to 2.0.
            movement_speed: Player movement speed. Defaults to 5.0.
        """
        self.host = host
        self.port = port
        self.max_clients = max_clients
        self.tick_rate = tick_rate
        self.heartbeat_timeout = heartbeat_timeout
        self.heartbeat_interval = heartbeat_interval
        self.movement_speed = movement_speed
        
        self.clients: Dict[str, Client] = {}
        self.clients_lock = threading.Lock()
        
        self.world = World()
        
        self.running = False
        self.server_socket: Optional[socket.socket] = None
        
        self._setup_logging()
        
        logger.info(f"Server initialized: {host}:{port}, max_clients={max_clients}")
    
    def _setup_logging(self) -> None:
        """Configure logging for the server."""
        global logger
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # File handler
        file_handler = logging.FileHandler('logs/server.log')
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    def load_config(self, config_path: str) -> bool:
        """
        Load server configuration from JSON file.
        
        Args:
            config_path: Path to the configuration file.
            
        Returns:
            bool: True if loading succeeded, False otherwise.
        """
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            server_config = config.get('server', {})
            self.host = server_config.get('host', self.host)
            self.port = server_config.get('port', self.port)
            self.max_clients = server_config.get('max_clients', self.max_clients)
            self.tick_rate = server_config.get('tick_rate', self.tick_rate)
            self.heartbeat_timeout = server_config.get(
                'heartbeat_timeout', self.heartbeat_timeout
            )
            self.heartbeat_interval = server_config.get(
                'heartbeat_interval', self.heartbeat_interval
            )
            
            world_config = config.get('world', {})
            map_file = world_config.get('map_file')
            object_file = world_config.get('object_file')
            
            if map_file and object_file:
                if not self.world.load_from_file(map_file, object_file):
                    logger.warning("Failed to load world from files, using generated world")
            
            movement_config = config.get('movement', {})
            self.movement_speed = movement_config.get('speed', self.movement_speed)
            
            logger.info(f"Configuration loaded from {config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return False
    
    def start(self) -> None:
        """Start the server main loop."""
        self.running = True
        
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.server_socket.settimeout(1.0)
            
            logger.info(f"Server started on {self.host}:{self.port}")
            
            # Start heartbeat thread
            heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
            heartbeat_thread.start()
            
            # Main accept loop
            while self.running:
                try:
                    client_socket, address = self.server_socket.accept()
                    
                    with self.clients_lock:
                        if len(self.clients) >= self.max_clients:
                            logger.warning(f"Max clients reached, rejecting {address}")
                            client_socket.close()
                            continue
                    
                    logger.info(f"New connection from {address}")
                    
                    # Start client handler thread
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, address),
                        daemon=True
                    )
                    client_thread.start()
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        logger.error(f"Error accepting connection: {e}")
                        
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            self.stop()
    
    def stop(self) -> None:
        """Stop the server and disconnect all clients."""
        logger.info("Stopping server...")
        self.running = False
        
        with self.clients_lock:
            for client in list(self.clients.values()):
                try:
                    self._send_message(client.socket, create_message(
                        MessageType.SYSTEM_MESSAGE,
                        {'message': 'Server shutting down'}
                    ))
                    client.socket.close()
                except Exception as e:
                    logger.error(f"Error closing client socket: {e}")
            
            self.clients.clear()
        
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception as e:
                logger.error(f"Error closing server socket: {e}")
        
        logger.info("Server stopped")
    
    def _handle_client(
        self,
        client_socket: socket.socket,
        address: Tuple[str, int]
    ) -> None:
        """
        Handle a client connection.
        
        Args:
            client_socket: Client socket.
            address: Client address.
        """
        client_id = str(uuid.uuid4())[:8]
        client = Client(
            client_id=client_id,
            player_id="",
            player_name="",
            socket=client_socket,
            address=address
        )
        
        client.last_heartbeat = time.time()
        
        try:
            client_socket.settimeout(0.1)
            
            while self.running:
                try:
                    data = client_socket.recv(4096)
                    if not data:
                        break
                    
                    client.last_heartbeat = time.time()
                    
                    # Parse and process message
                    try:
                        message_str = data.decode('utf-8')
                        message_data = json.loads(message_str)
                        
                        if not validate_message(message_data):
                            logger.warning(f"Invalid message from {address}")
                            continue
                        
                        message = Message(**message_data)
                        self._process_message(client, message)
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON decode error from {address}: {e}")
                    except Exception as e:
                        logger.error(f"Error processing message from {address}: {e}")
                        
                except socket.timeout:
                    continue
                except Exception as e:
                    logger.error(f"Error receiving from {address}: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Client handler error for {address}: {e}")
        finally:
            self._disconnect_client(client)
    
    def _process_message(self, client: Client, message: Message) -> None:
        """
        Process a received message from a client.
        
        Args:
            client: The client who sent the message.
            message: The received message.
        """
        try:
            msg_type = message.type
            
            if msg_type == MessageType.AUTH_REQUEST.value:
                self._handle_auth_request(client, message.payload)
            elif msg_type == MessageType.MOVE_REQUEST.value:
                self._handle_move_request(client, message.payload)
            elif msg_type == MessageType.CHAT_MESSAGE.value:
                self._handle_chat_message(client, message.payload)
            elif msg_type == MessageType.HEARTBEAT.value:
                self._handle_heartbeat(client)
            else:
                logger.warning(f"Unknown message type: {msg_type}")
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            self._send_error(client, f"Error processing message: {e}")
    
    def _handle_auth_request(self, client: Client, payload: Dict[str, Any]) -> None:
        """
        Handle authentication request.
        
        Args:
            client: The client requesting authentication.
            payload: Authentication request payload.
        """
        try:
            player_name = payload.get('player_name', '').strip()
            
            if not player_name:
                self._send_auth_response(client, False, error_message="Player name required")
                return
            
            if len(player_name) > 20:
                self._send_auth_response(client, False, error_message="Name too long")
                return
            
            # Check for duplicate names
            with self.clients_lock:
                for c in self.clients.values():
                    if c.player_name.lower() == player_name.lower():
                        self._send_auth_response(
                            client, False, error_message="Name already taken"
                        )
                        return
            
            # Generate player ID and spawn position
            player_id = str(uuid.uuid4())[:8]
            spawn_x, spawn_y = self.world.get_spawn_point()
            
            # Update client
            client.player_id = player_id
            client.player_name = player_name
            client.x = spawn_x
            client.y = spawn_y
            client.authenticated = True
            
            # Add to clients
            with self.clients_lock:
                self.clients[player_id] = client
            
            logger.info(f"Player {player_name} ({player_id}) authenticated from {client.address}")
            
            # Send auth response
            self._send_auth_response(client, True, player_id, spawn_x, spawn_y)
            
            # Broadcast player join
            self._broadcast_player_join(client)
            
            # Send current player list
            self._send_player_list(client)
            
        except Exception as e:
            logger.error(f"Auth error: {e}")
            self._send_auth_response(client, False, error_message=str(e))
    
    def _handle_move_request(self, client: Client, payload: Dict[str, Any]) -> None:
        """
        Handle movement request.
        
        Args:
            client: The client requesting movement.
            payload: Movement request payload.
        """
        if not client.authenticated:
            return
        
        try:
            direction_x = float(payload.get('direction_x', 0))
            direction_y = float(payload.get('direction_y', 0))
            timestamp = float(payload.get('timestamp', time.time()))
            
            # Normalize direction
            length = (direction_x ** 2 + direction_y ** 2) ** 0.5
            if length > 0:
                direction_x /= length
                direction_y /= length
            
            # Calculate new position
            delta_time = 1.0 / self.tick_rate
            distance = self.movement_speed * delta_time
            
            new_x = client.x + direction_x * distance
            new_y = client.y + direction_y * distance
            
            # Validate movement
            success, error = self.world.validate_movement(
                client.player_id,
                client.x,
                client.y,
                new_x,
                new_y
            )
            
            if success:
                client.x = new_x
                client.y = new_y
                client.direction_x = direction_x
                client.direction_y = direction_y
                
                # Send move response
                self._send_move_response(client, new_x, new_y, True)
                
                # Broadcast position update
                self._broadcast_position_update(client)
            else:
                self._send_move_response(client, client.x, client.y, False, error)
                
        except Exception as e:
            logger.error(f"Move error: {e}")
            self._send_move_response(client, client.x, client.y, False, str(e))
    
    def _handle_chat_message(self, client: Client, payload: Dict[str, Any]) -> None:
        """
        Handle chat message.
        
        Args:
            client: The client sending the chat message.
            payload: Chat message payload.
        """
        if not client.authenticated:
            return
        
        try:
            message_text = payload.get('message', '').strip()
            
            if not message_text:
                return
            
            if len(message_text) > 200:
                message_text = message_text[:200]
            
            chat_msg = ChatMessage(
                player_id=client.player_id,
                player_name=client.player_name,
                message=message_text,
                timestamp=time.time()
            )
            
            # Broadcast to all clients
            self._broadcast_message(create_message(
                MessageType.CHAT_MESSAGE,
                asdict(chat_msg)
            ))
            
            logger.info(f"Chat [{client.player_name}]: {message_text}")
            
        except Exception as e:
            logger.error(f"Chat error: {e}")
    
    def _handle_heartbeat(self, client: Client) -> None:
        """
        Handle heartbeat message.
        
        Args:
            client: The client sending heartbeat.
        """
        client.last_heartbeat = time.time()
        
        try:
            self._send_message(client.socket, create_message(
                MessageType.HEARTBEAT_ACK,
                {'timestamp': time.time()}
            ))
        except Exception as e:
            logger.error(f"Heartbeat error: {e}")
    
    def _heartbeat_loop(self) -> None:
        """Background thread to check for timed-out clients."""
        while self.running:
            try:
                time.sleep(self.heartbeat_interval)
                
                current_time = time.time()
                timed_out = []
                
                with self.clients_lock:
                    for client_id, client in self.clients.items():
                        if current_time - client.last_heartbeat > self.heartbeat_timeout:
                            timed_out.append(client_id)
                
                for client_id in timed_out:
                    with self.clients_lock:
                        client = self.clients.get(client_id)
                        if client:
                            logger.info(f"Client {client.player_name} timed out")
                            self._disconnect_client(client)
                            
            except Exception as e:
                logger.error(f"Heartbeat loop error: {e}")
    
    def _disconnect_client(self, client: Client) -> None:
        """
        Disconnect a client.
        
        Args:
            client: The client to disconnect.
        """
        try:
            with self.clients_lock:
                if client.player_id in self.clients:
                    del self.clients[client.player_id]
            
            try:
                client.socket.close()
            except Exception:
                pass
            
            if client.authenticated:
                logger.info(f"Player {client.player_name} disconnected")
                self._broadcast_player_leave(client)
                
        except Exception as e:
            logger.error(f"Disconnect error: {e}")
    
    def _broadcast_message(self, message: Message) -> None:
        """
        Broadcast a message to all connected clients.
        
        Args:
            message: The message to broadcast.
        """
        with self.clients_lock:
            for client in list(self.clients.values()):
                try:
                    self._send_message(client.socket, message)
                except Exception as e:
                    logger.error(f"Broadcast error to {client.player_name}: {e}")
    
    def _broadcast_player_join(self, client: Client) -> None:
        """
        Broadcast player join event.
        
        Args:
            client: The joined client.
        """
        player_info = PlayerInfo(
            player_id=client.player_id,
            player_name=client.player_name,
            x=client.x,
            y=client.y
        )
        
        message = create_message(
            MessageType.PLAYER_JOIN,
            asdict(player_info)
        )
        
        # Send to all other clients
        with self.clients_lock:
            for other_client in self.clients.values():
                if other_client.player_id != client.player_id:
                    try:
                        self._send_message(other_client.socket, message)
                    except Exception as e:
                        logger.error(f"Error broadcasting join: {e}")
    
    def _broadcast_player_leave(self, client: Client) -> None:
        """
        Broadcast player leave event.
        
        Args:
            client: The leaving client.
        """
        message = create_message(
            MessageType.PLAYER_LEAVE,
            {'player_id': client.player_id}
        )
        
        self._broadcast_message(message)
    
    def _broadcast_position_update(self, client: Client) -> None:
        """
        Broadcast position update for a player.
        
        Args:
            client: The client whose position updated.
        """
        position = PositionUpdate(
            player_id=client.player_id,
            player_name=client.player_name,
            x=client.x,
            y=client.y,
            direction_x=client.direction_x,
            direction_y=client.direction_y
        )
        
        message = create_message(
            MessageType.POSITION_UPDATE,
            asdict(position)
        )
        
        # Send to all other clients
        with self.clients_lock:
            for other_client in self.clients.values():
                if other_client.player_id != client.player_id:
                    try:
                        self._send_message(other_client.socket, message)
                    except Exception as e:
                        logger.error(f"Error broadcasting position: {e}")
    
    def _send_player_list(self, client: Client) -> None:
        """
        Send list of all players to a client.
        
        Args:
            client: The client to send the list to.
        """
        players = []
        with self.clients_lock:
            for other_client in self.clients.values():
                if other_client.player_id != client.player_id:
                    players.append(asdict(PlayerInfo(
                        player_id=other_client.player_id,
                        player_name=other_client.player_name,
                        x=other_client.x,
                        y=other_client.y
                    )))
        
        self._send_message(client.socket, create_message(
            MessageType.WORLD_STATE,
            {'players': players}
        ))
    
    def _send_auth_response(
        self,
        client: Client,
        success: bool,
        player_id: Optional[str] = None,
        spawn_x: Optional[float] = None,
        spawn_y: Optional[float] = None,
        error_message: Optional[str] = None
    ) -> None:
        """
        Send authentication response.
        
        Args:
            client: The client to respond to.
            success: Whether authentication succeeded.
            player_id: Assigned player ID if successful.
            spawn_x: Spawn X coordinate if successful.
            spawn_y: Spawn Y coordinate if successful.
            error_message: Error message if failed.
        """
        response = AuthResponse(
            success=success,
            player_id=player_id,
            error_message=error_message,
            spawn_x=int(spawn_x) if spawn_x is not None else None,
            spawn_y=int(spawn_y) if spawn_y is not None else None
        )
        
        self._send_message(client.socket, create_message(
            MessageType.AUTH_RESPONSE,
            asdict(response)
        ))
    
    def _send_move_response(
        self,
        client: Client,
        new_x: float,
        new_y: float,
        success: bool,
        error_message: Optional[str] = None
    ) -> None:
        """
        Send movement response.
        
        Args:
            client: The client to respond to.
            new_x: New X position.
            new_y: New Y position.
            success: Whether movement succeeded.
            error_message: Error message if failed.
        """
        response = MoveResponse(
            player_id=client.player_id,
            new_x=new_x,
            new_y=new_y,
            success=success,
            error_message=error_message
        )
        
        self._send_message(client.socket, create_message(
            MessageType.MOVE_RESPONSE,
            asdict(response)
        ))
    
    def _send_error(self, client: Client, error_message: str) -> None:
        """
        Send error message to client.
        
        Args:
            client: The client to send error to.
            error_message: Error message.
        """
        self._send_message(client.socket, create_message(
            MessageType.ERROR,
            {'error': error_message}
        ))
    
    def _send_message(self, sock: socket.socket, message: Message) -> None:
        """
        Send a message to a socket.
        
        Args:
            sock: Socket to send to.
            message: Message to send.
            
        Raises:
            socket.error: If sending fails.
        """
        data = message.to_json().encode('utf-8')
        sock.sendall(data)


def main() -> None:
    """Main entry point for the server."""
    import argparse
    
    parser = argparse.ArgumentParser(description='MMORPG Server')
    parser.add_argument(
        '--config', '-c',
        default='config/server_config.json',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--host', '-H',
        default=None,
        help='Server host'
    )
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=None,
        help='Server port'
    )
    
    args = parser.parse_args()
    
    server = MMORPGServer()
    
    # Load configuration
    if os.path.exists(args.config):
        server.load_config(args.config)
    else:
        logger.warning(f"Config file not found: {args.config}, using defaults")
    
    # Override with command line arguments
    if args.host:
        server.host = args.host
    if args.port:
        server.port = args.port
    
    try:
        server.start()
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    finally:
        server.stop()


if __name__ == '__main__':
    main()
