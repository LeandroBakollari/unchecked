# Unchecked

Unchecked is a notebook-paper survival dodge game. You control the checkbox while a hostile pencil sketches attacks from the top lane into the play area.

## Repository layout
```text
.
|-- game/                   # Game code and shipped assets
`-- scripts/                # Windows launch helpers
```

The game source stays entirely under `game/`.

## Run the game

### Option 1: launcher script

```bat
scripts\run.bat
```

### Option 2: run from Python
From the repository root:

```bat
py -m game.main
```

### Debug hitboxes
For tuning collision boxes, run the windowed debug version:

```bat
scripts\run_debug.bat
```

You can also toggle hitboxes during any run with `F3`, or start manually with:

```bat
py -m game.main --windowed --debug-hitboxes
```

## How it plays
- Move with `WASD` or the arrow keys.
- Stay inside the sketched dodge zone.
- Use `Character` on the home screen to select a checkbox skin, randomize the skin, or draw named custom characters.
- The pencil telegraphs an attack, then fires from the spot where it drew it.
- Attacks remain where they were drawn while the pencil keeps moving.
- Lose all HP and the run ends. Press `R` to restart.

Custom characters are saved locally in the same user app-data folder as scores, with one PNG per saved character.

## Current attacks
- Gun: places a gun at the pencil location and fires a three-shot burst toward the player.
- Grenade: arcs toward the player's recorded position and detonates after a warning pulse.
- Sword: previews slash lines, then lunges along them and briefly stays embedded.
- Shotgun: fires staggered spreads of fireballs across a cone.
- Mirror: triggers three random attacks in sequence.
- Sniper: tracks the player, locks aim, then fires a sustained beam.
- Boomerang: dives through the play area, leaves the screen, then returns upward.
- Shuriken: launches homing spinning projectiles after a short charge.
- Stuff: sweeps a staff and sends a rotating ring of fireballs toward the player.
- Pool: aims a cue at the player, strikes a spinning ball, and lets it bounce three times before leaving the dodge zone.

## Code map
- `game/main.py`: main loop, rendering, HUD, and attack registration.
- `game/player.py`: player movement and health.
- `game/pen.py`: pencil movement and attack timing.
- `game/utils.py`: shared geometry, UI helpers, and layout logic.
- `game/attacks/`: attack implementations built on `AttackBase`.
- `game/projectiles/`: projectile primitives and reusable projectile types.

## Adding an attack
1. Create a new subclass of `AttackBase` under `game/attacks/`.
2. Reuse helpers from `game/utils.py` instead of duplicating math.
3. Implement `update(dt, projectiles, player)` and `draw(surface)`.
4. Register the attack in `ATTACK_TYPES` in `game/main.py`.
5. Document the new attack in the list above.
