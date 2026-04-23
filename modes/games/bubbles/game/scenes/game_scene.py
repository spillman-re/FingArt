"""
Escena principal del juego.
Contiene la grilla, el lanzador, HUD, y toda la lógica de gameplay.
"""
import math
import pygame

from game.grid import BubbleGrid
from game.shooter import Shooter
from game.level_generator import LevelGenerator
from game.particle import ParticleSystem
from game.ui import Button, ScoreDisplay, draw_cursor, draw_hand_indicator
from game.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    GRID_COLS, GRID_ROWS, BUBBLE_RADIUS, BUBBLE_DIAMETER,
    GRID_X_OFFSET, GRID_Y_OFFSET,
    SHOOTER_X, SHOOTER_Y,
    DANGER_LINE_Y, MIN_MATCH,
    DIFFICULTY,
)


class GameScene:
    def __init__(self, difficulty='easy', sound_manager=None):
        self.difficulty = difficulty
        self.config = DIFFICULTY[difficulty]
        self.sound_manager = sound_manager

        # Grilla
        self.grid = BubbleGrid(
            GRID_COLS, GRID_ROWS, BUBBLE_RADIUS,
            GRID_X_OFFSET, GRID_Y_OFFSET,
        )
        LevelGenerator.generate(self.grid, self.config)

        # Lanzador
        self.shooter = Shooter(
            SHOOTER_X, SHOOTER_Y, BUBBLE_RADIUS,
            self.config['colors'],
        )

        # Efectos
        self.particles = ParticleSystem()

        # Puntuación
        self.score_display = ScoreDisplay(20, 10)
        self.score = 0

        # UI
        self.exit_button = Button(
            SCREEN_WIDTH - 130, 10, 120, 38,
            'MENU', (80, 30, 30), (255, 255, 255),
            (130, 45, 45), 18, 8,
        )

        # Estado
        self.state = 'playing'  # 'playing' | 'win' | 'lose'
        self.shots_since_drop = 0
        self.combo_count = 0
        self.result = None      # 'menu' | 'win' | 'lose'

        # Animación de peligro
        self._danger_pulse = 0.0

        # Sonido de resultado ya reproducido
        self._result_sound_played = False

    # ─── Actualización ───────────────────────────────────
    def update(self, hand_tracker):
        self.result = None
        if self.state != 'playing':
            return self.result

        fp = hand_tracker.index_pos
        ip = hand_tracker.is_pinching
        ps = hand_tracker.pinch_just_started
        pr = hand_tracker.pinch_just_released

        # Botón de menú
        if self.exit_button.update(fp, ip, ps):
            if self.sound_manager:
                self.sound_manager.play_button_click()
            self.result = 'menu'
            return self.result

        # Interacción con el shooter
        if fp:
            fx, fy = fp

            # Iniciar arrastre
            if ps and not self.shooter.dragging:
                if self.shooter.can_start_drag(fx, fy):
                    self.shooter.start_drag(fx, fy)

            # Actualizar arrastre
            if self.shooter.dragging:
                self.shooter.update_drag(fx, fy)

            # Soltar arrastre
            if pr and self.shooter.dragging:
                if self.shooter.release_drag():
                    self.shots_since_drop += 1
                    # Sonido de disparo
                    if self.sound_manager:
                        self.sound_manager.play_shoot()

        # Actualizar burbuja disparada
        if self.shooter.shot_active:
            hit, row, col = self.shooter.update_shot(self.grid)
            if hit and row >= 0:
                self._process_hit(row, col)

        # Bajada de techo
        drop_interval = self.config['ceiling_drop_interval']
        if drop_interval > 0 and self.shots_since_drop >= drop_interval:
            self.grid.add_row_at_top()
            self.shots_since_drop = 0

        # Actualizar animaciones
        self.grid.update()
        self.particles.update()
        self.score_display.update()

        # Verificar estado
        self._check_game_state()

        # Pulso de peligro
        lowest = self.grid.get_lowest_row()
        if lowest >= 0:
            ly = GRID_Y_OFFSET + lowest * int(BUBBLE_DIAMETER * 0.866) + BUBBLE_RADIUS
            if ly > DANGER_LINE_Y - 80:
                self._danger_pulse += 0.1

        return self.result

    # ─── Procesar impacto ────────────────────────────────
    def _process_hit(self, row, col):
        matches = self.grid.find_matches(row, col)

        if len(matches) >= MIN_MATCH:
            popped = self.grid.remove_bubbles(matches, pop=True)
            for i, b in enumerate(popped):
                self.particles.emit_burst(b.x, b.y, b.color, 12)
                # Sonido de pop con variación
                if self.sound_manager:
                    self.sound_manager.play_pop(i)

            floating = self.grid.find_floating()
            dropped = self.grid.remove_bubbles(floating, pop=False)
            for b in dropped:
                self.particles.emit_fall(b.x, b.y, b.color, 6)

            # Puntuación
            pts = LevelGenerator.calculate_score(
                popped, dropped, self.combo_count, self.config
            )
            self.score += pts
            self.score_display.set_score(self.score)

            # Combos
            self.combo_count += 1
            if self.combo_count > 1:
                self.score_display.show_combo(f'COMBO x{self.combo_count}!')
                if self.sound_manager:
                    self.sound_manager.play_combo(self.combo_count - 1)
            elif len(popped) > 3:
                self.score_display.show_combo(f'{len(popped)} BURBUJAS!')
            if dropped:
                self.score_display.show_combo(f'+{len(dropped)} CAIDA!')
        else:
            self.combo_count = 0
            # Sonido de colisión (burbuja se adhiere sin match)
            if self.sound_manager:
                self.sound_manager.play_collision()

    # ─── Verificar victoria/derrota ──────────────────────
    def _check_game_state(self):
        # Victoria
        if self.grid.is_cleared():
            self.state = 'win'
            self.result = 'win'
            if not self._result_sound_played and self.sound_manager:
                self.sound_manager.play_win()
                self._result_sound_played = True
            return

        # Derrota
        lowest = self.grid.get_lowest_row()
        if lowest >= 0:
            ly = GRID_Y_OFFSET + lowest * int(BUBBLE_DIAMETER * 0.866) + BUBBLE_RADIUS
            if ly + BUBBLE_RADIUS > DANGER_LINE_Y:
                self.state = 'lose'
                self.result = 'lose'
                if not self._result_sound_played and self.sound_manager:
                    self.sound_manager.play_lose()
                    self._result_sound_played = True

    # ─── Dibujo ──────────────────────────────────────────
    def draw(self, surface, camera_surface, hand_tracker):
        # Fondo de cámara
        if camera_surface is not None:
            surface.blit(camera_surface, (0, 0))

        # Overlay oscuro
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((10, 10, 10, 140))
        surface.blit(ov, (0, 0))

        # Fondo del área de juego
        gw = GRID_COLS * BUBBLE_DIAMETER + 20
        gh = DANGER_LINE_Y - GRID_Y_OFFSET + 40
        bg = pygame.Surface((gw, gh), pygame.SRCALPHA)
        bg.fill((10, 10, 10, 120))
        surface.blit(bg, (GRID_X_OFFSET - 10, GRID_Y_OFFSET - 10))

        # Borde del área
        rect = pygame.Rect(
            GRID_X_OFFSET - 2, GRID_Y_OFFSET - 2,
            GRID_COLS * BUBBLE_DIAMETER + 4, gh - 16
        )
        pygame.draw.rect(surface, (0, 180, 140, 50), rect, 2, border_radius=4)

        # Línea de peligro
        if self._danger_pulse > 0:
            da = int(50 + 40 * abs(math.sin(self._danger_pulse)))
        else:
            da = 25
        dl = pygame.Surface((GRID_COLS * BUBBLE_DIAMETER, 2), pygame.SRCALPHA)
        dl.fill((255, 50, 50, da))
        surface.blit(dl, (GRID_X_OFFSET, DANGER_LINE_Y))

        sf = pygame.font.SysFont('Segoe UI', 11)
        dt = sf.render('LINEA DE PELIGRO', True, (255, 70, 70))
        surface.blit(dt, dt.get_rect(center=(SCREEN_WIDTH // 2, DANGER_LINE_Y + 12)))

        # Grilla
        self.grid.draw(surface)

        # Partículas
        self.particles.draw(surface)

        # Lanzador
        self.shooter.draw(surface, self.config['trajectory_length'])

        # HUD
        self.score_display.draw(surface)

        df = pygame.font.SysFont('Segoe UI', 16, bold=True)
        dc = self.config['color']
        surface.blit(df.render(self.config['name'], True, dc), (20, 68))

        if self.config['ceiling_drop_interval'] > 0:
            rem = self.config['ceiling_drop_interval'] - self.shots_since_drop
            c = (255, 200, 100) if rem <= 2 else (180, 180, 200)
            rsf = pygame.font.SysFont('Segoe UI', 14)
            surface.blit(rsf.render(f'Disparos hasta bajada: {rem}', True, c), (20, 92))

        # Botón menú
        self.exit_button.draw(surface)

        # Indicador y cursor
        draw_hand_indicator(surface, hand_tracker.handedness)
        draw_cursor(surface, hand_tracker.index_pos, hand_tracker.is_pinching)
