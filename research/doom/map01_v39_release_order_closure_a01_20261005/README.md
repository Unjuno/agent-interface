# V39 selected release-order closure A01

## H / T / D / C / U

- **H:** The current V39 opt-in `--measurement-session` source closure uses the release-batch backend with explicit per-key owner-thread receipts and one owner-state sample after the entire key-up batch. Its selected V4→V3→V12 owner path should not call `query_keymap` between explicit key-up injections.
- **T:** On exact `main` `69dd261430cb1ed875f5a76411c4a2a54777c114`, run one inert fake-Xlib trace through the production `doom_owner_thread_release_batch_backend_v1.Backend` and production V4/V3/V12 adapters. The lower typed-backend step loop is stubbed to request two keys, `a` then `space`; tag XTest calls, XSync, owner sample, and keymap query on one monotonic clock. Independently audit source hashes, receipt identity/order, query placement, and mutation controls.
- **D:** PASS the narrow composition gate iff two identity-bound up receipts occur in requested order, the single owner-state sample begins after the second up and finishes before the cleanup query, no keymap query occurs between the ups, both rows report empty owned-key state after the sample, and no physical-authority field is promoted.
- **C:** The earlier A02 fake-display trace used a different V4 retained-input backend and observed between-UP queries. That can be an adapter/composition difference rather than behavior of the V39-selected release-batch closure.
- **U:** This probe replaces the X display and lower typed-backend operation generator. It does not exercise the complete V39 controller/Executor startup, a real X server, physical key state, task effect, useful feedback, recovery, bounded latency, threat exposure, or MAP01. It is source-composition evidence only and grants no live allocation.

## Result

The exact selected release backend emitted two identity-bound key-up receipts (`a`, then `space`) and one owner `input_state` sample after both. No `query_keymap` call occurred between the key-ups. The only observed keymap query came later during fake-owner close cleanup, after the batch sample. Both batch rows retained empty owned-key state and `physical_verification_authoritative=false`.

This resolves the source-path ordering discrepancy at the tested selected closure, but not the separate requirement for independently sampled physical state after each edge. It does not answer threat-aware policy effectiveness or Issue #59's live-control exit gate.

Reproduction: `python3 -B research/doom/map01_v39_release_order_closure_a01_20261005/probe.py`, then run `audit.py` and `python3 -B -m unittest research.doom.map01_v39_release_order_closure_a01_20261005.test_audit`.
