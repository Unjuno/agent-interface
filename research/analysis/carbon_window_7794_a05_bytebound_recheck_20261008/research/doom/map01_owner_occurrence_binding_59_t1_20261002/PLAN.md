# #59 owner occurrence-binding successor T1

## H / T / D / C / U

- **H:** The unchanged #5630 `InputOwner` admits repeated same-key pulses, but the owner event contract may omit a stable per-occurrence identifier and a per-explicit-up key-state sample even when each occurrence has its own explicit down/up cycle.
- **T:** On an in-process fake Xlib transport, call the pinned owner for `W down → W up → W down → W up → close` under one lease/intent. Capture both admission replies, owner records, fake-server events and every fake keymap query. Candidate once, separate raw-only audit once, no retries.
- **D:** `PASS_OWNER_BOUNDARY_SCOPED` only if four fake events alternate press/release, two admissions and two explicit-up brackets appear in monotonic order, both sides lack `interval_id`, the two brackets share owner/intent/keycode/key and no per-up query occurs (only terminal close may query). Any mismatch is a fail.
- **C:** Current-main anchor `f590fde44595a70eb1752a4940fbc3f119b80a66`; owner source pinned to #5630 head `288d0498d11cf16657e523a04616bf4f49cd94f4`, Git blob `c40db07e596b31557590cec5e90f6ab651573476`. Windows CPython host, deterministic fake transport.
- **U:** Source-level owner behavior only. No real X server, physical keyboard, held-key measurement, application delivery/effect, model, GUI, game/MAP01, latency, safety, or Docker/container claim. This is not the live allocation requested by the r133 roadmap.

## Why this is a distinct successor

The prior T0 exercised one explicit up plus owner cleanup and its auditor incorrectly expected the cleanup row to retain a key name; its `FAIL_AUDIT` is preserved unchanged. This successor instead completes two explicit up cycles, for which the pinned source records the key name, and predefines the correct identity fields and cleanup behavior. It tests the repeated occurrence path end-to-end through the unchanged owner rather than reinterpreting or rewriting T0.

## Frozen procedure

1. `python candidate.py` once.
2. `python audit.py` once, separate process; auditor reads raw only.
3. Preserve the first result. No retries or edits to frozen inputs after candidate execution.
