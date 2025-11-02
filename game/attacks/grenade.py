import pygame
import math
import random
from game.attacks.base import AttackBase


class GrenadeAttack(AttackBase):
    """Grenade attack behavior:
    - grenade spawns at pen position and flies toward player's current center
    - while flying, a pulsing red circle shows the future explosion radius
    - grenade rotates while moving
    - upon landing, short fuse then explosion occurs (damage in radius)
    """
    def __init__(self, pen_rect, player_rect, assets, speed=8, explosion_radius=120, fuse_after_land=5):
        super().__init__(pen_rect, player_rect, assets)
        self.grenade_img = assets['grenade_img']
        self.scale = 1.3
        w, h = self.grenade_img.get_width(), self.grenade_img.get_height()
        self.grenade_img = pygame.transform.scale(self.grenade_img, (int(w*self.scale), int(h*self.scale)))
        self.explosion_img = assets.get('explosion_img')
        self.spawn_x, self.spawn_y = self.pen_rect.center
        # target chosen at player's CURRENT location at spawn time
        self.target = player_rect.center
        self.x, self.y = pen_rect.center
        self.speed = speed
        dx = self.target[0] - self.x
        dy = self.target[1] - self.y
        dist = math.hypot(dx, dy) or 1.0
        self.vel_x = (dx / dist) * speed
        self.vel_y = (dy / dist) * speed
        self.angle = 0.0
        self.rotation_speed = random.uniform(8.0, 18.0)
        self.rect = self.grenade_img.get_rect(center=(int(self.x), int(self.y)))
        self.landed = False
        self.land_timer = 0
        self.fuse_after_land = fuse_after_land
        self.explosion_radius = explosion_radius
        self.damage = 20
        # pulsing preview parameters
        self.preview_alpha = 90
        self.preview_pulse_dir = 1
        self.preview_scale = 1.0
        self.explosion_show_time = 0
        self.explosion_duration = 15  # frames (≈0.25s at 60fps)


    def update(self, projectiles, player):
        if self.finished:
            return
        if not self.landed:
        # move grenade
            self.x += self.vel_x
            self.y += self.vel_y
            self.angle = (self.angle + self.rotation_speed) % 360
            self.rect.center = (int(self.x), int(self.y))
            # check landing threshold (close enough)
            if math.hypot(self.x - self.target[0], self.y - self.target[1]) < max(6, self.speed):
                self.landed = True
                self.land_timer = self.fuse_after_land
        else:
            # on ground: countdown fuse
            # if we are in explosion display phase
            if self.explosion_show_time > 0:
                self.explosion_show_time -= 1
                if self.explosion_show_time <= 0:
                    self.finished = True   # remove grenade after smoke fades
                return  # stop physics/drawing grenade itself during effect
            if self.land_timer > 0:
                self.land_timer -= 1
            else:
            # explode
                self.explode(player)
                self.explosion_show_time = self.explosion_duration


        # update preview pulsing while in flight
        self.preview_alpha += self.preview_pulse_dir * 6
        if self.preview_alpha >= 200:
            self.preview_pulse_dir = -1
        if self.preview_alpha <= 30:
            self.preview_pulse_dir = 1
        return []



    def explode(self, player):
        # if player center inside radius, damage
        dx = player.get_rect().centerx - self.target[0]
        dy = player.get_rect().centery - self.target[1]
        if math.hypot(dx, dy) <= self.explosion_radius:
            player.take_damage(self.damage)


    def draw(self, surface):
        # draw preview (pulsing circle) at target while grenade is flying
        if not self.landed:
            radius = int(self.explosion_radius * (0.9 + 0.15 * math.sin(pygame.time.get_ticks() / 200)))
            s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            alpha = max(20, min(220, int(self.preview_alpha)))
            pygame.draw.circle(s, (200, 0, 0, alpha), (radius, radius), radius)
            # subtle X in center
            #font = pygame.font.Font(None, 36)
            #x_surf = font.render('X', True, (255, 255, 255))
            surface.blit(s, (self.target[0] - radius, self.target[1] - radius))
            #surface.blit(x_surf, (self.target[0] - x_surf.get_width()//2, self.target[1] - x_surf.get_height()//2))


        # draw grenade (rotating)
        rotated = pygame.transform.rotate(self.grenade_img, self.angle)
        rect = rotated.get_rect(center=self.rect.center)
        surface.blit(rotated, rect)


        # optional explosion sprite on landing (brief flash)
        if self.landed and self.land_timer <= 0 and self.explosion_show_time > 0:
            if self.explosion_img:
                ex = pygame.transform.scale(self.explosion_img, (int(self.explosion_radius*2) + 100, int(self.explosion_radius*2) +100))
                rect = ex.get_rect(center=self.target)
                surface.blit(ex, rect)