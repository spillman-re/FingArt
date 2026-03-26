import cv2
import numpy as np
import math
import os

class FreePaintMode:
    def __init__(self, width=1280, height=720):
        self.width, self.height = width, height
        self.canvas = np.zeros((height, width, 3), np.uint8)
        self.xp, self.yp = 0, 0
        self.brush_color = (255, 0, 255)
        self.brush_size = 8
        self.eraser_size = 80
        self.header_h = 100
        
        # El último es el "Negro" corregido (Gris muy oscuro)
        self.colors = [(255,0,0), (0,0,255), (0,255,0), (0,255,255), (20,20,20)]
        
        # Cargar imágenes
        self.img_pencil = self._load_asset("assets/cursors/pencil.png", (60, 60))
        self.img_eraser = self._load_asset("assets/cursors/eraser.png", (70, 70))

        # Posición del botón Clear: (x1, y1, x2, y2)
        self.clear_btn_pos = (1100, 25, 1250, 75) 

        # Sizes        
        self.slider_pos = (400, 110, 880, 130) # (x1, y1, x2, y2) - Debajo del menú de colores
        self.slider_circle_x = 640  # Posición inicial del círculo (medio)
        self.brush_size = 10        # Tamaño inicial

        # Factor de suavizado (mientras más alto, más suave pero con más "retraso")
        # Un valor entre 3 y 7 es el punto dulce.
        self.smooth_factor = 5 
        self.curr_x, self.curr_y = 0, 0 # Coordenadas suavizadas actuales

        self.modes_btn_pos = (20, 25, 130, 75) # Esquina superior izquierda

    def _load_asset(self, path, size):
        if os.path.exists(path):
            img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
            return cv2.resize(img, size)
        return None

    def overlay_png(self, img, img_overlay, pos):
        if img_overlay is None: return img
        x, y = pos
        h, w = img_overlay.shape[:2]
        x, y = max(0, x), max(0, y)
        if x + w > self.width or y + h > self.height: return img
        
        roi = img[y:y+h, x:x+w]
        overlay_rgb = img_overlay[:, :, :3]
        alpha = img_overlay[:, :, 3] / 255.0
        
        for c in range(3):
            img[y:y+h, x:x+w, c] = (alpha * overlay_rgb[:, :, c] + (1.0 - alpha) * roi[:, :, c])
        return img

    def draw_ui(self, img):
        """Dibuja el menú superior y los botones"""
        # Fondo del encabezado
        overlay = img.copy()
        cv2.rectangle(overlay, (0, 0), (self.width, self.header_h), (40, 40, 40), -1)
        cv2.addWeighted(overlay, 0.7, img, 0.3, 0, img)

        # Botones de colores
        for i, color in enumerate(self.colors):
            x_pos = 150 + (i * 200)
            thickness = 4 if self.brush_color == color else 1
            cv2.rectangle(img, (x_pos, 25), (x_pos + 120, 75), color, -1)
            cv2.rectangle(img, (x_pos, 25), (x_pos + 120, 75), (255, 255, 255), thickness)
        
        # Botón CLEAR
        cv2.rectangle(img, (self.clear_btn_pos[0], self.clear_btn_pos[1]), 
                      (self.clear_btn_pos[2], self.clear_btn_pos[3]), (0, 0, 150), -1)
        cv2.putText(img, "CLEAR", (1135, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Botón MODOS (Color azulado para diferenciar del CLEAR)
        cv2.rectangle(img, (20, 25), (130, 75), (150, 50, 0), -1)
        cv2.putText(img, "MENU", (35, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Llamar al slider
        img = self.draw_slider(img)
        return img
        
    
    def draw_slider(self, img):
        # Dibujar la línea del slider (Gris oscuro)
        cv2.line(img, (self.slider_pos[0], self.slider_pos[1] + 10), 
                (self.slider_pos[2], self.slider_pos[1] + 10), (100, 100, 100), 5)
        
        # Dibujar el círculo del selector (Color del pincel actual)
        cv2.circle(img, (self.slider_circle_x, self.slider_pos[1] + 10), 15, self.brush_color, -1)
        cv2.circle(img, (self.slider_circle_x, self.slider_pos[1] + 10), 15, (255, 255, 255), 2)
        
        # Texto indicando el tamaño
        cv2.putText(img, f"Size: {self.brush_size}", (self.slider_pos[0] - 120, self.slider_pos[1] + 20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        return img

    def update(self, img, lm_list, fingers):
        # 1. Coordenadas básicas y distancias
        x1, y1 = lm_list[8][1], lm_list[8][2] # Índice
        x2, y2 = lm_list[4][1], lm_list[4][2] # Pulgar
        dist = math.hypot(x1 - x2, y1 - y2)
        
        cursor_type = "none"

        # --- LÓGICA DE INTERFACES DE ALTA PRIORIDAD (Esquinas) ---

        # A. Botón "MENU" (Esquina Superior Izquierda)
        # Verificamos si el índice está dentro del recuadro (20, 25) a (130, 75)
        if 20 < x1 < 130 and 25 < y1 < 75:
            self.xp, self.yp = 0, 0
            return "SWITCH_MENU" # Señal para el main.py

        # B. Botón "CLEAR" (Esquina Superior Derecha)
        # Verificamos si el índice está dentro de self.clear_btn_pos
        if self.clear_btn_pos[0] < x1 < self.clear_btn_pos[2] and \
           self.clear_btn_pos[1] < y1 < self.clear_btn_pos[3]:
            self.xp, self.yp = 0, 0
            self.canvas = np.zeros((self.height, self.width, 3), np.uint8)
            # No retornamos aquí para que permita ver el canvas limpio de inmediato

        # --- LÓGICA DE MENÚS (Colores y Slider) ---

        # C. Selección de Colores (Barra superior, excepto las esquinas)
        elif y1 < self.header_h:
            self.xp, self.yp = 0, 0
            for i, color in enumerate(self.colors):
                x_pos = 150 + (i * 200)
                if x_pos < x1 < x_pos + 120:
                    self.brush_color = color
            
            cv2.circle(img, (x1, y1), 15, self.brush_color, 2)
            cursor_type = "menu"

        # D. Slider de Tamaño
        elif 90 < y1 < 150:
            if self.slider_pos[0] < x1 < self.slider_pos[2]:
                self.slider_circle_x = x1
                self.brush_size = int(np.interp(x1, [self.slider_pos[0], self.slider_pos[2]], [1, 50]))
                self.xp, self.yp = 0, 0 
                cursor_type = "slider"
                cv2.circle(img, (x1, y1), 10, (255, 255, 255), -1)

        # --- LÓGICA DE HERRAMIENTAS DE TRABAJO ---

        # E. BORRADOR (Gesto: 3 dedos arriba)
        elif fingers[1]==1 and fingers[2]==1 and fingers[3]==1 and fingers[4]==0:
            target_x = (lm_list[8][1] + lm_list[16][1]) // 2
            target_y = (lm_list[8][2] + lm_list[16][2]) // 2

            if self.xp == 0 and self.yp == 0:
                self.curr_x, self.curr_y = target_x, target_y
            else:
                self.curr_x = self.xp + (target_x - self.xp) / self.smooth_factor
                self.curr_y = self.yp + (target_y - self.yp) / self.smooth_factor
            
            img = self.overlay_png(img, self.img_eraser, (int(self.curr_x)-35, int(self.curr_y)-35))
            cv2.circle(img, (int(self.curr_x), int(self.curr_y)), self.eraser_size // 2, (255, 255, 255), 2)
            
            if self.xp != 0:
                cv2.line(self.canvas, (int(self.xp), int(self.yp)), 
                         (int(self.curr_x), int(self.curr_y)), (0,0,0), self.eraser_size)
            
            self.xp, self.yp = self.curr_x, self.curr_y
            cursor_type = "eraser"

        # F. DIBUJO (Gesto: Pellizco)
        elif dist < 40:
            if self.xp == 0 and self.yp == 0:
                self.curr_x, self.curr_y = x1, y1
            else:
                self.curr_x = self.xp + (x1 - self.xp) / self.smooth_factor
                self.curr_y = self.yp + (y1 - self.yp) / self.smooth_factor

            if self.xp != 0:
                cv2.line(self.canvas, (int(self.xp), int(self.yp)), 
                         (int(self.curr_x), int(self.curr_y)), 
                         self.brush_color, self.brush_size)
            
            self.xp, self.yp = self.curr_x, self.curr_y
            cv2.circle(img, (int(self.curr_x), int(self.curr_y)), 4, (255, 255, 255), -1)
            cursor_type = "draw"

        # G. LÁPIZ (Gesto: Solo índice - Navegación/Puntero)
        elif fingers[1] == 1 and dist > 50:
            img = self.overlay_png(img, self.img_pencil, (x1-5, y1-55))
            self.xp, self.yp = 0, 0
            cursor_type = "pencil"

        # H. REPOSO
        else:
            self.xp, self.yp = 0, 0
            cv2.circle(img, (x1, y1), 8, (200, 200, 200), 1)

        # --- PROCESAMIENTO FINAL (Fusión y UI) ---

        # Fusión del canvas con el video
        img_gray = cv2.cvtColor(self.canvas, cv2.COLOR_BGR2GRAY)
        _, img_inv = cv2.threshold(img_gray, 5, 255, cv2.THRESH_BINARY_INV)
        img_inv = cv2.cvtColor(img_inv, cv2.COLOR_GRAY2BGR)
        
        img = cv2.bitwise_and(img, img_inv)
        img = cv2.bitwise_or(img, self.canvas)
        
        # Dibujar UI encima de todo
        return self.draw_ui(img)