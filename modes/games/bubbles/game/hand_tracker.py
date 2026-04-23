"""
Módulo de tracking de manos con MediaPipe Tasks API (nueva).
Detecta la posición del dedo índice (cursor) y el gesto de pinch (pulgar + índice).
Soporta mano derecha e izquierda.
"""
import os
import math
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


class HandTracker:
    def __init__(self):
        # Ruta al modelo
        model_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'hand_landmarker.task'
        )

        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_hands=1,
            min_hand_detection_confidence=0.6,
            min_hand_presence_confidence=0.6,
            min_tracking_confidence=0.5,
        )
        self._landmarker = vision.HandLandmarker.create_from_options(options)
        self._frame_ts = 0  # timestamp incremental en ms

        # Posiciones suavizadas
        self._smooth_x = 0.0
        self._smooth_y = 0.0
        self._smooth_factor = 0.45  # 0=muy suave, 1=sin suavizado

        # Estado público
        self.index_pos = None       # (x, y) en coordenadas de pantalla
        self.thumb_pos = None       # (x, y) del pulgar
        self.is_pinching = False
        self.pinch_distance = 999.0
        self.hand_detected = False
        self.handedness = None      # 'Derecha' o 'Izquierda' (del usuario)

        # Detección de flancos
        self._was_pinching = False
        self.pinch_just_started = False
        self.pinch_just_released = False

    # ─────────────────────────────────────────────────────
    def process(self, frame, screen_width, screen_height):
        """Procesa un frame BGR (ya volteado horizontalmente)."""
        h, w, _ = frame.shape

        # Convertir a RGB y crear mp.Image
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        # Incrementar timestamp
        self._frame_ts += 33  # ~30 FPS
        result = self._landmarker.detect_for_video(mp_image, self._frame_ts)

        self._was_pinching = self.is_pinching
        self.hand_detected = False
        self.pinch_just_started = False
        self.pinch_just_released = False

        if result.hand_landmarks and result.handedness:
            hand_lm = result.hand_landmarks[0]
            hand_info = result.handedness[0]

            # ── Handedness ──
            # MediaPipe reporta la mano como se ve en la imagen.
            # Como el frame está volteado (espejo), las etiquetas se invierten.
            raw_label = hand_info[0].category_name
            self.handedness = "Derecha" if raw_label == "Left" else "Izquierda"
            self.hand_detected = True

            # ── Landmarks ──
            index_tip = hand_lm[8]   # punta del índice
            thumb_tip = hand_lm[4]   # punta del pulgar

            # Convertir a píxeles de cámara
            raw_ix = index_tip.x * w
            raw_iy = index_tip.y * h

            # Escalar a coordenadas de pantalla
            scale_x = screen_width / w
            scale_y = screen_height / h
            target_x = raw_ix * scale_x
            target_y = raw_iy * scale_y

            # Suavizado exponencial
            if self.index_pos is None:
                self._smooth_x = target_x
                self._smooth_y = target_y
            else:
                a = self._smooth_factor
                self._smooth_x = a * target_x + (1 - a) * self._smooth_x
                self._smooth_y = a * target_y + (1 - a) * self._smooth_y

            self.index_pos = (int(self._smooth_x), int(self._smooth_y))

            # Pulgar (para feedback visual)
            self.thumb_pos = (
                int(thumb_tip.x * w * scale_x),
                int(thumb_tip.y * h * scale_y)
            )

            # ── Distancia de pinch ──
            dx = (index_tip.x - thumb_tip.x) * w
            dy = (index_tip.y - thumb_tip.y) * h
            self.pinch_distance = math.sqrt(dx * dx + dy * dy)
            self.is_pinching = self.pinch_distance < 40

            # Flancos
            if self.is_pinching and not self._was_pinching:
                self.pinch_just_started = True
            elif not self.is_pinching and self._was_pinching:
                self.pinch_just_released = True

        else:
            self.index_pos = None
            self.thumb_pos = None
            self.is_pinching = False
            self.handedness = None
            if self._was_pinching:
                self.pinch_just_released = True

    # ─────────────────────────────────────────────────────
    def cleanup(self):
        """Liberar recursos de MediaPipe."""
        self._landmarker.close()
