"""
Escena de fin de juego (victoria o derrota).
Muestra puntuación final y opciones para continuar.
"""
import math
import pygame

from game.ui import Button, draw_cursor, draw_hand_indicator
from game.constants import SCREEN_WIDTH, SCREEN_HEIGHT, DIFFICULTY


class GameOverScene:
    def __init__(self, is_winner, score, difficulty, sound_manager=None):
        self.is_winner = is_winner
        self.score = score
        self.difficulty = difficulty
        self.config = DIFFICULTY[difficulty]
        self.sound_manager = sound_manager

        cx = SCREEN_WIDTH // 2

        self.buttons = {
            'replay': Button(
                cx - 140, 420, 280, 52,
                'JUGAR DE NUEVO', (15, 80, 80), (255, 255, 255),
                (25, 130, 130), 24,
            ),
            'menu': Button(
                cx - 140, 492, 280, 52,
                'MENU PRINCIPAL', (55, 55, 75), (255, 255, 255),
                (80, 80, 110), 24,
            ),
            'exit': Button(
                cx - 110, 564, 220, 46,
                'SALIR', (60, 60, 60), (200, 200, 200),
                (90, 90, 90), 22,
            ),
        }

        self.result = None
        self._timer = 0
        self._score_anim = 0
        self._prev_hover = set()

    # ─────────────────────────────────────────────────────
    def update(self, hand_tracker):
        self._timer += 1
        self.result = None

        # Animar puntuación
        if self._score_anim < self.score:
            diff = self.score - self._score_anim
            self._score_anim += max(1, diff // 8)
            if self._score_anim > self.score:
                self._score_anim = self.score

        fp = hand_tracker.index_pos
        ip = hand_tracker.is_pinching
        ps = hand_tracker.pinch_just_started

        current_hover = set()

        for key, btn in self.buttons.items():
            if btn.update(fp, ip, ps):
                self.result = key
                if self.sound_manager:
                    self.sound_manager.play_button_click()

            if btn.hovering:
                current_hover.add(key)
                if key not in self._prev_hover and self.sound_manager:
                    self.sound_manager.play_button_hover()

        self._prev_hover = current_hover
        return self.result

    # ─────────────────────────────────────────────────────
    def draw(self, surface, camera_surface, hand_tracker):
        # Fondo
        if camera_surface is not None:
            surface.blit(camera_surface, (0, 0))

        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((5, 5, 20, 200))
        surface.blit(ov, (0, 0))

        cx = SCREEN_WIDTH // 2

        # Título
        tf = pygame.font.SysFont('Segoe UI', 56, bold=True)
        if self.is_winner:
            txt = 'VICTORIA!'
            color = (0, 255, 200)
        else:
            txt = 'GAME OVER'
            color = (255, 80, 80)

        shadow = tf.render(txt, True, (0, 0, 0))
        surface.blit(shadow, shadow.get_rect(center=(cx + 3, 143)))
        title = tf.render(txt, True, color)
        surface.blit(title, title.get_rect(center=(cx, 140)))

        # Dificultad
        df = pygame.font.SysFont('Segoe UI', 20)
        dt = df.render(f"Modo: {self.config['name']}", True, self.config['color'])
        surface.blit(dt, dt.get_rect(center=(cx, 205)))

        # Panel de puntuación
        pw, ph = 320, 130
        px = cx - pw // 2
        py = 250
        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill((15, 15, 40, 190))
        pygame.draw.rect(panel, (0, 200, 150, 70),
                         (0, 0, pw, ph), 2, border_radius=14)
        surface.blit(panel, (px, py))

        lf = pygame.font.SysFont('Segoe UI', 18)
        lt = lf.render('PUNTUACION FINAL', True, (180, 180, 220))
        surface.blit(lt, lt.get_rect(center=(cx, py + 35)))

        vf = pygame.font.SysFont('Segoe UI', 48, bold=True)
        vt = vf.render(f'{self._score_anim:,}', True, (0, 255, 200))
        surface.blit(vt, vt.get_rect(center=(cx, py + 82)))

        # Botones
        for btn in self.buttons.values():
            btn.draw(surface)

        # Indicador y cursor
        draw_hand_indicator(surface, hand_tracker.handedness)
        draw_cursor(surface, hand_tracker.index_pos, hand_tracker.is_pinching)
