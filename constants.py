# Configurações de Janela e Dimensões da Mesa
WIDTH, HEIGHT = 1280, 720
TABLE_WIDTH, TABLE_LENGTH = 15.0, 30.0
BALL_RADIUS = 0.5
POCKET_RADIUS = 0.9

# Parâmetros de Física e Força da Tacada
MAX_SHOT_POWER = 1.2
MAX_PULL_DIST = 15.0
MIN_PULL_DIST = 2.0
FRICTION = 0.992

# Parâmetros do HUD Interativo de Efeito (Spin)
HUD_CX = WIDTH - 100
HUD_CY = 100
HUD_R = 50

# Cores em Formato RGB Normalizado (0.0 a 1.0)
FELT_GREEN = (0.0, 0.4, 0.15)
WHITE = (1.0, 1.0, 1.0)
RED = (0.8, 0.1, 0.1)
YELLOW = (0.9, 0.7, 0.0)
BLACK = (0.1, 0.1, 0.1)
WOOD_BROWN = (0.3, 0.15, 0.05)
HUD_COLOR = (0.8, 0.75, 0.6)

# Posições das 6 Caçapas no Plano da Mesa (X, Z)
POCKETS = [
    (-TABLE_WIDTH / 2, -TABLE_LENGTH / 2),
    (TABLE_WIDTH / 2, -TABLE_LENGTH / 2),
    (-TABLE_WIDTH / 2, TABLE_LENGTH / 2),
    (TABLE_WIDTH / 2, TABLE_LENGTH / 2),
    (-TABLE_WIDTH / 2, 0),
    (TABLE_WIDTH / 2, 0),
]

# Máquina de Estados do Jogo
STATE_MENU = 0
STATE_PLAYING = 1
STATE_GAME_OVER = 2
STATE_PAUSED = 3
