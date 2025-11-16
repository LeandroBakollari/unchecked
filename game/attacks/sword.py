import pygame
import math
import random
from game.attacks.base import AttackBase


class SwordAttack(AttackBase):
    """
    Sprite-based sword attack.
    - 5 total slashes spawned at init:
        * 2 slashes locked to player center (angles -45, +45) — they follow player each frame
        * 3 slashes at random positions across the player's movement area (random angles)
    - Timing (frames @60fps) shortened by 0.5s:
        wait:  30  (0.0 - 0.5s)
        preview: 120 (0.5 - 2.0s)
        slash active: 120-210 (2.0 - 3.5s)  -> present for 1.5s
        finish: 270 (4.5s total)
    - Images are pre-scaled & rotated once at spawn to avoid per-frame transforms.
    """

    def __init__(self, pen_rect, player_rect, assets, damage=15):
        super().__init__(pen_rect, player_rect, assets)

        # assets you provide
        self.sword_img = assets["sword_img"]   # small center/hilt image
        self.slash_img = assets["slash_img"]   # vertical image (2:7 ratio)

        self.damage = damage
        self.origin = pen_rect.center

        # TIMING (reduced by 0.5s)
        self.wait_time = 30        # 0.0 - 0.5s
        self.preview_time = 120    # 0.5 - 2.0s
        self.slash_start = 120     # 2.0s
        self.slash_end = 210       # 3.5s
        self.finish_time = 270     # 4.5s
        self.timer = 0
        self.finished = False

        # how big to draw slashes relative to original image:
        # we increase scale to make slashes longer, but not huge (keeps perf)
        self.SLASH_SCALE = 1.1

        # how far random slashes may appear from screen edges (padding)
        self.RANDOM_AREA_PADDING = 40

        # number of slashes by type:
        self.TOTAL = 5
        self.FOLLOW_COUNT = 2   # these lock to player
        self.RANDOM_COUNT = 3

        # storage for slashes
        # each entry: { x,y, angle_deg, surf_preview, surf_real, is_follow, hit }
        self.slashes = []

        # spawn all 5 (two follow + three random)
        self.spawn_slashes(player_rect)


    # --------------------------
    # SPAWN LOGIC
    # --------------------------
    def spawn_slashes(self, player_rect):
        px, py = player_rect.center

        # prepare scaled base
        base_w = int(self.slash_img.get_width() * self.SLASH_SCALE)
        base_h = int(self.slash_img.get_height() * self.SLASH_SCALE)
        base_surf = pygame.transform.smoothscale(self.slash_img, (base_w, base_h))

        # --- TWO that FOLLOW the player (angles -45 and +45) ---
        for angle in (-45, 45):
            # initially at player center; will be updated each frame
            surf_real = pygame.transform.rotate(base_surf, -angle)
            surf_preview = surf_real.copy()
            surf_preview.set_alpha(140)  # preview alpha
            self.slashes.append({
                "x": px, "y": py,
                "angle": angle,
                "surf_real": surf_real,
                "surf_preview": surf_preview,
                "is_follow": True,
                "hit": False
            })

        # --- determine random placement area ---
        # try to use the actual screen surface (preferred)
        try:
            screen = pygame.display.get_surface()
            sw, sh = screen.get_width(), screen.get_height()
            area_left = self.RANDOM_AREA_PADDING
            area_top = self.RANDOM_AREA_PADDING
            area_right = sw - self.RANDOM_AREA_PADDING
            area_bottom = sh - self.RANDOM_AREA_PADDING
        except Exception:
            # fallback: use a rectangle around the player (big)
            area_left = px - 400
            area_top = py - 300
            area_right = px + 400
            area_bottom = py + 300

        # --- THREE random slashes anywhere in that area ---
        for _ in range(self.RANDOM_COUNT):
            rx = random.randint(int(area_left), int(area_right))
            ry = random.randint(int(area_top), int(area_bottom))
            ang = random.uniform(0, 360)
            surf_real = pygame.transform.rotate(base_surf, -ang)
            surf_preview = surf_real.copy()
            surf_preview.set_alpha(140)
            self.slashes.append({
                "x": rx, "y": ry,
                "angle": ang,
                "surf_real": surf_real,
                "surf_preview": surf_preview,
                "is_follow": False,
                "hit": False
            })


    # --------------------------
    # UPDATE (called every frame)
    # --------------------------
    def update(self, projectiles, player):
        if self.finished:
            return

        self.timer += 1

        # update follow slashes to player's current center so they always hit you directly
        px, py = player.get_rect().center
        for s in self.slashes:
            if s["is_follow"]:
                s["x"], s["y"] = px, py

        # apply damage when the slashes first spawn (at slash_start)
        if self.timer == self.slash_start:
            self.apply_damage(player)

        if self.timer >= self.finish_time:
            self.finished = True


    # --------------------------
    # DAMAGE: very simple, checks distance to line center
    # We check a small width around the slash centerline.
    # --------------------------
    def apply_damage(self, player):
        # player center
        px, py = player.get_rect().center

        # width threshold (how "thick" the slash hits)
        width_threshold = 18

        for s in self.slashes:
            if s["hit"]:
                continue

            # compute perpendicular distance from player to slash line:
            # treat slash as infinite line through (x,y) with orientation angle theta
            sx, sy = s["x"], s["y"]
            theta = math.radians(s["angle"])

            # vector from slash center to player
            vx = px - sx
            vy = py - sy

            # perpendicular distance = |vx * sin(theta) - vy * cos(theta)|
            perp = abs(vx * math.sin(theta) - vy * math.cos(theta))

            if perp <= width_threshold:
                # in range -> apply damage once
                try:
                    player.take_damage(self.damage)
                except Exception:
                    # safe fallback if player's API differs
                    if hasattr(player, "hp"):
                        player.hp -= self.damage
                s["hit"] = True
            else:
                s["hit"] = True  # mark as checked so we don't recheck


    # --------------------------
    # DRAW
    # --------------------------
    def draw(self, surf):
        if self.finished:
            return

        # draw sword base/hilt
        base_rect = self.sword_img.get_rect(center=self.origin)
        surf.blit(self.sword_img, base_rect)

        # PREVIEW PHASE (semi-transparent)
        if self.wait_time <= self.timer < self.preview_time:
            # interpolation alpha for nicer fade-in
            t = (self.timer - self.wait_time) / max(1, (self.preview_time - self.wait_time))
            alpha = int(110 + 120 * t)  # from ~110 -> ~230
            for s in self.slashes:
                img = s["surf_preview"]
                # we use a copy so we don't permanently change alpha
                img_to_draw = img.copy()
                img_to_draw.set_alpha(alpha)
                rect = img_to_draw.get_rect(center=(int(s["x"]), int(s["y"])))
                surf.blit(img_to_draw, rect)

        # REAL SLASH PHASE (full opacity)
        if self.slash_start <= self.timer < self.slash_end:
            for s in self.slashes:
                rect = s["surf_real"].get_rect(center=(int(s["x"]), int(s["y"])))
                surf.blit(s["surf_real"], rect)
