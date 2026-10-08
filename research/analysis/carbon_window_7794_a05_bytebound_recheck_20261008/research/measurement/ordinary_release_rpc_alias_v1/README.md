# Ordinary release RPC transition discriminator v1

Issue: #990  
Task: `ORDINARY-RELEASE-RPC-TRANSITION-DISCRIMINATOR-20260917-001`  
BASE: `c2505f4b090fecef9caa1248dd00d28ecda56a57`

Decision: **PASS_NOOP_RELEASE_RPC_ALIAS_SCOPED**

## H

Exact current `input_owner_v10.py` returns `None` for ordinary `up` both when it injects a KeyRelease+sync because the key remains owner-held and when the key has already been released and the later `up` is a no-op. Exact `input_owner_v11.py` sees only that public result and brackets the call.

If the two hidden base outcomes receive matched clocks and metadata, current v11 should therefore return identical telemetry even though one underlying call performed a release transition and the other did not.

## T

Disposable standard-library construction only; no X11/GUI/model/input. `test_alias.py` loads the repository's exact current v11 source after verifying Git blob `842071284156d3ccc647f47135ee62a9e512cb56`, then supplies a test-only `input_owner_v10` module preserving the relevant public release ABI (`None`).

100,000 matched pairs vary owner/token/deadline/key/operation/timing while holding each pair's visible inputs exactly equal. The fake base retains a hidden witness that differs between `TRANSITION_PERFORMED` and `ALREADY_RELEASED_NOOP`; this witness is intentionally unavailable to v11.

Negative controls require base exception propagation with no receipt, non-release delegation without release telemetry, and clock-reversal rejection.

## D / result

- exact v11 Git blob gate: PASS;
- hidden transition witness differs: 100,000/100,000 pairs;
- complete v11 receipt equality: 100,000/100,000 (`receipt_mismatches=0`);
- no-op arm still returns `release_transition_interval_ns=[start,return]` plus `x11_release_and_sync_completed_before_return=true`: 100,000/100,000;
- negative controls: 3/3;
- digest: `1f897a1ccb34e944768f8008a1bf675ad113b403d8398d0611a5202fc6847e54`.

Construction wall was 4.38 s, max RSS 92,720 KB on the container; diagnostic only.

## Interpretation

Current v11 receipt is valid as a **release-RPC call envelope**. Its interval alone is not sufficient evidence that the actual physical ordinary-up transition occurred inside that interval, because the wrapper aliases a real transition and an already-released no-op under the current v10 public ABI.

Therefore a #981/#988 normalization adapter must not use current v11 `release_transition_interval_ns` as a physical-up interval unless an additional owner/backend transition witness is bound to it.

This does not invalidate #869's retained successful construction case; it blocks generalizing the receipt shape to expiry/cancel/focus-cleanup paths that may have released before the later ordinary `up` call.

## C / U

The fake base isolates information flow rather than X11 timing. Owner-local held state is not itself hardware truth. A future `transition_performed` signal would only prove a backend transition was attempted from owner-held state; independent post-release physical/application evidence remains separate.
