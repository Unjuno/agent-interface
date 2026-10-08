# Historical result replay — #4366

**PASS_HISTORICAL_RESULT_PROJECTION_SCOPED**, not production promotion.
See PLAN.md for H/T/D/C/U, REPORT.md for interpretation, AUDIT.json for the original result.

24 fresh private counter cases / 96 receiver subprocesses. Both policies have
zero duplicate effects. The current-state projection returns 12 misbound replay
results (eight wrong values, four ABA version-only mismatches); the recorded-result
policy returns zero. Counts are directed cases, not estimated failure rates.

The public source freeze preceded formal execution at
`7c937479892296c4abc5746dfea005d248a8b9ec`, followed by Issue comment5832532854.
No shared runtime, GUI, model, provider, or real application task was executed.

## Complete evidence, not a summary capsule

Ten binary `evidence-*.xzpart` files concatenate to a 38,076-byte tar.xz archive:
SHA-256 `ccc38d655081ab85e831350a8a360efb60ba7184a3010bceb29b373c14df28bc`.
All 714 regular files / 3,824,828 member bytes are retained, including every
request, reply, SQL log, original/per-call/final SQLite file, process receipt,
construction record, frozen source, original audit and twelve mutation controls.
EVIDENCE.json binds piece lengths, SHA-256 and Git blob IDs. RAW_MANIFEST.json
inside the archive binds the remaining713 members. Nonexecuted bytecode caches
and temporary copied mutation directories are not retained; mutation code and
before/after hashes are retained.

Run from this directory in a trusted local checkout:

```sh
python -S -B verify.py
python -S -B -m unittest -v test_restore
```

`verify.py` restores into a temporary private directory, checks all member hashes
and14 readable-file copies, invokes only the read-only auditors and8 pure unit
methods, and requires byte-identical original AUDIT/CONTROLS output. It also
checks the six recorded outer batch exits. It starts zero scientific receivers.
RECONSTRUCTION.json and PACKAGING_TESTS.txt retain local validation results.

For manual data-only inspection, use a NEW destination:

```sh
python -S -B restore.py /tmp/e5d7-evidence-new
```

Do not rerun `run.py` against the consumed formal allocation. A new scientific
replication needs a fresh allocation and prospective conditions. Current-state
APIs may legitimately return current values; the finding concerns fields claimed
to be the ORIGINAL operation result, not whole-response byte equality.

## Qualification boundaries

Provided Linux execution container / CPython3.13.5 / SQLite3.46.1. Docker/OrbStack
image identity is unavailable. Process exit73 is not power-loss testing. A
same-author, separately implemented auditor is not external human review. No
model usefulness, token/latency benefit, current production defect, general GUI
atomicity, or integrated product readiness is inferred. GitHub publication,
applicable exact-head CI/review, and main integration are separate states recorded
on the PR; do not infer them from this scoped experimental PASS.
