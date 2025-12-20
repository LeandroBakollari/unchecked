import math
import random
import pygame

# Palette tuned for a light paper theme
PAPER_BG = (247, 244, 236)
PAPER_LINE = (214, 221, 232)
PAPER_RULE = (212, 143, 151)
INK = (35, 34, 30)
INK_MUTED = (70, 68, 60)


def get_font(size=28, bold=False):
    if not pygame.font.get_init():
        pygame.font.init()
    font = pygame.font.Font(None, size)
    font.set_bold(bold)
    return font


def load_scaled(path, size):
    im = pygame.image.load(path).convert_alpha()
    return pygame.transform.scale(im, size)


def clamp(val, min_v, max_v):
    return max(min_v, min(max_v, val))


def lerp(a, b, t):
    return a + (b - a) * clamp(t, 0.0, 1.0)


def vector_to(a, b):
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    dist = math.hypot(dx, dy)
    if dist == 0:
        return 0.0, 0.0, 0.0
    return dx, dy, dist


def normalized(dx, dy):
    dist = math.hypot(dx, dy)
    if dist == 0:
        return 0.0, 0.0, 0.0
    return dx / dist, dy / dist, dist


def angle_from_vector(dx, dy):
    return math.degrees(math.atan2(dy, dx))


def point_from_angle(origin, angle_deg, length):
    rad = math.radians(angle_deg)
    return (
        origin[0] + math.cos(rad) * length,
        origin[1] + math.sin(rad) * length,
    )


def swing_hits_rect(origin, angle_deg, length, half_width, hit_rect):
    """Approximate a sword swing as a wide line and test against a rect."""
    cx, cy = hit_rect.center
    dx = cx - origin[0]
    dy = cy - origin[1]
    rad = math.radians(angle_deg)
    along = dx * math.cos(rad) + dy * math.sin(rad)
    perp = -dx * math.sin(rad) + dy * math.cos(rad)
    reach = length * 0.5
    player_radius = math.hypot(hit_rect.width, hit_rect.height) * 0.35
    return abs(perp) <= half_width + player_radius and -reach <= along <= reach


def jitter(value, amount):
    return value + random.randint(-amount, amount)


def recalc_geometry(screen):
    screen_width, screen_height = screen.get_size()

    # Play area (player movement) sits low and centered
    area_width = int(screen_width * 0.68)
    area_height = int(screen_height * 0.58)
    area_rect = pygame.Rect(
        (screen_width - area_width) // 2,
        screen_height - area_height - int(screen_height * 0.06),
        area_width,
        area_height,
    )

    # Pencil drawing lane across the top
    top_area = pygame.Rect(
        int(screen_width * 0.08),
        int(screen_height * 0.06),
        int(screen_width * 0.84),
        int(screen_height * 0.22),
    )
    return screen_width, screen_height, area_rect, top_area


def draw_sketched_rect(surface, rect, color=INK, jitter_amount=3, passes=4, width=2):
    # deterministic jitter per rect so the border doesn't wiggle each frame
    seed_val = f"{rect.left}-{rect.top}-{rect.width}-{rect.height}"
    rng = random.Random(seed_val)
    for _ in range(passes):
        pts = [
            (rect.left + rng.randint(-jitter_amount, jitter_amount), rect.top + rng.randint(-jitter_amount, jitter_amount)),
            (rect.right + rng.randint(-jitter_amount, jitter_amount), rect.top + rng.randint(-jitter_amount, jitter_amount)),
            (rect.right + rng.randint(-jitter_amount, jitter_amount), rect.bottom + rng.randint(-jitter_amount, jitter_amount)),
            (rect.left + rng.randint(-jitter_amount, jitter_amount), rect.bottom + rng.randint(-jitter_amount, jitter_amount)),
        ]
        pygame.draw.lines(surface, color, True, pts, width)


def draw_paper_background(surface, area_rect, top_area):
    surface.fill(PAPER_BG)
    w, h = surface.get_size()
    margin = 36

    # notebook ruling
    for y in range(margin, h, 34):
        pygame.draw.line(surface, PAPER_LINE, (0, y), (w, y), 1)
    pygame.draw.line(surface, PAPER_RULE, (margin, 0), (margin, h), 2)

    # shaded zones
    for rect, alpha in ((top_area, 32), (area_rect, 40)):
        overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
        overlay.fill((255, 255, 255, alpha))
        surface.blit(overlay, rect.topleft)

    draw_sketched_rect(surface, top_area, color=INK_MUTED, jitter_amount=4, passes=3, width=2)
    draw_sketched_rect(surface, area_rect, color=INK, jitter_amount=4, passes=4, width=3)


def draw_health_bar(surface, x, y, health, max_health, width=230, height=26):
    health = clamp(health, 0, max_health)
    ratio = health / max_health if max_health else 0
    back_rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(surface, (255, 255, 255), back_rect.inflate(6, 6), border_radius=6)
    pygame.draw.rect(surface, (90, 90, 90), back_rect.inflate(2, 2), border_radius=6, width=2)

    if ratio > 0.6:
        color = (45, 180, 100)
    elif ratio > 0.3:
        color = (230, 170, 55)
    else:
        color = (200, 60, 50)
    inner = pygame.Rect(x, y, int(width * ratio), height)
    pygame.draw.rect(surface, color, inner, border_radius=4)
