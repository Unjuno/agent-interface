# Real MAP01 threat-contact fixture v1

The previous natural v26 allocation showed that a fixed seed does not fix a
model-reached state: Luna took a different route from v23 and never saw an
enemy. This fixture removes that navigation lottery while retaining the real
Freedoom MAP01 engine state. It is a benchmark start condition, not a custom
scenario and not an action oracle.

`map01-threat-contact-v1` was reached by replaying the first three v23 actions
and their measured model-wall coast intervals through the same X11 Executor
used for live control. Seven setup programs completed with seven verified empty
releases and zero model calls. The retained source frame is exact and shows at
least one enemy with health 100 and ammunition 50 at episode tic 1263.

The fixture binds the save to its SHA-256, the source-frame SHA-256, ViZDoom
1.3.0, the Freedoom IWAD SHA-256, MAP01, and skill 1. Session v7 validates all
of those fields before loading. A fresh process restored episode tic 1263 and
produced an exact first X11 observation that independently shows the enemy,
health 100, and ammunition 50. Saving is exposed only in setup mode; measured
control cannot invoke it. Loading grants no runtime input authority.

ViZDoom save/load silently failed when the engine received paths below this
workspace because `New project` contains a space. A model-free four-mode probe
repeated the operation through a no-space temporary directory and succeeded in
PLAYER, ASYNC_PLAYER, SPECTATOR, and ASYNC_SPECTATOR modes. Session v7 therefore
copies setup saves through its no-space session temporary directory. This is a
local compatibility finding, not evidence that save/load is generally reliable.
The upstream example labels the feature experimental:
<https://github.com/Farama-Foundation/ViZDoom/blob/main/examples/python/save_load_game.py>.
The API is documented at
<https://vizdoom.farama.org/main/api/python/doom_game/>.

Audit the promoted fixture from WSL with:

```sh
PYTHONPATH=_vizdoom:research/doom:research/live_control \
  python3 research/doom/audit_map01_threat_fixture_v1.py
```

The audit checks retained hashes and file inventory, environment binding,
recorded setup programs and releases, fresh-process restoration, exact source
and loaded observations, manual enemy review, initial HUD values, and a narrow
credential-pattern scan. It makes no gameplay, control-quality, repeated-
reliability, human-speed, or MAP01-clear claim.
