import math
import pygame
from game.attacks.base import AttackBase
from game.projectiles.bullet import BulletProjectile
from game import utils


class ShotgunAttack(AttackBase):
    """
    Fires two staggered waves of projectiles in a 140° cone aimed at the player area center.
    Wave 1: 7 projectiles, 20° apart.
    Wave 2: 6 projectiles, offset by +10° from the cone start.
    """

    def __init__(self, pen_rect, player_rect, assets):
        super().__init__(pen_rect, player_rect, assets)
        # The source shotgun art points left, so we flip it once to create a right-facing base for rotation.
        self.gun_img_raw = pygame.transform.flip(assets["shotgun_img"], True, False)
        self.projectile_img = assets["bullet_img"]

        # The shotgun remains anchored at the pen's draw position and only uses the initial player location to aim.
        self.origin = pygame.Vector2(pen_rect.center)
        self.base_angle = utils.angle_from_vector(*utils.vector_to(self.origin, player_rect.center)[:2])

        # These values describe the two-wave pellet spread.
        self.cone_width = 140
        self.step = 20
        self.wave1_count = 7
        self.wave2_count = 6
        self.wave2_offset = 10

        # Windup and cleanup keep the sprite on screen long enough to read the attack.
        self.windup = 0.35
        self.wave_gap = 0.35
        self.timer = 0.0
        self.wave1_fired = False
        self.wave2_fired = False
        self.cleanup_time = 1.2

        self.gun_img = pygame.transform.smoothscale(
            self.gun_img_raw, (int(self.gun_img_raw.get_width() * 1.2), int(self.gun_img_raw.get_height() * 0.8))
        )

    def _spawn_wave(self, start_angle, count, projectiles):
        """Spawn one spread wave by stepping through the cone angle in fixed increments."""
        for i in range(count):
            ang = start_angle + i * self.step
            rad = math.radians(ang)
            dx, dy = math.cos(rad), math.sin(rad)
            bullet = BulletProjectile(
                self.origin.x,
                self.origin.y,
                dx,
                dy,
                self.projectile_img,
            )
            projectiles.append(bullet)

    def update(self, dt, projectiles, player):
        """Fire the two pellet waves on schedule, then mark the attack finished after a short linger."""
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
        """Rotate the corrected base sprite so the muzzle faces the recorded target angle."""
        angle = -self.base_angle
        img = pygame.transform.rotate(self.gun_img, angle)
        rect = img.get_rect(center=self.origin)
        surface.blit(img, rect)
