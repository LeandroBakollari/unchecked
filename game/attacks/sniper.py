import math
import pygame

from game import utils
from game.attacks.base import AttackBase


class SniperAttack(AttackBase):
    """A stationary sniper that tracks the player during a warning phase, then fires a sustained beam."""

    def __init__(self, pen_rect, player_rect, assets, damage=7):
        super().__init__(pen_rect, player_rect, assets)

        # The sniper always stays where the pen finished drawing this attack.
        self.origin = pygame.Vector2(pen_rect.center)

        # The sprite source art points to the right, so rotating by -angle keeps the barrel aligned to the target.
        self.sniper_img_raw = assets["sniper_img"]
        self.sniper_img = self.sniper_img_raw
        self.sniper_rect = self.sniper_img.get_rect(center=self.origin)

        # Damage is applied in short contact ticks while the beam is active so touching it during the shot always hurts.
        self.damage = damage
        self.damage_tick_interval = 0.15
        self.damage_tick_timer = 0.0

        # Timings for the four-stage state machine: track, pause with locked aim, fire, then fade away.
        self.aim_duration = 2.0
        self.lock_delay = 0.4
        self.fire_duration = 1.0
        self.fade_duration = 0.3
        self.timer = 0.0

        # Beam widths are kept separate so the warning stays thin while the fired beam can fade down cleanly.
        self.warning_width = 4
        self.fire_width = 12

        # Cached aiming state is frozen the instant the attack starts firing.
        self.current_angle = 0.0
        self.aim_locked = False
        self.fire_angle = 0.0
        self.warning_end = pygame.Vector2(player_rect.center)
        self.fire_end = pygame.Vector2(player_rect.center)

        # A small muzzle offset prevents the line from starting at the center of the sprite body.
        self.muzzle_distance = max(self.sniper_img_raw.get_width() * 0.42, 24)

    def _get_direction(self, angle_deg):
        """Return a normalized direction vector for the given facing angle."""
        radians = math.radians(angle_deg)
        return pygame.Vector2(math.cos(radians), math.sin(radians))

    def _get_muzzle_position(self, angle_deg):
        """Move the line origin forward so the warning and beam start at the rifle barrel."""
        return self.origin + self._get_direction(angle_deg) * self.muzzle_distance

    def _ray_to_screen_edge(self, start_pos, angle_deg, surface_size):
        """Extend the fired beam from the muzzle until it reaches the edge of the visible screen."""
        direction = self._get_direction(angle_deg)
        width, height = surface_size
        candidates = []

        if abs(direction.x) > 1e-6:
            for boundary_x in (0, width):
                distance = (boundary_x - start_pos.x) / direction.x
                if distance > 0:
                    point = start_pos + direction * distance
                    if 0 <= point.y <= height:
                        candidates.append((distance, point))

        if abs(direction.y) > 1e-6:
            for boundary_y in (0, height):
                distance = (boundary_y - start_pos.y) / direction.y
                if distance > 0:
                    point = start_pos + direction * distance
                    if 0 <= point.x <= width:
                        candidates.append((distance, point))

        if not candidates:
            # Fallback keeps the beam valid even if the muzzle somehow starts outside the screen.
            return start_pos + direction * max(surface_size)

        _, end_point = min(candidates, key=lambda item: item[0])
        return end_point

    def _player_touches_beam(self, player_rect):
        """Test the actual muzzle-to-end beam segment against the player's hitbox with beam thickness."""
        beam_start = self._get_muzzle_position(self.fire_angle)
        hit_rect = player_rect.inflate(-8, -8)
        clipped_segment = hit_rect.clipline(
            (int(beam_start.x), int(beam_start.y)),
            (int(self.fire_end.x), int(self.fire_end.y)),
        )
        if clipped_segment:
            return True

        # If the center line misses by less than half the beam width, still count it as a hit.
        player_center = pygame.Vector2(hit_rect.center)
        beam_vector = self.fire_end - beam_start
        beam_length_sq = beam_vector.length_squared()
        if beam_length_sq <= 1e-6:
            return beam_start.distance_to(player_center) <= self.fire_width * 0.5

        projection = (player_center - beam_start).dot(beam_vector) / beam_length_sq
        projection = utils.clamp(projection, 0.0, 1.0)
        closest_point = beam_start + beam_vector * projection
        player_radius = max(hit_rect.width, hit_rect.height) * 0.35
        return closest_point.distance_to(player_center) <= (self.fire_width * 0.5) + player_radius

    def _lock_current_aim(self):
        """Freeze the tracked angle once and cache the full-screen beam endpoint."""
        self.aim_locked = True
        self.fire_angle = self.current_angle
        surface = pygame.display.get_surface()
        self.fire_end = self._ray_to_screen_edge(
            self._get_muzzle_position(self.fire_angle),
            self.fire_angle,
            surface.get_size(),
        )

    def update(self, dt, projectiles, player):
        """Advance the sniper through aim, pause, fire, and fade stages without spawning separate projectiles."""
        if self.finished:
            return []

        self.timer += dt
        player_center = pygame.Vector2(player.get_rect().center)
        fire_start_time = self.aim_duration + self.lock_delay
        fire_end_time = fire_start_time + self.fire_duration
        fade_end_time = fire_end_time + self.fade_duration

        if self.timer < self.aim_duration:
            # During the warning phase the sniper keeps rotating so the player can read the telegraph.
            self.warning_end = player_center
            dx, dy, _ = utils.vector_to(self.origin, self.warning_end)
            self.current_angle = utils.angle_from_vector(dx, dy)
        else:
            if not self.aim_locked:
                # Freeze the aim as soon as tracking ends so the player gets a readable reaction window.
                self._lock_current_aim()

            if fire_start_time <= self.timer <= fire_end_time:
                self.damage_tick_timer -= dt
                if self.damage_tick_timer <= 0.0 and self._player_touches_beam(player.get_rect()):
                    player.take_damage(self.damage)
                    self.damage_tick_timer = self.damage_tick_interval

            if self.timer >= fade_end_time:
                self.finished = True

        # The sprite rotation always matches the live aim during warning, then the frozen fire angle afterwards.
        sprite_angle = self.current_angle if self.timer < self.aim_duration else self.fire_angle
        self.sniper_img = pygame.transform.rotate(self.sniper_img_raw, -sprite_angle)
        self.sniper_rect = self.sniper_img.get_rect(center=(int(self.origin.x), int(self.origin.y)))
        return []

    def _draw_warning_line(self, surface):
        """Draw the thin telegraph from the sniper muzzle to the player's current position."""
        progress = utils.clamp(self.timer / self.aim_duration, 0.0, 1.0)
        start = self._get_muzzle_position(self.current_angle)
        end = self.warning_end
        red = int(utils.lerp(255, 255, progress))
        green = int(utils.lerp(255, 120, progress))
        blue = int(utils.lerp(255, 145, progress))
        pygame.draw.line(surface, (red, green, blue), start, end, self.warning_width)

    def _draw_fire_line(self, surface):
        """Draw the fired beam as a single dark red line that thins out during the fade stage."""
        fire_start_time = self.aim_duration + self.lock_delay
        elapsed_fire = self.timer - fire_start_time
        fade_progress = utils.clamp((elapsed_fire - self.fire_duration) / self.fade_duration, 0.0, 1.0)
        shrink = 1.0 - fade_progress

        beam_width = max(1, int(self.fire_width * 2 * shrink))
        start = self._get_muzzle_position(self.fire_angle)

        pygame.draw.line(surface, (140, 18, 18), start, self.fire_end, beam_width)

    def draw(self, surface):
        """Render the sprite and whichever line phase is currently active."""
        if self.finished:
            return

        if self.timer < self.aim_duration:
            self._draw_warning_line(surface)
        elif self.timer >= self.aim_duration + self.lock_delay:
            self._draw_fire_line(surface)

        surface.blit(self.sniper_img, self.sniper_rect)
