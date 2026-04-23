import cv2
import numpy as np
import math
import random
import pygame
# Asegúrate de que la carpeta se llame exactamente FruitNinja (ojo mayúsculas)
from .games.FruitNinja.game_logic import FruitNinjaGame
from .games.bubbles.bubbles_bridge import BubblesGameBridge

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

            cv2.circle(img, center, radius, color, thick)
            cv2.circle(img, center, radius + 10, color, 1)
            self._draw_game_icon(img, i, center)
            cv2.putText(img, name, (center[0] - 70, center[1] + 130),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        return img, selected

    def _draw_game_icon(self, img, idx, center):
        cx, cy = center
        if idx == 0: # Fruit Ninja
            cv2.ellipse(img, (cx, cy), (40, 30), 0, 0, 360, (0, 100, 0), -1)
            cv2.ellipse(img, (cx, cy), (30, 20), 0, 0, 360, (0, 0, 255), -1)
        elif idx == 1: # Bubbles
            cv2.circle(img, (cx-15, cy-15), 30, (255, 255, 255), 2)
            cv2.circle(img, (cx+15, cy+15), 20, (255, 255, 255), 1)
        elif idx == 2: # Flappy Bird
            cv2.circle(img, (cx, cy), 25, (0, 255, 255), -1)
            cv2.rectangle(img, (cx+15, cy-5), (cx+35, cy+5), (0, 165, 255), -1)
        elif idx == 3: # Snake
            cv2.line(img, (cx-30, cy), (cx+30, cy), (0, 255, 0), 8)
            cv2.circle(img, (cx+30, cy), 10, (0, 200, 0), -1)

    def run_game_logic(self, img, x, y, pinch, lm_list):
        # ---------------------------------------------------------
        # 1. FRUIT NINJA: Botón Central Superior
        # ---------------------------------------------------------
        if self.active_game == "FRUIT NINJA":
            if self.fruit_ninja is None:
                self.fruit_ninja = FruitNinjaGame(self.width, self.height)
            img = self.fruit_ninja.update(img, lm_list, pinch)
            
            # Dibujamos botón de salir específico para Fruit Ninja
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
        # 2. BUBBLES: Sin botón extra (usa el del juego)
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
            # Nota: No dibujamos botón aquí porque Bubbles tiene su propio botón "MENU"

        # ---------------------------------------------------------
        # 3. OTROS JUEGOS (Ejemplo Flappy Bird en una esquina)
        # ---------------------------------------------------------
        elif self.active_game == "FLAPPY BIRD":
            # Aquí podrías poner el botón en la esquina superior derecha por ejemplo
            pass

        return img