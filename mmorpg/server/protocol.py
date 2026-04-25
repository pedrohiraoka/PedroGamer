"""
Protocol definitions for MMORPG client-server communication.

This module defines all message types and structures used in the
communication protocol between clients and server.
"""

from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional, List
from enum import Enum
import json


class MessageType(Enum):
    """Enum defining all supported message types in the protocol."""
    
    AUTH_REQUEST = "auth_request"
    AUTH_RESPONSE = "auth_response"
    MOVE_REQUEST = "move_request"
    MOVE_RESPONSE = "move_response"
    POSITION_UPDATE = "position_update"
    CHAT_MESSAGE = "chat_message"
    PLAYER_JOIN = "player_join"
    PLAYER_LEAVE = "player_leave"
    HEARTBEAT = "heartbeat"
    HEARTBEAT_ACK = "heartbeat_ack"
    WORLD_STATE = "world_state"
    ERROR = "error"
    SYSTEM_MESSAGE = "system_message"


@dataclass
class Message:
    """Base message structure for all protocol communications."""
    
    type: str
    payload: Dict[str, Any]
    timestamp: float = 0.0
    
    def to_json(self) -> str:
        """
        Serialize the message to JSON string.
        
        Returns:
            str: JSON representation of the message.
        """
        return json.dumps(asdict(self))
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        """
        Deserialize a message from JSON string.
        
        Args:
            json_str: JSON string representation of the message.
            
        Returns:
            Message: Deserialized message object.
            
        Raises:
            ValueError: If the JSON is invalid or missing required fields.
        """
        data = json.loads(json_str)
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert message to dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the message.
        """
        return asdict(self)


@dataclass
class AuthRequest:
    """Authentication request sent by client to server."""
    
    player_name: str
    client_version: str = "1.0.0"


@dataclass
class AuthResponse:
    """Authentication response sent by server to client."""
    
    success: bool
    player_id: Optional[str] = None
    error_message: Optional[str] = None
    spawn_x: Optional[int] = None
    spawn_y: Optional[int] = None


@dataclass
class MoveRequest:
    """Movement request sent by client to server."""
    
    player_id: str
    direction_x: float
    direction_y: float
    timestamp: float


@dataclass
class MoveResponse:
    """Movement response sent by server to client."""
    
    player_id: str
    new_x: float
    new_y: float
    success: bool
    error_message: Optional[str] = None


@dataclass
class PositionUpdate:
    """Position update for a player broadcast to other clients."""
    
    player_id: str
    player_name: str
    x: float
    y: float
    direction_x: float = 0.0
    direction_y: float = 0.0


@dataclass
class ChatMessage:
    """Chat message structure."""
    
    player_id: str
    player_name: str
    message: str
    timestamp: float


@dataclass
class PlayerInfo:
    """Information about a connected player."""
    
    player_id: str
    player_name: str
    x: float
    y: float


@dataclass
class WorldState:
    """Complete world state snapshot."""
    
    players: List[Dict[str, Any]]
    objects: List[Dict[str, Any]]
    timestamp: float


def create_message(msg_type: MessageType, payload: Dict[str, Any]) -> Message:
    """
    Create a new message with the given type and payload.
    
    Args:
        msg_type: The type of message to create.
        payload: The payload data for the message.
        
    Returns:
        Message: The created message object.
    """
    import time
    return Message(
        type=msg_type.value,
        payload=payload,
        timestamp=time.time()
    )


def validate_message(data: Dict[str, Any]) -> bool:
    """
    Validate that a message dictionary has required fields.
    
    Args:
        data: Dictionary to validate.
        
    Returns:
        bool: True if valid, False otherwise.
    """
    required_fields = ['type', 'payload']
    return all(field in data for field in required_fields)
