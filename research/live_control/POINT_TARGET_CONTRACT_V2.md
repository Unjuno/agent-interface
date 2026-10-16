# Explicit point space and motion contract v2

Status: advance the explicit contract to a different-domain test. A
preregistered Chromium pair and independent Windows/WSL audit pass. The evidence
covers one known button and does not establish automatic region size, broad visual
identity, causal speed/token reduction or human-tempo control.

## Repaired ambiguity

The preceding model-point study asked Luna-low for absolute screenshot x/y while
task code assigned the `window_content` transformation frame. The runtime followed
one surface move correctly, but that result did not show that the model authored or
understood the frame. Its artifact audit therefore retained the mechanism while
holding interface promotion.

V2 separates two concepts:

- `point_space=source_observation_pixels`: x/y are absolute pixels in the exact
  source observation shown to the model;
- `motion_model=surface_origin_translation`: on later observations, the target
  moves by the x/y delta of the bound application's window origin;
- `motion_model=screen_fixed`: the target remains at the same global screenshot
  pixels when that window origin changes.

`point_target_contract_v2.py` validates this exact model result and maps its motion
model to the current runtime's `window_content` or `screen_chrome` implementation
term. The mapping is explicit rather than inferred from a field that also appears
to describe the numeric coordinate basis. Twelve valid/invalid pure paths pass on
Windows and WSL.

## Preregistered live pair

`chromium-point-contract-pair-01` freezes stable then changed-target sessions on
seed991015. Each case uses one current 1280x800 image, one identical controlled
Luna-low prompt and one model call. The runtime keeps the prior fixed24x14 region
so this allocation isolates point-space and motion authorship. There is no retry
or prompt, point, frame, size or order repair.

Both model calls return the exact contract:

```json
{
  "op": "target_reference",
  "point_space": "source_observation_pixels",
  "point": {"x": 270, "y": 243},
  "motion_model": "surface_origin_translation"
}
```

The point is inside the independently fixed Save-button endpoint. Reported input
is9,264 and9,265 tokens. Stable reports zero cached input; changed-target reports
6,912 cached input, so this pair is not a cache or cost comparison. Monetary cost
and observed provider model identity remain unavailable.

In stable, the exact fresh patch mints alias `save_form`. After the X11 surface
moves from `[10,10,1050,780]` to `[30,18,1050,780]`, the runtime applies the
model-authored motion semantics, revalidates `[20,8]` and resolves point
`[290,251]`. A scripted alias click admits only move/button-down, verifies release
and independently saves exact `t991015`. It uses14 durable calls. Decision start
to independent evaluation return is8,343.071ms, of which the parent-observed model
call is7,445.830ms. Click submit to return is327.139ms. These are descriptive
single-episode measurements.

In changed-target, the same surface navigates to `about:blank` after the model
returns. Fresh minting finds a different exact patch, creates no handle, admits
zero target pointer input, verifies release and leaves independent success false.
It uses10 durable calls. The deliberate navigation makes its timing incomparable
with stable.

The audit verifies preregistration hashes, identical prompt hashes, model/schema/
instruction hashes, exact model contracts, mapping, source/current patch digests,
surface translation, admissions, releases and independent output. All36 `.ait`
frames reconstruct exactly on Windows and WSL.

The artifact auditor also writes a structured `audit_passed=false` HOLD record
before returning a nonzero status if any frozen-source, model-contract, frame,
patch, lifecycle or output assertion fails. A failed first run therefore remains
machine-readable instead of disappearing behind an assertion traceback.

## Decision

Advance the explicit point-space/motion contract to a preregistered different-
domain test. Do not promote model-point handles as a default interface yet. The
24x14 region remains caller-authored, the target is one known Chromium button,
and a model can still choose the wrong motion semantic on a less obvious target.

The next test should use a non-Chromium target with an independent semantic oracle
and include both a valid target and a transient, similar or changed negative. It
should preserve actual input tokens and end-to-end timing. Automatic region size
or region proposal belongs in a later isolated allocation.

## Reproduction

```text
python research/live_control/probe_point_target_contract_v2.py
python research/live_control/audit_chromium_point_contract_pair_v1.py
wsl -e bash -lc "cd '/mnt/c/Users/junny/Documents/New project/agent-interface' && python3 research/live_control/audit_chromium_point_contract_pair_v1.py"
```

Artifacts: `research/live_control/results/chromium-point-contract-pair-01/`.
