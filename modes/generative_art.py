import cv2
import numpy as np
import math
import random

class GenerativeArtMode:
    def __init__(self, width=1280, height=720):
        self.width, self.height = width, height
        self.canvas = np.zeros((height, width, 3), np.uint8)
        self.center = (width // 2, height // 2)

        self.effects = [
            "MANDALA", "HEATMAP", "GRAVITY",
            "BLACKHOLE", "GRAVITY_PARTICLES",
            "VORTEX", "EXPLOSION", "FLOW", "COSMIC"
        ]

        self.active_idx = 0
        self.particles = []
        self.time = 0
        self.sidebar_w = 150
        self.brush_color_hue = 0
        self.MAX_PARTICLES = 1500
        self.menu_btn_pos = (20, 20, 130, 80)

    # 🔥 -------- LAYOUT CENTRALIZADO --------
    def _get_ui_layout(self):
        available_height = self.height - 120
        num_effects = len(self.effects)

        button_height = available_height // num_effects
        button_height = max(50, min(button_height, 80))

        start_y = 100

        return start_y, button_height

    # ------------------ UPDATE ------------------

    def update(self, img, lm_list, fingers):
        self.time += 0.05

        x1, y1 = lm_list[8][1], lm_list[8][2]
        x2, y2 = lm_list[4][1], lm_list[4][2]
        dist = math.hypot(x1 - x2, y1 - y2)

        # ---- BOTÓN MENÚ ----
        if self.menu_btn_pos[0] < x1 < self.menu_btn_pos[2] and \
           self.menu_btn_pos[1] < y1 < self.menu_btn_pos[3]:
            return "SWITCH_MENU"

        # ---- UI CLICK ----
        if x1 < self.sidebar_w:
            start_y, button_h = self._get_ui_layout()

            for i in range(len(self.effects)):
                y_pos = start_y + i * button_h

                if y_pos < y1 < y_pos + button_h:
                    if self.active_idx != i:
                        self.active_idx = i
                        self.canvas[:] = 0
                        self.particles.clear()

        # ---- FADE ----
        self.canvas = cv2.subtract(self.canvas, (12, 12, 12))

        pinch = dist < 45

        # -------- EFECTOS --------
        if self.active_idx == 0:
            if pinch: self._mandala(x1, y1, self.get_color())

        elif self.active_idx == 1:
            if pinch: self._heatmap_paint(x1, y1)

        elif self.active_idx == 2:
            img = self._gravity_well(img, x1, y1, pinch)

        elif self.active_idx == 3:
            img = self._blackhole(img, x1, y1, pinch)

        elif self.active_idx == 4:
            if pinch: self._gravity_particles(x1, y1, self.get_color())

        elif self.active_idx == 5:
            img = self._vortex(img, x1, y1)

        elif self.active_idx == 6:
            if pinch: self._explosion(x1, y1, self.get_color())

        elif self.active_idx == 7:
            if pinch: self._flow_field(x1, y1, self.get_color())

        elif self.active_idx == 8:
            if pinch: self._cosmic(x1, y1, self.get_color())

        # ---- partículas ----
        self._update_particles(x1, y1)

        # ---- mezcla ----
        img = cv2.add(img, self.canvas)

        return self.draw_ui(img)

    def get_color(self):
        self.brush_color_hue = (self.brush_color_hue + 2) % 180
        hsv = np.uint8([[[self.brush_color_hue, 255, 255]]])
        return tuple(map(int, cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)[0][0]))

    # ------------------ EFECTOS ------------------

    def _mandala(self, x, y, color):
        dx, dy = x - self.center[0], y - self.center[1]
        for i in range(10):
            angle = i * (math.pi * 2 / 10)
            rx = int(dx * math.cos(angle) - dy * math.sin(angle) + self.center[0])
            ry = int(dx * math.sin(angle) + dy * math.cos(angle) + self.center[1])
            cv2.circle(self.canvas, (rx, ry), 10, color, -1)
            cv2.circle(self.canvas, (rx, ry), 3, (255, 255, 255), -1)

    def _heatmap_paint(self, x, y):
        for _ in range(2):
            cv2.circle(self.canvas, (x, y), random.randint(15, 25), (255, 255, 255), -1)

    def _gravity_well(self, img, x, y, active):
        rows, cols = img.shape[:2]
        map_x, map_y = np.meshgrid(np.arange(cols), np.arange(rows))
        map_x = map_x.astype(np.float32)
        map_y = map_y.astype(np.float32)

        dx, dy = map_x - x, map_y - y
        dist = np.sqrt(dx*dx + dy*dy)

        radius = 180
        strength = 1.5 if active else 0.5

        mask = dist < radius
        factor = np.power(dist[mask]/radius, strength)

        map_x[mask] = x + dx[mask] * factor
        map_y[mask] = y + dy[mask] * factor

        return cv2.remap(img, map_x, map_y, cv2.INTER_LINEAR)

    def _blackhole(self, img, x, y, active):
        rows, cols = img.shape[:2]
        map_x, map_y = np.meshgrid(np.arange(cols), np.arange(rows))
        map_x = map_x.astype(np.float32)
        map_y = map_y.astype(np.float32)

        dx, dy = map_x - x, map_y - y
        dist = np.sqrt(dx*dx + dy*dy) + 1e-5

        radius = 220
        strength = 2.2 if active else 0.8

        mask = dist < radius
        pull = (radius / dist[mask]) ** strength

        map_x[mask] = x + dx[mask] / pull
        map_y[mask] = y + dy[mask] / pull

        warped = cv2.remap(img, map_x, map_y, cv2.INTER_LINEAR)

        dark = np.clip(1 - (dist / radius), 0, 1)
        dark = np.expand_dims(dark, axis=2)

        return (warped * (1 - dark * 0.8)).astype(np.uint8)

    def _vortex(self, img, x, y):
        rows, cols = img.shape[:2]
        map_x, map_y = np.meshgrid(np.arange(cols), np.arange(rows))
        map_x = map_x.astype(np.float32)
        map_y = map_y.astype(np.float32)

        dx, dy = map_x - x, map_y - y
        dist = np.sqrt(dx*dx + dy*dy)

        angle = np.arctan2(dy, dx)
        swirl = 2.5 * np.exp(-dist / 200)

        new_angle = angle + swirl

        map_x = x + dist * np.cos(new_angle)
        map_y = y + dist * np.sin(new_angle)

        return cv2.remap(img, map_x, map_y, cv2.INTER_LINEAR)

    def _gravity_particles(self, x, y, color):
        for _ in range(4):
            angle = random.uniform(0, 2 * math.pi)
            dist = random.uniform(20, 80)

            self.particles.append({
                "x": x + math.cos(angle)*dist,
                "y": y + math.sin(angle)*dist,
                "vx": 0, "vy": 0,
                "color": color,
                "life": 255,
                "mode": "orbit",
                "cx": x, "cy": y
            })

    def _explosion(self, x, y, color):
        for _ in range(12):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(5, 15)

            self.particles.append({
                "x": x, "y": y,
                "vx": math.cos(angle)*speed,
                "vy": math.sin(angle)*speed,
                "color": color,
                "life": 255
            })

    def _flow_field(self, x, y, color):
        for _ in range(2):
            self.particles.append({
                "x": x, "y": y,
                "vx": random.uniform(-2,2),
                "vy": random.uniform(-2,2),
                "color": color,
                "life": 150,
                "mode": "flow"
            })

    def _cosmic(self, x, y, color):
        for i in range(3):
            angle = self.time * 3 + i * 2
            px = int(x + math.cos(angle)*50)
            py = int(y + math.sin(angle)*50)

            cv2.circle(self.canvas, (px, py), 6, color, -1)
            cv2.circle(self.canvas, (px, py), 2, (255, 255, 255), -1)

    # ------------------ PARTICULAS ------------------

    def _update_particles(self, cx, cy):
        new_particles = []

        for p in self.particles:

            if p.get("mode") == "flow":
                angle = math.sin(p["x"] * 0.01 + self.time) + math.cos(p["y"] * 0.01)
                p["vx"] += math.cos(angle) * 0.5
                p["vy"] += math.sin(angle) * 0.5

            elif p.get("mode") == "orbit":
                dx, dy = cx - p["x"], cy - p["y"]
                dist = math.hypot(dx, dy) + 0.001

                force = 0.8 / dist
                p["vx"] += dx * force
                p["vy"] += dy * force

                p["vx"] += -dy * 0.01
                p["vy"] += dx * 0.01

            p["x"] += p["vx"]
            p["y"] += p["vy"]

            p["vx"] *= 0.96
            p["vy"] *= 0.96
            p["life"] -= 5

            if p["life"] > 0:
                alpha = p["life"] / 255
                c = tuple(int(v * alpha) for v in p["color"])
                cv2.circle(self.canvas, (int(p["x"]), int(p["y"])), 3, c, -1)
                new_particles.append(p)

        self.particles = new_particles[-self.MAX_PARTICLES:]

    # ------------------ UI ------------------

    def draw_ui(self, img):
        overlay = img.copy()

        cv2.rectangle(overlay, (0, 0), (self.sidebar_w, self.height), (20, 20, 20), -1)
        cv2.rectangle(overlay, (20, 20), (130, 80), (150, 50, 0), -1)

        cv2.addWeighted(overlay, 0.6, img, 0.4, 0, img)

        cv2.putText(img, "MENU", (45, 55),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        start_y, button_h = self._get_ui_layout()

        for i, name in enumerate(self.effects):
            y = start_y + i * button_h
            active = (i == self.active_idx)

            color = (0, 255, 255) if active else (150, 150, 150)

            cv2.rectangle(img, (10, y), (self.sidebar_w - 10, y + button_h - 10),
                          color, 3 if active else 1)

            cv2.putText(img, name, (20, y + int(button_h * 0.6)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

        return img