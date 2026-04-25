import pygame


class ProjectileBase:
    def __init__(self, x, y, dx, dy, speed, image, damage, lifetime=2000):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.speed = speed
        self.image = image
        self.damage = damage

        self.rect = self.image.get_rect(center=(x, y))
        self.spawn_time = pygame.time.get_ticks()
        self.lifetime = lifetime
        self.active = True

    def get_hitbox(self):
        return self.rect

    def get_debug_hitboxes(self):
        return [
            {
                "type": "rect",
                "rect": self.get_hitbox(),
                "label": "projectile",
            }
        ]

    def update(self, dt, player):
        self.x += self.dx * self.speed * dt
        self.y += self.dy * self.speed * dt
        self.rect.center = (self.x, self.y)

        if pygame.time.get_ticks() - self.spawn_time > self.lifetime:
            self.active = False
            return

        hitbox = player.get_hitbox() if hasattr(player, "get_hitbox") else player.rect
        if self.get_hitbox().colliderect(hitbox):
            player.take_damage(self.damage)
            self.active = False

    def draw(self, screen):
        screen.blit(self.image, self.rect)
