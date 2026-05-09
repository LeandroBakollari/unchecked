import pygame

from game.attacks.base import AttackBase
from game.projectiles.axe import AxeProjectile


class AxeAttack(AttackBase):
    """A spinning axe that locks onto the player at launch and flies straight."""

    def __init__(self, pen_rect, player_rect, assets):
        super().__init__(pen_rect, player_rect, assets)

        self.origin = pygame.Vector2(pen_rect.center)
        self.base_image = assets["axe_img"]
        self.image = self.base_image
        self.rect = self.image.get_rect(center=self.origin)

        self.launch_delay = 0.75
        self.cleanup_delay = 0.1
        self.timer = 0.0
        self.launched = False

        self.spin_angle = 0.0
        self.spin_speed = 420.0

    def _spawn_axe(self, player):
        target = pygame.Vector2(player.get_rect().center)
        direction = target - self.origin
        if direction.length_squared() <= 1e-6:
            direction = pygame.Vector2(0, 1)
        direction = direction.normalize()
        return AxeProjectile(self.origin.x, self.origin.y, direction.x, direction.y, self.base_image)

    def get_debug_hitboxes(self):
        if self.finished:
            return []
        return [{"type": "rect", "rect": self.rect, "label": "axe ready"}]

    def update(self, dt, projectiles, player):
        if self.finished:
            return []

        self.timer += dt
        self.spin_angle = (self.spin_angle + self.spin_speed * dt) % 360.0
        self.image = pygame.transform.rotate(self.base_image, -self.spin_angle)
        self.rect = self.image.get_rect(center=(int(self.origin.x), int(self.origin.y)))

        spawned = []
        if not self.launched and self.timer >= self.launch_delay:
            spawned.append(self._spawn_axe(player))
            self.launched = True

        if self.launched and self.timer >= self.launch_delay + self.cleanup_delay:
            self.finished = True

        return spawned

    def draw(self, surface):
        if self.finished or self.launched:
            return
        surface.blit(self.image, self.rect)
