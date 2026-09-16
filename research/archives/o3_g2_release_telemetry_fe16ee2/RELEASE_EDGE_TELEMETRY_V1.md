# Release-edge telemetry v1

Task: `O3-G2-RELEASE-TELEMETRY-001`  
Base: `f678afa8eb7b1db1da7cfd9a15ff65d4c146d74d`  
Scope: versioned telemetry-only runtime successor plus offline regression. No controller selection, recovery policy, model call, GUI action, OS-input live run, or formal allocation.

## Why this exists

Two retained analyses now independently agree on the blocking measurement defect: `input_owner_v10` timestamps key-down admission/acknowledgement but ordinary key-up returns no timing record. The retained v39 trace can therefore bound normal release by source ordering, but it cannot identify an exact ordinary release edge. The correct next move is instrumentation, not a recovery-policy change.

## Design

### `input_owner_v11.py`

`InputOwner v11` subclasses v10 instead of copying or mutating the owner thread. Every operation except `up` delegates directly to v10. For `up` only it records:

- `release_requested_ns`: immediately before the synchronous v10 `call('up', ...)`;
- `release_ack_ns`: immediately after that call returns. Under the frozen v10 contract, return occurs only after the owner thread has processed ordinary key-up and completed `d.sync()`;
- `release_attribution`: `ordinary_up`, `superseded_before_request`, or `raced_owner_release`, using the lease's independently recorded owner-release interruption evidence;
- owner/deadline identity and `grants_input_authority=false`.

This deliberately does **not** claim that `release_ack_ns` is the X server's exact physical transition timestamp. It is a conservative caller-side post-sync acknowledgement boundary.

The wrapper takes no pre-release state sample. That avoids inserting an extra owner round trip before the release whose timing is being measured.

### `doom_typed_release_backend_v2.py`

The v2 DOOM backend opts into v11 and preserves the inherited policy. On key-down it emits the same admission record as before. On key-up it emits the v11 release record and then performs a read-only `query_keymap()` through the already-open session display connection.

The added fields are:

- `physical_key_down`;
- `physical_verified_up`;
- `physical_verified_ns`;
- `physical_verification_source=session_display.query_keymap`;
- `physical_verification_authoritative=false`.

The physical sample is intentionally non-authoritative because another actor can press/release the same key and a sampled state is not a continuous occupancy trace. A query failure is retained in `physical_verification_error`; it does **not** turn a successful release into a control failure.

For a multi-key hold, each ordinary key-up gets its own row. Consequently a later analyzer can distinguish the first release edge (end of the all-keys-down interval) from the last verified-up edge (all requested keys observed up).

## Offline regression

Container environment used for this gate:

- Python: 3.13.x container runtime;
- Xlib import: available from `/opt/pyvenv/lib/python3.13/site-packages/Xlib`;
- no live X server or GUI/input action required;
- no network required.

Commands:

```text
python3 -m py_compile input_owner_v11.py doom_typed_release_backend_v2.py test_doom_typed_release_backend_v2.py
python3 test_doom_typed_release_backend_v2.py
```

Result: `PASS release-edge telemetry offline regression 11/11`.

Covered cases:

1. ordinary up request/ack boundaries;
2. non-up delegation unchanged;
3. fail-closed detection if the v10 up return contract changes;
4. owner release already verified before cleanup up;
5. owner release racing the up call;
6. physical-up sampled true;
7. physical key still observed down without failing control;
8. physical verification query failure remains telemetry-only;
9. multi-key per-key release rows;
10. superseded cleanup is labelled and not reinterpreted as an ordinary edge;
11. source-surface guard: v11 does not replace `_run`, v2 does not define policy/execute/validate behavior.

## H / T / D / C / U

**H — falsifiable hypothesis.** The missing normal release observability can be repaired without changing authority/recovery semantics by wrapping the existing v10 synchronous up call and sampling physical state only after release.

**T — minimum test.** Freeze v10/v1; implement only new v11/v2 files; run deterministic parent-call/fake-display regressions that include normal, raced, superseded, multi-key, physical-down and verification-failure cases; compile all new Python files.

**D — decision.** **PASS for offline instrumentation readiness.** The new path exposes a pre-call request boundary, post-v10-return acknowledgement boundary, and non-authoritative post-release physical sample while preserving the parent policy surface. **NOT YET PASS for live measurement** because this task intentionally executed no X11 input episode.

**C — ways this can fail.** Caller-side request/ack still brackets rather than timestamps the exact server transition. `query_keymap()` is a sample and can reflect external input. The extra post-release query/logging perturbs time after release and must not be mistaken for hold latency. A future v10 semantic change would invalidate the wrapper contract; the regression fails closed if `up` stops returning `None`.

**U — uncertainty.** Dominant residual uncertainty is the interval from `release_requested_ns` to `release_ack_ns`, plus external input between acknowledgement and physical sampling. The added query happens after release, so its latency does not extend the commanded hold, but it can extend post-release step completion. No population latency distribution or real-time guarantee is claimed from the offline test.

## Next gate

Do not enable v2 in the existing v38/v39 allocations and do not reuse those IDs. The next justified scientific action is one newly versioned matched live instrumentation experiment, only after a separate formal allocation lease. It should retain per-key release rows and independently timestamp a task-useful effect; only then is a bounded recovery-policy comparison admissible.
