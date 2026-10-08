# Finite conjunction of core admission repairs (#57)

**PASS_CORE_ADMISSION_COMPOSITION_SCOPED.** The privately combined exact #6860
and #6866 contract sources match an independent reference in all 9,000 declared
cases, with zero leaked exceptions and zero input mutations. Each repair alone
leaves the other defect class. This is finite direct-contract integration
evidence; production source and historical results are unchanged.

| Source arm | Cases | Reference mismatches | Leaked exceptions | Input mutations |
| --- | ---: | ---: | ---: | ---: |
| Current main | 9,000 | 1,654 | 750 | 0 |
| #6860 enum guards | 9,000 | 904 | 0 | 0 |
| #6866 current evidence scalars | 9,000 | 750 | 750 | 0 |
| Private conjunction | 9,000 | 0 | 0 | 0 |

These are exhaustive counts within one authored finite matrix, not estimated
failure probabilities. Exception counts are a subset of mismatches. In the
combined arm, 6 valid controls admit; 8,904 malformed controls refuse with
INVALID_PROGRAM; 90 other valid-input cases retain the expected expiry,
staleness, capability and coordinate refusals. All three OS names are metadata
controls executed on this Windows host. Three equality-at-expiry controls admit.

The matrix ran once at 2026-10-03 01:32:42–01:32:45 UTC (10:32 JST), candidate
exit 0. The raw-only independent auditor ran once, exit 0. Six raw corruptions
and four directed implementation mutations are detected, exit 0. A private
exact-Git-byte source export passes all 78 applicable core tests (including the
two PRs' added regressions), and its core doctor exits 0 with no native backend
loaded. Process intervals are command receipts, not comparative performance
measurements. Environment: Windows 11, CPython 3.11.9, AMD64, Intel family 6
model 183, one Python main thread per command. Audit and core/doctor commands
briefly overlapped; no shared runtime or input resource was acquired.

## Evidence and prospective identities

- [Protocol](PROTOCOL.md), [freeze](FREEZE.json), [exact source manifest](SOURCE_MANIFEST.json).
- [Audited result](AUDIT.json), [negative controls](CONTROLS.json).
- [All inputs](raw/cases.jsonl.gz), [all four arms' actual outputs](raw/results.jsonl.gz), [raw hash receipt](raw/RECEIPT.json).
- [Commands, UTC starts/ends, process exits and log hashes](logs/).
- [Copied source bytes](sources/) and [copied PR regression source](regressions/).
- [Private export manifest](CORE_SUITE_MANIFEST.json), [original construction helper source](construction/).

Main: `3116528f3abe0fec72cfc1b5b2b5b4b05538512e`.
#6860 head: `5821ec3adaa01a44a13011bdf1f069b716441981`.
#6866 head: `abd318643112150d073a242926494145c6461e33`.
The common review-base contract blob is `10786d38b98fc8988108230fe59ba8df9ed17cb4`;
it is unchanged by the intervening main archival update.
The combined source SHA-256 is
`1709078c2a144d78ab61a9bc59fbb9973c120b9a58101c079d69db65d43a66b1`.
The prospective local source-freeze commit is
`43faf65ab322e8a90c6484c2b3888dfbb35e4979`; it was created before execution.
That commit identifier is recorded afterward here, outside its own source tree.

## Recheck retained evidence without replaying the matrix

From this package directory, in a scratch export, use the functions directly;
the command-line auditor deliberately refuses to overwrite its original report:

```python
import audit_matrix as a
from pathlib import Path
p = Path('.')
result = a.verify(a.read_gzip(p/'raw/cases.jsonl.gz'),
                  a.read_gzip(p/'raw/results.jsonl.gz'))
print(result)
assert result['errors'] == []
```

Use SHA256SUMS and FREEZE.json to verify the actual file bytes first. gzip holds
the complete original JSONL bytes, with deterministic header metadata. Source
snapshots are exact Git bytes, isolated from Windows checkout newline changes.
No historical scheduler, model, native session or consumed experiment must be
rerun to audit this package. For a new construction reproduction, export the
package to a fresh directory, retain the original raw/AUDIT/CONTROLS elsewhere,
and run the three commands recorded in logs; their output paths refuse reuse.
The construction helpers are preserved as text to document the original export
and command recorder. They were run from the local work directory adjacent to
the isolated clone. CORE_SUITE_MANIFEST records every actual core-suite source.

## Disposition and limits

RETAIN this conjunction evidence for review of the existing two repairs. Neither
arm alone is a sufficient replacement for the conjunction under this matrix.
There is no new production repair or runtime promotion in this PR.
The independent auditor is separately implemented by this worker and imports
neither the runner nor contract. This worker is a nonauthor of #6860/#6866, but
no fixed reviewer committee/digest existed for this verification; it is not a
counted content approval or a final current-main apply-tree check.

The #6860 author's separate evidence-auditor type-comparison repair request
remains outstanding at the reviewed head. This independent conjunction audit
does not silently change that original evidence or substitute for its repair.
Source heads must be rechecked if an author updates them.

The state space excludes NaN/infinity, non-JSON values, arbitrary malformed
objects, concurrency, cancellation, backend/session behavior, physical clocks,
release, live GUI/application effects, tokens, latency and broad safety claims.
No model/container/WSLc/GPU/GUI/native input or formal allocation was used.
No shared resource or main apply lock is held. Common fleet deadline/N are not
available to this worker and were not reset. FINAL-v5 nonauthor consensus,
current-main combination verification, actual required GitHub conditions and
conditional application remain pending; main has not been updated.
