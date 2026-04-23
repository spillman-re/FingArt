import pygame
import cv2
import math
import random
import time
import os

class FruitNinjaGame:
    def __init__(self, width, height):
        self.width, self.height = width, height
        self.score = 0
        self.lives = 3
        self.game_over = False
        self.fruits = []
        self.last_spawn_time = 0
        self.spawn_delay = 1.5
        self.angle = 0
        self.last_sound_time = 0
        
        # Rutas de recursos
        self.base_path = 'FruitNinga_opencv_based--master/'
        
        # Inicializar Pygame Mixer (Sonidos)
        if not pygame.mixer.get_init():
            pygame.mixer.init()
            
        self._load_assets()
        pygame.mixer.music.play(-1)

    def _load_assets(self):
        # Imágenes
        self.bg = pygame.image.load(os.path.join(self.base_path, 'images/bg.jpg'))
        self.bg = pygame.transform.scale(self.bg, (self.width, self.height))
        
        # Frutas (Cargamos las listas igual que en tu original)
        self.watermelon = [pygame.transform.scale(pygame.image.load(os.path.join(self.base_path, f'images/watermelon{i}.png')), (70,70)) for i in [1,2,3]]
        self.berry = [pygame.transform.scale(pygame.image.load(os.path.join(self.base_path, f'images/berry{i}.png')), (70,70)) for i in [1,2,3]]
        self.orange = [pygame.transform.scale(pygame.image.load(os.path.join(self.base_path, f'images/Orang1.png')), (70,70)),
                       pygame.transform.scale(pygame.image.load(os.path.join(self.base_path, f'images/Orang2.png')), (70,70)),
                       pygame.transform.scale(pygame.image.load(os.path.join(self.base_path, f'images/Orange3.png')), (70,70))]
        self.bomb_imgs = [pygame.transform.scale(pygame.image.load(os.path.join(self.base_path, f'images/bomba{i}f.png')), (70,70)) for i in [1,2]]
        
        self.star = pygame.transform.scale(pygame.image.load(os.path.join(self.base_path, 'images/star1.png')), (50, 50))
        self.mask_star = pygame.mask.from_surface(self.star)
        
        self.corazon = pygame.transform.scale(pygame.image.load(os.path.join(self.base_path, 'images/corazon1.png')), (60, 60))
        self.corazon_v = pygame.transform.scale(pygame.image.load(os.path.join(self.base_path, 'images/corazon2.png')), (60, 60))
        
        self.font = pygame.font.SysFont("monospace", 30, bold=True)
        
        # Sonidos
        pygame.mixer.music.load(os.path.join(self.base_path, "sounds/Kevin MacLeod - Pixelland.wav"))
        self.slice_sounds = [pygame.mixer.Sound(os.path.join(self.base_path, f"sounds/corte{i}f.wav")) for i in [1,2]]
        self.explosion_sound = pygame.mixer.Sound(os.path.join(self.base_path, "sounds/bombf.wav"))

    def update(self, frame_cv, lm_list, pinch):
        # Creamos una superficie de Pygame para dibujar el juego
        game_surface = pygame.Surface((self.width, self.height))
        game_surface.blit(self.bg, (0, 0))
        
        # Coordenadas del dedo
        vx, vy = lm_list[8][1], lm_list[8][2]
        
        if self.game_over:
            return self._draw_game_over(game_surface, vx, vy, pinch)

        # Lógica de juego
        self._spawn_fruits()
        self._process_fruits(game_surface, vx, vy)
        
        # Dibujar UI de puntos y vidas
        score_txt = self.font.render(f"SCORE: {self.score}", True, (255, 255, 255))
        game_surface.blit(score_txt, (20, 20))
        for i in range(3):
            img = self.corazon if i < self.lives else self.corazon_v
            game_surface.blit(img, (self.width - 200 + i*60, 20))

        # Dibujar la estrella (puntero)
        game_surface.blit(self.star, (vx-25, vy-25))
        
        # Rotación de frutas
        self.angle = (self.angle + 2) % 360
        
        # CONVERTIR PYGAME A OPENCV (Para que el Main lo muestre)
        view = pygame.surfarray.array3d(game_surface)
        view = view.transpose([1, 0, 2])
        img_final = cv2.cvtColor(view, cv2.COLOR_RGB2BGR)
        
        return img_final

    def _spawn_fruits(self):
        curr_time = time.time()
        if len(self.fruits) < 6 and curr_time - self.last_spawn_time > self.spawn_delay:
            num = random.randint(2, 4)
            for _ in range(num):
                ftype = random.randint(0, 10)
                if ftype < 3: pic = self.watermelon[0]
                elif ftype < 6: pic = self.berry[0]
                elif ftype < 9: pic = self.orange[0]
                else: pic = self.bomb_imgs[0]
                
                self.fruits.append({
                    'x': random.randint(100, self.width-100), 'y': self.height,
                    'vx': 1.5 if random.random() > 0.5 else -1.5, 'vy': random.randint(18, 25),
                    'g': -0.6, 'pic': pic, 'is_bomb': (pic == self.bomb_imgs[0]), 'exploded': False
                })
            self.last_spawn_time = curr_time

    def _process_fruits(self, surface, vx, vy):
        for f in self.fruits[:]:
            f['y'] -= f['vy']
            f['vy'] += f['g']
            f['x'] += f['vx']
            
            # Dibujar con rotación
            rotated = pygame.transform.rotate(f['pic'], self.angle)
            surface.blit(rotated, (f['x'], f['y']))
            
            # Colisión por Máscara (como en tu código original)
            f_mask = pygame.mask.from_surface(f['pic'])
            offset = (int(vx - f['x'] - 25), int(vy - f['y'] - 25))
            
            if f_mask.overlap(self.mask_star, offset):
                if f['is_bomb'] and not f['exploded']:
                    self.explosion_sound.play()
                    self.lives -= 1
                    f['exploded'] = True
                    if self.lives <= 0: self.game_over = True
                    self.fruits.remove(f)
                elif not f['is_bomb']:
                    self.score += 1
                    random.choice(self.slice_sounds).play()
                    self.fruits.remove(f) # Simplificado: desaparece al corte
            
            elif f['y'] > self.height:
                self.fruits.remove(f)

    def _draw_game_over(self, surface, vx, vy, pinch):
        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(180)
        overlay.fill((0,0,0))
        surface.blit(overlay, (0,0))
        
        txt = self.font.render("GAME OVER", True, (255, 255, 255))
        surface.blit(txt, (self.width//2 - 100, self.height//2 - 100))
        
        # Botón reintentar
        btn = pygame.Rect(self.width//2 - 100, self.height//2, 200, 50)
        pygame.draw.rect(surface, (0, 200, 0), btn)
        surface.blit(self.font.render("REINTENTAR", True, (255,255,255)), (btn.x + 10, btn.y + 10))
        
        if btn.collidepoint(vx, vy) and pinch:
            self.__init__(self.width, self.height)
            
        view = pygame.surfarray.array3d(surface)
        view = view.transpose([1, 0, 2])
        return cv2.cvtColor(view, cv2.COLOR_RGB2BGR)