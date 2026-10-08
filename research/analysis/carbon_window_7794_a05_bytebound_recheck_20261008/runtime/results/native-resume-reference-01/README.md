# Hash-bound read-only native resume

Problem: a pending native exchange previously required the caller to reproduce
the entire original decision to read its eventual reply. That repeats action
content and invites accidental edits even though no new action is intended.

The existing `run`/CLI now accepts decision_sha256 instead of decision, only with
resume=true. It reads the explicitly selected run/stage request and verifies
the exact SHA256 and canonical bytes before using the unchanged source-binding,
request-byte comparison, reply-binding and owner-state checks. It never publishes
through this route. The digest is integrity binding, not authentication or new
authority. No latest-stage inference, sensor, auto-restart or input replay.

Validation:36 tests pass across native_exchange, agent_review and references.
New controls cover pending→reply without publish, false evaluation preservation,
unchanged request bytes/mtime, missing request, wrong/invalid digest, missing
resume, ambiguous decision+digest, noncanonical bytes, changed bytes between
reads, owner loss and mismatched replies. Pending/owner-loss tests are inert
fixtures; no fresh live failure or recovery trial is claimed.

The primary assistant used the CLI hash reference to review stage3 of the prior
native-direct-stdin-01 run, receiving the same saved-file success, needs_review
feedback and retained dialog pixels. No application was launched or controlled.
`check.py` then compares full-decision and hash-reference responses, verifies
identical content except exchange timestamps, and checks all69 original local
files retain bytes and modification times. It requires that original local run;
the original archived evidence remains in sibling native-direct-stdin-01.

Descriptive UTF-8 JSON request sizes (same separators/run path):

| Retained stage | Full decision resume | Hash reference resume |
| --- | ---: | ---: |
|1|430 bytes|165 bytes|
|2|420 bytes|165 bytes|
|3|250 bytes|165 bytes|

These are representation sizes, not model-token/cost or latency measurements.
Very small decisions may not shrink. Replies/images are unchanged. Source base
is70df9d880; implementation and test diff are in this PR. This engineering
validation had no preregistered performance claim. Live pending recovery and
model performance remain unmeasured.
