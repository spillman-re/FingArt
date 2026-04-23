"""
Generador procedural inteligente de niveles.
Crea patrones variados según la dificultad sin necesidad de conexión a internet.
"""
import random
import math

from game.bubble import Bubble


class LevelGenerator:
    """Genera niveles procedurales con patrones inteligentes."""

    @staticmethod
    def generate(grid, difficulty_config):
        """Genera un nivel para la grilla según la dificultad."""
        rows = difficulty_config['rows']
        num_colors = difficulty_config['colors']

        # Seleccionar patrón según dificultad
        if num_colors <= 4:  # Fácil
            pattern = random.choice([
                '_gen_horizontal', '_gen_clusters', '_gen_wave'
            ])
        elif num_colors <= 5:  # Medio
            pattern = random.choice([
                '_gen_diagonal', '_gen_checkerboard', '_gen_clusters',
                '_gen_wave', '_gen_diamond'
            ])
        else:  # Difícil
            pattern = random.choice([
                '_gen_random_controlled', '_gen_diagonal',
                '_gen_diamond', '_gen_checkerboard'
            ])

        method = getattr(LevelGenerator, pattern)
        method(grid, rows, num_colors)

    # ─── Patrones ────────────────────────────────────────

    @staticmethod
    def _gen_horizontal(grid, rows, num_colors):
        """Franjas horizontales del mismo color con ligera variación."""
        for r in range(rows):
            base_color = r % num_colors
            for c in range(grid.get_col_count(r)):
                color = base_color
                if random.random() < 0.15:
                    color = random.randint(0, num_colors - 1)
                b = Bubble(color, radius=grid.radius)
                b.x, b.y = grid.get_bubble_pos(r, c)
                grid.grid[r][c] = b

    @staticmethod
    def _gen_diagonal(grid, rows, num_colors):
        """Franjas diagonales."""
        for r in range(rows):
            for c in range(grid.get_col_count(r)):
                color = (r + c) % num_colors
                if random.random() < 0.1:
                    color = random.randint(0, num_colors - 1)
                b = Bubble(color, radius=grid.radius)
                b.x, b.y = grid.get_bubble_pos(r, c)
                grid.grid[r][c] = b

    @staticmethod
    def _gen_clusters(grid, rows, num_colors):
        """Grupos/clusters del mismo color (vecinos influencian)."""
        for r in range(rows):
            for c in range(grid.get_col_count(r)):
                neighbor_colors = []
                for nr, nc in [(r, c - 1), (r - 1, c)]:
                    if 0 <= nr < rows and 0 <= nc < grid.get_col_count(nr):
                        if grid.grid[nr][nc] is not None:
                            neighbor_colors.append(grid.grid[nr][nc].color_index)

                if neighbor_colors and random.random() < 0.6:
                    color = random.choice(neighbor_colors)
                else:
                    color = random.randint(0, num_colors - 1)

                b = Bubble(color, radius=grid.radius)
                b.x, b.y = grid.get_bubble_pos(r, c)
                grid.grid[r][c] = b

    @staticmethod
    def _gen_checkerboard(grid, rows, num_colors):
        """Patrón de tablero con variaciones."""
        color_a, color_b = random.sample(range(num_colors), 2)
        for r in range(rows):
            for c in range(grid.get_col_count(r)):
                color = color_a if (r + c) % 2 == 0 else color_b
                if random.random() < 0.2:
                    color = random.randint(0, num_colors - 1)
                b = Bubble(color, radius=grid.radius)
                b.x, b.y = grid.get_bubble_pos(r, c)
                grid.grid[r][c] = b

    @staticmethod
    def _gen_diamond(grid, rows, num_colors):
        """Patrón de diamante/rombos."""
        cx = grid.cols // 2
        for r in range(rows):
            for c in range(grid.get_col_count(r)):
                dist = abs(c - cx) + abs(r - rows // 2)
                color = dist % num_colors
                if random.random() < 0.15:
                    color = random.randint(0, num_colors - 1)
                b = Bubble(color, radius=grid.radius)
                b.x, b.y = grid.get_bubble_pos(r, c)
                grid.grid[r][c] = b

    @staticmethod
    def _gen_wave(grid, rows, num_colors):
        """Patrón sinusoidal ondulado."""
        freq = random.uniform(0.3, 0.8)
        for r in range(rows):
            for c in range(grid.get_col_count(r)):
                val = math.sin(c * freq + r * 0.5)
                color = int((val + 1) / 2 * num_colors) % num_colors
                if random.random() < 0.12:
                    color = random.randint(0, num_colors - 1)
                b = Bubble(color, radius=grid.radius)
                b.x, b.y = grid.get_bubble_pos(r, c)
                grid.grid[r][c] = b

    @staticmethod
    def _gen_random_controlled(grid, rows, num_colors):
        """Random controlado: evita clusters naturales (más difícil)."""
        for r in range(rows):
            for c in range(grid.get_col_count(r)):
                neighbor_colors = set()
                for nr, nc in grid.get_neighbors(r, c):
                    if 0 <= nr < rows and 0 <= nc < grid.get_col_count(nr):
                        if grid.grid[nr][nc] is not None:
                            neighbor_colors.add(grid.grid[nr][nc].color_index)

                # Evitar color de vecinos (lo hace más difícil)
                available = [i for i in range(num_colors) if i not in neighbor_colors]
                if not available or random.random() < 0.15:
                    available = list(range(num_colors))

                color = random.choice(available)
                b = Bubble(color, radius=grid.radius)
                b.x, b.y = grid.get_bubble_pos(r, c)
                grid.grid[r][c] = b

    # ─── Puntuación ──────────────────────────────────────

    @staticmethod
    def calculate_score(bubbles_popped, bubbles_dropped, combo_count, config):
        """Calcular puntuación de un movimiento."""
        base = config['points_per_bubble']

        pop_score = len(bubbles_popped) * base

        # Bonus por eliminar más de 3
        extra = max(0, len(bubbles_popped) - 3)
        combo_bonus = int(extra * base * 0.5)

        # Bonus por burbujas flotantes (x2)
        drop_score = len(bubbles_dropped) * base * 2

        # Multiplicador por combos consecutivos
        multiplier = 1.0 + combo_count * 0.1

        return int((pop_score + combo_bonus + drop_score) * multiplier)
