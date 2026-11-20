# Independent raw audit of native V15 virtual-X11 evidence

This package independently rechecks a single retained native virtual-X11 construction run from PR #8094. It never starts Xvfb, invokes candidate code, or replays the input operation.

## H/T/D/C/U

- **H:** The retained run's raw records support the narrow component claim that ordered multi-key UPs and cleanup-first cancellation preserve per-key admission identity and leave the X-server keymap neutral in the two recorded cases.
- **T:** Independently verify the 30-file evidence manifest, all 81 Git-locked source blobs at the exact source head, raw and source-lock hashes, the stored auditor and mutation dispositions, then reconstruct event order, identity joins, keymap states, cancellation, shutdown and VM stop directly from raw JSON.
- **D:** `PASS_SCOPED` only if every check in `RESULT.json` passes. A mismatch is `FAIL_OR_REVIEW`; no candidate rerun is part of this audit.
- **C:** The retained result and raw come from one execution. The producer auditor and this independent checker could share omissions in the recorded instrumentation or source contract.
- **U:** One invocation, two component cases, private Xvfb/XTEST only. No production `execute`/V39/Session, game, model, physical keyboard, app consumption, useful feedback, recovery efficacy, latency benefit or gameplay result.

## Evidence pins and result

- Evidence commit: `59e307adde701dc3e061ee3ff124c5982c20fcc9` (PR #8094 head when audited).
- Executed-source commit: `2b0cb591c3ebcb84d1db983612613850c08fffea`.
- Raw SHA-256: `923d7ce368cafe7a05b0799d7dbcac5eb39462628099d571c9d2cc4d8d8e3aa6`.
- Independent raw reconstruction: **15/15 PASS**. The retained author's audit records 658/658 and the eight saved corruption controls reject all eight mutations; those are checked as records, not presented as a new execution or independent 658-check rerun.
- The initial attempt stopped before reading evidence because the checker resolved the repository root one directory too high. `AUDIT_ATTEMPT_01_STOP.json` preserves that construction failure; the corrected attempt resolves root from the linked worktree and passes.

The directly reconstructed event sequence is DOWN a/s/w followed by batch UP w/s/a. Admission and release measurements retain matching actuation identities, and the X-server keymap ends neutral. In the cleanup-first case, a/s are released with `per_key_cleanup_snapshot`; the late same-lease batch is `Cancelled`, adds no window input event or owner record, and final owner close is verified neutral. These fields are X-server observations, not hardware-keyboard timing or application receipt.

## Reproduction

Use Python 3.11+ and the same repository checkout. Fetch PR #8094's exact evidence commit so its archived files are available, then run:

```powershell
git fetch origin refs/pull/8094/head:refs/review/pr-8094
python -B research/doom/v15_native_x11_raw_audit_a01_20261005/audit_raw.py
```

The audit is read-only with respect to the pinned evidence and writes `RESULT.json` in this package. It uses `git show`/`git rev-parse` to retrieve the exact package and source objects; it does not depend on the current working-tree copies of those sources. `SHA256SUMS` covers every package file except itself.
