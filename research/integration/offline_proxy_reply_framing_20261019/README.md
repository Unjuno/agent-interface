# Offline X11 proxy reply-framing discriminator

**Disposition:** `PASS_OFFLINE_POLICY_MODEL_SCOPED`.

This local check addresses the next discriminator named in the retained A02/A03
packet. It uses two synthetic X connections owned by the same PID, assigns
connection-local request sequences, parses complete X11 request/reply frame
lengths, and selects a single action-bound `input_sync` reply. A same-PID
process-identity reply is forwarded even when the old coarse `input_started`
condition is true. The selected input reply is withheld only after a matching
KeyPress receipt for that action. Sequence equality without connection equality,
unknown sequence mappings, wrong PID, wrong action, absent KeyPress receipt, and
non-input request roles do not trigger withholding.

## Method and results

The frozen A03 predicate was replayed as a pure Boolean rule:

```text
owner PID matches AND response type is Reply AND input_started exists
```

For a pre-press `process_identity` reply from a second connection with the same
peer PID, that rule selects `hold`. This reproduces the suspected circular-gate
hazard at the predicate level. It does not prove which reply A03 actually saw:
the retained A03 raw does not have per-connection reply sequence evidence.

The proposed discriminator is implemented only in this offline package. Its
ledger keys request identity by connection and sequence, checks the associated
peer PID and request role, and requires an action-matched KeyPress receipt before
selecting the one target reply. Seven unit tests pass in normal and optimized
Python. The test output and package hashes are retained alongside this report.

## Conditions and evidence

- Conditions: [`conditions.json`](conditions.json).
- Offline model: [`reply_gate.py`](reply_gate.py).
- Tests: [`test_reply_gate.py`](test_reply_gate.py).
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
