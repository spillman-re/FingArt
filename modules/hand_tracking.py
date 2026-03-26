import cv2
import mediapipe as mp

class HandDetector:
    def __init__(self, detection_con=0.7, track_con=0.7):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            model_complexity=0,  # <--- Optimización clave para rendimiento
            min_detection_confidence=detection_con,
            min_tracking_confidence=track_con
        )
        self.mp_draw = mp.solutions.drawing_utils

    def find_hands(self, img, draw=False):
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(img_rgb)
        if self.results.multi_hand_landmarks and draw:
            for hand_lms in self.results.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(img, hand_lms, self.mp_hands.HAND_CONNECTIONS)
        return img
    
    def get_position(self, img):
        self.lm_list = []
        if self.results.multi_hand_landmarks:
            my_hand = self.results.multi_hand_landmarks[0]
            # Aquí img.shape debe ser (720, 1280) gracias al resize previo
            h, w, c = img.shape 
            for id, lm in enumerate(my_hand.landmark):
                cx, cy = int(lm.x * w), int(lm.y * h)
                self.lm_list.append([id, cx, cy])
        return self.lm_list

    def fingers_up(self):
        if not self.lm_list: return [0,0,0,0,0]
        fingers = []
        # Pulgar (Lógica simplificada para diestros)
        if self.lm_list[4][1] > self.lm_list[3][1]:
            fingers.append(1)
        else:
            fingers.append(0)
        # Otros 4 dedos
        for id in [8, 12, 16, 20]:
            if self.lm_list[id][2] < self.lm_list[id - 2][2]:
                fingers.append(1)
            else:
                fingers.append(0)
        return fingers