# ============================================================
#  flower.py  -  METEOR FLOWER BUNCH
#  ──────────────────────────────────────────────────────────
#  A bunch of flowers that orbit around a center point
#  (your palm) like a meteor shower.
#
#  Visual elements:
#    - FlowerMeteorBunch  : the whole group orbiting your hand
#    - MeteorFlower       : one flower with a glowing comet tail
#    - CometTail          : stores position history, draws glow trail
#    - Sparkle            : burst particle when flower fully blooms
# ============================================================

import pygame
import math
import random


# ─────────────────────────────────────────────────────────────
#  Shared drawing helpers
# ─────────────────────────────────────────────────────────────

def draw_circle_alpha(surface, color, cx, cy, radius, alpha):
    """Draw a transparent circle using a temp surface + set_alpha."""
    if radius < 1 or alpha <= 0:
        return
    d = radius * 2 + 2
    temp = pygame.Surface((d, d))
    temp.fill((0, 0, 0))
    temp.set_colorkey((0, 0, 0))
    temp.set_alpha(max(0, min(255, alpha)))
    pygame.draw.circle(temp, color, (radius + 1, radius + 1), radius)
    surface.blit(temp, (int(cx) - radius - 1, int(cy) - radius - 1))


def draw_ellipse_alpha(surface, color, rect, alpha):
    """Draw a transparent ellipse. rect = (x,y,w,h) in surface coords."""
    if rect[2] < 2 or rect[3] < 2 or alpha <= 0:
        return
    temp = pygame.Surface((rect[2], rect[3]))
    temp.fill((0, 0, 0))
    temp.set_colorkey((0, 0, 0))
    temp.set_alpha(max(0, min(255, alpha)))
    pygame.draw.ellipse(temp, color, (0, 0, rect[2], rect[3]))
    surface.blit(temp, (rect[0], rect[1]))


# ─────────────────────────────────────────────────────────────
class CometTail:
    """
    Stores the last N positions of a flower and draws a
    glowing, fading trail behind it like a comet.
    """

    def __init__(self, color, max_length=35):
        self.base_color = color
        self.max_length = max_length
        self.positions  = []   # list of (x, y)

    def add(self, x, y):
        self.positions.append((float(x), float(y)))
        if len(self.positions) > self.max_length:
            self.positions.pop(0)

    def draw(self, surface):
        n = len(self.positions)
        if n < 2:
            return
        for i, (x, y) in enumerate(self.positions):
            # frac: 0.0 = oldest tip of tail, 1.0 = newest (at flower)
            frac   = i / max(1, n - 1)
            alpha  = int(frac * 220)
            radius = max(1, int(frac * 9))
            draw_circle_alpha(surface, self.base_color, x, y, radius, alpha)


# ─────────────────────────────────────────────────────────────
class Sparkle:
    """A glittery particle burst when a flower reaches full bloom."""

    def __init__(self, x, y, color):
        self.x     = float(x)
        self.y     = float(y)
        angle      = random.uniform(0, 2 * math.pi)
        speed      = random.uniform(2.0, 7.0)
        self.vx    = math.cos(angle) * speed
        self.vy    = math.sin(angle) * speed
        self.life  = 1.0
        self.decay = random.uniform(0.018, 0.04)
        self.size  = random.randint(2, 6)
        self.color = color

    def update(self):
        self.x    += self.vx
        self.y    += self.vy
        self.vy   += 0.12   # gentle gravity
        self.vx   *= 0.97   # air friction
        self.life -= self.decay

    def is_alive(self):
        return self.life > 0

    def draw(self, surface):
        alpha  = int(self.life * 255)
        radius = max(1, int(self.size * self.life))
        draw_circle_alpha(surface, self.color, self.x, self.y, radius, alpha)


# ─────────────────────────────────────────────────────────────
class MeteorFlower:
    """
    ONE flower that orbits around a center point.
    Has a CometTail trailing behind it and sparks when fully bloomed.

    orbit_angle  : starting angle (degrees) in the circular orbit
    theme_index  : selects the petal color
    """

    # 7 different color themes — one per flower in the bunch
    THEMES = [
        ((255,  70, 150), (255, 160, 200)),   # Hot pink
        ((160,  60, 255), (210, 140, 255)),   # Violet
        ((255, 200,  30), (255, 235, 100)),   # Gold
        (( 40, 200, 255), (130, 230, 255)),   # Sky blue
        ((255, 110,  40), (255, 180, 100)),   # Orange
        (( 80, 255, 140), (160, 255, 200)),   # Mint
        ((255,  40, 200), (255, 140, 230)),   # Magenta
    ]

    def __init__(self, orbit_angle, theme_index=0):
        self.orbit_angle  = float(orbit_angle)   # current angle in orbit (degrees)
        self.orbit_radius = 60.0                 # starts tight, expands with bloom
        self.x            = 0.0
        self.y            = 0.0
        self.bloom_level  = 0.0
        self.spin         = random.uniform(0, 360)  # petal spin offset

        theme              = self.THEMES[theme_index % len(self.THEMES)]
        self.color_outer   = theme[0]
        self.color_inner   = theme[1]
        self.center_color  = (255, 235, 80)

        # Comet tail uses the inner (lighter) petal color
        self.tail     = CometTail(self.color_inner, max_length=35)
        self.sparkles = []
        self._was_full = False

    # ── Called every frame ────────────────────────────────────
    def update(self, cx, cy, target_bloom, orbit_speed, target_radius):
        # Advance the orbit angle
        self.orbit_angle += orbit_speed

        # Smoothly grow/shrink the orbit radius
        self.orbit_radius += (target_radius - self.orbit_radius) * 0.09

        # Compute x, y from angle + radius
        rad  = math.radians(self.orbit_angle)
        self.x = cx + math.cos(rad) * self.orbit_radius
        self.y = cy + math.sin(rad) * self.orbit_radius

        # Smooth bloom transition
        self.bloom_level += (target_bloom - self.bloom_level) * 0.09
        self.bloom_level  = max(0.0, min(1.0, self.bloom_level))

        # Slowly spin the petals
        self.spin += 0.6

        # Feed position into comet tail
        self.tail.add(self.x, self.y)

        # Sparkle burst on full bloom
        if self.bloom_level > 0.97 and not self._was_full:
            self._was_full = True
            for _ in range(20):
                c = random.choice([
                    self.color_outer, self.color_inner,
                    (255, 255, 200), (255, 220, 100),
                ])
                self.sparkles.append(Sparkle(self.x, self.y, c))

        if self.bloom_level < 0.88:
            self._was_full = False

        # Update + cull dead sparkles
        self.sparkles = [s for s in self.sparkles if s.is_alive()]
        for s in self.sparkles:
            s.update()

    # ── Draw ──────────────────────────────────────────────────
    def draw(self, surface):
        # 1. Comet tail (drawn behind everything)
        self.tail.draw(surface)

        # 2. Sparkle particles
        for s in self.sparkles:
            s.draw(surface)

        # 3. Flower itself
        if self.bloom_level < 0.04:
            # Tiny glowing bud
            draw_circle_alpha(surface, (60, 200, 80),
                              self.x, self.y, 5, 200)
            return

        self._draw_petals(surface)
        self._draw_center(surface)

    def _draw_petals(self, surface):
        MAX   = 55          # max flower size (pixels)
        N     = 6           # number of petals
        bl    = self.bloom_level
        pw    = max(2, int(MAX * 0.36 * bl))
        ph    = max(2, int(MAX * 0.58 * bl))
        spread = max(1, int(MAX * 0.27 * bl))

        if pw < 2 or ph < 2:
            return

        for i in range(N):
            ang_deg = (360 / N) * i + self.spin
            ang_rad = math.radians(ang_deg)
            px = self.x + math.cos(ang_rad) * spread
            py = self.y + math.sin(ang_rad) * spread

            color = self.color_outer if i % 2 == 0 else self.color_inner

            # Build petal surface
            pw2, ph2 = pw * 2, ph * 2
            petal = pygame.Surface((pw2 + 2, ph2 + 2))
            petal.fill((0, 0, 0))
            petal.set_colorkey((0, 0, 0))
            petal.set_alpha(215)
            pygame.draw.ellipse(petal, color, (1, 1, pw2, ph2))

            rotated = pygame.transform.rotate(petal, -ang_deg - 90)
            rect    = rotated.get_rect(center=(int(px), int(py)))
            surface.blit(rotated, rect)

    def _draw_center(self, surface):
        r  = max(2, int(13 * self.bloom_level))
        cx, cy = int(self.x), int(self.y)
        # Outer glow
        draw_circle_alpha(surface, self.center_color, cx, cy, r + 3, 80)
        # Solid center
        pygame.draw.circle(surface, self.center_color, (cx, cy), r)
        pygame.draw.circle(surface, (255, 255, 210), (cx, cy), max(1, r - 3))


# ─────────────────────────────────────────────────────────────
class FlowerMeteorBunch:
    """
    A group of MeteorFlowers orbiting a center point (your palm).

    Gesture control:
      bloom_level 0.0  →  tight cluster, slow spin, buds
      bloom_level 0.5  →  medium orbit, medium speed, half bloom
      bloom_level 1.0  →  wide orbit, fast spin, full bloom + sparkles
    """

    def __init__(self, cx, cy, num_flowers=7):
        self.center_x  = float(cx)
        self.center_y  = float(cy)
        self.bloom_level = 0.0

        # Spread flowers evenly around the circle
        self.flowers = [
            MeteorFlower(
                orbit_angle = (360 / num_flowers) * i,
                theme_index = i
            )
            for i in range(num_flowers)
        ]

    # ── Called every frame ────────────────────────────────────
    def update(self, target_bloom, new_cx=None, new_cy=None):
        # Smoothly follow hand position
        if new_cx is not None:
            self.center_x += (new_cx - self.center_x) * 0.13
        if new_cy is not None:
            self.center_y += (new_cy - self.center_y) * 0.13

        # Orbit speed : 0.4 deg/frame (slow, closed) → 3.2 deg/frame (fast, open)
        orbit_speed = 0.4 + target_bloom * 2.8

        # Orbit radius: 80px (fist) → 230px (open hand)
        target_radius = 80 + target_bloom * 150

        for flower in self.flowers:
            flower.update(
                self.center_x, self.center_y,
                target_bloom, orbit_speed, target_radius
            )

    # ── Draw ──────────────────────────────────────────────────
    def draw(self, surface):
        # Draw a soft glow at center (palm indicator)
        draw_circle_alpha(surface, (200, 200, 255),
                          self.center_x, self.center_y, 18, 40)

        for flower in self.flowers:
            flower.draw(surface)
