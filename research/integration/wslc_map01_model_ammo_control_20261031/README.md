# WSLc MAP01: model-directed attack and ammo-aware wait control

This predeclared sequential pair addresses the [reverse-order pulse probe](../wslc_map01_model_pulse_reverse_order_20261031/), which did not sample ammunition. Both fresh allocations used Freedoom2 MAP01 skill 1, seed 991031, fixed guarded navigation, observed A-key hold followed by cancellation and verified release, fresh review and old-alias refusal. Each then made one host `gpt-6.1-sol` low-effort call on the full X11 screenshot and evaluated the same pixel/binding gate. The order was `af01` wait control, then `af02` attack. In the control the model's attack proposal was withheld and the runner waited 1,000 ms without input. In the attack arm a proposed fire passing the guard was executed for an externally fixed 1,000 ms; the prompt disclosed that the experiment controls duration. Eight passive samples followed without further input.

| Arm | Game-reported selected-weapon ammo before → after → final | Kills before → after → final |
|---|---:|---:|
| Wait control | 50 → 50 → 50 | 0 → 0 → 0 |
| Guarded attack | 50 → 47 → 47 | 0 → 1 → 1 |

Both model calls proposed fire for 500 ms; the attack arm's 1,000 ms duration was the predeclared intervention, not the model's requested duration. The attack passed all recorded guards and completed with verified empty release. Both final owner releases and tested keymaps were empty, and both host closures reported success. The ammo and kill counters are game-provided observations; no independent physical shot counter is claimed. The earlier cancelled turn may have had a partial effect.

This is one fixed-order, fixed-seed pair with separate model calls, different target coordinates and continuing simulator trajectories. It provides a distinguishable ammo and kill response in this controlled example, not a population estimate, proof of general causal performance, model-efficiency advantage or MAP01 completion. The prior pulse studies lacked ammo samples and cannot be retroactively assigned ammunition outcomes. The passive window is finite, so later effects are unknown.

`public.zip` retains frozen code/conditions, game and model screenshots, outputs and usage, samples, and guard/owner records. Private model protocol/call files remain local and are hash-indexed in `private-hashes.json`. `python audit.py` with Pillow verifies hashes, image and coordinate mapping, gate checks, intervention/observed counters, release ordering and passive timeline. WSLc used private Xvfb, network none, one CPU, 1 GiB and a 150 s watchdog.
