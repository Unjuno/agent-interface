# PR review correction — Issue #7778 T0

The frozen auditor had three review gaps: it accepted a safe but suboptimal slack result, skipped terminal-metric validation for `UNKNOWN_OVERLOAD`, and allowed `STATIC_RESERVATION` rows to idle ready soft work while serving as the gain comparator. The original raw files and `formal_01/audit.json` are preserved unchanged.

## Corrective audit

`auditor_v2.py` is an additive raw-only correction. It re-read the unchanged `formal_01/inputs.json` and `formal_01/candidate.json`, writing a separate result to `review_v2/audit.json`. The candidate and generator were not rerun. The corrected audit returned `PASS_METHOD_SCOPED`, `H_PASS_SCOPED`, 9 traces, 27 rows, zero audit errors. The frozen positive-slack cases still exactly equal their exhaustive maxima (21/18, 22/18, 22/18, 21/9 for slack/static).

The review regression script first confirms the unmodified raw baseline passes, then plants (1) a safe but suboptimal slack schedule with internally consistent event/terminal fields, and (2) forged low `soft_service` on the static burst overload row. Both are rejected (`FAIL_AUDIT`), 2/2.

## Reproduction

Using the same digest-pinned WSLc Python 3.12.15 container, source read-only, and the review_v2 output directory writable:

```powershell
wslc run --rm --pull never --network none --cpus 1 -e OUTPUT_DIR=/out -v "${PWD}:/src:ro" -v "${PWD}\review_v2:/out" -w /src python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016 python -B auditor_v2.py
wslc run --rm --pull never --network none --cpus 1 -v "${PWD}:/src:ro" -v "${PWD}\review_v2:/out" -w /src python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016 python -B review_v2/test_review.py
```

Observed: baseline corrective audit PASS; all three planted audit mutations rejected. Dispatch-overhead sensitivity was examined in a separate T0b allocation and its result is recorded separately on Issue #7778; this package remains the zero-overhead T0 result.
