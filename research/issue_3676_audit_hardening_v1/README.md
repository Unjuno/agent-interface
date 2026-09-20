# Issue #3676 — harden the #3675 independent audit

## H/T/D/C/U

- **H:** The #3675 auditor accepts contradictory and non-canonical traces; a strict ordered schema can reject targeted mutations without changing predecessor evidence.
- **T:** Preserve the predecessor raw, freeze and original audit bytes; run fixed mutations against both the predecessor and hardened auditors; verify the function and documented CLI use identical checks.
- **D:** PASS for the local construction rung requires exact predecessor artifact hashes, baseline acceptance, rejection of all three original controls and eight added controls, successful direct and subprocess CLI audits with identical output, and a clean source-hash audit. This is not the separate-container gate.
- **C:** Offline Python-only analysis of committed synthetic/fixture evidence. No X11, input, OrbStack, model, product, or new formal allocation. Container validation remains required before claiming independent isolated reproduction.
- **U:** A finite adversarial set does not prove completeness against arbitrary corruptions or validate the original XRes behavior.

## Finding and result

Against exact predecessor raw bytes (SHA-256 `ccb9a75eefb7df73cb13dbc9191d33334fb672c2fd58fcc5fa32be998e182807`), the predecessor audit accepted six tested variants: the baseline, unexpected event, duplicate stale row, contradictory `would_call_bridge`, reordered required transition and unsupported event field. Its documented invocation exited with the usage error because the argument-count check rejects the six-element argv vector.

The hardened offline audit requires exact top-level/event/nested schemas, ordered transition cardinality, consistent stale/fresh fields, and checks the study's source hashes before emitting a pass. Its `argparse` CLI requires both predecessor `--freeze` and this study's `--study-freeze`. The retained predecessor files in `evidence/` are byte-bound to their original hashes. See `REPORT.md` for actual construction results and limits.
