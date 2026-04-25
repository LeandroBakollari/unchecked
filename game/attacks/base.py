import math
import pygame
from game import utils


class AttackBase:
    """Base class for attacks. Subclass and implement update() and draw()."""

    def __init__(self, pen_rect, player_rect, assets):
        self.pen_rect = pen_rect
        self.player_rect = player_rect
        self.assets = assets
        self.finished = False
        self.spawn_time = pygame.time.get_ticks()

    def update(self, dt, projectiles, player):
        """Override in subclasses; append spawned projectiles to projectiles."""
        return []

    def draw(self, surface):
        raise NotImplementedError

    def get_debug_hitboxes(self):
        """Return debug collision shapes for the current attack state."""
        return []

    @staticmethod
    def angle_to(target_from, target_to):
        dx, dy, _ = utils.vector_to(target_from, target_to)
        deg = utils.angle_from_vector(dx, dy)
        return deg, math.radians(deg)
