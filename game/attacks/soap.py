import pygame

from game import utils
from game.attacks.base import AttackBase


class SoapAttack(AttackBase):
    """A thrown hand-soap hazard that slides, bounces, stops briefly, then melts away."""

    def __init__(
        self,
        pen_rect,
        player_rect,
        assets,
        damage=12,
        aim_duration=3.0,
        initial_speed=620.0,
        min_slide_speed=95.0,
        total_slide_distance=1600.0,
        max_bounces=2,
        bounce_speed_retention=0.86,
        edge_padding=34.0,
        stopped_duration=5.0,
        melt_duration=0.65,
        melt_curve=1.7,
        hitbox_scale=0.72,
    ):
        super().__init__(pen_rect, player_rect, assets)

        # Main gameplay tuning:
        # damage: health removed once when the soap hits the player, then the soap disappears.
        # aim_duration: hidden pre-launch lock-on time before the soap starts sliding.
        # initial_speed: first-frame launch speed in pixels per second.
        # min_slide_speed: when deceleration reaches this speed, the soap stops even if distance remains.
        # total_slide_distance: travel budget before stopping; raise this for longer sliding paths.
        # max_bounces: how many wall bounces are allowed before the soap stops on the next wall touch.
        # bounce_speed_retention: speed multiplier after each bounce; lower values make bounces die sooner.
        # edge_padding: inset from screen edges used as the bounce boundary.
        # stopped_duration: how long the soap sits still after sliding before it melts.
        # melt_duration: time spent shrinking away; lower values make the melt faster.
        # melt_curve: higher values shrink slowly at first and faster near the end.
        # hitbox_scale: collision size relative to the visible rotated soap sprite.
        self.damage = damage
        self.aim_duration = max(0.0, float(aim_duration))
        self.initial_speed = max(1.0, float(initial_speed))
        self.min_slide_speed = max(0.0, float(min_slide_speed))
        self.total_slide_distance = max(1.0, float(total_slide_distance))
        self.max_bounces = max(0, int(max_bounces))
        self.bounce_speed_retention = max(0.05, min(1.0, float(bounce_speed_retention)))
        self.edge_padding = max(0.0, float(edge_padding))
        self.stopped_duration = max(0.0, float(stopped_duration))
        self.melt_duration = max(0.05, float(melt_duration))
        self.melt_curve = max(0.2, float(melt_curve))
        self.hitbox_scale = max(0.1, min(1.0, float(hitbox_scale)))

        # The launch direction is locked to the player's position at spawn.
        self.origin = pygame.Vector2(pen_rect.center)
        self.aim_target = pygame.Vector2(player_rect.center)
        self.direction = self.aim_target - self.origin
        if self.direction.length_squared() <= 1e-6:
            self.direction = pygame.Vector2(0, 1)
        else:
            self.direction = self.direction.normalize()

        self.soap_img_raw = assets.get("soap_img") or self._make_fallback_soap()
        self.angle = utils.angle_from_vector(self.direction.x, self.direction.y)

        self.timer = 0.0
        self.position = pygame.Vector2(self.origin)
        self.entered_player_area = False
        self.current_speed = 0.0
        self.speed_multiplier = 1.0
        self.distance_traveled = 0.0
        self.bounces_used = 0
        self.state = "aiming"
        self.stopped_timer = 0.0
        self.melt_timer = 0.0

        self.soap_img = self.soap_img_raw
        self.rect = self.soap_img_raw.get_rect(center=(int(self.position.x), int(self.position.y)))
        self._refresh_sprite()

    def _make_fallback_soap(self):
        """Temporary soap art used until game/assets/images/soap.png is added."""
        surface = pygame.Surface((40, 48), pygame.SRCALPHA)
        body = pygame.Rect(7, 5, 26, 36)
        pygame.draw.rect(surface, (120, 210, 238, 235), body, border_radius=14)
        pygame.draw.rect(surface, (32, 92, 126, 230), body, width=3, border_radius=14)
        pygame.draw.arc(surface, (245, 252, 255, 190), pygame.Rect(12, 12, 16, 10), 3.3, 5.8, 2)
        pygame.draw.polygon(surface, (32, 92, 126, 190), [(20, 46), (15, 39), (25, 39)])
        return surface

    def _movement_bounds(self):
        surface = pygame.display.get_surface()
        if surface:
            _, _, player_area, _ = utils.recalc_geometry(surface)
            bounds = player_area.inflate(-int(self.edge_padding * 2), -int(self.edge_padding * 2))
            if bounds.width > 1 and bounds.height > 1:
                return bounds
        return pygame.Rect(0, 0, max(1, int(self.origin.x + 1000)), max(1, int(self.origin.y + 1000)))

    def _sprite_rotation(self):
        # The soap source image points downward, so angle 90 degrees needs no rotation.
        return -(self.angle - 90.0)

    def _current_scale(self):
        if self.state != "melting":
            return 1.0

        melt_progress = utils.clamp(self.melt_timer / self.melt_duration, 0.0, 1.0)
        return max(0.0, (1.0 - melt_progress) ** self.melt_curve)

    def _refresh_sprite(self):
        scale = self._current_scale()
        width = max(1, int(self.soap_img_raw.get_width() * scale))
        height = max(1, int(self.soap_img_raw.get_height() * scale))
        scaled = pygame.transform.smoothscale(self.soap_img_raw, (width, height))
        self.soap_img = pygame.transform.rotate(scaled, self._sprite_rotation())
        self.rect = self.soap_img.get_rect(center=(int(self.position.x), int(self.position.y)))

    def _hitbox(self):
        shrink_x = int(self.rect.width * (1.0 - self.hitbox_scale))
        shrink_y = int(self.rect.height * (1.0 - self.hitbox_scale))
        return self.rect.inflate(-shrink_x, -shrink_y)

    def _start_stopped(self):
        self.state = "stopped"
        self.current_speed = 0.0
        self.stopped_timer = 0.0

    def _start_melting(self):
        self.state = "melting"
        self.current_speed = 0.0
        self.melt_timer = 0.0

    def _begin_sliding(self):
        self.state = "sliding"
        self.current_speed = self.initial_speed

    def _update_sliding(self, dt):
        progress = utils.clamp(self.distance_traveled / self.total_slide_distance, 0.0, 1.0)
        self.current_speed = utils.lerp(self.initial_speed, self.min_slide_speed, progress) * self.speed_multiplier
        move_distance = self.current_speed * dt
        next_position = self.position + self.direction * move_distance
        bounds = self._movement_bounds()
        left = bounds.left
        right = bounds.right - 1
        top = bounds.top
        bottom = bounds.bottom - 1

        if not self.entered_player_area:
            if bounds.collidepoint(next_position.x, next_position.y):
                self.entered_player_area = True
            else:
                self.position = next_position
                self.distance_traveled += move_distance
                return

        bounced = False
        if next_position.x < left or next_position.x > right:
            if self.bounces_used >= self.max_bounces:
                next_position.x = utils.clamp(next_position.x, left, right)
                self.position = next_position
                self._start_stopped()
                return
            next_position.x = utils.clamp(next_position.x, left, right)
            self.direction.x *= -1
            bounced = True

        if next_position.y < top or next_position.y > bottom:
            if self.bounces_used >= self.max_bounces:
                next_position.y = utils.clamp(next_position.y, top, bottom)
                self.position = next_position
                self._start_stopped()
                return
            next_position.y = utils.clamp(next_position.y, top, bottom)
            self.direction.y *= -1
            bounced = True

        if bounced:
            self.bounces_used += 1
            self.speed_multiplier *= self.bounce_speed_retention
            self.current_speed *= self.bounce_speed_retention
            self.angle = utils.angle_from_vector(self.direction.x, self.direction.y)

        self.position = next_position
        self.distance_traveled += move_distance

        if self.distance_traveled >= self.total_slide_distance or self.current_speed <= self.min_slide_speed:
            self._start_stopped()

    def _update_damage(self, player):
        if self.state not in ("sliding", "stopped"):
            return

        if self._hitbox().colliderect(player.get_hitbox()):
            player.take_damage(self.damage)
            self.finished = True

    def update(self, dt, projectiles, player):
        if self.finished:
            return []

        self.timer += dt

        if self.state == "aiming" and self.timer >= self.aim_duration:
            self._begin_sliding()

        if self.state == "sliding":
            self._update_sliding(dt)
        elif self.state == "stopped":
            self.stopped_timer += dt
            if self.stopped_timer >= self.stopped_duration:
                self._start_melting()
        elif self.state == "melting":
            self.melt_timer += dt
            if self.melt_timer >= self.melt_duration:
                self.finished = True

        self._refresh_sprite()
        self._update_damage(player)
        return []

    def get_debug_hitboxes(self):
        if self.finished or self.state == "aiming":
            return []

        return [
            {
                "type": "rect",
                "rect": self._hitbox(),
                "label": "soap",
            }
        ]

    def draw(self, surface):
        if self.finished:
            return

        surface.blit(self.soap_img, self.rect)
