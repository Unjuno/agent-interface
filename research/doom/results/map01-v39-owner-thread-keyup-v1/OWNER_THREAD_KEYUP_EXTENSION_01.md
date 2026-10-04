# Owner-thread key-up receipt extension 01

Status: synthetic construction PASS. No live X11/game claim.

## H — Hypothesis

A caller-side bracket around `InputOwner.call("up")` is insufficient to distinguish an explicit owner-thread XTest KeyRelease/XSync from a queued no-op after cancellation cleanup already released the held key. An explicit normal-release candidate requires exactly one owner-thread receipt, bound to the same owner, key, intent token, and lease deadline, ordered inside the caller bracket. Missing or malformed owner evidence must fail closed through batch verification and offline analysis. Timestamp ordering must also prove that input acknowledgement preceded the release bracket; otherwise retained duration can be negative while marked measurement-ready.

## T — Test

Added fake-Xlib owner controls for explicit up and cleanup-before-queued-up, a transition wrapper join control, a backend batch-gate negative control with the owner receipt disabled, and analyzer controls for absent nested receipts, forged summary Booleans, and release-before-ack ordering. The analyzer independently checks nested owner/key/token/deadline identity and owner-thread timestamps inside the caller bracket. Combined these with #7395 malformed-history and caller-bracket checks and #7405 terminal-cleanup receipt handling.

## D — Data and execution

- Base: #7405 refreshed head `4284bd89d9876a6ce0fa5b350a84025dd6e5806f`, stacked on #7395.
- Owner-receipt candidate implementation and tests: `a119881f70211ffd428a28b96677e689d35db263`.
- Follow-up analyzer order guard and regression: current working change on top of #7402 candidate `dc7b2f478fd00181b36789920bd96bc0e8254330`.
- `python -B -m unittest discover -s research/doom -p "test_doom_typed_release_backend_v3.py" -v`: **28/28 PASS**.
- `python -B -m unittest research.doom.test_analyze_map01_direct_retained_input_v1 -v`: **6/6 PASS**.
- `python -B -m unittest discover -s research/live_control -p "test_input_transition_owner_v4_receipt.py" -v`: **4/4 PASS**.
- Python compilation of changed analyzer and test modules plus backend modules: PASS.
- `git diff --check`: PASS.
- WSLc A01: **STOP before container creation**. Its frozen `/mnt/c/w/keyupr3` bind source failed WSLc argument validation; no test process ran. Raw output, exit, container snapshot, and independent audit are retained in `results/map01-retained-time-analyzer-order-wslc-a01-20261004/`.
- WSLc A02: **6/6 PASS** in the pinned cached Python 3.12 image, with `--pull never`, `--network none`, source checkout mounted read-only, and command/output/hash provenance plus independent audit retained in `results/map01-retained-time-analyzer-order-wslc-a02-20261004/`. WSLc reported that swap limits are unsupported; the declared 512 MiB limit is not treated as proven strict total-memory enforcement.
- WSLc tested only the pure synthetic analyzer; no X server, game, or live allocation was run.

SHA-256 of owner-receipt candidate implementation and regression files (pre-existing candidate revision):

| File | SHA-256 |
|---|---|
| `research/live_control/input_owner_v11.py` | `a73c63d32a9f55574f3e5b32e67021844c923b3d133699ffd5c9bf971bd12330` |
| `research/live_control/input_transition_owner_v4.py` | `dd020956187d7be893a093b054f220603183e32560979639a281ce63daab7df9` |
| `research/doom/doom_typed_release_backend_v3.py` | `ad82198625f5cd6690093bf258ea303d547b6bad279456bf95f3facfb8398282` |
| `research/doom/test_doom_typed_release_backend_v3.py` | `25ac719787751db6fd3174a714e6238cfdae12ba3b248bd4f4543519b7cffe74` |

SHA-256 of the current analyzer order-guard candidate:

| File | SHA-256 |
|---|---|
| `research/doom/analyze_map01_direct_retained_input_v1.py` | `73d32c1d1a520f26daa6abce458d2fdbb9d19267d3c3387a9b53a9947a90a011` |
| `research/doom/test_analyze_map01_direct_retained_input_v1.py` | `c24d7a734624423f5bebb4592bebb8cb25f9e1cd0288647f85f04c3306749320` |

## C — Conclusion

The synthetic owner model distinguishes an explicit KeyRelease/XSync from a no-op after cleanup. The backend and analyzer reject missing owner-thread acknowledgement. The timestamp-order guard additionally rejects malformed event sequences that could otherwise create a negative retained-time lower bound. The receipt marks server sync completion only; it does not prove physical key state or application consumption.

## U — Uncertainty and next gate

This extension does not establish environmental change response, physical input release, finite recovery, task effect, latency/resource improvement, or the complete Issue #59 matched-threat control requirement. Review and integrate the #7395/#7405 cleanup stack before this change. Any live experiment requires a fresh authorized allocation and its full preflight; none is active or claimed.
