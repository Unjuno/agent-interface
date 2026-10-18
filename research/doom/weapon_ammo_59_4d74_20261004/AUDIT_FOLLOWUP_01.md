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

Review of the first follow-up found additional false-pass cases: the typed HUD
capture was not cross-bound to the ordinary screen-observation event, the
nearest HUD-comparison API row sat before the neutral scoring window and was
not itself required to be neutral, and `not any(action)` accepted malformed
vectors such as `[null]`. Shifting the HUD time by 1,000 seconds also continued
to pass because the auditor selected the nearest row without a time bound.

`audit_weapon_ammo_followup_01.py` reads the committed layout directly (and
accepts the earlier runner layout), computes the scoped HUD/API comparison from
raw JSON/JSONL, and requires the typed capture to match the ordinary initial
screen observation's step, sequence, capture time, binding, frame digest,
focus checks, typed-ready time, and retained image. HUD signals must be
observed, correctly typed, bound to that same capture, and carry a well-formed
common WAD digest. The API comparison sample must be a coherent neutral sample
between the initial HUD capture and the scoring window start. The coherent API
timeline must also bracket the HUD capture, rejecting a scorer timeline and
scoring window shifted wholly away from it. The selected comparison row itself
must have ordered timestamps, a stable TIC, and finite variables. Both that
comparison row and every scoring-window row must contain a finite numeric zero
action vector matching the nine unique recorded buttons. The audit also checks
selected-slot ammo agreement and clean child/reader/rescue fields.

The mutation suite passed 11/11 cases, including a pinned `FILES.json` digest check and rejection of a modified raw `RESULT.json`: committed-layout baseline, unobserved
signal rejection, signal capture-time mismatch, typed/screen observation
divergence, non-neutral pre-window comparison row, malformed and wrong-width
window action vectors, and a shifted HUD timestamp with no eligible pre-window API sample, a shifted
scorer timeline and window, and an unstable comparison-row TIC. The audit verifies the fixed manifest hash and byte count/SHA-256 of
the result, final record, event log, scorer log, and retained comparison image.
Timeline bracketing does not impose a maximum age within the bracket: the
retained comparison offset is 240,412,225 ns, but this is an observed value,
not a validated upper bound for future evidence. Commands:

```text
python3 audit_weapon_ammo_followup_01.py
python3 -m unittest -v test_audit_weapon_ammo_followup_01.py
python3 -m py_compile audit_weapon_ammo_followup_01.py test_audit_weapon_ammo_followup_01.py
git diff --check
```

This is a post-result audit repair and mutation test, not a prospectively frozen
independent auditor or a new game allocation. It supports only the retained
fixture's pre-window near-time HUD/selected-ammo mapping; it does not establish
damage exposure, recovery efficacy, simultaneous HUD/API truth, or live
controller trust/adoption. Preserve the earlier #7605 AMMO1 mismatch result
unchanged.
