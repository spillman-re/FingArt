import cv2
import numpy as np
import pygame
import os
import math

class UIManager:
    def __init__(self, width=1280, height=720):
        self.width, self.height = width, height

        # --- INICIALIZACIÓN ROBUSTA ---
        if not pygame.display.get_init():
            pygame.display.init()
        if not pygame.font.get_init():
            pygame.font.init()
        if not pygame.mixer.get_init():
            pygame.mixer.init()

        # Configuración de opciones y botones
        self.options = ["PIZARRA", "ARTE", "JUEGOS"]
        self.centers = [(320, 420), (640, 420), (960, 420)]
        self.radius = 110
        self.hover_active = [False, False, False] 
        
        # --- CARGA DE ASSETS DE AUDIO ---
        try:
            self.snd_hover = pygame.mixer.Sound("assets/sounds/hover.wav")
            self.snd_click = pygame.mixer.Sound("assets/sounds/click.wav")
            
            # Música de fondo en loop
            #pygame.mixer.music.load("assets/sounds/menu_bg.mp3")
            pygame.mixer.music.set_volume(0.1)
            pygame.mixer.music.play(-1)
        except Exception as e:
            print(f"Aviso: No se pudieron cargar los sonidos. Verifique la carpeta assets/sounds/. Error: {e}")

        # --- CARGA DEL LOGO ---
        self.logo = None
        if os.path.exists("assets/logo.png"):
            raw_logo = pygame.image.load("assets/logo.png")
            # Convert_alpha solo funciona si el modo de pantalla ya fue seteado en main.py
            if pygame.display.get_surface():
                self.logo = raw_logo.convert_alpha()
            else:
                self.logo = raw_logo
            self.logo = pygame.transform.scale(self.logo, (120, 120))

        # --- FUENTES ---
        # Usamos fuentes del sistema para asegurar compatibilidad
        self.font_title = pygame.font.SysFont("Trebuchet MS", 90, bold=True)
        self.font_btn = pygame.font.SysFont("Trebuchet MS", 30, bold=True)

    def draw_mode_selector(self, img, lm_list, pinch_dist):
        """
        Dibuja la interfaz neón sobre el frame de la cámara.
        Retorna: (frame_procesado, modo_seleccionado, booleano_innecesario)
        """
        # 1. Convertir Frame de OpenCV (BGR) a Pygame (RGB)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        surface = pygame.surfarray.make_surface(img_rgb.swapaxes(0, 1))
        
        # 2. Overlay "Glassmorphism" (Efecto cristal oscuro)
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((15, 15, 25, 210)) # Azul oscuro profundo con alta opacidad
        surface.blit(overlay, (0, 0))

        # 3. Dibujar Logo y Título con resplandor
        if self.logo:
            surface.blit(self.logo, (self.width//2 - 340, 40))
        
        title_surf = self.font_title.render("FingMix", True, (0, 255, 255))
        surface.blit(title_surf, (self.width//2 - 130, 50))

        selected_mode = None
        
        # Coordenadas del dedo índice
        x_f, y_f = lm_list[8][1], lm_list[8][2]

        # 4. Dibujar Botones Circulares Neón
        for i, name in enumerate(self.options):
            cx, cy = self.centers[i]
            dist = math.hypot(x_f - cx, y_f - cy)
            
            is_hover = dist < self.radius
            is_click = is_hover and pinch_dist < 40

            # --- Feedback Sonoro ---
            if is_hover:
                if not self.hover_active[i]:
                    try: self.snd_hover.play()
                    except: pass
                    self.hover_active[i] = True
            else:
                self.hover_active[i] = False

            # --- Colores y Efectos Visuales ---
            # Color cian para reposo/hover, verde para click
            main_color = (0, 255, 255) if not is_click else (0, 255, 0)
            
            if is_hover:
                # Dibujar resplandor neón (múltiples círculos con alfa decreciente)
                for r in range(1, 12):
                    glow_alpha = 120 // r
                    pygame.draw.circle(surface, (*main_color, glow_alpha), (cx, cy), self.radius + r, 2)
                
                circle_thickness = 7 # Borde más grueso en hover
            else:
                circle_thickness = 3

            # Dibujar el círculo principal del botón
            pygame.draw.circle(surface, main_color, (cx, cy), self.radius, circle_thickness)
            
            # Texto del botón
            txt_color = (255, 255, 255) if not is_hover else main_color
            txt_surf = self.font_btn.render(name, True, txt_color)
            txt_rect = txt_surf.get_rect(center=(cx, cy))
            surface.blit(txt_surf, txt_rect)

            # --- Lógica de Selección ---
            if is_click:
                try: self.snd_click.play()
                except: pass
                selected_mode = i

        # 5. Cursor Estilizado
        cursor_color = (0, 255, 0) if pinch_dist < 40 else (255, 255, 255)
        # Círculo exterior (mirilla)
        pygame.draw.circle(surface, cursor_color, (x_f, y_f), 15, 2)
        # Punto central
        pygame.draw.circle(surface, cursor_color, (x_f, y_f), 4)

        # 6. Convertir de vuelta a formato OpenCV (BGR)
        out_img = pygame.surfarray.array3d(surface)
        out_img = out_img.transpose([1, 0, 2])
        return cv2.cvtColor(out_img, cv2.COLOR_RGB2BGR), selected_mode, False