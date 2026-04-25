# Unchecked

Unchecked is a notebook-paper survival dodge game. You control the checkbox while a hostile pencil sketches attacks from the top lane into the play area.

## Repository layout
```text
.
|-- game/                   # Game code and shipped assets
|-- packaging/pyinstaller/  # PyInstaller build spec
|-- scripts/                # Windows launcher and packaging helpers
|-- build/                  # Local build output (generated)
|-- dist/                   # Packaged executable output (generated)
`-- portable/               # Portable zip output (generated)
```

The game source stays entirely under `game/`. Build artifacts are kept out of the code layout and are already ignored by Git.

## Run the game

### Option 1: run the packaged build
If `dist/Unchecked/Unchecked.exe` exists, start it with:

```bat
scripts\run.bat
```

### Option 2: run from Python
From the repository root:

```bat
py -m game.main
```

If `scripts\run.bat` does not find a packaged executable, it falls back to a local Python 3.11 install under `%LocalAppData%\Programs\Python\Python311\`.

### Debug hitbox build
For tuning collision boxes, run the windowed debug version:

```bat
scripts\run_debug.bat
```

You can also toggle hitboxes during any run with `F3`, or start manually with:

```bat
py -m game.main --windowed --debug-hitboxes
```

## Build a Windows package
Build with PyInstaller from the repository root:

```bat
py -m PyInstaller packaging\pyinstaller\Unchecked.spec
```

After the executable is built, create the portable zip with:

```bat
scripts\package_portable.bat
```

## How it plays
- Move with `WASD` or the arrow keys.
- Stay inside the sketched dodge zone.
- The pencil telegraphs an attack, then fires from the spot where it drew it.
- Attacks remain where they were drawn while the pencil keeps moving.
- Lose all HP and the run ends. Press `R` to restart.

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
