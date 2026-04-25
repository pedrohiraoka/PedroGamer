#!/usr/bin/env python3
"""
World Generator - Creates or loads world map data.

This script generates a tilemap and object map for the MMORPG world,
serializing them to JSON files for use by the server.
"""

import json
import random
import argparse
import os
import sys
from typing import Dict, List, Any, Tuple


def generate_terrain(
    width: int = 500,
    height: int = 500,
    water_bodies: int = 5,
    stone_areas: int = 3,
    forest_areas: int = 8
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Generate terrain tiles for the world.
    
    Args:
        width: World width in tiles. Defaults to 500.
        height: World height in tiles. Defaults to 500.
        water_bodies: Number of water bodies. Defaults to 5.
        stone_areas: Number of stone areas. Defaults to 3.
        forest_areas: Number of forest areas. Defaults to 8.
        
    Returns:
        Tuple containing list of tiles and list of spawn points.
    """
    print(f"Generating terrain for {width}x{height} world...")
    
    # Initialize with grass
    tiles = []
    for x in range(width):
        for y in range(height):
            tiles.append({
                'x': x,
                'y': y,
                'terrain_type': 'grass',
                'walkable': True,
                'properties': {}
            })
    
    # Create a 2D lookup for faster modification
    tile_map: Dict[Tuple[int, int], Dict[str, Any]] = {
        (t['x'], t['y']): t for t in tiles
    }
    
    # Add water bodies
    for i in range(water_bodies):
        cx = random.randint(50, width - 50)
        cy = random.randint(50, height - 50)
        radius = random.randint(15, 35)
        
        print(f"  Adding water body at ({cx}, {cy}) with radius {radius}")
        
        for x in range(cx - radius, cx + radius + 1):
            for y in range(cy - radius, cy + radius + 1):
                if 0 <= x < width and 0 <= y < height:
                    dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
                    if dist < radius:
                        tile = tile_map.get((x, y))
                        if tile:
                            tile['terrain_type'] = 'water'
                            tile['walkable'] = False
    
    # Add stone/mountain areas
    for i in range(stone_areas):
        cx = random.randint(50, width - 50)
        cy = random.randint(50, height - 50)
        radius = random.randint(8, 20)
        
        print(f"  Adding stone area at ({cx}, {cy}) with radius {radius}")
        
        for x in range(cx - radius, cx + radius + 1):
            for y in range(cy - radius, cy + radius + 1):
                if 0 <= x < width and 0 <= y < height:
                    dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
                    if dist < radius:
                        tile = tile_map.get((x, y))
                        if tile:
                            tile['terrain_type'] = 'stone'
                            tile['walkable'] = False
    
    # Add forest areas (dirt paths with trees)
    for i in range(forest_areas):
        cx = random.randint(50, width - 50)
        cy = random.randint(50, height - 50)
        radius = random.randint(10, 25)
        
        print(f"  Adding forest area at ({cx}, {cy}) with radius {radius}")
        
        for x in range(cx - radius, cx + radius + 1):
            for y in range(cy - radius, cy + radius + 1):
                if 0 <= x < width and 0 <= y < height:
                    dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
                    if dist < radius:
                        tile = tile_map.get((x, y))
                        if tile and tile['terrain_type'] == 'grass':
                            # Some areas become dirt
                            if random.random() < 0.1:
                                tile['terrain_type'] = 'dirt'
    
    # Convert back to list
    tiles = list(tile_map.values())
    
    # Generate spawn points
    spawn_points = [
        {'x': width // 2, 'y': height // 2, 'name': 'center'},
        {'x': 50, 'y': 50, 'name': 'northwest'},
        {'x': width - 50, 'y': 50, 'name': 'northeast'},
        {'x': 50, 'y': height - 50, 'name': 'southwest'},
        {'x': width - 50, 'y': height - 50, 'name': 'southeast'},
    ]
    
    # Find walkable spawn points
    for spawn in spawn_points:
        tile = tile_map.get((spawn['x'], spawn['y']))
        if tile and not tile['walkable']:
            # Find nearby walkable tile
            for offset_x in range(-5, 6):
                for offset_y in range(-5, 6):
                    check_x = spawn['x'] + offset_x
                    check_y = spawn['y'] + offset_y
                    check_tile = tile_map.get((check_x, check_y))
                    if check_tile and check_tile['walkable']:
                        spawn['x'] = check_x
                        spawn['y'] = check_y
                        break
    
    return tiles, spawn_points


def generate_objects(
    width: int = 500,
    height: int = 500,
    num_trees: int = 200,
    num_rocks: int = 100,
    num_houses: int = 20
) -> List[Dict[str, Any]]:
    """
    Generate world objects.
    
    Args:
        width: World width in tiles. Defaults to 500.
        height: World height in tiles. Defaults to 500.
        num_trees: Number of trees. Defaults to 200.
        num_rocks: Number of rocks. Defaults to 100.
        num_houses: Number of houses. Defaults to 20.
        
    Returns:
        List of object dictionaries.
    """
    print(f"Generating world objects...")
    
    objects = []
    obj_id = 0
    
    # Generate trees
    for i in range(num_trees):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        
        objects.append({
            'object_id': f'tree_{obj_id}',
            'x': x,
            'y': y,
            'object_type': 'tree',
            'collidable': True,
            'properties': {'variant': random.randint(1, 3)}
        })
        obj_id += 1
    
    # Generate rocks
    for i in range(num_rocks):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        
        objects.append({
            'object_id': f'rock_{obj_id}',
            'x': x,
            'y': y,
            'object_type': 'rock',
            'collidable': True,
            'properties': {'size': random.choice(['small', 'medium', 'large'])}
        })
        obj_id += 1
    
    # Generate houses
    for i in range(num_houses):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        
        objects.append({
            'object_id': f'house_{obj_id}',
            'x': x,
            'y': y,
            'object_type': 'house',
            'collidable': True,
            'properties': {'color': random.choice(['brown', 'gray', 'red'])}
        })
        obj_id += 1
    
    print(f"  Generated {len(objects)} objects")
    
    return objects


def save_world(
    tiles: List[Dict[str, Any]],
    spawn_points: List[Dict[str, Any]],
    objects: List[Dict[str, Any]],
    output_dir: str = 'resources'
) -> bool:
    """
    Save world data to JSON files.
    
    Args:
        tiles: List of tile dictionaries.
        spawn_points: List of spawn point dictionaries.
        objects: List of object dictionaries.
        output_dir: Output directory. Defaults to 'resources'.
        
    Returns:
        bool: True if saving succeeded.
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        
        # Save map file
        map_file = os.path.join(output_dir, 'world_map.json')
        map_data = {
            'width': 500,
            'height': 500,
            'tile_size': 40,
            'tiles': tiles,
            'spawn_points': spawn_points
        }
        
        with open(map_file, 'w') as f:
            json.dump(map_data, f, indent=2)
        
        print(f"Saved map to {map_file}")
        
        # Save objects file
        object_file = os.path.join(output_dir, 'world_objects.json')
        object_data = {
            'objects': objects
        }
        
        with open(object_file, 'w') as f:
            json.dump(object_data, f, indent=2)
        
        print(f"Saved objects to {object_file}")
        
        return True
        
    except Exception as e:
        print(f"Error saving world: {e}")
        return False


def load_existing_world(
    map_file: str,
    object_file: str
) -> Tuple[bool, List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Load existing world from JSON files.
    
    Args:
        map_file: Path to map JSON file.
        object_file: Path to objects JSON file.
        
    Returns:
        Tuple of (success, tiles, spawn_points, objects).
    """
    try:
        with open(map_file, 'r') as f:
            map_data = json.load(f)
        
        with open(object_file, 'r') as f:
            object_data = json.load(f)
        
        tiles = map_data.get('tiles', [])
        spawn_points = map_data.get('spawn_points', [])
        objects = object_data.get('objects', [])
        
        print(f"Loaded {len(tiles)} tiles and {len(objects)} objects")
        
        return True, tiles, spawn_points, objects
        
    except Exception as e:
        print(f"Error loading world: {e}")
        return False, [], [], []


def main() -> None:
    """Main entry point for world generator."""
    parser = argparse.ArgumentParser(description='MMORPG World Generator')
    parser.add_argument(
        '--generate', '-g',
        action='store_true',
        help='Generate a new world'
    )
    parser.add_argument(
        '--output', '-o',
        default='resources',
        help='Output directory for generated files'
    )
    parser.add_argument(
        '--width', '-W',
        type=int,
        default=500,
        help='World width in tiles'
    )
    parser.add_argument(
        '--height', '-H',
        type=int,
        default=500,
        help='World height in tiles'
    )
    parser.add_argument(
        '--load', '-l',
        nargs=2,
        metavar=('MAP_FILE', 'OBJECT_FILE'),
        help='Load existing world files'
    )
    
    args = parser.parse_args()
    
    if args.load:
        # Load existing world
        success, tiles, spawn_points, objects = load_existing_world(
            args.load[0],
            args.load[1]
        )
        
        if success:
            print("World loaded successfully!")
            print(f"  Tiles: {len(tiles)}")
            print(f"  Spawn points: {len(spawn_points)}")
            print(f"  Objects: {len(objects)}")
        else:
            print("Failed to load world")
            sys.exit(1)
    
    elif args.generate or True:  # Default to generate
        # Generate new world
        print("=" * 50)
        print("MMORPG World Generator")
        print("=" * 50)
        
        tiles, spawn_points = generate_terrain(
            width=args.width,
            height=args.height
        )
        
        objects = generate_objects(
            width=args.width,
            height=args.height
        )
        
        if save_world(tiles, spawn_points, objects, args.output):
            print("=" * 50)
            print("World generation complete!")
            print(f"  Total tiles: {len(tiles)}")
            print(f"  Spawn points: {len(spawn_points)}")
            print(f"  Objects: {len(objects)}")
            print("=" * 50)
        else:
            print("Failed to save world")
            sys.exit(1)
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
