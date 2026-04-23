import pygame
import cv2
import os
import sys

# Añadimos la carpeta del juego al path para que encuentre sus propios imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from game.sound_manager import SoundManager
from game.scenes.menu_scene import MenuScene
from game.scenes.game_scene import GameScene
from game.scenes.gameover_scene import GameOverScene
from game.constants import SCREEN_WIDTH, SCREEN_HEIGHT

class BubblesGameBridge:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        
        # --- INICIALIZACIÓN CRÍTICA ---
        if not pygame.font.get_init():
            pygame.font.init()
        if not pygame.mixer.get_init():
            pygame.mixer.init()
            
        # Inicializar sonidos
        self.sound = SoundManager()
        self.sound.start_music()
        
        # Inicializar Escenas
        self.scene_name = 'menu'
        self.menu = MenuScene(sound_manager=self.sound)
        self.game = None
        self.gameover = None
        
        # Clase "Fake Tracker" para engañar al juego
        self.fake_tracker = FakeHandTracker()

    def update(self, frame_cv, lm_list, pinch):
        # 1. Crear superficie de Pygame
        surface = pygame.Surface((self.width, self.height))
        
        # 2. Preparar el "Fake Tracker" con los datos de FingMix
        self.fake_tracker.update_data(lm_list, pinch)
        
        # 3. Convertir frame de cámara para el fondo del juego
        rgb = cv2.cvtColor(frame_cv, cv2.COLOR_BGR2RGB)
        cam_surf = pygame.surfarray.make_surface(rgb.swapaxes(0, 1))
        cam_surf = pygame.transform.scale(cam_surf, (self.width, self.height))

        # 4. Lógica de Escenas (Copiada de tu main original pero adaptada)
        result = None
        if self.scene_name == 'menu':
            result = self.menu.update(self.fake_tracker)
            self.menu.draw(surface, cam_surf, self.fake_tracker)
            if result in ('easy', 'medium', 'hard'):
                self.game = GameScene(result, sound_manager=self.sound)
                self.scene_name = 'game'
            elif result == 'exit':
                self.sound.cleanup()
                return "EXIT_TO_SELECTOR" # Señal para el GamesMode

        elif self.scene_name == 'game':
            result = self.game.update(self.fake_tracker)
            self.game.draw(surface, cam_surf, self.fake_tracker)
            if result == 'menu':
                self.scene_name = 'menu'
            elif result == 'win':
                self.gameover = GameOverScene(True, self.game.score, self.game.difficulty, self.sound)
                self.scene_name = 'gameover'
            elif result == 'lose':
                self.gameover = GameOverScene(False, self.game.score, self.game.difficulty, self.sound)
                self.scene_name = 'gameover'

        elif self.scene_name == 'gameover':
            result = self.gameover.update(self.fake_tracker)
            self.gameover.draw(surface, cam_surf, self.fake_tracker)
            if result == 'replay':
                self.game = GameScene(self.game.difficulty, sound_manager=self.sound)
                self.scene_name = 'game'
            elif result == 'menu':
                self.scene_name = 'menu'

        # 5. Retornar a OpenCV
        view = pygame.surfarray.array3d(surface)
        view = view.transpose([1, 0, 2])
        return cv2.cvtColor(view, cv2.COLOR_RGB2BGR)

# Esta clase imita la interfaz de tu HandTracker original
class FakeHandTracker:
    def __init__(self):
        self.index_pos = None
        self.is_pinching = False
        self.pinch_just_started = False
        self.pinch_just_released = False
        self.handedness = "Derecha"
        self._was_pinching = False

    def update_data(self, lm_list, pinch):
        self._was_pinching = self.is_pinching
        self.is_pinching = pinch
        
        if lm_list:
            # Landmark 8 es el índice
            self.index_pos = (lm_list[8][1], lm_list[8][2])
            self.handedness = "Derecha" # Simplificado
        else:
            self.index_pos = None

        # Detectar flancos de click
        self.pinch_just_started = self.is_pinching and not self._was_pinching
        self.pinch_just_released = not self.is_pinching and self._was_pinching