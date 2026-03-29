import math
import pygame

from game import utils
from game.attacks.base import AttackBase


class StuffAttack(AttackBase):
    """A magic staff that sweeps toward the player, then sustains a rotating arc of expanding fireballs."""

    def __init__(self, pen_rect, player_rect, assets, damage=10):
        super().__init__(pen_rect, player_rect, assets)

        # The staff remains at the pen's draw position for the entire attack.
        self.origin = pygame.Vector2(pen_rect.center)

        # The staff art points upward, while the fireball art points toward the bottom-left.
        self.staff_img_raw = assets["stuff_img"]
        self.fireball_img_raw = assets["fireball_img"]
        self.staff_img = self.staff_img_raw
        self.staff_rect = self.staff_img.get_rect(center=self.origin)

        # The attack waits, then sustains the rotating fireball pattern for a short readable window.
        self.windup_duration = 2.0
        self.pattern_duration = 3.0
        self.timer = 0.0

        # During the windup the staff waves across 180 degrees with the player-centered direction in the middle.
        self.base_angle = utils.angle_from_vector(*(pygame.Vector2(player_rect.center) - self.origin))
        self.sweep_arc = 180.0
        self.current_angle = self.base_angle

        # The rotating fireball ring uses six evenly spaced slots distributed across a 180 degree arc.
        self.fireball_count = 6
        self.arc_span = 180.0
        self.rotation_speed = 75.0
        self.fireball_max_radius = 155.0
        self.fireball_start_radius = 0.0
        self.fireball_expand_duration = 1.15
        self.fireball_radius = 0.0
        self.fireball_hitbox_scale = 0.8

        # The orbit center is locked when the pattern starts and sits halfway between the staff and the targeted player spot.
        self.pattern_started = False
        self.orbit_center = self.origin
        self.pattern_base_angle = self.base_angle
        self.fireball_start_angle = self.base_angle

        # Damage uses a short per-fireball cooldown so overlapping sprites do not stack every frame.
        self.damage = damage
        self.fireball_hit_cooldown = 0.18
        self.fireball_cooldowns = [0.0 for _ in range(self.fireball_count)]

    def _vector_angle(self, vector):
        """Convert a vector to degrees while handling zero-length vectors safely."""
        if vector.length_squared() <= 1e-6:
            return 0.0
        return math.degrees(math.atan2(vector.y, vector.x))

    def _start_pattern(self, player):
        """Lock the player-facing direction and the orbit midpoint when the fireballs begin."""
        self.pattern_started = True
        player_pos = pygame.Vector2(player.get_rect().center)
        self.orbit_center = self.origin.lerp(player_pos, 0.5)
        self.pattern_base_angle = self._vector_angle(player_pos - self.orbit_center)
        self.fireball_start_angle = self._vector_angle(self.origin - self.orbit_center)
        self.fireball_start_radius = self.orbit_center.distance_to(self.origin)
        self.fireball_radius = self.fireball_start_radius
        self.current_angle = self.pattern_base_angle

    def _target_fireball_angle(self, index):
        """Return the final slot angle for one fireball within the player-facing 180 degree arc."""
        if self.fireball_count == 1:
            base_offset = 0.0
        else:
            step = self.arc_span / (self.fireball_count - 1)
            base_offset = -self.arc_span * 0.5 + index * step
        return self.pattern_base_angle + base_offset

    def _fireball_angle(self, index, elapsed_pattern):
        """Unfold each fireball from the staff direction into its slot, then keep rotating from there."""
        unfold_progress = utils.clamp(elapsed_pattern / self.fireball_expand_duration, 0.0, 1.0)
        target_angle = self._target_fireball_angle(index)
        unfolded_angle = utils.lerp(self.fireball_start_angle, target_angle, unfold_progress)
        return unfolded_angle + elapsed_pattern * self.rotation_speed

    def _fireball_position(self, index, elapsed_pattern):
        """Place each fireball on the rotating arc using the shared orbit center and current radius."""
        angle = self._fireball_angle(index, elapsed_pattern)
        radians = math.radians(angle)
        offset = pygame.Vector2(math.cos(radians), math.sin(radians)) * self.fireball_radius
        return self.orbit_center + offset

    def _fireball_image(self, index, elapsed_pattern):
        """Rotate the fireball so its bottom-right side always points toward the orbit center."""
        radial_angle = self._fireball_angle(index, elapsed_pattern)
        inward_angle = radial_angle + 180.0

        # The source art's bottom-right direction is treated as the trailing side that should face the center.
        source_angle = 315.0
        return pygame.transform.rotate(self.fireball_img_raw, -(inward_angle - source_angle))

    def _update_damage(self, dt, player, elapsed_pattern):
        """Apply contact damage using smaller fireball hitboxes and independent per-fireball cooldowns."""
        player_hitbox = player.get_hitbox()
        for index in range(self.fireball_count):
            self.fireball_cooldowns[index] = max(0.0, self.fireball_cooldowns[index] - dt)
            fireball_pos = self._fireball_position(index, elapsed_pattern)
            fireball_img = self._fireball_image(index, elapsed_pattern)
            fireball_rect = fireball_img.get_rect(center=(int(fireball_pos.x), int(fireball_pos.y)))
            collision_rect = fireball_rect.inflate(
                -fireball_rect.width * (1.0 - self.fireball_hitbox_scale),
                -fireball_rect.height * (1.0 - self.fireball_hitbox_scale),
            )
            if collision_rect.colliderect(player_hitbox) and self.fireball_cooldowns[index] <= 0.0:
                player.take_damage(self.damage)
                self.fireball_cooldowns[index] = self.fireball_hit_cooldown

    def update(self, dt, projectiles, player):
        """Sweep the staff first, then lock into the rotating expanding fireball pattern."""
        if self.finished:
            return []

        self.timer += dt

        if self.timer < self.windup_duration:
            progress = utils.clamp(self.timer / self.windup_duration, 0.0, 1.0)
            sweep_offset = utils.lerp(-self.sweep_arc * 0.5, self.sweep_arc * 0.5, progress)
            self.current_angle = self.base_angle + sweep_offset
        else:
            if not self.pattern_started:
                self._start_pattern(player)

            elapsed_pattern = self.timer - self.windup_duration
            expand_progress = utils.clamp(elapsed_pattern / self.fireball_expand_duration, 0.0, 1.0)
            self.fireball_radius = utils.lerp(
                self.fireball_start_radius,
                self.fireball_max_radius,
                expand_progress,
            )
            self.current_angle = self.pattern_base_angle
            self._update_damage(dt, player, elapsed_pattern)

            if elapsed_pattern >= self.pattern_duration:
                self.finished = True

        # The staff image points upward, so subtract 90 degrees from the mathematical facing angle.
        self.staff_img = pygame.transform.rotate(self.staff_img_raw, -(self.current_angle + 90.0))
        self.staff_rect = self.staff_img.get_rect(center=(int(self.origin.x), int(self.origin.y)))
        return []

    def draw(self, surface):
        """Draw the staff and, once active, the rotating expanding fireball arc."""
        if self.finished:
            return

        surface.blit(self.staff_img, self.staff_rect)

        if not self.pattern_started:
            return

        elapsed_pattern = self.timer - self.windup_duration
        for index in range(self.fireball_count):
            fireball_pos = self._fireball_position(index, elapsed_pattern)
            fireball_img = self._fireball_image(index, elapsed_pattern)
            fireball_rect = fireball_img.get_rect(center=(int(fireball_pos.x), int(fireball_pos.y)))
            surface.blit(fireball_img, fireball_rect)
