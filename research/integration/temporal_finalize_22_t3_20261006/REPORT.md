# #22 T3 result: early historical success is not whole-stream completion

**PASS_TAIL_FINALIZATION_ENGINEERING**, scoped supplied-container study, not public-runtime or end-to-end benefit acceptance.

One prospective hash-frozen evaluation completed24/24 receiver cases. Driver is also the controlled source process. Actual receiver exits24/24 zero; actual runner exit0; supervising command exit0; timeouts/forced cleanup/evaluation retries/replacements/postfreeze source changes0. Independent raw-only audit:1080 checks, errors=[],source_errors=[],execution_ok=true;12/12 effective byte-changing corruption controls rejected. Eight real-pipe unit methods pass normally and with Python optimization. Separate implementation by the same author is not independent human review.

| API (12 cases each) | Complete transport | Protocol error | Unresolved transport | Historical-only reply |
|---|---:|---:|---:|---:|
| Unchanged T2 repeated wait | 0 | 0 | 0 | 12 |
| Explicit finalize | 2 | 8 | 2 | 0 |

Candidate normal close/EOF2 cases completed; missing-close, truncated JSON, message-after-close, and foreign epoch2 cases each were correctly rejected; open-writer2 cases returned unresolved at the explicit caller deadline. First receipts stayed unchanged24/24 and their historical SATISFIED remained true. The baseline is correct for its own history-only contract: these are not12 false success claims. The new operation supplies additional transport evidence, incurs additional I/O/waiting, and is not claimed faster.

## What changes

New finalize_reader.py subclasses the exact existing research TimedReader without editing it or its three parser/monitor dependencies. Unlike wait(), finalize() does not return merely because the historical monitor is terminal. It reads until the unchanged parser validates close plus EOF, detects a protocol error, or the fixed caller deadline expires. Same-pipe partial state survives a timeout. No new scheduler, reconnect, replay, task action, authority, or wall-clock source event is introduced.

A valid historical A/B observation can coexist with later malformed transport. Report those two facts separately; neither protocol closure nor historical satisfaction is current-world evidence or permission to execute an action.

## Evidence and chronology

Source-hash freeze was posted in #22 comment6014035650, after commitfc6bd1d73ea42f54c6d01f7b186b40b9ab3984be and exact Git blob readback, BEFORE this evaluation. This was public hash commitment; full source publication follows the first outcome, not earlier. Result comment6014058391 records the first outcome before packaging.

- FREEZE SHA256 d137c6b6b8b74c01606569a54da40b663564ce72ed006c2a0ac85697d05ed9fc.
- Raw118990 bytes SHA256 bc2cf2f5b9a460b7e352e831d76f5b8a5725fdb564279cd45368d047dae91ccd.
- AUDIT SHA256 06b81f7fc738f512433e7d1a6591033dd87c1ba491db00da33e24f8b65ae757b.
- Actual runner EXECUTION SHA256 3a1ce171fafd852e7d1e8a7fce59d066930c8f6b25e8154eb597729218e3fb7a.

construction/ preserves the initial RED baseline test, exact old test version, GREEN test receipts, four excluded process cases and184-check construction audit. Before implementation the test helper used None as a default, which would hide an explicit invalid None argument; it was corrected to an object sentinel before GREEN/freeze. This is a pre-evaluation test correction, not a post-result rescue. No old live/measurement allocation was rerun.

The prior T2 full ZIP remains conversation-hosted unchanged. Four dependency sources are byte-identical (PROVENANCE.json); the old raw outcomes are not reused as new trials or asserted fully republished here. The old #4220 missing-outer-exit HOLD is unchanged.

## Scope / environment

Provided Linux x86_64 container, CPython3.13.5, ordinary anonymous pipes/nonblocking reads/DefaultSelector; exact version/CPU/affinity in ENVIRONMENT.json. This is not WSLc, Docker, OrbStack, an image-attested run, or a workload on the user's shared CPU/GPU workstation. No network in the experiment, installation, model, GUI, OS task input, user data, or public-runtime modification. No speed/token/effect/energy measure or natural fault probability is claimed. Recorded clocks are diagnostic provenance;50ms is the declared caller test budget, not a recommended default or hard-return-time guarantee.

Exclusive same-pipe ownership and a cooperative finite protocol are required. No multithreaded concurrent API use, descriptor reuse, source authentication, reconnect, persistence, arbitrary application completeness, global event coverage, currentness, cancellation, or active-input release is established. An error can stop before reading the entire invalid tail. Completion after EOF applies only to the bytes delivered on that pipe.

## Integration decision / remaining roadmap

For callers needing both early feedback and validated stream retirement, keep wait-history and finalize-transport as explicit separate operations. Do not promote either to task success. This isolated helper is not wired into public CLI/MCP. #22/#57/#59 and the global ROADMAP remain open. Source/evidence delivery is a PR mechanism, not research success. Main integration requires applicable exact-head checks and review; owned branch must stay while any open PR depends on it.
