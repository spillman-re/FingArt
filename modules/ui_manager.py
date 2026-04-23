import cv2
import numpy as np
import math
import os

class UIManager:
    def __init__(self):
        # Volvemos a las 3 opciones originales
        self.options = ["PIZARRA", "ARTE", "JUEGOS"]
        
        # Centros calculados para que 3 esferas se vean balanceadas en 1280px
        # (Separación simétrica: 320, 640, 960)
        self.centers = [(320, 420), (640, 420), (960, 420)]
        self.radius = 100 # Un poco más grandes al ser solo tres
        
        # Ruta del logo
        self.logo_path = "assets/logo.png"
        self.logo = None
        if os.path.exists(self.logo_path):
            self.logo = cv2.imread(self.logo_path, cv2.IMREAD_UNCHANGED)
            if self.logo is not None:
                # Redimensionar logo para el encabezado
                self.logo = cv2.resize(self.logo, (100, 100))

    def draw_mode_selector(self, img, lm_list, pinch_dist):
        h, w, _ = img.shape
        x_finger, y_finger = lm_list[8][1], lm_list[8][2]

        # 1. Fondo elegante (más oscuro para que resalte el neón)
        overlay = img.copy()
        cv2.rectangle(overlay, (0, 0), (w, h), (10, 10, 10), -1)
        cv2.addWeighted(overlay, 0.88, img, 0.12, 0, img)

        # 2. BRANDING: FingMix
        # Línea de horizonte decorativa
        cv2.line(img, (100, 140), (w - 100, 140), (200, 200, 200), 1)
        
        # Título principal
        cv2.putText(img, "FingMix", (w // 2 - 130, 100), 
                    cv2.FONT_HERSHEY_TRIPLEX, 2.8, (0, 255, 255), 3)
        
        # Dibujar Logo
        if self.logo is not None:
            ly, lx, _ = self.logo.shape
            y_off, x_off = 20, w // 2 - 260
            # Si el logo tiene 4 canales (transparencia), usamos solo los 3 primeros para este resize rápido
            img[y_off:y_off+ly, x_off:x_off+lx] = self.logo[:,:,:3]

        selected_mode = None

        # 3. Dibujar esferas de modos
        for i, name in enumerate(self.options):
            dist_to_center = math.hypot(x_finger - self.centers[i][0], y_finger - self.centers[i][1])
            
            # Lógica de interacción
            if dist_to_center < self.radius:
                if pinch_dist < 40:
                    color = (0, 255, 0) # Click (Verde)
                    thickness = -1
                    selected_mode = i
                else:
                    color = (0, 255, 255) # Hover (Cian)
                    thickness = 8
                    # Efecto de pulso visual al estar encima
                    cv2.circle(img, self.centers[i], self.radius + 5, (0, 255, 255), 2)
            else:
                color = (255, 255, 255) # Reposo
                thickness = 2

            # Dibujar Círculo principal
            cv2.circle(img, self.centers[i], self.radius, color, thickness)
            
            # Texto del modo (Centrado dinámicamente)
            text_size = cv2.getTextSize(name, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2)[0]
            text_x = self.centers[i][0] - text_size[0] // 2
            cv2.putText(img, name, (text_x, self.centers[i][1] + 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)

        return img, selected_mode, False