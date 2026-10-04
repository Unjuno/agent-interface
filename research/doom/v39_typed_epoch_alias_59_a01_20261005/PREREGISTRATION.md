# V39 typed epoch exact-type boundary A01

## H / T / D / C / U

**H.** The current-main typed observation pipeline may accept a health or ammo reader row whose `sequence` or `capture_ns` is a Boolean or float equal to the enclosing integer epoch, because Python equality aliases `True` with `1` and `1.0` with `1`. This would weaken exact typed-epoch binding at `build_action_snapshot`.

**T.** Freeze the exact current-main `doom_typed_observation_v1.py` and its imported action-validity schema module. Run the real `extract_typed_observation` → `build_action_snapshot` pipeline once with a 2×2 in-memory RGB frame, deterministic clock, both required typed readers, and one fixed valid contract. Compare an exact-integer control with eight single-field mutations: Boolean and float aliases for `sequence` and `capture_ns`, applied independently to health and ammo rows. No production source, game, model, GUI, OS input, or shared resource is modified or started.

**D.** The control must be accepted. The exact-type contract gate passes only if all eight malformed rows are rejected before a snapshot is emitted. Any malformed row accepted by the source is `FAIL_CLOSED_EPOCH_IDENTITY_GAP`; any incomplete invocation is HOLD. A separate raw-only auditor must reconstruct the actual acceptance outcomes and compare every row to the frozen decision rule.

**C.** The in-tree HUD readers may currently be the only producers and may always copy validated metadata. This test does not show such readers emit malformed values; it tests whether the snapshot boundary itself enforces its stated exact-epoch contract against malformed reader output.

**U.** One deterministic host construction test, one source version, one valid frame, and one signal contract. It establishes neither live behavior nor exploitability, input authority, feedback quality, recovery, task effect, threat response, latency, safety, or MAP01 completion. No live allocation is consumed.
