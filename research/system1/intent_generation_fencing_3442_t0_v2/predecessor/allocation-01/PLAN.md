# Allocation plan: 3442 intent-generation fencing T0

## H/T/D/C/U

H: In a finite event-order fixture, FENCE_RECONCILE refuses proposals tied to a known superseded authenticated intent generation, cancels admitted-but-not-emitted work with verified release, preserves UNKNOWN for emitted/pending effects, preserves completed effects, and cannot be reverted by stale or reused generations; compare with start-only and generation-only admission fences.

T: Eleven frozen traces x three policies (33 rows): stable control; revision before admission; admitted/unemitted then revision; emitted/pending then revision; completed before revision; stale duplicate; published but delivery uncertain; restart with generation reuse; revision between check and commit; new intent forbids old action; late effect receipt. Candidate JSONL plus separate raw-only auditor. Synthetic CPU-only; no GUI/model/input/task effect/runtime code.

D: PASS_METHOD_SCOPED only if exact 33-row set/outcomes match, safe fence/reconciliation invariants hold, stable control progresses, and four corruption mutations are rejected. Otherwise typed HOLD/FAIL. No live-benefit claim.

C: Synthetic reducer may restate its own assumptions; real delivery ordering, authentication, broker linearization, effect receipts, and release are untested. Existing admission gates may suffice.

U: Finite method test only; no production alignment, GUI correctness, human consent, latency, safety, or runtime promotion.

Frozen base main 5865c5e74842b5bba6a6291e141afae75ca4a147. Candidate candidate.py; auditor audit.py; outputs raw/formal-01.jsonl and raw/audit-01.json. Host Python 3.11 RAM-only pipes with -B. Docker daemon timed out; C: had zero bytes free. No container/GPU/GUI.
