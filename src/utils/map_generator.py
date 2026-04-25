#!/usr/bin/env python3
"""
Ferramenta de geração procedural de mapas para MMORPG.

Este script gera mapas procedurais usando algoritmos de noise (Perlin/Simplex)
e cria estruturas como dungeons, cidades e áreas naturais.

Dependências:
    - numpy>=1.20.0
    - noise>=1.2.0 (opcional, para noise Perlin/Simplex)
    
Uso:
    python -m tools.map_generator --output maps/world_map.json --size 500
    
Autor: MMORPG Engine Team
"""

import argparse
import json
import math
import os
import random
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set

try:
    import numpy as np
except ImportError:
    print("Aviso: numpy não está instalado. Usando implementação fallback de noise.")
    print("Para melhor desempenho, instale: pip install numpy noise")
    np = None

try:
    from noise import pnoise2
except ImportError:
    pnoise2 = None


class NoiseGenerator:
    """Gerador de noise procedural para terreno."""
    
    def __init__(self, seed: int = None, octaves: int = 6, persistence: float = 0.5,
                 lacunarity: float = 2.0, scale: float = 100.0):
        """
        Inicializa o gerador de noise.
        
        Args:
            seed: Seed aleatória para reprodutibilidade.
            octaves: Número de oitavas de noise (detalhe).
            persistence: Persistência do noise (amplitude decrescente).
            lacunarity: Lacunaridade do noise (frequência crescente).
            scale: Escala do noise (quanto maior, mais suave).
        """
        self.seed = seed if seed is not None else random.randint(0, 10000)
        self.octaves = octaves
        self.persistence = persistence
        self.lacunarity = lacunarity
        self.scale = scale
        
    def generate_heightmap(self, width: int, height: int, 
                          offset_x: float = 0.0, offset_y: float = 0.0) -> np.ndarray:
        """
        Gera um heightmap usando noise Perlin/Simplex.
        
        Args:
            width: Largura do mapa em tiles.
            height: Altura do mapa em tiles.
            offset_x: Offset no eixo X para variação.
            offset_y: Offset no eixo Y para variação.
            
        Returns:
            Array 2D com valores de altura normalizados (0.0 a 1.0).
        """
        heightmap = np.zeros((height, width), dtype=np.float32)
        
        for y in range(height):
            for x in range(width):
                # Calcula noise em múltiplas oitavas
                value = 0.0
                amplitude = 1.0
                frequency = 1.0
                max_value = 0.0
                
                for _ in range(self.octaves):
                    nx = (x + offset_x) / self.scale * frequency
                    ny = (y + offset_y) / self.scale * frequency
                    
                    if pnoise2 is not None:
                        # Usa biblioteca noise externa
                        # Parâmetros corretos: repeatx e repeaty (minúsculas)
                        value += pnoise2(nx, ny, octaves=1, repeatx=1024, repeaty=1024) * amplitude
                    else:
                        # Fallback: noise simples baseado em seno/cosseno
                        value += self._simple_noise(nx, ny) * amplitude
                    
                    max_value += amplitude
                    amplitude *= self.persistence
                    frequency *= self.lacunarity
                
                # Normaliza para 0.0 a 1.0
                heightmap[y, x] = (value / max_value + 1.0) / 2.0
        
        return heightmap
    
    def _simple_noise(self, x: float, y: float) -> float:
        """
        Implementação fallback de noise simples.
        
        Args:
            x: Coordenada X.
            y: Coordenada Y.
            
        Returns:
            Valor de noise entre -1.0 e 1.0.
        """
        # Combina múltiplas funções seno/cosseno para simular noise
        value = math.sin(x * 12.9898 + y * 78.233) * 43758.5453
        value -= math.floor(value)
        value *= 2.0 - 1.0
        return value


class TerrainType:
    """Tipos de terreno com suas propriedades."""
    
    # IDs de terrain
    WATER_DEEP = 0
    WATER_SHALLOW = 1
    SAND = 2
    GRASS = 3
    FOREST = 4
    DIRT = 5
    STONE = 6
    SNOW = 7
    LAVA = 8
    
    # Mapeamento de altura para tipo de terreno
    HEIGHT_THRESHOLDS = {
        0.0: WATER_DEEP,
        0.2: WATER_SHALLOW,
        0.25: SAND,
        0.35: GRASS,
        0.55: FOREST,
        0.7: DIRT,
        0.85: STONE,
        0.95: SNOW,
    }
    
    @classmethod
    def get_from_height(cls, height: float, moisture: float = 0.5) -> int:
        """
        Determina o tipo de terreno baseado na altura e umidade.
        
        Args:
            height: Valor de altura (0.0 a 1.0).
            moisture: Valor de umidade (0.0 a 1.0).
            
        Returns:
            ID do tipo de terreno.
        """
        terrain = cls.GRASS
        
        for threshold, terrain_type in sorted(cls.HEIGHT_THRESHOLDS.items()):
            if height >= threshold:
                terrain = terrain_type
            else:
                break
        
        # Ajustes baseados na umidade
        if 0.35 <= height < 0.55:
            if moisture > 0.7:
                terrain = cls.FOREST
            elif moisture < 0.3:
                terrain = cls.DIRT
        
        return terrain


class MapGenerator:
    """Gerador de mapas procedurais para MMORPG."""
    
    def __init__(self, width: int = 500, height: int = 500, 
                 seed: int = None, tile_size: int = 40):
        """
        Inicializa o gerador de mapas.
        
        Args:
            width: Largura do mapa em tiles.
            height: Altura do mapa em tiles.
            seed: Seed aleatória para reprodutibilidade.
            tile_size: Tamanho de cada tile em pixels.
        """
        self.width = width
        self.height = height
        self.seed = seed if seed is not None else random.randint(0, 10000)
        self.tile_size = tile_size
        
        # Inicializa geradores de noise
        self.height_noise = NoiseGenerator(seed=self.seed, scale=80.0)
        self.moisture_noise = NoiseGenerator(seed=self.seed + 1, scale=100.0)
        self.detail_noise = NoiseGenerator(seed=self.seed + 2, scale=40.0, octaves=4)
        
        # Armazena dados do mapa
        self.tilemap: List[List[int]] = []
        self.objectmap: List[List[Optional[Dict[str, Any]]]] = []
        self.spawn_points: List[Dict[str, Any]] = []
        self.structures: List[Dict[str, Any]] = []
        
    def generate(self, create_objects: bool = True) -> Dict[str, Any]:
        """
        Gera o mapa completo.
        
        Args:
            create_objects: Se True, cria objetos e estruturas no mapa.
            
        Returns:
            Dicionário com todos os dados do mapa.
        """
        print(f"Gerando mapa {self.width}x{self.height} com seed {self.seed}...")
        
        # Gera heightmap e moisture map
        heightmap = self.height_noise.generate_heightmap(self.width, self.height)
        moisture_map = self.moisture_noise.generate_heightmap(self.width, self.height)
        detail_map = self.detail_noise.generate_heightmap(self.width, self.height)
        
        # Gera tilemap baseado nos maps de noise
        self._generate_tilemap(heightmap, moisture_map, detail_map)
        
        # Gera objetos se solicitado
        if create_objects:
            print("Gerando objetos e estruturas...")
            self._generate_objects(heightmap, moisture_map)
            self._generate_structures(heightmap)
            self._generate_spawn_points(heightmap)
        
        # Compila dados finais
        map_data = {
            'metadata': {
                'width': self.width,
                'height': self.height,
                'tile_size': self.tile_size,
                'seed': self.seed,
                'generated_at': str(__import__('datetime').datetime.now()),
                'version': '1.0'
            },
            'tilemap': self.tilemap,
            'objectmap': self.objectmap,
            'spawn_points': self.spawn_points,
            'structures': self.structures,
            'terrain_types': {
                'WATER_DEEP': TerrainType.WATER_DEEP,
                'WATER_SHALLOW': TerrainType.WATER_SHALLOW,
                'SAND': TerrainType.SAND,
                'GRASS': TerrainType.GRASS,
                'FOREST': TerrainType.FOREST,
                'DIRT': TerrainType.DIRT,
                'STONE': TerrainType.STONE,
                'SNOW': TerrainType.SNOW,
                'LAVA': TerrainType.LAVA
            }
        }
        
        print(f"Mapa gerado com sucesso!")
        print(f"  - Tiles: {self.width * self.height}")
        print(f"  - Objetos: {sum(1 for row in self.objectmap for obj in row if obj is not None)}")
        print(f"  - Spawn points: {len(self.spawn_points)}")
        print(f"  - Estruturas: {len(self.structures)}")
        
        return map_data
    
    def _generate_tilemap(self, heightmap: np.ndarray, moisture_map: np.ndarray,
                         detail_map: np.ndarray) -> None:
        """
        Gera o tilemap baseado nos maps de noise.
        
        Args:
            heightmap: Array 2D de alturas.
            moisture_map: Array 2D de umidade.
            detail_map: Array 2D de detalhes.
        """
        self.tilemap = []
        
        for y in range(self.height):
            row = []
            for x in range(self.width):
                height = heightmap[y, x]
                moisture = moisture_map[y, x]
                detail = detail_map[y, x]
                
                # Determina tipo de terreno base
                terrain = TerrainType.get_from_height(height, moisture)
                
                # Adiciona variação baseada no detail map
                if terrain == TerrainType.GRASS and detail > 0.7:
                    terrain = TerrainType.FOREST
                elif terrain == TerrainType.STONE and detail < 0.3:
                    terrain = TerrainType.DIRT
                
                row.append(terrain)
            
            self.tilemap.append(row)
    
    def _generate_objects(self, heightmap: np.ndarray, moisture_map: np.ndarray) -> None:
        """
        Gera objetos no mapa (árvores, rochas, etc.).
        
        Args:
            heightmap: Array 2D de alturas.
            moisture_map: Array 2D de umidade.
        """
        self.objectmap = [[None for _ in range(self.width)] for _ in range(self.height)]
        
        object_types = {
            TerrainType.FOREST: ['tree_small', 'tree_large', 'tree_autumn', 'bush', 'mushroom'],
            TerrainType.GRASS: ['flower', 'bush', 'rock_small'],
            TerrainType.STONE: ['rock_small', 'rock_large'],
            TerrainType.SAND: ['rock_small'],
            TerrainType.DIRT: ['rock_small', 'bush'],
        }
        
        for y in range(self.height):
            for x in range(self.width):
                terrain = self.tilemap[y][x]
                
                # Probabilidade de spawn baseada no terreno
                spawn_chance = {
                    TerrainType.FOREST: 0.4,
                    TerrainType.GRASS: 0.15,
                    TerrainType.STONE: 0.2,
                    TerrainType.SAND: 0.05,
                    TerrainType.DIRT: 0.1,
                }.get(terrain, 0.0)
                
                if random.random() < spawn_chance:
                    available_objects = object_types.get(terrain, [])
                    if available_objects:
                        obj_type = random.choice(available_objects)
                        self.objectmap[y][x] = {
                            'type': obj_type,
                            'variant': random.randint(0, 2),
                            'interactive': False
                        }
    
    def _generate_structures(self, heightmap: np.ndarray) -> None:
        """
        Gera estruturas como casas, dungeons, etc.
        
        Args:
            heightmap: Array 2D de alturas.
        """
        self.structures = []
        
        # Encontra áreas planas adequadas para construções
        flat_areas = []
        for y in range(50, self.height - 50, 20):
            for x in range(50, self.width - 50, 20):
                # Verifica se a área é plana e de terreno adequado
                region = heightmap[y:y+10, x:x+10]
                if region.std() < 0.05:  # Área plana
                    terrain = self.tilemap[y][x]
                    if terrain in [TerrainType.GRASS, TerrainType.DIRT]:
                        flat_areas.append((x, y))
        
        # Seleciona algumas áreas para estruturas
        num_structures = min(10, len(flat_areas) // 5)
        selected_areas = random.sample(flat_areas, min(num_structures, len(flat_areas)))
        
        structure_types = ['house', 'tower', 'well', 'bridge']
        
        for x, y in selected_areas:
            struct_type = random.choice(structure_types)
            self.structures.append({
                'type': struct_type,
                'x': x,
                'y': y,
                'width': 3 if struct_type == 'house' else 2,
                'height': 3 if struct_type == 'house' else 2,
                'rotation': random.choice([0, 90, 180, 270]),
                'interior': struct_type == 'house'
            })
    
    def _generate_spawn_points(self, heightmap: np.ndarray) -> None:
        """
        Gera pontos de spawn para jogadores.
        
        Args:
            heightmap: Array 2D de alturas.
        """
        self.spawn_points = []
        
        # Encontra áreas seguras para spawn (grama, plano, longe da água)
        safe_spawns = []
        for y in range(20, self.height - 20, 10):
            for x in range(20, self.width - 20, 10):
                terrain = self.tilemap[y][x]
                height = heightmap[y, x]
                
                # Verifica se é seguro
                if terrain in [TerrainType.GRASS, TerrainType.DIRT]:
                    if 0.3 < height < 0.7:  # Não muito baixo (água) nem muito alto (montanha)
                        # Verifica arredores
                        safe = True
                        for dy in range(-3, 4):
                            for dx in range(-3, 4):
                                ny, nx = y + dy, x + dx
                                if 0 <= ny < self.height and 0 <= nx < self.width:
                                    neighbor_terrain = self.tilemap[ny][nx]
                                    if neighbor_terrain in [TerrainType.WATER_DEEP, TerrainType.WATER_SHALLOW]:
                                        safe = False
                                        break
                            if not safe:
                                break
                        
                        if safe:
                            safe_spawns.append((x, y))
        
        # Seleciona 5 pontos de spawn principais
        num_spawns = min(5, len(safe_spawns))
        if safe_spawns:
            selected_spawns = random.sample(safe_spawns, num_spawns)
            for i, (x, y) in enumerate(selected_spawns):
                self.spawn_points.append({
                    'id': i,
                    'x': x,
                    'y': y,
                    'name': f'Spawn Point {i + 1}',
                    'is_main': i == 0  # Primeiro spawn é o principal
                })
    
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
        
        file_size = output_path.stat().st_size / (1024 * 1024)  # MB
        print(f"Mapa salvo em: {filepath} ({file_size:.2f} MB)")
    
    def load_from_file(self, filepath: str) -> Dict[str, Any]:
        """
        Carrega dados do mapa de arquivo JSON.
        
        Args:
            filepath: Caminho do arquivo de entrada.
            
        Returns:
            Dados do mapa carregados.
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            map_data = json.load(f)
        
        # Restaura atributos
        self.width = map_data['metadata']['width']
        self.height = map_data['metadata']['height']
        self.tile_size = map_data['metadata']['tile_size']
        self.seed = map_data['metadata']['seed']
        self.tilemap = map_data['tilemap']
        self.objectmap = map_data['objectmap']
        self.spawn_points = map_data['spawn_points']
        self.structures = map_data.get('structures', [])
        
        print(f"Mapa carregado de: {filepath}")
        print(f"  - Dimensões: {self.width}x{self.height}")
        print(f"  - Seed: {self.seed}")
        
        return map_data


def main():
    """Função principal do gerador de mapas."""
    parser = argparse.ArgumentParser(
        description='Gerador procedural de mapas para MMORPG',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python -m tools.map_generator --output maps/world_map.json
  python -m tools.map_generator --output maps/world_map.json --size 500 --seed 12345
  python -m tools.map_generator --load maps/world_map.json --validate
        """
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='maps/world_map.json',
        help='Caminho do arquivo de saída (padrão: maps/world_map.json)'
    )
    
    parser.add_argument(
        '--size', '-s',
        type=int,
        default=500,
        help='Tamanho do mapa (largura e altura) em tiles (padrão: 500)'
    )
    
    parser.add_argument(
        '--seed',
        type=int,
        default=None,
        help='Seed aleatória para reprodutibilidade (padrão: aleatória)'
    )
    
    parser.add_argument(
        '--tile-size', '-t',
        type=int,
        default=40,
        help='Tamanho do tile em pixels (padrão: 40)'
    )
    
    parser.add_argument(
        '--no-objects',
        action='store_true',
        help='Não gerar objetos no mapa'
    )
    
    parser.add_argument(
        '--load', '-l',
        type=str,
        default=None,
        help='Carregar mapa existente para validação ou processamento'
    )
    
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validar integridade do mapa carregado'
    )
    
    args = parser.parse_args()
    
    try:
        if args.load:
            # Carrega mapa existente
            generator = MapGenerator(tile_size=args.tile_size)
            map_data = generator.load_from_file(args.load)
            
            if args.validate:
                print("\nValidando mapa...")
                errors = []
                
                # Valida dimensões
                if len(map_data['tilemap']) != map_data['metadata']['height']:
                    errors.append("Altura do tilemap incorreta")
                
                if any(len(row) != map_data['metadata']['width'] for row in map_data['tilemap']):
                    errors.append("Largura do tilemap inconsistente")
                
                # Valida spawn points
                for spawn in map_data['spawn_points']:
                    x, y = spawn['x'], spawn['y']
                    if not (0 <= x < map_data['metadata']['width'] and 
                           0 <= y < map_data['metadata']['height']):
                        errors.append(f"Spawn point fora dos limites: ({x}, {y})")
                
                if errors:
                    print("Erros encontrados:")
                    for error in errors:
                        print(f"  - {error}")
                    return 1
                else:
                    print("Mapa válido!")
            
            return 0
        
        else:
            # Gera novo mapa
            generator = MapGenerator(
                width=args.size,
                height=args.size,
                seed=args.seed,
                tile_size=args.tile_size
            )
            
            map_data = generator.generate(create_objects=not args.no_objects)
            generator.save_to_file(args.output, map_data)
            
            print("\nGeração concluída com sucesso!")
            return 0
    
    except Exception as e:
        print(f"Erro ao gerar/carregar mapa: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
