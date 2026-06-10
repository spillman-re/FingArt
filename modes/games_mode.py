import cv2
import numpy as np
import math
import random
import pygame
# Asegúrate de que la carpeta se llame exactamente FruitNinja (ojo mayúsculas)
from .games.FruitNinja.game_logic import FruitNinjaGame
from .games.bubbles.bubbles_bridge import BubblesGameBridge
from .games.Snake.snake_logic import SnakeGame
from .games.flappy.flappy_logic import FlappyBirdGame


class GamesMode:
    def __init__(self, width=1280, height=720):
        self.width, self.height = width, height
        self.games = ["FRUIT NINJA", "BUBBLES", "FLAPPY BIRD", "SNAKE"]
        
        self.game_centers = [(256, 360), (512, 360), (768, 360), (1024, 360)]
        self.colors = [(0, 0, 255), (255, 255, 0), (0, 255, 255), (0, 255, 0)]
        
        self.active_game = None 
        self.menu_btn_pos = (20, 20, 130, 80)

        self.fruit_ninja = None
        self.bubbles_game = None
        self.snake_game = None
        self.flappy_bird = None
        self.last_pinch = False # Para detectar el flanco de subida (click)
        self.particles = []

        self.game_icons = [
            cv2.imread("assets/FruitLogoF.png", cv2.IMREAD_UNCHANGED),
            cv2.imread("assets/BubbleLogoF.png", cv2.IMREAD_UNCHANGED),
            cv2.imread("assets/FlappyLogoF.png", cv2.IMREAD_UNCHANGED),
            cv2.imread("assets/SnakeLogoF.png", cv2.IMREAD_UNCHANGED)
        ]

    def update(self, img, lm_list, fingers):
        x1, y1 = lm_list[8][1], lm_list[8][2]
        x2, y2 = lm_list[4][1], lm_list[4][2]
        pinch_dist = math.hypot(x1 - x2, y1 - y2)
        pinch = pinch_dist < 40

        # 1. BOTÓN VOLVER A FINGMIX
        if self.active_game is None:
            if self.menu_btn_pos[0] < x1 < self.menu_btn_pos[2] and \
               self.menu_btn_pos[1] < y1 < self.menu_btn_pos[3]:
                if pinch:
                    return "SWITCH_MENU"

        # 2. LÓGICA DEL SELECTOR O DEL JUEGO
        if self.active_game is None:
            img, selection = self.draw_game_selector(img, x1, y1, pinch)
            if selection is not None:
                self.active_game = self.games[selection]
                print(f"Iniciando: {self.active_game}")
        else:
            # CORRECCIÓN: Ahora pasamos lm_list a run_game_logic
            img = self.run_game_logic(img, x1, y1, pinch, lm_list)

        return img

    def draw_game_selector(self, img, x_f, y_f, pinch):
        overlay = img.copy()
        cv2.rectangle(overlay, (0, 0), (self.width, self.height), (30, 10, 10), -1)
        cv2.addWeighted(overlay, 0.7, img, 0.3, 0, img)
        
        cv2.putText(img, "ELIGE TU RETO", (self.width//2 - 180, 100), 
                    cv2.FONT_HERSHEY_TRIPLEX, 1.5, (255, 255, 255), 2)

        cv2.rectangle(img, (self.menu_btn_pos[0], self.menu_btn_pos[1]), 
                      (self.menu_btn_pos[2], self.menu_btn_pos[3]), (150, 50, 0), -1)
        cv2.putText(img, "BACK", (45, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        selected = None
        radius = 90
        for i, name in enumerate(self.games):
            center = self.game_centers[i]
            dist = math.hypot(x_f - center[0], y_f - center[1])
            if dist < radius:
                color, thick = (255, 255, 255), 5
                if pinch: selected = i
            else:
                color, thick = self.colors[i], 2

            hover = dist < radius

            clicked = hover and pinch
            if clicked:

                for _ in range(15):

                    self.particles.append({

                    "x": center[0],
                    "y": center[1],

                    "dx": random.randint(-8, 8),
                    "dy": random.randint(-8, 8),

                    "life": random.randint(15, 30),

                    "color": self.colors[i]
                })

            self._draw_game_icon(img, i, center, hover, clicked)
            cv2.putText(img, name, (center[0] - 70, center[1] + 130),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        self.draw_particles(img)
        return img, selected

    def _draw_game_icon(self, img, idx, center, hover = False, clicked = False):
        
        icon = self.game_icons[idx]

        # -----------------------------
        # EFECTO HOVER
        # -----------------------------

        if clicked:
            size = 440
        elif hover:
            size = 420
        else:
            size = 400

        icon = cv2.resize(icon, (size, size))

        b, g, r, a = cv2.split(icon)

        overlay = cv2.merge((b, g, r))

        x = center[0] - size // 2
        y = center[1] - size // 2

        mask = a / 255.0

        h, w = overlay.shape[:2]

        # Evitar errores fuera de pantalla
        if y < 0 or x < 0 or y+h > img.shape[0] or x+w > img.shape[1]:
            return

        roi = img[y:y+h, x:x+w]

        # -----------------------------
        # MEZCLA PNG
        # -----------------------------

        for c in range(3):
            roi[:, :, c] = (
            overlay[:, :, c] * mask +
            roi[:, :, c] * (1 - mask)
        )

        img[y:y+h, x:x+w] = roi


    def draw_particles(self, img):

        for p in self.particles[:]:

            p["x"] += p["dx"]
            p["y"] += p["dy"]

            p["life"] -= 1

            cv2.circle(
                img,
                (int(p["x"]), int(p["y"])),
                4,
                p["color"],
                -1
            )

            if p["life"] <= 0:
                self.particles.remove(p)


    def run_game_logic(self, img, x, y, pinch, lm_list):        
        pinch_started = pinch and not self.last_pinch
        self.last_pinch = pinch
        
        # ---------------------------------------------------------
        # 1. FRUIT NINJA
        # ---------------------------------------------------------
        if self.active_game == "FRUIT NINJA":
            if self.fruit_ninja is None:
                self.fruit_ninja = FruitNinjaGame(self.width, self.height)
            img = self.fruit_ninja.update(img, lm_list, pinch)
            
            exit_btn_pos = (560, 10, 720, 60)
            cv2.rectangle(img, (exit_btn_pos[0], exit_btn_pos[1]), 
                          (exit_btn_pos[2], exit_btn_pos[3]), (0, 0, 200), -1)
            cv2.putText(img, "SALIR", (exit_btn_pos[0] + 35, exit_btn_pos[1] + 35), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            if exit_btn_pos[0] < x < exit_btn_pos[2] and \
               exit_btn_pos[1] < y < exit_btn_pos[3] and pinch:
                pygame.mixer.music.stop()
                self.active_game = None
                self.fruit_ninja = None

        # ---------------------------------------------------------
        # 2. BUBBLES
        # ---------------------------------------------------------
        elif self.active_game == "BUBBLES":
            if self.bubbles_game is None:
                self.bubbles_game = BubblesGameBridge(self.width, self.height)
            
            result = self.bubbles_game.update(img, lm_list, pinch)
            if isinstance(result, str) and result == "EXIT_TO_SELECTOR":
                self.active_game = None
                self.bubbles_game = None
                return img
            img = result

        # ---------------------------------------------------------
        # 3. SNAKE (Corregido x1/y1 a x/y)
        # ---------------------------------------------------------
        elif self.active_game == "SNAKE":
            if self.snake_game is None:
                self.snake_game = SnakeGame(self.width, self.height)
            img = self.snake_game.update(img, lm_list, pinch)
            
            exit_btn_pos = (560, 10, 720, 60)
            cv2.rectangle(img, (exit_btn_pos[0], exit_btn_pos[1]), 
                          (exit_btn_pos[2], exit_btn_pos[3]), (0, 0, 200), -1)
            cv2.putText(img, "SALIR", (600, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Aquí estaba el error, ahora usa 'x' y 'y'
            if exit_btn_pos[0] < x < exit_btn_pos[2] and \
               exit_btn_pos[1] < y < exit_btn_pos[3] and pinch:
                self.active_game = None
                pygame.mixer.music.stop()
                self.snake_game = None

        # ---------------------------------------------------------
        # 4. FLAPPY BIRD
        # ---------------------------------------------------------
        elif self.active_game == "FLAPPY BIRD":
            if self.flappy_bird is None:
                self.flappy_bird = FlappyBirdGame(self.width, self.height)
            
            # Pasamos todos los datos necesarios
            img = self.flappy_bird.update(img, lm_list, pinch, pinch_started)
            
            # Botón SALIR (Dinamismo: Esquina superior derecha para Flappy)
            exit_btn_pos = (self.width - 150, 10, self.width - 20, 60)
            cv2.rectangle(img, (exit_btn_pos[0], exit_btn_pos[1]), (exit_btn_pos[2], exit_btn_pos[3]), (0, 0, 200), -1)
            cv2.putText(img, "SALIR", (exit_btn_pos[0]+20, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            if exit_btn_pos[0] < x < exit_btn_pos[2] and exit_btn_pos[1] < y < exit_btn_pos[3] and pinch:
                self.active_game = None
                self.flappy_bird = None

        return img