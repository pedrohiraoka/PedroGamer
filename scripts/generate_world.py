#!/usr/bin/env python3
"""
World generation script for MMORPG.

Usage:
    python scripts/generate_world.py [options]
"""

import argparse
import logging
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils import MapGenerator


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="MMORPG World Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/generate_world.py --output resources/world_map.json
    python scripts/generate_world.py --size 500 --seed 12345
        """
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="resources/world_map.json",
        help="Output path for world map (default: resources/world_map.json)"
    )
    
    parser.add_argument(
        "--objects-output",
        type=str,
        default="resources/world_objects.json",
        help="Output path for world objects (default: resources/world_objects.json)"
    )
    
    parser.add_argument(
        "--size", "-s",
        type=int,
        default=500,
        help="World size (width and height) in tiles (default: 500)"
    )
    
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility (default: random)"
    )
    
    parser.add_argument(
        "--tile-size", "-t",
        type=int,
        default=40,
        help="Tile size in pixels (default: 40)"
    )
    
    parser.add_argument(
        "--no-objects",
        action="store_true",
        help="Don't generate objects"
    )
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting world generation...")
    logger.info(f"Size: {args.size}x{args.size}")
    logger.info(f"Seed: {args.seed or 'random'}")
    
    try:
        # Generate world using the new MapGenerator
        generator = MapGenerator(
            width=args.size,
            height=args.size,
            seed=args.seed,
            tile_size=args.tile_size
        )
        
        map_data = generator.generate(create_objects=not args.no_objects)
        generator.save_to_file(args.output, map_data)
        
        # Also save objects separately for server loading
        if not args.no_objects:
            objects_data = {
                'objects': [
                    {
                        'object_id': f"obj_{i}",
                        'x': obj.x,
                        'y': obj.y,
                        'object_type': obj.object_type,
                        'collidable': obj.collidable,
                    }
                    for i, obj in enumerate(generator.world.objects.values())
                ]
            }
            
            os.makedirs(os.path.dirname(args.objects_output), exist_ok=True)
            import json
            with open(args.objects_output, 'w') as f:
                json.dump(objects_data, f, indent=2)
            logger.info(f"Objects saved to {args.objects_output}")
        
        logger.info("World generation completed successfully!")
        return 0
        
    except Exception as e:
        logger.error(f"World generation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
