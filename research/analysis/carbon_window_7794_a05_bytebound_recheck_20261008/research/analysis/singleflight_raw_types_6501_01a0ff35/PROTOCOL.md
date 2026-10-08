# #6501 retained-raw JSON type boundary

Worker 01a0ff35-0b9f-7d13-bcfa-22d064ff4fec, policy FINAL-v5.
Base main 11f1bae6f8dbfd280b6ccbd0def0bc23fa5da68d.

H: the retained auditor's Python equality accepts equal-valued JSON floats
and booleans where the frozen scheduler emits integer counts/times.
T: independently enumerate every integer scalar in the retained T0b raw;
substitute an equal-valued float once at each path, and a boolean at each
zero/one path. Keep each variant separate and record both audit decisions.
Unchanged raw, different numeric value and missing case are controls.
D: baseline acceptance of any type-changed variant establishes the scoped
integrity gap. A separate auditor version passes this repair gate only if
all these variants fail and unchanged raw passes. Retain all failures.
C: a mathematically numeric contract could intentionally permit integral
floats; this repair instead enforces the frozen raw's exact JSON types. It
does not change scheduling or decision semantics.
U: finite retained-output coverage only; not arbitrary malformed JSON,
duplicate-member decoding, unbounded schemas, backend/GUI safety, measured
latency, or task benefit. Original formal dispositions remain unchanged.

This is ordinary host-only regression and supplemental read-only audit,
not candidate execution or reuse of a formal allocation. No container,
WSLc, GPU, model or display is used. Output budget: 1 MiB. One small
CPython process at a time. Source/raw identities and command receipts are
retained. Fleet deadline and reviewer identities remain unconfirmed.
