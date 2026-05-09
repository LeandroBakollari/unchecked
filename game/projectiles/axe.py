import pygame

from game.projectiles.base import ProjectileBase


class AxeProjectile(ProjectileBase):
    """A straight-flying axe that spins after it launches."""

    def __init__(self, x, y, dx, dy, image, speed=560, damage=12):
        direction = pygame.Vector2(dx, dy)
        if direction.length_squared() <= 1e-6:
            direction = pygame.Vector2(0, 1)
        direction = direction.normalize()

        super().__init__(x, y, direction.x, direction.y, speed, image, damage, lifetime=6500)

        self.base_image = image
        self.spin_angle = 0.0
        self.spin_speed = 520.0
        self.hitbox_scale = 0.58
        self.rect = self.image.get_rect(center=(x, y))

    def get_hitbox(self):
        return self.rect.inflate(
            -int(self.rect.width * (1.0 - self.hitbox_scale)),
            -int(self.rect.height * (1.0 - self.hitbox_scale)),
        )

    def get_debug_hitboxes(self):
        return [{"type": "rect", "rect": self.get_hitbox(), "label": "axe"}]

    def update(self, dt, player):
        if pygame.time.get_ticks() - self.spawn_time > self.lifetime:
            self.active = False
            return

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

        screen_rect = pygame.display.get_surface().get_rect().inflate(120, 120)
        if not screen_rect.collidepoint(self.x, self.y):
            self.active = False
