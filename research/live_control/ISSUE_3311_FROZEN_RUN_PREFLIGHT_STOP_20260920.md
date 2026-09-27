# Issue #3311 — frozen integrated runner stopped at preflight CLI boundary (2026-09-20)

This is a second, later setup STOP after the Linux dependency bundle was rebuilt. It is not an efficiency result and does not replace the earlier STOP record.

## H/T/D/C/U

- **H:** The exact preregistered source bundle from the frozen allocation can reach schema preflight and then execute the six-task three-arm workflow inside the pinned container.
- **T:** Reconstructed all preregistered source SHA-256 identities exactly (`mismatch count 0`), added the transitive `unix_json_deadline.py` import, and built Linux-compatible `jsonschema==4.23.0` dependencies inside a Docker preparation container. Ran the frozen bundle in `mixed-formal-2992-debian:20260920` with `--network none`.
- **D:** The runner reached `preflight_call` but stopped before any allocation because the frozen `schema_preflight_v1.py` requires `/mnt/c/Users/junny/AppData/Roaming/npm/node_modules/@openai/codex/bin/codex.js`; the pinned Linux image contains no such file or codex binary. No model call, GUI session, task, token, latency, or effect row was emitted.
- **C:** `STOP_INTEGRATED_EFFICIENCY_PREFLIGHT_ENVIRONMENT`. Source identity and Python dependencies are no longer the blocker; the required model CLI boundary is unavailable in the pinned container.
- **U:** A reproducible container-native CLI/model boundary or an explicitly revised preregistration is required. Do not create a placeholder CLI or infer efficiency from preflight-only execution. The #3311 HOLD remains.

Image: `mixed-formal-2992-debian@sha256:766abfd10382ab8b59ed793094a685481190f840d338b7bc4664ca162a2da619`.

The exact frozen source manifest and raw stop record are under `research/live_control/integrated_efficiency_stop_20260920/frozen_preflight/`.
