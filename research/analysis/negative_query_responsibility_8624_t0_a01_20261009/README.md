# Issue #8624 — Negative-query responsibility T0 A01

This additive packet tests a finite, stratified target-query model with an explicit signed-fact intervention domain. It does not alter #5865's completeness gate or authorize GUI behavior.

The source and input freeze is in `FREEZE.json`; the frozen question and one-shot limits are in `PREREGISTRATION.md`. Construction tests are run with:

```sh
python3 -B test_construction.py
python3 -B -O test_construction.py
```

The one-shot formal reproduction is:

```sh
python3 -B candidate.py input.json candidate_raw.json
python3 -B auditor.py input.json candidate_raw.json audit.json
```

The auditor command is permitted only if the one candidate invocation exits 0. Do not rerun either frozen invocation. Preserve `candidate.stdout.txt`, `candidate.stderr.txt`, `candidate.exit`, `auditor.stdout.txt`, `auditor.stderr.txt`, `auditor.exit`, `candidate_raw.json`, and `audit.json` as produced. `RESULT.json` reports the scoped disposition and limitations; `SHA256SUMS` binds all retained files.
