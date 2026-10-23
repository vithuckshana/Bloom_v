# ============================================================
#  main2.py  -  BLOOM: Italian Pinch Gesture Bouquet
#  ----------------------------------------------------------
#  Run:  python main2.py
#
#  Gesture:
#    Pinch all fingers together (Italian ??)  ->  flowers hidden
#    Slowly open your fingers                  ->  flowers GROW + BLOOM
#    Pinch back to ??                          ->  flowers hide
#
#  The bloom level is directly tied to how open your fingers are.
#  Moving your hand moves the whole bouquet.
# ============================================================

import cv2
import pygame
import sys
import math
import random
import numpy as np

from hand_tracker import HandTracker

# -- Settings --------------------------------------------------
WIN_W  = 1280
WIN_H  = 720
CAM_W  = 640
CAM_H  = 480
FPS    = 30

BG_COLOR   = (8,   5,  20)
UI_COLOR   = (220, 220, 255)
DIM_COLOR  = ( 80,  80, 120)

PREV_W = 280
PREV_H = 210
PREV_X = WIN_W - PREV_W - 16
PREV_Y = 16


# -------------------------------------------------------------
#  Drawing helpers
# -------------------------------------------------------------

def draw_circle_alpha(surface, color, cx, cy, radius, alpha):
    """Draw a transparent filled circle."""
    if radius < 1 or alpha <= 0:
        return
    d = radius * 2 + 2
    temp = pygame.Surface((d, d))
    temp.fill((0, 0, 0))
    temp.set_colorkey((0, 0, 0))
    temp.set_alpha(max(0, min(255, alpha)))
    pygame.draw.circle(temp, color, (radius + 1, radius + 1), radius)
    surface.blit(temp, (int(cx) - radius - 1, int(cy) - radius - 1))


# -------------------------------------------------------------
#  Gesture: Pinch Spread Detector
# -------------------------------------------------------------

def get_pinch_bloom(landmarks):
    """
    Detects how open the hand is from a pinch/gather position.

    Method:
      1. Get all 5 fingertip positions (thumb + 4 fingers)
      2. Calculate how spread out they are from their centroid
      3. Map spread distance -> bloom level 0.0 (pinched) to 1.0 (fully open)

    Returns float 0.0 - 1.0
    """
    tip_ids = [4, 8, 12, 16, 20]   # thumb, index, middle, ring, pinky tips
    xs = [landmarks[i].x for i in tip_ids]
    ys = [landmarks[i].y for i in tip_ids]

    # Centroid of fingertips
    cx = sum(xs) / len(xs)
    cy = sum(ys) / len(ys)

    # Average distance of each tip from the centroid
    avg_spread = sum(
        math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
        for x, y in zip(xs, ys)
    ) / len(tip_ids)

    # Map: 0.03 = fully pinched (??), 0.17 = fully open hand
    bloom = (avg_spread - 0.03) / (0.17 - 0.03)
    return max(0.0, min(1.0, bloom))


def get_palm_pos(landmarks, fw, fh):
    """Return palm center as pixel (x, y)."""
    return (
        int(landmarks[9].x * fw),
        int(landmarks[9].y * fh)
    )


# -------------------------------------------------------------
#  Sparkle Particle
# -------------------------------------------------------------

class Sparkle:
    def __init__(self, x, y, color):
        self.x     = float(x)
        self.y     = float(y)
        a          = random.uniform(0, 2 * math.pi)
        spd        = random.uniform(2, 6)
        self.vx    = math.cos(a) * spd
        self.vy    = math.sin(a) * spd
        self.life  = 1.0
        self.decay = random.uniform(0.02, 0.04)
        self.size  = random.randint(2, 5)
        self.color = color

    def update(self):
        self.x    += self.vx
        self.y    += self.vy
        self.vy   += 0.10
        self.vx   *= 0.97
        self.life -= self.decay

    def is_alive(self): return self.life > 0

    def draw(self, surface):
        draw_circle_alpha(surface, self.color,
                          self.x, self.y,
                          max(1, int(self.size * self.life)),
                          int(self.life * 255))


# -------------------------------------------------------------
#  Single Flower with Stem
# -------------------------------------------------------------

THEMES = [
    ((255,  70, 150), (255, 160, 200)),   # Hot pink
    ((160,  60, 255), (210, 140, 255)),   # Violet
    ((255, 200,  30), (255, 235, 100)),   # Gold
    (( 40, 200, 255), (130, 230, 255)),   # Sky blue
    ((255, 110,  40), (255, 180, 100)),   # Orange
    (( 80, 255, 140), (160, 255, 200)),   # Mint
    ((255,  40, 200), (255, 140, 230)),   # Magenta
]


class BouquetFlower:
    """
    A single flower with a stem that leans at a set angle.

    stem_angle   : degrees from vertical (0=straight up, negative=lean left)
    stem_length  : pixel length of the stem when fully bloomed
    theme_index  : which color pair to use
    """

    def __init__(self, stem_angle, stem_length, theme_index):
        self.stem_angle_deg = stem_angle
        self.stem_length    = stem_length
        self.theme_index    = theme_index
        self.bloom_level    = 0.0
        self.spin           = random.uniform(0, 360)   # petal rotation offset

        theme              = THEMES[theme_index % len(THEMES)]
        self.color_outer   = theme[0]
        self.color_inner   = theme[1]
        self.center_color  = (255, 235, 80)
        self.stem_color    = ( 50, 160,  60)
        self.leaf_color    = ( 70, 190,  80)

        self.sparkles  = []
        self._was_full = False

    def flower_head_pos(self, grip_x, grip_y):
        """
        Compute the flower-head position given the grip (base) point.
        Stems go UPWARD from the grip point.
        """
        rad = math.radians(self.stem_angle_deg)
        # sin for horizontal lean, -cos to go UP (pygame y=0 is top)
        hx  = grip_x + math.sin(rad) * self.stem_length * self.bloom_level
        hy  = grip_y - math.cos(rad) * self.stem_length * self.bloom_level
        return hx, hy

    def update(self, target_bloom):
        self.bloom_level += (target_bloom - self.bloom_level) * 0.07
        self.bloom_level  = max(0.0, min(1.0, self.bloom_level))
        self.spin        += 0.5

        # Sparkle burst at full bloom
        hx, hy = self.flower_head_pos(0, 0)   # relative, actual pos added in draw
        if self.bloom_level > 0.97 and not self._was_full:
            self._was_full = True
            # sparkles are emitted from actual position; store for draw()
            self._burst_pending = True

        if self.bloom_level < 0.88:
            self._was_full     = False
            self._burst_pending = getattr(self, "_burst_pending", False)

        self.sparkles = [s for s in self.sparkles if s.is_alive()]
        for s in self.sparkles:
            s.update()

    def draw(self, surface, grip_x, grip_y):
        bl = self.bloom_level
        if bl < 0.02:
            return

        hx, hy = self.flower_head_pos(grip_x, grip_y)

        # Emit sparkles if burst pending
        if getattr(self, "_burst_pending", False):
            self._burst_pending = False
            for _ in range(18):
                c = random.choice([self.color_outer, self.color_inner,
                                   (255, 255, 180), self.center_color])
                self.sparkles.append(Sparkle(hx, hy, c))

        # -- Stem ----------------------------------------------
        # Thicker stems that grow with bloom level
        stem_w     = max(2, int(6 * bl))   # up to 6px thick
        stem_alpha = int(bl * 255)

        # Draw stem with a highlight line for a 3D vine look
        stem_surf = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
        r, g, b   = self.stem_color
        pygame.draw.line(stem_surf, (r, g, b, stem_alpha),
                         (int(grip_x), int(grip_y)),
                         (int(hx),     int(hy)), stem_w)
        # Lighter center highlight line (makes stem look round/3D)
        if stem_w >= 3:
            r2, g2, b2 = min(255, r+60), min(255, g+60), min(255, b+40)
            pygame.draw.line(stem_surf, (r2, g2, b2, min(200, stem_alpha)),
                             (int(grip_x), int(grip_y)),
                             (int(hx),     int(hy)), max(1, stem_w - 2))
        surface.blit(stem_surf, (0, 0))

        # -- Leaves (appear after 40% bloom) -------------------
        if bl > 0.4:
            leaf_alpha = min(255, int((bl - 0.4) / 0.6 * 255))
            leaf_frac  = (bl - 0.4) / 0.6
            leaf_size  = max(4, int(26 * leaf_frac))   # bigger leaves
            # Position leaf at ~1/3 up the stem
            mid_x = int(grip_x + (hx - grip_x) * 0.38)
            mid_y = int(grip_y + (hy - grip_y) * 0.38)
            rad   = math.radians(self.stem_angle_deg)
            # Perpendicular direction for leaf
            perp_x = -math.cos(rad)
            perp_y = -math.sin(rad)
            for side in [-1, 1]:
                lx = mid_x + int(side * perp_x * leaf_size * 1.5)
                ly = mid_y + int(side * perp_y * leaf_size * 1.5)
                # Draw leaf as a slightly elongated ellipse
                leaf_surf = pygame.Surface((leaf_size * 3, leaf_size * 2))
                leaf_surf.fill((0, 0, 0))
                leaf_surf.set_colorkey((0, 0, 0))
                leaf_surf.set_alpha(leaf_alpha)
                pygame.draw.ellipse(leaf_surf, self.leaf_color,
                                    (0, 0, leaf_size * 3, leaf_size * 2))
                # Rotate leaf to align with stem angle
                rot_angle = math.degrees(math.atan2(perp_y, perp_x)) * side
                leaf_rot  = pygame.transform.rotate(leaf_surf, -rot_angle - 90)
                lr        = leaf_rot.get_rect(center=(lx, ly))
                surface.blit(leaf_rot, lr)

        # -- Flower bud / petals -------------------------------
        if bl < 0.08:
            # Tiny green bud at tip
            pygame.draw.circle(surface, self.leaf_color, (int(hx), int(hy)), 5)
            return

        self._draw_petals(surface, hx, hy)
        self._draw_center(surface, hx, hy)

        # -- Sparkles ------------------------------------------
        for s in self.sparkles:
            s.draw(surface)

    def _draw_petals(self, surface, fx, fy):
        """
        Draw a beautiful layered flower with:
          - Outer petals  (large, wide)
          - Inner petals  (smaller, rotated 30deg, different shade)
          - Glow halo around the whole flower
        """
        bl = self.bloom_level
        if bl < 0.08:
            return

        # --- Glow halo behind everything ---
        GLOW_R = int(85 * bl)
        if GLOW_R > 2:
            for gr in range(GLOW_R, GLOW_R // 2, -3):
                ga = int(30 * (1 - gr / GLOW_R))
                draw_circle_alpha(surface, self.color_outer, fx, fy, gr, ga)

        # --- Outer petals (6 large petals) ---
        N_OUT   = 6
        MAX_OUT = 120        # max petal height at full bloom
        pw_out  = max(3, int(MAX_OUT * 0.42 * bl))   # petal width
        ph_out  = max(3, int(MAX_OUT * 0.72 * bl))   # petal height
        sp_out  = max(2, int(MAX_OUT * 0.32 * bl))   # spread from center

        for i in range(N_OUT):
            ang_deg = (360 / N_OUT) * i + self.spin
            ang_rad = math.radians(ang_deg)
            px = fx + math.cos(ang_rad) * sp_out
            py = fy + math.sin(ang_rad) * sp_out
            color = self.color_outer if i % 2 == 0 else self.color_inner
            pw2, ph2 = pw_out * 2, ph_out * 2
            petal = pygame.Surface((pw2 + 4, ph2 + 4))
            petal.fill((0, 0, 0))
            petal.set_colorkey((0, 0, 0))
            petal.set_alpha(230)
            pygame.draw.ellipse(petal, color, (2, 2, pw2, ph2))
            # Lighter edge highlight on each petal
            hw, hh = max(1, pw2 - 8), max(1, ph2 - 12)
            if hw > 2 and hh > 2:
                hc = tuple(min(255, c + 60) for c in color)
                pygame.draw.ellipse(petal, hc, (pw2 // 2 - hw // 2 + 2,
                                                 6, hw, hh))
            rotated = pygame.transform.rotate(petal, -ang_deg - 90)
            rect    = rotated.get_rect(center=(int(px), int(py)))
            surface.blit(rotated, rect)

        # --- Inner petals (5 petals, rotated 36deg offset, smaller) ---
        N_IN   = 5
        pw_in  = max(2, int(MAX_OUT * 0.28 * bl))
        ph_in  = max(2, int(MAX_OUT * 0.50 * bl))
        sp_in  = max(1, int(MAX_OUT * 0.18 * bl))

        for i in range(N_IN):
            ang_deg = (360 / N_IN) * i + self.spin + 36
            ang_rad = math.radians(ang_deg)
            px = fx + math.cos(ang_rad) * sp_in
            py = fy + math.sin(ang_rad) * sp_in
            # Inner petals use the lighter shade
            color = self.color_inner
            pw2, ph2 = pw_in * 2, ph_in * 2
            petal = pygame.Surface((pw2 + 4, ph2 + 4))
            petal.fill((0, 0, 0))
            petal.set_colorkey((0, 0, 0))
            petal.set_alpha(200)
            pygame.draw.ellipse(petal, color, (2, 2, pw2, ph2))
            rotated = pygame.transform.rotate(petal, -ang_deg - 90)
            rect    = rotated.get_rect(center=(int(px), int(py)))
            surface.blit(rotated, rect)

    def _draw_center(self, surface, fx, fy):
        """Golden center with a bright inner highlight, like a real flower."""
        bl = self.bloom_level
        r  = max(3, int(20 * bl))          # big golden center

        # Outer glow ring
        draw_circle_alpha(surface, self.center_color, fx, fy, r + 8, 60)
        draw_circle_alpha(surface, self.center_color, fx, fy, r + 4, 100)

        # Main center disc
        pygame.draw.circle(surface, self.center_color, (int(fx), int(fy)), r)

        # Bright highlight spot (like a real sunflower center)
        pygame.draw.circle(surface, (255, 255, 220),
                           (int(fx) - r // 4, int(fy) - r // 4),
                           max(2, r // 3))

        # Dark dots pattern in center (sunflower look)
        if r > 8:
            for dot_angle in range(0, 360, 60):
                da  = math.radians(dot_angle + self.spin * 0.3)
                ddr = int(r * 0.52)
                dx  = int(fx + math.cos(da) * ddr)
                dy  = int(fy + math.sin(da) * ddr)
                pygame.draw.circle(surface, (180, 120, 10), (dx, dy), max(1, r // 5))


# -------------------------------------------------------------
#  Bouquet  (the whole bunch)
# -------------------------------------------------------------

class Bouquet:
    """
    A fan-shaped bouquet of 7 flowers with stems.
    Grip point = palm position.
    Flowers fan out UPWARD from the grip.

    Layout (viewed from front):
             ??  ??  ??  ??  ??  ??  ??
              \  \   |  |  |  /  /
               \  \  |  |  | /  /
                ---- grip ----
    """

    # (stem_angle_degrees, stem_length, theme_index)
    # Stems are long so flowers reach high above your hand
    LAYOUT = [
        (  0, 340, 0),   # center, tallest, straight up
        (-16, 315, 1),   # slightly left
        ( 16, 315, 2),   # slightly right
        (-34, 285, 3),   # more left
        ( 34, 285, 4),   # more right
        (-54, 250, 5),   # far left, shorter
        ( 54, 250, 6),   # far right, shorter
    ]

    def __init__(self, cx, cy):
        self.cx = float(cx)
        self.cy = float(cy)

        self.flowers = [
            BouquetFlower(angle, length, theme)
            for angle, length, theme in self.LAYOUT
        ]

    def update(self, target_bloom, new_cx=None, new_cy=None):
        if new_cx is not None:
            self.cx += (new_cx - self.cx) * 0.14
        if new_cy is not None:
            self.cy += (new_cy - self.cy) * 0.14
        for f in self.flowers:
            f.update(target_bloom)

    def draw(self, surface):
        # Draw from outermost (back) to center (front)
        draw_order = [6, 5, 4, 3, 2, 1, 0]
        for i in draw_order:
            self.flowers[i].draw(surface, self.cx, self.cy)

        # Subtle grip glow at palm
        draw_circle_alpha(surface, (180, 255, 180), self.cx, self.cy, 12, 50)


# -------------------------------------------------------------
#  Frame converter
# -------------------------------------------------------------

def frame_to_surface(bgr_frame, w, h):
    resized    = cv2.resize(bgr_frame, (w, h))
    rgb        = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
    transposed = np.transpose(rgb, (1, 0, 2))
    return pygame.surfarray.make_surface(transposed)


# -------------------------------------------------------------
#  Main
# -------------------------------------------------------------

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption("Bloom 2 - Pinch to Bloom")
    clock  = pygame.time.Clock()
    font_b = pygame.font.SysFont("Arial", 24, bold=True)
    font_s = pygame.font.SysFont("Arial", 17)

    # Webcam
    print("Opening webcam...")
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  CAM_W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_H)
    cap.set(cv2.CAP_PROP_FPS, FPS)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        print("ERROR: Webcam not found!"); sys.exit(1)

    print("Warming up camera...")
    for _ in range(20): cap.read()
    print("Camera ready!")

    # Hand tracker
    tracker = HandTracker(max_hands=2)

    # Two bouquets (one per hand)
    bouquets = [
        Bouquet(WIN_W // 2 - 150, WIN_H // 2),
        Bouquet(WIN_W // 2 + 150, WIN_H // 2),
    ]

    # Background stars
    random.seed(77)
    stars = [(random.randint(0, WIN_W),
        random.randint(0, WIN_H),
              random.randint(25, 130)) for _ in range(250)]

    print()
    print("*** Bloom 2 is running! ***")
    print("   Pinch fingers (Italian pinch gesture)  ->  flowers hidden")
    print("   Open your fingers           ->  flowers bloom with stems!")
    print("   Pinch again                 ->  flowers hide")
    print("   Press ESC to quit.")
    print()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                cap.release(); pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                cap.release(); pygame.quit(); sys.exit()

        # Webcam frame
        ok, frame = cap.read()
        if not ok or frame is None:
            missed = getattr(main, "_miss", 0) + 1
            main._miss = missed
            if missed % 60 == 1:
                print(f"Camera frame dropped ({missed}). Close Teams/Zoom.")
            pygame.event.pump()
            clock.tick(FPS)
            continue
        main._miss = 0

        frame = cv2.flip(frame, 1)
        frame, landmarks_list = tracker.find_hands(frame, draw=True)

        # Background
        screen.fill(BG_COLOR)
        for sx, sy, bright in stars:
            pygame.draw.circle(screen, (bright, bright, bright), (sx, sy), 1)

        # Update bouquets from hand landmarks
        num_hands = len(landmarks_list)

        for i, lm in enumerate(landmarks_list):
            if i >= len(bouquets):
                break
            # bloom_level = how open the hand is from pinch
            bloom = get_pinch_bloom(lm)

            # Palm pixel position
            px, py = get_palm_pos(lm, CAM_W, CAM_H)

            # Map to screen coords
            sx = int((px / CAM_W) * (WIN_W - PREV_W - 60)) + 30
            sy = int((py / CAM_H) * WIN_H)

            bouquets[i].update(bloom, sx, sy)

        # Hands gone -> flowers close
        for i in range(num_hands, len(bouquets)):
            bouquets[i].update(0.0)

        # Draw bouquets
        for i, bouquet in enumerate(bouquets):
            any_visible = any(f.bloom_level > 0.01 for f in bouquet.flowers)
            if i < num_hands or any_visible:
                bouquet.draw(screen)

        # Camera preview
        cam_surf = frame_to_surface(frame, PREV_W, PREV_H)
        screen.blit(cam_surf, (PREV_X, PREV_Y))
        pygame.draw.rect(screen, (60, 60, 100),
                         (PREV_X - 2, PREV_Y - 2, PREV_W + 4, PREV_H + 4), 2)
        lbl = font_s.render("Camera", True, DIM_COLOR)
        screen.blit(lbl, (PREV_X, PREV_Y - 20))

        # UI
        if num_hands == 0:
            msg = font_b.render("Show your hand and PINCH to start!", True, UI_COLOR)
            screen.blit(msg, (WIN_W // 2 - msg.get_width() // 2, WIN_H - 55))
        else:
            for i, lm in enumerate(landmarks_list):
                if i >= len(bouquets):
                    break
                bloom     = get_pinch_bloom(lm)
                bloom_pct = int(bouquets[i].flowers[0].bloom_level * 100)
                state     = "Pinched [--]" if bloom < 0.15 else ("Blooming!" if bloom < 0.85 else "Full bloom!")
                clr       = [(255, 150, 200), (170, 130, 255)][i]
                txt = font_s.render(
                    f"Hand {i+1}: {state}  |  Bloom {bloom_pct}%",
                    True, clr
                )
                screen.blit(txt, (16, WIN_H - 48 + i * 24))

        esc = font_s.render("ESC = quit  |  main.py = meteor mode  |  main2.py = bouquet mode",
                            True, DIM_COLOR)
        screen.blit(esc, (16, 16))

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nBye!")
        pygame.quit()
        sys.exit(0)

