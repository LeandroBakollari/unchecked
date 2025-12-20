import math
import pygame
from game.attacks.base import AttackBase
from game.projectiles.bullet import BulletProjectile
from game import utils


class StaffAttack(AttackBase):
    """
    Staff fires two staggered waves of fireballs in a 140° cone aimed at the player area center.
    Wave 1: 7 fireballs, 20° apart starting at cone start.
    Wave 2: 6 fireballs, offset by +10° from cone start, 20° apart.
    """

    def __init__(self, pen_rect, player_rect, assets):
        super().__init__(pen_rect, player_rect, assets)
        self.staff_img_raw = assets["slash_img"]
        self.fireball_img = assets["bullet_img"]

        self.origin = pygame.Vector2(pen_rect.center)
        self.base_angle = utils.angle_from_vector(
            *utils.vector_to(self.origin, player_rect.center)[:2]
        )

        self.cone_width = 140
        self.step = 20
        self.wave1_count = 7
        self.wave2_count = 6
        self.wave2_offset = 10

        self.windup = 0.35
        self.wave_gap = 0.35
        self.timer = 0.0
        self.wave1_fired = False
        self.wave2_fired = False
        self.cleanup_time = 1.2

        self.staff_img = pygame.transform.smoothscale(
            self.staff_img_raw, (int(self.staff_img_raw.get_width() * 1.2), int(self.staff_img_raw.get_height() * 0.8))
        )

    def _spawn_wave(self, start_angle, count, projectiles):
        spawned = []
        for i in range(count):
            ang = start_angle + i * self.step
            rad = math.radians(ang)
            dx, dy = math.cos(rad), math.sin(rad)
            bullet = BulletProjectile(
                self.origin.x,
                self.origin.y,
                dx,
                dy,
                self.fireball_img,
            )
            spawned.append(bullet)
        projectiles.extend(spawned)

    def update(self, dt, projectiles, player):
        if self.finished:
            return []

        self.timer += dt

        if not self.wave1_fired and self.timer >= self.windup:
            start = self.base_angle - (self.cone_width / 2)
            self._spawn_wave(start, self.wave1_count, projectiles)
            self.wave1_fired = True

        if not self.wave2_fired and self.timer >= self.windup + self.wave_gap:
            start = self.base_angle - (self.cone_width / 2) + self.wave2_offset
            self._spawn_wave(start, self.wave2_count, projectiles)
            self.wave2_fired = True

        if self.timer >= self.windup + self.wave_gap + self.cleanup_time:
            self.finished = True

        return []

    def draw(self, surface):
        angle = -self.base_angle
        img = pygame.transform.rotate(self.staff_img, angle)
        rect = img.get_rect(center=self.origin)
        surface.blit(img, rect)
