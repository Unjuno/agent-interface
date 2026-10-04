# Weapon/ammo audit follow-up 02

This additive revision preserves the files and result recorded by follow-up 01. It closes three independently reproduced PASS paths in the follow-up 01 auditor: a typed HUD capture detached from the published image observation, a non-neutral nearest API sample outside the scored coast window, and malformed action values accepted as neutral through Python truthiness.

The auditor now requires the typed initial capture to match the unique ordinary `observation` event on ID, step, sequence, capture timestamp, pointer binding, and RGB digest. It validates every action as a finite numeric vector matching the recorded button count, with exact zero values, both across the scored window and on the nearest coherent API row used for HUD/API comparison. This exact observation cross-binding also prevents an arbitrary timestamp shift from preserving a PASS while signal metadata is changed consistently.

The original retained data and original `FILES.json` manifest are unchanged. The audit remains a post-result check of the retained fixture; it does not establish damage exposure, recovery efficacy, simultaneous HUD/API truth, or live controller trust/adoption. No game allocation was launched.

Validation: `python -m unittest -v test_audit_weapon_ammo_followup_02.py` passes 7/7; `python audit_weapon_ammo_followup_02.py` returns `PASS_HUD_WEAPON_AMMO_BINDING_SCOPED`; `py_compile` and `git diff --check` pass. The three new mutation regressions each failed against the follow-up 01 auditor before passing against this revision.
