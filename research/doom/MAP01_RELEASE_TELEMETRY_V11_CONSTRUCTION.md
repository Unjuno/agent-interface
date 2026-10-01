# MAP01 ordinary-release telemetry v11 construction

Status: **CONSTRUCTION PASS — integrated X11/DOOM execution still required.**

Base: `e731bd84fedbaad30bb8f70c4de3fbd9b9049308`.

Task: `O3-G2-OWNER-RELEASE-TELEMETRY-001`.

This construction follows the retained held-input result that exact ordinary
key-up time is not identifiable in v10 logs. It changes measurement only; no
recovery policy, planner schema, guard, hold duration or formal allocation is
changed here.

## Mechanism

`input_owner_v11.py` subclasses the frozen v10 owner and leaves its owner thread
unchanged. For ordinary `up` and `button_up`, the caller records one monotonic
clock sample immediately before the existing v10 call and one immediately after
that call returns. The existing v10 implementation performs X11 release plus
`d.sync()` inside that call.

The receipt therefore interval-censors the release transition to:

- `call_started_ns`: owner RPC has not yet completed the requested release;
- `call_returned_ns`: the v10 release + X11 synchronization has completed;
- `release_transition_interval_ns`: the enclosing interval.

This is deliberately **not** called a hardware key-up time, continuous physical
state proof or application-consumption time.

`doom_typed_release_backend_v2.py` binds keyboard admission and release records to
`program id`, `step`, owner identity and the executor lease intent token. Missing
program/step context rejects **before** the owner call so the measurement build
does not create an unattributed OS-input edge. The existing aggregate
cancel/expiry `owner_release` path remains separate and stronger because it also
queries empty input state.

Pointer release uses the same v11 owner. The inherited pointer helper already
adds program/step provenance to any non-`None` owner record, so `button_up`
receipts become visible without changing pointer action semantics.

## Verification completed in this construction

Two pure contract suites were executed without X11 by replacing only the inherited
owner call / previous backend execution boundary with deterministic fakes.

- `test_input_owner_v11.py`: **5/5 PASS**
  - key release bracket;
  - button release bracket;
  - non-release v10 result preservation;
  - no fabricated receipt on underlying owner failure;
  - fail-closed unexpected v10 release payload.
- `test_doom_typed_release_backend_v2.py`: **5/5 PASS**
  - down/release program-step provenance;
  - missing context rejected before owner call;
  - failed release does not falsely clear backend hold tracking;
  - execute context is cleared on error;
  - nested telemetry context rejected.

These are construction tests, not the repository's Windows/WSL integration suite.
They establish the wrapper/binding logic only.

## H / T / D / C / U

**H — falsifiable hypothesis.** A telemetry-only wrapper can reduce ordinary
release timing uncertainty from a whole post-snapshot interval to the duration of
one existing InputOwner RPC, while preserving v10 input authority and release
semantics.

**T — minimum integration test.** On a separately versioned MAP01 session, submit
at least one ordinary completed keyboard hold and one pointer press/release or
keyboard chord. Require each ordinary release receipt to have matching program,
step, owner and intent identity; ordered call timestamps; and no change in the
existing terminal empty-release audit. Include one cancellation control and one
underlying-owner failure/focus-loss control. No model call is required for this
instrumentation test.

**D — decision.** Construction PASS is already satisfied by 10/10 pure contract
checks. Integration PASS requires real X11 traces with release interval width
small enough for the intended occupancy metric and unchanged safety/release
behavior. FAIL if provenance is missing, release intervals overlap the wrong
program/step, or the instrumentation changes admission/cancellation semantics.
UNCERTAIN if scheduler stalls make the caller-side RPC interval too wide; that
would justify moving the timestamps inside a new owner implementation rather than
pretending the edge is exact.

**C — counter-hypothesis / break modes.** The caller thread may be descheduled
around the owner return, widening the interval. `d.sync()` confirms X-server
processing but not application semantic consumption. An external input actor can
still alter physical state. A future session implementation could bypass
`Backend.raw`, which must fail the provenance audit rather than silently pass.

**U — uncertainty.** Dominant new uncertainty is the release RPC interval width.
It is structural censoring, not sampling noise. The useful-effect clock remains a
separate unresolved measurement: MAP01 terminal scoring cannot yet timestamp the
first independent useful task result.

## Next gate

Do not merge this construction as evidence of improved control and do not start a
recovery-policy comparison from it alone.

The next integration generation should combine:

1. this ordinary-release receipt;
2. a scorer-only, controller-invisible, timestamped independent progress signal;
3. the existing model-wait / typed health-ammo / lease / revocation timeline.

That synchronized trace is the high-information Product Hunt demonstration
candidate: the game continues while the frontier model waits, local authority is
visible and bounded, actual input release is bounded, stale authority can be
revoked, and useful progress is scored independently. A failed run remains useful
because the same timeline localizes the failure instead of relying on a hero-run
narrative.
