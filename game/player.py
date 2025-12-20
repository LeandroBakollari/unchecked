import pygame


class Player:
    def __init__(self, image, screen_w, screen_h):
        self.image = image
        self.rect = image.get_rect()
        self.rect.centerx = screen_w // 2
        self.rect.bottom = screen_h - 50
        self.health = 100
        self._max_health = 100
        self.speed = 420  # units per second
        self.alive = True

    @property
    def max_health(self):
        return self._max_health

    @max_health.setter
    def max_health(self, v):
        self._max_health = v

    def get_rect(self):
        return self.rect

    def get_hitbox(self):
        return self.rect.inflate(-8, -8)

    def update(self, dt, area_rect):
        keys = pygame.key.get_pressed()
        move_x = (1 if keys[pygame.K_RIGHT] or keys[pygame.K_d] else 0) - (
            1 if keys[pygame.K_LEFT] or keys[pygame.K_a] else 0
        )
        move_y = (1 if keys[pygame.K_DOWN] or keys[pygame.K_s] else 0) - (
            1 if keys[pygame.K_UP] or keys[pygame.K_w] else 0
        )
        if move_x or move_y:
            length = (move_x**2 + move_y**2) ** 0.5 or 1.0
            self.rect.x += int((move_x / length) * self.speed * dt)
            self.rect.y += int((move_y / length) * self.speed * dt)

        self.rect.clamp_ip(area_rect)

    def on_resize(self, screen_w, screen_h):
        # keep the player roughly at the same relative place (near bottom center)
        self.rect.centerx = screen_w // 2
        self.rect.bottom = min(self.rect.bottom, screen_h - 40)

    def take_damage(self, amount):
        if not self.alive:
            return
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            self.alive = False

    def draw(self, surface):
        surface.blit(self.image, self.rect)
