#!/usr/bin/env python3
"""
Ferramenta de conversão de mapas Tiled (TMX/JSON) para o formato do MMORPG.

Este script importa mapas criados no editor Tiled e os converte para o formato
JSON utilizado pelo servidor e cliente do MMORPG.

Dependências:
    - pytmx>=1.7.0 (para carregar arquivos TMX)
    
Uso:
    python -m tools.tiled_importer --input maps/world.tmx --output maps/world_map.json
    
Autor: MMORPG Engine Team
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

# Tenta importar pytmx
try:
    from pytmx import load_pygame, TiledObject
    PYTMX_AVAILABLE = True
except ImportError:
    PYTMM_AVAILABLE = False
    print("Aviso: pytmx não está instalado.")
    print("Para importar mapas TMX, instale: pip install pytmx")
    print("Continuando com suporte apenas para JSON do Tiled...")


class TiledImporter:
    """Importador de mapas do editor Tiled."""
    
    # Mapeamento de tipos de terreno do Tiled para IDs do jogo
    TERRAIN_MAPPING = {
        'water_deep': 0,
        'water_shallow': 1,
        'sand': 2,
        'grass': 3,
        'forest': 4,
        'dirt': 5,
        'stone': 6,
        'snow': 7,
        'lava': 8,
    }
    
    # Mapeamento de tipos de objetos
    OBJECT_MAPPING = {
        'tree_small': 'tree_small',
        'tree_large': 'tree_large',
        'tree_autumn': 'tree_autumn',
        'rock_small': 'rock_small',
        'rock_large': 'rock_large',
        'flower': 'flower',
        'mushroom': 'mushroom',
        'bush': 'bush',
        'house': 'house',
        'tower': 'tower',
        'well': 'well',
        'bridge': 'bridge',
        'spawn_point': 'spawn_point',
    }
    
    def __init__(self):
        """Inicializa o importador."""
        self.tilemap: List[List[int]] = []
        self.objectmap: List[List[Optional[Dict[str, Any]]]] = []
        self.spawn_points: List[Dict[str, Any]] = []
        self.structures: List[Dict[str, Any]] = []
        self.width: int = 0
        self.height: int = 0
        self.tile_size: int = 40
        
    def import_tmx(self, filepath: str) -> Dict[str, Any]:
        """
        Importa um mapa no formato TMX do Tiled.
        
        Args:
            filepath: Caminho do arquivo TMX.
            
        Returns:
            Dicionário com os dados do mapa convertidos.
            
        Raises:
            ImportError: Se pytmx não estiver disponível.
        """
        if not PYTMX_AVAILABLE:
            raise ImportError("pytmx é necessário para importar arquivos TMX")
        
        print(f"Importando mapa TMX: {filepath}")
        
        # Carrega o mapa TMX
        tmx_data = load_pygame(filepath)
        
        self.width = tmx_data.width
        self.height = tmx_data.height
        self.tile_size = tmx_data.tilewidth  # Assume tile quadrado
        
        print(f"Dimensões do mapa: {self.width}x{self.height}")
        print(f"Tamanho do tile: {self.tile_size}px")
        
        # Inicializa mapas vazios
        self.tilemap = [[0 for _ in range(self.width)] for _ in range(self.height)]
        self.objectmap = [[None for _ in range(self.width)] for _ in range(self.height)]
        
        # Processa camadas de tile
        for layer in tmx_data.layers:
            if hasattr(layer, 'tiles'):  # Camada de tiles
                self._process_tile_layer(layer, tmx_data)
            elif hasattr(layer, 'objects'):  # Camada de objetos
                self._process_object_layer(layer)
        
        # Compila dados finais
        map_data = {
            'metadata': {
                'width': self.width,
                'height': self.height,
                'tile_size': self.tile_size,
                'source': filepath,
                'imported_at': str(__import__('datetime').datetime.now()),
                'version': '1.0'
            },
            'tilemap': self.tilemap,
            'objectmap': self.objectmap,
            'spawn_points': self.spawn_points,
            'structures': self.structures,
            'terrain_types': {
                'WATER_DEEP': 0,
                'WATER_SHALLOW': 1,
                'SAND': 2,
                'GRASS': 3,
                'FOREST': 4,
                'DIRT': 5,
                'STONE': 6,
                'SNOW': 7,
                'LAVA': 8
            }
        }
        
        print(f"Mapa importado com sucesso!")
        print(f"  - Tiles: {self.width * self.height}")
        print(f"  - Objetos: {sum(1 for row in self.objectmap for obj in row if obj is not None)}")
        print(f"  - Spawn points: {len(self.spawn_points)}")
        
        return map_data
    
    def import_json(self, filepath: str) -> Dict[str, Any]:
        """
        Importa um mapa no formato JSON exportado pelo Tiled.
        
        Args:
            filepath: Caminho do arquivo JSON.
            
        Returns:
            Dicionário com os dados do mapa convertidos.
        """
        print(f"Importando mapa JSON do Tiled: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            tiled_data = json.load(f)
        
        self.width = tiled_data['width']
        self.height = tiled_data['height']
        self.tile_size = tiled_data['tilewidth']
        
        print(f"Dimensões do mapa: {self.width}x{self.height}")
        print(f"Tamanho do tile: {self.tile_size}px")
        
        # Inicializa mapas vazios
        self.tilemap = [[0 for _ in range(self.width)] for _ in range(self.height)]
        self.objectmap = [[None for _ in range(self.width)] for _ in range(self.height)]
        
        # Processa camadas
        for layer in tiled_data['layers']:
            if layer['type'] == 'tilelayer':
                self._process_json_tile_layer(layer)
            elif layer['type'] == 'objectgroup':
                self._process_json_object_layer(layer)
        
        # Compila dados finais
        map_data = {
            'metadata': {
                'width': self.width,
                'height': self.height,
                'tile_size': self.tile_size,
                'source': filepath,
                'imported_at': str(__import__('datetime').datetime.now()),
                'version': '1.0'
            },
            'tilemap': self.tilemap,
            'objectmap': self.objectmap,
            'spawn_points': self.spawn_points,
            'structures': self.structures,
            'terrain_types': {
                'WATER_DEEP': 0,
                'WATER_SHALLOW': 1,
                'SAND': 2,
                'GRASS': 3,
                'FOREST': 4,
                'DIRT': 5,
                'STONE': 6,
                'SNOW': 7,
                'LAVA': 8
            }
        }
        
        print(f"Mapa importado com sucesso!")
        return map_data
    
    def _process_tile_layer(self, layer, tmx_data) -> None:
        """
        Processa uma camada de tiles do TMX.
        
        Args:
            layer: Camada de tiles do pytmx.
            tmx_data: Dados completos do mapa TMX.
        """
        for y in range(self.height):
            for x in range(self.width):
                tile_gid = layer.tiles[y][x][0]
                
                if tile_gid > 0:
                    # Tenta determinar o tipo de terreno baseado no GID
                    try:
                        tile_data = tmx_data.get_tile_image(x, y, layer.id)
                        # Usa propriedades do tile se disponíveis
                        if hasattr(tmx_data, 'tile_properties'):
                            props = tmx_data.tile_properties.get(tile_gid, {})
                            terrain_type = props.get('terrain', 'grass')
                            self.tilemap[y][x] = self.TERRAIN_MAPPING.get(terrain_type, 3)
                    except:
                        # Fallback: usa grama como padrão
                        self.tilemap[y][x] = 3
                else:
                    self.tilemap[y][x] = 3  # Grama como padrão
    
    def _process_object_layer(self, layer) -> None:
        """
        Processa uma camada de objetos do TMX.
        
        Args:
            layer: Camada de objetos do pytmx.
        """
        for obj in layer.objects:
            x = int(obj.x // self.tile_size)
            y = int(obj.y // self.tile_size)
            
            obj_type = obj.type.lower() if obj.type else 'unknown'
            
            if obj_type in self.OBJECT_MAPPING:
                mapped_type = self.OBJECT_MAPPING[obj_type]
                
                if mapped_type == 'spawn_point':
                    # Adiciona ponto de spawn
                    self.spawn_points.append({
                        'id': len(self.spawn_points),
                        'x': x,
                        'y': y,
                        'name': obj.name or f'Spawn {len(self.spawn_points)}',
                        'is_main': len(self.spawn_points) == 0
                    })
                elif mapped_type in ['house', 'tower', 'well', 'bridge']:
                    # Adiciona estrutura
                    self.structures.append({
                        'type': mapped_type,
                        'x': x,
                        'y': y,
                        'width': int(obj.width // self.tile_size) if obj.width > 0 else 2,
                        'height': int(obj.height // self.tile_size) if obj.height > 0 else 2,
                        'rotation': 0,
                        'interior': mapped_type == 'house'
                    })
                else:
                    # Adiciona objeto normal
                    if 0 <= x < self.width and 0 <= y < self.height:
                        self.objectmap[y][x] = {
                            'type': mapped_type,
                            'variant': 0,
                            'interactive': obj_type in ['well', 'chest', 'door']
                        }
    
    def _process_json_tile_layer(self, layer: Dict[str, Any]) -> None:
        """
        Processa uma camada de tiles do JSON do Tiled.
        
        Args:
            layer: Dados da camada de tiles.
        """
        data = layer['data']
        for i, tile_gid in enumerate(data):
            x = i % self.width
            y = i // self.width
            
            if tile_gid > 0:
                # Tenta obter propriedades do tile
                if 'tiles' in layer and i < len(layer['tiles']):
                    tile_info = layer['tiles'][i]
                    if isinstance(tile_info, dict):
                        props = tile_info.get('properties', {})
                        terrain_type = props.get('terrain', 'grass')
                        self.tilemap[y][x] = self.TERRAIN_MAPPING.get(terrain_type, 3)
                    else:
                        self.tilemap[y][x] = 3
                else:
                    self.tilemap[y][x] = 3  # Grama como padrão
            else:
                self.tilemap[y][x] = 3
    
    def _process_json_object_layer(self, layer: Dict[str, Any]) -> None:
        """
        Processa uma camada de objetos do JSON do Tiled.
        
        Args:
            layer: Dados da camada de objetos.
        """
        for obj in layer.get('objects', []):
            x = int(obj['x'] // self.tile_size)
            y = int(obj['y'] // self.tile_size)
            
            obj_type = obj.get('type', '').lower()
            obj_name = obj.get('name', '')
            
            if obj_type in self.OBJECT_MAPPING:
                mapped_type = self.OBJECT_MAPPING[obj_type]
                
                if mapped_type == 'spawn_point':
                    self.spawn_points.append({
                        'id': len(self.spawn_points),
                        'x': x,
                        'y': y,
                        'name': obj_name or f'Spawn {len(self.spawn_points)}',
                        'is_main': len(self.spawn_points) == 0
                    })
                elif mapped_type in ['house', 'tower', 'well', 'bridge']:
                    width = obj.get('width', 0)
                    height = obj.get('height', 0)
                    self.structures.append({
                        'type': mapped_type,
                        'x': x,
                        'y': y,
                        'width': int(width // self.tile_size) if width > 0 else 2,
                        'height': int(height // self.tile_size) if height > 0 else 2,
                        'rotation': obj.get('rotation', 0),
                        'interior': mapped_type == 'house'
                    })
                else:
                    if 0 <= x < self.width and 0 <= y < self.height:
                        self.objectmap[y][x] = {
                            'type': mapped_type,
                            'variant': 0,
                            'interactive': obj_type in ['well', 'chest', 'door']
                        }
    
    def save_to_file(self, filepath: str, map_data: Dict[str, Any]) -> None:
        """
        Salva os dados do mapa em arquivo JSON.
        
        Args:
            filepath: Caminho do arquivo de saída.
            map_data: Dados do mapa a serem salvos.
        """
        output_path = Path(filepath)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(map_data, f, indent=2)
        
        file_size = output_path.stat().st_size / (1024 * 1024)
        print(f"Mapa salvo em: {filepath} ({file_size:.2f} MB)")


def main():
    """Função principal do importador."""
    parser = argparse.ArgumentParser(
        description='Importador de mapas do Tiled (TMX/JSON) para MMORPG',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python -m tools.tiled_importer --input maps/world.tmx --output maps/world_map.json
  python -m tools.tiled_importer --input maps/world.json --output maps/world_map.json
  
Dicas:
  - No Tiled, use propriedades personalizadas nos tiles para definir o tipo de terreno
  - Crie camadas separadas para terreno, objetos e spawns
  - Use os seguintes tipos de objeto: tree_*, rock_*, flower, house, tower, spawn_point
        """
    )
    
    parser.add_argument(
        '--input', '-i',
        type=str,
        required=True,
        help='Caminho do arquivo de entrada (TMX ou JSON)'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='maps/imported_map.json',
        help='Caminho do arquivo de saída (padrão: maps/imported_map.json)'
    )
    
    args = parser.parse_args()
    
    try:
        importer = TiledImporter()
        input_path = Path(args.input)
        
        if input_path.suffix.lower() == '.tmx':
            map_data = importer.import_tmx(args.input)
        elif input_path.suffix.lower() == '.json':
            map_data = importer.import_json(args.input)
        else:
            print(f"Erro: Formato de arquivo não suportado: {input_path.suffix}")
            print("Use .tmx ou .json")
            return 1
        
        importer.save_to_file(args.output, map_data)
        print("\nImportação concluída com sucesso!")
        return 0
        
    except ImportError as e:
        print(f"Erro de importação: {e}")
        return 1
    except Exception as e:
        print(f"Erro ao importar mapa: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
