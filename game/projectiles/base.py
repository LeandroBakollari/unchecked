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

    def update(self, dt, player):
        # Move
        self.x += self.dx * self.speed * dt
        self.y += self.dy * self.speed * dt
        self.rect.center = (self.x, self.y)

        # Lifetime check
        if pygame.time.get_ticks() - self.spawn_time > self.lifetime:
            self.active = False
            return

        # Collision check
        if self.rect.colliderect(player.rect):
            player.take_damage(self.damage)   # ✅ correct damage call
            self.active = False

    def draw(self, screen):
        screen.blit(self.image, self.rect)
