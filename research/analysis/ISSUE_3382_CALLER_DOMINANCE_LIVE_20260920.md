# Issue #3382 — frozen adaptive caller two-tier stage dominance (2026-09-20)

This is the first scoped outcome for #3382. It is a static caller-topology result, not a live GUI, model, latency, or task-correctness claim.

## H/T/D/C/U

- **H:** Every executable path in the frozen `run()` caller that reaches `execute` is dominated by the required `final_revalidate`, including cold, reuse, local-repair, model-repair, and safe-stop branches.
- **T:** Retrieved `research/live_control/adaptive_acquisition_caller_v3.py` from main and froze it by SHA-256. A separate AST auditor ran inside Docker image `mixed-formal-2992-debian:20260920` with `--network none`. It enumerated every `local()` call site in `run()`, searched nested helpers for alternate `execute` calls, and checked the final-gate/execute topology.
- **D:** `PASS_CALLER_TWO_TIER_STAGE_DOMINANCE_SCOPED`. Frozen source SHA-256: `8517d130d7336b27e6ddfc0ee06629d2b1183070cf845c3ef4ada8adc3cd79ca`. `final_revalidate` call sites: 1 at line 392. `execute` call sites: 1 at line 399. Nested execute call sites: 0. Independent Docker audit JSON SHA-256: `f8f842c8739466a6b7abac923e46bc407065a400d67c3b22120d50dd484c0bd8`.
- **C:** The frozen caller topology satisfies the declared two-tier dominance gate for this source identity. All earlier source, result, and failure records remain unchanged.
- **U:** This does not prove receipt correctness, replay safety, live GUI behavior, model usage, latency, or application effects. Those are explicitly outside #3382's boundary.

Frozen source, source manifest, raw audit output, and auditor are under `research/analysis/caller_two_tier_stage_dominance_v2/`.
