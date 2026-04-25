# Cliente MMORPG 2D em Python/Pygame

Cliente 2D para um jogo MMORPG desenvolvido com Python e Pygame, baseado no capítulo "Construindo um jogo MMORPG com Python".

## Funcionalidades Implementadas

- **Estrutura básica do jogo**: Janela 640x480 pixels, loop principal com clock (7 FPS), tratamento de evento QUIT
- **Carregamento de recursos**: Mapas via cPickle (tilemap.txt, objmap.txt), imagens de tiles e objetos
- **Renderização de mapa**: Sistema de tiles 16x11 (40x40 pixels cada), suporte a deslocamento de câmera (slide_x, slide_y)
- **Movimentação do jogador**: Captura de teclado (setas direcionais), validação via servidor
- **Interface de texto**: Área inferior de 40 pixels para mensagens do servidor
- **Comunicação em rede**: Conexão TCP (127.0.0.1:5000), thread listener para recebimento de mensagens
- **Eventos suportados**: GOTO, SETOBJECT, MESSAGE, SYSTEM, GETINFO

## Requisitos

- Python 3.x
- Pygame 2.x

## Instalação

```bash
pip install pygame
```

## Execução

```bash
python mmorpg_client.py
```

**Nota**: O cliente requer um servidor MMORPG compatível rodando em `127.0.0.1:5000`.

## Estrutura de Arquivos Esperada

```
/workspace/
├── mmorpg_client.py    # Código do cliente
├── tilemap.txt         # Mapa de tiles (cPickle)
├── objmap.txt          # Mapa de objetos (cPickle)
├── tiles/
│   ├── tile0.png
│   ├── tile1.png
│   └── ... (até tile23.png)
└── objects/
    ├── obj0.png
    ├── obj1.png
    └── ... (até obj23.png)
```

Se as imagens não forem encontradas, o cliente criará tiles/objetos padrão coloridos automaticamente.

## Controles

- **Setas direcionais**: Movimentar personagem
- **Mouse (clique)**: Enviar evento GETINFO para posição clicada
- **Fechar janela**: Encerra conexão e sai do jogo

## Funções Principais

| Função | Descrição |
|--------|-----------|
| `load_resources()` | Carrega mapas e imagens |
| `handle(event)` | Processa eventos do servidor |
| `move(direction)` | Calcula nova posição e envia GOTO |
| `goto(x, y)` | Cria e posta evento GOTO |
| `settext(message)` | Atualiza área de texto |
| `send(data)` | Envia dados ao servidor |
| `listener()` | Thread que recebe mensagens do servidor |
| `render_map()` | Renderiza tiles e objetos |
| `init_game()` | Inicializa Pygame, recursos e conexão |
| `main()` | Loop principal do jogo |

## Protocolo de Comunicação

O cliente se conecta via TCP e envia/recebe:
- Eventos Pygame serializados como listas
- Strings de sistema (ex: "bye bye" no encerramento)

Eventos enviados ao servidor:
- `SYSTEM`: Login com ID e nome do jogador
- `GOTO`: Solicitação de movimento
- `GETINFO`: Informação sobre posição do mouse

Eventos recebidos do servidor:
- `GOTO`: Atualiza posição da câmera
- `SETOBJECT`: Atualiza matriz de objetos
- `MESSAGE`: Exibe mensagem na interface
- `SYSTEM`: Imprime no console

## Observações

- Este código é compatível com Python 3 (usa `pickle` e `_thread` com alias)
- Para Python 2, use `cPickle` e `thread` diretamente
- O servidor deve validar movimentos e gerenciar a lógica do jogo
