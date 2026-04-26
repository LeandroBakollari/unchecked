import math
import pygame

from game import utils
from game.projectiles.base import ProjectileBase


class ShurikenProjectile(ProjectileBase):
    """A spinning projectile that gently curves toward the player's current position until it leaves the screen."""

    def __init__(self, x, y, dx, dy, image, speed=520, damage=10):
        super().__init__(x, y, dx, dy, speed, image, damage, lifetime=10000)

        # Store a clean base sprite because each frame re-renders the spin from the original image.
        self.base_image = image
        self.spin_angle = 0.0
        self.spin_speed = 300.0

        # Gentle steering keeps the path readable instead of snapping directly onto the player.
        self.turn_rate_degrees = 65.0
        self.hitbox_scale = 0.6
        self.rect = self.image.get_rect(center=(x, y))

    def get_hitbox(self):
        return self.rect.inflate(
            -int(self.rect.width * (1.0 - self.hitbox_scale)),
            -int(self.rect.height * (1.0 - self.hitbox_scale)),
        )

    def _normalize_angle(self, angle_deg):
        """Wrap an angle to the -180 to 180 range so turn clamping behaves consistently."""
        return (angle_deg + 180.0) % 360.0 - 180.0

    def update(self, dt, player):
        """Curve the shuriken slightly toward the player, spin it, and remove it once it leaves the screen."""
        if pygame.time.get_ticks() - self.spawn_time > self.lifetime:
            self.active = False
            return

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

        self.spin_angle = (self.spin_angle + self.spin_speed * dt) % 360.0
        self.image = pygame.transform.rotate(self.base_image, -self.spin_angle)
        self.rect = self.image.get_rect(center=(int(self.x), int(self.y)))

        hitbox = player.get_hitbox() if hasattr(player, "get_hitbox") else player.rect
        if self.get_hitbox().colliderect(hitbox):
            player.take_damage(self.damage)
            self.active = False
            return

        screen_rect = pygame.display.get_surface().get_rect()
        margin = 80
        if (
            self.x < screen_rect.left - margin
            or self.x > screen_rect.right + margin
            or self.y < screen_rect.top - margin
            or self.y > screen_rect.bottom + margin
        ):
            self.active = False
