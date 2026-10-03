# Audit-only allocation A02 — HOLD_MUTATION_CONTROL_FAILURE

One audit CLI invocation exited 1 at the aggregate mutation gate (`ValueError: mutation_control_failure`); candidate invocations=0, retries=0, and no audit JSON was written. The eight-row reconstruction/truth comparisons precede the failed gate, but no PASS is claimed. The specific failure was a no-op mutation that relabeled an already-target track instead of a foreground track.

The correction and successful supplemental audit are recorded as distinct allocation A03 under Issue #6843. A02's failed outcome and source remain unchanged.

Batch local CI after all formal allocations were terminal reran the three mini-record construction tests and Python byte-compilation; both passed. No formal inputs or output paths were exercised by these checks.
