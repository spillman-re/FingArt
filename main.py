import cv2
import time
import math
import numpy as np
import pygame
from modules.hand_tracking import HandDetector
from modules.camera_utils import get_available_cameras
from modules.ui_manager import UIManager
from modes.free_paint import FreePaintMode
from modes.generative_art import GenerativeArtMode 
from modes.games_mode import GamesMode

def main():
    # --- 1. INICIALIZACIÓN DE PANTALLA COMPLETA ---
    pygame.init()
    info = pygame.display.Info()
    SCREEN_W, SCREEN_H = info.current_w, info.current_h
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.FULLSCREEN | pygame.DOUBLEBUF)
    pygame.display.set_caption("FingMix - High Fidelity Arcade")

    # --- 2. GESTIÓN DE CÁMARAS ---
    cameras = get_available_cameras()
    if not cameras:
        print("Error: No se detectó ninguna cámara.")
        return
    
    current_cam_idx = 0
    cap = cv2.VideoCapture(cameras[current_cam_idx])
    
    # --- 3. INICIALIZACIÓN DE MÓDULOS ---
    detector = HandDetector()
    ui = UIManager()
    paint_mode = FreePaintMode()
    art_mode = GenerativeArtMode() 
    games_mode = GamesMode()

    current_mode = paint_mode
    menu_active = True
    run = True

    while run:
        success, frame = cap.read()
        
        if not success or frame is None:
            # Si una cámara falla (como Iriun desconectándose), intentamos reconectar
            continue

        # --- 4. NORMALIZACIÓN DE ASPECTO (Solución Iriun/Webcam) ---
        # No importa la resolución original, forzamos a 1280x720 antes de procesar
        # Esto asegura que las coordenadas de Mediapipe coincidan siempre con la UI
        img = cv2.resize(frame, (1280, 720))
        img = cv2.flip(img, 1)
        
        # Procesamiento de manos sobre el frame normalizado
        img = detector.find_hands(img)
        lm_list = detector.get_position(img)

        # --- 5. GESTIÓN DE EVENTOS (ESC y CAMBIAR CÁMARA) ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            
            if event.type == pygame.KEYDOWN:
                # Salir con ESC
                if event.key == pygame.K_ESCAPE:
                    run = False
                
                # Cambiar cámara con 'C'
                if event.key == pygame.K_c:
                    current_cam_idx = (current_cam_idx + 1) % len(cameras)
                    cap.release()
                    cap = cv2.VideoCapture(cameras[current_cam_idx])
                    print(f"Cambiado a cámara índice: {cameras[current_cam_idx]}")

        # --- 6. LÓGICA DE MODOS ---
        if len(lm_list) != 0:
            x1, y1 = lm_list[8][1], lm_list[8][2]
            x2, y2 = lm_list[4][1], lm_list[4][2]
            pinch_dist = math.hypot(x1 - x2, y1 - y2)
            fingers = detector.fingers_up()

            if menu_active:
                img, selection, exit_menu = ui.draw_mode_selector(img, lm_list, pinch_dist)
                
                if exit_menu:
                    menu_active = False
                elif selection is not None:
                    if selection == 0: current_mode = paint_mode
                    elif selection == 1:
                        current_mode = art_mode 
                        art_mode.canvas = np.zeros((720, 1280, 3), np.uint8)
                    elif selection == 2: current_mode = games_mode
                    menu_active = False
            else:
                result = current_mode.update(img, lm_list, fingers)
                if isinstance(result, str):
                    if result == "SWITCH_MENU":
                        menu_active = True
                else:
                    img = result

        # --- 7. RENDERIZADO Y ESCALADO FINAL ---
        # Convertimos de OpenCV (BGR) a Pygame (RGB)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        # Transponemos para que Pygame lo entienda correctamente
        frame_surf = pygame.surfarray.make_surface(img_rgb.swapaxes(0, 1))
        
        # Escalamos al tamaño de tu monitor (Pantalla Grande)
        # Al haber hecho el resize a 1280x720 arriba, los botones siempre estarán en su sitio
        final_surf = pygame.transform.scale(frame_surf, (SCREEN_W, SCREEN_H))
        
        screen.blit(final_surf, (0, 0))
        pygame.display.flip()

    # --- 8. CIERRE SEGURO ---
    cap.release()
    pygame.quit()

if __name__ == "__main__":
    main()