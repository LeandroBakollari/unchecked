import pygame
import math
import random
from game.attacks.base import AttackBase


class SwordAttack(AttackBase):
    def __init__(self, pen_rect, player_rect, assets,
                 preview_duration=40,
                 x_attack_damage=10,
                 slash_damage=10,
                 random_slashes=3,
                 swing_duration=15,
                 preview_scale=1.2,
                 delay_between_slashes=25):
        super().__init__(pen_rect, player_rect, assets)
        self.slash_img = assets['slash_img']

        # configs
        self.preview_duration = preview_duration
        self.swing_duration = swing_duration
        self.random_slashes = random_slashes
        self.x_attack_damage = x_attack_damage
        self.slash_damage = slash_damage
        self.preview_scale = preview_scale
        self.delay_between_slashes = delay_between_slashes

        # target locked on spawn (used only for X attack)
        self.target = (player_rect.centerx, player_rect.centery)

        # state
        self.phase = 0
        self.timer = 0
        self.slash_index = 0
        self.current_angle = 0
        self.swing_progress = 0
        self.delay_timer = 0
        self.finished = False
        self.active_slashes = []

        # X attack angles
        self.x_angles = [-45, 45]

    def update(self, projectiles, player):
        if self.finished:
            return

        # === PHASE 0: Preview X ===
        if self.phase == 0:
            self.timer += 1
            if self.timer >= self.preview_duration:
                self.timer = 0
                self.phase = 1
                self.slash_index = 0

        # === PHASE 1: Perform X attack ===
        elif self.phase == 1:
            if self.slash_index < len(self.x_angles):
                self.swing_progress += 1
                if self.swing_progress >= self.swing_duration:
                    angle = self.x_angles[self.slash_index]
                    self.do_slash(player, angle, self.x_attack_damage, self.target)
                    self.slash_index += 1
                    self.swing_progress = 0
            else:
                self.phase = 2
                self.slash_index = 0
                self.timer = 0
                self.delay_timer = 0

        # === PHASE 2: Random slashes ===
        elif self.phase == 2:
            if self.slash_index >= self.random_slashes:
                self.finished = True
                return

            if self.delay_timer < self.delay_between_slashes:
                self.delay_timer += 1
                return

            if self.timer < (self.preview_duration // 2):
                if self.timer == 0:
                    self.current_angle = random.uniform(0, 360)
                    # new target is current player pos
                    self.target = (player.rect.centerx, player.rect.centery)
                self.timer += 1
            elif self.timer < (self.preview_duration // 2) + self.swing_duration:
                self.swing_progress += 1
                self.timer += 1
            else:
                self.do_slash(player, self.current_angle, self.slash_damage, self.target)
                self.slash_index += 1
                self.timer = 0
                self.swing_progress = 0
                self.delay_timer = 0

        # fade out old slashes
        for slash in self.active_slashes[:]:
            slash["life"] -= 1
            if slash["life"] <= 0:
                self.active_slashes.remove(slash)

        return []

    def do_slash(self, player, angle, damage, center):
        """Spawns a visual slash + deals damage if player intersects straight hitbox."""
        self.active_slashes.append({
            "angle": angle,
            "life": 10,
            "center": center
        })

        # straight hitbox line
        length = max(self.slash_img.get_width(), self.slash_img.get_height()) * 2
        thickness = 40  # visual width
        hitbox_len = length * 0.5  # smaller hitbox
        hitbox_thickness = 12

        # player center
        px, py = player.get_rect().center

        # find distance from player to slash line
        cx, cy = center
        rad = math.radians(angle)
        x1 = cx - math.cos(rad) * hitbox_len / 2
        y1 = cy + math.sin(rad) * hitbox_len / 2
        x2 = cx + math.cos(rad) * hitbox_len / 2
        y2 = cy - math.sin(rad) * hitbox_len / 2

        # distance formula from point to line segment
        dist = abs((y2 - y1)*px - (x2 - x1)*py + x2*y1 - y2*x1) / math.hypot(y2 - y1, x2 - x1)
        if dist <= hitbox_thickness and min(x1, x2) - 10 <= px <= max(x1, x2) + 10 and min(y1, y2) - 10 <= py <= max(y1, y2) + 10:
            player.take_damage(damage)

    def draw(self, surface):
        # === PHASE 0: Preview X lines ===
        if self.phase == 0:
            color = (255, 50, 50, 180)
            for a in self.x_angles:
                self.draw_line(surface, self.target, a, color)

        # === PHASE 1: Show X lines while swinging ===
        if self.phase == 1 and self.slash_index < len(self.x_angles):
            angle = self.x_angles[self.slash_index]
            self.draw_line(surface, self.target, angle, (255, 150, 150, 200))

        # === PHASE 2: Show preview line ===
        if self.phase == 2 and self.timer < (self.preview_duration // 2):
            self.draw_line(surface, self.target, self.current_angle, (255, 180, 0, 200))

        # === Draw active slashes ===
        for slash in self.active_slashes:
            self.draw_slash(surface, slash["center"], slash["angle"], slash["life"])

    def draw_line(self, surface, center, angle, color):
        length = max(self.slash_img.get_width(), self.slash_img.get_height()) * 2
        x1 = center[0] - math.cos(math.radians(angle)) * length / 2
        y1 = center[1] + math.sin(math.radians(angle)) * length / 2
        x2 = center[0] + math.cos(math.radians(angle)) * length / 2
        y2 = center[1] - math.sin(math.radians(angle)) * length / 2
        s = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        pygame.draw.line(s, color, (x1, y1), (x2, y2), 4)
        surface.blit(s, (0, 0))

    def draw_slash(self, surface, center, angle, life):
        slash_rot = pygame.transform.rotate(self.slash_img, angle)
        w = int(slash_rot.get_width() * 2.2)  # longer
        h = slash_rot.get_height()
        slash_rot = pygame.transform.scale(slash_rot, (w, h))
        alpha = max(0, min(255, int(255 * (life / 10))))
        slash_rot.set_alpha(alpha)
        rect = slash_rot.get_rect(center=center)
        surface.blit(slash_rot, rect)
