# V12 two-key retry-order A01 (2026-10-05)

Issue #59 / PR #7910 scoped synthetic experiment. This is a research-only reproduction package, not a runtime integration patch.

## H / T / D / C / U

- **H:** If two explicit key-up deliveries are dropped, V12 terminal cleanup retries both touched keys, but set-backed retry enumeration can differ from admission order.
- **T:** Use the #7910 fake-X harness with two mapped keys: admit keycode 74, then 65; drop both explicit KeyRelease deliveries; capture cleanup KeyRelease events and final fake keymap. Compare exact current-main V12 source (main `6860b585305e539ec93896f5adcbf658cbbd8592`) to candidate source at PR #7910 head `416846ef59b08c862cca84c128d1853e16a6143a`. The current-main V12 file is identical to #7910 base `018934cdf45fcabffcc4efe25b5c7b3d59bd459f`; PR #7910 changes only that owner module and the added regression test.
- **D:** Current-main baseline is expected RED: release verification raises with keys `[65, 74]` still down, including close cleanup. Candidate is PASS in normal and optimized mode (1/1 each); explicit UP order is `[74, 65]`, cleanup retry order is `[65, 74]`, terminal fake keymap is empty and receipt says verified.
- **C:** One Python 3.14.8 fake-X implementation and two keycodes. Exact current-main owner source was used for baseline; exact PR candidate owner source for candidate. No physical X server, OS input, GUI/game, model, task effect, authority, safety, or latency claim.
- **U:** The observed retry order is not admission-order-preserving for this input/runtime. This establishes an ordering property, not by itself that reversed independent KeyRelease operations are unsafe for every workload. Issue #5156’s per-key bracket constraints and #59’s runtime integration/live-threat gates remain open. No production PR merge or formal/live allocation is implied.

## Frozen sources and execution

See `FREEZE.json` for commits, paths, SHA-256, image digest and the in-memory transformation. `outcomes.json` retains the red/green dispositions and exact observed sequence. The source snapshots and transformed test are included so another worker can rerun them without altering historical evidence.

The experiment was executed in an isolated OrbStack Docker container using `python:3.14-slim` (digest in the freeze). The fetched source and transformed test were executed from memory; their SHA-256s are frozen. To rerun from this package after checkout, mount either `main/input_owner_v12.py` or `candidate/input_owner_v12.py` as `/work/input_owner_v12.py`, mount `test_two_key_cleanup_order.py` as `/work/test_two_key_cleanup_order.py`, set `-w /work`, then run `python test_two_key_cleanup_order.py` (and `python -O test_two_key_cleanup_order.py`). The main baseline is expected to exit nonzero; the candidate is expected to pass.

## Independent audit

The assertion in the transformed harness checks the emitted two-key release sequence and final state. Independently compare the retained `raw_trace_line` in `outcomes.json`: its admission and retry arrays differ, while terminal state is empty. This audit supports only the stated fake-X ordering result.
