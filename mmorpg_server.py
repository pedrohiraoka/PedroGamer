#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Servidor MMORPG para o cliente Pygame
Baseado no capítulo "Construindo um jogo MMORPG com Python"

Este servidor implementa:
- Conexão TCP múltipla para clientes
- Validação de movimentos dos jogadores
- Broadcast de mensagens para todos os jogadores
- Gerenciamento de estado do mapa (tiles e objetos)
- Resposta a consultas GETINFO

Nota: Este código é compatível com Python 3. Para Python 2, use:
- import cPickle (ao invés de pickle)
- import thread (ao invés de _thread)
"""

import socket
import pickle as cPickle
import _thread as thread
import time
import random

# Constantes do servidor
HOST = '127.0.0.1'
PORT = 5000
MAX_PLAYERS = 100
MAP_WIDTH = 500   # Largura do mapa em tiles
MAP_HEIGHT = 500  # Altura do mapa em tiles

# Tipos de eventos (devem corresponder aos do cliente)
GOTO = 1      # pygame.USEREVENT + 1
SETOBJECT = 2 # pygame.USEREVENT + 2
MESSAGE = 3   # pygame.USEREVENT + 3
SYSTEM = 4    # pygame.USEREVENT + 4
GETINFO = 5   # pygame.USEREVENT + 5

# Variáveis globais do servidor
clients = {}         # Dicionário de clientes conectados {id: (socket, nome, x, y)}
client_counter = 0   # Contador para IDs de clientes
lock = thread.allocate_lock()  # Lock para acesso thread-safe às variáveis globais

# Mapa de objetos (compartilhado entre todos os jogadores)
# Inicializado com zeros (sem objetos)
objmap = [[0 for x in range(MAP_WIDTH)] for y in range(MAP_HEIGHT)]

# Mapa de tiles (apenas para referência, não é modificado dinamicamente)
tilemap = [[0 for x in range(MAP_WIDTH)] for y in range(MAP_HEIGHT)]


def broadcast(event_list, exclude_id=None):
    """
    Envia uma lista de eventos para todos os clientes conectados.
    
    Args:
        event_list: Lista de eventos serializáveis
        exclude_id: ID do cliente a ser excluído do broadcast (opcional)
    """
    with lock:
        data = cPickle.dumps(event_list) + '\n'
        for client_id, (client_sock, name, x, y) in clients.items():
            if client_id != exclude_id:
                try:
                    client_sock.sendall(data)
                except socket.error:
                    # Cliente desconectado, será removido depois
                    pass


def send_to_client(client_id, event_list):
    """
    Envia uma lista de eventos para um cliente específico.
    
    Args:
        client_id: ID do cliente destinatário
        event_list: Lista de eventos serializáveis
    """
    with lock:
        if client_id in clients:
            client_sock, name, x, y = clients[client_id]
            try:
                data = cPickle.dumps(event_list) + '\n'
                client_sock.sendall(data)
            except socket.error:
                # Cliente desconectado
                return False
    return True


def validate_move(client_id, new_x, new_y):
    """
    Valida se um movimento é permitido.
    
    Regras de validação:
    - Dentro dos limites do mapa (0 a MAP_WIDTH-1, 0 a MAP_HEIGHT-1)
    - Tile de destino não é obstáculo (valor 0 no tilemap)
    - Não há outro jogador na posição
    
    Args:
        client_id: ID do jogador que quer mover
        new_x: Nova coordenada X
        new_y: Nova coordenada Y
    
    Returns:
        True se o movimento é válido, False caso contrário
    """
    # Verificar limites do mapa
    if new_x < 0 or new_x >= MAP_WIDTH:
        return False
    if new_y < 0 or new_y >= MAP_HEIGHT:
        return False
    
    # Verificar se é um tile válido (não obstáculo)
    # Neste exemplo simples, consideramos todos os tiles como válidos
    # Em um jogo real, verificaríamos tilemap[new_y][new_x]
    
    # Verificar colisão com outros jogadores
    with lock:
        for other_id, (sock, name, x, y) in clients.items():
            if other_id != client_id and x == new_x and y == new_y:
                return False  # Outro jogador já está nesta posição
    
    return True


def handle_client(client_sock, client_id, client_name):
    """
    Thread que gerencia a comunicação com um cliente específico.
    Recebe eventos do cliente, processa e envia respostas.
    
    Args:
        client_sock: Socket do cliente
        client_id: ID único do cliente
        client_name: Nome do jogador
    """
    global clients, objmap
    
    buffer = ""
    running = True
    
    # Posição inicial aleatória para o jogador
    start_x = random.randint(0, MAP_WIDTH - 1)
    start_y = random.randint(0, MAP_HEIGHT - 1)
    
    with lock:
        clients[client_id] = (client_sock, client_name, start_x, start_y)
    
    print("Jogador %d (%s) conectado em (%d, %d)" % (client_id, client_name, start_x, start_y))
    
    # Enviar mensagem de boas-vindas e posição inicial
    welcome_events = [
        [SYSTEM, "Bem-vindo ao MMORPG, %s!" % client_name],
        [MESSAGE, "Use as setas para mover. Clique para obter informações."],
        [GOTO, start_x, start_y]  # Posicionar câmera do jogador
    ]
    send_to_client(client_id, welcome_events)
    
    # Notificar outros jogadores sobre novo jogador
    broadcast([
        [SYSTEM, "%s entrou no jogo." % client_name]
    ], exclude_id=client_id)
    
    while running:
        try:
            data = client_sock.recv(1024)
            if not data:
                # Cliente desconectou
                break
            
            buffer += data
            
            # Processar mensagens completas (separadas por newline)
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                
                if not line:
                    continue
                
                # Verificar se é string simples (como "bye bye")
                if line == "bye bye":
                    print("Jogador %d (%s) solicitou saída." % (client_id, client_name))
                    running = False
                    break
                
                try:
                    # Tentar desserializar como lista de eventos
                    events = eval(line)
                    
                    if not isinstance(events, list):
                        # Não é uma lista válida
                        continue
                    
                    # Processar cada evento
                    for event_data in events:
                        if not isinstance(event_data, list) or len(event_data) == 0:
                            continue
                        
                        event_type = event_data[0]
                        
                        if event_type == GOTO:
                            # Solicitação de movimento
                            new_x = event_data[1] if len(event_data) > 1 else 0
                            new_y = event_data[2] if len(event_data) > 2 else 0
                            
                            with lock:
                                current_x, current_y = clients[client_id][2], clients[client_id][3]
                            
                            if validate_move(client_id, new_x, new_y):
                                # Movimento válido, atualizar posição
                                with lock:
                                    clients[client_id] = (client_sock, client_name, new_x, new_y)
                                
                                # Confirmar movimento para o cliente
                                send_to_client(client_id, [[GOTO, new_x, new_y]])
                                
                                # Opcional: notificar outros jogadores sobre movimento
                                # broadcast([[SETOBJECT, current_x, current_y, 0]])  # Limpar posição antiga
                                # broadcast([[SETOBJECT, new_x, new_y, 1]])  # Marcar nova posição
                            else:
                                # Movimento inválido, enviar mensagem de erro
                                send_to_client(client_id, [
                                    [MESSAGE, "Movimento inválido! Posição bloqueada."]
                                ])
                        
                        elif event_type == GETINFO:
                            # Consulta de informação sobre uma posição
                            info_x = int(event_data[1]) if len(event_data) > 1 else 0
                            info_y = int(event_data[2]) if len(event_data) > 2 else 0
                            
                            # Obter informações da posição
                            if 0 <= info_y < MAP_HEIGHT and 0 <= info_x < MAP_WIDTH:
                                obj_value = objmap[info_y][info_x]
                                tile_value = tilemap[info_y][info_x]
                                
                                # Verificar se há jogador nesta posição
                                player_here = None
                                with lock:
                                    for pid, (sock, name, x, y) in clients.items():
                                        if x == info_x and y == info_y:
                                            player_here = name
                                            break
                                
                                # Construir mensagem de resposta
                                if player_here:
                                    msg = "Posição (%d, %d): Jogador %s" % (info_x, info_y, player_here)
                                elif obj_value > 0:
                                    msg = "Posição (%d, %d): Objeto tipo %d" % (info_x, info_y, obj_value)
                                else:
                                    msg = "Posição (%d, %d): Vazio (tile %d)" % (info_x, info_y, tile_value)
                                
                                send_to_client(client_id, [[MESSAGE, msg]])
                            else:
                                send_to_client(client_id, [[MESSAGE, "Posição fora do mapa!"]])
                        
                        elif event_type == SYSTEM:
                            # Mensagem de sistema (ex: LOGIN)
                            msg = event_data[1] if len(event_data) > 1 else ""
                            if msg.startswith("LOGIN"):
                                # Já processado na conexão inicial
                                pass
                            else:
                                print("SYSTEM de %d: %s" % (client_id, msg))
                        
                        elif event_type == MESSAGE:
                            # Mensagem de chat (pode ser broadcast para todos)
                            msg = event_data[1] if len(event_data) > 1 else ""
                            broadcast([
                                [MESSAGE, "[%s]: %s" % (client_name, msg)]
                            ])
                
                except (SyntaxError, NameError, TypeError, ValueError) as e:
                    # Erro ao processar evento
                    print("Erro ao processar evento de %d: %s" % (client_id, str(e)))
        
        except socket.error as e:
            print("Erro de socket com cliente %d: %s" % (client_id, str(e)))
            break
        except Exception as e:
            print("Erro inesperado com cliente %d: %s" % (client_id, str(e)))
            break
    
    # Remover cliente da lista
    with lock:
        if client_id in clients:
            del clients[client_id]
    
    # Fechar socket
    try:
        client_sock.close()
    except:
        pass
    
    # Notificar outros jogadores sobre saída
    broadcast([
        [SYSTEM, "%s saiu do jogo." % client_name]
    ])
    
    print("Jogador %d (%s) desconectado." % (client_id, client_name))


def spawn_random_object():
    """
    Função auxiliar para spawnar objetos aleatórios no mapa.
    Pode ser chamada periodicamente para adicionar dinamismo ao jogo.
    """
    global objmap
    
    x = random.randint(0, MAP_WIDTH - 1)
    y = random.randint(0, MAP_HEIGHT - 1)
    obj_type = random.randint(1, 23)  # Tipos de objeto de 1 a 23
    
    objmap[y][x] = obj_type
    
    # Notificar todos os jogadores sobre o novo objeto
    broadcast([[SETOBJECT, x, y, obj_type]])
    print("Objeto tipo %d spawnado em (%d, %d)" % (obj_type, x, y))


def object_spawner():
    """
    Thread que spawnar objetos aleatórios periodicamente.
    """
    while True:
        time.sleep(10)  # Spawnar um objeto a cada 10 segundos
        spawn_random_object()


def main():
    """
    Função principal do servidor.
    Inicia o socket, aceita conexões e gerencia threads.
    """
    global client_counter
    
    # Criar socket TCP
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_sock.bind((HOST, PORT))
        server_sock.listen(5)
        print("=" * 60)
        print("Servidor MMORPG iniciado em %s:%d" % (HOST, PORT))
        print("Mapa: %dx%d tiles" % (MAP_WIDTH, MAP_HEIGHT))
        print("Máximo de jogadores: %d" % MAX_PLAYERS)
        print("=" * 60)
        print("Aguardando conexões...")
        
        # Iniciar thread de spawn de objetos
        thread.start_new_thread(object_spawner, ())
        
        while True:
            # Aceitar nova conexão
            client_sock, addr = server_sock.accept()
            print("Nova conexão de %s:%d" % (addr[0], addr[1]))
            
            # Gerar ID único para o cliente
            with lock:
                client_counter += 1
                client_id = client_counter
            
            # Usar endereço IP como nome padrão (pode ser sobrescrito pelo LOGIN)
            client_name = "Player_%d" % client_id
            
            # Iniciar thread para gerenciar este cliente
            thread.start_new_thread(handle_client, (client_sock, client_id, client_name))
    
    except KeyboardInterrupt:
        print("\nServidor encerrado pelo usuário.")
    
    except socket.error as e:
        print("Erro no socket do servidor: %s" % str(e))
    
    finally:
        # Fechar socket do servidor
        server_sock.close()
        print("Servidor encerrado.")


if __name__ == "__main__":
    main()
