# Issue #4583 — posthoc raw audit for #4449

This is an independent audit of immutable formal bytes merged by #4449 / PR
#4582. It does not rerun the study or alter the original `STOP_AUDIT`.

## H / T / D / C / U

**H** — Enumerating all rule-closed interpretations of the finite positive
two-claim graph independently reconstructs its least grounded model. All 256
retained candidate and full-rebuild states should match that oracle. The
actual JSONL condition digest should match a canonical sequence with newline
bytes, while the original frozen digest is expected to match only the escaped
two-character `\\n` separator. Effective mutations of copied raw fields
should all be rejected.

**T** — Audit the exact `#4449` formal `rows.jsonl`, `conditions.jsonl`,
`input.json`, `process.json`, and source freeze, identified in `FREEZE.json`.
One isolated OrbStack Linux/arm64 CPython standard-library container; no
candidate, model, GUI, native input, network, or modification of raw inputs.

**D** — `PASS_POSTHOC_RAW_AUDIT_ONLY` requires exact raw/source identities,
256 unique ordered conditions, the escaped-separator diagnosis, candidate and
full rebuild equality with the independent least-model oracle on every row,
zero added claims, no outside-cone changes, both counterexample families,
process/source identity agreement, and 10/10 effective evidence corruptions
rejected. Any mismatch is STOP. This cannot relabel #4449's allocation.

**C** — Only the stored finite two-claim/six-rule corpus is covered. The audit
does not rerun the formal study or validate unretained execution behavior.

**U** — No arbitrary-graph, production runtime, concurrency, GUI/task,
performance, model-utility, or product claim. The audit is not external human
review.

See `PLAN.md`, `FREEZE.json`, and `RESULT.md`.
