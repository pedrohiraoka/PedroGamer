#!/usr/bin/env python3
"""
MMORPG Client - Pygame-based client application.

This module implements a 2D MMORPG client with tile-based rendering,
camera system, movement prediction, and network communication.
"""

import pygame
import socket
import threading
import json
import logging
import time
import os
import sys
from typing import Dict, Optional, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@dataclass
class Player:
    """Represents a player in the game world."""
    
    player_id: str
    player_name: str
    x: float
    y: float
    direction_x: float = 0.0
    direction_y: float = 0.0
    color: Tuple[int, int, int] = (0, 255, 0)


@dataclass
class WorldObject:
    """Represents an object in the world."""
    
    object_id: str
    x: int
    y: int
    object_type: str


class GameEvent(Enum):
    """Custom game events."""
    
    AUTH_SUCCESS = pygame.USEREVENT + 1
    AUTH_FAILURE = pygame.USEREVENT + 2
    POSITION_UPDATE = pygame.USEREVENT + 3
    PLAYER_JOIN = pygame.USEREVENT + 4
    PLAYER_LEAVE = pygame.USEREVENT + 5
    CHAT_MESSAGE = pygame.USEREVENT + 6
    SYSTEM_MESSAGE = pygame.USEREVENT + 7
    DISCONNECTED = pygame.USEREVENT + 8


class Camera:
    """
    Camera system that follows the player.
    
    Attributes:
        x: Camera X position.
        y: Camera Y position.
        width: Camera viewport width.
        height: Camera viewport height.
    """
    
    def __init__(self, width: int, height: int):
        """
        Initialize the camera.
        
        Args:
            width: Viewport width in pixels.
            height: Viewport height in pixels.
        """
        self.x = 0.0
        self.y = 0.0
        self.width = width
        self.height = height
        self.target_x = 0.0
        self.target_y = 0.0
    
    def update(self, target_x: float, target_y: float, delta_time: float) -> None:
        """
        Update camera position to follow target.
        
        Args:
            target_x: Target X position to follow.
            target_y: Target Y position to follow.
            delta_time: Time since last update.
        """
        self.target_x = target_x
        self.target_y = target_y
        
        # Smooth camera movement
        lerp_factor = 5.0 * delta_time
        self.x += (target_x - self.x) * lerp_factor
        self.y += (target_y - self.y) * lerp_factor
    
    def apply(self, x: float, y: float) -> Tuple[int, int]:
        """
        Apply camera transform to world coordinates.
        
        Args:
            x: World X coordinate.
            y: World Y coordinate.
            
        Returns:
            Tuple[int, int]: Screen coordinates.
        """
        screen_x = int((x - self.x) * 40 + self.width / 2)
        screen_y = int((y - self.y) * 40 + self.height / 2)
        return (screen_x, screen_y)
    
    def is_visible(self, x: float, y: float, margin: float = 1.0) -> bool:
        """
        Check if a world position is visible in the camera.
        
        Args:
            x: World X coordinate.
            y: World Y coordinate.
            margin: Visibility margin in tiles.
            
        Returns:
            bool: True if visible, False otherwise.
        """
        tile_margin_x = margin + self.width / 80
        tile_margin_y = margin + self.height / 80
        
        return (
            self.x - tile_margin_x <= x <= self.x + tile_margin_x and
            self.y - tile_margin_y <= y <= self.y + tile_margin_y
        )


class NetworkClient:
    """
    Network client for server communication.
    
    Handles all network operations in a separate thread.
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 5000,
        event_queue: Optional[Any] = None
    ):
        """
        Initialize the network client.
        
        Args:
            host: Server host. Defaults to "localhost".
            port: Server port. Defaults to 5000.
            event_queue: Pygame event queue for injecting events.
        """
        self.host = host
        self.port = port
        self.event_queue = event_queue
        
        self.socket: Optional[socket.socket] = None
        self.connected = False
        self.running = False
        self.player_id: Optional[str] = None
        self.player_name: Optional[str] = None
        
        self._receive_thread: Optional[threading.Thread] = None
        self._heartbeat_thread: Optional[threading.Thread] = None
    
    def connect(self) -> bool:
        """
        Connect to the server.
        
        Returns:
            bool: True if connection succeeded, False otherwise.
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5.0)
            self.socket.connect((self.host, self.port))
            self.socket.settimeout(0.1)
            
            self.connected = True
            self.running = True
            
            self._receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self._receive_thread.start()
            
            self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
            self._heartbeat_thread.start()
            
            logging.info(f"Connected to {self.host}:{self.port}")
            return True
            
        except Exception as e:
            logging.error(f"Connection failed: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from the server."""
        self.running = False
        self.connected = False
        
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
        
        if self._receive_thread:
            self._receive_thread.join(timeout=2.0)
        
        if self._heartbeat_thread:
            self._heartbeat_thread.join(timeout=2.0)
        
        logging.info("Disconnected from server")
    
    def authenticate(self, player_name: str) -> None:
        """
        Send authentication request.
        
        Args:
            player_name: Player name for authentication.
        """
        self.player_name = player_name
        self._send_message("auth_request", {
            "player_name": player_name,
            "client_version": "1.0.0"
        })
    
    def send_movement(self, direction_x: float, direction_y: float) -> None:
        """
        Send movement request.
        
        Args:
            direction_x: X direction (-1 to 1).
            direction_y: Y direction (-1 to 1).
        """
        if not self.connected:
            return
        
        self._send_message("move_request", {
            "player_id": self.player_id or "",
            "direction_x": direction_x,
            "direction_y": direction_y,
            "timestamp": time.time()
        })
    
    def send_chat(self, message: str) -> None:
        """
        Send chat message.
        
        Args:
            message: Chat message text.
        """
        if not self.connected:
            return
        
        self._send_message("chat_message", {
            "message": message
        })
    
    def _send_message(self, msg_type: str, payload: Dict[str, Any]) -> None:
        """
        Send a message to the server.
        
        Args:
            msg_type: Message type.
            payload: Message payload.
        """
        if not self.socket or not self.connected:
            return
        
        try:
            message = {
                "type": msg_type,
                "payload": payload,
                "timestamp": time.time()
            }
            data = json.dumps(message).encode('utf-8')
            self.socket.sendall(data)
        except Exception as e:
            logging.error(f"Send error: {e}")
            self.connected = False
    
    def _receive_loop(self) -> None:
        """Receive loop running in separate thread."""
        buffer = ""
        
        while self.running:
            try:
                data = self.socket.recv(4096)
                if not data:
                    self.connected = False
                    break
                
                buffer += data.decode('utf-8')
                
                # Process complete messages
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line.strip():
                        self._process_message(json.loads(line))
                        
            except socket.timeout:
                continue
            except json.JSONDecodeError as e:
                logging.error(f"JSON decode error: {e}")
            except Exception as e:
                logging.error(f"Receive error: {e}")
                self.connected = False
                break
        
        if self.event_queue:
            pygame.event.post(pygame.event.Event(GameEvent.DISCONNECTED.value))
    
    def _process_message(self, data: Dict[str, Any]) -> None:
        """
        Process a received message.
        
        Args:
            data: Message data dictionary.
        """
        try:
            msg_type = data.get('type', '')
            payload = data.get('payload', {})
            
            if msg_type == 'auth_response':
                self._handle_auth_response(payload)
            elif msg_type == 'move_response':
                self._handle_move_response(payload)
            elif msg_type == 'position_update':
                self._handle_position_update(payload)
            elif msg_type == 'player_join':
                self._handle_player_join(payload)
            elif msg_type == 'player_leave':
                self._handle_player_leave(payload)
            elif msg_type == 'chat_message':
                self._handle_chat_message(payload)
            elif msg_type == 'world_state':
                self._handle_world_state(payload)
            elif msg_type == 'error':
                self._handle_error(payload)
            elif msg_type == 'system_message':
                self._handle_system_message(payload)
                
        except Exception as e:
            logging.error(f"Error processing message: {e}")
    
    def _handle_auth_response(self, payload: Dict[str, Any]) -> None:
        """Handle authentication response."""
        success = payload.get('success', False)
        
        if success:
            self.player_id = payload.get('player_id')
            spawn_x = payload.get('spawn_x', 0)
            spawn_y = payload.get('spawn_y', 0)
            
            if self.event_queue:
                pygame.event.post(pygame.event.Event(
                    GameEvent.AUTH_SUCCESS.value,
                    {
                        'player_id': self.player_id,
                        'spawn_x': spawn_x,
                        'spawn_y': spawn_y
                    }
                ))
        else:
            error_msg = payload.get('error_message', 'Unknown error')
            if self.event_queue:
                pygame.event.post(pygame.event.Event(
                    GameEvent.AUTH_FAILURE.value,
                    {'error': error_msg}
                ))
    
    def _handle_move_response(self, payload: Dict[str, Any]) -> None:
        """Handle movement response."""
        if self.event_queue:
            pygame.event.post(pygame.event.Event(
                GameEvent.POSITION_UPDATE.value,
                {
                    'player_id': payload.get('player_id'),
                    'x': payload.get('new_x'),
                    'y': payload.get('new_y'),
                    'is_self': True
                }
            ))
    
    def _handle_position_update(self, payload: Dict[str, Any]) -> None:
        """Handle position update for other players."""
        if self.event_queue:
            pygame.event.post(pygame.event.Event(
                GameEvent.POSITION_UPDATE.value,
                {
                    'player_id': payload.get('player_id'),
                    'player_name': payload.get('player_name'),
                    'x': payload.get('x'),
                    'y': payload.get('y'),
                    'direction_x': payload.get('direction_x', 0),
                    'direction_y': payload.get('direction_y', 0),
                    'is_self': False
                }
            ))
    
    def _handle_player_join(self, payload: Dict[str, Any]) -> None:
        """Handle player join event."""
        if self.event_queue:
            pygame.event.post(pygame.event.Event(
                GameEvent.PLAYER_JOIN.value,
                {
                    'player_id': payload.get('player_id'),
                    'player_name': payload.get('player_name'),
                    'x': payload.get('x'),
                    'y': payload.get('y')
                }
            ))
    
    def _handle_player_leave(self, payload: Dict[str, Any]) -> None:
        """Handle player leave event."""
        if self.event_queue:
            pygame.event.post(pygame.event.Event(
                GameEvent.PLAYER_LEAVE.value,
                {'player_id': payload.get('player_id')}
            ))
    
    def _handle_chat_message(self, payload: Dict[str, Any]) -> None:
        """Handle chat message."""
        if self.event_queue:
            pygame.event.post(pygame.event.Event(
                GameEvent.CHAT_MESSAGE.value,
                {
                    'player_id': payload.get('player_id'),
                    'player_name': payload.get('player_name'),
                    'message': payload.get('message')
                }
            ))
    
    def _handle_world_state(self, payload: Dict[str, Any]) -> None:
        """Handle world state update."""
        players = payload.get('players', [])
        for player_data in players:
            if self.event_queue:
                pygame.event.post(pygame.event.Event(
                    GameEvent.PLAYER_JOIN.value,
                    player_data
                ))
    
    def _handle_error(self, payload: Dict[str, Any]) -> None:
        """Handle error message."""
        error_msg = payload.get('error', 'Unknown error')
        logging.error(f"Server error: {error_msg}")
    
    def _handle_system_message(self, payload: Dict[str, Any]) -> None:
        """Handle system message."""
        message = payload.get('message', '')
        if self.event_queue:
            pygame.event.post(pygame.event.Event(
                GameEvent.SYSTEM_MESSAGE.value,
                {'message': message}
            ))
    
    def _heartbeat_loop(self) -> None:
        """Send periodic heartbeats."""
        while self.running and self.connected:
            try:
                time.sleep(2.0)
                self._send_message("heartbeat", {})
            except Exception:
                break


class MMORPGClient:
    """
    Main MMORPG client class.
    
    Handles game rendering, input, and network communication.
    """
    
    def __init__(
        self,
        window_width: int = 640,
        window_height: int = 480,
        fps: int = 60,
        server_host: str = "localhost",
        server_port: int = 5000
    ):
        """
        Initialize the MMORPG client.
        
        Args:
            window_width: Window width in pixels. Defaults to 640.
            window_height: Window height in pixels. Defaults to 480.
            fps: Target FPS. Defaults to 60.
            server_host: Server host. Defaults to "localhost".
            server_port: Server port. Defaults to 5000.
        """
        self.window_width = window_width
        self.window_height = window_height
        self.fps = fps
        self.server_host = server_host
        self.server_port = server_port
        
        self.running = False
        self.clock: Optional[pygame.time.Clock] = None
        self.screen: Optional[pygame.Surface] = None
        self.font: Optional[pygame.font.Font] = None
        self.small_font: Optional[pygame.font.Font] = None
        
        self.camera = Camera(window_width, window_height)
        self.network: Optional[NetworkClient] = None
        self.event_queue: List[Any] = []
        
        self.local_player: Optional[Player] = None
        self.players: Dict[str, Player] = {}
        self.objects: List[WorldObject] = []
        
        self.messages: List[Tuple[float, str]] = []
        self.chat_input = ""
        self.show_chat_input = False
        
        self.movement_direction = [0.0, 0.0]
        self.last_move_time = 0.0
        self.move_delay = 0.05
        
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Configure logging."""
        os.makedirs('logs', exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/client.log'),
                logging.StreamHandler()
            ]
        )
    
    def initialize(self) -> bool:
        """
        Initialize Pygame and create window.
        
        Returns:
            bool: True if initialization succeeded.
        """
        try:
            pygame.init()
            pygame.display.set_caption("MMORPG Client")
            
            self.screen = pygame.display.set_mode(
                (self.window_width, self.window_height)
            )
            self.clock = pygame.time.Clock()
            self.font = pygame.font.Font(None, 24)
            self.small_font = pygame.font.Font(None, 18)
            
            logging.info("Pygame initialized")
            return True
            
        except Exception as e:
            logging.error(f"Initialization failed: {e}")
            return False
    
    def connect(self) -> bool:
        """
        Connect to the server.
        
        Returns:
            bool: True if connection succeeded.
        """
        self.network = NetworkClient(
            host=self.server_host,
            port=self.server_port,
            event_queue=self.event_queue
        )
        
        return self.network.connect()
    
    def run(self) -> None:
        """Main game loop."""
        self.running = True
        
        # Show login prompt
        player_name = self._get_player_name()
        if not player_name:
            self.running = False
            return
        
        self.network.authenticate(player_name)
        
        while self.running:
            delta_time = self.clock.tick(self.fps) / 1000.0 if self.clock else 0.0
            
            self._handle_events()
            self._update(delta_time)
            self._render()
        
        self.shutdown()
    
    def _get_player_name(self) -> str:
        """
        Get player name from user.
        
        Returns:
            str: Player name or empty string if cancelled.
        """
        input_text = ""
        input_active = True
        
        while input_active and self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return ""
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if input_text.strip():
                            input_active = False
                            return input_text.strip()
                    elif event.key == pygame.K_ESCAPE:
                        return ""
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    else:
                        if len(input_text) < 20:
                            char = event.unicode
                            if char.isalnum() or char in '_-':
                                input_text += char
            
            # Render login screen
            if self.screen:
                self.screen.fill((30, 30, 30))
                
                title = self.font.render("Enter Player Name:", True, (255, 255, 255))
                self.screen.blit(title, (
                    self.window_width // 2 - title.get_width() // 2,
                    self.window_height // 2 - 50
                ))
                
                input_surface = self.font.render(input_text + "_", True, (255, 255, 0))
                self.screen.blit(input_surface, (
                    self.window_width // 2 - input_surface.get_width() // 2,
                    self.window_height // 2
                ))
                
                hint = self.small_font.render(
                    "Press ENTER to confirm, ESC to cancel",
                    True, (150, 150, 150)
                )
                self.screen.blit(hint, (
                    self.window_width // 2 - hint.get_width() // 2,
                    self.window_height // 2 + 50
                ))
                
                pygame.display.flip()
        
        return input_text.strip()
    
    def _handle_events(self) -> None:
        """Handle pygame and custom events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.show_chat_input:
                        self.show_chat_input = False
                        self.chat_input = ""
                    else:
                        self.running = False
                elif event.key == pygame.K_RETURN:
                    if self.show_chat_input and self.chat_input.strip():
                        if self.network:
                            self.network.send_chat(self.chat_input)
                        self.show_chat_input = False
                        self.chat_input = ""
                elif event.key == pygame.K_t:
                    self.show_chat_input = True
                elif event.key == pygame.K_w:
                    self.movement_direction[1] = -1.0
                elif event.key == pygame.K_s:
                    self.movement_direction[1] = 1.0
                elif event.key == pygame.K_a:
                    self.movement_direction[0] = -1.0
                elif event.key == pygame.K_d:
                    self.movement_direction[0] = 1.0
            
            elif event.type == pygame.KEYUP:
                if event.key in (pygame.K_w, pygame.K_s):
                    self.movement_direction[1] = 0.0
                if event.key in (pygame.K_a, pygame.K_d):
                    self.movement_direction[0] = 0.0
            
            elif event.type == GameEvent.AUTH_SUCCESS.value:
                self.local_player = Player(
                    player_id=event.player_id,
                    player_name=self.network.player_name or "Unknown",
                    x=event.spawn_x,
                    y=event.spawn_y
                )
                self.camera.x = event.spawn_x
                self.camera.y = event.spawn_y
                self._add_message("System", "Welcome to the game!")
            
            elif event.type == GameEvent.AUTH_FAILURE.value:
                self._add_message("System", f"Authentication failed: {event.error}")
                self.running = False
            
            elif event.type == GameEvent.POSITION_UPDATE.value:
                self._handle_position_event(event)
            
            elif event.type == GameEvent.PLAYER_JOIN.value:
                player_id = event.player_id
                if player_id and player_id not in self.players:
                    self.players[player_id] = Player(
                        player_id=player_id,
                        player_name=event.player_name or "Unknown",
                        x=event.x or 0,
                        y=event.y or 0
                    )
                    self._add_message("System", f"{event.player_name} joined the game")
            
            elif event.type == GameEvent.PLAYER_LEAVE.value:
                player_id = event.player_id
                if player_id in self.players:
                    player_name = self.players[player_id].player_name
                    del self.players[player_id]
                    self._add_message("System", f"{player_name} left the game")
            
            elif event.type == GameEvent.CHAT_MESSAGE.value:
                player_name = event.player_name or "Unknown"
                message = event.message or ""
                self._add_message(player_name, message)
            
            elif event.type == GameEvent.SYSTEM_MESSAGE.value:
                self._add_message("System", event.message or "")
            
            elif event.type == GameEvent.DISCONNECTED.value:
                self._add_message("System", "Disconnected from server")
                self.running = False
    
    def _handle_position_event(self, event: Any) -> None:
        """
        Handle position update event.
        
        Args:
            event: Position update event.
        """
        player_id = event.player_id
        
        if event.is_self and self.local_player:
            self.local_player.x = event.x
            self.local_player.y = event.y
        elif player_id in self.players:
            player = self.players[player_id]
            player.x = event.x
            player.y = event.y
            player.direction_x = event.direction_x
            player.direction_y = event.direction_y
    
    def _update(self, delta_time: float) -> None:
        """
        Update game state.
        
        Args:
            delta_time: Time since last update.
        """
        # Update camera
        if self.local_player:
            self.camera.update(
                self.local_player.x,
                self.local_player.y,
                delta_time
            )
        
        # Send movement
        current_time = time.time()
        if any(self.movement_direction) and current_time - self.last_move_time > self.move_delay:
            if self.network and self.network.connected:
                self.network.send_movement(
                    self.movement_direction[0],
                    self.movement_direction[1]
                )
                self.last_move_time = current_time
        
        # Update messages (remove old ones)
        self.messages = [
            (t, m) for t, m in self.messages
            if time.time() - t < 10.0
        ]
    
    def _render(self) -> None:
        """Render the game."""
        if not self.screen:
            return
        
        # Clear screen
        self.screen.fill((20, 20, 30))
        
        # Render terrain (simplified - just grid)
        self._render_terrain()
        
        # Render objects
        self._render_objects()
        
        # Render other players
        self._render_players()
        
        # Render local player
        if self.local_player:
            self._render_player(self.local_player, is_local=True)
        
        # Render UI
        self._render_ui()
        
        pygame.display.flip()
    
    def _render_terrain(self) -> None:
        """Render terrain tiles."""
        if not self.screen or not self.local_player:
            return
        
        # Calculate visible area
        start_x = int(self.camera.x - self.window_width / 80 - 1)
        end_x = int(self.camera.x + self.window_width / 80 + 1)
        start_y = int(self.camera.y - self.window_height / 80 - 1)
        end_y = int(self.camera.y + self.window_height / 80 + 1)
        
        # Draw grid
        for x in range(start_x, end_x + 1):
            for y in range(start_y, end_y + 1):
                screen_x, screen_y = self.camera.apply(x, y)
                
                # Check bounds
                if x < 0 or x >= 500 or y < 0 or y >= 500:
                    color = (40, 40, 50)
                else:
                    # Simple terrain coloring
                    color = (34, 139, 34)  # Grass green
                
                pygame.draw.rect(self.screen, color, (screen_x, screen_y, 40, 40))
                pygame.draw.rect(self.screen, (50, 50, 60), (screen_x, screen_y, 40, 40), 1)
    
    def _render_objects(self) -> None:
        """Render world objects."""
        if not self.screen:
            return
        
        for obj in self.objects:
            if self.camera.is_visible(obj.x, obj.y):
                screen_x, screen_y = self.camera.apply(obj.x, obj.y)
                
                # Draw object based on type
                if obj.object_type == "tree":
                    pygame.draw.circle(self.screen, (34, 139, 34), (screen_x + 20, screen_y + 20), 15)
                    pygame.draw.circle(self.screen, (0, 100, 0), (screen_x + 20, screen_y + 20), 15, 2)
                elif obj.object_type == "rock":
                    pygame.draw.rect(self.screen, (128, 128, 128), (screen_x + 5, screen_y + 10, 30, 25))
                    pygame.draw.rect(self.screen, (80, 80, 80), (screen_x + 5, screen_y + 10, 30, 25), 2)
                elif obj.object_type == "house":
                    pygame.draw.rect(self.screen, (139, 69, 19), (screen_x + 5, screen_y + 5, 30, 30))
                    pygame.draw.polygon(self.screen, (100, 50, 10), [
                        (screen_x + 5, screen_y + 5),
                        (screen_x + 20, screen_y - 5),
                        (screen_x + 35, screen_y + 5)
                    ])
    
    def _render_players(self) -> None:
        """Render other players."""
        for player in self.players.values():
            if self.camera.is_visible(player.x, player.y):
                self._render_player(player, is_local=False)
    
    def _render_player(self, player: Player, is_local: bool = False) -> None:
        """
        Render a player.
        
        Args:
            player: Player to render.
            is_local: Whether this is the local player.
        """
        if not self.screen:
            return
        
        screen_x, screen_y = self.camera.apply(player.x, player.y)
        
        # Draw player body
        color = (0, 255, 0) if is_local else (255, 165, 0)
        pygame.draw.circle(self.screen, color, (screen_x + 20, screen_y + 20), 18)
        pygame.draw.circle(self.screen, (0, 0, 0), (screen_x + 20, screen_y + 20), 18, 2)
        
        # Draw player name
        name_text = self.small_font.render(player.player_name[:15], True, (255, 255, 255))
        self.screen.blit(name_text, (screen_x + 20 - name_text.get_width() // 2, screen_y - 5))
    
    def _render_ui(self) -> None:
        """Render user interface."""
        if not self.screen:
            return
        
        # Draw chat/messages area
        ui_y = self.window_height - 150
        
        # Background
        pygame.draw.rect(self.screen, (0, 0, 0, 128), (0, ui_y, self.window_width, 150))
        pygame.draw.line(self.screen, (100, 100, 100), (0, ui_y), (self.window_width, ui_y), 2)
        
        # Draw recent messages
        message_y = ui_y + 5
        for timestamp, message in self.messages[-5:]:
            text = self.small_font.render(message, True, (255, 255, 255))
            self.screen.blit(text, (5, message_y))
            message_y += 20
        
        # Draw chat input
        if self.show_chat_input:
            input_bg = pygame.Surface((self.window_width - 20, 25))
            input_bg.fill((50, 50, 50))
            self.screen.blit(input_bg, (10, self.window_height - 35))
            
            input_text = self.font.render(self.chat_input + "_", True, (255, 255, 255))
            self.screen.blit(input_text, (15, self.window_height - 33))
        else:
            hint = self.small_font.render("Press T to chat", True, (150, 150, 150))
            self.screen.blit(hint, (10, self.window_height - 30))
        
        # Draw status
        if self.network:
            status = "Connected" if self.network.connected else "Disconnected"
            color = (0, 255, 0) if self.network.connected else (255, 0, 0)
            status_text = self.small_font.render(f"Status: {status}", True, color)
            self.screen.blit(status_text, (self.window_width - 100, 10))
        
        # Draw FPS
        if self.clock:
            fps_text = self.small_font.render(f"FPS: {int(self.clock.get_fps())}", True, (255, 255, 0))
            self.screen.blit(fps_text, (self.window_width - 100, 30))
    
    def _add_message(self, sender: str, text: str) -> None:
        """
        Add a chat/system message.
        
        Args:
            sender: Message sender.
            text: Message text.
        """
        message = f"[{sender}]: {text}"
        self.messages.append((time.time(), message))
        
        # Keep only last 20 messages
        if len(self.messages) > 20:
            self.messages = self.messages[-20:]
    
    def shutdown(self) -> None:
        """Shutdown the client."""
        self.running = False
        
        if self.network:
            self.network.disconnect()
        
        pygame.quit()
        logging.info("Client shutdown complete")


def main() -> None:
    """Main entry point for the client."""
    import argparse
    
    parser = argparse.ArgumentParser(description='MMORPG Client')
    parser.add_argument(
        '--host', '-H',
        default='localhost',
        help='Server host'
    )
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=5000,
        help='Server port'
    )
    parser.add_argument(
        '--width', '-W',
        type=int,
        default=640,
        help='Window width'
    )
    parser.add_argument(
        '--height', '-T',
        type=int,
        default=480,
        help='Window height'
    )
    
    args = parser.parse_args()
    
    client = MMORPGClient(
        window_width=args.width,
        window_height=args.height,
        server_host=args.host,
        server_port=args.port
    )
    
    if not client.initialize():
        logging.error("Failed to initialize client")
        return
    
    if not client.connect():
        logging.error("Failed to connect to server")
        client.shutdown()
        return
    
    client.run()


if __name__ == '__main__':
    main()
