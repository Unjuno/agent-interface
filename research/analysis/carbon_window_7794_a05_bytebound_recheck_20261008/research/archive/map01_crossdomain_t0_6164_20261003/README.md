# Issue #59 / PR #6164 cross-domain time-coverage chain — exact preservation

## Why this is an archive, not a result promotion

PR #6164 remains an old Draft whose recorded mergeability is `CONFLICTING`.
Its own body says not to merge the research branch while Issue #59's empirical
real-time-control gate is unresolved. This PR therefore preserves the whole
38-file experiment chain under the historical archive namespace instead of
merging its stale branch tree or changing active research paths.

The retained sequence has distinct outcomes:

- T0-01: candidate disposition `HOLD_CROSSDOMAIN_TIME_COVERAGE_UNIDENTIFIED`,
  while the independent auditor recorded `FAIL_AUDIT`.
- T0-02: a separate candidate again held; its separate auditor also recorded
  `FAIL_AUDIT` for a missing-event-class handling defect.
- T0-03: audit-only successor; it reconstructed the predecessor HOLD from
  raw inputs. This is scoped audit-method evidence, not a candidate result or
  physical input-coverage finding.

These records are not pooled, rescored, or silently corrected here. The later
source-bound #6169 audit successor in merged PR #6171 remains separate and is
not used to replace any T0-01/T0-02 artifact. No live app/game/model/GUI/input,
Docker, WSL, or GPU evidence is claimed. Physical held duration, release
evidence, useful feedback, safety, task completion, and MAP01 exit remain
unestablished.

## Exact source and local validation

The original PR head is `5283513eccd81748b9cc3eb287fc415af3b87db9`; its base
was `4606309ce64f022850e0b1a0be5286087a6153e8`. Its 39-file PR diff included
one generated analysis-index file and 38 experiment-chain files. This archive
retains the 38 experiment files byte-for-byte and intentionally does not copy
the stale repository-wide generated index; the current index remains on main.

`MANIFEST.json` identifies the exact source/target path-prefix mapping and
immutable tree. `VERIFICATION.json` records static per-file blob and size
comparison. The original package SHA256SUMS files are retained verbatim. No
candidate, auditor, download script, or construction test was run during this
rescue; consumed allocations were not replayed.

## Integration disposition

This archive makes the complete historical package recoverable from main but
does not claim a method PASS, close Issue #59, or authorize another allocation.
The original Draft branch should remain untouched until this preservation is
reviewed and merged. Only then can its stale PR/remote ref be retired safely.
