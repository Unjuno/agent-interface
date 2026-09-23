# Explicit saved-contract match followed by final evaluation in one caller

checkpoint_finish.run implements a caller-selected policy: request a fresh
checkpoint, and only if the declared saved-artifact predicate matches, request
finish and return its independently evaluated result. finish_on_match=True is
required. This policy is appropriate only when the caller intentionally chooses
that predicate as its trigger to stop accepting further input. It is not inferred
from an arbitrary VERIFIED field or offered as universal task-completion detection.

The helper validates query identity, boundary status, contiguous record cursor,
exact contract and actual value mapping, open observation window, null task success,
no authority and a SHA-256-shaped artifact digest. Comparison uses canonical JSON
so boolean and numeric values are not treated as equal. The helper does not itself
read or authenticate that artifact; it consumes a trusted runtime query response.
Missing evidence, UNKNOWN, busy, gap, wrong identity or mismatched fields return
needs_decision without finish. All reply records are retained.

The helper sends no GUI input. It makes at most two exchange calls and never
retries. The caller supplies two distinct fresh IDs, received cursor, contract and
an exchange callback with its own I/O deadline and request persistence. A request
is placed in the returned transcript before exchange is attempted. The live probe
also writes requests to disk before sending. finish_attempted means attempted by
the caller, not proof that the runtime received it. Transport failures after finish
may leave admission closed; they do not authorize another input replay.

## Scoped final evaluation

Runtime v31 attaches evaluation_request correlation to the independent evaluation
performed by explicit finish. It does not attribute that score to an earlier input
action. Request boundary v4/cursor v7/socket v16 recognize this evaluation by its
finish request identity, while retaining prior admitted-action boundary behavior.
A record claiming both attribution forms is rejected as ambiguous. The helper
requires explicit finish evaluation identity and a boolean score. It retains false
scores and never substitutes the earlier checkpoint's VERIFIED for final success.

If an earlier finish_after finalizer was already reserved, explicit finish still
joins it rather than performing a new evaluation. That path may close without a
new matching finish evaluation; this helper returns unresolved/error, not a guessed
result. It is designed for the terminal-review path used in the experiment.

## Evidence and scope

Thirteen controls use a previously recorded Calc checkpoint and synthetic final
responses. They cover success, UNKNOWN, wrong query, changed contract/actual,
invalid hash, gap, busy, missing cursor, false final evaluation, wrong final identity,
legacy unscoped evaluation and a final transport exception. The eight precondition
failures make only one call and never finish. Test sources and input hashes are
retained in checkpoint-finish-controls-02; controls-01 is the preceding inline run.

The scripted Calc integration first submits cell edits with terminal review.
The first conditional call sees UNKNOWN and leaves admission open. The fixture
then confirms Excel format. The second conditional call receives VERIFIED and
immediately sends scoped finish; independent evaluation succeeds. Twelve frames,
full delivered prefixes, release, runtime source hashes and replay of both archived
workbooks after source cleanup pass. All measured processes record matching clocks.

Checkpoint reply receipt to finish-call start was 0.199 ms in that run. The earlier
actual assistant run had 23352.712 ms between those boundaries. These are different
scripted/assistant conditions, not a matched speedup comparison. The structural
improvement is that the selected policy no longer requires a model/tool turn merely
to request the final score after a matching checkpoint. It still performs both
socket exchanges and final independent evaluation. Model receipt, actual tokens,
overall live tempo and unfamiliar completion policies remain unmeasured.

The predicate checks only specified saved cells/fields, not all preserved or
forbidden effects. It proves no actor causation, freshness at finalization or input
authority. A later change can still make the final score false. The runtime remains
an optional candidate; actual assistant use of this helper and regression coverage
for the new finish identity outside the Calc route remain next work.

Evidence: probe_checkpoint_finish_controls.py, probe_checkpoint_finish_calc.py,
results/checkpoint-finish-controls-01/02 and results/checkpoint-finish-calc-01.
