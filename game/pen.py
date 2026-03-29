import math
import random
import pygame


class Pen:
    def __init__(self, image, top_area):
        self.image = image
        self.rect = image.get_rect(center=top_area.center)
        self.x = float(self.rect.centerx)
        self.y = float(self.rect.centery)
        self.top_area = top_area

        # The pen starts slower and ramps over a full three-minute run before reaching top speed.
        self.base_speed = 230.0
        self.max_speed = 780.0
        self.time_to_max_speed = 180.0
        self.draw_duration = 0.55  # seconds holding position to "draw"
        self.wait_timer = 0.0
        self.drawing = False
        self.ready_flag = False
        self.elapsed = 0.0

        self.pick_new_target()

    def pick_new_target(self):
        self.target_x = random.uniform(self.top_area.left, self.top_area.right)
        self.target_y = random.uniform(self.top_area.top, self.top_area.bottom)

    def update(self, dt):
        self.elapsed += dt
        progress = min(1.0, self.elapsed / self.time_to_max_speed)
        speed = self.base_speed + (self.max_speed - self.base_speed) * progress

        if self.wait_timer > 0:
            self.wait_timer -= dt
            if self.wait_timer <= 0 and self.drawing:
                self.drawing = False
                self.ready_flag = True
            return

        dx = self.target_x - self.x
        dy = self.target_y - self.y
        dist = math.hypot(dx, dy) or 1.0
        step = speed * dt
        if dist > step:
            self.x += (dx / dist) * step
            self.y += (dy / dist) * step
        else:
            # arrived, start drawing (attack telegraph)
            self.x, self.y = self.target_x, self.target_y
            self.drawing = True
            self.wait_timer = self.draw_duration

        self.rect.center = (int(self.x), int(self.y))

    def ready_to_attack(self):
        if self.ready_flag:
            self.ready_flag = False
            return True
        return False

    def get_rect(self):
        return self.rect

    def draw(self, surface):
        # a light scribble circle while "drawing"
        if self.drawing:
            scribble = pygame.Surface((90, 90), pygame.SRCALPHA)
            for _ in range(12):
                ox, oy = random.randint(-6, 6), random.randint(-6, 6)
                pygame.draw.ellipse(
                    scribble,
                    (30, 30, 30, 60),
                    (20 + ox, 20 + oy, 50, 50),
                    2,
                )
            surface.blit(scribble, scribble.get_rect(center=self.rect.center))

        surface.blit(self.image, self.rect)
