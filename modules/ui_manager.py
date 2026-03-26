import cv2
import numpy as np
import math

class UIManager:
    def __init__(self):
        self.options = ["PIZARRA", "ARTE", "JUEGOS"]
        # Posiciones de los centros de los modos (X, Y)
        self.centers = [(320, 360), (640, 360), (960, 360)]
        self.radius = 90
        # NUEVA POSICIÓN: Botón VOLVER arriba al centro (x1, y1, x2, y2)
        self.back_btn_pos = (540, 25, 740, 85) 

    def draw_mode_selector(self, img, lm_list, pinch_dist):
        h, w, _ = img.shape
        x_finger, y_finger = lm_list[8][1], lm_list[8][2]

        # 1. Fondo oscurecido
        overlay = img.copy()
        cv2.rectangle(overlay, (0, 0), (w, h), (15, 15, 15), -1)
        cv2.addWeighted(overlay, 0.75, img, 0.25, 0, img)

        selected_mode = None
        exit_menu = False

        # 2. Dibujar las esferas de los modos
        for i, name in enumerate(self.options):
            dist_to_center = math.hypot(x_finger - self.centers[i][0], y_finger - self.centers[i][1])
            
            # Hover: El dedo está sobre el círculo
            if dist_to_center < self.radius:
                # CLICK: Si además de estar encima, está pellizcando (< 40)
                if pinch_dist < 40:
                    color = (0, 255, 0) # Verde: Selección confirmada
                    thickness = -1
                    selected_mode = i
                else:
                    color = (255, 0, 255) # Morado: Solo encima (sin click)
                    thickness = 5
            else:
                color = (255, 255, 255)
                thickness = 2

            cv2.circle(img, self.centers[i], self.radius, color, thickness)
            cv2.putText(img, name, (self.centers[i][0] - 60, self.centers[i][1] + 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)

        # 3. Botón VOLVER (Ubicado arriba con validación de pellizco)
        is_over_back = self.back_btn_pos[0] < x_finger < self.back_btn_pos[2] and \
                       self.back_btn_pos[1] < y_finger < self.back_btn_pos[3]
        
        # Si está encima y pellizca, se pone verde, si no, gris oscuro
        back_color = (0, 255, 0) if (is_over_back and pinch_dist < 40) else (40, 40, 40)
        
        # Dibujar el botón VOLVER
        cv2.rectangle(img, (self.back_btn_pos[0], self.back_btn_pos[1]), 
                      (self.back_btn_pos[2], self.back_btn_pos[3]), back_color, -1)
        
        # Borde blanco para el botón
        cv2.rectangle(img, (self.back_btn_pos[0], self.back_btn_pos[1]), 
                      (self.back_btn_pos[2], self.back_btn_pos[3]), (255, 255, 255), 2)
        
        cv2.putText(img, "VOLVER", (self.back_btn_pos[0] + 45, self.back_btn_pos[1] + 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        if is_over_back and pinch_dist < 40:
            exit_menu = True

        return img, selected_mode, exit_menu