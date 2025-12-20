import pygame
from game import utils
from game.attacks.base import AttackBase
from game.projectiles.bullet import BulletProjectile


class GunAttack(AttackBase):
    def __init__(self, pen_rect, player_rect, assets, shots=3, delay_seconds=0.35):
        super().__init__(pen_rect, player_rect, assets)

        self.fire_delay = delay_seconds
        self.cooldown = 0.0
        self.shots_fired = 0
        self.total_shots = shots

        self.gun_orig = assets["gun_img"]
        self.bullet_img = assets["bullet_img"]

        self.spawn_pos = self.pen_rect.center
        self.gun_img = self.gun_orig
        self.gun_rect = self.gun_img.get_rect(center=self.spawn_pos)

        self.recoil_offset = 0.0
        self.recoiling = False
        self.recoil_speed = 60.0  # px/s
        self.recoil_max = 18.0

    def update(self, dt, projectiles_list, player=None):
        if self.finished:
            return []

        target_center = player.get_rect().center if player else self.player_rect.center
        dx, dy, dist = utils.vector_to(self.spawn_pos, target_center)
        dist = dist or 1.0
        angle_deg = utils.angle_from_vector(dx, dy)

        screen_width = pygame.display.get_surface().get_width()
        base_img = pygame.transform.flip(self.gun_orig, False, True) if self.spawn_pos[0] > screen_width / 2 else self.gun_orig

        self.gun_img = pygame.transform.rotate(base_img, -angle_deg)
        self.gun_rect = self.gun_img.get_rect(center=self.spawn_pos)

        if self.recoiling:
            self.recoil_offset += self.recoil_speed * dt
            if self.recoil_offset >= self.recoil_max:
                self.recoil_speed = -abs(self.recoil_speed)
            if self.recoil_offset <= 0:
                self.recoil_offset = 0.0
                self.recoil_speed = abs(self.recoil_speed)
                self.recoiling = False

        recoil_x = -(dx / dist) * self.recoil_offset
        recoil_y = -(dy / dist) * self.recoil_offset
        self.gun_rect.centerx += int(recoil_x)
        self.gun_rect.centery += int(recoil_y)

        spawned = []
        self.cooldown += dt
        if self.cooldown >= self.fire_delay:
            self.cooldown -= self.fire_delay
            ndx, ndy, _ = utils.normalized(dx, dy)
            bullet = BulletProjectile(
                self.spawn_pos[0],
                self.spawn_pos[1],
                ndx,
                ndy,
                self.bullet_img,
            )
            spawned.append(bullet)

            self.shots_fired += 1
            self.recoiling = True
            self.recoil_offset = 0.0
            self.recoil_speed = abs(self.recoil_speed)

            if self.shots_fired >= self.total_shots:
                self.finished = True

        return spawned

    def draw(self, surface):
        surface.blit(self.gun_img, self.gun_rect)
