# Preservation note — 2026-10-05 session handoff

This note records the distinction between the frozen evidence and its present repository context. The experiment packages and their original inputs, outputs, audit results, and SHA-256 manifests are retained unchanged except for the generated A02 audit/manifest refresh produced by `audit_currentmain_a02.py` during handoff.

- A01 is frozen against `6a2826d391b77496b69752609a6f07b6971b4b6f`. `run_checks.py` passes in normal and optimized Python 3.12.10 modes. `audit.py` cannot be rerun in the current checkout because it explicitly requires both `HEAD` and `origin/main` to equal that historical freeze SHA. Current checkout HEAD remains the frozen branch commit and `origin/main` is `1fbef34f244588bff3d79b7cbea423dcb510ef8f`.
- A02 is frozen against `b6907899f11b036f2af572e8d4794ebb4b7e5c83`; its independent audit reports 21/21 checks passing. It remains evidence for those frozen source blobs only. The package already contains the later applicability correction and its review-request draft; no current-main finding is claimed.
- No production source was changed. No candidate, game, model, GUI, native input, or allocation was run during this handoff.
- Local verification on 2026-10-05: A01 `run_checks.py` PASS (normal and `-O`); A02 `run_checks.py` PASS (normal and `-O`); A02 independent audit PASS 21/21. The A01 audit's current-checkout prerequisite is not met and is intentionally reported as unverified rather than bypassed.

These packages preserve bounded synthetic construction evidence and an explicit stale-source limitation. They do not authorize adoption or merge.