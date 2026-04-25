# MMORPG 2D - Python + Pygame

Jogo MMORPG 2D baseado no capítulo "Construindo um jogo MMORPG com Python".

## Estrutura do Projeto

```
/workspace/
├── mmorpg_server.py    # Servidor MMORPG (TCP, multi-cliente)
├── mmorpg_client.py    # Cliente gráfico (Pygame)
├── tilemap.txt         # Mapa de tiles (500x500, serializado com pickle)
├── objmap.txt          # Mapa de objetos (500x500, serializado com pickle)
├── tiles/              # Imagens dos tiles (tile0.png a tile23.png)
└── objects/            # Imagens dos objetos (obj0.png a obj23.png)
```

## Requisitos

- Python 3.x
- Pygame (`pip install pygame`)

## Como Executar

### 1. Iniciar o Servidor

Em um terminal, execute:

```bash
python mmorpg_server.py
```

O servidor irá:
- Iniciar na porta 5000 (127.0.0.1:5000)
- Aceitar múltiplos clientes simultaneamente
- Gerenciar posições dos jogadores
- Validar movimentos
- Spawnar objetos aleatórios a cada 10 segundos
- Fazer broadcast de mensagens para todos os jogadores

### 2. Iniciar o(s) Cliente(s)

Em outro(s) terminal(is), execute:

```bash
python mmorpg_client.py
```

Cada instância será um jogador diferente no mesmo mundo.

## Controles do Jogo

- **Setas Direcionais**: Movimentar o personagem
- **Mouse (clique)**: Obter informações sobre uma posição do mapa
- **Fechar janela**: Desconectar do servidor

## Funcionalidades Implementadas

### Servidor (mmorpg_server.py)

- ✅ Conexão TCP multi-cliente
- ✅ Validação de movimentos (limites do mapa, colisão entre jogadores)
- ✅ Broadcast de mensagens para todos os jogadores
- ✅ Sistema de spawn de objetos aleatórios
- ✅ Resposta a consultas GETINFO (clique do mouse)
- ✅ Thread-safe com locks para acesso concorrente
- ✅ Tratamento robusto de desconexões

### Cliente (mmorpg_client.py)

- ✅ Janela 640x480 pixels com Pygame
- ✅ Loop principal com clock (7 FPS)
- ✅ Carregamento de mapas via cPickle (tilemap.txt, objmap.txt)
- ✅ Carregamento de imagens de tiles e objetos (24 tipos cada)
- ✅ Renderização de mapa baseado em tiles (16x11 quadros visíveis)
- ✅ Sistema de câmera com deslocamento (slide_x, slide_y)
- ✅ Movimentação via teclado (setas direcionais)
- ✅ Interface de texto na parte inferior (40px de altura)
- ✅ Comunicação TCP com servidor (127.0.0.1:5000)
- ✅ Thread listener para receber mensagens do servidor
- ✅ Eventos suportados: GOTO, SETOBJECT, MESSAGE, SYSTEM, GETINFO

## Protocolo de Comunicação

Os eventos são serializados como listas usando pickle e enviados via TCP:

- `[GOTO, x, y]` - Solicitar movimento para posição (x, y)
- `[SETOBJECT, x, y, obj]` - Atualizar objeto na posição (x, y)
- `[MESSAGE, "texto"]` - Mensagem exibida na interface
- `[SYSTEM, "texto"]` - Mensagem de sistema (console)
- `[GETINFO, x, y]` - Consultar informações da posição (x, y)

## Mapa

- Dimensões: 500x500 tiles
- Cada tile: 40x40 pixels
- Área visível: 16x11 tiles (640x440 pixels, menos área de texto)
- Tiles: 24 tipos diferentes (tile0.png a tile23.png)
- Objetos: 24 tipos diferentes (obj0.png a obj23.png)

## Notas

- O servidor deve ser iniciado antes dos clientes
- Vários clientes podem se conectar simultaneamente
- Objetos são spawnados aleatoriamente a cada 10 segundos
- Ao fechar o cliente, envia "bye bye" para o servidor e desconecta

## Troubleshooting

**Erro de conexão:** Verifique se o servidor está rodando em 127.0.0.1:5000

**Arquivos de mapa ausentes:** Execute o script de geração ou verifique se tilemap.txt e objmap.txt existem

**Imagens ausentes:** Verifique se as pastas tiles/ e objects/ contêm os arquivos PNG

**Problemas de áudio no Linux:** Configure ALSA ou use `SDL_AUDIODRIVER=dummy python mmorpg_client.py`
