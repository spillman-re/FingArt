import cv2
import time
import math
import numpy as np
from modules.hand_tracking import HandDetector
from modules.camera_utils import get_available_cameras
from modules.ui_manager import UIManager
from modes.free_paint import FreePaintMode
from modes.free_paint import FreePaintMode
from modes.generative_art import GenerativeArtMode
from modes.games_mode import GamesMode


def main():
    cameras = get_available_cameras()
    if not cameras:
        print("Error: No se detectó ninguna cámara.")
        return

    current_camera = 0
    cap = cv2.VideoCapture(cameras[current_camera])

    # Mantener la resolución original del proyecto
    cap.set(3, 1280)
    cap.set(4, 720)

    detector = HandDetector()
    ui = UIManager()

    paint_mode = FreePaintMode()
    art_mode = GenerativeArtMode()
    games_mode = GamesMode()

    current_mode = paint_mode
    menu_active = True

    # Crear ventana en pantalla completa
    window_name = "FingArt - Multimodal"

    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(
        window_name,
        cv2.WND_PROP_FULLSCREEN,
        cv2.WINDOW_FULLSCREEN
    )

    while True:
        success, img = cap.read()
        if not success or img is None:
            continue

        # Mantener el tamaño esperado por toda la aplicación
        img = cv2.resize(img, (1280, 720))
        img = cv2.flip(img, 1)

        img = detector.find_hands(img)
        lm_list = detector.get_position(img)

        if len(lm_list) != 0:
            x1, y1 = lm_list[8][1], lm_list[8][2]
            x2, y2 = lm_list[4][1], lm_list[4][2]
            pinch_dist = math.hypot(x1 - x2, y1 - y2)
            fingers = detector.fingers_up()

            if menu_active:
                img, selection, exit_menu = ui.draw_mode_selector(
                    img,
                    lm_list,
                    pinch_dist
                )

                if exit_menu:
                    menu_active = False

                elif selection is not None:
                    if selection == 0:
                        current_mode = paint_mode
                        print("Modo: Pizarra Libre")

                    elif selection == 1:
                        current_mode = art_mode
                        art_mode.canvas = np.zeros((720, 1280, 3), np.uint8)
                        print("Modo: Arte Generativo")

                    elif selection == 2:
                        print("Modo: Minijuegos")
                        current_mode = games_mode

                    menu_active = False

            else:
                result = current_mode.update(img, lm_list, fingers)

                if isinstance(result, str):
                    if result == "SWITCH_MENU":
                        menu_active = True
                else:
                    img = result

        cv2.imshow(window_name, img)

        key = cv2.waitKey(1) & 0xFF

        # ESC para salir
        if key == 27:
            break

        # Cambiar de cámara con la tecla C
        elif key == ord('c') and len(cameras) > 1:
            current_camera = (current_camera + 1) % len(cameras)

            cap.release()
            cap = cv2.VideoCapture(cameras[current_camera])

            # Mantener la misma resolución
            cap.set(3, 1280)
            cap.set(4, 720)

            print(f"Cámara cambiada a: {cameras[current_camera]}")

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()