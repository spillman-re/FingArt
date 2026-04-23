"""
Escena del menú principal.
Muestra título, botones de dificultad (Fácil, Medio, Difícil), botón de salir.
Feed de cámara completo como fondo.
"""
import math
import pygame

from game.ui import Button, draw_cursor, draw_hand_indicator
from game.constants import SCREEN_WIDTH, SCREEN_HEIGHT


class MenuScene:
    def __init__(self, sound_manager=None):
        self.sound_manager = sound_manager
        cx = SCREEN_WIDTH // 2

        self.buttons = {
            'easy': Button(
                cx - 140, 320, 280, 52,
                'FACIL', (15, 90, 50), (255, 255, 255),
                (25, 140, 70), 26
            ),
            'medium': Button(
                cx - 140, 390, 280, 52,
                'MEDIO', (130, 120, 10), (255, 255, 255),
                (180, 165, 20), 26
            ),
            'hard': Button(
                cx - 140, 460, 280, 52,
                'DIFICIL', (120, 25, 25), (255, 255, 255),
                (180, 45, 45), 26
            ),
            'exit': Button(
                cx - 110, 545, 220, 48,
                'SALIR', (60, 60, 65), (200, 200, 200),
                (95, 95, 100), 24
            ),
        }

        self.result = None
        self._pulse = 0.0
        self._prev_hover = set()  # para detectar hover nuevo

    # ─────────────────────────────────────────────────────
    def update(self, hand_tracker):
        self._pulse += 0.05
        self.result = None

        fp = hand_tracker.index_pos
        ip = hand_tracker.is_pinching
        ps = hand_tracker.pinch_just_started

        current_hover = set()

        for key, btn in self.buttons.items():
            was_hovering = btn.hovering
            if btn.update(fp, ip, ps):
                self.result = key
                # Sonido de click
                if self.sound_manager:
                    self.sound_manager.play_button_click()
                return self.result

            # Detectar hover nuevo para sonido
            if btn.hovering:
                current_hover.add(key)
                if key not in self._prev_hover and self.sound_manager:
                    self.sound_manager.play_button_hover()

        self._prev_hover = current_hover
        return None

    # ─────────────────────────────────────────────────────
    def draw(self, surface, camera_surface, hand_tracker):
        # Fondo de cámara
        if camera_surface is not None:
            surface.blit(camera_surface, (0, 0))

        # Overlay oscuro
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((10, 10, 10, 160))
        surface.blit(ov, (0, 0))

        cx = SCREEN_WIDTH // 2

        # ── Título ──
        tf = pygame.font.SysFont('Segoe UI', 62, bold=True)
        sf = pygame.font.SysFont('Segoe UI', 20)

        # Sombra
        shadow = tf.render('BUBBLE SHOOTER', True, (0, 0, 0))
        sr = shadow.get_rect(center=(cx + 3, 113))
        surface.blit(shadow, sr)

        # Título principal
        title = tf.render('BUBBLE SHOOTER', True, (0, 230, 180))
        tr = title.get_rect(center=(cx, 110))
        surface.blit(title, tr)

        # Subtítulo
        sub = sf.render('Control por Gestos de Mano', True, (170, 170, 210))
        surface.blit(sub, sub.get_rect(center=(cx, 170)))

        # ── Instrucciones ──
        inf = pygame.font.SysFont('Segoe UI', 15)
        lines = [
            "Usa tu dedo indice como cursor",
            "Junta pulgar e indice para seleccionar",
        ]
        for i, line in enumerate(lines):
            t = inf.render(line, True, (140, 140, 165))
            surface.blit(t, t.get_rect(center=(cx, 210 + i * 22)))

        # ── Etiqueta de dificultad ──
        dlf = pygame.font.SysFont('Segoe UI', 16)
        dlabel = dlf.render('Selecciona la dificultad:', True, (180, 180, 200))
        surface.blit(dlabel, dlabel.get_rect(center=(cx, 295)))

        # ── Botones ──
        for btn in self.buttons.values():
            btn.draw(surface)

        # ── Indicador de mano y cursor ──
        draw_hand_indicator(surface, hand_tracker.handedness)
        draw_cursor(surface, hand_tracker.index_pos, hand_tracker.is_pinching)
