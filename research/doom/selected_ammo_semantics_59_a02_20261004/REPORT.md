# Selected weapon ammunition semantics — #59 construction A02

## Result

`PARTIAL_SIGNAL_SEMANTICS_PASS_SLOT_MAPPING_HOLD`. In a fresh, input-free Doom episode, direct `get_game_variable()` reads exactly matched the ordered `GameState.game_variables` vector at both retained samples. At the first sample (episode tic 1), `SELECTED_WEAPON=2`, `SELECTED_WEAPON_AMMO=50`, `AMMO1=0`; the retained HUD visibly reads 50. All ten `AMMO0..AMMO9` values are in `out/raw.json`. This falsifies treating `AMMO1` as the selected-weapon ammo signal for this state. `AMMO2` and `AMMO4` both equal 50, so this state cannot establish a unique mapping from selected weapon ID to an ammo slot.

After a no-button 35-tic coast, episode time advanced from tic 1 to 36. The HUD screenshot shows a nearby enemy while health stayed 100. This is evidence of environmental change during the coast, not an independently useful feedback-onset measurement and not evidence of a response or recovery.

## Frozen protocol and provenance

H/T/D/C/U is frozen in `out/FREEZE.json`. The first construction attempt, `59-selected-ammo-semantics-a01-20261004`, is preserved under the sibling A01 directory as `STOP_IMAGE_ASSET_MISSING_BEFORE_GAME_INIT`; its requested `doom2.wad` did not exist in the image. The A01 freeze also contains an invalid future `created_utc` value and must not be treated as valid preregistration. A02 is separately labeled, uses the exact image asset `freedoom2.wad`, and is not a replay of A01.

Image: `post-guard-game-59-4d74:20261004`, image ID `sha256:94014a0f7757b46b7c3ae83f430ad973ae6abe1722937bdc6d060139aaeb6378`.

Candidate source: `source/probe.py`, SHA-256 `376607361f77fbf4c7d9f72ea88c7bf4e8b6c0f7cc59e6ec9ec11b4010d65e6c`.

Command: `wslc run --rm --network none --user 65534:65534 --cpus 1 --memory 512m --workdir /out -v <A02>/source:/study:ro -v <A02>/out:/out:rw -e PYTHONDONTWRITEBYTECODE=1 -e HOME=/tmp post-guard-game-59-4d74:20261004 python3 -B /study/probe.py`.

The container exited 0. WSLc warned that the kernel lacks swap-limit capabilities / cgroup mount; requested memory enforcement remains unverified. Independent audit exited 0 and checked tic bracket, empty submitted-input list, API/GameState equality, all ten ammo slots and PNG hashes.

## Limits and next discriminating measurement

This is one initial scenario state, two samples, and no model/planner/controller or gameplay action. It does not qualify HUD OCR generally, field freshness under load, useful feedback, per-key release timing, causal latency, damage avoidance, or bounded recovery. The actual #59 gate remains fresh v39-lineage evidence for per-key admission/up/release, independently useful feedback onset, and bounded recovery under a matched condition. Any input-bearing run still needs its separately available allocation and must not be inferred from this construction.

Next signal-specific construction, if useful: select a state where selected weapon differs from the currently duplicated ammo-slot values (or use a controlled, authorized weapon-switch fixture), then verify `SELECTED_WEAPON_AMMO` against the visible HUD and slot vector at the same episode tic. Do not use `AMMO1` as a proxy.
