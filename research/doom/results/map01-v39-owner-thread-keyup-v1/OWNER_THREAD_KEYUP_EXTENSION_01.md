# Owner-thread key-up receipt extension 01

Status: synthetic construction PASS. No live X11/game claim.

## H — Hypothesis

A caller-side bracket around `InputOwner.call("up")` is insufficient to distinguish an explicit owner-thread XTest KeyRelease/XSync from a queued no-op after cancellation cleanup already released the held key. An explicit normal-release candidate requires exactly one owner-thread receipt, bound to the same owner, key, intent token, and lease deadline, ordered inside the caller bracket. Missing or malformed owner evidence must fail closed through batch verification and offline analysis.

## T — Test

Added fake-Xlib owner controls for explicit up and cleanup-before-queued-up, a transition wrapper join control, a backend batch-gate negative control with the owner receipt disabled, and an analyzer negative control with the batch owner receipt absent. Combined these with #7395 malformed-history and caller-bracket checks and #7405 terminal-cleanup receipt handling.

## D — Data and execution

- Base: #7405 refreshed head `50c5d5ffe69f67c6ad56811496cec93694929cfe`, stacked on #7395.
- Candidate code and tests: `91782ce69572173d1d068d34c9fccff967d81a27`.
- `python -m unittest discover -s research/doom -p "test_doom_typed_release_backend_v3.py" -v`: **28/28 PASS**.
- `python -m unittest discover -s research/doom -p "test_analyze_map01_direct_retained_input_v1.py" -v`: **4/4 PASS**.
- `python -m unittest discover -s research/live_control -p "test_input_transition_owner_v4_receipt.py" -v`: **4/4 PASS**, including two inherited owner tests.
- Python compilation of changed owner, transition, backend, analyzer, session, and test modules: PASS.
- `git diff --check`: PASS.
- Fake Xlib only; no X server, game, container, or live allocation was run.

SHA-256 of candidate implementation and regression files:

| File | SHA-256 |
|---|---|
| `research/live_control/input_owner_v11.py` | `a73c63d32a9f55574f3e5b32e67021844c923b3d133699ffd5c9bf971bd12330` |
| `research/live_control/input_transition_owner_v4.py` | `dd020956187d7be893a093b054f220603183e32560979639a281ce63daab7df9` |
| `research/doom/doom_typed_release_backend_v3.py` | `6d8b655164361851ea3e8f829c2ecc1232a4c7278a768231d7e4461d6e4c46dc` |
| `research/doom/analyze_map01_direct_retained_input_v1.py` | `3c5277244f7cf8b173f351744454d74fdae20a0b321ec581f2d512dfed0e0c74` |
| `research/doom/test_doom_typed_release_backend_v3.py` | `2b7ecabf433bfbc3d9549e5410122dcfa0b57c1cb67e91019891f570960a5fb5` |
| `research/doom/test_analyze_map01_direct_retained_input_v1.py` | `0ff26f9235a90c4d69e659606a362df65dc76e3d300748ec7753ba158e8d4460` |

## C — Conclusion

The synthetic owner model distinguishes an explicit KeyRelease/XSync from a no-op after cleanup. The backend and analyzer reject missing owner-thread acknowledgement. The receipt marks server sync completion only; it does not prove physical key state or application consumption.

## U — Uncertainty and next gate

This extension does not establish environmental change response, physical input release, finite recovery, task effect, latency/resource improvement, or the complete Issue #59 matched-threat control requirement. Review and integrate the #7395/#7405 cleanup stack before this change. Any live experiment requires a fresh authorized allocation and its full preflight; none is active or claimed.
