import argparse
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
    INK,
    blur_surface,
    clamp,
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
from game.attacks.pool import PoolAttack


def parse_runtime_args():
    parser = argparse.ArgumentParser(description="Unchecked")
    parser.add_argument("--debug-hitboxes", action="store_true", help="draw gameplay collision hitboxes")
    parser.add_argument("--windowed", action="store_true", help="start in a resizable window")
    parser.add_argument("--width", type=int, default=1280, help="window width when --windowed is used")
    parser.add_argument("--height", type=int, default=850, help="window height when --windowed is used")
    return parser.parse_known_args()[0]


runtime_args = parse_runtime_args()

pygame.init()

windowed_size = (max(720, runtime_args.width), max(520, runtime_args.height))
fullscreen = not runtime_args.windowed
debug_hitboxes = runtime_args.debug_hitboxes

if fullscreen:
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
else:
    screen = pygame.display.set_mode(windowed_size, pygame.RESIZABLE)
pygame.display.set_caption("Unchecked")
clock = pygame.time.Clock()

screen_width, screen_height, area_rect, top_area = recalc_geometry(screen)


def get_base_path():
    """Resolve the correct base path for source runs and bundled executable runs."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def get_data_dir():
    """Store user-created data outside the project tree."""
    local_root = os.getenv("LOCALAPPDATA")
    if local_root:
        data_dir = Path(local_root) / "Unchecked"
    else:
        data_dir = Path.home() / ".unchecked"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_scores_path():
    """Store scores in the user's local app-data folder instead of inside the project tree."""
    return DATA_DIR / "scores.json"


def get_custom_character_path():
    """Legacy path used by the first single-custom-character version."""
    return DATA_DIR / "custom_character.png"


def get_custom_characters_dir():
    """Store named custom character PNGs and their index locally."""
    custom_dir = DATA_DIR / "characters"
    custom_dir.mkdir(parents=True, exist_ok=True)
    return custom_dir


BASE_PATH = get_base_path()
DATA_DIR = get_data_dir()
ASSET_PATH = BASE_PATH / "game" / "assets" / "images"
SCORES_PATH = get_scores_path()
CUSTOM_CHARACTER_PATH = get_custom_character_path()
CUSTOM_CHARACTERS_DIR = get_custom_characters_dir()
CUSTOM_CHARACTER_INDEX_PATH = CUSTOM_CHARACTERS_DIR / "characters.json"
PLAYER_ICON_SIZE = (26, 26)
CUSTOM_CHARACTER_SIZE = (64, 64)
CUSTOM_SKIN_PREFIX = "custom:"
RANDOM_SKIN_NAME = "Random"
CUSTOM_BRUSH_RADIUS = 3
MAX_CHARACTER_NAME_LENGTH = 18
CHARACTER_COLORS = [
    ("Black", (35, 34, 30)),
    ("White", (255, 255, 255)),
    ("Red", (220, 62, 58)),
    ("Orange", (235, 130, 40)),
    ("Yellow", (238, 198, 58)),
    ("Green", (70, 168, 86)),
    ("Blue", (58, 118, 214)),
    ("Purple", (139, 86, 196)),
    ("Pink", (224, 95, 158)),
    ("Brown", (132, 82, 52)),
    ("Gray", (120, 120, 120)),
    ("Cyan", (58, 176, 190)),
]

checkbox_icon = load_scaled(str(ASSET_PATH / "Checkbox.png"), PLAYER_ICON_SIZE)
checkbox_icon_1 = load_scaled(str(ASSET_PATH / "Checkbox1.png"), PLAYER_ICON_SIZE)
checkbox_icon_2 = load_scaled(str(ASSET_PATH / "Checkbox2.png"), PLAYER_ICON_SIZE)
checkbox_icon_3 = load_scaled(str(ASSET_PATH / "Checkbox3.png"), PLAYER_ICON_SIZE)
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
pool_ball_img = load_scaled(str(ASSET_PATH / "poolBall.png"), (42, 42))
pool_cue_img = load_scaled(str(ASSET_PATH / "poolCue.png"), (124, 124))
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
    "pool_ball_img": pool_ball_img,
    "pool_cue_img": pool_cue_img,
}

ATTACK_TYPES = [GunAttack, GrenadeAttack, SwordAttack, ShotgunAttack, MirrorAttack, SniperAttack, BoomerangAttack, ShurikenAttack, StuffAttack, PoolAttack]
# ATTACK_TYPES = [PoolAttack]

AttackAssets["attack_classes"] = [GunAttack, GrenadeAttack, SwordAttack, ShotgunAttack, SniperAttack, BoomerangAttack, ShurikenAttack, StuffAttack, PoolAttack]


def create_blank_custom_character():
    """Create a transparent drawing surface for the custom player skin."""
    return pygame.Surface(CUSTOM_CHARACTER_SIZE, pygame.SRCALPHA)


def custom_skin_key(character_id):
    return f"{CUSTOM_SKIN_PREFIX}{character_id}"


def is_custom_skin_key(skin_key):
    return isinstance(skin_key, str) and skin_key.startswith(CUSTOM_SKIN_PREFIX)


def custom_id_from_skin_key(skin_key):
    return skin_key[len(CUSTOM_SKIN_PREFIX):]


def custom_character_has_ink(surface):
    """Return true when the custom character has at least one visible pixel."""
    return pygame.mask.from_surface(surface).count() > 0


def sanitize_custom_character_id(name):
    """Create a filesystem-friendly id from a user-facing character name."""
    cleaned = []
    for char in name.lower().strip():
        if char.isalnum():
            cleaned.append(char)
        elif char in (" ", "-", "_"):
            cleaned.append("_")
    slug = "".join(cleaned).strip("_")
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug or "custom"


def unique_custom_character_id(name, existing_id=None):
    """Create a custom character id that does not collide with existing records."""
    base_id = sanitize_custom_character_id(name)
    used_ids = {record.get("id") for record in custom_character_records}
    if existing_id:
        used_ids.discard(existing_id)
    character_id = base_id
    index = 2
    while character_id in used_ids:
        character_id = f"{base_id}_{index}"
        index += 1
    return character_id


def normalize_custom_character_record(item):
    """Validate a saved custom character record from disk."""
    if not isinstance(item, dict):
        return None

    character_id = str(item.get("id", "")).strip()
    name = str(item.get("name", "")).strip()
    file_name = str(item.get("file", "")).strip()
    if not character_id or not name or not file_name:
        return None

    return {
        "id": character_id,
        "name": name[:MAX_CHARACTER_NAME_LENGTH],
        "file": Path(file_name).name,
    }


def load_custom_character_records():
    """Load the index of named custom characters."""
    if not CUSTOM_CHARACTER_INDEX_PATH.exists():
        return []
    try:
        data = json.loads(CUSTOM_CHARACTER_INDEX_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    if not isinstance(data, list):
        return []

    records = []
    seen_ids = set()
    for item in data:
        record = normalize_custom_character_record(item)
        if record is None or record["id"] in seen_ids:
            continue
        records.append(record)
        seen_ids.add(record["id"])
    return records


def save_custom_character_records():
    """Persist the custom character index."""
    CUSTOM_CHARACTER_INDEX_PATH.write_text(json.dumps(custom_character_records, indent=2), encoding="utf-8")


def load_custom_character_surface_from_path(path):
    """Load and normalize a custom character PNG."""
    try:
        surface = pygame.image.load(str(path)).convert_alpha()
    except (OSError, pygame.error):
        return None

    if surface.get_size() != CUSTOM_CHARACTER_SIZE:
        surface = pygame.transform.smoothscale(surface, CUSTOM_CHARACTER_SIZE)
    return surface


def make_custom_character_icon(surface):
    """Scale the saved drawing down to the in-game player size."""
    return pygame.transform.smoothscale(surface, PLAYER_ICON_SIZE)


def migrate_legacy_custom_character():
    """Import the first single custom-character save into the named library."""
    if custom_character_records or not CUSTOM_CHARACTER_PATH.exists():
        return

    surface = load_custom_character_surface_from_path(CUSTOM_CHARACTER_PATH)
    if surface is None or not custom_character_has_ink(surface):
        return

    character_id = unique_custom_character_id("Custom")
    file_name = f"{character_id}.png"
    try:
        pygame.image.save(surface, str(CUSTOM_CHARACTERS_DIR / file_name))
    except (OSError, pygame.error):
        return

    custom_character_records.append({"id": character_id, "name": "Custom", "file": file_name})
    save_custom_character_records()


BUILTIN_PLAYER_SKINS = {
    "Checkbox": checkbox_icon,
    "Checkbox1": checkbox_icon_1,
    "Checkbox2": checkbox_icon_2,
    "Checkbox3": checkbox_icon_3,
}
PLAYER_SKINS = BUILTIN_PLAYER_SKINS.copy()
custom_character_records = load_custom_character_records()
custom_character_surfaces = {}


def rebuild_player_skins():
    """Refresh selectable player skins from built-ins plus saved custom characters."""
    global PLAYER_SKINS, custom_character_surfaces, custom_character_records
    PLAYER_SKINS = BUILTIN_PLAYER_SKINS.copy()
    custom_character_surfaces = {}
    valid_records = []

    for record in custom_character_records:
        surface = load_custom_character_surface_from_path(CUSTOM_CHARACTERS_DIR / record["file"])
        if surface is None or not custom_character_has_ink(surface):
            continue

        valid_records.append(record)
        custom_character_surfaces[record["id"]] = surface
        PLAYER_SKINS[custom_skin_key(record["id"])] = make_custom_character_icon(surface)

    if len(valid_records) != len(custom_character_records):
        custom_character_records = valid_records
        save_custom_character_records()


migrate_legacy_custom_character()
rebuild_player_skins()
custom_character_draft = create_blank_custom_character()
custom_character_name_input = ""
editing_custom_character_id = None
selected_draw_color = CHARACTER_COLORS[0][1]


def get_custom_character_record(character_id):
    for record in custom_character_records:
        if record["id"] == character_id:
            return record
    return None


def get_skin_label(skin_key):
    if skin_key == RANDOM_SKIN_NAME:
        return RANDOM_SKIN_NAME
    if is_custom_skin_key(skin_key):
        record = get_custom_character_record(custom_id_from_skin_key(skin_key))
        return record["name"] if record else "Custom"
    return skin_key


def get_selectable_skin_keys():
    return [RANDOM_SKIN_NAME, *PLAYER_SKINS.keys()]


def get_player_icon_for_run():
    if selected_player_skin == RANDOM_SKIN_NAME:
        return random.choice(list(PLAYER_SKINS.values()))
    return PLAYER_SKINS.get(selected_player_skin, checkbox_icon)


def select_player_skin(skin_key):
    """Select a built-in, custom, or random player skin."""
    global selected_player_skin, selected_player_icon
    if skin_key == RANDOM_SKIN_NAME:
        selected_player_skin = RANDOM_SKIN_NAME
        selected_player_icon = checkbox_icon
        return True
    if skin_key not in PLAYER_SKINS:
        return False
    selected_player_skin = skin_key
    selected_player_icon = PLAYER_SKINS[skin_key]
    return True


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


def bounded_int(value, min_value, max_value):
    """Clamp layout dimensions while tolerating very small windows."""
    max_value = max(1, int(max_value))
    min_value = min(int(min_value), max_value)
    return int(clamp(value, min_value, max_value))


def get_ui_scale():
    """Scale menu controls from the smaller screen dimension so laptop panels stay contained."""
    return clamp(min(screen_width / 1366, screen_height / 768), 0.72, 1.08)


def build_home_layout():
    """Create the stacked menu layout shown in the mockup."""
    scale = get_ui_scale()
    outer_margin = bounded_int(screen_width * 0.045, 28, 72)
    title_width = bounded_int(screen_width * 0.52, 320, screen_width - outer_margin * 2)
    title_height = bounded_int(76 * scale, 54, 78)
    title_rect = pygame.Rect(0, 0, title_width, title_height)
    title_rect.center = (screen_width // 2, bounded_int(screen_height * 0.14, 58, screen_height - 36))

    button_width = bounded_int(screen_width * 0.29, 250, min(430, screen_width - outer_margin * 2))
    button_height = bounded_int(62 * scale, 48, 64)
    button_gap = bounded_int(12 * scale, 8, 14)
    square_size = bounded_int(96 * scale, 58, 96)
    lower_gap = bounded_int(22 * scale, 12, 22)
    icon_gap = bounded_int(12 * scale, 8, 12)

    stack_height = button_height * 3 + button_gap * 2 + icon_gap + square_size
    preferred_start_y = title_rect.bottom + bounded_int(54 * scale, 18, 60)
    max_bottom = screen_height - bounded_int(26 * scale, 18, 34)
    start_y = min(preferred_start_y, max_bottom - stack_height)
    start_y = max(title_rect.bottom + bounded_int(12 * scale, 8, 18), start_y)

    play_rect = pygame.Rect(0, start_y, button_width, button_height)
    play_rect.centerx = screen_width // 2
    characters_rect = pygame.Rect(play_rect.x, play_rect.bottom + button_gap, button_width, button_height)
    scoreboard_rect = pygame.Rect(play_rect.x, characters_rect.bottom + button_gap, button_width, button_height)

    pair_width = square_size * 2 + lower_gap
    icon_y = scoreboard_rect.bottom + icon_gap
    audio_rect = pygame.Rect((screen_width - pair_width) // 2, icon_y, square_size, square_size)
    settings_rect = pygame.Rect(audio_rect.right + lower_gap, icon_y, square_size, square_size)

    return {
        "title": title_rect,
        "play": play_rect,
        "characters": characters_rect,
        "scoreboard": scoreboard_rect,
        "audio": audio_rect,
        "settings": settings_rect,
    }


def build_home_modal_rect(width_ratio=0.38, height_ratio=0.44, min_width=340, min_height=360):
    """Create a centered pop-up card for home-page subviews."""
    margin = bounded_int(min(screen_width, screen_height) * 0.055, 24, 56)
    rect = pygame.Rect(
        0,
        0,
        bounded_int(screen_width * width_ratio, min_width, screen_width - margin * 2),
        bounded_int(screen_height * height_ratio, min_height, screen_height - margin * 2),
    )
    rect.center = (screen_width // 2, screen_height // 2 + 18)
    return rect


def build_characters_modal_layout():
    """Create selectable character rows plus custom edit/delete controls."""
    modal = build_home_modal_rect(width_ratio=0.54, height_ratio=0.72, min_width=470, min_height=520)
    scale = get_ui_scale()
    button_height = bounded_int(52 * scale, 42, 54)
    new_rect = pygame.Rect(modal.x + 22, modal.bottom - 22 - button_height, modal.width - 44, button_height)

    skin_keys = get_selectable_skin_keys()
    row_top = modal.y + bounded_int(84 * scale, 70, 90)
    row_gap = bounded_int(8 * scale, 6, 10)
    row_height = bounded_int(54 * scale, 46, 58)
    available_height = max(1, new_rect.y - row_top - 16)
    visible_count = max(1, int((available_height + row_gap) // (row_height + row_gap)))
    max_scroll = max(0, len(skin_keys) - visible_count)
    scroll = int(clamp(character_list_scroll, 0, max_scroll))

    edit_width = bounded_int(54 * scale, 48, 58)
    delete_width = bounded_int(54 * scale, 48, 58)
    action_height = bounded_int(36 * scale, 30, 38)

    rows = []
    row_y = row_top
    for skin_key in skin_keys[scroll: scroll + visible_count]:
        row_rect = pygame.Rect(modal.x + 22, row_y, modal.width - 44, row_height)
        edit_rect = None
        delete_rect = None
        select_rect = row_rect
        if is_custom_skin_key(skin_key):
            delete_rect = pygame.Rect(row_rect.right - delete_width - 10, 0, delete_width, action_height)
            delete_rect.centery = row_rect.centery
            edit_rect = pygame.Rect(delete_rect.x - edit_width - 8, 0, edit_width, action_height)
            edit_rect.centery = row_rect.centery
            select_rect = pygame.Rect(row_rect.x, row_rect.y, edit_rect.x - row_rect.x - 8, row_rect.height)
        rows.append(
            {
                "skin": skin_key,
                "rect": row_rect,
                "select": select_rect,
                "edit": edit_rect,
                "delete": delete_rect,
            }
        )
        row_y += row_height + row_gap

    return {
        "modal": modal,
        "rows": rows,
        "new": new_rect,
        "scroll": scroll,
        "max_scroll": max_scroll,
        "total": len(skin_keys),
        "visible_count": visible_count,
    }


def build_draw_character_layout():
    """Create the named custom-character drawing surface and controls."""
    modal = build_home_modal_rect(width_ratio=0.58, height_ratio=0.80, min_width=560, min_height=610)
    scale = get_ui_scale()
    button_height = bounded_int(50 * scale, 42, 52)
    button_gap = bounded_int(12 * scale, 8, 14)
    button_y = modal.bottom - 24 - button_height
    button_width = max(86, (modal.width - 44 - button_gap * 2) // 3)

    back_rect = pygame.Rect(modal.x + 22, button_y, button_width, button_height)
    clear_rect = pygame.Rect(back_rect.right + button_gap, button_y, button_width, button_height)
    save_rect = pygame.Rect(clear_rect.right + button_gap, button_y, button_width, button_height)

    input_height = bounded_int(48 * scale, 42, 50)
    input_rect = pygame.Rect(modal.x + 28, modal.y + bounded_int(72 * scale, 62, 80), modal.width - 56, input_height)

    swatch_size = bounded_int(28 * scale, 22, 30)
    swatch_gap = bounded_int(10 * scale, 7, 10)
    swatches_per_row = min(6, max(4, (modal.width - 80 + swatch_gap) // (swatch_size + swatch_gap)))
    swatches = []
    palette_top = input_rect.bottom + bounded_int(16 * scale, 10, 18)
    for index, (label, color) in enumerate(CHARACTER_COLORS):
        row = index // swatches_per_row
        col = index % swatches_per_row
        row_count = min(swatches_per_row, len(CHARACTER_COLORS) - row * swatches_per_row)
        row_width = row_count * swatch_size + (row_count - 1) * swatch_gap
        swatch_x = modal.centerx - row_width // 2 + col * (swatch_size + swatch_gap)
        swatch_y = palette_top + row * (swatch_size + swatch_gap)
        swatches.append({"label": label, "color": color, "rect": pygame.Rect(swatch_x, swatch_y, swatch_size, swatch_size)})

    palette_bottom = max(item["rect"].bottom for item in swatches)
    canvas_top = palette_bottom + bounded_int(20 * scale, 14, 22)
    canvas_bottom = button_y - bounded_int(24 * scale, 16, 26)
    canvas_side = bounded_int(min(modal.width - 92, canvas_bottom - canvas_top), 160, min(330, modal.width - 56))
    canvas_rect = pygame.Rect(0, canvas_top, canvas_side, canvas_side)
    canvas_rect.centerx = modal.centerx

    return {
        "modal": modal,
        "input": input_rect,
        "swatches": swatches,
        "canvas": canvas_rect,
        "back": back_rect,
        "clear": clear_rect,
        "save": save_rect,
    }


def build_game_over_layout():
    """Create the main overlay and modal rectangles for the end screen."""
    scale = get_ui_scale()
    modal = pygame.Rect(
        0,
        0,
        bounded_int(screen_width * 0.46, 440, screen_width - 72),
        bounded_int(screen_height * 0.48, 340, screen_height - 72),
    )
    modal.center = (screen_width // 2, screen_height // 2)
    gap = bounded_int(18 * scale, 10, 20)
    margin = bounded_int(modal.width * 0.075, 24, 38)
    button_height = bounded_int(60 * scale, 46, 62)
    button_width = max(90, (modal.width - margin * 2 - gap * 2) // 3)
    button_y = modal.bottom - margin - button_height
    retry_rect = pygame.Rect(modal.left + margin, button_y, button_width, button_height)
    home_rect = pygame.Rect(retry_rect.right + gap, button_y, button_width, button_height)
    save_rect = pygame.Rect(home_rect.right + gap, button_y, button_width, button_height)
    return {
        "modal": modal,
        "retry": retry_rect,
        "home": home_rect,
        "save": save_rect,
    }


def build_save_modal_layout():
    """Create the name-entry modal shown after choosing save score."""
    scale = get_ui_scale()
    modal = pygame.Rect(
        0,
        0,
        bounded_int(screen_width * 0.34, 320, screen_width - 72),
        bounded_int(screen_height * 0.25, 210, screen_height - 72),
    )
    modal.center = (screen_width // 2, int(screen_height * 0.54))
    input_height = bounded_int(54 * scale, 44, 54)
    save_width = min(170, modal.width - 52)
    save_height = bounded_int(50 * scale, 42, 50)
    input_rect = pygame.Rect(modal.x + 26, modal.y + bounded_int(78 * scale, 64, 82), modal.width - 52, input_height)
    save_rect = pygame.Rect(modal.centerx - save_width // 2, modal.bottom - 24 - save_height, save_width, save_height)
    return {"modal": modal, "input": input_rect, "save": save_rect}


def create_run_state():
    """Create a fresh run state for gameplay or retry."""
    return {
        "player": Player(get_player_icon_for_run(), screen_width, screen_height),
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


def refresh_screen_layout(new_screen):
    """Recalculate geometry after toggling fullscreen or resizing the debug window."""
    global screen, screen_width, screen_height, area_rect, top_area
    screen = new_screen
    screen_width, screen_height, area_rect, top_area = recalc_geometry(screen)

    if "run_state" not in globals():
        return

    run_state["snapshot"] = None
    run_state["player"].on_resize(screen_width, screen_height)
    run_state["pen"].top_area = top_area
    run_state["pen"].rect.clamp_ip(top_area)
    run_state["pen"].x, run_state["pen"].y = run_state["pen"].rect.center


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


def show_toast(message, duration=2.2):
    """Show a short home-screen status message."""
    global toast_message, toast_timer
    toast_message = message
    toast_timer = duration if message else 0.0


def open_custom_character_editor():
    """Start a blank custom character drawing."""
    open_custom_character_record(None)


def open_custom_character_record(character_id):
    """Start editing a blank or saved custom character drawing."""
    global home_modal, custom_character_draft, custom_character_name_input, editing_custom_character_id
    global drawing_custom_character, custom_draw_last_point, selected_draw_color
    editing_custom_character_id = character_id
    selected_draw_color = CHARACTER_COLORS[0][1]
    drawing_custom_character = False
    custom_draw_last_point = None

    record = get_custom_character_record(character_id) if character_id else None
    if record:
        custom_character_draft = custom_character_surfaces.get(character_id, create_blank_custom_character()).copy()
        custom_character_name_input = record["name"]
    else:
        custom_character_draft = create_blank_custom_character()
        custom_character_name_input = ""

    home_modal = "draw_character"


def canvas_to_custom_character_point(mouse_pos, canvas_rect):
    """Map a screen-space mouse point into the saved custom character surface."""
    local_x = (mouse_pos[0] - canvas_rect.x) / max(1, canvas_rect.width)
    local_y = (mouse_pos[1] - canvas_rect.y) / max(1, canvas_rect.height)
    return (
        int(clamp(local_x * CUSTOM_CHARACTER_SIZE[0], 0, CUSTOM_CHARACTER_SIZE[0] - 1)),
        int(clamp(local_y * CUSTOM_CHARACTER_SIZE[1], 0, CUSTOM_CHARACTER_SIZE[1] - 1)),
    )


def draw_on_custom_character_draft(mouse_pos, continue_stroke=False):
    """Draw the selected ink color onto the custom character draft."""
    global custom_draw_last_point
    canvas_rect = build_draw_character_layout()["canvas"]
    if not canvas_rect.collidepoint(mouse_pos):
        custom_draw_last_point = None
        return False

    point = canvas_to_custom_character_point(mouse_pos, canvas_rect)
    if continue_stroke and custom_draw_last_point is not None:
        pygame.draw.line(custom_character_draft, selected_draw_color, custom_draw_last_point, point, CUSTOM_BRUSH_RADIUS * 2)
    pygame.draw.circle(custom_character_draft, selected_draw_color, point, CUSTOM_BRUSH_RADIUS)
    custom_draw_last_point = point
    return True


def clear_custom_character_draft():
    """Clear the in-progress drawing without deleting the saved PNG."""
    global custom_draw_last_point
    custom_character_draft.fill((0, 0, 0, 0))
    custom_draw_last_point = None


def save_custom_character():
    """Persist the custom character draft and select it for the next run."""
    global selected_player_skin, selected_player_icon, home_modal
    global drawing_custom_character, custom_draw_last_point
    global editing_custom_character_id

    name = custom_character_name_input.strip()
    if not name:
        show_toast("Name it")
        return
    if not custom_character_has_ink(custom_character_draft):
        show_toast("Draw first")
        return

    record = get_custom_character_record(editing_custom_character_id) if editing_custom_character_id else None
    created_record = False
    if record is None:
        character_id = unique_custom_character_id(name)
        record = {"id": character_id, "name": name[:MAX_CHARACTER_NAME_LENGTH], "file": f"{character_id}.png"}
        custom_character_records.append(record)
        created_record = True
    else:
        character_id = record["id"]
        record["name"] = name[:MAX_CHARACTER_NAME_LENGTH]

    try:
        pygame.image.save(custom_character_draft, str(CUSTOM_CHARACTERS_DIR / record["file"]))
    except (OSError, pygame.error):
        if created_record:
            custom_character_records.remove(record)
        show_toast("Save failed")
        return

    save_custom_character_records()
    rebuild_player_skins()
    selected_player_skin = custom_skin_key(character_id)
    selected_player_icon = PLAYER_SKINS.get(selected_player_skin, checkbox_icon)
    editing_custom_character_id = character_id
    home_modal = "characters"
    drawing_custom_character = False
    custom_draw_last_point = None
    show_toast("Character saved")


def delete_custom_character(character_id):
    """Delete a saved custom character and remove it from the character picker."""
    global custom_character_records, selected_player_skin, selected_player_icon
    record = get_custom_character_record(character_id)
    if record is None:
        return

    try:
        (CUSTOM_CHARACTERS_DIR / record["file"]).unlink(missing_ok=True)
    except OSError:
        pass

    custom_character_records = [item for item in custom_character_records if item["id"] != character_id]
    save_custom_character_records()
    rebuild_player_skins()

    if selected_player_skin == custom_skin_key(character_id):
        selected_player_skin = "Checkbox"
        selected_player_icon = PLAYER_SKINS[selected_player_skin]
    show_toast("Character deleted")


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
    if debug_hitboxes:
        draw_debug_hitboxes(surface)


def draw_home(surface):
    """Render the paper-drawn home page with the requested placeholder boxes."""
    layout = build_home_layout()
    background_a = layout["title"].inflate(48, 24)
    background_b = layout["play"].union(layout["settings"]).union(layout["audio"]).inflate(44, 36)
    draw_paper_background(surface, background_b, background_a)

    draw_panel(surface, layout["title"], fill=(255, 255, 255, 120))
    draw_hand_text(
        surface,
        "Unchecked",
        layout["title"].centerx,
        layout["title"].centery,
        size=58,
        center=True,
        bold=True,
        max_width=layout["title"].width - 24,
        max_height=layout["title"].height - 12,
    )

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
    elif home_modal == "draw_character":
        draw_custom_character_modal(surface)
    elif home_modal == "scoreboard":
        draw_scoreboard_modal(surface)

    if toast_timer > 0.0 and toast_message:
        toast_rect = pygame.Rect(0, 0, 240, 60)
        toast_rect.center = (screen_width // 2, screen_height - 54)
        draw_panel(surface, toast_rect, fill=(255, 248, 220, 185), center_label=True, label=toast_message, label_size=26)


def draw_characters_modal(surface):
    """Show selectable built-in, random, and saved custom skins."""
    layout = build_characters_modal_layout()
    modal = layout["modal"]
    shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    shade.fill((255, 255, 255, 70))
    surface.blit(shade, (0, 0))
    draw_panel(surface, modal, fill=(255, 252, 245, 235))
    draw_hand_text(surface, "Characters", modal.centerx, modal.y + 34, size=36, center=True, bold=True)

    for row in layout["rows"]:
        skin_key = row["skin"]
        row_rect = row["rect"]
        draw_panel(surface, row_rect, fill=(255, 255, 255, 120))
        preview_size = min(36, row_rect.height - 10)
        preview_rect = pygame.Rect(0, 0, preview_size, preview_size)
        preview_rect.center = (row_rect.x + 34, row_rect.centery)
        if skin_key == RANDOM_SKIN_NAME:
            pygame.draw.rect(surface, (255, 255, 255), preview_rect, border_radius=4)
            pygame.draw.rect(surface, INK, preview_rect, 2, border_radius=4)
            draw_hand_text(surface, "?", preview_rect.centerx, preview_rect.centery, size=28, center=True, bold=True)
        else:
            preview = pygame.transform.scale(PLAYER_SKINS[skin_key], (preview_size, preview_size))
            surface.blit(preview, preview_rect)

        text_y = row_rect.y + max(8, (row_rect.height - 28) // 2)
        text_right = row["edit"].x - 10 if row["edit"] else row_rect.right - 64
        draw_hand_text(surface, get_skin_label(skin_key), row_rect.x + 68, text_y, size=26, max_width=text_right - row_rect.x - 68)

        if row["edit"]:
            draw_panel(surface, row["edit"], fill=(245, 245, 238, 170), center_label=True, label="Edit", label_size=18)
            draw_panel(surface, row["delete"], fill=(255, 232, 226, 185), center_label=True, label="Del", label_size=18)
        else:
            radio_center = (row_rect.right - 30, row_rect.centery)
            pygame.draw.circle(surface, (35, 34, 30), radio_center, 12, 2)
            if selected_player_skin == skin_key:
                pygame.draw.circle(surface, (35, 34, 30), radio_center, 6)

        if row["edit"] and selected_player_skin == skin_key:
            radio_center = (row["edit"].x - 18, row_rect.centery)
            pygame.draw.circle(surface, (35, 34, 30), radio_center, 10, 2)
            pygame.draw.circle(surface, (35, 34, 30), radio_center, 5)

    if layout["max_scroll"] > 0:
        bar = pygame.Rect(modal.right - 18, layout["rows"][0]["rect"].top, 5, layout["rows"][-1]["rect"].bottom - layout["rows"][0]["rect"].top)
        pygame.draw.rect(surface, (205, 200, 190), bar, border_radius=2)
        thumb_height = max(18, int(bar.height * layout["visible_count"] / layout["total"]))
        thumb_y = bar.y + int((bar.height - thumb_height) * (layout["scroll"] / layout["max_scroll"]))
        pygame.draw.rect(surface, INK, pygame.Rect(bar.x, thumb_y, bar.width, thumb_height), border_radius=2)

    draw_panel(surface, layout["new"], fill=(235, 235, 225, 180), center_label=True, label="New custom", label_size=26)


def draw_custom_character_modal(surface):
    """Show the named local character drawing modal."""
    layout = build_draw_character_layout()
    modal = layout["modal"]
    canvas_rect = layout["canvas"]
    shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    shade.fill((255, 255, 255, 70))
    surface.blit(shade, (0, 0))
    draw_panel(surface, modal, fill=(255, 252, 245, 235))
    title = "Edit character" if editing_custom_character_id else "New character"
    draw_hand_text(surface, title, modal.centerx, modal.y + 34, size=36, center=True, bold=True)

    draw_panel(surface, layout["input"], fill=(255, 255, 255, 170))
    name_text = custom_character_name_input or "Name character"
    name_color = INK if custom_character_name_input else (120, 112, 100)
    draw_hand_text(surface, name_text, layout["input"].x + 14, layout["input"].y + 11, size=28, color=name_color, max_width=layout["input"].width - 28)

    for item in layout["swatches"]:
        swatch_rect = item["rect"]
        pygame.draw.rect(surface, item["color"], swatch_rect, border_radius=4)
        border_color = INK if item["color"] == selected_draw_color else (120, 112, 100)
        border_width = 4 if item["color"] == selected_draw_color else 2
        pygame.draw.rect(surface, border_color, swatch_rect, border_width, border_radius=4)

    draw_panel(surface, canvas_rect.inflate(12, 12), fill=(255, 255, 255, 150))
    pygame.draw.rect(surface, (255, 255, 255), canvas_rect)
    grid_color = (226, 226, 218)
    grid_step = max(12, canvas_rect.width // 8)
    for x in range(canvas_rect.left + grid_step, canvas_rect.right, grid_step):
        pygame.draw.line(surface, grid_color, (x, canvas_rect.top), (x, canvas_rect.bottom), 1)
    for y in range(canvas_rect.top + grid_step, canvas_rect.bottom, grid_step):
        pygame.draw.line(surface, grid_color, (canvas_rect.left, y), (canvas_rect.right, y), 1)

    drawing_preview = pygame.transform.scale(custom_character_draft, canvas_rect.size)
    surface.blit(drawing_preview, canvas_rect.topleft)
    pygame.draw.rect(surface, INK, canvas_rect, 2)

    draw_panel(surface, layout["back"], center_label=True, label="Back", label_size=26)
    draw_panel(surface, layout["clear"], center_label=True, label="Clear", label_size=26)
    draw_panel(surface, layout["save"], center_label=True, label="Save", label_size=26)


def draw_scoreboard_modal(surface):
    """Show the saved score list in a small centered window."""
    modal = build_home_modal_rect(width_ratio=0.42, height_ratio=0.58, min_height=420)
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
        draw_hand_text(surface, line, modal.x + 24, line_y, size=24, max_width=modal.width - 170)
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
    draw_hand_text(
        surface,
        "Game Over",
        layout["modal"].centerx,
        layout["modal"].y + 54,
        size=50,
        center=True,
        bold=True,
        max_width=layout["modal"].width - 56,
    )

    if run_state["result"]["new_high_score"]:
        draw_hand_text(surface, "New high score", layout["modal"].centerx, layout["modal"].y + 100, size=28, center=True, max_width=layout["modal"].width - 56)

    draw_hand_text(surface, f"Time  {format_time_mmss(run_state['result']['time'])}", layout["modal"].x + 36, layout["modal"].y + 144, size=30, max_width=layout["modal"].width - 72)
    draw_hand_text(surface, f"Attacks  {run_state['result']['attacks']}", layout["modal"].x + 36, layout["modal"].y + 184, size=30, max_width=layout["modal"].width - 72)

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


DEBUG_COLORS = {
    "player": (35, 170, 95),
    "pen": (70, 125, 240),
    "projectile": (225, 70, 55),
    "attack": (215, 135, 35),
    "warning": (180, 65, 210),
}


def draw_debug_rect(surface, rect, color, label=None):
    if rect is None:
        return

    rect = pygame.Rect(rect)
    if rect.width <= 0 or rect.height <= 0:
        return

    fill = pygame.Surface(rect.size, pygame.SRCALPHA)
    fill.fill((*color, 38))
    surface.blit(fill, rect.topleft)
    pygame.draw.rect(surface, color, rect, 2)
    if label:
        draw_hand_text(surface, label, rect.left, rect.top - 16, size=16, color=color, max_width=120)


def draw_debug_circle(surface, center, radius, color, label=None):
    radius = int(radius)
    if radius <= 0:
        return

    center = (int(center[0]), int(center[1]))
    fill = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    pygame.draw.circle(fill, (*color, 30), (radius, radius), radius)
    surface.blit(fill, (center[0] - radius, center[1] - radius))
    pygame.draw.circle(surface, color, center, radius, 2)
    if label:
        draw_hand_text(surface, label, center[0] - radius, center[1] - radius - 16, size=16, color=color, max_width=140)


def draw_debug_line(surface, start, end, width, color, label=None):
    start = (int(start[0]), int(start[1]))
    end = (int(end[0]), int(end[1]))
    width = max(1, int(width))
    pygame.draw.line(surface, (*color,), start, end, width)
    pygame.draw.line(surface, (20, 20, 20), start, end, 1)
    if label:
        draw_hand_text(surface, label, start[0], start[1] - 16, size=16, color=color, max_width=140)


def draw_debug_hitbox_entry(surface, entry, fallback_color):
    kind = entry.get("type", "rect")
    color = entry.get("color", fallback_color)
    label = entry.get("label")

    if kind == "rect":
        draw_debug_rect(surface, entry.get("rect"), color, label)
    elif kind == "circle":
        draw_debug_circle(surface, entry.get("center", (0, 0)), entry.get("radius", 0), color, label)
    elif kind == "line":
        draw_debug_line(surface, entry.get("start", (0, 0)), entry.get("end", (0, 0)), entry.get("width", 1), color, label)


def draw_debug_hitboxes(surface):
    """Draw the active gameplay collision shapes for tuning attacks."""
    player = run_state["player"]
    draw_debug_rect(surface, player.get_hitbox(), DEBUG_COLORS["player"], "player")
    draw_debug_rect(surface, run_state["pen"].get_rect(), DEBUG_COLORS["pen"], "pen")

    for attack in run_state["active_attacks"]:
        if not hasattr(attack, "get_debug_hitboxes"):
            continue
        for entry in attack.get_debug_hitboxes():
            draw_debug_hitbox_entry(surface, entry, DEBUG_COLORS["attack"])

    for projectile in run_state["projectiles"]:
        if not hasattr(projectile, "get_debug_hitboxes"):
            continue
        for entry in projectile.get_debug_hitboxes():
            draw_debug_hitbox_entry(surface, entry, DEBUG_COLORS["projectile"])

    indicator = pygame.Rect(screen_width - 166, 18, 142, 34)
    draw_panel(surface, indicator, fill=(255, 252, 245, 170), center_label=True, label="F3 Hitboxes", label_size=18)


scores = load_scores()
game_state = "home"
selected_player_skin = "Checkbox"
selected_player_icon = PLAYER_SKINS[selected_player_skin]
audio_muted = False
home_modal = None
character_list_scroll = 0
drawing_custom_character = False
custom_draw_last_point = None
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
                elif game_state == "home" and home_modal == "draw_character":
                    home_modal = "characters"
                    drawing_custom_character = False
                    custom_draw_last_point = None
                elif game_state == "home" and home_modal is not None:
                    home_modal = None
                else:
                    running = False

            elif event.key == pygame.K_F11:
                fullscreen = not fullscreen
                if fullscreen:
                    refresh_screen_layout(pygame.display.set_mode((0, 0), pygame.FULLSCREEN))
                else:
                    refresh_screen_layout(pygame.display.set_mode(windowed_size, pygame.RESIZABLE))

            elif event.key == pygame.K_F3:
                debug_hitboxes = not debug_hitboxes

            elif game_state == "home" and home_modal == "draw_character" and event.key == pygame.K_RETURN:
                save_custom_character()

            elif game_state == "home" and home_modal == "draw_character" and event.key == pygame.K_BACKSPACE:
                custom_character_name_input = custom_character_name_input[:-1]

            elif game_state == "home" and home_modal is None and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                begin_run()

            elif game_state == "save_score" and event.key == pygame.K_RETURN:
                save_current_score()

            elif game_state == "save_score" and event.key == pygame.K_BACKSPACE:
                run_state["name_input"] = run_state["name_input"][:-1]

        elif event.type == pygame.TEXTINPUT and game_state == "home" and home_modal == "draw_character":
            custom_character_name_input = (custom_character_name_input + event.text)[:MAX_CHARACTER_NAME_LENGTH]

        elif event.type == pygame.TEXTINPUT and game_state == "save_score":
            if len(run_state["name_input"]) < 18:
                run_state["name_input"] += event.text

        elif event.type == pygame.VIDEORESIZE and not fullscreen:
            windowed_size = (max(720, event.w), max(520, event.h))
            refresh_screen_layout(pygame.display.set_mode(windowed_size, pygame.RESIZABLE))

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            drawing_custom_character = False
            custom_draw_last_point = None

        elif event.type == pygame.MOUSEMOTION:
            if game_state == "home" and home_modal == "draw_character" and drawing_custom_character:
                draw_on_custom_character_draft(event.pos, continue_stroke=True)

        elif event.type == pygame.MOUSEWHEEL:
            if game_state == "home" and home_modal == "characters":
                layout = build_characters_modal_layout()
                character_list_scroll = int(clamp(character_list_scroll - event.y, 0, layout["max_scroll"]))

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            if game_state == "home":
                home_layout = build_home_layout()
                if home_modal == "draw_character":
                    draw_layout = build_draw_character_layout()
                    if not draw_layout["modal"].collidepoint(mouse_pos):
                        home_modal = "characters"
                        drawing_custom_character = False
                        custom_draw_last_point = None
                    elif any(item["rect"].collidepoint(mouse_pos) for item in draw_layout["swatches"]):
                        for item in draw_layout["swatches"]:
                            if item["rect"].collidepoint(mouse_pos):
                                selected_draw_color = item["color"]
                                break
                    elif draw_layout["canvas"].collidepoint(mouse_pos):
                        drawing_custom_character = True
                        custom_draw_last_point = None
                        draw_on_custom_character_draft(mouse_pos)
                    elif draw_layout["back"].collidepoint(mouse_pos):
                        home_modal = "characters"
                        drawing_custom_character = False
                        custom_draw_last_point = None
                    elif draw_layout["clear"].collidepoint(mouse_pos):
                        clear_custom_character_draft()
                    elif draw_layout["save"].collidepoint(mouse_pos):
                        save_custom_character()

                elif home_modal == "characters":
                    character_layout = build_characters_modal_layout()
                    modal = character_layout["modal"]
                    if not modal.collidepoint(mouse_pos):
                        home_modal = None
                    else:
                        for row in character_layout["rows"]:
                            skin_key = row["skin"]
                            if row["delete"] and row["delete"].collidepoint(mouse_pos):
                                delete_custom_character(custom_id_from_skin_key(skin_key))
                                break
                            if row["edit"] and row["edit"].collidepoint(mouse_pos):
                                open_custom_character_record(custom_id_from_skin_key(skin_key))
                                break
                            if row["select"].collidepoint(mouse_pos):
                                select_player_skin(skin_key)
                                home_modal = None
                                break
                        else:
                            if character_layout["new"].collidepoint(mouse_pos):
                                open_custom_character_editor()
                elif home_modal == "scoreboard":
                    modal = build_home_modal_rect(width_ratio=0.42, height_ratio=0.58, min_height=420)
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
