import pygame
import math
from game.attacks.base import AttackBase
from game.projectiles.bullet import BulletProjectile

class GunAttack(AttackBase):
    def __init__(self, pen_rect, player_rect, assets, shots=3, delay_frames=18):
        super().__init__(pen_rect, player_rect, assets)
        
        self.fire_delay = delay_frames
        self.fire_count = 0
        self.shots_fired = 0
        self.total_shots = shots

        self.gun_orig = assets['gun_img']
        self.bullet_img = assets['bullet_img']

        # Gun is drawn at the pen's location at spawn
        self.spawn_pos = self.pen_rect.center
        self.gun_img = self.gun_orig
        self.gun_rect = self.gun_img.get_rect(center=self.spawn_pos)

        # recoil
        self.recoil_offset = 0.0
        self.recoiling = False
        self.recoil_speed = 4.0
        self.recoil_max = 12.0

    def update(self, projectiles_list, player=None):
        if self.finished:
            return []

        # --- Calculate angle at spawn time ---
        dx = self.player_rect.centerx - self.spawn_pos[0]
        dy = self.player_rect.centery - self.spawn_pos[1]
        dist = math.hypot(dx, dy) or 1.0
        angle_deg = math.degrees(math.atan2(dy, dx))

        # --- Flip if on right side ---
        screen_width = pygame.display.get_surface().get_width()
        if self.spawn_pos[0] > screen_width / 2:
            base_img = pygame.transform.flip(self.gun_orig, False, True)
        else:
            base_img = self.gun_orig

        # Rotate to aim at player
        self.gun_img = pygame.transform.rotate(base_img, -angle_deg)
        self.gun_rect = self.gun_img.get_rect(center=self.spawn_pos)

        # --- recoil ---
        if self.recoiling:
            self.recoil_offset += self.recoil_speed
            if self.recoil_offset >= self.recoil_max:
                self.recoil_speed = -abs(self.recoil_speed)
            if self.recoil_offset <= 0:
                self.recoil_offset = 0.0
                self.recoil_speed = abs(self.recoil_speed)
                self.recoiling = False

        recoil_x = - (dx / dist) * self.recoil_offset
        recoil_y = - (dy / dist) * self.recoil_offset
        self.gun_rect.centerx += int(recoil_x)
        self.gun_rect.centery += int(recoil_y)

        # --- fire logic ---
        self.fire_count += 1
        spawned = []

        if self.fire_count >= self.fire_delay:
            self.fire_count = 0

            # spawn bullet aimed at player location at firing
            bullet = BulletProjectile(
                self.spawn_pos[0],
                self.spawn_pos[1],
                dx / dist,
                dy / dist,
                self.bullet_img
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
