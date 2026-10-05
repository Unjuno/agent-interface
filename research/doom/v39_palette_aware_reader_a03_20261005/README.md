# V39 palette-aware reader A03 — publication package

## Result

The executed A03 candidate passed its preregistered compatibility-only gate on 35 saved frames. All 33 same-episode held-out frames matched the retained palette-0 typed values; sequence 31 remained health 97/ammo 47 under palette 0; sequence 35 resolved to health 100/ammo 47 under palette 9. Every frame resolved to one unique pair under a common palette. Blank/no-HUD, no-common-palette, and conflicting-pair controls returned UNKNOWN. The independent audit of the exact local run passed 229 checks.

## Source privacy note

The exact executed candidate and freeze-generation helper contained a hard-coded local WAD path including a Windows account path. The path is not included here. `FREEZE.executed.json` retains the exact freeze bytes and the SHA-256 of the executed candidate. `candidate_public.py` is a publication-only copy with the WAD path read from `FREEDOOM2_WAD`; it was not the executed candidate and its source hash is different. The local A03 raw outcome and original audit log are retained unchanged. `audit_public.py` independently validates the raw output and all publicly retained input/source hashes, but it explicitly cannot byte-verify the withheld executed candidate or freeze-preparation script.

## Limits

This is a saved-image compatibility result using 35 frames from one episode. Stored typed values come from the same reader family and are not independent HUD truth. No renderer palette state, live game/input, model, task effect, runtime integration, useful feedback, bounded recovery, or Issue #59 gate closure is established. The public candidate copy has not been rerun.

See `PROTOCOL.md`, `FREEZE.executed.json`, `output/raw.json`, the execution logs, and `SHA256SUMS`. The WAD is external and identified by the SHA in the freeze; it is not bundled.
