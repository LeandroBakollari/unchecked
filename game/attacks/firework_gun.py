import math

import pygame

from game import utils
from game.attacks.base import AttackBase
from game.projectiles.firework import FireworkProjectile


class FireworkGunAttack(AttackBase):
    """A delayed firework gun that launches three rockets and curves the outer two away."""

    def __init__(self, pen_rect, player_rect, assets):
        super().__init__(pen_rect, player_rect, assets)

        self.origin = pygame.Vector2(pen_rect.center)
        self.gun_base = assets.get("fireworkgun_img") or self._build_gun_fallback()
        self.firework_img = assets.get("firework_img") or self._build_firework_fallback()

        self.image = self.gun_base
        self.rect = self.image.get_rect(center=self.origin)
        self.source_angle = 180.0
        self.current_angle = self._angle_to(player_rect.center)
        self.fire_angle = self.current_angle

        self.fire_delay = 3.0
        self.linger_duration = 0.55
        self.timer = 0.0
        self.fired = False

        self.side_start_angle = 8.0
        self.side_final_angle = 90.0
        self.muzzle_distance = max(self.gun_base.get_width() * 0.44, 34)

        self.recoil_timer = 0.0
        self.recoil_duration = 0.22
        self.recoil_distance = 18.0
        self.recoil_offset = pygame.Vector2(0, 0)

    def _build_gun_fallback(self):
        surface = pygame.Surface((124, 76), pygame.SRCALPHA)
        pygame.draw.rect(surface, (252, 252, 248), (12, 17, 76, 24), border_radius=8)
        pygame.draw.rect(surface, (35, 34, 30), (12, 17, 76, 24), width=3, border_radius=8)
        pygame.draw.circle(surface, (35, 34, 30), (16, 29), 11, width=3)
        pygame.draw.rect(surface, (252, 252, 248), (68, 37, 24, 16), border_radius=4)
        pygame.draw.rect(surface, (35, 34, 30), (68, 37, 24, 16), width=3, border_radius=4)
        pygame.draw.polygon(surface, (252, 252, 248), [(92, 34), (112, 68), (92, 72), (80, 42)])
        pygame.draw.polygon(surface, (35, 34, 30), [(92, 34), (112, 68), (92, 72), (80, 42)], width=3)
        pygame.draw.arc(surface, (35, 34, 30), (70, 39, 28, 24), math.radians(0), math.radians(180), 3)
        return surface

    def _build_firework_fallback(self):
        surface = pygame.Surface((28, 72), pygame.SRCALPHA)
        pygame.draw.polygon(surface, (200, 44, 44), [(14, 3), (5, 20), (23, 20)])
        pygame.draw.rect(surface, (245, 220, 78), (7, 19, 14, 25), border_radius=4)
        pygame.draw.rect(surface, (35, 34, 30), (7, 19, 14, 25), width=2, border_radius=4)
        pygame.draw.line(surface, (35, 34, 30), (14, 44), (14, 69), 2)
        return surface

    def _direction_from_angle(self, angle_deg):
        radians = math.radians(angle_deg)
        return pygame.Vector2(math.cos(radians), math.sin(radians))

    def _angle_to(self, target):
        dx, dy, dist = utils.vector_to(self.origin, target)
        if dist <= 1e-6:
            return 180.0
        return utils.angle_from_vector(dx, dy)

    def _muzzle_position(self):
        return self.origin + self._direction_from_angle(self.fire_angle) * self.muzzle_distance

    def _update_aim(self, player):
        if self.fired:
            self.current_angle = self.fire_angle
            return
        target = player.get_rect().center if player else self.player_rect.center
        self.current_angle = self._angle_to(target)

    def _base_gun_image(self):
        surface = pygame.display.get_surface()
        screen_width = surface.get_width() if surface else 0
        if screen_width and self.origin.x < screen_width / 2:
            return pygame.transform.flip(self.gun_base, False, True)
        return self.gun_base

    def _update_recoil(self, dt):
        if self.recoil_timer <= 0.0:
            self.recoil_offset.update(0, 0)
            return

        self.recoil_timer = max(0.0, self.recoil_timer - dt)
        progress = 1.0 - (self.recoil_timer / self.recoil_duration)
        amount = math.sin(progress * math.pi) * self.recoil_distance
        self.recoil_offset = -self._direction_from_angle(self.fire_angle) * amount

    def _update_image(self):
        angle = self.fire_angle if self.fired else self.current_angle
        base_image = self._base_gun_image()
        self.image = pygame.transform.rotate(base_image, -(angle - self.source_angle))
        center = self.origin + self.recoil_offset
        self.rect = self.image.get_rect(center=(int(center.x), int(center.y)))

    def _spawn_fireworks(self):
        self.fire_angle = self.current_angle
        muzzle = self._muzzle_position()

        return [
            FireworkProjectile(muzzle.x, muzzle.y, self.fire_angle, self.firework_img, target_angle=None),
            FireworkProjectile(
                muzzle.x,
                muzzle.y,
                self.fire_angle - self.side_start_angle,
                self.firework_img,
                target_angle=self.fire_angle - self.side_final_angle,
            ),
            FireworkProjectile(
                muzzle.x,
                muzzle.y,
                self.fire_angle + self.side_start_angle,
                self.firework_img,
                target_angle=self.fire_angle + self.side_final_angle,
            ),
        ]

    def get_debug_hitboxes(self):
        if self.finished:
            return []
        return [{"type": "rect", "rect": self.rect, "label": "firework gun"}]

    def update(self, dt, projectiles, player):
        if self.finished:
            return []

        self.timer += dt
        self._update_aim(player)
        self._update_recoil(dt)

        spawned = []
        if not self.fired and self.timer >= self.fire_delay:
            spawned = self._spawn_fireworks()
            self.fired = True
            self.recoil_timer = self.recoil_duration
            self._update_recoil(0.0)

        self._update_image()

        if self.fired and self.timer >= self.fire_delay + self.linger_duration:
            self.finished = True

        return spawned

    def draw(self, surface):
        if self.finished:
            return
        surface.blit(self.image, self.rect)
