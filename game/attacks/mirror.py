import random
import pygame
from game.attacks.base import AttackBase


class MirrorAttack(AttackBase):
    """
    A mirror pen that spawns three attacks at half speed compared to the main pen.
    Uses a simple square as its visual placeholder.
    """

    def __init__(self, pen_rect, player_rect, assets, draw_delay=1.1):
        super().__init__(pen_rect, player_rect, assets)
        # The mirror is larger than the other props and never rotates.
        self.image = assets["mirror_img"]
        self.rect = self.image.get_rect(center=pen_rect.center)
        self.timer = 0.0
        self.draw_delay = draw_delay
        self.spawns_done = 0
        self.max_spawns = 3
        self.spawn_times = [self.draw_delay * i for i in range(1, self.max_spawns + 1)]
        self.attack_classes = assets.get("attack_classes", [])

    def update(self, dt, projectiles, player):
        """Spawn delayed mirrored attacks from the mirror's fixed position."""
        if self.finished:
            return []

        self.timer += dt
        spawned = []

        while self.spawns_done < self.max_spawns and self.timer >= self.spawn_times[self.spawns_done]:
            if not self.attack_classes:
                break
            cls = random.choice(self.attack_classes)
            try:
                attack = cls(self.rect, player.get_rect(), self.assets)
                spawned.append(attack)
            except Exception:
                pass
            self.spawns_done += 1

        if self.spawns_done >= self.max_spawns:
            # give a small buffer so visuals can show
            if self.timer >= self.spawn_times[-1] + 0.4:
                self.finished = True

        return spawned

    def draw(self, surface):
        """Draw the non-rotating mirror sprite at the original pen location."""
        surface.blit(self.image, self.rect)
