# R264 expiry-freeze audit (2026-11-17)

## Decision

**Do not execute R264.** Its frozen description and conditions specify a 30 s
lease, a 60 s SHIFT hold, then delayed SHIFT-up and a second click. The pinned
runner instead exercises the separate producer-exception recovery path. It
cannot answer the frozen expiry question. The trial directory does not exist;
no R264 input was sent.

This is a preflight stop on a frozen but unused ID. R264 remains unattempted and
must not be modified or repurposed. A correct live successor needs a new ID,
new conditions and a current-main source pin.

## Direct source cross-check

The local frozen packet is
`private-packets/map01_native_windows_current_main_r180_abnormal_exit_20261114/runner-candidates/r264-current-main-expiry-delay/`.
Its `README.md` describes the delayed-operation expiry experiment, while
`conditions-r264.json` contains both the expiry sequence and producer-exception
fields (`fault`, UNKNOWN source projection, and exception-recovery scope).
Freeze-file SHA-256 is
`96bb2f65ff24471e0de0361733b7e3c6971a1d4108bc3a9753e713022e975ad4`;
condition-file SHA-256 is
`283c053bfd7b53595cee5b19b51b483cfc4220f34b39e7084d3410ffd8077a8e`.
The condition pins `runner-candidate.py` SHA-256
`cd49d5cf3e34eef53b7661cbc4f338cf6188bb06db2990e0de1cda50a05bfb5c`.

At that exact pinned file hash, the runner:

- starts its MCP server from `server_with_exception.py`;
- constructs a single LEFT-down → 120 ms dwell → LEFT-up program, with no
  30 s lease hold, 60 s wait, SHIFT hold, or post-expiry second click;
- polls for an UNKNOWN producer-exit / separate cancellation-recovery result
  for 20 s, not the frozen 45 s expiry-result window.

These differences are on the action path and experiment endpoint, not wording.
Running it would produce a different experiment under R264's label. The
correct expiry runner already exists in the separate R263 candidate packet as
`runner_expiry.py` and uses `server_with_expiry.py`, but R263 is itself old-source
and its freeze is consumed. It is a construction reference only; it cannot be
substituted into R264 after the freeze.

## Current state and source applicability

- Current main: `4000f9f8607dcf72bb70b1a1193245dbf2b4919b`.
- R264 frozen source: `a5a2e04a70f5f81eae072e757a303045a469b580`.
- Between those revisions, 37 runtime files changed (5,431 insertions / 159
  deletions). R264 is not a current-main freeze even apart from the runner
  mismatch.
- No R264 trial directory exists.
- Host GZDoom process count: zero at the audit; Computer Use inventory had no
  GZDoom window.
- Persistent input custody at audit: `clear`, no pending obligation, revision
  985. R264 had captured revision 880 and a different state-file hash, so its
  preflight would refuse even if its runner matched its protocol.

## Current-main contract recheck

On exact main `4000f9f8607dcf72bb70b1a1193245dbf2b4919b`, three focused synthetic
tests passed 3/3 normally (11.243 s) and 3/3 under optimized CPython `-O`
(10.114 s). The test names and captured logs are in `normal.log` and
`optimized.log`. They cover startup expiry refusing late dispatch, public
caller cancellation timing/exactly-once recovery, and a zero-native-action
expired start gate. They do not execute the R264 runner, exercise a live expiry
wait, or establish a MAP01 effect.

## Next valid step

Build a new single-arm current-main freeze from the R263 expiry runner, first
cross-checking the action program, lease, delayed operations, result horizon,
and expected receipts against one condition file. Freeze a distinct ID only
after the current custody file, neutral input state, pinned assets, source
commit/tree and runner hashes all match. This can produce one scoped live
expiry/release/effect observation; it still will not measure #57 integrated
model-token efficiency. That larger evaluation remains open.

