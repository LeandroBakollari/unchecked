import pygame

from game import utils
from game.attacks.base import AttackBase
from game.projectiles.shuriken import ShurikenProjectile


class ShurikenAttack(AttackBase):
    """A stationary spinning shuriken that charges, then launches three curved homing shurikens one second apart."""

    def __init__(self, pen_rect, player_rect, assets):
        super().__init__(pen_rect, player_rect, assets)

        # The spawn point never moves with the pen after the attack is drawn.
        self.origin = pygame.Vector2(pen_rect.center)

        # The placed shuriken and the launched projectiles share the same art, with the projectile slightly smaller.
        self.base_image = assets["shuriken_img"]
        self.projectile_image = assets.get("shuriken_projectile_img", self.base_image)
        self.image = self.base_image
        self.rect = self.image.get_rect(center=self.origin)

        # The attack waits first, then spins in place for three seconds while firing once per second.
        self.idle_duration = 1.0
        self.spin_duration = 3.0
        self.launch_interval = 1.0
        self.timer = 0.0
        self.spin_timer = 0.0
        self.shots_fired = 0
        self.total_shots = 3

        # The placed shuriken spins slightly faster than the boomerang, per your request.
        self.spin_angle = 0.0
        self.spin_speed = 300.0

    def _spawn_shuriken(self, player):
        """Create one gently homing shuriken aimed at the player's current location."""
        target = pygame.Vector2(player.get_rect().center)
        direction = target - self.origin
        if direction.length_squared() <= 1e-6:
            direction = pygame.Vector2(0, 1)
        direction = direction.normalize()

        return ShurikenProjectile(
            self.origin.x,
            self.origin.y,
            direction.x,
            direction.y,
            self.projectile_image,
        )

    def update(self, dt, projectiles, player):
        """Idle first, then spin in place and launch one homing shuriken per second."""
        if self.finished:
            return []

        self.timer += dt
        if self.timer < self.idle_duration:
            return []

        self.spin_timer += dt
        self.spin_angle = (self.spin_angle + self.spin_speed * dt) % 360.0
        self.image = pygame.transform.rotate(self.base_image, -self.spin_angle)
        self.rect = self.image.get_rect(center=(int(self.origin.x), int(self.origin.y)))

        spawned = []
        while self.shots_fired < self.total_shots and self.spin_timer >= (self.shots_fired + 1) * self.launch_interval:
            spawned.append(self._spawn_shuriken(player))
            self.shots_fired += 1

        if self.shots_fired >= self.total_shots and self.spin_timer >= self.spin_duration:
            self.finished = True

        return spawned

    def draw(self, surface):
        """Draw the charging shuriken only while it is still waiting to launch its full set."""
        if self.finished:
            return
        surface.blit(self.image, self.rect)
