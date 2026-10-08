# Existing compiled-spec shape follow-up

Status: **PASS finite integration shape; HOLD exact runtime execution.**

The follow-up uses the state-machine shape already retained in `compiled_runtime_cross_domain_compat_v1` continuous control: `surface_present` plus `zone ∈ {LEFT, RIGHT, GOAL}` selects `move_right`, `move_left`, or completion. It adds one hidden admission guard per movement action to isolate the staged-dependency mechanism without changing the method's branch structure.

All current combinations were enumerated after a plan-time LEFT or RIGHT selection:

- current zone: LEFT / RIGHT / GOAL;
- surface present: false / true;
- selected/inactive action guards: false / true;
- unrelated nuisance bit: 0 / 1.

Total: **96 states**.

Ground truth allows the old planned action only when the surface is present, the current zone still selects the originally planned action, and that action's current admission guard is true.

| method | stale executes | false rejects | correct execute | correct reject |
|---|---:|---:|---:|---:|
| state union | 0 | **4** | 4 | 88 |
| staged, no branch revalidation | **40** | 0 | 8 | 48 |
| staged + branch revalidation | **0** | **0** | 8 | 88 |

The canonical digest in this finite fixture is computed from the complete current state and is independent of projected dependency membership, so this test does not change evidence-identity semantics.

This strengthens the prior generated and SQLite counterexamples using an existing compiled-method shape, but it is not execution of the exact `compiled_gui_interface_v1.py` runtime. The current environment does not provide an arbitrary GitHub Actions dispatch path, and the exact Chromium-v5 environment remains SETUP_BLOCKED under #184.

## Decision

Advance only **staged + branch-predicate revalidation** to an exact-runtime development allocation. Keep batching calibration and canonical evidence changes out of that allocation.
