# MMORPG 2D em Python com Pygame

Um jogo MMORPG 2D completo desenvolvido em Python 3, utilizando Pygame para renderização e sockets TCP para comunicação em tempo real. O projeto é dividido em três componentes principais: servidor, cliente e gerador de mundo.

## Estrutura do Projeto

```
workspace/
├── src/                      # Código fonte principal
│   ├── __init__.py          # Pacote principal
│   ├── client/              # Cliente Pygame
│   │   ├── __init__.py
│   │   └── client.py        # Implementação do cliente
│   ├── server/              # Servidor multithread
│   │   ├── __init__.py
│   │   └── server.py        # Implementação do servidor
│   ├── world/               # Gerenciamento do mundo
│   │   ├── __init__.py
│   │   ├── world.py         # Classe World e colisões
│   │   └── generator.py     # Geração procedural de mundo
│   ├── protocol/            # Protocolo de comunicação
│   │   ├── __init__.py
│   │   └── messages.py      # Definições de mensagens
│   └── utils/               # Utilitários e ferramentas
│       ├── __init__.py
│       ├── config.py        # Gerenciamento de configuração
│       └── map_generator.py # Gerador de mapas procedural
├── scripts/                  # Scripts de entrada
│   ├── run_server.py        # Script para iniciar o servidor
│   ├── run_client.py        # Script para iniciar o cliente
│   └── generate_world.py    # Script para gerar mundo
├── config/                   # Arquivos de configuração
│   ├── server_config.json   # Configuração do servidor
│   └── client_config.json   # Configuração do cliente
├── resources/                # Recursos do jogo
│   ├── sprites/             # Sprites e texturas
│   ├── world_map.json       # Mapa do mundo
│   └── world_objects.json   # Objetos do mundo
├── tests/                    # Testes unitários
├── logs/                     # Logs (gerado automaticamente)
├── requirements.txt          # Dependências Python
└── README.md                # Este arquivo
```

## Requisitos

- **Python 3.8 ou superior**
- **Pygame** (para o cliente)

## Instalação

### 1. Clone ou copie o projeto

```bash
cd /workspace
```

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

### 3. Gere o mundo (opcional)

O servidor pode gerar um mundo automaticamente, mas você pode pré-gerar:

```bash
python scripts/generate_world.py --output resources/world_map.json
```

## Como Executar

### Iniciar o Servidor

Em um terminal:

```bash
cd /workspace
python scripts/run_server.py
```

Ou com parâmetros diretos:

```bash
python scripts/run_server.py --host 0.0.0.0 --port 5000
```

**Opções do servidor:**
- `--config, -c`: Caminho para o arquivo de configuração
- `--host, -H`: Endereço do servidor (padrão: 0.0.0.0)
- `--port, -p`: Porta do servidor (padrão: 5000)
- `--max-clients`: Número máximo de clientes (padrão: 10)
- `--tick-rate`: Taxa de atualização do servidor (padrão: 30)

### Iniciar o Cliente

Em outro terminal (pode abrir múltiplas instâncias):

```bash
cd /workspace
python scripts/run_client.py
```

**Opções do cliente:**
- `--config, -c`: Caminho para o arquivo de configuração
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
python scripts/run_server.py

# Em outro terminal, teste a conexão
python -c "import socket; s = socket.socket(); s.connect(('localhost', 5000)); print('Conexão bem-sucedida!'); s.close()"
```

### Teste 2: Múltiplos clientes

```bash
# Terminal 1: Servidor
python scripts/run_server.py

# Terminal 2: Cliente 1
python scripts/run_client.py

# Terminal 3: Cliente 2 (use nome diferente)
python scripts/run_client.py
```

Os dois clientes devem conseguir se ver no jogo.

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

## Desenvolvimento

### Estrutura de Módulos

O código foi reestruturado para seguir boas práticas de organização:

- **src/**: Contém todo o código fonte da aplicação
- **scripts/**: Pontos de entrada para execução
- **tests/**: Testes unitários e de integração
- **config/**: Arquivos de configuração
- **resources/**: Assets do jogo (sprites, mapas, etc.)

### Rodando Testes

```bash
# Instale as dependências de desenvolvimento
pip install pytest pytest-cov

# Execute os testes
pytest tests/ -v --cov=src
```

### Formatando o Código

```bash
# Instale as ferramentas de formatação
pip install black flake8 mypy

# Formate o código
black src/ scripts/ tests/

# Verifique linting
flake8 src/ scripts/ tests/

# Verifique tipos
mypy src/
```

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
python scripts/run_server.py --port 5001
```

### Erro: "Connection refused"

O servidor não está rodando ou está em outra porta.

```bash
# Verifique se o servidor está ativo
python scripts/run_server.py

# Conecte na porta correta
python scripts/run_client.py --port 5000
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
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## Contato

Para dúvidas ou sugestões, abra uma issue no repositório.
