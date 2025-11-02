import pygame
import math


def get_font(size=28):
    if not pygame.font.get_init():
        pygame.font.init()
    return pygame.font.Font(None, size)


def load_scaled(path, size):
    im = pygame.image.load(path).convert_alpha()
    return pygame.transform.scale(im, size)


def recalc_geometry(screen):
    screen_width, screen_height = screen.get_size()
    area_width = int(screen_width * 0.6)
    area_height = int(screen_height * 0.6)
    area_rect = pygame.Rect(
        (screen_width - area_width) // 2,
        screen_height - area_height,
        area_width, area_height
    )
    top_area = pygame.Rect(
        int(screen_width * 0.05),
        int(screen_height * 0.05),
        int(screen_width * 0.9),
        int(screen_height * 0.3)
    )
    return screen_width, screen_height, area_rect, top_area


def draw_health_bar(surface, x, y, health, max_health, width=200, height=25):
    health = max(0, min(health, max_health))
    ratio = health / max_health
    pygame.draw.rect(surface, (50, 50, 50), (x - 2, y - 2, width + 4, height + 4))
    if ratio > 0.6:
        color = (0, 200, 0)
    elif ratio > 0.3:
        color = (230, 200, 0)
    else:
        color = (200, 0, 0)
    pygame.draw.rect(surface, color, (x, y, int(width * ratio), height))