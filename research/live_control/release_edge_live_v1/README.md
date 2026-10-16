# Release-edge live X11 v1 — preformal freeze

Issue: #869  
BASE: `e2eaa0fb53c561852d286797d6477aeba194b7f7`  
Status: **PREFORMAL_FROZEN_NO_FORMAL_ROWS**

This directory freezes the next live measurement rung without consuming a formal allocation. Later #60 coordination comments acknowledge the O1 handoff, but the searchable current coordination state still says `FORMAL EXPERIMENT LEASE: NONE` / `LIVE MODEL/GUI/OS-INPUT AUTHORITY: NONE` for new live lanes. Therefore this branch contains no formal result and must not be represented as one.

## Pinned current-main dependencies

- `research/live_control/input_owner_v10.py` Git blob `341b3c01649943ddaad5f28431a792c4889cc36e`
- `research/live_control/input_owner_v11.py` Git blob `842071284156d3ccc647f47135ee62a9e512cb56`
- `research/doom/doom_typed_release_backend_v2.py` Git blob `cf13d630ae22a50272a766c86d7f325f352a89d7`

The per-case runner recomputes Git blob IDs from bytes and stops before X11 input if any identity drifts.

## H

Hold the Tk fixture, F8 key, 150 ms requested hold, fresh private Xvfb session, terminal keymap check, and independent application callbacks fixed. Change only the instrumentation path:

- `baseline_v10`: exact `InputOwnerV10`, ordinary `up` returns no telemetry.
- `candidate_v11`: exact `InputOwnerV11`; the exact v2 `Backend.raw` method is loaded with a test-only parent stub so the real v11 owner call is enriched with the v2 `id`/`step` lineage and emitted once.

The candidate should expose one bounded `input_release_rpc` without changing the independently observed press/release effect or terminal released state.

## T

Formal shape remains six matched pairs / 12 fresh sessions, counterbalanced by pair. One block invocation only; no same-ID rerun, replacement, threshold tuning, or extension. Each case starts a fresh `Xvfb -ac`, fresh Tk receiver, and fresh owner. The controller never reads Tk effect logs while acting. The auditor reads them only after the case.

The current branch intentionally stops before formal execution.

## D

`PASS_RELEASE_EDGE_LIVE_X11_SCOPED` requires:

1. baseline and candidate each produce exactly one independent Tk F8 press and one release in all six cases;
2. all 12 terminal X keymap checks report F8 up and owner state reports no held key;
3. candidate emits exactly one `input_release_rpc` per `up`, with matching case `id`, step, owner/intent lineage, positive ordered interval, and `grants_input_authority=false`;
4. baseline has no release RPC by construction;
5. pinned source, schedule, result, and audit integrity pass; formal invocation count is one and reruns are zero.

A release/effect regression, stale key, malformed lineage, false telemetry or authority expansion is `FAIL_RELEASE_EDGE_LIVE_X11`. Correct mechanics without unambiguous release-edge telemetry is `HOLD_LIVE_RELEASE_TELEMETRY_NOT_DISCRIMINATING`.

## C

Tk callback time is application-consumption evidence, not the physical X-server transition. XSync completion and the application callback are expected to be separate endpoints. Scheduler behavior may widen either interval.

## U

One Linux/Xvfb/Tk keyboard fixture only. No MAP01, human-tempo, token, cross-backend, production or policy-benefit claim follows.

## Excluded construction retained outside the formal allocation

One matched construction pair was run in a disposable container. The first harness attempt stopped before input because python-xlib required an Xauthority path despite `Xvfb -ac`; construction changed only setup by supplying an empty `XAUTHORITY` file.

The corrected pair observed:

- v10: Tk events `[press, release]`, terminal F8 up, ordinary `up -> None`;
- v11: Tk events `[press, release]`, terminal F8 up, one `input_release_rpc`;
- v11 RPC interval width: `291121 ns`;
- independent Tk release callback: `220221 ns` after RPC return in this one excluded case;
- Tk press-to-release intervals: v10 `150458779 ns`, v11 `150390297 ns`;
- exact v2 source was separately loaded with a parent stub and its `raw()` path correctly enriched the one release receipt with `id`/`step` while preserving `authority=false`.

Construction audit errors: `[]`.

Important limitation: the local v11 and v2 construction copies matched their Git blob IDs exactly. The local v10 copy was reconstructed from MCP text with normalized line endings and therefore did **not** match the repository blob byte-for-byte, although the executed Python text was semantically equivalent. Consequently construction is mechanics evidence only; the formal runner's exact byte gate is mandatory before any scored row.