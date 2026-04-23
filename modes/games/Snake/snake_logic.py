import cv2
import numpy as np
import random
import time
import os
import pygame

class SnakeGame:
    def __init__(self, width=1280, height=720):
        self.width, self.height = width, height
        
        # Cargar assets de imagen
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        path_manzana = os.path.join(self.dir_path, "imagenes", "manzana.png")
        self.imgManzana = cv2.imread(path_manzana, cv2.IMREAD_UNCHANGED)
        if self.imgManzana is not None:
            self.imgManzana = cv2.resize(self.imgManzana, (50, 50))

        # --- AUDIO ---
        if not pygame.mixer.get_init():
            pygame.mixer.init()
            
        # Carga de sonidos (Asegúrate de tener estos archivos en una carpeta 'sounds')
        try:
            self.snd_comer = pygame.mixer.Sound(os.path.join(self.dir_path, "sounds", "eat.wav"))
            pygame.mixer.music.load(os.path.join(self.dir_path, "sounds", "snake_bg.mp3"))
            pygame.mixer.music.set_volume(0.4)
        except:
            print("Aviso: No se encontraron archivos de audio en snake/sounds/")

        # Variables de suavizado
        self.smooth_x, self.smooth_y = width // 2, height // 2
        self.lerp_factor = 0.35  # Ajusta entre 0.1 (muy suave) y 1.0 (instantáneo)

        self.reset_game()

    def reset_game(self):
        self.puntos = []
        self.longitudes = []
        self.longitudActual = 0
        self.longitudPermitida = 150
        self.cabezaAnterior = (self.width // 2, self.height // 2)
        self.smooth_x, self.smooth_y = self.width // 2, self.height // 2
        self.comidaX, self.comidaY = random.randint(100, self.width-100), random.randint(100, self.height-100)
        self.puntaje = 0
        self.finDelJuego = False
        
        # Reiniciar música
        try:
            pygame.mixer.music.play(-1)
        except: pass

    def update(self, img, lm_list, pinch):
        if not self.finDelJuego and lm_list:
            # 1. Suavizado de posición (Dedo índice ID 8)
            target_x, target_y = lm_list[8][1], lm_list[8][2]
            self.smooth_x += (target_x - self.smooth_x) * self.lerp_factor
            self.smooth_y += (target_y - self.smooth_y) * self.lerp_factor
            
            puntoActual = (int(self.smooth_x), int(self.smooth_y))
            
            # 2. Límite de pantalla (Dificultad extra)
            if puntoActual[0] <= 0 or puntoActual[0] >= self.width or \
               puntoActual[1] <= 0 or puntoActual[1] >= self.height:
                self.finDelJuego = True

            self.puntos.append(puntoActual)

            distancia = np.hypot(puntoActual[0] - self.cabezaAnterior[0], puntoActual[1] - self.cabezaAnterior[1])
            self.longitudes.append(distancia)
            self.longitudActual += distancia
            self.cabezaAnterior = puntoActual

            # Reducir longitud si excede la permitida
            if self.longitudActual > self.longitudPermitida:
                for i, dist in enumerate(self.longitudes):
                    self.longitudActual -= dist
                    self.longitudes.pop(i)
                    self.puntos.pop(i)
                    if self.longitudActual < self.longitudPermitida:
                        break

            # Colisión con el propio cuerpo (Dificultad: ajustado a 10 puntos de margen)
            if len(self.puntos) > 10:
                cabeza = np.array(self.puntos[-1])
                for i in range(len(self.puntos) - 10):
                    if np.linalg.norm(cabeza - np.array(self.puntos[i])) < 10:
                        self.finDelJuego = True

            # Comer manzana
            if abs(puntoActual[0] - self.comidaX) < 45 and abs(puntoActual[1] - self.comidaY) < 45:
                try: self.snd_comer.play() 
                except: pass
                
                self.comidaX = random.randint(100, self.width-100)
                self.comidaY = random.randint(100, self.height-100)
                self.longitudPermitida += 50 # Dificultad: crece más rápido
                self.puntaje += 1

        # --- DIBUJO ---
        # 1. Cuerpo degradado
        for i in range(1, len(self.puntos)):
            grosor = int(np.interp(i, [0, len(self.puntos)], [5, 25]))
            color = (int(np.interp(i, [0, len(self.puntos)], [200, 0])), 255, int(np.interp(i, [0, len(self.puntos)], [0, 255])))
            cv2.line(img, self.puntos[i - 1], self.puntos[i], color, grosor)

        # 2. Cabeza Pro
        if self.puntos:
            cv2.circle(img, self.puntos[-1], 18, (50, 50, 255), -1)
            # Ojos blancos
            cv2.circle(img, (self.puntos[-1][0]-6, self.puntos[-1][1]-6), 5, (255, 255, 255), -1)
            cv2.circle(img, (self.puntos[-1][0]+6, self.puntos[-1][1]-6), 5, (255, 255, 255), -1)
            # Pupilas negras
            cv2.circle(img, (self.puntos[-1][0]-6, self.puntos[-1][1]-6), 2, (0, 0, 0), -1)
            cv2.circle(img, (self.puntos[-1][0]+6, self.puntos[-1][1]-6), 2, (0, 0, 0), -1)

        # 3. Manzana
        img = self.overlayPNG(img, self.imgManzana, (self.comidaX - 25, self.comidaY - 25))

        # 4. UI
        cv2.putText(img, f'SCORE: {self.puntaje}', (self.width-250, 60), 
                    cv2.FONT_HERSHEY_DUPLEX, 1.2, (255, 255, 255), 2)

        if self.finDelJuego:
            pygame.mixer.music.stop()
            self.draw_game_over(img, pinch)

        return img

    def draw_game_over(self, img, pinch):
        overlay = img.copy()
        cv2.rectangle(overlay, (0, 0), (self.width, self.height), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, img, 0.3, 0, img)
        
        cv2.putText(img, "SERPIENTE ELIMINADA", (self.width//2 - 350, self.height//2 - 50),
                    cv2.FONT_HERSHEY_TRIPLEX, 2, (0, 0, 255), 4)
        
        btn_x1, btn_y1, btn_x2, btn_y2 = self.width//2 - 150, self.height//2 + 20, self.width//2 + 150, self.height//2 + 100
        color_btn = (0, 255, 0) if pinch else (0, 200, 0)
        cv2.rectangle(img, (btn_x1, btn_y1), (btn_x2, btn_y2), color_btn, -1)
        cv2.putText(img, "REINTENTAR", (btn_x1 + 45, btn_y1 + 55), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 2)
        
        if pinch:
            self.reset_game()

    def overlayPNG(self, img, imgOverlay, pos):
        if imgOverlay is None: return img
        h, w = imgOverlay.shape[:2]
        x, y = pos
        if x < 0 or y < 0 or x + w > img.shape[1] or y + h > img.shape[0]: return img
        if imgOverlay.shape[2] == 4:
            alpha = imgOverlay[:, :, 3] / 255.0
            for c in range(3):
                img[y:y+h, x:x+w, c] = (imgOverlay[:, :, c] * alpha + img[y:y+h, x:x+w, c] * (1 - alpha))
        else:
            img[y:y+h, x:x+w] = imgOverlay
        return img