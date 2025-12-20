import random
import pygame

from game.player import Player
from game.pen import Pen
from game.utils import (
    load_scaled,
    recalc_geometry,
    draw_health_bar,
    get_font,
    draw_paper_background,
)

from game.attacks.gun import GunAttack
from game.attacks.grenade import GrenadeAttack
from game.attacks.sword import SwordAttack
from game.attacks.staff import StaffAttack

pygame.init()

# --- ATTACK REGISTRY ---
ATTACK_TYPES = [GunAttack, GrenadeAttack, SwordAttack, StaffAttack]

# --- DISPLAY SETUP ---
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.display.set_caption("Unchecked")
pygame.mouse.set_visible(False)
clock = pygame.time.Clock()
fullscreen = True

screen_width, screen_height, area_rect, top_area = recalc_geometry(screen)

# --- ASSETS ---
ASSET_PATH = "game/assets/images/"
checkbox_icon = load_scaled(ASSET_PATH + "Checkbox.png", (26, 26))
pen_img = load_scaled(ASSET_PATH + "pen.png", (130, 130))
gun_img = load_scaled(ASSET_PATH + "gun.png", (110, 110))
bullet_img = load_scaled(ASSET_PATH + "bullet.png", (20, 20))
grenade_img = load_scaled(ASSET_PATH + "grenade.png", (42, 42))
explosion_img = load_scaled(ASSET_PATH + "explosion.png", (160, 160))
sword_img = load_scaled(ASSET_PATH + "sword.png", (80, 80))
slash_img = load_scaled(ASSET_PATH + "slash.png", (200, 30))

AttackAssets = {
    "gun_img": gun_img,
    "bullet_img": bullet_img,
    "grenade_img": grenade_img,
    "explosion_img": explosion_img,
    "sword_img": sword_img,
    "slash_img": slash_img,
}

# --- ENTITIES ---
player = Player(checkbox_icon, screen_width, screen_height)
pen = Pen(pen_img, top_area)

active_attacks = []
projectiles = []
elapsed_time = 0.0
game_over = False


def spawn_attack():
    attack_cls = random.choice(ATTACK_TYPES)
    attack = attack_cls(pen.get_rect(), player.get_rect(), AttackAssets)
    active_attacks.append(attack)


running = True
while running:
    dt = clock.tick(60) / 1000.0
    if not game_over:
        elapsed_time += dt

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
                    screen = pygame.display.set_mode((1280, 900))
                screen_width, screen_height, area_rect, top_area = recalc_geometry(screen)
                player.on_resize(screen_width, screen_height)
                pen.top_area = top_area
                pen.rect.clamp_ip(top_area)
                pen.x, pen.y = pen.rect.center
            if event.key == pygame.K_r and game_over:
                player = Player(checkbox_icon, screen_width, screen_height)
                active_attacks.clear()
                projectiles.clear()
                elapsed_time = 0.0
                game_over = False

    # --- INPUT & PLAYER ---
    if not game_over:
        player.update(dt, area_rect)

    # --- PEN MOVEMENT & ATTACK SPAWNING ---
    pen.update(dt)
    if not game_over and pen.ready_to_attack():
        spawn_attack()
        pen.pick_new_target()

    # --- UPDATE ATTACKS ---
    if not game_over:
        for attack in active_attacks[:]:
            spawned = attack.update(dt, projectiles, player) or []
            if spawned:
                projectiles.extend(spawned)
            if attack.finished:
                active_attacks.remove(attack)

    # --- UPDATE PROJECTILES ---
    if not game_over:
        for proj in projectiles[:]:
            proj.update(dt, player)
            if not proj.active or not player.alive:
                projectiles.remove(proj)

    if not player.alive and not game_over:
        game_over = True
        active_attacks.clear()
        projectiles.clear()

    # --- DRAW ---
    draw_paper_background(screen, area_rect, top_area)

    # labels
    font_small = get_font(22)
    font_big = get_font(30)
    screen.blit(font_small.render("Pencil lane", True, (45, 45, 45)), (top_area.x, top_area.y - 26))
    screen.blit(font_small.render("Dodge zone", True, (45, 45, 45)), (area_rect.x, area_rect.y - 26))

    # HUD
    hud_font = get_font(28, bold=True)
    hp_text = hud_font.render(f"HP {player.health}/{player.max_health}", True, (35, 35, 35))
    screen.blit(hp_text, (32, 26))
    draw_health_bar(screen, 32, 58, player.health, player.max_health)

    time_text = font_big.render(f"{elapsed_time:0.1f}s", True, (50, 50, 50))
    screen.blit(time_text, (screen.get_width() - 150, 28))

    pen.draw(screen)
    for attack in active_attacks:
        attack.draw(screen)
    for proj in projectiles:
        proj.draw(screen)
    player.draw(screen)

    if game_over:
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((245, 240, 230, 210))
        screen.blit(overlay, (0, 0))
        msg = font_big.render("Knocked out!", True, (30, 30, 30))
        prompt = font_small.render("Press R to restart or ESC to quit", True, (50, 50, 50))
        screen.blit(msg, msg.get_rect(center=(screen_width // 2, screen_height // 2 - 16)))
        screen.blit(prompt, prompt.get_rect(center=(screen_width // 2, screen_height // 2 + 20)))

    pygame.display.flip()

pygame.quit()
