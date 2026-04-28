import math
import pygame

from game import utils
from game.attacks.base import AttackBase
from game.projectiles.missile import MissileProjectile


class MissileLauncherAttack(AttackBase):
    """A tracking launcher that fires three aggressive homing missiles."""

    def __init__(self, pen_rect, player_rect, assets):
        super().__init__(pen_rect, player_rect, assets)

        self.origin = pygame.Vector2(pen_rect.center)
        self.base_image = assets["missile_launcher_img"]
        self.missile_image = assets["missile_img"]
        self.image = self.base_image
        self.rect = self.image.get_rect(center=self.origin)

        self.current_angle = utils.angle_from_vector(*(pygame.Vector2(player_rect.center) - self.origin))
        self.source_angle = 180.0
        self.muzzle_distance = max(self.base_image.get_width() * 0.42, 32)

        self.timer = 0.0
        self.first_fire_delay = 0.35
        self.fire_interval = 0.65
        self.shots_fired = 0
        self.total_shots = 3

        self.shake_timer = 0.0
        self.shake_duration = 0.18
        self.shake_offset = pygame.Vector2(0, 0)

    def _direction_from_angle(self, angle_deg):
        radians = math.radians(angle_deg)
        return pygame.Vector2(math.cos(radians), math.sin(radians))

    def _muzzle_position(self):
        return self.origin + self._direction_from_angle(self.current_angle) * self.muzzle_distance

    def _update_aim(self, player):
        target = pygame.Vector2(player.get_rect().center)
        direction = target - self.origin
        if direction.length_squared() <= 1e-6:
            direction = pygame.Vector2(1, 0)
        self.current_angle = math.degrees(math.atan2(direction.y, direction.x))

    def _update_shake(self, dt):
        if self.shake_timer <= 0.0:
            self.shake_offset.update(0, 0)
            return

        self.shake_timer = max(0.0, self.shake_timer - dt)
        progress = self.shake_timer / self.shake_duration
        direction = self._direction_from_angle(self.current_angle)
        perpendicular = pygame.Vector2(-direction.y, direction.x)
        recoil = -direction * (10.0 * progress)
        wobble = perpendicular * (4.0 * progress * math.sin(progress * math.tau * 4.0))
        self.shake_offset = recoil + wobble

    def _spawn_missile(self):
        direction = self._direction_from_angle(self.current_angle)
        muzzle = self._muzzle_position()
        return MissileProjectile(
            muzzle.x,
            muzzle.y,
            direction.x,
            direction.y,
            self.missile_image,
        )

    def update(self, dt, projectiles, player):
        if self.finished:
            return []

        self.timer += dt
        self._update_aim(player)
        self._update_shake(dt)

        spawned = []
        next_fire_time = self.first_fire_delay + self.shots_fired * self.fire_interval
        if self.shots_fired < self.total_shots and self.timer >= next_fire_time:
            spawned.append(self._spawn_missile())
            self.shots_fired += 1
            self.shake_timer = self.shake_duration
            self._update_shake(0.0)

        self.image = pygame.transform.rotate(self.base_image, -(self.current_angle - self.source_angle))
        center = self.origin + self.shake_offset
        self.rect = self.image.get_rect(center=(int(center.x), int(center.y)))

        if self.shots_fired >= self.total_shots and self.shake_timer <= 0.0:
            self.finished = True

        return spawned

    def draw(self, surface):
        if self.finished:
            return
        surface.blit(self.image, self.rect)
