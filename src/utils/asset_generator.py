#!/usr/bin/env python3
"""
Ferramenta de geração de assets visuais para o MMORPG.

Este script gera programaticamente todos os sprites, tiles e elementos
de UI necessários para o jogo, criando spritesheets otimizados.

Dependências:
    - pygame>=2.5.0
    
Uso:
    python -m tools.asset_generator --output assets/sprites
    
Autor: MMORPG Engine Team
"""

import argparse
import json
import math
import os
import random
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

try:
    import pygame
except ImportError:
    print("Erro: pygame não está instalado.")
    print("Instale com: pip install pygame")
    sys.exit(1)


class ColorPalette:
    """Paletas de cores pré-definidas para diferentes biomas e estilos."""
    
    # Cores base para terreno
    GRASS_LIGHT = (144, 238, 144)
    GRASS_DARK = (34, 139, 34)
    WATER_SHALLOW = (173, 216, 230)
    WATER_DEEP = (65, 105, 225)
    DIRT = (139, 69, 19)
    DIRT_DARK = (101, 67, 33)
    STONE_LIGHT = (169, 169, 169)
    STONE_DARK = (105, 105, 105)
    SAND = (245, 245, 220)
    SNOW = (255, 250, 250)
    
    # Cores para objetos
    WOOD_TRUNK = (101, 67, 33)
    WOOD_LEAVES = (34, 139, 34)
    WOOD_LEAVES_AUTUMN = (255, 140, 0)
    ROCK_GRAY = (128, 128, 128)
    ROCK_BROWN = (139, 90, 43)
    
    # Cores para construções
    ROOF_RED = (178, 34, 34)
    ROOF_BROWN = (101, 67, 33)
    WALL_WHITE = (245, 245, 245)
    WALL_WOOD = (210, 180, 140)
    DOOR = (101, 67, 33)
    WINDOW = (135, 206, 250)
    
    # Cores para personagens
    SKIN_LIGHT = (255, 224, 189)
    SKIN_MEDIUM = (210, 180, 140)
    SKIN_DARK = (139, 69, 19)
    HAIR_BLACK = (0, 0, 0)
    HAIR_BROWN = (101, 67, 33)
    HAIR_BLONDE = (255, 215, 0)
    HAIR_RED = (178, 34, 34)
    
    # Cores para UI
    UI_BACKGROUND = (40, 40, 40)
    UI_BORDER = (100, 100, 100)
    UI_TEXT = (255, 255, 255)
    UI_HIGHLIGHT = (255, 215, 0)
    UI_HEALTH = (220, 20, 60)
    UI_MANA = (65, 105, 225)
    UI_XP = (255, 215, 0)


class AssetGenerator:
    """Gerador de assets visuais para o MMORPG."""
    
    def __init__(self, tile_size: int = 40):
        """
        Inicializa o gerador de assets.
        
        Args:
            tile_size: Tamanho de cada tile em pixels (padrão: 40).
        """
        self.tile_size = tile_size
        self.sprites: Dict[str, pygame.Surface] = {}
        self.tilesets: Dict[str, Dict[str, pygame.Surface]] = {}
        self.ui_elements: Dict[str, pygame.Surface] = {}
        
        # Inicializa pygame
        if not pygame.get_init():
            pygame.init()
        
        # Cria superfície temporária para desenho
        self.temp_surface = pygame.Surface((tile_size, tile_size))
        
    def generate_terrain_tiles(self) -> Dict[str, pygame.Surface]:
        """
        Gera tiles de terreno básicos.
        
        Returns:
            Dicionário com nomes dos tiles e suas superfícies.
        """
        tiles = {}
        ts = self.tile_size
        
        # Grama (variações)
        for i in range(4):
            surface = pygame.Surface((ts, ts))
            surface.fill(ColorPalette.GRASS_LIGHT)
            
            # Adiciona detalhes de grama
            for _ in range(15 + i * 5):
                x = (random.randint(0, ts - 4), random.randint(0, ts - 4))
                color_var = max(50, ColorPalette.GRASS_DARK[0] - i * 10)
                grass_color = (
                    color_var,
                    min(200, ColorPalette.GRASS_DARK[1] + i * 5),
                    color_var // 2
                )
                pygame.draw.rect(surface, grass_color, (x[0], x[1], 3, 3))
            
            tiles[f'grass_{i}'] = surface
        
        # Água (variações de profundidade)
        for i in range(3):
            surface = pygame.Surface((ts, ts))
            color = ColorPalette.WATER_SHALLOW if i == 0 else ColorPalette.WATER_DEEP
            surface.fill(color)
            
            # Adiciona ondulações
            for wave in range(3):
                y_offset = ts // 3 * wave + ts // 6
                pygame.draw.line(
                    surface,
                    (min(255, color[0] + 30), min(255, color[1] + 30), min(255, color[2] + 30)),
                    (5, y_offset),
                    (ts - 5, y_offset),
                    2
                )
            
            tiles[f'water_{i}'] = surface
        
        # Terra
        for i in range(3):
            surface = pygame.Surface((ts, ts))
            surface.fill(ColorPalette.DIRT)
            
            # Adiciona pedras e textura
            for _ in range(10 + i * 5):
                x = random.randint(0, ts - 5)
                y = random.randint(0, ts - 5)
                size = random.randint(2, 5)
                color = ColorPalette.DIRT_DARK if random.random() > 0.5 else ColorPalette.STONE_LIGHT
                pygame.draw.circle(surface, color, (x, y), size)
            
            tiles[f'dirt_{i}'] = surface
        
        # Pedra
        for i in range(3):
            surface = pygame.Surface((ts, ts))
            surface.fill(ColorPalette.STONE_LIGHT)
            
            # Adiciona rachaduras e detalhes
            for _ in range(8):
                start = (random.randint(0, ts), random.randint(0, ts))
                end = (
                    start[0] + random.randint(-10, 10),
                    start[1] + random.randint(-10, 10)
                )
                pygame.draw.line(surface, ColorPalette.STONE_DARK, start, end, 1)
            
            tiles[f'stone_{i}'] = surface
        
        # Areia
        surface = pygame.Surface((ts, ts))
        surface.fill(ColorPalette.SAND)
        for _ in range(20):
            x = random.randint(0, ts - 2)
            y = random.randint(0, ts - 2)
            pygame.draw.circle(surface, ColorPalette.DIRT, (x, y), 1)
        tiles['sand'] = surface
        
        # Neve
        surface = pygame.Surface((ts, ts))
        surface.fill(ColorPalette.SNOW)
        for _ in range(30):
            x = random.randint(0, ts - 2)
            y = random.randint(0, ts - 2)
            pygame.draw.circle(surface, (200, 200, 255), (x, y), 1)
        tiles['snow'] = surface
        
        return tiles
    
    def generate_object_tiles(self) -> Dict[str, pygame.Surface]:
        """
        Gera tiles de objetos (árvores, rochas, etc.).
        
        Returns:
            Dicionário com nomes dos objetos e suas superfícies.
        """
        objects = {}
        ts = self.tile_size
        
        # Árvore pequena
        tree_small = pygame.Surface((ts, ts), pygame.SRCALPHA)
        # Tronco
        pygame.draw.rect(tree_small, ColorPalette.WOOD_TRUNK, (ts//2 - 4, ts//2, 8, ts//2))
        # Folhas
        pygame.draw.circle(tree_small, ColorPalette.WOOD_LEAVES, (ts//2, ts//2), ts//2 - 5)
        pygame.draw.circle(tree_small, ColorPalette.GRASS_DARK, (ts//2 - 5, ts//2 - 5), 8)
        pygame.draw.circle(tree_small, ColorPalette.GRASS_DARK, (ts//2 + 5, ts//2 - 5), 8)
        objects['tree_small'] = tree_small
        
        # Árvore grande
        tree_large = pygame.Surface((ts, ts), pygame.SRCALPHA)
        # Tronco
        pygame.draw.rect(tree_large, ColorPalette.WOOD_TRUNK, (ts//2 - 6, ts//2, 12, ts//2))
        # Folhas (múltiplos círculos)
        pygame.draw.circle(tree_large, ColorPalette.WOOD_LEAVES, (ts//2, ts//3), ts//2 - 3)
        pygame.draw.circle(tree_large, ColorPalette.WOOD_LEAVES, (ts//2 - 8, ts//2 - 5), 10)
        pygame.draw.circle(tree_large, ColorPalette.WOOD_LEAVES, (ts//2 + 8, ts//2 - 5), 10)
        # Detalhes
        pygame.draw.circle(tree_large, ColorPalette.GRASS_DARK, (ts//2, ts//3 - 5), 5)
        objects['tree_large'] = tree_large
        
        # Árvore outono
        tree_autumn = pygame.Surface((ts, ts), pygame.SRCALPHA)
        pygame.draw.rect(tree_autumn, ColorPalette.WOOD_TRUNK, (ts//2 - 5, ts//2, 10, ts//2))
        pygame.draw.circle(tree_autumn, ColorPalette.WOOD_LEAVES_AUTUMN, (ts//2, ts//2 - 5), ts//2 - 5)
        objects['tree_autumn'] = tree_autumn
        
        # Rocha pequena
        rock_small = pygame.Surface((ts, ts), pygame.SRCALPHA)
        points = [
            (ts//2 - 8, ts - 10),
            (ts//2 - 12, ts - 15),
            (ts//2 - 10, ts - 25),
            (ts//2 - 5, ts - 30),
            (ts//2 + 5, ts - 30),
            (ts//2 + 10, ts - 25),
            (ts//2 + 12, ts - 15),
            (ts//2 + 8, ts - 10)
        ]
        pygame.draw.polygon(rock_small, ColorPalette.ROCK_GRAY, points)
        pygame.draw.polygon(rock_small, ColorPalette.STONE_LIGHT, [
            (ts//2 - 5, ts - 20),
            (ts//2 - 8, ts - 25),
            (ts//2 - 5, ts - 28),
            (ts//2, ts - 28),
            (ts//2 + 5, ts - 25)
        ])
        objects['rock_small'] = rock_small
        
        # Rocha grande
        rock_large = pygame.Surface((ts, ts), pygame.SRCALPHA)
        points = [
            (ts//2 - 15, ts - 8),
            (ts//2 - 18, ts - 15),
            (ts//2 - 15, ts - 28),
            (ts//2 - 8, ts - 35),
            (ts//2, ts - 38),
            (ts//2 + 8, ts - 35),
            (ts//2 + 15, ts - 28),
            (ts//2 + 18, ts - 15),
            (ts//2 + 15, ts - 8)
        ]
        pygame.draw.polygon(rock_large, ColorPalette.ROCK_GRAY, points)
        # Detalhes
        pygame.draw.polygon(rock_large, ColorPalette.STONE_LIGHT, [
            (ts//2 - 8, ts - 20),
            (ts//2 - 12, ts - 25),
            (ts//2 - 8, ts - 30),
            (ts//2, ts - 32),
            (ts//2 + 8, ts - 30),
            (ts//2 + 12, ts - 25),
            (ts//2 + 8, ts - 20)
        ])
        objects['rock_large'] = rock_large
        
        # Flor
        flower = pygame.Surface((ts, ts), pygame.SRCALPHA)
        # Caule
        pygame.draw.line(flower, ColorPalette.GRASS_DARK, (ts//2, ts - 10), (ts//2, ts//2 + 5), 2)
        # Pétalas
        for i in range(5):
            angle = i * 72 * math.pi / 180
            x = ts//2 + int(8 * math.cos(angle))
            y = ts//2 + int(8 * math.sin(angle))
            pygame.draw.circle(flower, (255, 105, 180), (x, y), 4)
        # Centro
        pygame.draw.circle(flower, (255, 255, 0), (ts//2, ts//2), 3)
        objects['flower'] = flower
        
        # Cogumelo
        mushroom = pygame.Surface((ts, ts), pygame.SRCALPHA)
        # Haste
        pygame.draw.rect(mushroom, (255, 255, 240), (ts//2 - 3, ts//2 + 5, 6, ts//2 - 5))
        # Chapéu
        pygame.draw.ellipse(mushroom, (220, 20, 60), (ts//2 - 10, ts//2 - 10, 20, 15))
        # Pontos brancos
        pygame.draw.circle(mushroom, (255, 255, 255), (ts//2 - 5, ts//2 - 5), 2)
        pygame.draw.circle(mushroom, (255, 255, 255), (ts//2 + 5, ts//2 - 5), 2)
        pygame.draw.circle(mushroom, (255, 255, 255), (ts//2, ts//2 - 8), 2)
        objects['mushroom'] = mushroom
        
        # Arbusto
        bush = pygame.Surface((ts, ts), pygame.SRCALPHA)
        pygame.draw.circle(bush, ColorPalette.GRASS_DARK, (ts//2 - 8, ts//2 + 5), 10)
        pygame.draw.circle(bush, ColorPalette.GRASS_DARK, (ts//2 + 8, ts//2 + 5), 10)
        pygame.draw.circle(bush, ColorPalette.GRASS_DARK, (ts//2, ts//2 - 5), 12)
        # Bagas
        for i in range(5):
            x = ts//2 + random.randint(-8, 8)
            y = ts//2 + random.randint(-5, 10)
            pygame.draw.circle(bush, (220, 20, 60), (x, y), 3)
        objects['bush'] = bush
        
        return objects
    
    def generate_building_tiles(self) -> Dict[str, pygame.Surface]:
        """
        Gera tiles de construções (casas, paredes, portas).
        
        Returns:
            Dicionário com nomes dos elementos de construção.
        """
        buildings = {}
        ts = self.tile_size
        
        # Parede de madeira
        wall_wood = pygame.Surface((ts, ts))
        wall_wood.fill(ColorPalette.WALL_WOOD)
        # Tábuas
        for i in range(4):
            y = i * (ts // 4)
            pygame.draw.line(wall_wood, ColorPalette.WOOD_TRUNK, (0, y), (ts, y), 2)
            # Detalhes da madeira
            for j in range(3):
                x = random.randint(0, ts - 10)
                pygame.draw.line(wall_wood, ColorPalette.WOOD_TRUNK, (x, y + 2), (x + 8, y + 2), 1)
        buildings['wall_wood'] = wall_wood
        
        # Parede branca
        wall_white = pygame.Surface((ts, ts))
        wall_white.fill(ColorPalette.WALL_WHITE)
        # Tijolos sutis
        for i in range(3):
            y = i * (ts // 3)
            offset = 0 if i % 2 == 0 else ts // 4
            pygame.draw.line(wall_white, ColorPalette.UI_BORDER, (offset, y), (ts, y), 1)
            for j in range(4):
                x = j * (ts // 4) + offset
                if x < ts:
                    pygame.draw.line(wall_white, ColorPalette.UI_BORDER, (x, y), (x, y + ts // 3), 1)
        buildings['wall_white'] = wall_white
        
        # Telhado vermelho
        roof_red = pygame.Surface((ts, ts))
        roof_red.fill((0, 0, 0, 0))  # Transparente
        # Triângulo do telhado
        points = [(0, 0), (ts, 0), (ts//2, ts)]
        pygame.draw.polygon(roof_red, ColorPalette.ROOF_RED, points)
        # Detalhes das telhas
        for i in range(5):
            y = i * (ts // 5)
            width = ts - (y * 2)
            if width > 0:
                pygame.draw.line(roof_red, (150, 30, 30), (y, y), (ts - y, y), 2)
        buildings['roof_red'] = roof_red
        
        # Telhado marrom
        roof_brown = pygame.Surface((ts, ts))
        roof_brown.fill((0, 0, 0, 0))
        points = [(0, 0), (ts, 0), (ts//2, ts)]
        pygame.draw.polygon(roof_brown, ColorPalette.ROOF_BROWN, points)
        for i in range(5):
            y = i * (ts // 5)
            pygame.draw.line(roof_brown, (80, 50, 30), (y, y), (ts - y, y), 2)
        buildings['roof_brown'] = roof_brown
        
        # Porta
        door = pygame.Surface((ts, ts), pygame.SRCALPHA)
        door.fill((0, 0, 0, 0))
        # Arco da porta
        pygame.draw.arc(door, ColorPalette.DOOR, (5, 0, ts - 10, ts), 0, math.pi, 3)
        # Preenchimento
        pygame.draw.rect(door, ColorPalette.DOOR, (8, ts//2, ts - 16, ts//2))
        # Maçaneta
        pygame.draw.circle(door, (255, 215, 0), (ts - 15, ts//2 + 10), 3)
        buildings['door'] = door
        
        # Janela
        window = pygame.Surface((ts, ts), pygame.SRCALPHA)
        window.fill((0, 0, 0, 0))
        # Moldura
        pygame.draw.rect(window, ColorPalette.WOOD_TRUNK, (5, 5, ts - 10, ts - 10), 3)
        # Vidro
        pygame.draw.rect(window, ColorPalette.WINDOW, (8, 8, ts - 16, ts - 16))
        # Caixilho
        pygame.draw.line(window, ColorPalette.WOOD_TRUNK, (ts//2, 8), (ts//2, ts - 8), 2)
        pygame.draw.line(window, ColorPalette.WOOD_TRUNK, (8, ts//2), (ts - 8, ts//2), 2)
        buildings['window'] = window
        
        # Casa completa (tile único para exemplo)
        house = pygame.Surface((ts * 2, ts * 2), pygame.SRCALPHA)
        # Base
        pygame.draw.rect(house, ColorPalette.WALL_WHITE, (10, ts, ts * 2 - 20, ts - 10))
        # Telhado
        roof_points = [(0, ts), (ts * 2, ts), (ts, 10)]
        pygame.draw.polygon(house, ColorPalette.ROOF_RED, roof_points)
        # Porta
        pygame.draw.rect(house, ColorPalette.DOOR, (ts - 15, ts + 20, 30, ts - 30))
        pygame.draw.circle(house, (255, 215, 0), (ts + 10, ts + 40), 3)
        # Janelas
        for x_offset in [-25, 25]:
            pygame.draw.rect(house, ColorPalette.WINDOW, (ts + x_offset - 10, ts + 15, 20, 20))
            pygame.draw.line(house, ColorPalette.WOOD_TRUNK, (ts + x_offset, ts + 15), (ts + x_offset, ts + 35), 2)
            pygame.draw.line(house, ColorPalette.WOOD_TRUNK, (ts + x_offset - 10, ts + 25), (ts + x_offset + 10, ts + 25), 2)
        buildings['house'] = house
        
        return buildings
    
    def generate_character_sprites(self) -> Dict[str, Dict[str, pygame.Surface]]:
        """
        Gera sprites de personagens com diferentes direções e animações.
        
        Returns:
            Dicionário aninhado: {classe: {direção: superfície}}
        """
        characters = {}
        ts = self.tile_size
        
        # Classes de personagens
        classes = ['warrior', 'mage', 'archer', 'rogue']
        class_colors = {
            'warrior': (178, 34, 34),      # Vermelho
            'mage': (65, 105, 225),        # Azul
            'archer': (34, 139, 34),       # Verde
            'rogue': (101, 67, 33)         # Marrom
        }
        
        # Direções
        directions = ['down', 'up', 'left', 'right']
        
        for char_class in classes:
            characters[char_class] = {}
            color = class_colors[char_class]
            
            for direction in directions:
                sprite = pygame.Surface((ts, ts), pygame.SRCALPHA)
                
                # Posições baseadas na direção
                if direction == 'down':
                    body_y = ts // 3
                    head_y = ts // 6
                    flip = False
                elif direction == 'up':
                    body_y = ts // 3
                    head_y = ts // 6
                    flip = False
                elif direction == 'left':
                    body_y = ts // 3
                    head_y = ts // 6
                    flip = True
                else:  # right
                    body_y = ts // 3
                    head_y = ts // 6
                    flip = False
                
                # Corpo
                body_rect = pygame.Rect(ts//4, body_y, ts//2, ts//3)
                pygame.draw.ellipse(sprite, color, body_rect)
                
                # Cabeça
                head_pos = (ts//2, head_y)
                pygame.draw.circle(sprite, ColorPalette.SKIN_MEDIUM, head_pos, ts//6)
                
                # Olhos (visíveis apenas para down/left/right)
                if direction != 'up':
                    eye_offset = -3 if flip else 3
                    pygame.draw.circle(sprite, (0, 0, 0), (ts//2 + eye_offset - 2, head_y + 2), 2)
                    pygame.draw.circle(sprite, (0, 0, 0), (ts//2 + eye_offset + 2, head_y + 2), 2)
                
                # Cabelo
                hair_color = ColorPalette.HAIR_BROWN
                pygame.draw.arc(sprite, hair_color, 
                              (ts//2 - ts//6, head_y - ts//8, ts//3, ts//4),
                              0, math.pi, 3)
                
                # Pernas
                leg_color = (50, 50, 50)
                pygame.draw.rect(sprite, leg_color, (ts//2 - 6, body_y + ts//4, 5, ts//4))
                pygame.draw.rect(sprite, leg_color, (ts//2 + 1, body_y + ts//4, 5, ts//4))
                
                # Acessórios da classe
                if char_class == 'warrior':
                    # Espada
                    sword_color = (192, 192, 192)
                    if direction in ['down', 'right']:
                        pygame.draw.line(sprite, sword_color, 
                                       (ts - 10, body_y + 10), (ts - 5, body_y - 10), 3)
                    else:
                        pygame.draw.line(sprite, sword_color, 
                                       (10, body_y + 10), (5, body_y - 10), 3)
                
                elif char_class == 'mage':
                    # Chapéu pontudo
                    hat_points = [
                        (ts//2 - 10, head_y - 5),
                        (ts//2 + 10, head_y - 5),
                        (ts//2, head_y - 20)
                    ]
                    pygame.draw.polygon(sprite, (128, 0, 128), hat_points)
                    # Cajado
                    staff_color = (139, 69, 19)
                    pygame.draw.line(sprite, staff_color, 
                                   (ts - 8, body_y), (ts - 8, ts - 10), 2)
                    pygame.draw.circle(sprite, (100, 100, 255), (ts - 8, body_y - 5), 4)
                
                elif char_class == 'archer':
                    # Arco
                    bow_color = (139, 69, 19)
                    if direction in ['down', 'right']:
                        pygame.draw.arc(sprite, bow_color, 
                                      (ts - 15, body_y - 10, 15, 30), -math.pi/2, math.pi/2, 2)
                    else:
                        pygame.draw.arc(sprite, bow_color, 
                                      (0, body_y - 10, 15, 30), math.pi/2, -math.pi/2, 2)
                
                elif char_class == 'rogue':
                    # Capuz
                    hood_color = (50, 50, 50)
                    pygame.draw.arc(sprite, hood_color, 
                                  (ts//2 - 12, head_y - 10, 24, 20), 0, math.pi, 4)
                    # Adaga
                    dagger_color = (192, 192, 192)
                    if direction in ['down', 'right']:
                        pygame.draw.line(sprite, dagger_color, 
                                       (ts - 10, body_y + 15), (ts - 5, body_y + 5), 2)
                    else:
                        pygame.draw.line(sprite, dagger_color, 
                                       (10, body_y + 15), (5, body_y + 5), 2)
                
                characters[char_class][direction] = sprite
        
        return characters
    
    def generate_ui_elements(self) -> Dict[str, pygame.Surface]:
        """
        Gera elementos de interface do usuário.
        
        Returns:
            Dicionário com nomes dos elementos de UI.
        """
        ui = {}
        
        # Barra de vida
        health_bar = pygame.Surface((100, 15), pygame.SRCALPHA)
        pygame.draw.rect(health_bar, (50, 0, 0), (0, 0, 100, 15))
        pygame.draw.rect(health_bar, ColorPalette.UI_HEALTH, (2, 2, 96, 11))
        pygame.draw.rect(health_bar, (255, 255, 255), (0, 0, 100, 15), 1)
        ui['health_bar'] = health_bar
        
        # Barra de mana
        mana_bar = pygame.Surface((100, 15), pygame.SRCALPHA)
        pygame.draw.rect(mana_bar, (0, 0, 50), (0, 0, 100, 15))
        pygame.draw.rect(mana_bar, ColorPalette.UI_MANA, (2, 2, 96, 11))
        pygame.draw.rect(mana_bar, (255, 255, 255), (0, 0, 100, 15), 1)
        ui['mana_bar'] = mana_bar
        
        # Barra de XP
        xp_bar = pygame.Surface((100, 8), pygame.SRCALPHA)
        pygame.draw.rect(xp_bar, (50, 50, 0), (0, 0, 100, 8))
        pygame.draw.rect(xp_bar, ColorPalette.UI_XP, (1, 1, 98, 6))
        pygame.draw.rect(xp_bar, (255, 255, 255), (0, 0, 100, 8), 1)
        ui['xp_bar'] = xp_bar
        
        # Slot de inventário
        inv_slot = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.rect(inv_slot, ColorPalette.UI_BACKGROUND, (0, 0, 40, 40))
        pygame.draw.rect(inv_slot, ColorPalette.UI_BORDER, (0, 0, 40, 40), 2)
        pygame.draw.rect(inv_slot, (60, 60, 60), (2, 2, 36, 36))
        ui['inventory_slot'] = inv_slot
        
        # Botão
        button = pygame.Surface((80, 30), pygame.SRCALPHA)
        pygame.draw.rect(button, ColorPalette.UI_BORDER, (0, 0, 80, 30))
        pygame.draw.rect(button, (80, 80, 80), (2, 2, 76, 26))
        pygame.draw.rect(button, (100, 100, 100), (4, 4, 72, 22))
        ui['button'] = button
        
        # Caixa de diálogo
        dialog_box = pygame.Surface((300, 100), pygame.SRCALPHA)
        pygame.draw.rect(dialog_box, ColorPalette.UI_BACKGROUND, (0, 0, 300, 100))
        pygame.draw.rect(dialog_box, ColorPalette.UI_BORDER, (0, 0, 300, 100), 2)
        pygame.draw.rect(dialog_box, (50, 50, 50), (5, 5, 290, 90))
        ui['dialog_box'] = dialog_box
        
        # Cursor
        cursor = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.polygon(cursor, (255, 255, 255), [(0, 0), (0, 18), (5, 13), (8, 20), (11, 18), (8, 11), (18, 0)])
        pygame.draw.polygon(cursor, (0, 0, 0), [(0, 0), (0, 18), (5, 13), (8, 20), (11, 18), (8, 11), (18, 0)], 1)
        ui['cursor'] = cursor
        
        # Ícone de minimapa
        minimap = pygame.Surface((100, 100), pygame.SRCALPHA)
        pygame.draw.rect(minimap, (0, 0, 0), (0, 0, 100, 100))
        pygame.draw.circle(minimap, (50, 50, 50), (50, 50), 45)
        pygame.draw.circle(minimap, (255, 255, 255), (50, 50), 5)
        ui['minimap_frame'] = minimap
        
        return ui
    
    def generate_sprite_sheet(self, sprites: Dict[str, pygame.Surface], 
                             output_path: str, margin: int = 2) -> Dict[str, Dict[str, int]]:
        """
        Gera uma spritesheet a partir de um dicionário de sprites.
        
        Args:
            sprites: Dicionário de nomes para superfícies.
            output_path: Caminho para salvar a spritesheet.
            margin: Margem entre sprites em pixels.
            
        Returns:
            Dicionário com coordenadas de cada sprite na spritesheet.
        """
        if not sprites:
            return {}
        
        # Ordena sprites por nome para consistência
        sorted_sprites = sorted(sprites.items())
        
        # Calcula dimensões da spritesheet
        sprite_width = self.tile_size
        sprite_height = self.tile_size
        
        # Determina layout (tentativa de criar uma grade quadrada)
        num_sprites = len(sorted_sprites)
        cols = math.ceil(math.sqrt(num_sprites))
        rows = math.ceil(num_sprites / cols)
        
        sheet_width = cols * (sprite_width + margin) - margin
        sheet_height = rows * (sprite_height + margin) - margin
        
        # Cria a spritesheet
        sprite_sheet = pygame.Surface((sheet_width, sheet_height), pygame.SRCALPHA)
        sprite_sheet.fill((0, 0, 0, 0))
        
        # Mapeamento de coordenadas
        sprite_map = {}
        
        for idx, (name, sprite) in enumerate(sorted_sprites):
            col = idx % cols
            row = idx // cols
            
            x = col * (sprite_width + margin)
            y = row * (sprite_height + margin)
            
            # Redimensiona se necessário
            if sprite.get_width() != sprite_width or sprite.get_height() != sprite_height:
                sprite = pygame.transform.smoothscale(sprite, (sprite_width, sprite_height))
            
            sprite_sheet.blit(sprite, (x, y))
            
            sprite_map[name] = {
                'x': x,
                'y': y,
                'width': sprite_width,
                'height': sprite_height
            }
        
        # Salva a spritesheet
        pygame.image.save(sprite_sheet, output_path)
        
        return sprite_map
    
    def save_all_assets(self, output_dir: str) -> Dict[str, Any]:
        """
        Gera e salva todos os assets do jogo.
        
        Args:
            output_dir: Diretório de saída para os assets.
            
        Returns:
            Dicionário com informações sobre os arquivos gerados.
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        generated_files = {}
        
        print("Gerando tiles de terreno...")
        terrain_tiles = self.generate_terrain_tiles()
        terrain_sheet_path = output_path / 'terrain_spritesheet.png'
        terrain_map = self.generate_sprite_sheet(terrain_tiles, str(terrain_sheet_path))
        generated_files['terrain'] = {
            'file': str(terrain_sheet_path),
            'sprites': terrain_map,
            'count': len(terrain_tiles)
        }
        
        print("Gerando objetos...")
        object_tiles = self.generate_object_tiles()
        object_sheet_path = output_path / 'object_spritesheet.png'
        object_map = self.generate_sprite_sheet(object_tiles, str(object_sheet_path))
        generated_files['objects'] = {
            'file': str(object_sheet_path),
            'sprites': object_map,
            'count': len(object_tiles)
        }
        
        print("Gerando construções...")
        building_tiles = self.generate_building_tiles()
        building_sheet_path = output_path / 'building_spritesheet.png'
        building_map = self.generate_sprite_sheet(building_tiles, str(building_sheet_path))
        generated_files['buildings'] = {
            'file': str(building_sheet_path),
            'sprites': building_map,
            'count': len(building_tiles)
        }
        
        print("Gerando personagens...")
        character_sprites = self.generate_character_sprites()
        for char_class, directions in character_sprites.items():
            class_sheet_path = output_path / f'{char_class}_spritesheet.png'
            class_map = self.generate_sprite_sheet(directions, str(class_sheet_path))
            generated_files[f'character_{char_class}'] = {
                'file': str(class_sheet_path),
                'sprites': class_map,
                'count': len(directions)
            }
        
        print("Gerando elementos de UI...")
        ui_elements = self.generate_ui_elements()
        ui_sheet_path = output_path / 'ui_spritesheet.png'
        ui_map = self.generate_sprite_sheet(ui_elements, str(ui_sheet_path))
        generated_files['ui'] = {
            'file': str(ui_sheet_path),
            'sprites': ui_map,
            'count': len(ui_elements)
        }
        
        # Salva metadados JSON
        metadata_path = output_path / 'sprite_metadata.json'
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(generated_files, f, indent=2)
        generated_files['metadata'] = str(metadata_path)
        
        print(f"\nAssets gerados com sucesso em: {output_path}")
        print(f"Total de categorias: {len(generated_files)}")
        
        return generated_files


def main():
    """Função principal do gerador de assets."""
    parser = argparse.ArgumentParser(
        description='Gerador de assets visuais para MMORPG',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python -m tools.asset_generator --output assets/sprites
  python -m tools.asset_generator --output assets/sprites --tile-size 32
        """
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='assets/sprites',
        help='Diretório de saída para os assets (padrão: assets/sprites)'
    )
    
    parser.add_argument(
        '--tile-size', '-t',
        type=int,
        default=40,
        help='Tamanho do tile em pixels (padrão: 40)'
    )
    
    args = parser.parse_args()
    
    try:
        generator = AssetGenerator(tile_size=args.tile_size)
        generated = generator.save_all_assets(args.output)
        
        print("\n=== Resumo da Geração ===")
        for category, info in generated.items():
            if isinstance(info, dict) and 'count' in info:
                print(f"  {category}: {info['count']} sprites -> {info['file']}")
        
        print("\nGeração concluída com sucesso!")
        return 0
        
    except Exception as e:
        print(f"Erro ao gerar assets: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
