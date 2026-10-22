# A01 — V39 invalidation / planner interruption composition

Status: pre-run deterministic construction test. Exact source base: `f72cd82d62c9d9f3860d4fa40980c56618bf5aaf`.

Source identities:

- `research/doom/map01_overlap_controller_v39.py` Git blob `fcd97a2483327fc6812b4cd134816cfe5193bf4f`
- `research/live_control/persistent_planner_adapter_v2.py` Git blob `e2566d063f9aeba77ea74a3996625fe80425d9f6`

## H / T / D / C / U

**H:** When the current V39 invalidation helper is composed with the current persistent planner adapter, invalidation sends a matching planner interrupt and cover cancellation, requires a permitted terminal disposition plus verified empty release, refuses to admit an answer from the invalidated turn even if a completed answer arrives afterward, and permits a subsequent same-thread fresh turn to be admitted.

**T:** Execute the actual `cancel_invalidated_cover` and `PersistentPlannerAdapter` implementations with deterministic in-process fakes. Exercise three accepted terminal races (`cancelled`, `completed`, `expired`), one interrupt transport error, and six negative terminal/release controls. Record the ordered event rows and per-case disposition. No model, game, installed App Server, GUI, external provider, OS input, or real key state.

**D:** `PASS_CONSTRUCTION_SCOPED` only if all four eligible cases issue the exact matching interrupt and cover cancel, all stale answers are ineligible, each eligible case can admit only the next fresh same-thread answer, and all six negative controls fail closed. Any mismatch is `FAIL_CONSTRUCTION`; dependency/runtime setup failure is `STOP_INFRA` and is not a candidate outcome.

**C:** Deterministic fakes establish only Python control-flow composition. They do not establish real App Server timing/semantics, live threat exposure, physical key release, useful task feedback, recovery, progress, or game outcome. The separate installed-App-Server probe in PR #8380 is not repeated or treated as V39 integration evidence.

**U:** No timing distribution, failure probability, causal gameplay benefit, or cross-runtime result is estimated. Container execution was attempted for eligibility; Docker Engine answered `ps` with no running containers, while image inventory failed because containerd could not read a content blob (`operation not supported`). This local construction test therefore runs in the bundled Python only; no image was pulled and no shared container state was changed.

## Frozen command

From repository root:

```sh
/Users/taka/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 research/doom/v39_interrupt_cancel_composition_a01_20261008/run_candidate.py --out research/doom/v39_interrupt_cancel_composition_a01_20261008/candidate.json
/Users/taka/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 research/doom/v39_interrupt_cancel_composition_a01_20261008/audit_result.py research/doom/v39_interrupt_cancel_composition_a01_20261008/candidate.json
```

The candidate is invoked once. Do not rerun or overwrite its first result; corrections require a new version and path.
