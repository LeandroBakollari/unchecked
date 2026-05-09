import math

import pygame

from game import utils
from game.projectiles.base import ProjectileBase


class FireworkProjectile(ProjectileBase):
    """A firework that can fly straight first, then curve toward a locked angle."""

    def __init__(
        self,
        x,
        y,
        angle_deg,
        image,
        target_angle=None,
        speed=430,
        damage=8,
        curve_delay=0.65,
        curve_duration=1.25,
        lifetime=6500,
    ):
        self.base_image = image
        self.start_angle = angle_deg
        self.current_angle = angle_deg
        self.target_angle = target_angle
        self.curve_delay = curve_delay
        self.curve_duration = max(0.01, curve_duration)
        self.hitbox_scale = 0.48
        self.age = 0.0
        self.lifetime_seconds = lifetime / 1000.0

        dx, dy = self._direction_from_angle(angle_deg)
        super().__init__(x, y, dx, dy, speed, image, damage, lifetime=lifetime)
        self._update_sprite()

    def _direction_from_angle(self, angle_deg):
        radians = math.radians(angle_deg)
        return math.cos(radians), math.sin(radians)

    def _normalize_angle_delta(self, angle_deg):
        return (angle_deg + 180.0) % 360.0 - 180.0

    def _set_angle(self, angle_deg):
        self.current_angle = angle_deg
        self.dx, self.dy = self._direction_from_angle(angle_deg)

    def _update_heading(self):
        if self.target_angle is None:
            return

        if self.age < self.curve_delay:
            return

        progress = utils.clamp((self.age - self.curve_delay) / self.curve_duration, 0.0, 1.0)
        angle_delta = self._normalize_angle_delta(self.target_angle - self.start_angle)
        self._set_angle(self.start_angle + angle_delta * progress)

    def _update_sprite(self):
        angle = pygame.math.Vector2(self.dx, self.dy).angle_to(pygame.math.Vector2(0, -1))
        self.image = pygame.transform.rotate(self.base_image, angle)
        self.rect = self.image.get_rect(center=(int(self.x), int(self.y)))

    def get_hitbox(self):
        return self.rect.inflate(
            -int(self.rect.width * (1.0 - self.hitbox_scale)),
            -int(self.rect.height * (1.0 - self.hitbox_scale)),
        )

    def get_debug_hitboxes(self):
        return [{"type": "rect", "rect": self.get_hitbox(), "label": "firework"}]

    def update(self, dt, player):
        self.age += dt
        if self.age > self.lifetime_seconds:
            self.active = False
            return

        self._update_heading()
        self.x += self.dx * self.speed * dt
        self.y += self.dy * self.speed * dt
        self._update_sprite()

        hitbox = player.get_hitbox() if hasattr(player, "get_hitbox") else player.rect
        if self.get_hitbox().colliderect(hitbox):
            player.take_damage(self.damage)
            self.active = False
            return

        screen_rect = pygame.display.get_surface().get_rect().inflate(180, 180)
        if not screen_rect.collidepoint(self.x, self.y):
            self.active = False
