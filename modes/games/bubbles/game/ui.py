"""
Componentes de interfaz de usuario:
Button, ScoreDisplay, cursor, indicador de mano.
Todos interactúan mediante gestos (hover + pinch).
"""
import pygame
import math


# ═══════════════════════════════════════════════════════════
#  BOTÓN INTERACTIVO POR GESTOS
# ═══════════════════════════════════════════════════════════
class Button:
    def __init__(self, x, y, width, height, text,
                 color=(50, 50, 70), text_color=(255, 255, 255),
                 hover_color=None, font_size=28, border_radius=12):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.color = color
        self.text_color = text_color
        self.hover_color = hover_color or tuple(min(255, c + 35) for c in color)
        self.font_size = font_size
        self.border_radius = border_radius

        self.hovering = False
        self.pressed = False
        self._press_timer = 0
        self._hover_scale = 1.0
        self._glow = 0.0

    def contains(self, x, y):
        return (self.x <= x <= self.x + self.width and
                self.y <= y <= self.y + self.height)

    def update(self, finger_pos, is_pinching, pinch_just_started):
        """Retorna True si el botón fue activado."""
        self.hovering = False
        activated = False

        if finger_pos:
            if self.contains(*finger_pos):
                self.hovering = True
                if pinch_just_started:
                    self.pressed = True
                    self._press_timer = 8
                    activated = True

        # Animaciones suaves
        target = 1.06 if self.hovering else 1.0
        self._hover_scale += (target - self._hover_scale) * 0.2
        self._glow += ((100 if self.hovering else 0) - self._glow) * 0.15

        if self._press_timer > 0:
            self._press_timer -= 1
        else:
            self.pressed = False

        return activated

    def draw(self, surface):
        s = self._hover_scale
        w = int(self.width * s)
        h = int(self.height * s)
        x = self.x - (w - self.width) // 2
        y = self.y - (h - self.height) // 2

        if self.pressed:
            y += 2

        # Glow
        if self._glow > 3:
            gs = pygame.Surface((w + 24, h + 24), pygame.SRCALPHA)
            pygame.draw.rect(gs, (*self.hover_color, int(self._glow * 0.35)),
                             (0, 0, w + 24, h + 24),
                             border_radius=self.border_radius + 6)
            surface.blit(gs, (x - 12, y - 12))

        # Fondo
        c = self.hover_color if self.hovering else self.color
        if self.pressed:
            c = tuple(min(255, v + 50) for v in c)
        bs = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(bs, (*c, 220), (0, 0, w, h),
                         border_radius=self.border_radius)

        # Borde
        bc = (255, 255, 255, 150 if self.hovering else 60)
        pygame.draw.rect(bs, bc, (0, 0, w, h), 2,
                         border_radius=self.border_radius)
        surface.blit(bs, (x, y))

        # Texto
        font = pygame.font.SysFont('Segoe UI', self.font_size, bold=True)
        ts = font.render(self.text, True, self.text_color)
        tr = ts.get_rect(center=(x + w // 2, y + h // 2))
        surface.blit(ts, tr)


# ═══════════════════════════════════════════════════════════
#  DISPLAY DE PUNTUACIÓN
# ═══════════════════════════════════════════════════════════
class ScoreDisplay:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.score = 0
        self.display_score = 0
        self._combo_text = ""
        self._combo_timer = 0

    def set_score(self, score):
        self.score = score

    def show_combo(self, text):
        self._combo_text = text
        self._combo_timer = 60

    def update(self):
        if self.display_score < self.score:
            diff = self.score - self.display_score
            self.display_score += max(1, diff // 5)
            if self.display_score > self.score:
                self.display_score = self.score
        if self._combo_timer > 0:
            self._combo_timer -= 1

    def draw(self, surface):
        small = pygame.font.SysFont('Segoe UI', 16)
        big = pygame.font.SysFont('Segoe UI', 36, bold=True)

        lbl = small.render('SCORE', True, (180, 180, 200))
        surface.blit(lbl, (self.x, self.y))

        val = big.render(f'{self.display_score:,}', True, (0, 255, 200))
        surface.blit(val, (self.x, self.y + 18))

        if self._combo_timer > 0 and self._combo_text:
            cf = pygame.font.SysFont('Segoe UI', 20, bold=True)
            cs = cf.render(self._combo_text, True, (255, 215, 0))
            oy = int((60 - self._combo_timer) * 0.5)
            surface.blit(cs, (self.x, self.y + 58 - oy))


# ═══════════════════════════════════════════════════════════
#  CURSOR DE MANO
# ═══════════════════════════════════════════════════════════
def draw_cursor(surface, pos, is_pinching=False):
    """Dibuja el cursor basado en la posición del dedo índice."""
    if pos is None:
        return
    x, y = pos

    if is_pinching:
        # Estado pinch: círculo sólido
        pygame.draw.circle(surface, (255, 80, 80), (x, y), 14)
        pygame.draw.circle(surface, (255, 180, 180), (x, y), 9)
        pygame.draw.circle(surface, (255, 255, 255), (x, y), 4)
    else:
        # Cursor normal: anillo con glow
        glow = pygame.Surface((64, 64), pygame.SRCALPHA)
        pygame.draw.circle(glow, (0, 255, 150, 25), (32, 32), 28)
        pygame.draw.circle(glow, (0, 255, 150, 50), (32, 32), 20)
        surface.blit(glow, (x - 32, y - 32))
        pygame.draw.circle(surface, (0, 255, 150), (x, y), 13, 2)
        pygame.draw.circle(surface, (255, 255, 255), (x, y), 3)


# ═══════════════════════════════════════════════════════════
#  INDICADOR DE MANO
# ═══════════════════════════════════════════════════════════
def draw_hand_indicator(surface, handedness, x=20, y=680):
    """Muestra qué mano se detecta (o pide mostrar la mano)."""
    font = pygame.font.SysFont('Segoe UI', 14)
    if handedness:
        color = (180, 180, 200)
        txt = f"Mano: {handedness}"
    else:
        color = (255, 150, 150)
        txt = "Muestra tu mano a la camara"
    surface.blit(font.render(txt, True, color), (x, y))
