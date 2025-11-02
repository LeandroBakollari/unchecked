import pygame
import math


class AttackBase:
    """Base class for attacks. Subclass and implement update() and draw().
    Constructor arguments should include references to pen_rect, player_rect and any shared assets dict.
    """
    def __init__(self, pen_rect, player_rect, assets):
        self.pen_rect = pen_rect
        self.player_rect = player_rect
        self.assets = assets
        self.finished = False


    def update(self, projectiles, player):
        """All spawned projectiles are appended to this list."""
        return []


    def draw(self, surface):
        raise NotImplementedError


    @staticmethod
    def angle_to(target_from, target_to):
        dx = target_to[0] - target_from[0]
        dy = target_to[1] - target_from[1]
        theta = math.atan2(-dy, dx)
        return math.degrees(theta), theta