"""
Grilla hexagonal de burbujas.
Gestiona posicionamiento, snap-to-grid, BFS para matches y detección de flotantes.
"""
import math
import random
from collections import deque

from game.bubble import Bubble
from game.constants import BUBBLE_COLORS, BUBBLE_DIAMETER


class BubbleGrid:
    def __init__(self, cols, max_rows, radius, x_offset, y_offset):
        self.cols = cols
        self.max_rows = max_rows
        self.radius = radius
        self.diameter = radius * 2
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.row_height = int(self.diameter * 0.866)

        # Datos: grid[row][col] = Bubble | None
        self.grid = [[None for _ in range(cols)] for _ in range(max_rows)]

        # Listas de animación
        self.popping_bubbles: list[Bubble] = []
        self.falling_bubbles: list[Bubble] = []

    # ─── Geometría ───────────────────────────────────────
    def get_col_count(self, row):
        """Filas impares tienen una columna menos."""
        return self.cols - 1 if row % 2 == 1 else self.cols

    def get_bubble_pos(self, row, col):
        """Posición en píxeles del centro de una celda."""
        x = self.x_offset + col * self.diameter + self.radius
        if row % 2 == 1:
            x += self.radius  # offset hexagonal
        y = self.y_offset + row * self.row_height + self.radius
        return x, y

    def get_grid_pos(self, x, y):
        """Convertir píxeles a celda (row, col) más cercana."""
        row = round((y - self.y_offset - self.radius) / self.row_height)
        row = max(0, min(row, self.max_rows - 1))

        adj_x = x - self.x_offset - self.radius
        if row % 2 == 1:
            adj_x -= self.radius
        col = round(adj_x / self.diameter)
        col = max(0, min(col, self.get_col_count(row) - 1))
        return row, col

    # ─── Vecinos (hex grid) ──────────────────────────────
    def get_neighbors(self, row, col):
        """Retorna las celdas vecinas válidas en grilla hexagonal."""
        neighbors = []
        # Misma fila
        if col > 0:
            neighbors.append((row, col - 1))
        if col < self.get_col_count(row) - 1:
            neighbors.append((row, col + 1))

        # Filas adyacentes
        if row % 2 == 0:
            offsets = [-1, 0]
        else:
            offsets = [0, 1]

        for dr in (-1, 1):
            nr = row + dr
            if 0 <= nr < self.max_rows:
                for dc in offsets:
                    nc = col + dc
                    if 0 <= nc < self.get_col_count(nr):
                        neighbors.append((nr, nc))
        return neighbors

    # ─── Colocación ──────────────────────────────────────
    def place_bubble(self, bubble, row, col):
        """Colocar burbuja en la grilla. Retorna True si tuvo éxito."""
        if not (0 <= row < self.max_rows):
            return False
        if not (0 <= col < self.get_col_count(row)):
            return False

        if self.grid[row][col] is not None:
            # Buscar celda vacía cercana
            best = None
            best_dist = float('inf')
            for dr in range(-2, 3):
                for dc in range(-2, 3):
                    nr, nc = row + dr, col + dc
                    if 0 <= nr < self.max_rows and 0 <= nc < self.get_col_count(nr):
                        if self.grid[nr][nc] is None:
                            bx, by = self.get_bubble_pos(nr, nc)
                            d = math.hypot(bubble.x - bx, bubble.y - by)
                            if d < best_dist:
                                best_dist = d
                                best = (nr, nc)
            if best is None:
                return False
            row, col = best

        x, y = self.get_bubble_pos(row, col)
        bubble.x = x
        bubble.y = y
        bubble.moving = False
        bubble.vx = 0
        bubble.vy = 0
        self.grid[row][col] = bubble
        return True

    def snap_moving_bubble(self, bubble):
        """Ajustar burbuja en movimiento a la celda más cercana."""
        row, col = self.get_grid_pos(bubble.x, bubble.y)

        if self.grid[row][col] is not None:
            best = None
            best_dist = float('inf')
            for dr in range(-2, 3):
                for dc in range(-2, 3):
                    nr, nc = row + dr, col + dc
                    if 0 <= nr < self.max_rows and 0 <= nc < self.get_col_count(nr):
                        if self.grid[nr][nc] is None:
                            bx, by = self.get_bubble_pos(nr, nc)
                            d = math.hypot(bubble.x - bx, bubble.y - by)
                            if d < best_dist:
                                best_dist = d
                                best = (nr, nc)
            if best:
                row, col = best
            else:
                return None, None

        if self.place_bubble(bubble, row, col):
            return row, col
        return None, None

    # ─── BFS: Matches ────────────────────────────────────
    def find_matches(self, row, col):
        """BFS para encontrar burbujas conectadas del mismo color."""
        if self.grid[row][col] is None:
            return []

        target = self.grid[row][col].color_index
        visited = set()
        queue = deque([(row, col)])
        matched = []

        while queue:
            r, c = queue.popleft()
            if (r, c) in visited:
                continue
            visited.add((r, c))
            if self.grid[r][c] is None:
                continue
            if self.grid[r][c].color_index != target:
                continue
            matched.append((r, c))
            for nr, nc in self.get_neighbors(r, c):
                if (nr, nc) not in visited:
                    queue.append((nr, nc))
        return matched

    # ─── BFS: Flotantes ──────────────────────────────────
    def find_floating(self):
        """Encontrar burbujas no conectadas al techo (fila 0)."""
        connected = set()
        queue = deque()

        for c in range(self.cols):
            if self.grid[0][c] is not None:
                queue.append((0, c))
                connected.add((0, c))

        while queue:
            r, c = queue.popleft()
            for nr, nc in self.get_neighbors(r, c):
                if (nr, nc) not in connected:
                    if 0 <= nr < self.max_rows and 0 <= nc < self.get_col_count(nr):
                        if self.grid[nr][nc] is not None:
                            connected.add((nr, nc))
                            queue.append((nr, nc))

        floating = []
        for r in range(self.max_rows):
            for c in range(self.get_col_count(r)):
                if self.grid[r][c] is not None and (r, c) not in connected:
                    floating.append((r, c))
        return floating

    # ─── Remoción ────────────────────────────────────────
    def remove_bubbles(self, positions, pop=True):
        """Eliminar burbujas y iniciar animación (pop o caída)."""
        removed = []
        for r, c in positions:
            b = self.grid[r][c]
            if b is not None:
                if pop:
                    b.start_pop()
                    self.popping_bubbles.append(b)
                else:
                    b.start_fall()
                    self.falling_bubbles.append(b)
                removed.append(b)
                self.grid[r][c] = None
        return removed

    # ─── Colisión con burbuja en movimiento ──────────────
    def check_collision(self, bubble):
        """¿La burbuja en movimiento colisiona con alguna estática o el techo?"""
        for r in range(self.max_rows):
            for c in range(self.get_col_count(r)):
                if self.grid[r][c] is not None:
                    if bubble.collides_with(self.grid[r][c]):
                        return True
        if bubble.y - bubble.radius <= self.y_offset:
            return True
        return False

    # ─── Estado del juego ────────────────────────────────
    def get_lowest_row(self):
        """Fila más baja con burbujas."""
        for r in range(self.max_rows - 1, -1, -1):
            for c in range(self.get_col_count(r)):
                if self.grid[r][c] is not None:
                    return r
        return -1

    def is_cleared(self):
        """¿Se eliminaron todas las burbujas? (condición de victoria)."""
        for r in range(self.max_rows):
            for c in range(self.get_col_count(r)):
                if self.grid[r][c] is not None:
                    return False
        return True

    def get_active_colors(self):
        """Retorna set de color_index activos en la grilla."""
        colors = set()
        for r in range(self.max_rows):
            for c in range(self.get_col_count(r)):
                if self.grid[r][c] is not None:
                    colors.add(self.grid[r][c].color_index)
        return colors

    # ─── Bajada de techo ─────────────────────────────────
    def add_row_at_top(self):
        """Baja todas las filas y agrega una nueva arriba."""
        # Desplazar hacia abajo
        for r in range(self.max_rows - 1, 0, -1):
            for c in range(self.get_col_count(r)):
                if c < self.get_col_count(r - 1):
                    self.grid[r][c] = self.grid[r - 1][c]
                else:
                    self.grid[r][c] = None

        # Limpiar fila 0
        for c in range(self.cols):
            self.grid[0][c] = None

        # Agregar burbujas nuevas
        num_colors = len(BUBBLE_COLORS)
        for c in range(self.get_col_count(0)):
            ci = random.randint(0, num_colors - 1)
            b = Bubble(ci, radius=self.radius)
            x, y = self.get_bubble_pos(0, c)
            b.x = x
            b.y = y
            self.grid[0][c] = b

        self._update_all_positions()

    def _update_all_positions(self):
        """Recalcular posiciones de todas las burbujas."""
        for r in range(self.max_rows):
            for c in range(self.get_col_count(r)):
                if self.grid[r][c] is not None:
                    x, y = self.get_bubble_pos(r, c)
                    self.grid[r][c].x = x
                    self.grid[r][c].y = y

    # ─── Update / Draw ───────────────────────────────────
    def update(self):
        self.popping_bubbles = [b for b in self.popping_bubbles if b.update()]
        self.falling_bubbles = [b for b in self.falling_bubbles if b.update()]

    def draw(self, surface):
        # Burbujas estáticas
        for r in range(self.max_rows):
            for c in range(self.get_col_count(r)):
                if self.grid[r][c] is not None:
                    self.grid[r][c].draw(surface)
        # Animaciones
        for b in self.popping_bubbles:
            b.draw(surface)
        for b in self.falling_bubbles:
            b.draw(surface)
