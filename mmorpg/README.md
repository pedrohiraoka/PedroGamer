# MMORPG 2D em Python com Pygame

Um jogo MMORPG 2D completo desenvolvido em Python 3, utilizando Pygame para renderização e sockets TCP para comunicação em tempo real. O projeto é dividido em três componentes principais: servidor, cliente e gerador de mundo.

## Estrutura do Projeto

```
mmorpg/
├── server/
│   ├── __init__.py
│   ├── server.py          # Servidor principal multithread
│   ├── world.py           # Gerenciamento do mundo e colisões
│   └── protocol.py        # Definições do protocolo de comunicação
├── client/
│   ├── __init__.py
│   └── client.py          # Cliente Pygame com renderização
├── world_generator/
│   ├── __init__.py
│   └── generate_world.py  # Gerador de mapas e objetos
├── config/
│   ├── server_config.json # Configuração do servidor
│   └── client_config.json # Configuração do cliente
├── resources/
│   ├── sprites/           # Sprites opcionais (não requeridos)
│   ├── world_map.json     # Mapa gerado
│   └── world_objects.json # Objetos do mundo
├── logs/                  # Logs do servidor e cliente
├── requirements.txt       # Dependências
└── README.md             # Este arquivo
```

## Requisitos

- **Python 3.8 ou superior**
- **Pygame** (para o cliente)

## Instalação

### 1. Clone ou copie o projeto

```bash
cd /workspace/mmorpg
```

### 2. Instale as dependências

```bash
pip install pygame
```

Ou use o arquivo de requisitos:

```bash
pip install -r requirements.txt
```

### 3. Gere o mundo (opcional)

O servidor pode gerar um mundo automaticamente, mas você pode pré-gerar:

```bash
python -m world_generator.generate_world --generate --output resources
```

## Como Executar

### Iniciar o Servidor

Em um terminal:

```bash
cd /workspace/mmorpg
python -m server.server --config config/server_config.json
```

Ou com parâmetros diretos:

```bash
python -m server.server --host 0.0.0.0 --port 5000
```

**Opções do servidor:**
- `--config, -c`: Caminho para o arquivo de configuração
- `--host, -H`: Endereço do servidor (padrão: 0.0.0.0)
- `--port, -p`: Porta do servidor (padrão: 5000)

### Iniciar o Cliente

Em outro terminal (pode abrir múltiplas instâncias):

```bash
cd /workspace/mmorpg
python -m client.client --host localhost --port 5000
```

**Opções do cliente:**
- `--host, -H`: Endereço do servidor (padrão: localhost)
- `--port, -p`: Porta do servidor (padrão: 5000)
- `--width, -W`: Largura da janela (padrão: 640)
- `--height, -T`: Altura da janela (padrão: 480)

## Controles do Jogo

| Tecla | Ação |
|-------|------|
| W | Mover para cima |
| S | Mover para baixo |
| A | Mover para esquerda |
| D | Mover para direita |
| T | Abrir chat |
| ENTER | Enviar mensagem |
| ESC | Sair / Fechar chat |

## Protocolo de Comunicação

O protocolo usa JSON sobre TCP com os seguintes tipos de mensagem:

### Mensagens Cliente → Servidor

- **auth_request**: Autenticação inicial
- **move_request**: Requisição de movimento
- **chat_message**: Mensagem de chat
- **heartbeat**: Manter conexão ativa

### Mensagens Servidor → Cliente

- **auth_response**: Resposta de autenticação
- **move_response**: Confirmação de movimento
- **position_update**: Atualização de posição de jogadores
- **player_join**: Novo jogador entrou
- **player_leave**: Jogador saiu
- **chat_message**: Mensagem de chat broadcast
- **world_state**: Estado inicial do mundo
- **system_message**: Mensagens do sistema
- **error**: Erros

### Exemplo de Mensagem

```json
{
    "type": "auth_request",
    "payload": {
        "player_name": "Jogador1",
        "client_version": "1.0.0"
    },
    "timestamp": 1234567890.123
}
```

## Configuração

### Servidor (config/server_config.json)

```json
{
    "server": {
        "host": "0.0.0.0",
        "port": 5000,
        "tick_rate": 30,
        "max_clients": 10,
        "heartbeat_timeout": 10.0,
        "heartbeat_interval": 2.0
    },
    "world": {
        "width": 500,
        "height": 500,
        "tile_size": 40
    },
    "movement": {
        "speed": 5.0,
        "validation_enabled": true
    }
}
```

### Cliente (config/client_config.json)

```json
{
    "client": {
        "window_width": 640,
        "window_height": 480,
        "fps": 60,
        "server_host": "localhost",
        "server_port": 5000
    }
}
```

## Testes de Conectividade

### Teste 1: Verificar se o servidor está rodando

```bash
# Em um terminal, inicie o servidor
python -m server.server

# Em outro terminal, teste a conexão
python -c "import socket; s = socket.socket(); s.connect(('localhost', 5000)); print('Conexão bem-sucedida!'); s.close()"
```

### Teste 2: Múltiplos clientes

```bash
# Terminal 1: Servidor
python -m server.server

# Terminal 2: Cliente 1
python -m client.client

# Terminal 3: Cliente 2 (use nome diferente)
python -m client.client
```

Os dois clientes devem conseguir se ver no jogo.

### Teste 3: Stress test simples

```python
# test_connections.py
import socket
import threading
import json
import time

def connect_client(client_id):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('localhost', 5000))
        
        # Auth
        msg = {"type": "auth_request", "payload": {"player_name": f"Bot{client_id}"}}
        sock.send(json.dumps(msg).encode())
        
        time.sleep(0.5)
        
        # Move
        msg = {"type": "move_request", "payload": {"direction_x": 1, "direction_y": 0}}
        sock.send(json.dumps(msg).encode())
        
        time.sleep(0.5)
        sock.close()
        print(f"Client {client_id}: OK")
    except Exception as e:
        print(f"Client {client_id}: ERROR - {e}")

threads = []
for i in range(10):
    t = threading.Thread(target=connect_client, args=(i,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

print("Teste completo!")
```

## Características Técnicas

### Servidor

- ✅ TCP multithread com suporte a 10+ conexões simultâneas
- ✅ Validação de movimento no servidor (anti-cheat)
- ✅ Detecção de colisão com obstáculos e limites
- ✅ Sistema de heartbeat com timeout
- ✅ Serialização JSON para segurança
- ✅ Logs estruturados
- ✅ Carregamento de mapa personalizado

### Cliente

- ✅ Renderização baseada em tiles (640x480, 40x40 pixels/tile)
- ✅ Câmera que segue o jogador
- ✅ Movimento suave com vetores de velocidade
- ✅ Previsão de movimento local
- ✅ Chat integrado
- ✅ Tratamento de reconexão
- ✅ FPS estável (60 FPS)

### Mundo

- ✅ Mapa 500x500 tiles
- ✅ Terrenos variados (grama, água, pedra, terra)
- ✅ Objetos interativos (árvores, rochas, casas)
- ✅ Pontos de spawn múltiplos
- ✅ Geração procedural ou carregamento de arquivo

## Extensibilidade

O código foi projetado para ser modular e extensível. Para adicionar novos sistemas:

### Inventário

1. Adicione novos tipos de mensagem em `protocol.py`
2. Implemente handlers no servidor em `server.py`
3. Adicione UI no cliente em `client.py`

### Combate

1. Estenda a classe `Player` com atributos de combate
2. Adicione validação de ações de combate no servidor
3. Implemente animações e efeitos no cliente

### Persistência

1. Adicione banco de dados (SQLite, PostgreSQL)
2. Modifique `World` para carregar/salvar estado
3. Implemente save/load de progresso do jogador

## Logs

Os logs são salvos em:

- `logs/server.log`: Logs do servidor
- `logs/client.log`: Logs do cliente

## Solução de Problemas

### Erro: "Address already in use"

O servidor já está rodando ou a porta está ocupada.

```bash
# Linux/Mac
lsof -i :5000
kill <PID>

# Ou use outra porta
python -m server.server --port 5001
```

### Erro: "Connection refused"

O servidor não está rodando ou está em outra porta.

```bash
# Verifique se o servidor está ativo
python -m server.server

# Conecte na porta correta
python -m client.client --port 5000
```

### Cliente não renderiza

Verifique se o Pygame está instalado corretamente:

```bash
pip install --upgrade pygame
```

## Licença

Este projeto é fornecido como material educacional. Use livremente para aprendizado e desenvolvimento.

## Contribuição

Para contribuir:

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## Contato

Para dúvidas ou sugestões, abra uma issue no repositório.
