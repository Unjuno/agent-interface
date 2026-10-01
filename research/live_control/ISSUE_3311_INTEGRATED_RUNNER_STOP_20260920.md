# Issue #3311 — integrated efficiency runner stopped during container dependency resolution (2026-09-20)

This is a preserved setup STOP, not an efficiency result. No historical result was rewritten and no RETAIN/REJECT claim is made.

## H/T/D/C/U

- **H:** The frozen six-task, three-arm integrated workflow can be executed from the main source bundle inside the pinned Docker runtime, producing fresh cold/warm/invalidation/repair evidence.
- **T:** Retrieved the main source bundle for `research/live_control/run_integrated_efficiency_live_v1.py` and its local imports, then attempted import/execution inside `mixed-formal-2992-debian:20260920` with `--network none`, `PYTHONPATH=/workspace`, and a read-only source mount. The image digest was `sha256:766abfd10382ab8b59ed793094a685481190f840d338b7bc4664ca162a2da619`.
- **D:** The runner stopped before allocation. Initial import failed on missing `jsonschema`; a pinned host-side install of `jsonschema==4.23.0` then failed in the Linux container because `rpds.rpds` was not loadable. A pure-Python-compatible `jsonschema==4.17.3` attempt then stopped on missing `pyrsistent`. No task, model, GUI, token, latency, or effect row was emitted.
- **C:** `STOP_INTEGRATED_EFFICIENCY_RUNNER`. The fresh allocation gate was not reached; this is not evidence for or against integrated efficiency.
- **U:** A reproducible Linux dependency bundle or image build recipe is still required. Do not substitute host wheels or a synthetic runner. Preserve #3311's `HOLD` and rerun only after the exact dependency closure is frozen for the container architecture.

The attempted source bundle and STOP log are under `research/live_control/integrated_efficiency_stop_20260920/`.
