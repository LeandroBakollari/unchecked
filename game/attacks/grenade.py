import math
import random
import pygame
from game.attacks.base import AttackBase
from game import utils


class GrenadeAttack(AttackBase):
    """Grenade attack behavior with pulsing preview and timed explosion."""

    def __init__(self, pen_rect, player_rect, assets, speed=520, explosion_radius=120, fuse_after_land=0.45):
        super().__init__(pen_rect, player_rect, assets)
        self.grenade_img = assets["grenade_img"]
        scale = 1.2
        w, h = self.grenade_img.get_width(), self.grenade_img.get_height()
        self.grenade_img = pygame.transform.scale(self.grenade_img, (int(w * scale), int(h * scale)))
        self.explosion_img = assets.get("explosion_img")
        self.spawn_x, self.spawn_y = self.pen_rect.center
        self.target = player_rect.center
        self.x, self.y = pen_rect.center
        self.speed = speed
        dx, dy, dist = utils.vector_to((self.x, self.y), self.target)
        dist = dist or 1.0
        self.vel_x = (dx / dist) * speed
        self.vel_y = (dy / dist) * speed
        self.angle = 0.0
        self.rotation_speed = random.uniform(180.0, 360.0)
        self.rect = self.grenade_img.get_rect(center=(int(self.x), int(self.y)))
        self.landed = False
        self.explosion_radius = explosion_radius
        self.damage = 20
        self.preview_alpha = 90
        self.preview_pulse_dir = 1
        self.explosion_show_time = 0.0
        self.explosion_duration = 0.35

    def update(self, dt, projectiles, player):
        if self.finished:
            return []

        if not self.landed:
            self.x += self.vel_x * dt
            self.y += self.vel_y * dt
            self.angle = (self.angle + self.rotation_speed * dt) % 360
            self.rect.center = (int(self.x), int(self.y))

            if math.hypot(self.x - self.target[0], self.y - self.target[1]) < max(12, self.speed * dt):
                self.landed = True
                self.explode(player)
                self.explosion_show_time = self.explosion_duration
        else:
            if self.explosion_show_time > 0:
                self.explosion_show_time -= dt
                if self.explosion_show_time <= 0:
                    self.finished = True
                return []

        self.preview_alpha += self.preview_pulse_dir * 140 * dt
        if self.preview_alpha >= 200:
            self.preview_pulse_dir = -1
        if self.preview_alpha <= 30:
            self.preview_pulse_dir = 1
        return []

    def explode(self, player):
        dx = player.get_rect().centerx - self.target[0]
        dy = player.get_rect().centery - self.target[1]
        if math.hypot(dx, dy) <= self.explosion_radius:
            player.take_damage(self.damage)

    def get_debug_hitboxes(self):
        if self.finished:
            return []
        return [
            {
                "type": "circle",
                "center": self.target,
                "radius": self.explosion_radius,
                "label": "grenade",
            }
        ]

    def draw(self, surface):
        if not self.landed:
            radius = int(self.explosion_radius * (0.9 + 0.15 * math.sin(pygame.time.get_ticks() / 200)))
            s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            alpha = max(20, min(220, int(self.preview_alpha)))
            pygame.draw.circle(s, (200, 0, 0, alpha), (radius, radius), radius)
            surface.blit(s, (self.target[0] - radius, self.target[1] - radius))

        rotated = pygame.transform.rotate(self.grenade_img, self.angle)
        rect = rotated.get_rect(center=self.rect.center)
        surface.blit(rotated, rect)

        if self.landed and self.explosion_show_time > 0:
            if self.explosion_img:
                ex = pygame.transform.scale(
                    self.explosion_img,
                    (int(self.explosion_radius * 2) + 100, int(self.explosion_radius * 2) + 100),
                )
                rect = ex.get_rect(center=self.target)
                surface.blit(ex, rect)
