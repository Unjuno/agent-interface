# Offline X11 proxy reply-framing discriminator

**Disposition:** `PASS_OFFLINE_POLICY_MODEL_SCOPED`.

This local check addresses the next discriminator named in the retained A02/A03
packet. It uses two synthetic X connections owned by the same PID, assigns
connection-local request sequences, parses complete X11 request/reply frame
lengths, and selects a single action-bound `GetPointerControl` reply on the
input connection. A same-PID
process-identity reply is forwarded even when the old coarse `input_started`
condition is true. The selected input reply is withheld only after a matching
KeyPress receipt for that action. Sequence equality without connection equality,
unknown sequence mappings, wrong PID, wrong action, absent KeyPress receipt, and
non-input request roles, or a mismatched keycode do not trigger withholding.

## Method and results

The frozen A03 predicate was replayed as a pure Boolean rule:

```text
owner PID matches AND response type is Reply AND input_started exists
```

For a pre-press `process_identity` reply from a second connection with the same
peer PID, that rule selects `hold`. This reproduces the suspected circular-gate
hazard at the predicate level. It does not prove which reply A03 actually saw:
the retained A03 raw does not have per-connection reply sequence evidence.

## Standard-caller source crosswalk

The current source identifies a narrower candidate reply than the first model
did:

1. On a guarded key-down, `_GuardedBackend._before_input_press` calls
   `_verify_process_identity_for_press` before dispatching input. When the query
   worker is enabled, `_read_process_identity` calls `_target_query`.
2. `TargetQueryWorker` runs its reader on a Python thread (same process PID),
   and the factory creates `X11TargetQueries`, whose constructor opens a new
   `display.Display`. This is a distinct X connection from the input backend
   connection, despite sharing the owner PID.
3. `X11Backend.key_state` then sends `xtest.fake_input(..., KeyPress, ...)` on
   the backend connection and calls `self.d.sync()`. The A03 lock pins
   `python-xlib==0.33`; that version's `Display.sync()` calls
   `get_pointer_control()`, a reply request with core opcode 106.
4. The frozen A03 proxy does not inspect client requests in its client-to-server
   relay. Its server-to-owner relay gates any reply from the owner PID after
   `input_started`; it has no connection/request-role selection. Thus a
   process-identity reply can be delayed before KeyPress, while the later input
   synchronization reply is not uniquely selected.

The revised offline model records the XTEST `FakeInput` KeyPress request and
the following `GetPointerControl` request on one connection, then correlates
their connection-local sequences with the reply. It deliberately gives a
second same-PID identity connection a reply with the same numeric sequence; that
identity reply is forwarded while only the input connection's target reply is
selected after a keycode/action-matched KeyPress receipt. Eight unit tests pass
in normal and optimized Python. Conditions, source crosswalk, test output, and
package hashes are retained alongside this report.

This source crosswalk strengthens the circular-gate diagnosis but does not
recover the reply A03 actually saw: its first result has no per-connection
sequence trace. The offline package does not implement a live socket proxy or
parse XTEST's per-connection `QueryExtension` negotiation. A fresh candidate
must bind that negotiated opcode, connection ID, peer PID, request sequence,
request role, and observed keycode/action before any new live attempt.

## Conditions and evidence

- Conditions: [`conditions.json`](conditions.json).
- Offline model: [`reply_gate.py`](reply_gate.py).
- Tests: [`test_reply_gate.py`](test_reply_gate.py).
- Source-chain audit: [`raw/source-chain-audit.json`](raw/source-chain-audit.json).
- Saved test output: [`raw/test-normal.txt`](raw/test-normal.txt) and
  [`raw/test-optimized.txt`](raw/test-optimized.txt).
- Baseline predicate replay: [`raw/legacy-gate-replay.json`](raw/legacy-gate-replay.json).
- Source hashes: [`SHA256SUMS`](SHA256SUMS).

No WSLc/Docker allocation, live X server, GUI, MCP server, OS input, or network
was used. A02 and A03 remain immutable and consumed; neither was rerun or
reinterpreted as a successful blocked trial. This result says nothing about
physical release, blocked-I/O cancellation, independent application effect,
bounded recovery, MAP01, or efficiency.

## Next decision

Before any fresh live candidate is frozen, inspect the actual proxy/caller
composition for a trustworthy way to associate a reply with `(connection,
peer-PID, request-sequence, request-role, action-id)` and a KeyPress observation
with that action. The old A03 raw has no such trace, and the offline model does
not add it retroactively. If the proxy cannot establish these identities, keep
the blocked path `UNKNOWN` and do not proceed to a new allocation on this
predicate alone.
