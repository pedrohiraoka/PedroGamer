"""
World management module for MMORPG server.

This module handles world state, map loading, collision detection,
and player position validation.
"""

import json
import logging
import random
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import os

logger = logging.getLogger(__name__)


@dataclass
class Tile:
    """Represents a single tile in the world map."""
    
    x: int
    y: int
    terrain_type: str
    walkable: bool = True
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorldObject:
    """Represents an interactive object in the world."""
    
    object_id: str
    x: int
    y: int
    object_type: str
    collidable: bool = True
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SpawnPoint:
    """Represents a spawn point for players."""
    
    x: float
    y: float
    name: str = "default"


class World:
    """
    Manages the game world including map, objects, and collision detection.
    
    Attributes:
        width: Width of the world in tiles.
        height: Height of the world in tiles.
        tile_size: Size of each tile in pixels.
    """
    
    def __init__(self, width: int = 500, height: int = 500, tile_size: int = 40):
        """
        Initialize the world.
        
        Args:
            width: Width of the world in tiles. Defaults to 500.
            height: Height of the world in tiles. Defaults to 500.
            tile_size: Size of each tile in pixels. Defaults to 40.
        """
        self.width = width
        self.height = height
        self.tile_size = tile_size
        
        self.tiles: Dict[Tuple[int, int], Tile] = {}
        self.objects: Dict[str, WorldObject] = {}
        self.spawn_points: List[SpawnPoint] = []
        
        self._initialize_default_world()
    
    def _initialize_default_world(self) -> None:
        """Initialize a default world with basic terrain."""
        logger.info("Initializing default world...")
        
        # Fill with grass by default
        for x in range(self.width):
            for y in range(self.height):
                self.tiles[(x, y)] = Tile(
                    x=x,
                    y=y,
                    terrain_type="grass",
                    walkable=True
                )
        
        # Add water bodies (only if world is large enough)
        if self.width >= 150 and self.height >= 150:
            for i in range(5):
                cx = random.randint(50, self.width - 50)
                cy = random.randint(50, self.height - 50)
                radius = random.randint(10, 30)
                
                for x in range(cx - radius, cx + radius):
                    for y in range(cy - radius, cy + radius):
                        if 0 <= x < self.width and 0 <= y < self.height:
                            dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
                            if dist < radius:
                                self.tiles[(x, y)] = Tile(
                                    x=x,
                                    y=y,
                                    terrain_type="water",
                                    walkable=False
                                )
        
        # Add stone areas (only if world is large enough)
        if self.width >= 150 and self.height >= 150:
            for i in range(3):
                cx = random.randint(50, self.width - 50)
                cy = random.randint(50, self.height - 50)
                radius = random.randint(5, 15)
                
                for x in range(cx - radius, cx + radius):
                    for y in range(cy - radius, cy + radius):
                        if 0 <= x < self.width and 0 <= y < self.height:
                            dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
                            if dist < radius:
                                self.tiles[(x, y)] = Tile(
                                    x=x,
                                    y=y,
                                    terrain_type="stone",
                                    walkable=False
                                )
        
        # Add spawn points
        self.spawn_points = [
            SpawnPoint(x=self.width // 2, y=self.height // 2, name="center"),
            SpawnPoint(x=min(50, self.width - 1), y=min(50, self.height - 1), name="northwest"),
            SpawnPoint(x=max(self.width - 50, 0), y=min(50, self.height - 1), name="northeast"),
            SpawnPoint(x=min(50, self.width - 1), y=max(self.height - 50, 0), name="southwest"),
            SpawnPoint(x=max(self.width - 50, 0), y=max(self.height - 50, 0), name="southeast"),
        ]
        
        # Add some world objects (only if world is large enough)
        if self.width >= 20 and self.height >= 20:
            num_objects = min(50, (self.width * self.height) // 100)
            for i in range(num_objects):
                obj_x = random.randint(0, self.width - 1)
                obj_y = random.randint(0, self.height - 1)
                obj_type = random.choice(["tree", "rock", "house"])
                
                obj_id = f"obj_{i}"
                self.objects[obj_id] = WorldObject(
                    object_id=obj_id,
                    x=obj_x,
                    y=obj_y,
                    object_type=obj_type,
                    collidable=(obj_type in ["tree", "rock", "house"])
                )
        
        logger.info(f"World initialized: {self.width}x{self.height} tiles")
    
    def load_from_file(self, map_file: str, object_file: str) -> bool:
        """
        Load world from JSON files.
        
        Args:
            map_file: Path to the map JSON file.
            object_file: Path to the objects JSON file.
            
        Returns:
            bool: True if loading succeeded, False otherwise.
        """
        try:
            if not os.path.exists(map_file):
                logger.warning(f"Map file not found: {map_file}")
                return False
            
            if not os.path.exists(object_file):
                logger.warning(f"Object file not found: {object_file}")
                return False
            
            with open(map_file, 'r') as f:
                map_data = json.load(f)
            
            with open(object_file, 'r') as f:
                object_data = json.load(f)
            
            # Load tiles
            self.tiles.clear()
            for tile_data in map_data.get('tiles', []):
                tile = Tile(
                    x=tile_data['x'],
                    y=tile_data['y'],
                    terrain_type=tile_data['terrain_type'],
                    walkable=tile_data.get('walkable', True),
                    properties=tile_data.get('properties', {})
                )
                self.tiles[(tile.x, tile.y)] = tile
            
            # Load objects
            self.objects.clear()
            for obj_data in object_data.get('objects', []):
                obj = WorldObject(
                    object_id=obj_data['object_id'],
                    x=obj_data['x'],
                    y=obj_data['y'],
                    object_type=obj_data['object_type'],
                    collidable=obj_data.get('collidable', True),
                    properties=obj_data.get('properties', {})
                )
                self.objects[obj.object_id] = obj
            
            # Load spawn points
            self.spawn_points.clear()
            for spawn_data in map_data.get('spawn_points', []):
                spawn = SpawnPoint(
                    x=spawn_data['x'],
                    y=spawn_data['y'],
                    name=spawn_data.get('name', 'default')
                )
                self.spawn_points.append(spawn)
            
            logger.info(f"World loaded from {map_file} and {object_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading world: {e}")
            return False
    
    def save_to_file(self, map_file: str, object_file: str) -> bool:
        """
        Save world to JSON files.
        
        Args:
            map_file: Path to save the map JSON file.
            object_file: Path to save the objects JSON file.
            
        Returns:
            bool: True if saving succeeded, False otherwise.
        """
        try:
            # Ensure directories exist
            os.makedirs(os.path.dirname(map_file) if os.path.dirname(map_file) else '.', exist_ok=True)
            os.makedirs(os.path.dirname(object_file) if os.path.dirname(object_file) else '.', exist_ok=True)
            
            # Save tiles
            map_data = {
                'width': self.width,
                'height': self.height,
                'tiles': [
                    {
                        'x': tile.x,
                        'y': tile.y,
                        'terrain_type': tile.terrain_type,
                        'walkable': tile.walkable,
                        'properties': tile.properties
                    }
                    for tile in self.tiles.values()
                ],
                'spawn_points': [
                    {'x': sp.x, 'y': sp.y, 'name': sp.name}
                    for sp in self.spawn_points
                ]
            }
            
            with open(map_file, 'w') as f:
                json.dump(map_data, f, indent=2)
            
            # Save objects
            object_data = {
                'objects': [
                    {
                        'object_id': obj.object_id,
                        'x': obj.x,
                        'y': obj.y,
                        'object_type': obj.object_type,
                        'collidable': obj.collidable,
                        'properties': obj.properties
                    }
                    for obj in self.objects.values()
                ]
            }
            
            with open(object_file, 'w') as f:
                json.dump(object_data, f, indent=2)
            
            logger.info(f"World saved to {map_file} and {object_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving world: {e}")
            return False
    
    def is_walkable(self, x: float, y: float) -> bool:
        """
        Check if a position is walkable.
        
        Args:
            x: X coordinate in tile units.
            y: Y coordinate in tile units.
            
        Returns:
            bool: True if the position is walkable, False otherwise.
        """
        # Check bounds
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return False
        
        # Check tile walkability
        tile_x = int(x)
        tile_y = int(y)
        
        tile = self.tiles.get((tile_x, tile_y))
        if tile and not tile.walkable:
            return False
        
        # Check object collisions
        for obj in self.objects.values():
            if obj.collidable:
                if abs(obj.x - x) < 0.5 and abs(obj.y - y) < 0.5:
                    return False
        
        return True
    
    def get_spawn_point(self) -> Tuple[float, float]:
        """
        Get a random spawn point.
        
        Returns:
            Tuple[float, float]: X and Y coordinates of the spawn point.
        """
        if not self.spawn_points:
            return (self.width / 2, self.height / 2)
        
        spawn = random.choice(self.spawn_points)
        return (spawn.x, spawn.y)
    
    def validate_movement(
        self,
        player_id: str,
        current_x: float,
        current_y: float,
        new_x: float,
        new_y: float
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate a movement request.
        
        Args:
            player_id: ID of the moving player.
            current_x: Current X position.
            current_y: Current Y position.
            new_x: Requested new X position.
            new_y: Requested new Y position.
            
        Returns:
            Tuple[bool, Optional[str]]: (success, error_message)
        """
        # Check bounds
        if new_x < 0 or new_x >= self.width:
            return False, "Movement out of bounds (X)"
        
        if new_y < 0 or new_y >= self.height:
            return False, "Movement out of bounds (Y)"
        
        # Check tile walkability at new position
        if not self.is_walkable(new_x, new_y):
            return False, "Cannot move to non-walkable tile"
        
        # Check for collisions along the path (simple check)
        steps = max(abs(new_x - current_x), abs(new_y - current_y)) * 4
        if steps > 0:
            dx = (new_x - current_x) / steps
            dy = (new_y - current_y) / steps
            
            for i in range(int(steps) + 1):
                check_x = current_x + dx * i
                check_y = current_y + dy * i
                if not self.is_walkable(check_x, check_y):
                    return False, "Collision detected"
        
        return True, None
    
    def get_tile(self, x: int, y: int) -> Optional[Tile]:
        """
        Get a tile at the specified coordinates.
        
        Args:
            x: X coordinate.
            y: Y coordinate.
            
        Returns:
            Optional[Tile]: The tile at the coordinates, or None if out of bounds.
        """
        return self.tiles.get((x, y))
    
    def get_objects_in_range(
        self,
        center_x: float,
        center_y: float,
        radius: float
    ) -> List[WorldObject]:
        """
        Get all objects within a certain radius.
        
        Args:
            center_x: Center X coordinate.
            center_y: Center Y coordinate.
            radius: Search radius.
            
        Returns:
            List[WorldObject]: List of objects in range.
        """
        result = []
        for obj in self.objects.values():
            dist = ((obj.x - center_x) ** 2 + (obj.y - center_y) ** 2) ** 0.5
            if dist <= radius:
                result.append(obj)
        return result
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert world state to dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the world.
        """
        return {
            'width': self.width,
            'height': self.height,
            'tile_size': self.tile_size,
            'objects': [
                {
                    'object_id': obj.object_id,
                    'x': obj.x,
                    'y': obj.y,
                    'object_type': obj.object_type
                }
                for obj in self.objects.values()
            ]
        }
