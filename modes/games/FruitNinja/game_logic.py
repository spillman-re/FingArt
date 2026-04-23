import pygame
import cv2
import numpy as np
import math
import random
import time
import os

# --- CLASE FRUTA (Mantenida de tu código original) ---
class FruitItem:
    def __init__(self, x, y, pic, bomb_img, u=25, g=-0.5):
        self.x = x
        self.y = y
        self.pic = pic
        self.u = u
        self.pos = x
        self.g = g
        self.is_bomb = (pic == bomb_img)
        self.exploded = False

    def show(self, win, angle):
        win.blit(pygame.transform.rotate(self.pic, angle), (self.x, self.y))

class FruitNinjaGame:
    def __init__(self, width=1280, height=720):
        # Adaptamos el tamaño a la resolución de FingMix
        self.WIDTH, self.HEIGHT = width, height

        if not pygame.mixer.get_init():
            pygame.mixer.init()
        if not pygame.font.get_init(): # <--- AGREGA ESTA LÍNEA
            pygame.font.init()
        
        # Variables de estado (Tus originales)
        self.a = [] # Lista de frutas
        self.score = 0
        self.lives = 3
        self.game_over = False
        self.last_spawn_time = 0
        self.spawn_delay = 1.5
        self.angle = 0
        self.last_sound_time = 0
        self.last_click_time = 0
        
        # Variables de movimiento y suavizado
        self.vx, self.vy = 0, 0
        self.prev_vx, self.prev_vy = 0, 0

        # Rutas dinámicas
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        
        # Inicialización de Pygame interna
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        
        self._load_assets()
        
        # Máscara del puntero (Tu estrella)
        self.small_star = pygame.transform.scale(self.star_img, (50, 50))
        self.maskp = pygame.mask.from_surface(self.small_star)
        
        pygame.mixer.music.play(-1)

    def _load_assets(self):
        def get_p(folder, file): return os.path.join(self.dir_path, folder, file)

        # Imágenes de fondo
        self.bg = pygame.transform.scale(pygame.image.load(get_p('images', 'bg.jpg')), (self.WIDTH, self.HEIGHT))
        
        # Frutas: Watermelon y Berry (Siguen el patrón 1, 2, 3)
        self.watermelon = [pygame.transform.scale(pygame.image.load(get_p('images', f'watermelon{i}.png')), (70,70)) for i in [1,2,3]]
        self.berry = [pygame.transform.scale(pygame.image.load(get_p('images', f'berry{i}.png')), (70,70)) for i in [1,2,3]]
        
        # NARANJA: Aquí estaba el error. Nombres exactos de tu carpeta:
        self.orange = [
            pygame.transform.scale(pygame.image.load(get_p('images', 'Orang1.png')), (70,70)),
            pygame.transform.scale(pygame.image.load(get_p('images', 'Orang2.png')), (70,70)),
            pygame.transform.scale(pygame.image.load(get_p('images', 'Orange3.png')), (70,70)) # <--- Con 'e'
        ]
        
        # Bomba (bomba1f.png, bomba2f.png)
        self.bomb = [pygame.transform.scale(pygame.image.load(get_p('images', f'bomba{i}f.png')), (70, 70)) for i in [1,2]]
        
        # Los demás assets
        self.star_img = pygame.image.load(get_p('images', 'star1.png'))
        self.corazon = pygame.transform.scale(pygame.image.load(get_p('images', 'corazon1.png')), (60, 60))
        self.corazon_vacio = pygame.transform.scale(pygame.image.load(get_p('images', 'corazon2.png')), (60, 60))
        
        # Fuentes y Sonidos (se mantienen igual)
        self.myfont = pygame.font.SysFont("monospace", 24, bold=True)
        self.big_font = pygame.font.SysFont("monospace", 60, bold=True)
        pygame.mixer.music.load(get_p('sounds', "Kevin MacLeod - Pixelland.wav"))
        self.slice_sounds = [pygame.mixer.Sound(get_p('sounds', f"corte{i}f.wav")) for i in [1,2]]
        self.whoosh_sounds = [pygame.mixer.Sound(get_p('sounds', f"mov{i}.wav")) for i in [1,2]]
        self.explosion_sound = pygame.mixer.Sound(get_p('sounds', "bombf.wav"))

    def update(self, frame_cv, lm_list, pinch):
        # 1. Crear superficie de Pygame para procesar
        win = pygame.Surface((self.WIDTH, self.HEIGHT))
        win.blit(self.bg, (0, 0))

        # 2. Lógica de posicionamiento y suavizado (Tu lógica original)
        old_vx, old_vy = self.vx, self.vy
        
        if len(lm_list) != 0:
            cx, cy = lm_list[8][1], lm_list[8][2] # Dedo índice
            # Mapeo a resolución de pantalla y suavizado 0.7/0.3
            self.vx = int(cx * 0.7 + self.prev_vx * 0.3)
            self.vy = int(cy * 0.7 + self.prev_vy * 0.3)
            self.prev_vx, self.prev_vy = self.vx, self.vy
        else:
            self.vx, self.vy = self.prev_vx, self.prev_vy

        current_time = time.time()
        
        # Sonido Whoosh por velocidad
        speed = abs(self.vx - old_vx) + abs(self.vy - old_vy)
        if speed > 15 and current_time - self.last_sound_time > 0.2:
            random.choice(self.whoosh_sounds).play()
            self.last_sound_time = current_time

        # 3. Lógica de Game Over (Tu lógica de cortina negra y botones)
        if self.game_over:
            return self._handle_game_over(win, current_time, pinch)

        # 4. Generar Frutas (Tu lógica de dificultad por Score)
        self._spawn_manager(current_time)

        # 5. Movimiento y Colisiones (Tu lógica de Máscaras y Cortes)
        self._process_physics_and_collisions(win)

        # 6. UI: Score y Vidas
        scoretext = self.myfont.render(f"PUNTUACION: {self.score}", True, (255, 255, 255))
        win.blit(scoretext, (20, 20))
        for i in range(3):
            pic = self.corazon if i < self.lives else self.corazon_vacio
            win.blit(pic, (self.WIDTH - 220 + i*65, 20))

        # Dibujar Puntero (Estrella)
        win.blit(self.small_star, (self.vx - 25, self.vy - 25))
        
        # Actualizar ángulo de rotación
        self.angle = (self.angle + 2) % 360

        # 7. Retornar Frame convertido a OpenCV
        return self._pygame_to_cv2(win)

    def _spawn_manager(self, current_time):
        self.spawn_delay = max(1.1, 2.8 - self.score * 0.02)
        if random.randint(0, 10) < 3: self.spawn_delay += random.randint(1, 2)

        if len(self.a) < 7 and current_time - self.last_spawn_time > self.spawn_delay:
            if self.score < 5: number = random.randint(2, 3)
            elif self.score < 15: number = random.randint(3, 4)
            else: number = random.randint(4, 6)

            for _ in range(number):
                pos = random.randint(100, self.WIDTH - 100)
                fruit_type = random.randint(0, 10)
                if fruit_type < 3: pic = self.watermelon[0]
                elif fruit_type < 6: pic = self.berry[0]
                elif fruit_type < 9: pic = self.orange[0]
                else: pic = self.bomb[0]

                vel = random.randint(18, 26)
                self.a.append(FruitItem(pos, self.HEIGHT, pic, self.bomb[0], vel, -0.5))
            self.last_spawn_time = current_time

    def _process_physics_and_collisions(self, win):
        for z in self.a[:]:
            z.y -= z.u
            z.u += z.g
            z.x += 1.4 if z.pos <= self.WIDTH // 2 else -1.4
            
            z.show(win, self.angle)

            # Colisión
            mask = pygame.mask.from_surface(z.pic)
            offset = (int(self.vx - z.x - 25), int(self.vy - z.y - 25))
            
            if mask.overlap(self.maskp, offset):
                if z.is_bomb and not z.exploded:
                    z.pic = self.bomb[1]
                    z.exploded = True
                    self.lives -= 1
                    self.explosion_sound.play()
                    if self.lives <= 0: self.game_over = True
                elif not z.is_bomb:
                    self.score += 1
                    random.choice(self.slice_sounds).play()
                    # Lógica de partición (tus if de berry, orange, watermelon)
                    self._slice_fruit(z)
                    self.a.remove(z)
            elif z.y > self.HEIGHT + 50:
                self.a.remove(z)

    def _slice_fruit(self, z):
        # Mantenemos tu lógica de spawnear las dos mitades al cortar
        if z.pic == self.berry[0]:
            self.a.append(FruitItem(z.x + 10, z.y + 10, self.berry[1], self.bomb[0], z.u, z.g))
            self.a.append(FruitItem(z.x - 10, z.y - 10, self.berry[2], self.bomb[0], z.u, z.g))
        elif z.pic == self.watermelon[0]:
            self.a.append(FruitItem(z.x + 10, z.y + 10, self.watermelon[1], self.bomb[0], z.u, z.g))
            self.a.append(FruitItem(z.x - 10, z.y - 10, self.watermelon[2], self.bomb[0], z.u, z.g))
        elif z.pic == self.orange[0]:
            self.a.append(FruitItem(z.x + 10, z.y + 10, self.orange[1], self.bomb[0], z.u, z.g))
            self.a.append(FruitItem(z.x - 10, z.y - 10, self.orange[2], self.bomb[0], z.u, z.g))

    def _handle_game_over(self, win, current_time, pinch):
        pygame.mixer.music.set_volume(0.2)
        overlay = pygame.Surface((self.WIDTH, self.HEIGHT))
        overlay.set_alpha(180); overlay.fill((0, 0, 0))
        win.blit(overlay, (0, 0))

        go_text = self.big_font.render("PERDISTE", True, (255, 255, 255))
        win.blit(go_text, go_text.get_rect(center=(self.WIDTH//2, self.HEIGHT//2 - 100)))

        # Botones (Tu lógica de colisión con vx, vy)
        retry_rect = pygame.Rect(self.WIDTH//2 - 120, self.HEIGHT//2, 240, 60)
        retry_color = (0, 255, 0) if retry_rect.collidepoint(self.vx, self.vy) else (0, 180, 0)
        
        pygame.draw.rect(win, retry_color, retry_rect, border_radius=15)
        retry_txt = self.myfont.render("REINTENTAR", True, (255, 255, 255))
        win.blit(retry_txt, retry_txt.get_rect(center=retry_rect.center))

        if retry_rect.collidepoint(self.vx, self.vy) and pinch and current_time - self.last_click_time > 0.5:
            self.reset_game()
            self.last_click_time = current_time

        win.blit(self.small_star, (self.vx - 25, self.vy - 25))
        return self._pygame_to_cv2(win)

    def reset_game(self):
        self.score = 0
        self.lives = 3
        self.a.clear()
        self.game_over = False
        pygame.mixer.music.stop()
        pygame.mixer.music.play(-1)
        pygame.mixer.music.set_volume(0.5)

    def _pygame_to_cv2(self, surface):
        view = pygame.surfarray.array3d(surface)
        view = view.transpose([1, 0, 2]) # Corregir ejes para OpenCV
        return cv2.cvtColor(view, cv2.COLOR_RGB2BGR)