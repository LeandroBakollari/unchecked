import math
import pygame

from game import utils
from game.projectiles.base import ProjectileBase


class MissileProjectile(ProjectileBase):
    """A small missile that homes aggressively, then locks its heading and exits."""

    def __init__(self, x, y, dx, dy, image, speed=400, damage=6):
        direction = pygame.Vector2(dx, dy)
        if direction.length_squared() <= 1e-6:
            direction = pygame.Vector2(1, 0)
        direction = direction.normalize()

        super().__init__(x, y, direction.x, direction.y, speed, image, damage, lifetime=18000)

        self.base_image = image
        self.source_angle = -5.0
        self.turn_rate_degrees = 80.0
        self.homing_duration = 10.0
        self.hitbox_scale = 0.58
        self._update_sprite()

    def _normalize_angle(self, angle_deg):
        return (angle_deg + 180.0) % 360.0 - 180.0

    def _update_sprite(self):
        angle = math.degrees(math.atan2(self.dy, self.dx))
        self.image = pygame.transform.rotate(self.base_image, -(angle - self.source_angle))
        self.rect = self.image.get_rect(center=(int(self.x), int(self.y)))

    def get_hitbox(self):
        return self.rect.inflate(
            -int(self.rect.width * (1.0 - self.hitbox_scale)),
            -int(self.rect.height * (1.0 - self.hitbox_scale)),
        )

    def get_debug_hitboxes(self):
        return [{"type": "rect", "rect": self.get_hitbox(), "label": "missile"}]

    def update(self, dt, player):
        elapsed = (pygame.time.get_ticks() - self.spawn_time) / 1000.0
        if pygame.time.get_ticks() - self.spawn_time > self.lifetime:
            self.active = False
            return

        if elapsed < self.homing_duration:
            desired = pygame.Vector2(player.get_rect().centerx - self.x, player.get_rect().centery - self.y)
            if desired.length_squared() > 1e-6:
                desired_angle = math.degrees(math.atan2(desired.y, desired.x))
                current_angle = math.degrees(math.atan2(self.dy, self.dx))
                turn_step = self.turn_rate_degrees * dt
                angle_delta = self._normalize_angle(desired_angle - current_angle)
                current_angle += utils.clamp(angle_delta, -turn_step, turn_step)
                self.dx = math.cos(math.radians(current_angle))
                self.dy = math.sin(math.radians(current_angle))

        self.x += self.dx * self.speed * dt
        self.y += self.dy * self.speed * dt
        self._update_sprite()

        hitbox = player.get_hitbox() if hasattr(player, "get_hitbox") else player.rect
        if self.get_hitbox().colliderect(hitbox):
            player.take_damage(self.damage)
            self.active = False
            return

        screen_rect = pygame.display.get_surface().get_rect()
        margin = 120
        if (
            self.x < screen_rect.left - margin
            or self.x > screen_rect.right + margin
            or self.y < screen_rect.top - margin
            or self.y > screen_rect.bottom + margin
        ):
            self.active = False
