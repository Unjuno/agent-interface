# Weapon/ammo audit follow-up 01

This additive follow-up rechecks the retained `weapon-ammo-construction-04`
result from main commit `af6d0f9842a2377fba736d2d65643b02690f99d9`. It leaves the
original raw data, `FILES.json`, `SAVED_AUDIT.json`, and experiment report
unchanged.

The published `audit_weapon_ammo_04.py` expects
`sample-pair-04/00-coast/RESULT.json`, while the committed package stores the
cell at `00-coast/RESULT.json`; running it from the published package therefore
raises `FileNotFoundError`. In a temporary copy with the expected directory
layout restored, changing the initial ammo signal to `status=unobserved`, an
invalid format, a different focus binding, and sequence 999 still yielded
`PASS_HUD_WEAPON_AMMO_BINDING_SCOPED`. The original PASS predicate compared
signal values but did not validate their observation metadata.

`audit_weapon_ammo_followup_01.py` reads the committed layout directly (and
accepts the earlier runner layout), computes the scoped HUD/API comparison from
raw JSON/JSONL, and requires the HUD signals to be observed, correctly typed,
bound to the same capture time, sequence and pointer binding, and carry a
well-formed common WAD digest. It also checks coherent finite samples, neutral
actions in the window, selected-slot ammo agreement, and clean child/reader and
rescue fields. It reports the existing scoped PASS on the unmodified evidence.

The mutation suite passed 4/4 cases: committed-layout baseline, unobserved and
misbound HUD signal rejection, capture-time mismatch rejection, and non-neutral
window rejection. Commands:

```text
python3 audit_weapon_ammo_followup_01.py
python3 -m unittest -v test_audit_weapon_ammo_followup_01.py
python3 -m py_compile audit_weapon_ammo_followup_01.py test_audit_weapon_ammo_followup_01.py
git diff --check
```

This is a post-result audit repair and mutation test, not a prospectively frozen
independent auditor or a new game allocation. It supports only the retained
fixture's near-time HUD/selected-ammo mapping; it does not establish damage
exposure, recovery efficacy, simultaneous HUD/API truth, or live controller
trust/adoption. Preserve the earlier #7605 AMMO1 mismatch result unchanged.
