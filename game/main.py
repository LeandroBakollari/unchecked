import json
import os
import random
import sys
from datetime import datetime
from pathlib import Path

import pygame

from game.player import Player
from game.pen import Pen
from game.utils import (
    blur_surface,
    draw_hand_text,
    draw_health_bar,
    draw_panel,
    draw_paper_background,
    format_time_mmss,
    load_scaled,
    recalc_geometry,
)

from game.attacks.base import AttackBase
from game.attacks.gun import GunAttack
from game.attacks.grenade import GrenadeAttack
from game.attacks.sword import SwordAttack
from game.attacks.shotgun import ShotgunAttack
from game.attacks.mirror import MirrorAttack
from game.attacks.sniper import SniperAttack
from game.attacks.boomerang import BoomerangAttack
from game.attacks.shuriken import ShurikenAttack
from game.attacks.stuff import StuffAttack

pygame.init()

screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.display.set_caption("Unchecked")
clock = pygame.time.Clock()
fullscreen = True

screen_width, screen_height, area_rect, top_area = recalc_geometry(screen)


def get_base_path():
    """Resolve the correct base path for source runs and bundled executable runs."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def get_scores_path():
    """Store scores in the user's local app-data folder instead of inside the project tree."""
    local_root = os.getenv("LOCALAPPDATA")
    if local_root:
        data_dir = Path(local_root) / "Unchecked"
    else:
        data_dir = Path.home() / ".unchecked"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "scores.json"


BASE_PATH = get_base_path()
ASSET_PATH = BASE_PATH / "game" / "assets" / "images"
SCORES_PATH = get_scores_path()

checkbox_icon = load_scaled(str(ASSET_PATH / "Checkbox.png"), (26, 26))
checkbox_icon_1 = load_scaled(str(ASSET_PATH / "Checkbox1.png"), (26, 26))
checkbox_icon_2 = load_scaled(str(ASSET_PATH / "Checkbox2.png"), (26, 26))
checkbox_icon_3 = load_scaled(str(ASSET_PATH / "Checkbox3.png"), (26, 26))
pen_img = load_scaled(str(ASSET_PATH / "pen.png"), (130, 130))
gun_img = load_scaled(str(ASSET_PATH / "gun.png"), (110, 110))
bullet_img = load_scaled(str(ASSET_PATH / "bullet.png"), (20, 20))
grenade_img = load_scaled(str(ASSET_PATH / "grenade.png"), (42, 42))
explosion_img = load_scaled(str(ASSET_PATH / "explosion.png"), (160, 160))
sword_img = load_scaled(str(ASSET_PATH / "sword.png"), (80, 80))
slash_img = load_scaled(str(ASSET_PATH / "slash.png"), (200, 30))
shotgun_img = load_scaled(str(ASSET_PATH / "shotgun.png"), (150, 90))
mirror_img = load_scaled(str(ASSET_PATH / "mirror.png"), (110, 110))
sniper_img = load_scaled(str(ASSET_PATH / "sniper.png"), (150, 85))
boomerang_img = load_scaled(str(ASSET_PATH / "boomerang.png"), (95, 95))
shuriken_img = load_scaled(str(ASSET_PATH / "shuriken.png"), (78, 78))
shuriken_projectile_img = load_scaled(str(ASSET_PATH / "shuriken.png"), (62, 62))
stuff_img = load_scaled(str(ASSET_PATH / "stuff.png"), (120, 120))
fireball_img = load_scaled(str(ASSET_PATH / "fireball.png"), (54, 54))
audio_icon = load_scaled(str(ASSET_PATH / "audio.png"), (56, 56))
settings_icon = load_scaled(str(ASSET_PATH / "settings.png"), (56, 56))

AttackAssets = {
    "gun_img": gun_img,
    "bullet_img": bullet_img,
    "grenade_img": grenade_img,
    "explosion_img": explosion_img,
    "sword_img": sword_img,
    "slash_img": slash_img,
    "shotgun_img": shotgun_img,
    "mirror_img": mirror_img,
    "sniper_img": sniper_img,
    "boomerang_img": boomerang_img,
    "shuriken_img": shuriken_img,
    "shuriken_projectile_img": shuriken_projectile_img,
    "stuff_img": stuff_img,
    "fireball_img": fireball_img,
}

ATTACK_TYPES = [GunAttack, GrenadeAttack, SwordAttack, ShotgunAttack, MirrorAttack, SniperAttack, BoomerangAttack, ShurikenAttack, StuffAttack]
AttackAssets["attack_classes"] = [GunAttack, GrenadeAttack, SwordAttack, ShotgunAttack, SniperAttack, BoomerangAttack, ShurikenAttack, StuffAttack]

PLAYER_SKINS = {
    "Checkbox": checkbox_icon,
    "Checkbox1": checkbox_icon_1,
    "Checkbox2": checkbox_icon_2,
    "Checkbox3": checkbox_icon_3,
}


def sort_scores(scores):
    """Order runs by survival time first and attack count second."""
    return sorted(scores, key=lambda item: (item.get("time", 0.0), item.get("attacks", 0)), reverse=True)


def load_scores():
    """Load saved runs from disk, tolerating a missing or malformed file."""
    if not SCORES_PATH.exists():
        return []
    try:
        data = json.loads(SCORES_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    if not isinstance(data, list):
        return []
    return sort_scores([item for item in data if isinstance(item, dict)])


def save_scores(scores):
    """Persist the score table to disk."""
    SCORES_PATH.write_text(json.dumps(sort_scores(scores)[:20], indent=2), encoding="utf-8")


def build_home_layout():
    """Create the stacked menu layout shown in the mockup."""
    title_rect = pygame.Rect(0, 0, int(screen_width * 0.52), 76)
    title_rect.center = (screen_width // 2, int(screen_height * 0.14))

    button_width = int(screen_width * 0.29)
    button_height = 62
    button_gap = 12
    start_y = title_rect.bottom + 60

    play_rect = pygame.Rect(0, start_y, button_width, button_height)
    play_rect.centerx = screen_width // 2
    characters_rect = pygame.Rect(play_rect.x, play_rect.bottom + button_gap, button_width, button_height)
    scoreboard_rect = pygame.Rect(play_rect.x, characters_rect.bottom + button_gap, button_width, button_height)

    square_size = 96
    lower_gap = 22
    settings_rect = pygame.Rect(play_rect.centerx + lower_gap // 2, scoreboard_rect.bottom + 12, square_size, square_size)
    audio_rect = pygame.Rect(settings_rect.x - square_size - lower_gap, settings_rect.y, square_size, square_size)

    return {
        "title": title_rect,
        "play": play_rect,
        "characters": characters_rect,
        "scoreboard": scoreboard_rect,
        "audio": audio_rect,
        "settings": settings_rect,
    }


def build_home_modal_rect(width_ratio=0.38, height_ratio=0.44):
    """Create a centered pop-up card for home-page subviews."""
    rect = pygame.Rect(0, 0, int(screen_width * width_ratio), int(screen_height * height_ratio))
    rect.center = (screen_width // 2, screen_height // 2 + 18)
    return rect


def build_game_over_layout():
    """Create the main overlay and modal rectangles for the end screen."""
    modal = pygame.Rect(0, 0, int(screen_width * 0.46), int(screen_height * 0.46))
    modal.center = (screen_width // 2, screen_height // 2)
    button_width = int(modal.width * 0.26)
    button_height = 62
    retry_rect = pygame.Rect(modal.left + 38, modal.bottom - 92, button_width, button_height)
    home_rect = pygame.Rect(retry_rect.right + 18, retry_rect.y, button_width, button_height)
    save_rect = pygame.Rect(modal.right - button_width - 38, modal.centery + 18, button_width, button_height)
    return {
        "modal": modal,
        "retry": retry_rect,
        "home": home_rect,
        "save": save_rect,
    }


def build_save_modal_layout():
    """Create the name-entry modal shown after choosing save score."""
    modal = pygame.Rect(0, 0, int(screen_width * 0.32), int(screen_height * 0.23))
    modal.center = (screen_width // 2, int(screen_height * 0.54))
    input_rect = pygame.Rect(modal.x + 26, modal.y + 78, modal.width - 52, 54)
    save_rect = pygame.Rect(modal.centerx - 80, modal.bottom - 74, 160, 50)
    return {"modal": modal, "input": input_rect, "save": save_rect}


def create_run_state():
    """Create a fresh run state for gameplay or retry."""
    return {
        "player": Player(selected_player_icon, screen_width, screen_height),
        "pen": Pen(pen_img, top_area),
        "active_attacks": [],
        "projectiles": [],
        "elapsed_time": 0.0,
        "attack_count": 0,
        "snapshot": None,
        "result": None,
        "score_saved": False,
        "name_input": "",
    }


def set_mouse_visibility(mode):
    """Show the cursor in menus and overlays, hide it during play."""
    pygame.mouse.set_visible(mode != "playing")


def begin_run():
    """Start a new run from either the menu or retry."""
    global game_state, run_state
    run_state = create_run_state()
    game_state = "playing"
    set_mouse_visibility(game_state)


def return_home(message=""):
    """Go back to the menu and optionally show a short status message."""
    global game_state, toast_message, toast_timer
    game_state = "home"
    toast_message = message
    toast_timer = 2.2 if message else 0.0
    set_mouse_visibility(game_state)


def get_best_time(scores):
    """Return the best saved survival time."""
    if not scores:
        return 0.0
    return max(item.get("time", 0.0) for item in scores)


def register_attack(attack):
    """Add a spawned attack to the active list and count it toward the run total."""
    run_state["active_attacks"].append(attack)
    run_state["attack_count"] += 1


def spawn_attack():
    """Spawn a random attack from the pen's current draw position."""
    attack_cls = random.choice(ATTACK_TYPES)
    attack = attack_cls(run_state["pen"].get_rect(), run_state["player"].get_rect(), AttackAssets)
    register_attack(attack)


def save_current_score():
    """Persist the current run using the typed name, then return to the home screen."""
    global scores
    if not run_state["result"]:
        return

    name = run_state["name_input"].strip() or "Anonymous"
    scores.append(
        {
            "name": name,
            "time": run_state["result"]["time"],
            "attacks": run_state["result"]["attacks"],
            "saved_at": datetime.now().isoformat(timespec="seconds"),
        }
    )
    scores = sort_scores(scores)
    save_scores(scores)
    run_state["score_saved"] = True
    return_home("Score saved")


def draw_game_scene(surface):
    """Render the gameplay screen and the left-side run stats."""
    draw_paper_background(surface, area_rect, top_area)
    draw_hand_text(surface, "Pencil lane", top_area.x, top_area.y - 28, size=24)
    draw_hand_text(surface, "Dodge zone", area_rect.x, area_rect.y - 28, size=24)

    hud_x = max(48, area_rect.left - 180)
    timer_panel = pygame.Rect(hud_x, area_rect.y + 40, 150, 92)
    attacks_panel = pygame.Rect(hud_x, timer_panel.bottom + 18, 150, 92)
    health_panel = pygame.Rect(32, 24, 280, 88)

    draw_panel(surface, timer_panel, label="Time", label_size=24)
    draw_hand_text(surface, format_time_mmss(run_state["elapsed_time"]), timer_panel.centerx, timer_panel.centery + 10, size=34, center=True, bold=True)

    draw_panel(surface, attacks_panel, label="Attacks", label_size=24)
    draw_hand_text(surface, str(run_state["attack_count"]), attacks_panel.centerx, attacks_panel.centery + 10, size=34, center=True, bold=True)

    draw_panel(surface, health_panel)
    draw_hand_text(
        surface,
        f"HP {run_state['player'].health}/{run_state['player'].max_health}",
        health_panel.x + 16,
        health_panel.y + 12,
        size=30,
        bold=True,
    )
    draw_health_bar(surface, health_panel.x + 16, health_panel.y + 46, run_state["player"].health, run_state["player"].max_health, width=240)

    run_state["pen"].draw(surface)
    for attack in run_state["active_attacks"]:
        attack.draw(surface)
    for proj in run_state["projectiles"]:
        proj.draw(surface)
    run_state["player"].draw(surface)


def draw_home(surface):
    """Render the paper-drawn home page with the requested placeholder boxes."""
    layout = build_home_layout()
    background_a = pygame.Rect(int(screen_width * 0.16), int(screen_height * 0.12), int(screen_width * 0.68), 96)
    background_b = pygame.Rect(int(screen_width * 0.28), int(screen_height * 0.34), int(screen_width * 0.44), 320)
    draw_paper_background(surface, background_b, background_a)

    draw_panel(surface, layout["title"], fill=(255, 255, 255, 120))
    draw_hand_text(surface, "Unchecked", layout["title"].centerx, layout["title"].centery, size=58, center=True, bold=True)

    button_fill = (180, 180, 180, 180)
    draw_panel(surface, layout["play"], fill=button_fill, center_label=True, label="Play", label_size=42)
    draw_panel(surface, layout["characters"], fill=button_fill, center_label=True, label="Character", label_size=34)
    draw_panel(surface, layout["scoreboard"], fill=button_fill, center_label=True, label="Score board", label_size=32)
    draw_panel(surface, layout["audio"], fill=button_fill)
    draw_panel(surface, layout["settings"], fill=button_fill)

    audio_rect = audio_icon.get_rect(center=layout["audio"].center)
    settings_rect = settings_icon.get_rect(center=layout["settings"].center)
    surface.blit(audio_icon, audio_rect)
    surface.blit(settings_icon, settings_rect)

    if audio_muted:
        pygame.draw.line(surface, (20, 20, 20), (layout["audio"].x + 12, layout["audio"].bottom - 12), (layout["audio"].right - 12, layout["audio"].y + 12), 4)

    if home_modal == "characters":
        draw_characters_modal(surface)
    elif home_modal == "scoreboard":
        draw_scoreboard_modal(surface)

    if toast_timer > 0.0 and toast_message:
        toast_rect = pygame.Rect(0, 0, 240, 60)
        toast_rect.center = (screen_width // 2, screen_height - 54)
        draw_panel(surface, toast_rect, fill=(255, 248, 220, 185), center_label=True, label=toast_message, label_size=26)


def draw_characters_modal(surface):
    """Show the list of selectable checkbox skins."""
    modal = build_home_modal_rect()
    shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    shade.fill((255, 255, 255, 70))
    surface.blit(shade, (0, 0))
    draw_panel(surface, modal, fill=(255, 252, 245, 235))
    draw_hand_text(surface, "Characters", modal.centerx, modal.y + 34, size=36, center=True, bold=True)

    row_y = modal.y + 88
    row_height = 66
    for skin_name, skin_image in PLAYER_SKINS.items():
        row_rect = pygame.Rect(modal.x + 22, row_y, modal.width - 44, row_height)
        draw_panel(surface, row_rect, fill=(255, 255, 255, 120))
        preview = pygame.transform.scale(skin_image, (36, 36))
        surface.blit(preview, preview.get_rect(center=(row_rect.x + 34, row_rect.centery)))
        draw_hand_text(surface, skin_name, row_rect.x + 68, row_rect.y + 18, size=26)

        radio_center = (row_rect.right - 30, row_rect.centery)
        pygame.draw.circle(surface, (35, 34, 30), radio_center, 12, 2)
        if selected_player_skin == skin_name:
            pygame.draw.circle(surface, (35, 34, 30), radio_center, 6)
        row_y += row_height + 10


def draw_scoreboard_modal(surface):
    """Show the saved score list in a small centered window."""
    modal = build_home_modal_rect(width_ratio=0.34, height_ratio=0.48)
    shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    shade.fill((255, 255, 255, 70))
    surface.blit(shade, (0, 0))
    draw_panel(surface, modal, fill=(255, 252, 245, 235))
    draw_hand_text(surface, "Score board", modal.centerx, modal.y + 34, size=36, center=True, bold=True)

    top_scores = scores[:10]
    if not top_scores:
        draw_hand_text(surface, "No saved scores yet.", modal.centerx, modal.centery, size=26, center=True)
        return

    line_y = modal.y + 82
    for index, item in enumerate(top_scores, start=1):
        line = f"{index}. {item.get('name', 'Anon')}"
        draw_hand_text(surface, line, modal.x + 24, line_y, size=24)
        draw_hand_text(surface, format_time_mmss(item.get("time", 0)), modal.right - 130, line_y, size=24)
        line_y += 32


def draw_game_over_overlay(surface):
    """Render the blurred game over overlay and summary controls."""
    layout = build_game_over_layout()
    if run_state["snapshot"] is None:
        run_state["snapshot"] = blur_surface(surface.copy())

    surface.blit(run_state["snapshot"], (0, 0))
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    overlay.fill((245, 240, 230, 145))
    surface.blit(overlay, (0, 0))

    draw_panel(surface, layout["modal"], fill=(255, 252, 245, 220))
    draw_hand_text(surface, "Game Over", layout["modal"].centerx, layout["modal"].y + 54, size=50, center=True, bold=True)

    if run_state["result"]["new_high_score"]:
        draw_hand_text(surface, "New high score", layout["modal"].centerx, layout["modal"].y + 100, size=28, center=True)

    draw_hand_text(surface, f"Time  {format_time_mmss(run_state['result']['time'])}", layout["modal"].x + 36, layout["modal"].y + 144, size=30)
    draw_hand_text(surface, f"Attacks  {run_state['result']['attacks']}", layout["modal"].x + 36, layout["modal"].y + 184, size=30)

    draw_panel(surface, layout["save"], center_label=True, label="Save score", label_size=24)
    draw_panel(surface, layout["retry"], center_label=True, label="Retry", label_size=28)
    draw_panel(surface, layout["home"], center_label=True, label="Home", label_size=28)


def draw_save_modal(surface):
    """Render the name-entry prompt on top of the game over overlay."""
    layout = build_save_modal_layout()
    shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    shade.fill((255, 255, 255, 70))
    surface.blit(shade, (0, 0))

    draw_panel(surface, layout["modal"], fill=(255, 252, 245, 235))
    draw_hand_text(surface, "Save score", layout["modal"].centerx, layout["modal"].y + 32, size=34, center=True, bold=True)
    draw_panel(surface, layout["input"], fill=(255, 255, 255, 170))
    entry_text = run_state["name_input"] or "Type your name"
    entry_color = (35, 34, 30) if run_state["name_input"] else (120, 112, 100)
    draw_hand_text(surface, entry_text, layout["input"].x + 14, layout["input"].y + 12, size=28, color=entry_color)
    draw_panel(surface, layout["save"], center_label=True, label="Save", label_size=26)


scores = load_scores()
game_state = "home"
selected_player_skin = "Checkbox"
selected_player_icon = PLAYER_SKINS[selected_player_skin]
audio_muted = False
home_modal = None
run_state = create_run_state()
toast_message = ""
toast_timer = 0.0
set_mouse_visibility(game_state)

running = True
while running:
    dt = clock.tick(60) / 1000.0
    if toast_timer > 0.0:
        toast_timer = max(0.0, toast_timer - dt)
        if toast_timer <= 0.0:
            toast_message = ""

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if game_state == "save_score":
                    game_state = "game_over"
                    set_mouse_visibility(game_state)
                elif game_state == "home" and home_modal is not None:
                    home_modal = None
                else:
                    running = False

            elif event.key == pygame.K_F11:
                fullscreen = not fullscreen
                if fullscreen:
                    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                else:
                    screen = pygame.display.set_mode((1280, 900))
                screen_width, screen_height, area_rect, top_area = recalc_geometry(screen)
                run_state["snapshot"] = None
                run_state["player"].on_resize(screen_width, screen_height)
                run_state["pen"].top_area = top_area
                run_state["pen"].rect.clamp_ip(top_area)
                run_state["pen"].x, run_state["pen"].y = run_state["pen"].rect.center

            elif game_state == "home" and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                begin_run()

            elif game_state == "save_score" and event.key == pygame.K_RETURN:
                save_current_score()

            elif game_state == "save_score" and event.key == pygame.K_BACKSPACE:
                run_state["name_input"] = run_state["name_input"][:-1]

        elif event.type == pygame.TEXTINPUT and game_state == "save_score":
            if len(run_state["name_input"]) < 18:
                run_state["name_input"] += event.text

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            if game_state == "home":
                home_layout = build_home_layout()
                if home_modal == "characters":
                    modal = build_home_modal_rect()
                    if not modal.collidepoint(mouse_pos):
                        home_modal = None
                    else:
                        row_y = modal.y + 88
                        row_height = 66
                        for skin_name in PLAYER_SKINS:
                            row_rect = pygame.Rect(modal.x + 22, row_y, modal.width - 44, row_height)
                            if row_rect.collidepoint(mouse_pos):
                                selected_player_skin = skin_name
                                selected_player_icon = PLAYER_SKINS[skin_name]
                                home_modal = None
                                break
                            row_y += row_height + 10
                elif home_modal == "scoreboard":
                    modal = build_home_modal_rect(width_ratio=0.34, height_ratio=0.48)
                    if not modal.collidepoint(mouse_pos):
                        home_modal = None
                elif home_layout["play"].collidepoint(mouse_pos):
                    begin_run()
                elif home_layout["characters"].collidepoint(mouse_pos):
                    home_modal = "characters"
                elif home_layout["scoreboard"].collidepoint(mouse_pos):
                    home_modal = "scoreboard"
                elif home_layout["audio"].collidepoint(mouse_pos):
                    audio_muted = not audio_muted

            elif game_state == "game_over":
                overlay_layout = build_game_over_layout()
                if overlay_layout["retry"].collidepoint(mouse_pos):
                    begin_run()
                elif overlay_layout["home"].collidepoint(mouse_pos):
                    return_home()
                elif overlay_layout["save"].collidepoint(mouse_pos) and not run_state["score_saved"]:
                    game_state = "save_score"
                    set_mouse_visibility(game_state)

            elif game_state == "save_score":
                save_layout = build_save_modal_layout()
                if save_layout["save"].collidepoint(mouse_pos):
                    save_current_score()

    if game_state == "playing":
        run_state["elapsed_time"] += dt
        run_state["player"].update(dt, area_rect)
        run_state["pen"].update(dt)

        if run_state["pen"].ready_to_attack():
            spawn_attack()
            run_state["pen"].pick_new_target()

        for attack in run_state["active_attacks"][:]:
            spawned = attack.update(dt, run_state["projectiles"], run_state["player"]) or []
            for obj in spawned:
                if isinstance(obj, AttackBase):
                    register_attack(obj)
                else:
                    run_state["projectiles"].append(obj)
            if attack.finished:
                run_state["active_attacks"].remove(attack)

        for proj in run_state["projectiles"][:]:
            proj.update(dt, run_state["player"])
            if not proj.active or not run_state["player"].alive:
                run_state["projectiles"].remove(proj)

        if not run_state["player"].alive:
            best_time = get_best_time(scores)
            run_state["result"] = {
                "time": run_state["elapsed_time"],
                "attacks": run_state["attack_count"],
                "new_high_score": run_state["elapsed_time"] > best_time,
            }
            game_state = "game_over"
            run_state["snapshot"] = None
            set_mouse_visibility(game_state)

    if game_state == "home":
        draw_home(screen)
    else:
        draw_game_scene(screen)
        if game_state in ("game_over", "save_score"):
            draw_game_over_overlay(screen)
            if game_state == "save_score":
                draw_save_modal(screen)

    pygame.display.flip()

pygame.quit()
