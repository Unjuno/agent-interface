# MAP01 recovery mechanics development v2 — retained result

Status: **PASS real MAP01 mechanics / measurement integration; no useful-control efficacy claim.**

Run `34972531032` was the first and only `map01-recovery-mechanics-dev-02` workflow execution and held `PASS_CANONICAL_GLOBAL_OWNER`. The artifact contains 68 files / 3,062,661 bytes and has SHA-256 `3cdb33fe41d39ea21f864ab3a6f87cda0b92336adf2cab73b3d28519f158e2f1`.

Dev-01 remains failed. V2 repaired only the retained-input join: release-batch `(intent_token,key)` identity now binds the id-less `input_admission` rows. Nine regressions, including the exact dev-01 timestamps, passed before the live pair.

On the same fresh seed-990615 development condition and frozen 600 ms accounting window:

- coast admitted **0** inputs and therefore retained **600.000 ms** no-input upper bound;
- bounded recovery admitted one `a` hold with **275.070–275.719 ms** retained input (0.649 ms censor width);
- recovery no-input upper bound was **324.930 ms**, a reduction of **275.070 ms** (45.845% of the 600 ms window);
- both programs completed and ended in independently verified empty input;
- scorer missed periods = 0 and controller-visible scorer leaks = 0;
- strict five-field terminal scorer agreement passed in both arms;
- both independent gameplay scores were 0 kills / 0 deaths / no exit, so no useful-outcome advantage was observed.

This closes the development question: the real ViZDoom/X11 v13 stack can carry separately admitted bounded recovery authority through the measurement path and measure its reduction in input-free wait time without weakening release/scorer invariants. It does **not** establish that the recovery action is useful, because the action was fixed development input and no model call occurred.

The next formal gate must not reuse the stale v2 prerequisites. It should freeze a new recovery matched version that references protocol-valid measurement live-04 and the workflow-path-global allocation owner, then acquire a distinct runner/formal lease. A mechanism-only result must remain distinct from an efficacy claim.
