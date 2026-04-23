"""
Shooter: cañón/lanzador de burbujas.
Gestiona la mecánica de arrastre (slingshot) para apuntar y disparar.
"""
import math
import random
import pygame

from game.bubble import Bubble
from game.constants import (
    GRID_X_OFFSET, GRID_Y_OFFSET, GRID_COLS,
    BUBBLE_DIAMETER, SCREEN_WIDTH, SCREEN_HEIGHT,
    SHOOT_SPEED_MIN, SHOOT_SPEED_MAX, PULL_FORCE_FACTOR,
)


class Shooter:
    def __init__(self, x, y, radius, num_colors):
        self.x = x
        self.y = y
        self.radius = radius
        self.num_colors = num_colors

        # Burbujas actual y siguiente
        self.current_bubble = self._new_bubble()
        self.next_bubble = self._new_bubble()
        self.next_bubble.x = self.x + 70
        self.next_bubble.y = self.y

        # Estado de arrastre
        self.dragging = False
        self.drag_start = None
        self.drag_current = None
        self.shoot_angle = -math.pi / 2   # recto hacia arriba
        self.shoot_power = 0.0

        # Trayectoria
        self.trajectory_points = []

        # Burbuja disparada
        self.shot_bubble = None
        self.shot_active = False

        # Estadísticas
        self.shots_fired = 0
        self.combo_count = 0

    # ─── Helpers ─────────────────────────────────────────
    def _new_bubble(self):
        ci = random.randint(0, self.num_colors - 1)
        return Bubble(ci, self.x, self.y, self.radius)

    def sync_colors(self, active_colors):
        """Sincronizar colores disponibles con los de la grilla."""
        if active_colors:
            self.num_colors = max(active_colors) + 1

    # ─── Interacción de arrastre ─────────────────────────
    def can_start_drag(self, fx, fy):
        """¿El dedo está sobre la burbuja actual?"""
        if self.shot_active:
            return False
        return math.hypot(fx - self.x, fy - self.y) < self.radius * 2.5

    def start_drag(self, fx, fy):
        self.dragging = True
        self.drag_start = (fx, fy)
        self.drag_current = (fx, fy)

    def update_drag(self, fx, fy):
        if not self.dragging:
            return
        self.drag_current = (fx, fy)

        # Dirección tipo slingshot (opuesto al arrastre)
        dx = self.x - fx
        dy = self.y - fy

        # Forzar que apunte hacia arriba
        if dy >= 0:
            dy = -1

        self.shoot_angle = math.atan2(dy, dx)

        # Limitar ángulo (no disparar demasiado horizontal)
        min_a = -math.pi + 0.18
        max_a = -0.18
        self.shoot_angle = max(min_a, min(max_a, self.shoot_angle))

        # Potencia basada en distancia vertical de arrastre
        pull = max(0, fy - self.y)
        self.shoot_power = min(1.0, pull * PULL_FORCE_FACTOR)

        self._calc_trajectory()

    def release_drag(self):
        """Soltar el arrastre → disparar."""
        if not self.dragging:
            return False
        self.dragging = False

        if self.shoot_power < 0.1:
            self.shoot_power = 0
            self.trajectory_points = []
            return False

        # ¡Disparar!
        speed = SHOOT_SPEED_MIN + self.shoot_power * (SHOOT_SPEED_MAX - SHOOT_SPEED_MIN)
        self.current_bubble.vx = math.cos(self.shoot_angle) * speed
        self.current_bubble.vy = math.sin(self.shoot_angle) * speed
        self.current_bubble.moving = True

        self.shot_bubble = self.current_bubble
        self.shot_active = True
        self.shots_fired += 1

        # Preparar siguiente burbuja
        self.current_bubble = self.next_bubble
        self.current_bubble.x = self.x
        self.current_bubble.y = self.y
        self.next_bubble = self._new_bubble()
        self.next_bubble.x = self.x + 70
        self.next_bubble.y = self.y

        self.shoot_power = 0
        self.trajectory_points = []
        return True

    # ─── Trayectoria ─────────────────────────────────────
    def _calc_trajectory(self, max_bounces=3):
        if self.shoot_power < 0.05:
            self.trajectory_points = []
            return

        speed = SHOOT_SPEED_MIN + self.shoot_power * (SHOOT_SPEED_MAX - SHOOT_SPEED_MIN)
        vx = math.cos(self.shoot_angle) * speed
        vy = math.sin(self.shoot_angle) * speed
        x, y = float(self.x), float(self.y)

        pts = []
        bounces = 0
        left = GRID_X_OFFSET
        right = GRID_X_OFFSET + GRID_COLS * BUBBLE_DIAMETER

        for step in range(300):
            x += vx
            y += vy

            if x - self.radius < left:
                x = left + self.radius
                vx = -vx
                bounces += 1
            elif x + self.radius > right:
                x = right - self.radius
                vx = -vx
                bounces += 1

            if bounces > max_bounces or y < GRID_Y_OFFSET:
                break

            if step % 3 == 0:
                pts.append((int(x), int(y)))

        self.trajectory_points = pts

    # ─── Actualización del disparo ───────────────────────
    def update_shot(self, grid):
        """Mover burbuja disparada. Retorna (hit, row, col)."""
        if not self.shot_active or self.shot_bubble is None:
            return False, -1, -1

        b = self.shot_bubble
        spd = math.hypot(b.vx, b.vy)
        steps = max(1, int(spd / (self.radius * 0.5)))
        svx = b.vx / steps
        svy = b.vy / steps

        left = GRID_X_OFFSET
        right = GRID_X_OFFSET + GRID_COLS * BUBBLE_DIAMETER

        for _ in range(steps):
            b.x += svx
            b.y += svy

            # Rebote en paredes
            if b.x - b.radius < left:
                b.x = left + b.radius
                b.vx = -b.vx
                svx = -svx
            elif b.x + b.radius > right:
                b.x = right - b.radius
                b.vx = -b.vx
                svx = -svx

            # Colisión con grilla
            if grid.check_collision(b):
                b.moving = False
                row, col = grid.snap_moving_bubble(b)
                self.shot_active = False
                self.shot_bubble = None
                return (True, row, col) if row is not None else (False, -1, -1)

            # Techo
            if b.y < GRID_Y_OFFSET:
                b.y = GRID_Y_OFFSET + b.radius
                b.moving = False
                row, col = grid.snap_moving_bubble(b)
                self.shot_active = False
                self.shot_bubble = None
                return (True, row, col) if row is not None else (False, -1, -1)

            # Fuera de pantalla (seguridad)
            if b.y > SCREEN_HEIGHT + 50 or b.y < -50:
                self.shot_active = False
                self.shot_bubble = None
                return False, -1, -1

        return False, -1, -1

    # ─── Dibujo ──────────────────────────────────────────
    def draw(self, surface, trajectory_bounces=3):
        # Burbuja actual
        if not self.shot_active:
            self.current_bubble.draw(surface)

        # Siguiente burbuja (preview)
        if self.next_bubble:
            nx, ny = int(self.next_bubble.x), int(self.next_bubble.y)
            font = pygame.font.SysFont('Segoe UI', 12)
            lbl = font.render('NEXT', True, (180, 180, 200))
            surface.blit(lbl, (nx - 15, ny - 28))
            c = self.next_bubble.color
            sr = int(self.radius * 0.7)
            dk = (max(0, c[0] - 40), max(0, c[1] - 40), max(0, c[2] - 40))
            pygame.draw.circle(surface, dk, (nx, ny), sr)
            pygame.draw.circle(surface, c, (nx, ny), sr - 1)

        # Trayectoria punteada
        if self.dragging and self.trajectory_points:
            limit = trajectory_bounces * 20
            for i, (px, py) in enumerate(self.trajectory_points[:limit]):
                alpha = max(40, 220 - i * 4)
                sz = max(1, 3 - i // 20)
                s = pygame.Surface((sz * 2 + 2, sz * 2 + 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (255, 255, 255, alpha), (sz + 1, sz + 1), sz)
                surface.blit(s, (px - sz - 1, py - sz - 1))

        # Barra de potencia
        if self.dragging:
            bx = self.x - 50
            by = self.y + 30
            bw, bh = 100, 8
            pygame.draw.rect(surface, (40, 40, 40), (bx, by, bw, bh), border_radius=4)
            fw = int(bw * self.shoot_power)
            if fw > 0:
                r = min(255, int(self.shoot_power * 2 * 255))
                g = min(255, int((1 - self.shoot_power) * 2 * 255))
                pygame.draw.rect(surface, (r, g, 50), (bx, by, fw, bh), border_radius=4)
            pygame.draw.rect(surface, (180, 180, 180), (bx, by, bw, bh), 1, border_radius=4)

            # Línea de arrastre
            if self.drag_current:
                ln = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                pygame.draw.line(ln, (255, 255, 255, 80),
                                 (int(self.x), int(self.y)),
                                 (int(self.drag_current[0]), int(self.drag_current[1])), 2)
                surface.blit(ln, (0, 0))

        # Burbuja en vuelo
        if self.shot_active and self.shot_bubble:
            self.shot_bubble.draw(surface)

    # ─── Reset ───────────────────────────────────────────
    def reset(self, num_colors):
        self.num_colors = num_colors
        self.current_bubble = self._new_bubble()
        self.next_bubble = self._new_bubble()
        self.next_bubble.x = self.x + 70
        self.next_bubble.y = self.y
        self.dragging = False
        self.shot_active = False
        self.shot_bubble = None
        self.shots_fired = 0
        self.combo_count = 0
        self.shoot_power = 0
        self.trajectory_points = []
