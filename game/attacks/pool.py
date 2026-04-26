import math

import pygame

from game import utils
from game.attacks.base import AttackBase


class PoolAttack(AttackBase):
    """A pool cue lines up a shot, strikes a spinning ball, and lets it bounce three times."""

    def __init__(self, pen_rect, player_rect, assets, damage=12):
        super().__init__(pen_rect, player_rect, assets)

        self.origin = pygame.Vector2(pen_rect.center)
        self.ball_position = pygame.Vector2(pen_rect.center)
        self.aim_target = pygame.Vector2(player_rect.center)

        self.ball_img_raw = assets["pool_ball_img"]
        self.ball_img = self.ball_img_raw
        self.ball_rect = self.ball_img.get_rect(center=self.ball_position)
        self.ball_radius = max(8, self.ball_img_raw.get_width() * 0.42)

        self.cue_img_raw = assets["pool_cue_img"]
        self.cue_img_raw = pygame.transform.scale(
            self.cue_img_raw,
            (int(self.cue_img_raw.get_width() * 1.18), self.cue_img_raw.get_height()),
        )
        self.cue_img = self.cue_img_raw
        self.cue_rect = self.cue_img.get_rect(center=self.origin)
        self.cue_source_angle = -45.0
        self.cue_tip_distance = max(self.cue_img_raw.get_width(), self.cue_img_raw.get_height()) * 0.54

        self.damage = damage

        self.aim_duration = 1.7
        self.pullback_duration = 0.45
        self.strike_duration = 0.16
        self.cue_linger_duration = 0.25
        self.timer = 0.0
        self.post_launch_timer = 0.0

        self.current_angle = self._angle_to_player(player_rect)
        self.fire_angle = self.current_angle
        self.aim_locked = False
        self.launched = False

        self.ball_speed = 520.0
        self.velocity = pygame.Vector2(0, 0)
        self.spin_angle = 0.0

        self.max_bounces = 3
        self.bounce_count = 0
        self.entered_table = False

    def _direction_from_angle(self, angle_deg):
        radians = math.radians(angle_deg)
        return pygame.Vector2(math.cos(radians), math.sin(radians))

    def _angle_to_player(self, player_rect):
        dx, dy, dist = utils.vector_to(self.origin, player_rect.center)
        if dist <= 1e-6:
            return 90.0
        return utils.angle_from_vector(dx, dy)

    def _table_rect(self):
        surface = pygame.display.get_surface()
        _, _, area_rect, _ = utils.recalc_geometry(surface)
        return area_rect

    def _cue_gap(self):
        pullback_start = self.aim_duration
        strike_start = pullback_start + self.pullback_duration
        launch_time = strike_start + self.strike_duration

        if self.timer < pullback_start:
            return 34.0
        if self.timer < strike_start:
            progress = (self.timer - pullback_start) / self.pullback_duration
            return utils.lerp(34.0, 88.0, progress)
        if self.timer < launch_time:
            progress = (self.timer - strike_start) / self.strike_duration
            return utils.lerp(88.0, 18.0, progress)
        return 18.0

    def _cue_center(self):
        direction = self._direction_from_angle(self.fire_angle if self.aim_locked else self.current_angle)
        return self.origin - direction * (self.cue_tip_distance + self._cue_gap())

    def _lock_aim(self):
        self.aim_locked = True
        self.fire_angle = self.current_angle

    def _launch_ball(self):
        self.launched = True
        self.velocity = self._direction_from_angle(self.fire_angle) * self.ball_speed

    def _update_aim(self, player):
        self.aim_target = pygame.Vector2(player.get_rect().center)
        dx, dy, dist = utils.vector_to(self.origin, self.aim_target)
        if dist > 1e-6:
            self.current_angle = utils.angle_from_vector(dx, dy)

    def _update_ball_spin(self, distance):
        circumference = max(1.0, 2.0 * math.pi * self.ball_radius)
        self.spin_angle = (self.spin_angle + (distance / circumference) * 360.0 * 1.45) % 360.0

    def _bounce_against_table(self):
        if self.bounce_count >= self.max_bounces:
            return

        table = self._table_rect()
        radius = self.ball_radius
        bounced = False

        if self.ball_position.x - radius <= table.left and self.velocity.x < 0:
            self.ball_position.x = table.left + radius
            self.velocity.x *= -1
            bounced = True
        elif self.ball_position.x + radius >= table.right and self.velocity.x > 0:
            self.ball_position.x = table.right - radius
            self.velocity.x *= -1
            bounced = True

        if self.ball_position.y - radius <= table.top and self.velocity.y < 0:
            self.ball_position.y = table.top + radius
            self.velocity.y *= -1
            bounced = True
        elif self.ball_position.y + radius >= table.bottom and self.velocity.y > 0:
            self.ball_position.y = table.bottom - radius
            self.velocity.y *= -1
            bounced = True

        if bounced:
            self.bounce_count += 1

    def _update_ball_damage(self, player):
        if self.get_hitbox().colliderect(player.get_hitbox()):
            player.take_damage(self.damage)
            self.finished = True

    def get_hitbox(self):
        rect = pygame.Rect(0, 0, int(self.ball_radius * 1.55), int(self.ball_radius * 1.55))
        rect.center = (int(self.ball_position.x), int(self.ball_position.y))
        return rect

    def get_debug_hitboxes(self):
        if self.finished:
            return []

        return [
            {
                "type": "circle",
                "center": self.ball_position,
                "radius": self.ball_radius,
                "label": f"pool ball {self.bounce_count}/{self.max_bounces}",
            }
        ]

    def update(self, dt, projectiles, player):
        if self.finished:
            return []

        self.timer += dt
        launch_time = self.aim_duration + self.pullback_duration + self.strike_duration

        if not self.launched:
            if self.timer < self.aim_duration:
                self._update_aim(player)
            elif not self.aim_locked:
                self._lock_aim()

            if self.timer >= launch_time:
                self._launch_ball()
            return []

        self.post_launch_timer += dt
        old_position = self.ball_position.copy()
        self.ball_position += self.velocity * dt
        self._update_ball_spin(self.ball_position.distance_to(old_position))

        table = self._table_rect()
        if not self.entered_table and table.collidepoint(self.ball_position):
            self.entered_table = True
        if self.entered_table:
            self._bounce_against_table()

        self.ball_img = pygame.transform.rotate(self.ball_img_raw, -self.spin_angle)
        self.ball_rect = self.ball_img.get_rect(center=(int(self.ball_position.x), int(self.ball_position.y)))
        self._update_ball_damage(player)

        screen_rect = pygame.display.get_surface().get_rect().inflate(180, 180)
        if not screen_rect.collidepoint(self.ball_position):
            self.finished = True

        return []

    def _draw_cue(self, surface):
        if self.launched and self.post_launch_timer > self.cue_linger_duration:
            return

        angle = self.fire_angle if self.aim_locked else self.current_angle
        cue_center = self._cue_center()
        self.cue_img = pygame.transform.rotate(self.cue_img_raw, self.cue_source_angle - angle)
        self.cue_rect = self.cue_img.get_rect(center=(int(cue_center.x), int(cue_center.y)))
        surface.blit(self.cue_img, self.cue_rect)

    def _draw_ball(self, surface):
        if not self.launched:
            self.ball_rect = self.ball_img_raw.get_rect(center=(int(self.origin.x), int(self.origin.y)))
            surface.blit(self.ball_img_raw, self.ball_rect)
            return
        surface.blit(self.ball_img, self.ball_rect)

    def draw(self, surface):
        if self.finished:
            return

        self._draw_cue(surface)
        self._draw_ball(surface)
