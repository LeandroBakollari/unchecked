import pygame
import random
import math


class Pen:
    def __init__(self, image, top_area):
        self.image = image
        self.rect = image.get_rect(center=top_area.center)
        self.x = float(self.rect.centerx)
        self.y = float(self.rect.centery)
        self.top_area = top_area
        self.speed = 50.0
        self.wait_time = 0
        self.drawing = False
        self.pick_new_target()


    def pick_new_target(self):
        self.target_x = random.randint(int(self.top_area.left), int(self.top_area.right))
        self.target_y = random.randint(int(self.top_area.top), int(self.top_area.bottom))


    def update(self):
        if self.wait_time > 0:
            self.wait_time -= 1
            return
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        dist = math.hypot(dx, dy) or 1.0
        if dist > self.speed:
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed
            self.rect.center = (int(self.x), int(self.y))
        else:
            # arrived, start drawing (attack)
            self.rect.center = (self.target_x, self.target_y)
            self.drawing = True
            self.wait_time = 40


    def ready_to_attack(self):
        if self.drawing and self.wait_time == 0:
            self.drawing = False
            return True
        return False
    

    def get_rect(self):
        return self.rect


    def draw(self, surface):
        surface.blit(self.image, self.rect)