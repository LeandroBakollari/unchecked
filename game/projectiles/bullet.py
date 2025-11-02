import math
import pygame
from .base import ProjectileBase

class BulletProjectile(ProjectileBase):
    def __init__(self, x, y, dx, dy, image, speed=600, damage=10, lifetime=2500):
        super().__init__(x, y, dx, dy, speed, image, damage, lifetime)

        angle_rad = pygame.math.Vector2(dx, dy).angle_to(pygame.math.Vector2(0, -1))  # default bullet points up
        self.image = pygame.transform.rotate(image, angle_rad)
        self.rect = self.image.get_rect(center=(x, y))
