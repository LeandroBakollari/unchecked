import pygame
import random
from game.player import Player
from game.pen import Pen
from game.utils import load_scaled, recalc_geometry, draw_health_bar, get_font

# === ATTACKS ===
from game.attacks.gun import GunAttack
from game.attacks.grenade import GrenadeAttack
from game.attacks.sword import SwordAttack

pygame.init()

# === SETTINGS ===
ATTACK_TYPES = [GunAttack, GrenadeAttack, SwordAttack]

screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.display.set_caption("Unchecked - Modular")
pygame.mouse.set_visible(False)
clock = pygame.time.Clock()
fullscreen = True
running = True

# geometry global state (recalc on resize)
screen_width, screen_height, area_rect, top_area = recalc_geometry(screen)

# === ASSETS ===
ASSET_PATH = "game/assets/images/"
checkbox_icon = load_scaled(ASSET_PATH + "Checkbox.png", (25, 25))
pen_img = load_scaled(ASSET_PATH + "pen.png", (130, 130))
gun_img = load_scaled(ASSET_PATH + "gun.png", (100, 100))
bullet_img = load_scaled(ASSET_PATH + "bullet.png", (20, 20))
grenade_img = load_scaled(ASSET_PATH + "grenade.png", (40, 40))
explosion_img = load_scaled(ASSET_PATH + "explosion.png", (160, 160))
sword_img = load_scaled(ASSET_PATH + "sword.png", (80, 80))
slash_img = load_scaled(ASSET_PATH + "slash.png", (200, 30))

# attach images to attack factory via simple registry
AttackAssets = {
    'gun_img': gun_img,
    'bullet_img': bullet_img,
    'grenade_img': grenade_img,
    'explosion_img': explosion_img,
    'sword_img': sword_img,
    'slash_img': slash_img
}

# === PLAYER & PEN ===
player = Player(checkbox_icon, screen_width, screen_height)
pen = Pen(pen_img, top_area)

# === GAME OBJECT MANAGERS ===
active_attacks = []
projectiles = []  # unified list for bullets, grenades, slashes, etc.

# === GAME LOOP ===
while running:
    dt = clock.get_time() / 1000  # delta time in seconds

    # --- EVENTS ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            if event.key == pygame.K_F11:
                fullscreen = not fullscreen
                if fullscreen:
                    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                else:
                    screen = pygame.display.set_mode((1200, 900))
                screen_width, screen_height, area_rect, top_area = recalc_geometry(screen)
                player.on_resize(screen_width, screen_height)

    # --- INPUT & PLAYER ---
    player.handle_input()
    player.clamp_to(area_rect)

    # --- PEN MOVEMENT & ATTACK SPAWNING ---
    pen.update()
    if pen.ready_to_attack():
        attack_cls = random.choice(ATTACK_TYPES)
        attack = attack_cls(pen.get_rect(), player.get_rect(), AttackAssets)
        active_attacks.append(attack)
        pen.pick_new_target()

    # --- UPDATE ATTACKS & SPAWN PROJECTILES ---
    for attack in active_attacks[:]:
        new_projectiles = attack.update(projectiles, player) or []  # always a list
        if new_projectiles:
            projectiles.extend(new_projectiles)
        if attack.finished:
            active_attacks.remove(attack)

    # --- UPDATE PROJECTILES ---
    for proj in projectiles[:]:  # iterate over a copy so we can remove safely
        proj.update(dt, player)
        if not proj.active or player.health <= 0:
            projectiles.remove(proj)

    # --- CHECK PLAYER ALIVE ---
    if not player.alive:
        running = False

    # --- DRAW ---
    screen.fill((210, 210, 200))
    pygame.draw.rect(screen, (180, 180, 180), area_rect, 5)

    # HUD
    font = get_font()
    text = font.render(f"HP: {player.health}/{player.max_health}", True, (255, 255, 255))
    screen.blit(text, (35, 30))
    draw_health_bar(screen, 35, 60, player.health, player.max_health)

    # DRAW GAME OBJECTS
    pen.draw(screen)
    for attack in active_attacks:
        attack.draw(screen)
    for proj in projectiles:
        proj.draw(screen)
    player.draw(screen)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
