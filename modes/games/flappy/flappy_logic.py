import pygame
import cv2
import random
import time
import os
from collections import deque

class FlappyBirdGame:
    def __init__(self, width=1280, height=720):
        self.width, self.height = width, height
        self.dir_path = os.path.dirname(os.path.realpath(__file__))

        # --- INICIALIZACIÓN DE MÓDULOS DE PYGAME ---
        if not pygame.font.get_init():
            pygame.font.init()
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        
        # Estados
        self.MENU, self.PLAYING, self.GAME_OVER = 0, 1, 2
        self.current_state = self.MENU
        
        self._load_assets()
        
        # Físicas
        self.gravity = 0.5
        self.jump_strength = -10
        self.bird_frame = self.bird_img.get_rect()
        
        self.reset_game("normal")

    def _load_assets(self):
        def get_p(f, n): return os.path.join(self.dir_path, f, n)
        
        # Imágenes
        self.bird_img = pygame.image.load(get_p("assets", "bird_sprite.png"))
        self.bird_img = pygame.transform.scale(self.bird_img, (int(self.bird_img.get_width() / 6), int(self.bird_img.get_height() / 6)))
        
        self.pipe_img = pygame.image.load(get_p("assets", "pipe_sprite_single.png"))
        self.pipe_img = pygame.transform.scale(self.pipe_img, (160, 800))
        self.pipe_template = self.pipe_img.get_rect()
        
        # Sonidos
        if not pygame.mixer.get_init(): pygame.mixer.init()
        self.wing_sound = pygame.mixer.Sound(get_p("assets", "sfx_wing.wav"))
        self.point_sound = pygame.mixer.Sound(get_p("assets", "sfx_point.wav"))
        
        self.font_main = pygame.font.SysFont("Helvetica Bold.ttf", 64)
        self.font_ui = pygame.font.SysFont("Helvetica Bold.ttf", 40)

    def reset_game(self, difficulty):
        self.pipe_frames = deque()
        self.score = 0
        self.didUpdateScore = False
        self.bird_frame.center = (self.width // 6, self.height // 2)
        self.bird_velocity_y = 0
        self.game_clock = time.time()
        self.stage = 1
        self.pipeSpawnTimer = 0

        if difficulty == "easy":
            self.space_between_pipes, self.time_between_pipe_spawn, self.dist_between_pipes = 350, 60, 400
        elif difficulty == "hard":
            self.space_between_pipes, self.time_between_pipe_spawn, self.dist_between_pipes = 180, 30, 600
        else: # Normal
            self.space_between_pipes, self.time_between_pipe_spawn, self.dist_between_pipes = 250, 40, 500

        self.pipe_velocity = self.dist_between_pipes / self.time_between_pipe_spawn

    def update(self, frame_cv, lm_list, pinch, pinch_started):
        # Superficie de dibujo
        win = pygame.Surface((self.width, self.height))
        
        cam_rgb = cv2.cvtColor(frame_cv, cv2.COLOR_BGR2RGB)
        # --------------------------------------

        # Convertir a superficie de Pygame (manteniendo el swapaxes para la orientación)
        cam_surf = pygame.surfarray.make_surface(cam_rgb.swapaxes(0, 1))
        win.blit(cam_surf, (0, 0))
        
        # Overlay para que se vean mejor los sprites
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 40))
        win.blit(overlay, (0, 0))

        if self.current_state == self.MENU:
            self._draw_menu(win, lm_list, pinch_started)
            
        elif self.current_state == self.PLAYING:
            self._run_physics(pinch_started)
            self._draw_playing(win)
            
        elif self.current_state == self.GAME_OVER:
            self._draw_game_over(win, lm_list, pinch_started)

        # Dibujar cursor de FingMix
        if lm_list:
            p_color = (0, 255, 0) if pinch else (255, 255, 255)
            pygame.draw.circle(win, p_color, (lm_list[8][1], lm_list[8][2]), 10, 2)

        return self._pygame_to_cv2(win)

    def _run_physics(self, pinch_started):
        if pinch_started:
            self.wing_sound.play()
            self.bird_velocity_y = self.jump_strength

        self.bird_velocity_y += self.gravity
        self.bird_frame.y += self.bird_velocity_y

        # Límites
        if self.bird_frame.top < 0: self.bird_frame.y, self.bird_velocity_y = 0, 0
        if self.bird_frame.bottom > self.height: self.bird_frame.y, self.bird_velocity_y = self.height - self.bird_frame.height, 0

        # Tuberías
        for pf in self.pipe_frames:
            pf[0].x -= self.pipe_velocity
            pf[1].x -= self.pipe_velocity

        if len(self.pipe_frames) > 0 and self.pipe_frames[0][0].right < 0:
            self.pipe_frames.popleft()

        # Spawning
        if self.pipeSpawnTimer == 0:
            top = self.pipe_template.copy()
            top.x, top.y = self.width, random.randint(120 - 800, self.height - 140 - self.space_between_pipes - 800)
            bottom = self.pipe_template.copy()
            bottom.x, bottom.y = self.width, top.y + 800 + self.space_between_pipes
            self.pipe_frames.append([top, bottom])

        self.pipeSpawnTimer += 1
        if self.pipeSpawnTimer >= self.time_between_pipe_spawn: self.pipeSpawnTimer = 0

        # Dificultad incremental
        if time.time() - self.game_clock >= 10:
            self.time_between_pipe_spawn *= 5/6
            self.pipe_velocity = self.dist_between_pipes / self.time_between_pipe_spawn
            self.stage += 1
            self.game_clock = time.time()

        # Colisiones y Score
        checker = True
        for pf in self.pipe_frames:
            if pf[0].left <= self.bird_frame.x <= pf[0].right:
                checker = False
                if not self.didUpdateScore:
                    self.point_sound.play()
                    self.score += 1
                    self.didUpdateScore = True
            if self.bird_frame.colliderect(pf[0]) or self.bird_frame.colliderect(pf[1]):
                self.current_state = self.GAME_OVER
        if checker: self.didUpdateScore = False

    def _draw_playing(self, win):
        angle = max(min(-self.bird_velocity_y * 3, 35), -90)
        rotated_bird = pygame.transform.rotate(self.bird_img, angle)
        rotated_rect = rotated_bird.get_rect(center=self.bird_frame.center)
        
        for pf in self.pipe_frames:
            win.blit(self.pipe_img, pf[1])
            win.blit(pygame.transform.flip(self.pipe_img, 0, 1), pf[0])
            
        win.blit(rotated_bird, rotated_rect.topleft)
        
        win.blit(self.font_ui.render(f'Stage {self.stage}', True, (255, 255, 255)), (20, 20))
        win.blit(self.font_ui.render(f'Score: {self.score}', True, (255, 255, 255)), (20, 60))

    def _draw_menu(self, win, lm_list, pinch_started):
        title = self.font_main.render('Flappy Bird Art', True, (255, 255, 255))
        win.blit(title, title.get_rect(center=(self.width//2, 100)))
        
        opts = [("Fácil", "easy", 250), ("Normal", "normal", 330), ("Difícil", "hard", 410)]
        for text, diff, y in opts:
            rect = pygame.Rect(self.width//2 - 100, y, 200, 60)
            hover = lm_list and rect.collidepoint(lm_list[8][1], lm_list[8][2])
            color = (100, 255, 100) if hover else (50, 200, 50)
            pygame.draw.rect(win, color, rect, border_radius=10)
            txt_surf = self.font_ui.render(text, True, (255, 255, 255))
            win.blit(txt_surf, txt_surf.get_rect(center=rect.center))
            
            if hover and pinch_started:
                self.reset_game(diff)
                self.current_state = self.PLAYING

    def _draw_game_over(self, win, lm_list, pinch_started):
        txt = self.font_main.render('¡GAME OVER!', True, (255, 50, 50))
        win.blit(txt, txt.get_rect(center=(self.width//2, 200)))
        
        rect = pygame.Rect(self.width//2 - 120, 350, 240, 60)
        hover = lm_list and rect.collidepoint(lm_list[8][1], lm_list[8][2])
        pygame.draw.rect(win, (100, 100, 255) if hover else (50, 50, 200), rect, border_radius=10)
        btn_txt = self.font_ui.render("REINTENTAR", True, (255, 255, 255))
        win.blit(btn_txt, btn_txt.get_rect(center=rect.center))
        
        if hover and pinch_started: self.current_state = self.MENU

    def _pygame_to_cv2(self, surface):
        view = pygame.surfarray.array3d(surface)
        view = view.transpose([1, 0, 2])
        return cv2.cvtColor(view, cv2.COLOR_RGB2BGR)