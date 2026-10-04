# Post-run source-composition limitation (read-only review)

Recorded 2026-10-04 after frozen `current-main-a01`; this note is not part of the frozen test protocol and did not rerun or relabel that result.

Current main's V13 owner (`research/live_control/input_owner_v13.py`, Git blob `f10f2d05dcaa63c35b51c8f38b737753574b8fa0`) derives from V11 and overrides `_run`; its `owner_release` cleanup row retains a single verification time and has no `key_release_intervals_ns` field.

Main now also retains PR #7542's six-module/13-test fixed-order composition fixture at `research/live_control/batch_fixture_composition_59_4d74_20261004/`. Its frozen V12 owner source (blob `da1a0b496572f3b853a84a94451e6824369a49b0`) has per-key cancellation intervals and is composed with Executor V13, V4, and related lease modules. That package's source list does not include the current `input_owner_v13.py`; PR #7542's report also states that it made no runtime-source edit. It therefore does not test the ordinary V13 `input_release_rpc` return through the V3/V4 boundary.

A01 complements that retained V12/Executor V13 fixture by testing the ordinary V13 owner return through V4 and the current batch consumer. Neither package demonstrates one integrated runtime stack that preserves ordinary V13 RPC evidence and V12 cancellation intervals together. Any adoption must explicitly compose or factor both paths and then freeze/test the resulting source graph. No runtime, physical-input, or cancellation-interval adoption is claimed here.
