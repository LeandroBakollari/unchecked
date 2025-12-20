import math
import random
import pygame
from game.attacks.base import AttackBase
from game import utils


class SwordAttack(AttackBase):
    """
    Sword attack:
    - 3 loose slashes near the player's position at spawn + 1 cross slash at the player's spot.
    - Sword appears at the draw spot for 2s, hops slightly downward, vanishes, then previews begin.
    - Red pulsing preview lines for ~2.5s, then the sword stabs along the line and disappears.
    """

    def __init__(self, pen_rect, player_rect, assets, damage=15):
        super().__init__(pen_rect, player_rect, assets)
        self.sword_img = assets["sword_img"]
        self.damage = damage

        self.idle_time = 1.3
        self.idle_hop = 12
        self.preview_time = 1.7
        self.strike_time = 0.25

        self.slash_length = 360
        self.preview_thickness = 10
        self.slash_half_width = self.preview_thickness * 0.5
        self.global_timer = 0.0
        self.sword_visible = True
        self.sword_origin = pygame.Vector2(pen_rect.center)
        self.hopped = False

        self.slashes = []
        self._spawn_slashes(player_rect)

    def _make_slash(self, center_pos, angle_deg, preview_offset=0.0):
        # define start/end in local coords centered at center_pos
        half_len = self.slash_length * 0.5
        dir_vec = pygame.Vector2(math.cos(math.radians(angle_deg)), math.sin(math.radians(angle_deg)))
        start = pygame.Vector2(center_pos) - dir_vec * half_len
        end = pygame.Vector2(center_pos) + dir_vec * half_len
        return {
            "center": pygame.Vector2(center_pos),
            "start": start,
            "end": end,
            "angle": angle_deg,
            "timer": 0.0,
            "hit": False,
            "preview_offset": preview_offset,
            "sword_pos": None,
        }

    def _spawn_slashes(self, player_rect):
        center = pygame.Vector2(player_rect.center)
        radius = 150

        for _ in range(2):
            offset_dir = pygame.Vector2(random.uniform(50, radius), 0).rotate(random.uniform(0, 360))
            pos = center + offset_dir
            angle = random.uniform(-130, 130)
            jitter = random.uniform(-0.1, 0.1)
            self.slashes.append(self._make_slash(pos, angle, jitter))

        for angle in (45, -45):
            self.slashes.append(self._make_slash(center, angle, 0.0))

    def update(self, dt, projectiles, player):
        if self.finished:
            return []

        self.global_timer += dt

        # hide sword after idle and hop slightly down
        if self.sword_visible and self.global_timer >= self.idle_time:
            if not self.hopped:
                self.sword_origin.y += self.idle_hop
                self.hopped = True
            self.sword_visible = False

        if self.global_timer < self.idle_time:
            return []

        for slash in self.slashes:
            slash["timer"] += dt
            t = slash["timer"] - slash["preview_offset"]

            # strike moment
            if self.preview_time <= t < self.preview_time + self.strike_time and not slash["hit"]:
                center = slash["center"]
                ang = slash["angle"]
                if utils.swing_hits_rect(center, ang, self.slash_length, self.slash_half_width, player.get_hitbox()):
                    player.take_damage(self.damage)
                slash["hit"] = True

            # sword position during strike
            if self.preview_time <= t < self.preview_time + self.strike_time:
                prog = (t - self.preview_time) / self.strike_time
                sword_point = slash["start"].lerp(slash["end"], 0.4 + 0.6 * prog)
                slash["sword_pos"] = sword_point
            elif t >= self.preview_time + self.strike_time:
                if slash["sword_pos"] is None:
                    slash["sword_pos"] = slash["end"]
                if not slash["hit"]:
                    slash["hit"] = True

        if all(s["timer"] >= s["preview_offset"] + self.preview_time + self.strike_time for s in self.slashes):
            self.finished = True

        return []

    def draw(self, surface):
        if self.finished:
            return

        if self.sword_visible:
            origin_rect = self.sword_img.get_rect(center=self.sword_origin)
            surface.blit(self.sword_img, origin_rect)

        for slash in self.slashes:
            t = slash["timer"] - slash["preview_offset"]

            # preview line pulse
            if t < self.preview_time and not self.sword_visible:
                alpha = int(130 + 90 * (0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.008)))
                start = slash["start"]
                end = slash["end"]
                pygame.draw.line(surface, (220, 40, 40, alpha), start, end, int(self.preview_thickness))
                pygame.draw.line(surface, (255, 90, 90, alpha), start, end, max(2, int(self.preview_thickness * 0.45)))

            # sword during strike only
            if self.preview_time <= t < self.preview_time + self.strike_time:
                pos = slash["sword_pos"]
                if pos is None:
                    continue
                angle = -slash["angle"]
                img = pygame.transform.rotate(self.sword_img, angle)
                render_pos = pygame.Vector2(pos)
                rect = img.get_rect(center=(int(render_pos.x), int(render_pos.y)))
                surface.blit(img, rect)
