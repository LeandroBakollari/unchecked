import math
import pygame

from game import utils
from game.attacks.base import AttackBase


class BoomerangAttack(AttackBase):
    """A two-pass boomerang that launches, dives off-screen, then returns for one final upward pass."""

    def __init__(self, pen_rect, player_rect, assets, damage=10):
        super().__init__(pen_rect, player_rect, assets)

        # The boomerang starts exactly where the pen finished drawing it.
        self.position = pygame.Vector2(pen_rect.center)

        # Use the boomerang sprite from the asset pack, but keep a procedural fallback so the attack remains robust.
        self.base_image = assets.get("boomerang_img") or self._build_boomerang_image()
        self.image = self.base_image
        self.rect = self.image.get_rect(center=self.position)

        # Damage is applied once on contact, then the boomerang is removed.
        self.damage = damage
        self.hitbox_width = max(34, int(self.base_image.get_width() * 0.56))
        self.hitbox_height = max(14, int(self.base_image.get_height() * 0.24))

        # The boomerang waits in place first so the player can read the spawn.
        self.idle_duration = 1.0
        self.timer = 0.0

        # Movement state is broken into explicit phases so each leg is easy to tune separately.
        self.phase = "idle"
        self.respawn_delay = 1.0
        self.respawn_timer = 0.0

        # Launch speed stays moderate while the spin is visible and readable.
        self.speed = 420.0
        self.spin_speed = 220.0
        self.rotation = 0.0

        # The initial straight line uses the player's position captured at the end of the idle stage.
        self.launch_target = pygame.Vector2(player_rect.center)
        self.velocity = pygame.Vector2(0, 1)

        # Curving is intentionally subtle: the heading can only drift 10 degrees from the base travel angle.
        self.max_curve_degrees = 10.0
        self.turn_rate_degrees = 90.0
        self.downward_base_angle = 90.0
        self.upward_base_angle = -90.0
        self.side_multiplier = 0.0

        # Visibility toggles off while the boomerang is below the screen waiting to return.
        self.visible = True
        self.reentry_side_padding = 70

    def _build_boomerang_image(self):
        """Create a simple painted boomerang surface so the attack has a distinct readable shape."""
        surface = pygame.Surface((88, 88), pygame.SRCALPHA)
        arc_rect = pygame.Rect(14, 14, 60, 60)

        pygame.draw.arc(surface, (95, 35, 25), arc_rect, math.radians(210), math.radians(318), 14)
        pygame.draw.arc(surface, (170, 95, 65), arc_rect.inflate(-10, -10), math.radians(210), math.radians(318), 10)

        tip_a = [(22, 56), (12, 68), (28, 62)]
        tip_b = [(58, 18), (70, 10), (62, 26)]
        pygame.draw.polygon(surface, (95, 35, 25), tip_a)
        pygame.draw.polygon(surface, (95, 35, 25), tip_b)
        return surface

    def _vector_from_angle(self, angle_deg):
        """Convert a heading angle into a unit direction vector."""
        radians = math.radians(angle_deg)
        return pygame.Vector2(math.cos(radians), math.sin(radians))

    def _normalize_angle(self, angle_deg):
        """Wrap any angle into the -180 to 180 range for stable steering math."""
        return (angle_deg + 180.0) % 360.0 - 180.0

    def _steer_toward_player(self, player, base_angle, dt):
        """Curve gently toward the player's current x-position without exceeding the 10 degree cap."""
        desired = pygame.Vector2(player.get_rect().center) - self.position
        if desired.length_squared() <= 1e-6:
            return self._vector_from_angle(base_angle)

        desired_angle = math.degrees(math.atan2(desired.y, desired.x))
        angle_delta = self._normalize_angle(desired_angle - base_angle)
        limited_target_angle = base_angle + utils.clamp(angle_delta, -self.max_curve_degrees, self.max_curve_degrees)

        current_angle = math.degrees(math.atan2(self.velocity.y, self.velocity.x))
        step = self.turn_rate_degrees * dt
        to_target = self._normalize_angle(limited_target_angle - current_angle)
        applied_delta = utils.clamp(to_target, -step, step)
        new_angle = current_angle + applied_delta
        return self._vector_from_angle(new_angle)

    def get_hitbox(self):
        """Use a smaller horizontal rectangle instead of the sprite's rotating square bounds."""
        if not self.visible or self.finished:
            return None
        rect = pygame.Rect(0, 0, self.hitbox_width, self.hitbox_height)
        rect.center = (int(self.position.x), int(self.position.y))
        return rect

    def get_debug_hitboxes(self):
        hitbox = self.get_hitbox()
        if hitbox is None:
            return []
        return [{"type": "rect", "rect": hitbox, "label": "boomerang"}]

    def _update_damage(self, dt, player):
        """Deal damage once on body contact, then remove this boomerang."""
        hitbox = self.get_hitbox()
        if hitbox and hitbox.colliderect(player.get_hitbox()):
            player.take_damage(self.damage)
            self.visible = False
            self.finished = True

    def _start_downward_curve(self, player):
        """Switch from the opening straight line to the first limited-curvature chase leg."""
        self.phase = "curve_down"
        self.side_multiplier = -1.0 if player.get_rect().centerx < self.launch_target.x else 1.0
        self.velocity = self._vector_from_angle(self.downward_base_angle + (self.side_multiplier * self.max_curve_degrees))

    def _start_return_pass(self, player, screen_rect):
        """Respawn just below the screen near the side where the first pass disappeared."""
        self.phase = "return_up"
        self.visible = True

        player_rect = player.get_rect()
        respawn_x = player_rect.centerx + (self.side_multiplier * (player_rect.width * 1.8 + self.reentry_side_padding))
        respawn_x = utils.clamp(respawn_x, 40, screen_rect.width - 40)
        self.position = pygame.Vector2(respawn_x, screen_rect.height + 45)
        self.velocity = self._vector_from_angle(self.upward_base_angle - (self.side_multiplier * self.max_curve_degrees))
        self.rect = self.image.get_rect(center=(int(self.position.x), int(self.position.y)))

    def update(self, dt, projectiles, player):
        """Advance the boomerang through idle, straight launch, downward curve, hidden wait, and return."""
        if self.finished:
            return []

        self.timer += dt
        screen_rect = pygame.display.get_surface().get_rect()

        if self.phase == "idle":
            if self.timer >= self.idle_duration:
                self.phase = "launch"
                self.launch_target = pygame.Vector2(player.get_rect().center)
                direction = self.launch_target - self.position
                if direction.length_squared() <= 1e-6:
                    direction = pygame.Vector2(0, 1)
                self.velocity = direction.normalize()

        elif self.phase == "launch":
            self.rotation = (self.rotation + self.spin_speed * dt) % 360.0
            self.position += self.velocity * self.speed * dt

            if self.position.y >= player.get_rect().centery:
                self._start_downward_curve(player)

        elif self.phase == "curve_down":
            self.rotation = (self.rotation + self.spin_speed * dt) % 360.0
            self.velocity = self._steer_toward_player(player, self.downward_base_angle + (self.side_multiplier * self.max_curve_degrees), dt)
            self.position += self.velocity * self.speed * dt

            if self.position.y - self.rect.height * 0.5 > screen_rect.height:
                self.phase = "waiting_return"
                self.visible = False
                self.respawn_timer = 0.0

        elif self.phase == "waiting_return":
            self.respawn_timer += dt
            if self.respawn_timer >= self.respawn_delay:
                self._start_return_pass(player, screen_rect)

        elif self.phase == "return_up":
            self.rotation = (self.rotation + self.spin_speed * dt) % 360.0
            self.velocity = self._steer_toward_player(player, self.upward_base_angle - (self.side_multiplier * self.max_curve_degrees), dt)
            self.position += self.velocity * self.speed * dt

            if self.position.y + self.rect.height * 0.5 < 0:
                self.finished = True

        self.image = pygame.transform.rotate(self.base_image, -self.rotation)
        self.rect = self.image.get_rect(center=(int(self.position.x), int(self.position.y)))
        self._update_damage(dt, player)
        return []

    def draw(self, surface):
        """Draw the rotating boomerang only while it is on-screen and active."""
        if self.finished or not self.visible:
            return
        surface.blit(self.image, self.rect)
