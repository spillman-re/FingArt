"""
Sistema de partículas para efectos visuales:
explosiones de burbujas, sparkles, caídas.
"""
import pygame
import random
import math


class Particle:
    """Una partícula individual con física básica."""

    __slots__ = ('x', 'y', 'vx', 'vy', 'color', 'life', 'max_life',
                 'size', 'gravity', 'alive')

    def __init__(self, x, y, color, speed=None, angle=None,
                 life=30, size=3, gravity=0.15):
        self.x = x
        self.y = y
        self.color = color
        speed = speed or random.uniform(2, 6)
        angle = angle if angle is not None else random.uniform(0, 2 * math.pi)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = life
        self.max_life = life
        self.size = size
        self.gravity = gravity
        self.alive = True

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        self.vx *= 0.99  # fricción sutil
        self.life -= 1
        if self.life <= 0:
            self.alive = False

    def draw(self, surface):
        if not self.alive:
            return
        t = max(0.0, self.life / self.max_life)
        sz = max(1, int(self.size * t))
        # Fade to white as particle dies
        r = min(255, int(self.color[0] * t + 255 * (1 - t)))
        g = min(255, int(self.color[1] * t + 255 * (1 - t)))
        b = min(255, int(self.color[2] * t + 255 * (1 - t)))
        pygame.draw.circle(surface, (r, g, b), (int(self.x), int(self.y)), sz)


class ParticleSystem:
    """Gestiona múltiples partículas."""

    def __init__(self):
        self.particles: list[Particle] = []

    # ── Emisores ────────────────────────────────────────
    def emit_burst(self, x, y, color, count=15):
        """Explosión radial (para burbujas que revientan)."""
        for _ in range(count):
            self.particles.append(Particle(
                x, y, color,
                speed=random.uniform(1.5, 7),
                angle=random.uniform(0, 2 * math.pi),
                life=random.randint(15, 35),
                size=random.randint(2, 5),
            ))

    def emit_sparkle(self, x, y, color, count=5):
        """Chispas suaves (para efectos decorativos)."""
        for _ in range(count):
            self.particles.append(Particle(
                x, y, color,
                speed=random.uniform(0.5, 2),
                angle=random.uniform(0, 2 * math.pi),
                life=random.randint(10, 20),
                size=random.randint(1, 3),
                gravity=0.05,
            ))

    def emit_fall(self, x, y, color, count=8):
        """Partículas cayendo (para burbujas flotantes)."""
        for _ in range(count):
            self.particles.append(Particle(
                x, y, color,
                speed=random.uniform(1, 4),
                angle=random.uniform(math.pi * 0.2, math.pi * 0.8),
                life=random.randint(20, 40),
                size=random.randint(2, 4),
                gravity=0.3,
            ))

    # ── Actualización y dibujo ──────────────────────────
    def update(self):
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.alive]

    def draw(self, surface):
        for p in self.particles:
            p.draw(surface)

    def clear(self):
        self.particles.clear()
