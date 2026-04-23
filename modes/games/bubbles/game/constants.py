"""
Constantes globales del juego Bubble Shooter.
"""

# ─── Pantalla ────────────────────────────────────────────
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 30

# ─── Burbuja ─────────────────────────────────────────────
BUBBLE_RADIUS = 20
BUBBLE_DIAMETER = BUBBLE_RADIUS * 2
ROW_HEIGHT = int(BUBBLE_DIAMETER * 0.866)

# ─── Grilla ──────────────────────────────────────────────
GRID_COLS = 12
GRID_ROWS = 16  # filas máximas posibles
GRID_X_OFFSET = (SCREEN_WIDTH - GRID_COLS * BUBBLE_DIAMETER) // 2
GRID_Y_OFFSET = 60

# ─── Lanzador ────────────────────────────────────────────
SHOOTER_Y = SCREEN_HEIGHT - 140
SHOOTER_X = SCREEN_WIDTH // 2

# ─── Colores de burbujas ─────────────────────────────────
BUBBLE_COLORS = [
    (231, 76, 60),     # Rojo
    (52, 152, 219),    # Azul
    (46, 204, 113),    # Verde
    (241, 196, 15),    # Amarillo
    (155, 89, 182),    # Morado
    (230, 126, 34),    # Naranja
]

COLOR_NAMES = ['rojo', 'azul', 'verde', 'amarillo', 'morado', 'naranja']

# ─── Colores de UI ───────────────────────────────────────
TEXT_COLOR = (255, 255, 255)
ACCENT_COLOR = (0, 255, 200)
CURSOR_COLOR = (0, 255, 150)

# ─── Hand tracking ───────────────────────────────────────
PINCH_THRESHOLD = 40
SMOOTH_FACTOR = 0.4

# ─── Modos de dificultad ─────────────────────────────────
DIFFICULTY = {
    'easy': {
        'rows': 5,
        'colors': 4,
        'points_per_bubble': 10,
        'ceiling_drop_interval': 0,   # nunca baja
        'trajectory_length': 3,       # rebotes visibles completos
        'name': 'Facil',
        'color': (46, 204, 113),
    },
    'medium': {
        'rows': 7,
        'colors': 5,
        'points_per_bubble': 15,
        'ceiling_drop_interval': 8,   # baja cada 8 disparos
        'trajectory_length': 2,
        'name': 'Medio',
        'color': (241, 196, 15),
    },
    'hard': {
        'rows': 10,
        'colors': 6,
        'points_per_bubble': 25,
        'ceiling_drop_interval': 5,   # baja cada 5 disparos
        'trajectory_length': 1,
        'name': 'Dificil',
        'color': (231, 76, 60),
    }
}

# ─── Línea de peligro ────────────────────────────────────
DANGER_LINE_Y = SHOOTER_Y - BUBBLE_DIAMETER * 3

# ─── Mecánicas ───────────────────────────────────────────
MIN_MATCH = 3
SHOOT_SPEED_MIN = 10
SHOOT_SPEED_MAX = 20
PULL_FORCE_FACTOR = 0.06
