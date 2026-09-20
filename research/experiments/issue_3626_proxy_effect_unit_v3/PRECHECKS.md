# Construction and preflight record

- Container runtime: OrbStack Docker; pinned Linux/arm64 image is recorded in `FREEZE.json`.
- Unit gate: deterministic proxy pixels, `wait_state` signature/callsites, root-window pointer mask query (released and pressed controls), and two-target synchronization contract.
- GTK/Xvfb construction smoke must produce one acknowledged visible counter transition 0→1; excluded from formal rows.
- Formal launcher checks local image ID/platform, source/preregistration/freeze hashes, unit tests, construction smoke, and empty output paths under `set -euo pipefail` before exactly one formal invocation.
- Ambiguous formal rows require two ready PIDs and two viewable distinct XIDs before pre-dispatch state; otherwise formal result cannot pass.

## Formal-03

- One invocation, 28 rows, zero runner exceptions; no retries.
- Independent audit: `PASS_PROXY_BINDING_EFFECT_UNIT`, zero errors, all four corruption challenges detected.
- All 28 rows had a successful Button1-up root-window query and process/socket cleanup.
- All four ambiguous controls were established before dispatch with two ready fixture PIDs and distinct XIDs; all yielded without emissions/effects.
- See `evidence/formal-03/REPORT.md` for exact hashes, counts, and scope limits.
