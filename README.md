# Unchecked

An endless dodge game on notebook paper. You play the small checkbox; an evil pencil hops around its drawing lane and sketches attacks that land in the dodge zone a heartbeat later.

## How it plays
- Move with WASD or arrow keys. Stay inside the sketched dodge zone.
- The pencil picks a random spot in its top lane, waits ~0.5s as a telegraph, then the chosen attack fires from that spot. The pencil immediately wanders elsewhere and can stack multiple active attacks.
- Attacks never chase the pencil; they stay where they were drawn. The pencil accelerates over time, which increases how many overlapping attacks you see.
- Lose all HP and the run ends. Press `R` after dying to restart.

## Current attacks
- Gun: plants a gun at the pencil location and fires 3 shots toward the player, one burst at a time with recoil.
- Grenade: lobs a spinning grenade toward where the player stood when it was drawn; a pulsing circle marks the blast before it detonates.
- Sword: shows red pulsing preview lines, then a sword leaps in and stabs along each slash; the sword stays stuck briefly (shakes before vanishing).

Add new attacks by appending another bullet to this list that briefly states the telegraph, movement, and hit logic.

## Code map
- `game/main.py` — game loop, HUD, paper-themed rendering.
- `game/utils.py` — geometry helpers (`vector_to`, `normalized`, `angle_from_vector`, `point_from_angle`, `swing_hits_rect`), UI helpers, and layout calculation.
- `game/player.py` — player movement, HP handling.
- `game/pen.py` — pencil roaming logic and draw timing.
- `game/attacks/` — attack implementations; inherit `AttackBase`.
- `game/projectiles/` — reusable projectile base + bullet.

### Adding an attack
1. Create a class that subclasses `AttackBase` in `game/attacks/`.
2. Use helpers from `utils` (for aiming, line hits, or paper UI) instead of re-deriving math.
3. Implement `update(dt, projectiles, player)` (spawn projectiles or call `player.take_damage`) and `draw(surface)`.
4. Register the class in `ATTACK_TYPES` inside `game/main.py` and add a bullet to the list above.
