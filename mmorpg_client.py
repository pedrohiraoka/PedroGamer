#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Cliente 2D para MMORPG usando Python e Pygame
Baseado no capítulo "Construindo um jogo MMORPG com Python"

Este cliente implementa:
- Renderização de mapa baseado em tiles
- Movimentação de personagem via teclado
- Interface de texto para mensagens do servidor
- Comunicação em rede via sockets TCP

Nota: Este código é compatível com Python 3. Para Python 2, use:
- import cPickle (ao invés de pickle)
- import thread (ao invés de _thread)
"""

import pygame
from pygame.locals import *
import socket
import pickle as cPickle  # Usando alias para compatibilidade com o código original
import _thread as thread  # Usando alias para compatibilidade com o código original

# Constantes do jogo
HOST = '127.0.0.1'
PORT = 5000
TILE = 40  # Tamanho de cada tile em pixels
WIDTH = 640  # Largura da janela
HEIGHT = 480  # Altura da janela
FPS = 7  # Frames por segundo

# Posição central da tela para o jogador
MIDDLE = (WIDTH / 2 - 1, HEIGHT / 2 - 1)

# Direções de movimento (cima, baixo, esquerda, direita)
MOVES = {
    K_UP: (-1, 0),
    K_DOWN: (1, 0),
    K_LEFT: (0, -1),
    K_RIGHT: (0, 1)
}

# Variáveis globais
screen = None
clock = None
font = None
text_surface = None
sock = None
player_id = None
player_name = None

# Mapas (carregados dos arquivos)
tilemap = []  # Matriz de tiles do cenário
objmap = []   # Matriz de objetos do cenário

# Imagens carregadas
tiles = []  # Lista de imagens dos tiles (tile0.png a tile23.png)
objs = []   # Lista de imagens dos objetos (obj0.png a obj23.png)

# Estado do jogo
slide_x = 0  # Deslocamento horizontal da câmera
slide_y = 0  # Deslocamento vertical da câmera
moving = 0   # Velocidade atual do jogador (direção)
running = True  # Flag para controlar o loop principal


def load_resources():
    """
    Carrega todos os recursos do jogo: mapas e imagens.
    Usa cPickle para carregar os arquivos de mapa.
    """
    global tilemap, objmap, tiles, objs
    
    try:
        # Carregar mapa de tiles
        with open('tilemap.txt', 'rb') as f:
            tilemap = cPickle.load(f)
        print("Tilemap carregado com sucesso.")
        
        # Carregar mapa de objetos
        with open('objmap.txt', 'rb') as f:
            objmap = cPickle.load(f)
        print("Objmap carregado com sucesso.")
        
    except IOError as e:
        print("Erro ao carregar arquivos de mapa: %s" % str(e))
        print("Certifique-se que tilemap.txt e objmap.txt existem no diretório atual.")
        return False
    
    # Carregar imagens dos tiles (tile0.png a tile23.png)
    tiles = []
    for i in range(24):
        try:
            img = pygame.image.load('tiles/tile%d.png' % i)
            tiles.append(img)
        except IOError:
            # Se não encontrar, cria um tile padrão (quadrado colorido)
            img = pygame.Surface((TILE, TILE))
            img.fill((100 + i * 5, 100, 100))
            tiles.append(img)
    print("Tiles carregados: %d imagens" % len(tiles))
    
    # Carregar imagens dos objetos (obj0.png a obj23.png)
    objs = []
    for i in range(24):
        try:
            img = pygame.image.load('objects/obj%d.png' % i)
            objs.append(img)
        except IOError:
            # Se não encontrar, cria um objeto padrão
            img = pygame.Surface((TILE, TILE))
            img.fill((200, 100 + i * 5, 100))
            objs.append(img)
    print("Objetos carregados: %d imagens" % len(objs))
    
    return True


def handle(event):
    """
    Processa eventos recebidos do servidor ou gerados localmente.
    
    Tipos de eventos suportados:
    - GOTO: Move a câmera para as coordenadas especificadas
    - SETOBJECT: Atualiza um objeto na matriz objmap
    - MESSAGE: Exibe mensagem na área de texto
    - SYSTEM: Imprime mensagem no console
    """
    global slide_x, slide_y
    
    if event.type == GOTO:
        # Move a câmera para a posição do evento
        # O servidor envia as coordenadas globais do jogador
        slide_x = event.x - MIDDLE[0]
        slide_y = event.y - MIDDLE[1]
        print("GOTO: x=%d, y=%d" % (event.x, event.y))
        
    elif event.type == SETOBJECT:
        # Atualiza a matriz de objetos na posição especificada
        # e.y e e.x são as coordenadas, e.obj é o novo valor do objeto
        if 0 <= event.y < len(objmap) and 0 <= event.x < len(objmap[0]):
            objmap[event.y][event.x] = event.obj
            print("SETOBJECT: (%d, %d) = %d" % (event.x, event.y, event.obj))
            
    elif event.type == MESSAGE:
        # Exibe mensagem na área de texto inferior
        settext(event.message)
        print("MESSAGE: %s" % event.message)
        
    elif event.type == SYSTEM:
        # Mensagem de sistema (imprime no console)
        print("SYSTEM: %s" % event.message)


def move(direction):
    """
    Calcula a nova posição baseada na direção de movimento.
    Envia evento GOTO para o servidor validar o movimento.
    
    Args:
        direction: Código da tecla direcional (K_UP, K_DOWN, etc.)
    """
    global slide_x, slide_y
    
    if direction not in MOVES:
        return
    
    dy, dx = MOVES[direction]
    
    # Posição atual do jogador (coordenadas globais)
    current_x = slide_x + MIDDLE[0]
    current_y = slide_y + MIDDLE[1]
    
    # Nova posição desejada
    new_x = current_x + dx
    new_y = current_y + dy
    
    # Cria e envia evento GOTO para o servidor validar
    goto_event = pygame.event.Event(GOTO, {'x': new_x, 'y': new_y})
    send(goto_event)


def goto(x, y):
    """
    Cria e posta um evento GOTO com as coordenadas especificadas.
    Usado para movimentação do jogador.
    
    Args:
        x: Coordenada X global
        y: Coordenada Y global
    """
    event = pygame.event.Event(GOTO, {'x': x, 'y': y})
    pygame.event.post(event)


def settext(message):
    """
    Atualiza a superfície de texto na parte inferior da tela.
    Renderiza o texto em branco sobre fundo preto.
    
    Args:
        message: String a ser exibida
    """
    global text_surface
    
    if font is None:
        return
    
    # Renderizar texto
    text_surface = font.render(message, True, (255, 255, 255), (0, 0, 0))
    text_surface.set_alpha(255)


def send(event_or_string):
    """
    Envia dados para o servidor através do socket.
    Pode enviar um evento Pygame serializado ou uma string.
    
    Args:
        event_or_string: Evento Pygame ou string a ser enviada
    """
    global sock
    
    if sock is None:
        print("Socket não conectado. Não foi possível enviar:", event_or_string)
        return
    
    try:
        if isinstance(event_or_string, pygame.event.Event):
            # Serializar evento como lista para envio
            # Formato: [tipo, atributos...]
            event_data = [event_or_string.type]
            for attr in ['x', 'y', 'obj', 'message']:
                if hasattr(event_or_string, attr):
                    event_data.append(getattr(event_or_string, attr))
                else:
                    event_data.append(None)
            data = cPickle.dumps(event_data)
        else:
            # Enviar string diretamente
            data = str(event_or_string)
        
        sock.sendall(data)
        print("Enviado:", event_or_string)
        
    except socket.error as e:
        print("Erro ao enviar dados: %s" % str(e))


def listener():
    """
    Thread que escuta continuamente mensagens do servidor.
    Recebe dados, desserializa e posta eventos na fila da Pygame.
    """
    global sock, running
    
    buffer = ""
    
    while running:
        try:
            data = sock.recv(1024)
            if not data:
                print("Servidor desconectado.")
                running = False
                break
            
            buffer += data
            
            # Processar mensagens completas
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                
                if not line:
                    continue
                
                try:
                    # Tentar desserializar como lista de eventos
                    events = eval(line)
                    
                    if isinstance(events, list):
                        # Processar cada evento da lista
                        for event_data in events:
                            if isinstance(event_data, list) and len(event_data) > 0:
                                event_type = event_data[0]
                                
                                # Criar evento Pygame customizado
                                if event_type == GOTO:
                                    event = pygame.event.Event(GOTO, {
                                        'x': event_data[1] if len(event_data) > 1 else 0,
                                        'y': event_data[2] if len(event_data) > 2 else 0
                                    })
                                elif event_type == SETOBJECT:
                                    event = pygame.event.Event(SETOBJECT, {
                                        'x': event_data[1] if len(event_data) > 1 else 0,
                                        'y': event_data[2] if len(event_data) > 2 else 0,
                                        'obj': event_data[3] if len(event_data) > 3 else 0
                                    })
                                elif event_type == MESSAGE:
                                    event = pygame.event.Event(MESSAGE, {
                                        'message': event_data[1] if len(event_data) > 1 else ''
                                    })
                                elif event_type == SYSTEM:
                                    event = pygame.event.Event(SYSTEM, {
                                        'message': event_data[1] if len(event_data) > 1 else ''
                                    })
                                else:
                                    # Evento genérico
                                    event = pygame.event.Event(event_type)
                                
                                pygame.event.post(event)
                    else:
                        # Mensagem de texto do servidor
                        print("Servidor:", events)
                        
                except (SyntaxError, NameError, TypeError):
                    # Não é uma lista válida, tratar como mensagem de texto
                    print("Servidor:", line)
                    
        except socket.error as e:
            print("Erro na conexão: %s" % str(e))
            running = False
            break
        except Exception as e:
            print("Erro no listener: %s" % str(e))
            continue
    
    print("Listener encerrado.")


def render_map():
    """
    Renderiza o mapa na tela, incluindo tiles e objetos.
    Suporta deslocamento da câmera (slide_x, slide_y).
    """
    global screen, slide_x, slide_y
    
    # Calcular região visível do mapa
    start_tile_x = slide_x / TILE
    start_tile_y = slide_y / TILE
    
    # Número de tiles visíveis (16 colunas x 11 linhas de quadros de 40x40)
    visible_cols = WIDTH / TILE + 1
    visible_rows = (HEIGHT - 40) / TILE + 1  # Subtrair área de texto
    
    # Renderizar tiles do cenário
    for row in range(visible_rows):
        for col in range(visible_cols):
            map_x = start_tile_x + col
            map_y = start_tile_y + row
            
            # Verificar limites do mapa (500x500 tiles)
            if 0 <= map_y < len(tilemap) and 0 <= map_x < len(tilemap[0]):
                tile_index = tilemap[map_y][map_x]
                
                # Selecionar imagem do tile (limitar a 24 tipos)
                if 0 <= tile_index < len(tiles):
                    screen_x = col * TILE - (slide_x % TILE)
                    screen_y = row * TILE - (slide_y % TILE)
                    screen.blit(tiles[tile_index], (screen_x, screen_y))
    
    # Renderizar objetos (índices menores que 24)
    # Objetos podem ter offsets negativos (até 6 linhas acima e 4 colunas à esquerda)
    for row in range(visible_rows + 6):  # Margem para objetos grandes
        for col in range(visible_cols + 4):
            map_x = start_tile_x + col - 4  # Offset negativo
            map_y = start_tile_y + row - 6  # Offset negativo
            
            # Verificar limites do mapa
            if 0 <= map_y < len(objmap) and 0 <= map_x < len(objmap[0]):
                obj_index = objmap[map_y][map_x]
                
                # Apenas objetos com índice < 24
                if 0 <= obj_index < 24 and obj_index < len(objs):
                    screen_x = (col + 4) * TILE - (slide_x % TILE) - 4 * TILE
                    screen_y = (row + 6) * TILE - (slide_y % TILE) - 6 * TILE
                    screen.blit(objs[obj_index], (screen_x, screen_y))


def init_game(player_id_param=1, player_name_param="Jogador"):
    """
    Inicializa o jogo: Pygame, janela, recursos e conexão com servidor.
    
    Args:
        player_id_param: ID do jogador
        player_name_param: Nome do jogador
    """
    global screen, clock, font, text_surface, sock
    global player_id, player_name, running
    
    player_id = player_id_param
    player_name = player_name_param
    
    # Inicializar Pygame
    pygame.init()
    
    # Criar janela 640x480
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("MMORPG Client")
    
    # Criar clock para controlar FPS (7 frames por segundo)
    clock = pygame.time.Clock()
    
    # Inicializar fonte para interface de texto
    font = pygame.font.Font(None, 24)
    
    # Criar superfície de texto inicial
    settext("Conectando ao servidor...")
    
    # Carregar recursos (mapas e imagens)
    if not load_resources():
        print("Falha ao carregar recursos. Verifique os arquivos.")
        return False
    
    # Conectar ao servidor via TCP
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((HOST, PORT))
        print("Conectado ao servidor %s:%d" % (HOST, PORT))
        
        # Enviar evento SYSTEM inicial com ID e nome do jogador
        login_event = pygame.event.Event(SYSTEM, {
            'message': 'LOGIN %d %s' % (player_id, player_name)
        })
        send(login_event)
        
        # Iniciar thread listener para receber mensagens do servidor
        thread.start_new_thread(listener, ())
        
    except socket.error as e:
        print("Falha na conexão com o servidor: %s" % str(e))
        settext("Erro de conexão: %s" % str(e))
        return False
    
    return True


def main():
    """
    Loop principal do jogo.
    Controla eventos, atualização e renderização.
    """
    global running, moving, slide_x, slide_y
    
    # Inicializar jogo com ID e nome do jogador
    if not init_game():
        print("Não foi possível iniciar o jogo.")
        return
    
    # Definir tipos de eventos customizados
    global GOTO, SETOBJECT, MESSAGE, SYSTEM, GETINFO
    GOTO = pygame.USEREVENT + 1
    SETOBJECT = pygame.USEREVENT + 2
    MESSAGE = pygame.USEREVENT + 3
    SYSTEM = pygame.USEREVENT + 4
    GETINFO = pygame.USEREVENT + 5
    
    # Mensagem inicial
    settext("Bem-vindo ao MMORPG! Use as setas para mover.")
    
    while running:
        # Controlar FPS (7 frames por segundo)
        clock.tick(FPS)
        
        # Processar eventos da Pygame
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
                
            elif event.type == KEYDOWN:
                if event.key in MOVES:
                    # Iniciar movimento na direção pressionada
                    moving = event.key
                    move(event.key)
                    
            elif event.type == KEYUP:
                if event.key in MOVES and event.key == moving:
                    # Parar movimento quando tecla é solta
                    moving = 0
                    
            elif event.type == MOUSEBUTTONDOWN:
                # Clique do mouse: calcular posição global e enviar GETINFO
                mouse_x, mouse_y = event.pos
                
                # Calcular posição no mapa global
                global_x = slide_x / TILE + mouse_x / TILE
                global_y = slide_y / TILE + mouse_y / TILE
                
                # Enviar evento GETINFO para o servidor
                info_event = pygame.event.Event(GETINFO, {
                    'x': global_x,
                    'y': global_y
                })
                send(info_event)
                print("GETINFO: x=%d, y=%d" % (global_x, global_y))
                
            elif event.type in [GOTO, SETOBJECT, MESSAGE, SYSTEM]:
                # Processar eventos recebidos do servidor
                handle(event)
        
        # Atualizar estado do jogo
        # (movimentação contínua se houver tecla pressionada)
        if moving != 0:
            move(moving)
        
        # Renderizar
        screen.fill((0, 0, 0))  # Limpar tela com preto
        
        # Renderizar mapa (tiles e objetos)
        render_map()
        
        # Desenhar área de texto na parte inferior (40 pixels de altura)
        text_rect = pygame.Rect(0, HEIGHT - 40, WIDTH, 40)
        pygame.draw.rect(screen, (0, 0, 0), text_rect)
        
        if text_surface:
            screen.blit(text_surface, (5, HEIGHT - 35))
        
        # Atualizar display
        pygame.display.flip()
    
    # Encerramento: enviar "bye bye" e fechar socket
    print("Encerrando jogo...")
    send("bye bye")
    
    if sock:
        sock.close()
    
    pygame.quit()
    print("Jogo encerrado.")


if __name__ == "__main__":
    main()
