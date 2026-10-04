# PR review correction — Issue #7778 T0

The original frozen auditor had two gaps: eligible slack-stealing rows could report less than the independent maximum-service oracle and still pass; `UNKNOWN_OVERLOAD` rows returned before checking reported terminal remaining work and optional service. The original raw files and `formal_01/audit.json` are preserved without modification.

## Corrective audit

`auditor_v2.py` is an additive raw-only correction. It re-read the unchanged `formal_01/inputs.json` and `formal_01/candidate.json`, writing a separate result to `review_v2/audit.json`. The candidate and generator were not rerun. The corrected audit returned `PASS_METHOD_SCOPED`, `H_PASS_SCOPED`, 9 traces, 27 rows, zero audit errors. The frozen positive-slack cases still exactly equal their exhaustive maxima (21/18, 22/18, 22/18, 21/9 for slack/static).

The review regression script first confirms the unmodified raw baseline passes, then plants (1) a safe but suboptimal slack schedule with internally consistent event/terminal fields, and (2) forged low `soft_service` on the static burst overload row. Both are rejected (`FAIL_AUDIT`), 2/2.

## Reproduction

Using the same digest-pinned WSLc Python 3.12.15 container, source read-only, and the review_v2 output directory writable:

```powershell
wslc run --rm --pull never --network none --cpus 1 -e OUTPUT_DIR=/out -v "${PWD}:/src:ro" -v "${PWD}\review_v2:/out" -w /src python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016 python -B auditor_v2.py
wslc run --rm --pull never --network none --cpus 1 -v "${PWD}:/src:ro" -v "${PWD}\review_v2:/out" -w /src python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016 python -B review_v2/test_review.py
```

Observed: baseline corrective audit PASS; regression checks 2/2 rejected. The original run's missing dispatch-overhead sensitivity still limits the result to the zero-overhead synthetic method scope and remains an Issue-level follow-up.
