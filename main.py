# ============================================================
#  main.py  -  BLOOM: Meteor Flower Hand Tracker
#  ──────────────────────────────────────────────────────────
#  Run:  python main.py
#
#  Every frame:
#    1. Grab webcam frame
#    2. MediaPipe detects hand landmarks
#    3. Count fingers -> bloom_level (0.0 - 1.0)
#    4. Update FlowerMeteorBunch (orbit speed, radius, bloom)
#    5. Draw everything on screen
# ============================================================

import cv2
import pygame
import sys
import math
import random
import numpy as np

from hand_tracker import HandTracker
from gesture      import get_bloom_level, get_palm_position
from flower       import FlowerMeteorBunch

# ── Window & Camera Settings ─────────────────────────────────
WIN_W  = 1280
WIN_H  = 720
CAM_W  = 640
CAM_H  = 480
FPS    = 30

# ── Colors ────────────────────────────────────────────────────
BG_COLOR       = (8,  5, 20)     # deep dark purple-black
UI_COLOR       = (210, 210, 255) # soft lavender
DIM_COLOR      = (80,  80, 120)  # dimmer hints
BORDER_COLOR   = (60,  60, 100)

# ── Camera preview (top-right) ────────────────────────────────
PREV_W  = 280
PREV_H  = 210
PREV_X  = WIN_W - PREV_W - 16
PREV_Y  = 16


# ─────────────────────────────────────────────────────────────
def frame_to_surface(bgr_frame, w, h):
    """Convert OpenCV BGR frame to a Pygame surface."""
    resized    = cv2.resize(bgr_frame, (w, h))
    rgb        = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
    transposed = np.transpose(rgb, (1, 0, 2))   # (H,W,C) -> (W,H,C) for pygame
    return pygame.surfarray.make_surface(transposed)


def draw_stars(surface, stars):
    """Draw the static background starfield."""
    for sx, sy, bright in stars:
        pygame.draw.circle(surface, (bright, bright, bright), (sx, sy), 1)


# ─────────────────────────────────────────────────────────────
def main():

    # ── Pygame init ──────────────────────────────────────────
    pygame.init()
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption("Bloom - Meteor Flower Shower")
    clock  = pygame.time.Clock()
    font_b = pygame.font.SysFont("Arial", 24, bold=True)
    font_s = pygame.font.SysFont("Arial", 17)

    # ── Webcam init ──────────────────────────────────────────
    print("Opening webcam...")
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(0)          # fallback: no backend flag
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  CAM_W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_H)
    cap.set(cv2.CAP_PROP_FPS, FPS)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        print("ERROR: Webcam not found!")
        sys.exit(1)

    print("Warming up camera...")
    for _ in range(20):
        cap.read()
    print("Camera ready!")

    # ── Hand tracker ─────────────────────────────────────────
    tracker = HandTracker(max_hands=2)

    # ── Flower meteor bunches (one per hand, up to 2) ────────
    # Both start in the center; they move to each hand position
    bunches = [
        FlowerMeteorBunch(WIN_W // 2 - 150, WIN_H // 2, num_flowers=7),
        FlowerMeteorBunch(WIN_W // 2 + 150, WIN_H // 2, num_flowers=7),
    ]

    # ── Static starfield ─────────────────────────────────────
    random.seed(99)
    stars = [
        (random.randint(0, WIN_W),
         random.randint(0, WIN_H),
         random.randint(30, 140))
        for _ in range(250)
    ]

    print("*** Bloom is running! Show your hand to the camera. ***")
    print("   Open hand = flowers orbit wide + bloom fully")
    print("   Fist      = flowers cluster tight + close")
    print("   2 hands   = 2 meteor bunches!")
    print("   Press ESC to quit.")

    # ── Main loop ─────────────────────────────────────────────
    while True:

        # Handle window close / ESC
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                cap.release(); pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                cap.release(); pygame.quit(); sys.exit()

        # ── Read webcam frame ─────────────────────────────────
        ok, frame = cap.read()
        if not ok or frame is None:
            missed = getattr(main, "_miss", 0) + 1
            main._miss = missed
            if missed % 60 == 1:
                print(f"Camera frame dropped ({missed}). Close Teams/Zoom if camera is black.")
            pygame.event.pump()
            clock.tick(FPS)
            continue
        main._miss = 0

        frame = cv2.flip(frame, 1)               # mirror
        frame, landmarks_list = tracker.find_hands(frame, draw=True)

        # ── Draw background ───────────────────────────────────
        screen.fill(BG_COLOR)
        draw_stars(screen, stars)

        # ── Update flower bunches from hand landmarks ─────────
        num_hands = len(landmarks_list)

        for i, lm in enumerate(landmarks_list):
            if i >= len(bunches):
                break

            bloom = get_bloom_level(lm)

            # Palm pixel position in webcam space
            px, py = get_palm_position(lm, CAM_W, CAM_H)

            # Map webcam coords to screen coords
            # Leave right side free for camera preview
            sx = int((px / CAM_W) * (WIN_W - PREV_W - 60)) + 30
            sy = int((py / CAM_H) * WIN_H)

            bunches[i].update(bloom, sx, sy)

        # Hands that disappeared -> slowly close their bunch
        for i in range(num_hands, len(bunches)):
            bunches[i].update(0.0)     # target bloom = 0 -> flowers close

        # ── Draw flower bunches ───────────────────────────────
        for i, bunch in enumerate(bunches):
            # Draw if hand is active OR bunch hasn't fully closed yet
            any_visible = any(f.bloom_level > 0.01 for f in bunch.flowers)
            if i < num_hands or any_visible:
                bunch.draw(screen)

        # ── Camera preview ────────────────────────────────────
        cam_surf = frame_to_surface(frame, PREV_W, PREV_H)
        screen.blit(cam_surf, (PREV_X, PREV_Y))
        pygame.draw.rect(screen, BORDER_COLOR,
                         (PREV_X - 2, PREV_Y - 2, PREV_W + 4, PREV_H + 4), 2)
        lbl = font_s.render("Camera", True, DIM_COLOR)
        screen.blit(lbl, (PREV_X, PREV_Y - 20))

        # ── UI text ───────────────────────────────────────────
        if num_hands == 0:
            msg = font_b.render("Show your hand to the camera!", True, UI_COLOR)
            screen.blit(msg, (WIN_W // 2 - msg.get_width() // 2, WIN_H - 55))
        else:
            for i, lm in enumerate(landmarks_list):
                if i >= len(bunches):
                    break
                fingers   = int(get_bloom_level(lm) * 5)
                bloom_pct = int(bunches[i].flowers[0].bloom_level * 100)
                clr = [(255, 140, 190), (170, 130, 255)][i]
                txt = font_s.render(
                    f"Hand {i+1}: {fingers}/5 fingers  |  Bloom {bloom_pct}%  |  "
                    f"Orbit speed x{0.4 + get_bloom_level(lm)*2.8:.1f}",
                    True, clr
                )
                screen.blit(txt, (16, WIN_H - 48 + i * 24))

        esc = font_s.render("ESC = quit", True, DIM_COLOR)
        screen.blit(esc, (16, 16))

        pygame.display.flip()
        clock.tick(FPS)


# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nBye! Closing Bloom.")
        pygame.quit()
        sys.exit(0)
