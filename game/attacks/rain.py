import random
import pygame

from game.attacks.base import AttackBase


class RainAttack(AttackBase):
    """A stationary cloud that drops vertical raindrops over an exact timed window."""

    def __init__(
        self,
        pen_rect,
        player_rect,
        assets,
        damage=8,
        drop_count=6,
        last_drop_time=8.0,
        drop_speed=430.0,
        drop_spawn_padding=14,
        drop_hitbox_scale=0.65,
        cleanup_padding=80,
    ):
        super().__init__(pen_rect, player_rect, assets)

        # Main gameplay tuning:
        # damage: health removed by one raindrop hit.
        # drop_count: total number of raindrops this cloud creates.
        # last_drop_time: the final drop is scheduled at exactly this many seconds after spawn.
        # drop_speed: vertical falling speed in pixels per second.
        # drop_spawn_padding: horizontal inset from cloud edges used for random spawn positions.
        # drop_hitbox_scale: collision size relative to the raindrop sprite.
        # cleanup_padding: extra distance below the screen before missed drops are removed.
        self.damage = damage
        self.drop_count = max(1, int(drop_count))
        self.last_drop_time = max(0.0, float(last_drop_time))
        self.drop_speed = float(drop_speed)
        self.drop_spawn_padding = max(0, int(drop_spawn_padding))
        self.drop_hitbox_scale = max(0.1, min(1.0, float(drop_hitbox_scale)))
        self.cleanup_padding = max(0, int(cleanup_padding))

        # The cloud is locked to the pen's draw position for the full attack.
        self.origin = pygame.Vector2(pen_rect.center)
        self.cloud_img = assets.get("cloud_img") or self._make_fallback_cloud()
        self.raindrop_img = assets.get("raindrop_img") or self._make_fallback_raindrop()
        self.cloud_rect = self.cloud_img.get_rect(center=(int(self.origin.x), int(self.origin.y)))

        # Randomize all drops up front so the pattern is stable for this attack instance.
        # The last drop is always exactly at last_drop_time; earlier drops are random within the window.
        early_times = [random.uniform(0.0, self.last_drop_time) for _ in range(self.drop_count - 1)]
        self.drop_schedule = sorted(early_times) + [self.last_drop_time]
        self.scheduled_x_positions = [self._random_drop_x() for _ in range(self.drop_count)]

        self.timer = 0.0
        self.schedule_epsilon = 1e-6
        self.next_drop_index = 0
        self.active_drops = []

    def _make_fallback_cloud(self):
        """Temporary cloud art used until game/assets/images/cloud.png is added."""
        surface = pygame.Surface((180, 88), pygame.SRCALPHA)
        color = (235, 235, 235, 230)
        outline = (70, 70, 70, 180)
        circles = [(50, 48, 34), (85, 36, 42), (126, 50, 32), (92, 56, 46)]
        for x, y, radius in circles:
            pygame.draw.circle(surface, color, (x, y), radius)
            pygame.draw.circle(surface, outline, (x, y), radius, 2)
        pygame.draw.ellipse(surface, color, (28, 42, 126, 34))
        pygame.draw.ellipse(surface, outline, (28, 42, 126, 34), 2)
        return surface

    def _make_fallback_raindrop(self):
        """Temporary raindrop art used until game/assets/images/raindrop.png is added."""
        surface = pygame.Surface((24, 38), pygame.SRCALPHA)
        points = [(12, 2), (22, 22), (12, 36), (2, 22)]
        pygame.draw.polygon(surface, (75, 150, 235, 235), points)
        pygame.draw.polygon(surface, (30, 75, 145, 210), points, 2)
        return surface

    def _random_drop_x(self):
        left = self.cloud_rect.left + self.drop_spawn_padding
        right = self.cloud_rect.right - self.drop_spawn_padding
        if right <= left:
            return self.cloud_rect.centerx
        return random.uniform(left, right)

    def _get_screen_rect(self):
        surface = pygame.display.get_surface()
        if surface:
            return surface.get_rect()
        return pygame.Rect(0, 0, max(1, self.cloud_rect.right), max(1, self.cloud_rect.bottom + 600))

    def _spawn_drop(self, index, elapsed_since_spawn):
        x = self.scheduled_x_positions[index]
        y = self.cloud_rect.bottom + self.drop_speed * elapsed_since_spawn
        rect = self.raindrop_img.get_rect(center=(int(x), int(y)))
        self.active_drops.append(
            {
                "x": float(x),
                "y": float(y),
                "rect": rect,
            }
        )

    def _drop_hitbox(self, drop):
        rect = drop["rect"]
        shrink_x = int(rect.width * (1.0 - self.drop_hitbox_scale))
        shrink_y = int(rect.height * (1.0 - self.drop_hitbox_scale))
        return rect.inflate(-shrink_x, -shrink_y)

    def update(self, dt, projectiles, player):
        if self.finished:
            return []

        self.timer += dt
        screen_rect = self._get_screen_rect()

        for drop in self.active_drops[:]:
            drop["y"] += self.drop_speed * dt
            drop["rect"].center = (int(drop["x"]), int(drop["y"]))

            if self._drop_hitbox(drop).colliderect(player.get_hitbox()):
                player.take_damage(self.damage)
                self.active_drops.remove(drop)
                continue

            if drop["rect"].top > screen_rect.bottom + self.cleanup_padding:
                self.active_drops.remove(drop)

        while (
            self.next_drop_index < self.drop_count
            and self.drop_schedule[self.next_drop_index] <= self.timer + self.schedule_epsilon
        ):
            drop_time = self.drop_schedule[self.next_drop_index]
            self._spawn_drop(self.next_drop_index, self.timer - drop_time)
            self.next_drop_index += 1

        if self.next_drop_index >= self.drop_count and not self.active_drops:
            self.finished = True

        return []

    def get_debug_hitboxes(self):
        if self.finished:
            return []

        return [
            {
                "type": "rect",
                "rect": self._drop_hitbox(drop),
                "label": "rain",
            }
            for drop in self.active_drops
        ]

    def draw(self, surface):
        if self.finished:
            return

        surface.blit(self.cloud_img, self.cloud_rect)
        for drop in self.active_drops:
            surface.blit(self.raindrop_img, drop["rect"])
