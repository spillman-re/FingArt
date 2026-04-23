"""
Clase Bubble: representa una burbuja individual en el juego.
Incluye renderizado con efecto de gradiente/highlight y animaciones de pop/caída.
"""
import pygame
import math

# Colores de burbujas (mismos que en constants.py, copiados aquí para independencia)
_COLORS = [
    (231, 76, 60),     # Rojo
    (52, 152, 219),    # Azul
    (46, 204, 113),    # Verde
    (241, 196, 15),    # Amarillo
    (155, 89, 182),    # Morado
    (230, 126, 34),    # Naranja
]


class Bubble:
    def __init__(self, color_index, x=0, y=0, radius=20):
        self.color_index = color_index
        self.x = float(x)
        self.y = float(y)
        self.radius = radius

        # Física
        self.vx = 0.0
        self.vy = 0.0
        self.moving = False

        # Animación de pop
        self.popping = False
        self._pop_timer = 0
        self._pop_duration = 10

        # Animación de caída
        self.falling = False
        self._fall_speed = 0.0

    # ── Propiedades ─────────────────────────────────────
    @property
    def color(self):
        return _COLORS[self.color_index % len(_COLORS)]

    # ── Actualización ───────────────────────────────────
    def update(self):
        """Actualizar estado. Retorna False si debe eliminarse."""
        if self.moving:
            self.x += self.vx
            self.y += self.vy

        if self.popping:
            self._pop_timer += 1
            if self._pop_timer >= self._pop_duration:
                return False  # eliminar

        if self.falling:
            self._fall_speed += 0.5
            self.y += self._fall_speed
            if self.y > 800:
                return False

        return True

    # ── Dibujo ──────────────────────────────────────────
    def draw(self, surface):
        if self.popping:
            self._draw_pop(surface)
            return
        self._draw_normal(surface)

    def _draw_normal(self, surface):
        c = self.color
        r = self.radius
        ix, iy = int(self.x), int(self.y)

        # Sombra exterior (más oscuro)
        darker = (max(0, c[0] - 50), max(0, c[1] - 50), max(0, c[2] - 50))
        pygame.draw.circle(surface, darker, (ix, iy), r)

        # Cuerpo principal
        pygame.draw.circle(surface, c, (ix, iy), r - 2)

        # Highlight superior-izquierdo
        lighter = (min(255, c[0] + 90), min(255, c[1] + 90), min(255, c[2] + 90))
        hx = int(self.x - r * 0.3)
        hy = int(self.y - r * 0.3)
        pygame.draw.circle(surface, lighter, (hx, hy), max(1, r // 3))

        # Brillo pequeño (punto blanco)
        pygame.draw.circle(surface, (255, 255, 255), (hx - 1, hy - 1), max(1, r // 5))

        # Contorno sutil
        pygame.draw.circle(surface, (255, 255, 255), (ix, iy), r, 1)

    def _draw_pop(self, surface):
        progress = self._pop_timer / self._pop_duration
        r = int(self.radius * (1 - progress))
        if r <= 0:
            return
        alpha = int(255 * (1 - progress))
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        c = self.color
        pygame.draw.circle(s, (*c, alpha), (r, r), r)
        surface.blit(s, (int(self.x - r), int(self.y - r)))

    # ── Acciones ────────────────────────────────────────
    def start_pop(self):
        self.popping = True
        self._pop_timer = 0
        self.moving = False

    def start_fall(self):
        self.falling = True
        self.moving = False
        self._fall_speed = 0.0

    # ── Colisiones ──────────────────────────────────────
    def collides_with(self, other):
        dx = self.x - other.x
        dy = self.y - other.y
        dist = math.sqrt(dx * dx + dy * dy)
        return dist < (self.radius + other.radius) * 0.9

    def distance_to(self, x, y):
        dx = self.x - x
        dy = self.y - y
        return math.sqrt(dx * dx + dy * dy)
